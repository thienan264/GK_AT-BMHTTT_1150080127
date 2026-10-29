#!/usr/bin/env python3
"""Build a source submission without personal identities, build outputs or unrelated labs."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
import hashlib

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'dist' / '1150080127_Ma_hoa_lai_Ban_nop.zip'
ROOT_FILES = ['pom.xml', 'README.md', 'README.docx', 'environment.lock.json', '.gitignore']
FOLDERS = ['src', 'scripts', 'tools', 'docs', 'presentation', 'artifacts']
EXCLUDED_PARTS = {'__pycache__', '.local-keys', '.git', 'target', 'LAB9_Resources', 'upgrade-verification'}
EXCLUDED_SUFFIXES = {'.p12', '.pfx', '.key', '.pyc'}

def include(path):
    return (path.is_file()
            and not any(part in EXCLUDED_PARTS for part in path.relative_to(ROOT).parts)
            and not path.name.startswith(('LAB9', '.DS_Store', '.env'))
            and path.suffix.lower() not in EXCLUDED_SUFFIXES)

def main():
    files = [ROOT / name for name in ROOT_FILES if (ROOT / name).is_file()]
    for name in FOLDERS:
        files.extend(path for path in (ROOT / name).rglob('*') if include(path))
    files = sorted(set(files))
    OUTPUT.parent.mkdir(exist_ok=True)
    with ZipFile(OUTPUT, 'w', ZIP_DEFLATED) as archive:
        for path in files:
            archive.write(path, str(path.relative_to(ROOT)))
        manifest = '\n'.join(hashlib.sha256(path.read_bytes()).hexdigest() + '  ' + str(path.relative_to(ROOT)) for path in files)
        archive.writestr('SUBMISSION_SHA256SUMS.txt', manifest + '\n')
    with ZipFile(OUTPUT) as archive:
        assert archive.testzip() is None
        assert not any('.local-keys' in name or name.endswith(('.p12', '.pfx', '.key')) or 'LAB9' in name for name in archive.namelist())
    print(f'{OUTPUT}\n{len(files)} files; no personal private keys or unrelated LAB9 files.')

if __name__ == '__main__':
    main()
