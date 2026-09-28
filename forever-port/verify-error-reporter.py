"""Reporter data-only parsing, checkpoint retention and failure handoff tests."""
from pathlib import Path
import importlib.util, tempfile, json
from lupa.lua51 import LuaRuntime
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('reporter',Path(__file__).with_name('error_reporter.py'))
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
sample=r'''EllesmereUIDB = {
 ["chat"] = "[\"_foreverLastReport\"] = \"fake\"",
 -- ["_foreverLastReport"] = "comment"
 ["_foreverLastReport"] = "EllesmereUI\nCaptured suite errors: 1\nError 1 (2 occurrences):\nEllesmereUI test\nstack",
 ["_foreverErrorReports"] = { "old\nreport", -- [1]
 [2] = [=[long
report]=], },
 ["unrelated"] = os.execute("must never execute"),
}'''
reports=mod.saved_reports(sample)
assert len(reports)==3 and reports[1]=='old\nreport' and reports[2]=='long\nreport'
assert mod.lua_string(r'"\065\010\\\""',0)[0]=='A\n\\"'
try:mod.saved_reports('["_foreverLastReport"] = os.execute("anything")')
except ValueError:pass
else:raise AssertionError('Executable diagnostic accepted')
with tempfile.TemporaryDirectory() as tmp:
    d=Path(tmp);sv=d/'save.lua';sv.write_text(sample,encoding='utf-8')
    ledger=mod.load_ledger(d/'ledger.json');mod.scan(ledger,saved_files=[sv]);mod.scan(ledger,saved_files=[sv])
    assert len(ledger['issues'])==1
    row=next(iter(ledger['issues'].values()));assert row['observations']==1
    row['status']='resolved';mod.scan(ledger,saved_files=[sv]);assert row['status']=='resolved'
    sv.write_text(sample.replace('2 occurrences','3 occurrences'),encoding='utf-8')
    mod.scan(ledger,saved_files=[sv]);assert row['status']=='open'
    row['status']='resolved';sv.write_text(sample,encoding='utf-8')
    mod.scan(ledger,saved_files=[sv]);assert row['status']=='resolved','historical evidence reopened a fixed issue'
    (d/'.verification').mkdir()
    (d/'.verification/results.json').write_text(json.dumps([{'test':'EllesmereUI/forever-port/verify-example.py','returncode':1}]))
    (d/'.verification/EllesmereUI-verify-example.py.txt').write_text('assertion failure')
    mod.scan(ledger,stage=d);assert len(ledger['issues'])==2
    mod.save_ledger(d/'ledger.json',ledger);assert mod.load_ledger(d/'ledger.json')==ledger
print('PASS: Lua strings/comments/history parsed without execution; ledger dedup/reopen/save and verification failures')
source=(ROOT/'EllesmereUI_Forever.lua').read_text(encoding='utf-8-sig')
start=source.index('local function SaveReport()');end=source.index('SLASH_EUIFOREVER1',start)
lua=LuaRuntime();lua.execute('status={errors={}}; EllesmereUIDB={sentinel=42}; report="clean"; function Report() return report end')
lua.execute(source[start:end])
lua.execute('''
status.SaveReport(); assert(EllesmereUIDB._foreverErrorReports==nil)
status.errors={"error"};report="one";status.SaveReport();status.SaveReport()
assert(#EllesmereUIDB._foreverErrorReports==1)
for i=2,9 do report=tostring(i);status.SaveReport() end
assert(#EllesmereUIDB._foreverErrorReports==5 and EllesmereUIDB._foreverErrorReports[1]=="5")
status.errors={};report="clean";status.SaveReport()
assert(#EllesmereUIDB._foreverErrorReports==5 and EllesmereUIDB._foreverLastReport=="clean")
status.errors={"error"};report=string.rep("x",40000);status.SaveReport()
assert(#EllesmereUIDB._foreverErrorReports[5]==32768 and EllesmereUIDB.sentinel==42)
''')
print('PASS: production diagnostic history bounded/deduplicated, survives clean checkpoint, settings retained')
