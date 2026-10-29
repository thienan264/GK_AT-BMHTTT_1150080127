#!/usr/bin/env python3
"""Fetch pinned NIST generator source to an explicit temporary destination (large download).
Not needed for ordinary Java tests: generated vectors are already frozen in the project.
"""
import argparse,pathlib,urllib.request,tempfile,zipfile,shutil
COMMIT='975de31eb83d87039ec88934fdc47d8c312b892d'
def main():
 p=argparse.ArgumentParser();p.add_argument('--destination',required=True,type=pathlib.Path);a=p.parse_args()
 root=a.destination.resolve()/('ACVP-Server-'+COMMIT)
 if root.exists():raise SystemExit('Destination exists; use it or select a new directory')
 prefixes=['_config/','gen-val/samples/GenValAppRunner/src/','gen-val/samples/NIST.CVP.ACVTS.Orleans.ServerHost/']
 prefixes+=['gen-val/src/'+name+'/src/' for name in ['common','crypto','oracle','orleans','generation']]
 with tempfile.TemporaryFile() as archive:
  with urllib.request.urlopen('https://codeload.github.com/usnistgov/ACVP-Server/zip/'+COMMIT,timeout=60) as response:shutil.copyfileobj(response,archive)
  archive.seek(0)
  with zipfile.ZipFile(archive) as z:
   for item in z.infolist():
    rel='/'.join(item.filename.split('/')[1:])
    if item.is_dir() or not (rel.startswith(tuple(prefixes)) or rel in ['README.md','gen-val/samples/sharedappsettings.json']):continue
    path=root/rel;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(z.read(item))
 for name in ['Directory.Build.props','Directory.Packages.props']:shutil.copyfile(root/'_config'/name,root/name)
 print('Source ready:',root)
if __name__=='__main__':main()
