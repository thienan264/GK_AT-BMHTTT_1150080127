#!/usr/bin/env python3
"""Exercise the running local web demo; never contacts an external host."""
import urllib.request, urllib.error, json, sys, os
from pathlib import Path
BASE=os.environ.get('DEMO_BASE','http://127.0.0.1:8080')
def request(path,data=None):
    req=urllib.request.Request(BASE+path,data=data)
    try:
        with urllib.request.urlopen(req,timeout=20) as r:return r.status,r.read()
    except urllib.error.HTTPError as e:return e.code,e.read()
def api(path,data=None):
    code,body=request(path,data);return code,json.loads(body)
assert api('/api/status')[1]['mode'].startswith('Local demo')
assert b'expected' in request('/')[1]
for gzip in ['false','true']:
    data=('Dữ liệu thử công khai '.encode()*100)+bytes(range(256))
    code,enc=api('/api/encrypt?filename=public-test.bin&gzip='+gzip,data);assert code==200 and enc['success']
    pkg=request(enc['downloadUrl'])[1]
    code,dec=api('/api/decrypt',pkg);assert code==200 and dec['success']
    assert request(dec['downloadUrl'])[1]==data
    code,wrong=api('/api/decrypt-unauthorized',pkg);assert code==200 and wrong['rejected']
    changed=bytearray(pkg);changed[-1]^=1
    code,bad=api('/api/decrypt',bytes(changed));assert code==400 and not bad['success'] and 'downloadUrl' not in bad
    code,bad=api('/api/decrypt',pkg+b'0');assert code==400 and not bad['success']
code,checks=api('/api/nist');assert code==200 and checks['success'] and checks['total']==140
assert all(r['status']=='PASS' for r in checks['testCases'])
message='HTTP localhost PASS: baseline/GZIP round-trip, downloads, wrong key, changed signature, trailing bytes, 140 live reference cases.'
print(message)
if len(sys.argv)>1:
    from pathlib import Path
    Path(sys.argv[1]).write_text(message+'\n')
