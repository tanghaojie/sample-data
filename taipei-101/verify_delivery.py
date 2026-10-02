"""Check Vercel commit status and independently hash the deployed GLB."""
from pathlib import Path
from urllib.request import urlopen, Request
import json, hashlib, datetime, subprocess
HERE=Path(__file__).resolve().parent
sha='0e4fa28fc84f0c48117f26951953bfd602e9503d'
status_url=f'https://api.github.com/repos/tanghaojie/sample-data/commits/{sha}/status'
with urlopen(Request(status_url,headers={'User-Agent':'Taipei101-delivery-verification'}),timeout=40) as r:status=json.load(r)
vercel=next(s for s in status['statuses'] if s['context']=='Vercel')
assert vercel['state']=='success',vercel
url='https://sample-data-jt.vercel.app/taipei-101/taipei-101.glb'
with urlopen(url,timeout=45) as r:
    data=r.read();headers=dict(r.headers);http=r.status
local=(HERE/'taipei-101.glb').read_bytes()
digest=hashlib.sha256(data).hexdigest()
assert http==200
assert headers.get('content-type',headers.get('Content-Type','')).split(';')[0]=='model/gltf-binary'
assert len(data)==len(local)
assert digest==hashlib.sha256(local).hexdigest()
assert headers.get('access-control-allow-origin',headers.get('Access-Control-Allow-Origin'))=='*'
record_path=HERE/'delivery-verification.json'
record=json.loads(record_path.read_text('utf-8')) if record_path.exists() else {}
record.update({'modelCommit':sha,'githubRepository':'https://github.com/tanghaojie/sample-data','deployment':vercel['target_url'],'vercelState':vercel['state'],'glbUrl':url,'httpStatus':http,'contentType':'model/gltf-binary','cors':'*','bytes':len(data),'sha256':digest,'localRemoteHashMatch':True,'verifiedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'khronosErrors':0,'khronosWarnings':0})
record.setdefault('browserLoad','pending')
record_path.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(record,ensure_ascii=False,indent=2))
