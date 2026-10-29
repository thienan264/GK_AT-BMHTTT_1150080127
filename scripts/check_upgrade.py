#!/usr/bin/env python3
"""Local HTTP, public-key trust, isolated roles and restart persistence.
Creates only temporary test keys, never touches the operator's identities.
"""
import os, sys, subprocess, tempfile, secrets, shutil, time, json, urllib.request, urllib.error, signal
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
env=os.environ.copy();env['DEMO_KEYSTORE_PASSWORD']=secrets.token_urlsafe(24)
if sys.platform=='darwin':
    env['JAVA_HOME']=subprocess.check_output(['/usr/libexec/java_home','-v','21'],text=True).strip()
    env['PATH']=str(Path(env['JAVA_HOME'])/'bin')+os.pathsep+env['PATH']
log=[]
def record(s):print(s,flush=True);log.append(s)
with tempfile.TemporaryDirectory(prefix='hybrid-local-') as tmp:
    tmp=Path(tmp);keys=tmp/'keys'
    subprocess.run([sys.executable,'scripts/demo.py','init','--keys',str(keys)],cwd=ROOT,env=env,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
    for role,private in [('sender','alice'),('receiver','bob')]:
        folder=tmp/role;folder.mkdir()
        for name in ['alice.cer','bob.cer',private+'.p12']:shutil.copy2(keys/name,folder/name)
    cp=str(ROOT/'target/classes')+os.pathsep+str(Path.home()/'.m2/repository/com/google/code/gson/gson/2.10.1/gson-2.10.1.jar')
    fingerprints=subprocess.check_output([sys.executable,'scripts/demo.py','fingerprints','--keys',str(keys)],cwd=ROOT,env=env,text=True)
    alicefp=fingerprints.splitlines()[0].split(': ',1)[1]
    destination=tmp/'receiver/alice.cer';beforecert=destination.read_bytes()
    trustcmd=[sys.executable,'scripts/demo.py','trust','--keys',str(tmp/'receiver'),'--identity','alice','--certificate',str(keys/'alice.cer'),'--fingerprint']
    wrong=subprocess.run(trustcmd+['00'*32],cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    assert wrong.returncode!=0 and destination.read_bytes()==beforecert
    subprocess.run(trustcmd+[alicefp],cwd=ROOT,env=env,check=True,stdout=subprocess.DEVNULL)
    record('PASS: public-key import rejects mismatched fingerprint and accepts explicitly confirmed fingerprint.')
    def req(path,data=None,origin=None,headers=None):
        request_headers=dict(headers or {})
        if origin is not None:request_headers['Origin']=origin
        r=urllib.request.Request('http://127.0.0.1:18080'+path,data=data,headers=request_headers)
        try:
            with urllib.request.urlopen(r,timeout=10) as response:return response.status,response.read(),response.headers
        except urllib.error.HTTPError as e:return e.code,e.read(),e.headers
    def api(path,data=None,**kw):
        code,body,headers=req(path,data,**kw);return code,json.loads(body),headers
    def start(role):
        output=open(tmp/'server.log','ab')
        command=([sys.executable,'scripts/demo.py','run','--keys',str(tmp/role),'--role',role,'--port','18080'] if role=='combined' else
            ['java','-Ddemo.keys='+str(tmp/role),'-Ddemo.role='+role,'-cp',cp,'vn.edu.atbm.mssv1150080127.web.WebServerApp','18080'])
        proc=subprocess.Popen(command,cwd=ROOT,env=env,stdout=output,stderr=output,start_new_session=True)
        output.close()
        for _ in range(100):
            if proc.poll() is not None:raise RuntimeError((tmp/'server.log').read_text())
            try:
                if api('/api/status')[0]==200:return proc
            except (OSError,urllib.error.URLError):pass
            time.sleep(.1)
        stop(proc);raise RuntimeError('Local HTTP startup timed out')
    def stop(proc):os.killpg(proc.pid,signal.SIGTERM);proc.wait(timeout=10)
    payload='Dữ liệu kiểm tra restart'.encode()*100
    proc=start('sender')
    try:
        assert api('/api/status')[1]['role']=='sender'
        code,enc,_=api('/api/encrypt?filename=restart.txt&gzip=true',payload);assert code==200,enc
        package=req(enc['downloadUrl'])[1]
        assert api('/api/decrypt',package)[0]==400
        assert api('/api/encrypt',payload,origin='http://evil.example')[0]==403
        assert api('/api/status',headers={'Host':'evil.example:18080'})[0]==403
        assert api('/api/status',headers={'Sec-Fetch-Site':'cross-site'})[0]==403
        assert api('/api/status',origin='https://127.0.0.1:18080')[0]==403
        assert api('/api/status',origin='http://127.0.0.1:18080')[0]==200
        record('PASS: local HTTP only; cross-origin POST rejected; sender has no Bob private key; no TLS files required.')
    finally:stop(proc)
    for iteration in range(2):
        proc=start('receiver')
        try:
            code,dec,_=api('/api/decrypt',package);assert code==200 and dec['senderVerified'],dec
            code,body,headers=req(dec['downloadUrl']);assert body==payload and headers['Cache-Control']=='no-store'
            assert api('/api/encrypt',payload)[0]==400
            changed=bytearray(package);changed[-1]^=1
            code,bad,_=api('/api/decrypt',bytes(changed));assert code==400 and 'downloadUrl' not in bad
            assert api('/api/decrypt-unauthorized',package)[1]['rejected']
            assert api('/api/decrypt',package+b'x')[0]==400
            assert api('/api/nist')[1]['passed']==140
            record('PASS: receiver restart '+str(iteration+1)+' decrypts saved sender package; tampering/wrong recipient/trailing bytes rejected; 140 reference cases pass.')
        finally:stop(proc)
    shutil.copytree(keys,tmp/'combined')
    proc=start('combined')
    try:
        smokeenv=env.copy();smokeenv['DEMO_BASE']='http://127.0.0.1:18080'
        smoke=subprocess.check_output([sys.executable,'scripts/smoke_web.py'],cwd=ROOT,env=smokeenv,text=True)
        record('PASS: documented demo.py run launcher starts local HTTP with configured identities.')
        record(smoke.strip())
        code,enc,_=api('/api/encrypt?filename=empty.bin',b'');assert code==200,enc
        code,dec,_=api('/api/decrypt',req(enc['downloadUrl'])[1]);assert code==200,dec
        assert req(dec['downloadUrl'])[1]==b''
        record('PASS: zero-byte file survives local HTTP signed round-trip.')
    finally:stop(proc)
    # Wrong password fails closed and must never replace existing key files.
    import hashlib
    path=tmp/'receiver/bob.p12';before=hashlib.sha256(path.read_bytes()).hexdigest()
    badenv=env.copy();badenv['DEMO_KEYSTORE_PASSWORD']='incorrect-password'
    failed=subprocess.run(['java','-Ddemo.keys='+str(tmp/'receiver'),'-Ddemo.role=receiver','-cp',cp,
        'vn.edu.atbm.mssv1150080127.web.WebServerApp','18080'],cwd=ROOT,env=badenv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=15)
    assert failed.returncode!=0 and hashlib.sha256(path.read_bytes()).hexdigest()==before
    record('PASS: wrong keystore password refuses startup without replacing keys.')
if len(sys.argv)>1:Path(sys.argv[1]).write_text('\n'.join(log)+'\n')
