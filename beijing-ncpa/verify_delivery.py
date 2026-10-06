"""Verify the Git commit's Vercel success, then independently hash all GLBs."""
from pathlib import Path
from urllib.request import urlopen,Request
import hashlib,json,datetime,subprocess,sys,concurrent.futures,argparse
HERE=Path(__file__).resolve().parent
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('revision',nargs='?',default='HEAD')
parser.add_argument('--no-write',action='store_true',help='Verify a final presentation commit without altering the committed evidence record.')
args=parser.parse_args()
sha=subprocess.check_output(['git','rev-parse',args.revision],cwd=HERE,text=True).strip()
status_url=f'https://api.github.com/repos/tanghaojie/sample-data/commits/{sha}/status'
with urlopen(Request(status_url,headers={'User-Agent':'NCPA-asset-delivery'}),timeout=40) as response:status=json.load(response)
vercel=next((s for s in status['statuses'] if s['context']=='Vercel'),None)
if not vercel or vercel['state']!='success':
    print(json.dumps({'commit':sha,'vercelState':vercel['state'] if vercel else 'not_reported','detail':vercel.get('description') if vercel else None},ensure_ascii=False));sys.exit(2)
def check(filename):
    url='https://sample-data-jt.vercel.app/beijing-ncpa/'+filename
    with urlopen(Request(url,headers={'Origin':'https://cyber-sight-geo.vercel.app'}),timeout=75) as response:
        data=response.read();headers={k.lower():v for k,v in response.headers.items()};code=response.status
    local=(HERE/filename).read_bytes();digest=hashlib.sha256(data).hexdigest()
    assert code==200 and headers['content-type'].split(';')[0]=='model/gltf-binary'
    assert headers.get('access-control-allow-origin')=='*'
    assert len(data)==len(local) and digest==hashlib.sha256(local).hexdigest()
    return {'filename':filename,'url':url,'httpStatus':code,'mime':'model/gltf-binary','cors':'*','bytes':len(data),'sha256':digest,'localRemoteHashMatch':True}
files=['beijing-ncpa.glb','beijing-ncpa-balanced.glb','beijing-ncpa-compatible.glb']
assets=list(concurrent.futures.ThreadPoolExecutor(3).map(check,files))
p=HERE/'delivery-verification.json'
record=json.loads(p.read_text('utf-8')) if p.exists() else {}
record.update({'repository':'https://github.com/tanghaojie/sample-data','publishedCommit':sha,'vercelState':'success','deploymentUrl':vercel['target_url'],'assets':assets,'verifiedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat()})
record.setdefault('browserVerification',{'status':'pending','url':'https://cyber-sight-geo.vercel.app/geo.html'})
if not args.no_write:p.write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'commit':sha,'vercelState':'success','deploymentUrl':vercel['target_url'],'assetsVerified':len(assets),'allHashesMatch':True,'recordWritten':not args.no_write},ensure_ascii=False))
