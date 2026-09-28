"""Validate the export and build an installable ZIP without personal data."""
from pathlib import Path
import argparse, hashlib, json, re, zipfile, posixpath
from sync_public import ROOT, PROFILE, STUB, linked

def build(output):
    manifest = json.loads((ROOT / 'public-source-manifest.json').read_text())['files']
    if (ROOT / PROFILE).read_bytes() != STUB:
        raise ValueError('Public profile must be the exact no-op placeholder')
    version = re.search(r'^## Version:\s*(\S+)', (ROOT / 'EllesmereUI.toc').read_text(), re.M).group(1)
    payload = {}
    for name, expected in manifest.items():
        path = ROOT / name
        if path.is_absolute() and (not path.resolve().is_relative_to(ROOT) or linked(path)):
            raise ValueError(f'Unsafe export path: {name}')
        if any(linked(p) for p in path.parents if p != ROOT and p.is_relative_to(ROOT)):
            raise ValueError(f'Linked parent: {name}')
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != expected:
            raise ValueError(f'Export changed; re-sync or review manifest: {name}')
        parts = Path(name).parts
        if 'forever-port' in parts or 'tests' in parts:
            continue
        archive_name = name if len(parts) > 1 and parts[0].startswith('EllesmereUI') else 'EllesmereUI/' + name
        payload[archive_name] = data
    # Walk active addon manifests, not dormant standalone library manifests.
    references = 0
    queue = [name for name in payload if name.endswith('.toc') and len(Path(name).parts) == 2]
    visited = set()
    while queue:
        name = queue.pop()
        if name in visited:
            continue
        visited.add(name)
        data = payload[name]
        text = data.decode('utf-8-sig')
        refs = ([line.strip() for line in text.splitlines() if line.strip() and not line.lstrip().startswith('#')]
                if name.endswith('.toc') else re.findall(r'\bfile\s*=\s*["\']([^"\']+)', text))
        for ref in refs:
            ref = ref.replace('\\', '/')
            if ref.startswith(('Interface/', 'Blizzard_', '$')) or '$' in ref:
                continue
            target = posixpath.normpath((Path(name).parent / ref).as_posix())
            if target not in payload:
                raise ValueError(f'Missing package reference: {name}: {ref}')
            references += 1
            if target.endswith('.xml'):
                queue.append(target)
    payload['EllesmereUI/README.md'] = (ROOT / 'README.md').read_bytes()
    output = output.resolve()
    if output.is_relative_to(ROOT):
        raise ValueError('Keep release artifacts outside the source checkout')
    output.mkdir(parents=True, exist_ok=True)
    archive = output / f'EllesmereUI-{version}.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zipfile_out:
        for name, data in sorted(payload.items()):
            info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            zipfile_out.writestr(info, data)
    with zipfile.ZipFile(archive) as check:
        if check.testzip() is not None or set(check.namelist()) != set(payload):
            raise ValueError('ZIP verification failed')
        for name, data in payload.items():
            if check.read(name) != data:
                raise ValueError(f'ZIP byte mismatch: {name}')
    checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
    (output / 'SHA256SUMS.txt').write_text(f'{checksum}  {archive.name}\n', encoding='utf-8')
    print(json.dumps({'archive': str(archive), 'sha256': checksum, 'files': len(payload), 'references': references}, indent=2))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    build(parser.parse_args().output)
