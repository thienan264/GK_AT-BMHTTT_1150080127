#!/usr/bin/env python3
import hashlib,json,pathlib
base=pathlib.Path(__file__).resolve().parents[1]/'src/test/resources/nist-acvp'
manifest=json.loads((base/'manifest.json').read_text())
for file in manifest['files']:
    data=(base/file['name']).read_bytes()
    if len(data)!=file['size_bytes'] or hashlib.sha256(data).hexdigest()!=file['sha256']:
        raise ValueError('Mismatch: '+file['name'])
print('ACVP manifest OK:',manifest['quality'])

