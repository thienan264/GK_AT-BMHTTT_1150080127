#!/usr/bin/env python3
"""Provision persistent keys explicitly; run local loopback HTTP without passwords in argv."""
import argparse, getpass, os, subprocess, sys, hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
p=argparse.ArgumentParser()
p.add_argument('action', choices=['init','run','fingerprints','trust'])
p.add_argument('--keys',type=Path,default=ROOT/'.local-keys')
p.add_argument('--role',choices=['combined','sender','receiver'],default='combined')
p.add_argument('--port',type=int,default=8080)
p.add_argument('--identity',choices=['alice','bob'])
p.add_argument('--certificate',type=Path)
p.add_argument('--fingerprint',help='Expected SHA-256 of public key DER, confirmed out of band')
a=p.parse_args();a.keys=a.keys.resolve()
env=os.environ.copy()
if sys.platform=='darwin':
    env['JAVA_HOME']=subprocess.check_output(['/usr/libexec/java_home','-v','21'],text=True).strip()
    env['PATH']=str(Path(env['JAVA_HOME'])/'bin')+os.pathsep+env['PATH']
def run(args):subprocess.run(args,cwd=ROOT,env=env,check=True)
def public_fingerprint(path):
    pem=subprocess.check_output(['openssl','x509','-in',str(path),'-pubkey','-noout'],env=env)
    der=subprocess.check_output(['openssl','pkey','-pubin','-outform','DER'],input=pem,env=env)
    return hashlib.sha256(der).hexdigest().upper()
if a.action not in ['fingerprints','trust']:
    password=env.get('DEMO_KEYSTORE_PASSWORD') or getpass.getpass('Mật khẩu keystore (ít nhất 12 ký tự): ')
    if len(password)<12:sys.exit('Cần mật khẩu ít nhất 12 ký tự.')
    if a.action=='init' and not env.get('DEMO_KEYSTORE_PASSWORD'):
        if password!=getpass.getpass('Nhập lại mật khẩu: '):sys.exit('Mật khẩu không trùng.')
    env['DEMO_KEYSTORE_PASSWORD']=password
if a.action=='init':
    if a.keys.exists() and any(a.keys.iterdir()):sys.exit('Thư mục đã có dữ liệu. Không ghi đè hoặc tự thay khoá. Dùng run, hoặc chọn thư mục mới bằng --keys.')
    a.keys.mkdir(parents=True,exist_ok=True);a.keys.chmod(0o700)
    for name in ['alice','bob']:
        args=['keytool','-genkeypair','-alias',name,'-keyalg','RSA','-keysize','2048','-sigalg','SHA256withRSA',
              '-dname','CN='+name,'-validity','365', '-storetype','PKCS12',
              '-keystore',str(a.keys/(name+'.p12')),'-storepass:env','DEMO_KEYSTORE_PASSWORD']
        run(args);(a.keys/(name+'.p12')).chmod(0o600)
        run(['keytool','-exportcert','-rfc','-alias',name,'-keystore',str(a.keys/(name+'.p12')),
             '-storepass:env','DEMO_KEYSTORE_PASSWORD','-file',str(a.keys/(name+'.cer'))])
    print('Đã tạo khoá. Sao lưu .p12 an toàn; chia sẻ .cer, không chia sẻ .p12.')
elif a.action=='trust':
    if not (a.identity and a.certificate and a.fingerprint):sys.exit('trust cần --identity, --certificate, --fingerprint đã đối chiếu qua kênh tin cậy.')
    actual=public_fingerprint(a.certificate)
    if actual!=a.fingerprint.replace(':','').upper():sys.exit('Fingerprint không khớp. Không nhập khoá.')
    if not a.keys.is_dir():sys.exit('Thư mục khoá chưa tồn tại.')
    target=a.keys/(a.identity+'.cer')
    if target.exists() and target.read_bytes()!=a.certificate.read_bytes():
        backup=target.with_suffix('.cer.previous')
        if backup.exists():sys.exit('Đã có bản sao .cer.previous, hãy quản lý bản sao trước khi đổi tiếp.')
        backup.write_bytes(target.read_bytes())
    target.write_bytes(a.certificate.read_bytes())
    print('Đã nhập public key đã đối chiếu. Khởi động lại ứng dụng để nạp cấu hình tin cậy.')
elif a.action=='fingerprints':
    for name in ['alice','bob']:
        print(name+' SHA-256(public key DER): '+public_fingerprint(a.keys/(name+'.cer')),flush=True)
else:
    # Initialization is never implicit: missing/corrupt keys cause startup to fail.
    run(['mvn','-q','compile','exec:java','-Ddemo.keys='+str(a.keys),'-Ddemo.role='+a.role,'-Dexec.args='+str(a.port)])
