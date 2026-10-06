// Asset validation only. No frontend/browser tests.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const validator = require('gltf-validator');
const directory = __dirname;
const filenames = process.argv.slice(2).length ? process.argv.slice(2) : ['beijing-ncpa.glb'];
function rotate(p, q) {
  const [x,y,z,w]=q, [a,b,c]=p;
  const tx=2*(y*c-z*b), ty=2*(z*a-x*c), tz=2*(x*b-y*a);
  return [a+w*tx+y*tz-z*ty,b+w*ty+z*tx-x*tz,c+w*tz+x*ty-y*tx];
}
async function check(filename) {
  const b=fs.readFileSync(path.join(directory,filename));
  assert.equal(b.toString('ascii',0,4),'glTF'); assert.equal(b.readUInt32LE(4),2);assert.equal(b.readUInt32LE(8),b.length);
  const jl=b.readUInt32LE(12),d=JSON.parse(b.toString('utf8',20,20+jl));
  const binary=20+jl+8;
  assert(!(d.buffers||[]).some(x=>x.uri));assert(!(d.images||[]).some(x=>x.uri));
  assert(!d.cameras?.length);assert(!d.extensions?.KHR_lights_punctual);assert(!d.animations?.length);
  assert(!d.extensionsRequired?.length);
  assert(!(d.extensionsUsed||[]).some(x=>['KHR_materials_unlit','KHR_materials_transmission','KHR_materials_volume'].includes(x)));
  const roots=d.nodes.filter(n=>n.name==='GEO_ROOT');assert.equal(roots.length,1);
  const root=roots[0],meta=root.extras;
  assert.equal(meta.horizontal_crs,'EPSG:4326');assert.equal(meta.units,'meters');assert.equal(meta.geo_metadata_version,1);
  assert.equal(meta.coordinate_accuracy,'approximate');assert(!('ellipsoid_height_m' in meta));assert.equal(meta.height_m,46.285);
  assert.equal(meta.longitude_wgs84,116.38355);assert.equal(meta.latitude_wgs84,39.90334);
  const placement=JSON.parse(fs.readFileSync(path.join(directory,'placement.json'),'utf8'));
  for (const [k,v] of Object.entries(meta))assert.equal(placement[k],v,`Sidecar mismatch ${k}`);
  const transformedX=rotate([1,0,0],root.rotation);assert(Math.abs(transformedX[2]-1)<1e-6,'East axis');
  const transformedY=rotate([0,0,-1],root.rotation);assert(Math.abs(transformedY[0]-1)<1e-6,'North axis');
  let vertices=0,triangles=0,normalMappedPrimitives=0,texturedPrimitives=0;
  const lo=[Infinity,Infinity,Infinity],hi=[-Infinity,-Infinity,-Infinity];
  const envelopeLo=[Infinity,Infinity,Infinity],envelopeHi=[-Infinity,-Infinity,-Infinity];
  for (const m of d.meshes)for (const p of m.primitives) {
    assert(p.mode===undefined||p.mode===4);assert(p.attributes.NORMAL!==undefined);
    const material=d.materials[p.material];
    if (material.normalTexture){assert(p.attributes.TANGENT!==undefined,'Missing authored tangent');normalMappedPrimitives++;}
    if (material.normalTexture||material.pbrMetallicRoughness?.baseColorTexture||material.pbrMetallicRoughness?.metallicRoughnessTexture) {
      assert(p.attributes.TEXCOORD_0!==undefined);texturedPrimitives++;
    }
    const a=d.accessors[p.attributes.POSITION],v=d.bufferViews[a.bufferView];assert.equal(a.componentType,5126);
    const envelope=/Titanium panels|glass panes|Shell joint backing/.test(m.name);
    for(let i=0;i<a.count;i++) {
      const local=[0,1,2].map(c=>b.readFloatLE(binary+(v.byteOffset||0)+(a.byteOffset||0)+i*(v.byteStride||12)+c*4));
      assert(local.every(Number.isFinite));const point=rotate(local,root.rotation);
      for(let c=0;c<3;c++){lo[c]=Math.min(lo[c],point[c]);hi[c]=Math.max(hi[c],point[c]);if(envelope){envelopeLo[c]=Math.min(envelopeLo[c],point[c]);envelopeHi[c]=Math.max(envelopeHi[c],point[c]);}}
    }
    vertices+=a.count;triangles+=d.accessors[p.indices].count/3;
  }
  assert(Math.abs(envelopeHi[1]-46.285)<.03,'Published envelope height');
  assert(Math.abs(envelopeHi[2]-envelopeLo[2]-212.2)<.15,'East-west span');
  assert(Math.abs(envelopeHi[0]-envelopeLo[0]-143.64)<.2,'North-south span');
  const emissive=d.materials.filter(m=>m.emissiveFactor?.some(v=>v>0)).map(m=>({name:m.name,factor:m.emissiveFactor,strength:m.extensions?.KHR_materials_emissive_strength?.emissiveStrength||1}));
  assert(emissive.length>=4);
  const report=await validator.validateBytes(new Uint8Array(b),{uri:filename,maxIssues:1000});
  fs.writeFileSync(path.join(directory,filename.replace('.glb','-khronos.json')),JSON.stringify(report,null,2)+'\n');
  assert.equal(report.issues.numErrors,0,'Khronos errors');assert.equal(report.issues.numWarnings,0,'Khronos warnings');
  const result={filename,bytes:b.length,sha256:crypto.createHash('sha256').update(b).digest('hex'),triangles,vertices,meshes:d.meshes.length,drawCalls:d.meshes.reduce((n,m)=>n+m.primitives.length,0),materials:d.materials.length,images:d.images.length,texturedPrimitives,normalMappedPrimitives,boundsGltfAfterRoot:{min:lo,max:hi},envelopeDimensions_m:[envelopeHi[2]-envelopeLo[2],envelopeHi[0]-envelopeLo[0],envelopeHi[1]],extensionsUsed:d.extensionsUsed||[],externalDependencies:0,presentationLights:0,presentationCameras:0,metadata:meta,emissive,khronos:{errors:report.issues.numErrors,warnings:report.issues.numWarnings,infos:report.issues.numInfos},verifiedAtUtc:new Date().toISOString()};
  fs.writeFileSync(path.join(directory,filename.replace('.glb','-validation.json')),JSON.stringify(result,null,2)+'\n');
  console.log(JSON.stringify({filename,bytes:b.length,triangles,images:d.images.length,errors:0,warnings:0}));
  return result;
}
async function main(){const results=[];for(const f of filenames)results.push(await check(f));fs.writeFileSync(path.join(directory,'validation.json'),JSON.stringify(results,null,2)+'\n');}
main().catch(e=>{console.error(e);process.exitCode=1});
