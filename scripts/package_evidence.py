#!/usr/bin/env python3
import hashlib,json,pathlib,sys,xml.etree.ElementTree as ET,subprocess
root=pathlib.Path(__file__).resolve().parents[1]; folder=pathlib.Path(sys.argv[1])
cases=[]
for p in sorted(folder.glob('TEST-*.xml')):
    tree=ET.parse(p)
    for tc in tree.findall('.//testcase'):
        cases.append({'class':tc.get('classname'),'name':tc.get('name'),'seconds':tc.get('time'),'status':'FAIL' if tc.find('failure') is not None or tc.find('error') is not None else ('SKIP' if tc.find('skipped') is not None else 'PASS')})
(folder/'test-cases.json').write_text(json.dumps(cases,indent=2)+'\n')
source=[]
for base in ['src','scripts','tools','docs','README.docx','README.md','pom.xml','environment.lock.json']:
    p=root/base
    for file in ([p] if p.is_file() else sorted(p.rglob('*'))):
        if file.is_file() and '__pycache__' not in file.parts and 'LAB9_Resources' not in file.parts and not file.name.startswith(('LAB9', '.DS_Store')) and file.suffix not in {'.pyc','.p12','.pfx','.key'}: source.append({'name':str(file.relative_to(root)),'sha256':hashlib.sha256(file.read_bytes()).hexdigest()})
(folder/'source-manifest.json').write_text(json.dumps(source,indent=2)+'\n')
files=[{'name':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(folder.iterdir()) if p.is_file() and p.name!='checksums.json']
(folder/'checksums.json').write_text(json.dumps(files,indent=2)+'\n')
print('JUnit evidence:',len(cases),'cases;',sum(x['status']=='PASS' for x in cases),'passed')
