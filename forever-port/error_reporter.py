"""Private agent error ledger. Read diagnostics as data; never execute saved Lua.

The ledger lives outside CurseForge. No network, game input or SavedVariables
writes. scan imports saved reports and/or staged verification failures; status
and resolve give the next agent an explicit handoff rather than hiding failures.
"""
from pathlib import Path
import argparse, datetime, hashlib, json, os, re, subprocess, sys

MANAGER = Path.home() / 'Documents/EllesmereUI-Forever-Updates'
DEFAULT_LEDGER = MANAGER / 'diagnostics/errors.json'

def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()
def digest(value): return hashlib.sha256(value.encode('utf-8')).hexdigest()
def safe_file(path):
    path=Path(path).absolute()
    for p in (path,*path.parents):
        if p.is_symlink() or p.is_junction(): raise ValueError(f'Reparse point refused: {p}')
    return path

def lua_string(source, start):
    """Decode only a Lua quoted/long string literal, with no eval or interpreter."""
    long=re.match(r'\[(=*)\[',source[start:])
    if long:
        close=']'+long[1]+']'; begin=start+len(long[0]); end=source.find(close,begin)
        if end<0: raise ValueError('Unterminated diagnostic string')
        value=source[begin:end]
        if value.startswith('\n'): value=value[1:]
        return value,end+len(close)
    quote=source[start:start+1]
    if quote not in ('"',"'"): raise ValueError('Diagnostic value is not a literal string')
    pos=start+1; out=[]
    escapes={'a':'\a','b':'\b','f':'\f','n':'\n','r':'\r','t':'\t','v':'\v'}
    while pos<len(source):
        c=source[pos];pos+=1
        if c==quote: return ''.join(out),pos
        if c!='\\': out.append(c);continue
        if pos>=len(source): break
        c=source[pos];pos+=1
        if c.isdigit():
            digits=c
            while pos<len(source) and len(digits)<3 and source[pos].isdigit(): digits+=source[pos];pos+=1
            if int(digits)>255: raise ValueError('Invalid Lua byte escape')
            out.append(chr(int(digits)))
        else: out.append(escapes.get(c,c))
    raise ValueError('Unterminated diagnostic string')

def saved_reports(source):
    """Lexically walk strings/comments; keys embedded in chat cannot match.

    Extract the existing last report and our bounded string-only error history.
    All other values remain uninterpreted, including arbitrary Lua expressions.
    """
    i=0; reports=[]
    while i<len(source):
        if source.startswith('--',i):
            j=i+2
            if re.match(r'\[=*\[',source[j:]): _,i=lua_string(source,j)
            else:
                end=source.find('\n',j);i=len(source) if end<0 else end+1
        elif source[i] in ('"',"'") or re.match(r'\[=*\[',source[i:i+16]):
            _,i=lua_string(source,i)
        elif source[i]=='[':
            key=re.match(r'\["(_foreverLastReport|_foreverErrorReports)"\]\s*=\s*',source[i:])
            if not key: i+=1;continue
            i+=len(key[0])
            if key[1]=='_foreverLastReport':
                value,i=lua_string(source,i);reports.append(value)
            else:
                if source[i:i+1]!='{': raise ValueError('Error history must be a literal table')
                i+=1
                while True:
                    gap=re.match(r'[\s,]*',source[i:]);i+=len(gap[0])
                    if source[i:i+1]=='}':i+=1;break
                    if source.startswith('--',i):
                        end=source.find('\n',i);i=len(source) if end<0 else end+1;continue
                    index=re.match(r'\[\d+\]\s*=\s*',source[i:])
                    if index:i+=len(index[0])
                    value,i=lua_string(source,i);reports.append(value)
                    if len(reports)>10: raise ValueError('Unexpectedly large diagnostic history')
        else:i+=1
    return reports

def load_ledger(path):
    if not path.exists():return {'schema':1,'issues':{},'observations':[]}
    return json.loads(safe_file(path).read_text(encoding='utf-8'))

def record(db,kind,key,detail,source,evidence):
    identity=digest(kind+'\n'+key)[:16];t=now()
    old=db['issues'].get(identity)
    if old and evidence in old.get('seen_evidence',[old.get('last_evidence')]):return identity
    row=old or {'id':identity,'kind':kind,'key':key,'first_seen':t,'observations':0}
    row.update(status='open',last_seen=t,detail=detail[:16000],source=source,last_evidence=evidence,
               observations=row['observations']+1)
    row['seen_evidence']=(row.get('seen_evidence',[])+[evidence])[-100:]
    db['issues'][identity]=row
    return identity

def scan(db,stage=None,saved_files=()):
    if stage:
        stage=safe_file(stage)
        results_path=safe_file(stage/'.verification/results.json')
        results=json.loads(results_path.read_text(encoding='utf-8'))
        for result in results:
            if result['returncode']:
                name=result['test'];test=Path(name)
                log=safe_file(stage/'.verification'/(test.parent.parent.name+'-'+test.name+'.txt'))
                detail=log.read_text(encoding='utf-8') if log.exists() else 'Failure log unavailable'
                record(db,'offline-test',name,detail,str(log),digest(detail))
        db['observations'].append({'time':now(),'kind':'verification','source':str(results_path),
            'passed':sum(r['returncode']==0 for r in results),'failed':sum(r['returncode']!=0 for r in results)})
    for saved in saved_files:
        saved=safe_file(saved)
        before=saved.stat();raw=saved.read_bytes();after=saved.stat()
        if (before.st_size,before.st_mtime_ns)!=(after.st_size,after.st_mtime_ns):raise ValueError('Save changed during read; retry after the game checkpoint')
        reports=saved_reports(raw.decode('utf-8-sig'))
        for report in reports:
            for match in re.finditer(r'(?:^|\n)Error \d+ \((\d+) occurrences\):\n(.*?)(?=\nError \d+ \(|\Z)',report,re.S):
                detail=match[2][:16000];key=detail.split('\n',1)[0]
                record(db,'runtime',key,detail,str(saved),digest(report))
        db['observations'].append({'time':now(),'kind':'saved-diagnostics','source':str(saved),
            'sha256':hashlib.sha256(raw).hexdigest(),'mtime_ns':after.st_mtime_ns,'reports':len(reports),
            'note':'On-disk checkpoint only; current game memory and absence of uncaptured errors are unknown.'})
    db['observations']=db['observations'][-100:]

def discover_saves():
    cfg=json.loads((MANAGER/'current.json').read_text())
    root=safe_file(Path(cfg['installation']).parent.parent/'WTF')
    found=[]
    for folder,dirs,files in os.walk(root,followlinks=False):
        dirs[:]=[n for n in dirs if not (Path(folder)/n).is_symlink() and not (Path(folder)/n).is_junction()]
        if Path(folder).name=='SavedVariables' and 'EllesmereUI.lua' in files:
            found.append(safe_file(Path(folder)/'EllesmereUI.lua'))
    return found

def save_ledger(path,db):
    safe_file(path);path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix('.tmp');safe_file(tmp)
    if tmp.exists():raise ValueError('Stale ledger temporary file; review before retrying')
    tmp.write_text(json.dumps(db,indent=2),encoding='utf-8');os.replace(tmp,path)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--ledger',type=Path,default=DEFAULT_LEDGER)
    sub=p.add_subparsers(dest='command',required=True)
    q=sub.add_parser('scan');q.add_argument('--stage',type=Path);q.add_argument('--saved-file',type=Path,action='append',default=[]);q.add_argument('--discover-saves',action='store_true')
    q=sub.add_parser('verify');q.add_argument('--stage',type=Path,required=True)
    sub.add_parser('status')
    q=sub.add_parser('resolve');q.add_argument('id');q.add_argument('--evidence',required=True)
    args=p.parse_args();db=load_ledger(args.ledger);rc=0
    if args.command=='verify':
        results=args.stage/'.verification/results.json'
        prior=results.stat().st_mtime_ns if results.exists() else None
        run=subprocess.run([sys.executable,str(MANAGER/'manage.py'),'verify','--stage',str(args.stage)],capture_output=True,text=True,errors='replace')
        print(run.stdout,end='');print(run.stderr,end='',file=sys.stderr);rc=run.returncode
        if results.exists() and results.stat().st_mtime_ns!=prior:scan(db,args.stage)
        if rc:record(db,'verification','stage verification',run.stdout+run.stderr,str(args.stage),digest(run.stdout+run.stderr))
    elif args.command=='scan':scan(db,args.stage,args.saved_file+(discover_saves() if args.discover_saves else []))
    elif args.command=='resolve':
        row=db['issues'][args.id];row.update(status='resolved',resolved_at=now(),resolution=args.evidence)
    if args.command!='status':save_ledger(args.ledger,db)
    open_rows=[r for r in db['issues'].values() if r['status']=='open']
    print(f'{len(open_rows)} open issues; ledger: {args.ledger}')
    for row in open_rows:print(row['id'],row['kind'],row['key'])
    if args.command=='status' and open_rows:rc=1
    return rc

if __name__=='__main__':
    try:sys.exit(main())
    except Exception as error:print('STOP:',error,file=sys.stderr);sys.exit(2)
