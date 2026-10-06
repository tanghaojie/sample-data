"""Package the local editable deliverable and retained references, without drafts/logs."""
from pathlib import Path
import hashlib,json,zipfile
from PIL import Image

ROOT=Path(__file__).resolve().parent
names=['day','night','sunset','aerial','detail','entrance','elevation']
log=(ROOT/'render-all.log').read_text('utf-8',errors='replace')
assert all('NCPA_RENDER_COMPLETE '+name in log for name in names)
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
files=[]
for name in names:
    p=ROOT/'renders'/f'{name}.png'
    with Image.open(p) as im:
        assert im.size==(1800,1200);im.verify()
    files.append({'file':f'renders/{name}.png','bytes':p.stat().st_size,'sha256':digest(p),'dimensions_px':[1800,1200]})
manifest={'renderer':'Blender 5.2.1 LTS / Cycles CPU / 32 samples / denoised','sourceBlendSha256':digest(ROOT/'beijing-ncpa.blend'),'modelGlbSha256':digest(ROOT/'beijing-ncpa.glb'),'files':files,'scope':'Presentation images with artificial lighting and self-reflection; distinct from Geo browser proof.'}
(ROOT/'renders'/'render-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
package=ROOT/'beijing-ncpa-delivery.zip'
selected=[]
for p in ROOT.rglob('*'):
    if not p.is_file():continue
    rel=p.relative_to(ROOT)
    if any(s in {'__pycache__','node_modules'} for s in rel.parts):continue
    if p.name.startswith('draft-') or p.suffix in {'.zip','.log','.blend1','.html','.txt'}:continue
    if p.suffix.lower() not in {'.glb','.blend','.json','.py','.cjs','.md','.png','.jpg'} and p.name not in {'architectural-record-2008.pdf','.gitignore'}:continue
    selected.append(p)
with zipfile.ZipFile(package,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
    for p in sorted(selected):archive.write(p,'beijing-ncpa/'+p.relative_to(ROOT).as_posix())
with zipfile.ZipFile(package) as archive:
    assert archive.testzip() is None
    assert len(archive.namelist())==len(selected)
print(json.dumps({'archive':str(package),'files':len(selected),'bytes':package.stat().st_size,'rendersVerified':len(files)},ensure_ascii=False))
