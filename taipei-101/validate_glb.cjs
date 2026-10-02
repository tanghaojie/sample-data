const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
const filename = path.join(__dirname, 'taipei-101.glb');
const b = fs.readFileSync(filename);
assert.equal(b.toString('ascii', 0, 4), 'glTF');
assert.equal(b.readUInt32LE(4), 2);
assert.equal(b.readUInt32LE(8), b.length);
const jsonLength = b.readUInt32LE(12);
assert.equal(b.readUInt32LE(16), 0x4e4f534a);
const d = JSON.parse(b.toString('utf8', 20, 20 + jsonLength));
const binHeader = 20 + jsonLength;
assert.equal(b.readUInt32LE(binHeader + 4), 0x004e4942);
const binary = binHeader + 8;
assert(!(d.buffers || []).some(x => x.uri), 'External buffer');
assert(!(d.images || []).some(x => x.uri), 'External texture');
assert(!d.cameras?.length, 'Presentation camera exported');
assert(!d.extensions?.KHR_lights_punctual, 'Presentation lighting exported');
assert(!(d.extensionsUsed || []).includes('KHR_materials_unlit'));
assert(!d.extensionsRequired?.length, 'Required compression/runtime extensions');
const lo = [Infinity, Infinity, Infinity], hi = [-Infinity, -Infinity, -Infinity];
let positions = 0, triangles = 0;
for (const m of d.meshes) for (const p of m.primitives) {
  assert(p.mode === undefined || p.mode === 4, 'Non-triangle primitive');
  assert(p.attributes.NORMAL !== undefined, 'Missing PBR normals');
  const a = d.accessors[p.attributes.POSITION], v = d.bufferViews[a.bufferView];
  assert.equal(a.componentType, 5126); assert.equal(a.type, 'VEC3');
  for (let i = 0; i < a.count; i++) for (let c = 0; c < 3; c++) {
    const x = b.readFloatLE(binary + (v.byteOffset || 0) + (a.byteOffset || 0) + i * (v.byteStride || 12) + c * 4);
    assert(Number.isFinite(x), 'Invalid coordinate');
    lo[c] = Math.min(lo[c], x); hi[c] = Math.max(hi[c], x);
  }
  positions += a.count;
  triangles += d.accessors[p.indices].count / 3;
}
assert(Math.abs(lo[1]) < .25, 'Ground-centred origin');
assert(Math.abs(hi[1] - 508) < .05, 'Architectural height');
const emissive = d.materials.filter(m => m.emissiveFactor?.some(x => x > 0)).map(m => ({
  name: m.name, factor: m.emissiveFactor,
  strength: m.extensions?.KHR_materials_emissive_strength?.emissiveStrength || 1,
}));
assert(emissive.length >= 7, 'Missing night channels');
const result = {
  asset: d.asset, bytes: b.length,
  sha256: crypto.createHash('sha256').update(b).digest('hex'),
  meshes: d.meshes.length, materials: d.materials.length, positions, triangles,
  boundsGltfYUp: { min: lo, max: hi },
  extensionsUsed: d.extensionsUsed || [], emissive,
  externalDependencies: 0, presentationLights: 0, presentationCameras: 0,
};
async function main() {
  try {
    const validator = require('gltf-validator');
    const report = await validator.validateBytes(new Uint8Array(b), { uri: 'taipei-101.glb', maxIssues: 100 });
    fs.writeFileSync(path.join(__dirname, 'gltf-validator-report.json'), JSON.stringify(report, null, 2) + '\n');
    assert.equal(report.issues.numErrors, 0, 'Khronos validator errors');
    result.khronos = { errors: report.issues.numErrors, warnings: report.issues.numWarnings };
  } catch (e) {
    if (e.code === 'MODULE_NOT_FOUND') throw new Error('Install gltf-validator and provide NODE_PATH before validation');
    throw e;
  }
  fs.writeFileSync(path.join(__dirname, 'validation.json'), JSON.stringify(result, null, 2) + '\n');
  console.log(JSON.stringify(result, null, 2));
}
main().catch(e => { console.error(e); process.exitCode = 1; });
