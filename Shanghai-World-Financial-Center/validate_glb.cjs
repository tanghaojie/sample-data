const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const filename = path.join(__dirname,'shanghai-world-financial-center.glb');
const b=fs.readFileSync(filename);
function assert(c,m){if(!c)throw new Error(m)}
assert(b.toString('ascii',0,4)==='glTF','magic');assert(b.readUInt32LE(4)===2,'version');assert(b.readUInt32LE(8)===b.length,'length');
const jsonLen=b.readUInt32LE(12),doc=JSON.parse(b.toString('utf8',20,20+jsonLen));
const binStart=20+jsonLen+8;
assert(!doc.buffers.some(x=>x.uri),'external buffers');assert(!(doc.images||[]).some(x=>x.uri),'external textures');
assert(!doc.cameras?.length,'cameras');assert(!doc.extensions?.KHR_lights_punctual,'lights');
assert(!(doc.extensionsUsed||[]).includes('KHR_materials_unlit'),'unlit');
let triangles=0,positions=0;
let lo=[Infinity,Infinity,Infinity],hi=[-Infinity,-Infinity,-Infinity];
for(const mesh of doc.meshes)for(const p of mesh.primitives){
 assert(p.mode===undefined||p.mode===4,'triangle mode');
 const a=doc.accessors[p.attributes.POSITION],v=doc.bufferViews[a.bufferView];
 assert(a.componentType===5126 && a.type==='VEC3','float vec3 positions');
 for(let i=0;i<a.count;i++)for(let c=0;c<3;c++){
  const x=b.readFloatLE(binStart+(v.byteOffset||0)+(a.byteOffset||0)+i*(v.byteStride||12)+c*4);
  assert(Number.isFinite(x),'nonfinite position');lo[c]=Math.min(lo[c],x);hi[c]=Math.max(hi[c],x);
 }
 positions+=a.count;triangles+=doc.accessors[p.indices].count/3;
}
assert(Math.abs(hi[1]-lo[1]-492)<.01,'height in exported Y axis');assert(Math.abs(lo[1])<.01,'ground origin');
const emissive=doc.materials.filter(m=>m.emissiveFactor?.some(v=>v>0)).map(m=>({name:m.name,factor:m.emissiveFactor,strength:m.extensions?.KHR_materials_emissive_strength?.emissiveStrength||1}));
assert(emissive.length>=5,'night channels');
const result={asset:doc.asset,bytes:b.length,sha256:crypto.createHash('sha256').update(b).digest('hex'),meshCount:doc.meshes.length,materialCount:doc.materials.length,triangles,positions,bounds:{min:lo,max:hi},extensions:doc.extensionsUsed||[],emissive};
fs.writeFileSync(path.join(__dirname,'validation.json'),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify(result,null,2));
