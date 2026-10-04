"""Small explicit glTF 2.0 writer for merged, textured 3D Tiles content."""

import json
import struct
from collections import defaultdict

import numpy as np


class MeshBucket:
    def __init__(self):
        self.positions, self.normals, self.tangents, self.uvs, self.colors, self.indices = [], [], [], [], [], []

    def append(self, positions, normals, uvs, color, indices, tangent=(1, 0, 0, 1)):
        offset = len(self.positions)
        # Tileset default: glTF Y up, X forward -> ENU after Cesium Y-to-Z correction.
        self.positions.extend((p[0], p[2], -p[1]) for p in positions)
        self.normals.extend((n[0], n[2], -n[1]) for n in normals)
        self.tangents.extend([(tangent[0], tangent[2], -tangent[1], tangent[3])] * len(positions))
        self.uvs.extend(uvs)
        self.colors.extend([color] * len(positions))
        self.indices.extend(offset + int(i) for i in indices)


def write_glb(path, buckets, library, extras):
    binary = bytearray()
    views, accessors, primitives, images, textures, materials = [], [], [], [], [], []

    def texture(name):
        index = len(images)
        images.append({"uri": f"../materials/{name}.png"})
        textures.append({"source": index, "sampler": 0})
        return {"index": index}

    material_indices = {}
    for entry in library:
        name = entry["name"]
        if not buckets.get(name) or not buckets[name].indices:
            continue
        material = {
            "name": name,
            "pbrMetallicRoughness": {
                "baseColorTexture": texture(name + "-base"),
                "metallicRoughnessTexture": texture(name + "-orm"),
                "metallicFactor": 0.0,
                "roughnessFactor": 1.0,
            },
            "normalTexture": {**texture(name + "-normal"), "scale": 0.45},
            "doubleSided": False,
        }
        if entry["emissive"]:
            material["emissiveTexture"] = texture(name + "-emissive")
            material["emissiveFactor"] = [1.0, 1.0, 1.0]
        material_indices[name] = len(materials)
        materials.append(material)

    def accessor(values, dtype, kind, target, bounds=False):
        while len(binary) % 4:
            binary.append(0)
        array = np.asarray(values, dtype=dtype)
        payload = array.tobytes()
        view_index = len(views)
        views.append({"buffer": 0, "byteOffset": len(binary), "byteLength": len(payload), "target": target})
        binary.extend(payload)
        result = {"bufferView": view_index, "componentType": 5126 if dtype == "<f4" else 5125, "count": len(values), "type": kind}
        if bounds:
            result["min"] = array.min(axis=0).tolist()
            result["max"] = array.max(axis=0).tolist()
        accessors.append(result)
        return len(accessors) - 1

    for name, bucket in sorted(buckets.items()):
        if not bucket.indices:
            continue
        primitives.append({
            "attributes": {
                "POSITION": accessor(bucket.positions, "<f4", "VEC3", 34962, True),
                "NORMAL": accessor(bucket.normals, "<f4", "VEC3", 34962),
                "TANGENT": accessor(bucket.tangents, "<f4", "VEC4", 34962),
                "TEXCOORD_0": accessor(bucket.uvs, "<f4", "VEC2", 34962),
                "COLOR_0": accessor(bucket.colors, "<f4", "VEC3", 34962),
            },
            "indices": accessor(bucket.indices, "<u4", "SCALAR", 34963),
            "material": material_indices[name],
            "mode": 4,
        })
    if not primitives:
        raise ValueError("Cannot export an empty tile")
    document = {
        "asset": {"version": "2.0", "generator": "Cyber Sight open context v1", "copyright": "© OpenStreetMap contributors; Overture Maps Foundation; source details in metadata.json"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"name": "CONTEXT_ROOT", "mesh": 0}],
        "meshes": [{"primitives": primitives}],
        "materials": materials,
        "images": images,
        "textures": textures,
        "samplers": [{"magFilter": 9729, "minFilter": 9987, "wrapS": 10497, "wrapT": 10497}],
        "buffers": [{"byteLength": len(binary)}],
        "bufferViews": views,
        "accessors": accessors,
        "extras": extras,
    }
    encoded = json.dumps(document, separators=(",", ":"), ensure_ascii=False).encode()
    encoded += b" " * (-len(encoded) % 4)
    binary.extend(b"\0" * (-len(binary) % 4))
    total = 12 + 8 + len(encoded) + 8 + len(binary)
    with open(path, "wb") as stream:
        stream.write(struct.pack("<III", 0x46546C67, 2, total))
        stream.write(struct.pack("<II", len(encoded), 0x4E4F534A))
        stream.write(encoded)
        stream.write(struct.pack("<II", len(binary), 0x004E4942))
        stream.write(binary)
    positions = np.concatenate([np.asarray(b.positions) for b in buckets.values() if b.indices])
    # Convert back to tile-local ENU for the 3D Tiles bounding box.
    enu = positions[:, [0, 2, 1]] * [1, -1, 1]
    low, high = enu.min(axis=0), enu.max(axis=0)
    center, half = (low + high) / 2, np.maximum((high - low) / 2, 0.01)
    box = [*center.tolist(), half[0], 0, 0, 0, half[1], 0, 0, 0, half[2]]
    return box, sum(len(b.indices) // 3 for b in buckets.values())


def new_buckets():
    return defaultdict(MeshBucket)
