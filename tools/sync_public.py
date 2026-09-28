"""Export a reviewed private suite capture to this public repository. Never deploys."""
from pathlib import Path
import argparse, hashlib, json, os, subprocess, re

ROOT = Path(__file__).resolve().parents[1]
PROFILE = 'EllesmereUI_ForeverProfile.lua'
STUB = b'-- Public distribution: the owner\'s private profile snapshot is intentionally omitted.\n-- Normal EllesmereUI defaults and existing SavedVariables remain authoritative.\n-- Never install this placeholder over the owner\'s private customization seed.\n'
RUNTIME = {'.lua', '.toc', '.xml', '.tga', '.blp', '.ttf', '.otf', '.ogg', '.mp3', '.wav', '.png', '.jpg', '.jpeg', '.dds'}

def digest(data):
    return hashlib.sha256(data).hexdigest()

def public_bytes(name, data):
    # A provenance comment includes an account folder, not executable behavior.
    if name == 'EllesmereUIQuestTracker/EllesmereUIQuestTracker_Forever.lua':
        data = re.sub(rb'(--[^\r\n]*WTF/Account/)[^/\r\n]+/', rb'\1PRIVATE/', data)
    return data

def linked(path):
    return path.is_symlink() or path.is_junction()

def files(folder):
    if linked(folder):
        raise ValueError(f'Reparse point: {folder}')
    for base, dirs, names in os.walk(folder, followlinks=False):
        dirs[:] = [n for n in dirs if n not in {'.git', '__pycache__', '.verification'} and not linked(Path(base) / n)]
        for name in sorted(names):
            path = Path(base) / name
            if not linked(path):
                yield path

def exported(name):
    p = Path(name)
    if any(part.lower() in {'wtf', 'savedvariables', 'backups', 'diagnostics', 'native-fixtures'} for part in p.parts):
        return False
    if p.name == PROFILE:
        return False
    if 'forever-port' in p.parts:
        return p.name.startswith('verify') and p.suffix == '.py' or p.name in {'error_reporter.py', 'native-layout-candidate.lua'}
    if 'tests' in p.parts:
        return p.suffix in {'.py', '.lua'}
    return p.suffix.lower() in RUNTIME or p.name.endswith('.toc.disabled') or p.name.lower() in {'license', 'license.md', 'license.txt', 'copying', 'copying.txt'} or p.name == '_keys.txt'

def sync(source):
    source = source.resolve()
    if source == ROOT or ROOT.is_relative_to(source) or source.is_relative_to(ROOT):
        raise ValueError('Source must be a separate reviewed suite capture')
    if not (source / 'EllesmereUI/EllesmereUI.toc').is_file():
        raise ValueError('Source must contain EllesmereUI and sibling addon folders')
    output = {}
    for folder in sorted(source.glob('EllesmereUI*')):
        if not folder.is_dir() or linked(folder):
            continue
        for path in files(folder):
            name = path.relative_to(folder if folder.name == 'EllesmereUI' else source).as_posix()
            if exported(name):
                output[name] = public_bytes(name, path.read_bytes())
    output[PROFILE] = STUB
    # Only remove tracked runtime/export paths that are obsolete in this snapshot.
    tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
    for name in tracked:
        if not name or name.startswith(('.github/', '.tools/', 'tools/', 'docs/')):
            continue
        if exported(name) and name not in output:
            dest = ROOT / name
            if linked(dest) or any(linked(p) for p in dest.parents if p != ROOT and p.is_relative_to(ROOT)):
                raise ValueError(f'Reparse point in output: {name}')
            dest.resolve().relative_to(ROOT)
            if dest.is_file():
                dest.unlink()
    for name, data in output.items():
        dest = ROOT / name
        if linked(dest) or any(linked(p) for p in dest.parents if p != ROOT and p.is_relative_to(ROOT)):
            raise ValueError(f'Reparse point in output: {name}')
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
    manifest = {'format': 1, 'profile': 'public no-op; private seed excluded',
                'files': {name: digest(data) for name, data in sorted(output.items())}}
    (ROOT / 'public-source-manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    print(f'Exported {len(output)} public files; private profile replaced only in repository.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    sync(parser.parse_args().source)
