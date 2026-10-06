"""Remove unused tangent streams and repack GLB buffers without changing appearance.

Blender exports tangents on every mesh when requested. Untextured submillimetre
paving seams can contain unused zero tangents. Only normal-mapped primitives
need tangent space; keep those verbatim and discard unused streams.
"""
import json,struct,sys
from pathlib import Path

def finalize(path):
    path=Path(path);raw=path.read_bytes();jl=struct.unpack_from('<I',raw,12)[0]
    doc=json.loads(raw[20:20+jl]);binary=raw[20+jl+8:]
    assert not doc.get('animations') and not doc.get('skins')
    for mesh in doc['meshes']:
        for p in mesh['primitives']:
            if not doc['materials'][p['material']].get('normalTexture'):
                p['attributes'].pop('TANGENT',None)
    used=set()
    for mesh in doc['meshes']:
        for p in mesh['primitives']:
            used.update(p['attributes'].values());used.add(p['indices'])
    indices=sorted(used);remap={old:new for new,old in enumerate(indices)}
    doc['accessors']=[doc['accessors'][i] for i in indices]
    for mesh in doc['meshes']:
        for p in mesh['primitives']:
            p['attributes']={k:remap[v] for k,v in p['attributes'].items()};p['indices']=remap[p['indices']]
    used_views={a['bufferView'] for a in doc['accessors']}
    used_views.update(i['bufferView'] for i in doc.get('images',[]))
    ids=sorted(used_views);vmap={old:new for new,old in enumerate(ids)}
    new_binary=bytearray();views=[]
    for old in ids:
        v=doc['bufferViews'][old].copy();start=v.get('byteOffset',0)
        while len(new_binary)%4:new_binary.append(0)
        v['byteOffset']=len(new_binary);new_binary.extend(binary[start:start+v['byteLength']]);views.append(v)
    for a in doc['accessors']:a['bufferView']=vmap[a['bufferView']]
    for i in doc.get('images',[]):i['bufferView']=vmap[i['bufferView']]
    doc['bufferViews']=views;doc['buffers'][0]['byteLength']=len(new_binary)
    while len(new_binary)%4:new_binary.append(0)
    jb=json.dumps(doc,ensure_ascii=False,separators=(',',':')).encode('utf-8')
    jb+=b' '*((-len(jb))%4)
    result=struct.pack('<4sII',b'glTF',2,12+8+len(jb)+8+len(new_binary))+struct.pack('<I4s',len(jb),b'JSON')+jb+struct.pack('<I4s',len(new_binary),b'BIN\0')+new_binary
    path.write_bytes(result)
    print('NCPA_GLB_FINALIZED',path.name,len(raw),'->',len(result))

if __name__=='__main__':
    for p in sys.argv[1:]:finalize(p)
