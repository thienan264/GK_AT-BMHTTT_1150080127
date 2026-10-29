#!/usr/bin/env python3
"""Run unmodified NIST GenVal binaries at a pinned source commit. Requires .NET8 and a running local Orleans host."""
import argparse,datetime,hashlib,json,pathlib,subprocess,tempfile,shutil
ROOT=pathlib.Path(__file__).resolve().parents[1]
COMMIT='975de31eb83d87039ec88934fdc47d8c312b892d'
def main():
 p=argparse.ArgumentParser();p.add_argument('--source',required=True,type=pathlib.Path);p.add_argument('--validate',action='store_true');args=p.parse_args()
 source=args.source.resolve();runner=source/'gen-val/samples/GenValAppRunner/src/bin/Release/net8.0/NIST.CVP.ACVTS.Generation.GenValApp.dll'
 if not runner.exists():raise SystemExit('Build NIST GenValApp and ServerHost first; see tools/nist-generation/config.json')
 for folder in ['generated-kts-sha256','generated-aes256']:
  target=ROOT/'src/test/resources/nist-acvp'/folder
  command=['dotnet',str(runner)]
  if args.validate:
   if folder!='generated-kts-sha256':continue
   command+=['-n',str(target/'internalProjection.json'),'-b',str(target/'iutResponses.json')]
  else:command+=['-g',str(target/'registration.json')]
  label='validation' if args.validate else 'generation'
  with (target/(label+'.log')).open('w') as log:
   r=subprocess.run(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=300)
  if r.returncode:raise SystemExit(f'{folder}: see {label}.log (exit {r.returncode})')
  if args.validate:
   verdict=json.loads((target/'validation.json').read_text())
   if verdict.get('disposition')!='passed' or len(verdict.get('tests',[]))!=20 or any(t['result']!='passed' for t in verdict['tests']):
    raise SystemExit('NIST validator did not pass all 20 cases')
   # Prove the NIST validator actually rejects a wrong Java response.
   wrong=json.loads((target/'iutResponses.json').read_text())
   answer=wrong['testGroups'][0]['tests'][0]
   answer['dkm']=('01' if answer['dkm'].startswith('00') else '00')+answer['dkm'][2:]
   with tempfile.TemporaryDirectory(prefix='nist-negative-') as temp:
    temp=pathlib.Path(temp);bad=temp/'iutResponses.json';bad.write_text(json.dumps(wrong,indent=2)+'\n')
    with (target/'negative-validation.log').open('w') as log:
     subprocess.run(['dotnet',str(runner),'-n',str(target/'internalProjection.json'),'-b',str(bad)],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,timeout=120)
    negative=json.loads((temp/'validation.json').read_text())
    if negative.get('disposition')=='passed' or not any(t['result']!='passed' for t in negative.get('tests',[])):
     raise SystemExit('Negative control was incorrectly accepted')
    shutil.copyfile(temp/'validation.json',target/'negative-validation.json')
    shutil.copyfile(bad,target/'negativeResponses.json')
   paths=['src/main/java/vn/edu/atbm/mssv1150080127/crypto/RsaKeyManager.java','src/main/java/vn/edu/atbm/mssv1150080127/crypto/RsaOaep.java','src/main/java/vn/edu/atbm/mssv1150080127/util/KtsOaepVectors.java']
   evidence={'validated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'kind':'local NIST GenVal validator, not NIST-issued validation','passed_cases':20,'wrap_cases':10,'unwrap_cases':10,'negative_control':'one submitted dkm byte modified; validator must reject','source_sha256':{path:hashlib.sha256((ROOT/path).read_bytes()).hexdigest() for path in paths},'iutResponses_sha256':hashlib.sha256((target/'iutResponses.json').read_bytes()).hexdigest(),'validation_sha256':hashlib.sha256((target/'validation.json').read_bytes()).hexdigest()}
   (target/'java-validation-evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
  if not args.validate:
   hashes={}
   for name in ['NIST.CVP.ACVTS.Generation.GenValApp.dll','NIST.CVP.ACVTS.Libraries.Generation.dll','NIST.CVP.ACVTS.Libraries.Crypto.dll']:
    hashes[name]=hashlib.sha256((runner.parent/name).read_bytes()).hexdigest()
   origin={'kind':'locally-generated-by-NIST-GenVal','repository':'https://github.com/usnistgov/ACVP-Server','commit':COMMIT,'generated_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'command':['dotnet','<pinned-source>/gen-val/samples/GenValAppRunner/src/bin/Release/net8.0/NIST.CVP.ACVTS.Generation.GenValApp.dll','-g',folder+'/registration.json'],'dotnet':subprocess.check_output(['dotnet','--version'],text=True).strip(),'generator_binary_sha256':hashes,'notice':'Generated locally using NIST source, NOT downloaded pre-existing vectors and NOT NIST certification. Registration selects parameters; NIST generator computes independent expected answers. Source code unmodified; config props copied as documented by upstream.'}
   (target/'origin.json').write_text(json.dumps(origin,indent=2)+'\n')
  print(folder,label,'OK',flush=True)
if __name__=='__main__':main()
