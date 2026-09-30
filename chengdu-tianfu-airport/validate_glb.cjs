const fs=require('fs'),path=require('path'),crypto=require('crypto');
const b=fs.readFileSync(path.join(__dirname,'chengdu-tianfu-airport.glb'));
function ok(c,m){if(!c)throw new Error(m)}
ok(b.toString('ascii',0,4)==='glTF','magic');ok(b.readUInt32LE(4)===2,'version');ok(b.readUInt32LE(8)===b.length,'byte length');
const jl=b.readUInt32LE(12),g=JSON.parse(b.toString('utf8',20,20+jl)),start=20+jl+8;
ok(!g.buffers.some(x=>x.uri),'external buffers');ok(!(g.images||[]).some(x=>x.uri),'external images');ok(!g.cameras?.length,'camera export');ok(!g.extensions?.KHR_lights_punctual,'light export');ok(!(g.extensionsUsed||[]).includes('KHR_materials_unlit'),'unlit');
const lo=[Infinity,Infinity,Infinity],hi=[-Infinity,-Infinity,-Infinity];let triangles=0,verts=0,degenerate=0;
function accessor(i){const a=g.accessors[i],v=g.bufferViews[a.bufferView];return {a,v,base:start+(v.byteOffset||0)+(a.byteOffset||0)}}
for(const mesh of g.meshes)for(const p of mesh.primitives){
 ok(p.mode===undefined||p.mode===4,'non-triangle primitive');const {a,v,base}=accessor(p.attributes.POSITION);ok(a.componentType===5126&&a.type==='VEC3','positions');
 for(let j=0;j<a.count;j++)for(let c=0;c<3;c++){let f=b.readFloatLE(base+j*(v.byteStride||12)+c*4);ok(Number.isFinite(f),'nonfinite');lo[c]=Math.min(lo[c],f);hi[c]=Math.max(hi[c],f)}
 const q=accessor(p.indices);ok(q.a.count%3===0,'index count');const bytes={5121:1,5123:2,5125:4}[q.a.componentType];ok(bytes,'index component');for(let j=0;j<q.a.count;j++){const off=q.base+j*bytes;const i=bytes===4?b.readUInt32LE(off):bytes===2?b.readUInt16LE(off):b.readUInt8(off);ok(i<a.count,'index bounds')}
 triangles+=q.a.count/3;verts+=a.count;
 if(p.attributes.NORMAL!==undefined){const n=accessor(p.attributes.NORMAL);for(let j=0;j<n.a.count;j++){let sum=0;for(let c=0;c<3;c++){const x=b.readFloatLE(n.base+j*(n.v.byteStride||12)+c*4);ok(Number.isFinite(x),'normal');sum+=x*x}ok(sum>.8&&sum<1.2,'unit normal')}}
}
ok(Math.abs(lo[1])<.01,'bottom ground origin');ok(hi[1]>34&&hi[1]<50,'meter height');ok(Math.abs(hi[0]-lo[0]-2100)<1,'site width');
const emissive=g.materials.filter(m=>m.emissiveFactor?.some(x=>x>0)).map(m=>({name:m.name,factor:m.emissiveFactor,strength:m.extensions?.KHR_materials_emissive_strength?.emissiveStrength||1}));ok(emissive.length>=6,'night channels');
const geo=JSON.parse(fs.readFileSync(path.join(__dirname,'geometry-report.json')));ok(geo.gates.length===83,'83 gates');
const result={asset:g.asset,bytes:b.length,sha256:crypto.createHash('sha256').update(b).digest('hex'),meshCount:g.meshes.length,materialCount:g.materials.length,triangles,vertices:verts,gates:geo.gates.length,bounds:{min:lo,max:hi},extensionsUsed:g.extensionsUsed||[],extensionsRequired:g.extensionsRequired||[],emissive};
fs.writeFileSync(path.join(__dirname,'validation.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result,null,2));
