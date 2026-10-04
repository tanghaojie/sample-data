"""Validate generated assets: geometry, references, winding, ENU and bounds."""

import argparse
import json
import math
import struct
from pathlib import Path

import numpy as np
from PIL import Image


def read_glb(path):
    data = path.read_bytes()
    magic, version, length = struct.unpack_from("<III", data)
    assert magic == 0x46546C67 and version == 2 and length == len(data), path
    json_length, json_type = struct.unpack_from("<II", data, 12)
    assert json_type == 0x4E4F534A and json_length % 4 == 0
    document = json.loads(data[20:20 + json_length])
    bin_length, bin_type = struct.unpack_from("<II", data, 20 + json_length)
    assert bin_type == 0x004E4942
    binary = data[28 + json_length:]
    assert len(binary) == bin_length
    assert 0 <= bin_length - document["buffers"][0]["byteLength"] < 4
    return document, binary


def accessor(document, binary, index):
    item = document["accessors"][index]
    view = document["bufferViews"][item["bufferView"]]
    width = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[item["type"]]
    assert item["componentType"] in (5125, 5126)
    start = view.get("byteOffset", 0) + item.get("byteOffset", 0)
    length = item["count"] * width * 4
    assert start % 4 == 0 and length <= view["byteLength"] and start + length <= len(binary)
    dtype = "<f4" if item["componentType"] == 5126 else "<u4"
    return np.frombuffer(binary, dtype=dtype, count=item["count"] * width, offset=start).reshape(-1, width)


def validate_glb(path, excluded):
    document, binary = read_glb(path)
    assert not excluded.intersection(document["extras"]["building_ids"]), path
    for image in document["images"]:
        texture = (path.parent / image["uri"]).resolve()
        assert texture.is_file(), texture
        with Image.open(texture) as bitmap:
            assert bitmap.width == bitmap.height == 256
    points, triangles = [], 0
    for mesh in document["meshes"]:
        for primitive in mesh["primitives"]:
            attributes = primitive["attributes"]
            position = accessor(document, binary, attributes["POSITION"])
            normal = accessor(document, binary, attributes["NORMAL"])
            tangent = accessor(document, binary, attributes["TANGENT"])
            uv = accessor(document, binary, attributes["TEXCOORD_0"])
            color = accessor(document, binary, attributes["COLOR_0"])
            indices = accessor(document, binary, primitive["indices"]).ravel()
            assert len(indices) % 3 == 0 and int(indices.max()) < len(position)
            assert all(np.isfinite(a).all() for a in (position, normal, tangent, uv, color))
            assert np.allclose(np.linalg.norm(normal, axis=1), 1, atol=1e-5)
            assert np.allclose(np.linalg.norm(tangent[:, :3], axis=1), 1, atol=1e-5)
            assert np.allclose((normal * tangent[:, :3]).sum(axis=1), 0, atol=1e-5)
            assert ((color >= 0) & (color <= 1)).all()
            tri = indices.reshape(-1, 3)
            cross = np.cross(position[tri[:, 1]] - position[tri[:, 0]], position[tri[:, 2]] - position[tri[:, 0]])
            assert (np.einsum("ij,ij->i", cross, normal[tri[:, 0]]) > 1e-8).all(), f"backwards/degenerate face in {path}"
            triangles += len(tri)
            points.append(position[:, [0, 2, 1]] * [1, -1, 1])
    return np.concatenate(points), triangles


def validate(directory):
    directory = Path(directory)
    tileset = json.loads((directory / "tileset.json").read_text())
    config = json.loads((directory / "config.json").read_text())
    scene = json.loads((directory / "scene.json").read_text())
    assert tileset["asset"]["version"] == "1.1" and scene["version"] == 1
    assert scene["context"]["terrain"] == "ellipsoid"
    excluded = set(config.get("exclude_building_ids", []))
    root = np.asarray(tileset["root"]["boundingVolume"]["box"])
    root_half = root[[3, 7, 11]]
    checked, count = set(), 0
    for tile in tileset["root"]["children"]:
        matrix = np.asarray(tile["transform"]).reshape(4, 4).T
        assert np.allclose(matrix[3], [0, 0, 0, 1])
        assert np.allclose(matrix[:3, :3].T @ matrix[:3, :3], np.eye(3), atol=1e-8)
        assert np.linalg.det(matrix[:3, :3]) > 0.999999
        bounds = np.asarray(tile["boundingVolume"]["box"])
        half = bounds[[3, 7, 11]]
        assert (half > 0).all()
        assert tile["geometricError"] > 0 and tile["refine"] == "REPLACE"
        for node in [tile, *tile["children"]]:
            path = directory / node["content"]["uri"]
            points, triangles = validate_glb(path, excluded)
            checked.add(str(path))
            count += triangles
            assert (np.abs(points - bounds[:3]) <= half + 1e-3).all(), path
            world = points @ matrix[:3, :3].T + matrix[:3, 3]
            assert (np.abs(world - root[:3]) <= root_half + 0.01).all(), path
    assert len(checked) == len(list((directory / "tiles").glob("*.glb")))
    result = {"files": len(checked), "triangles": count, "geometry_and_references": "passed", "excluded_building_ids": sorted(excluded)}
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory")
    validate(parser.parse_args().directory)
