"""Build reproducible, georeferenced 3D Tiles from Overture GeoJSON.

This asset-side tool intentionally does not require a running frontend or Blender.
Source heights and approximations remain separately recorded in metadata.json.
"""

import argparse
import gzip
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import mapbox_earcut
import numpy as np
from pyproj import CRS, Transformer
from shapely import make_valid
from shapely.geometry import GeometryCollection, MultiPolygon, Point, Polygon, mapping, shape
from shapely.geometry.polygon import orient
from shapely.ops import transform, unary_union

from glb import new_buckets, write_glb
from materials import STYLES, create_materials

ECEF = Transformer.from_crs("EPSG:4979", "EPSG:4978", always_xy=True)


def read_json(path):
    opener = gzip.open if str(path).endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as stream:
        return json.load(stream)


def finite_positive(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value > 0


def polygons(geometry):
    if isinstance(geometry, Polygon):
        yield geometry
    elif isinstance(geometry, (MultiPolygon, GeometryCollection)):
        for item in geometry.geoms:
            yield from polygons(item)


def height(properties, defaults, override=None):
    """Normalize ground-to-top and floating-bottom elevations, in metres.

    OSM-derived parts keep OSM height/levels as top elevation above ground.
    Overture's generic height description is an extent: for other sources with
    a nonzero minimum, use bottom+extent and record that distinct method.
    """
    category = properties.get("class") or properties.get("subtype") or "default"
    floor_m = 3.3 if category in {"office", "commercial", "hospital"} else 3.0
    bottom = properties.get("min_height")
    if not finite_positive(bottom):
        floor = properties.get("min_floor")
        bottom = floor * floor_m if finite_positive(floor) else 0.0
    value = properties.get("height")
    osm = any(s.get("provider") == "osm" or s.get("dataset") == "OpenStreetMap" for s in properties.get("sources", []))
    if finite_positive(override):
        top, method = float(override), "override"
    elif finite_positive(value):
        top, method = float(value) + (0 if osm else bottom), "source_height"
    elif finite_positive(properties.get("num_floors")):
        top, method = float(properties["num_floors"]) * floor_m, "floors_estimate"
    else:
        top = bottom + float(defaults.get(category, defaults["default"]))
        method = "type_estimate"
    if not (math.isfinite(top) and 0 <= bottom < top <= 1500):
        raise ValueError(f"Invalid vertical extent: bottom={bottom}, top={top}")
    return bottom, top, method


def material_name(properties):
    declared = str(properties.get("facade_material", ""))
    category = properties.get("class") or properties.get("subtype")
    if "brick" in declared:
        return "brick"
    if "glass" in declared or category == "office":
        return "office"
    if category in {"apartments", "residential", "house", "dormitory"}:
        return "residential"
    if category in {"commercial", "retail", "supermarket", "mall"}:
        return "commercial"
    return "concrete"


def enu_frame(longitude, latitude):
    lon, lat = math.radians(longitude), math.radians(latitude)
    east = np.array([-math.sin(lon), math.cos(lon), 0.0])
    north = np.array([-math.sin(lat) * math.cos(lon), -math.sin(lat) * math.sin(lon), math.cos(lat)])
    up = np.array([math.cos(lat) * math.cos(lon), math.cos(lat) * math.sin(lon), math.sin(lat)])
    rotation = np.column_stack((east, north, up))
    origin = np.array(ECEF.transform(longitude, latitude, 0))
    matrix = np.eye(4)
    matrix[:3, :3], matrix[:3, 3] = rotation, origin
    return origin, rotation, matrix.T.ravel().tolist()


def mesh_polygon(polygon, bottom, top, color, facade, buckets, project_to_local):
    polygon = orient(polygon, sign=1.0)
    rings = [list(polygon.exterior.coords)[:-1], *[list(r.coords)[:-1] for r in polygon.interiors]]
    points = np.asarray([point for ring in rings for point in ring], dtype=np.float64)
    ends = np.cumsum([len(ring) for ring in rings], dtype=np.uint32)
    triangles = mapbox_earcut.triangulate_float64(points, ends).reshape(-1, 3)
    local = np.asarray([project_to_local(x, y) for x, y in points])
    positions = local.copy()
    positions[:, 2] += top
    roof_indices = []
    # Quantize exactly as glTF POSITION. Very thin clipping slivers can change
    # orientation after float32 export; do not emit sub-millimetre-area faces.
    projected = positions[:, :2].astype(np.float32)
    for triangle in triangles:
        a, b, c = projected[triangle]
        ab, ac = b - a, c - a
        signed = float(ab[0] * ac[1] - ab[1] * ac[0])
        if abs(signed) < 0.002:
            continue
        if signed < 0:
            triangle = triangle[[0, 2, 1]]
        roof_indices.extend(triangle)
    buckets["roof"].append(positions, [(0, 0, 1)] * len(points), points / 16, color, roof_indices)
    if bottom > 0:
        underside = local.copy()
        underside[:, 2] += bottom
        reversed_indices = np.asarray(roof_indices).reshape(-1, 3)[:, [0, 2, 1]].ravel()
        buckets["roof"].append(underside, [(0, 0, -1)] * len(points), points / 16, color, reversed_indices, (1, 0, 0, -1))
    for ring in rings:
        perimeter = 0.0
        for i, start in enumerate(ring):
            end = ring[(i + 1) % len(ring)]
            a, b = np.asarray(project_to_local(*start)), np.asarray(project_to_local(*end))
            delta, length = b - a, math.dist(start, end)
            if length < 0.001:
                continue
            normal = np.array([delta[1], -delta[0], 0.0])
            normal /= np.linalg.norm(normal)
            wall = [a + [0, 0, bottom], b + [0, 0, bottom], b + [0, 0, top], a + [0, 0, top]]
            uv = [(perimeter / 12, bottom / 12), ((perimeter + length) / 12, bottom / 12), ((perimeter + length) / 12, top / 12), (perimeter / 12, top / 12)]
            tangent = (delta[0], delta[1], 0)
            tangent = np.asarray(tangent) / np.linalg.norm(tangent)
            buckets[facade].append(wall, [normal] * 4, uv, color, [0, 1, 2, 0, 2, 3], (*tangent, 1))
            perimeter += length


def prepare_buildings(config, building_features, part_features):
    longitude, latitude = config["longitude_wgs84"], config["latitude_wgs84"]
    projection = CRS.from_proj4(f"+proj=aeqd +lat_0={latitude} +lon_0={longitude} +datum=WGS84 +units=m")
    to_meters = Transformer.from_crs("EPSG:4326", projection, always_xy=True)
    to_geo = Transformer.from_crs(projection, "EPSG:4326", always_xy=True)
    area = Point(0, 0).buffer(config["radius_m"], quad_segs=64)
    exclusions = set(config.get("exclude_building_ids", []))
    mask = config.get("exclude_polygon")
    mask = transform(to_meters.transform, make_valid(shape(mask))) if mask else None
    defaults, overrides = config["height_defaults_m"], config.get("height_overrides_m", {})
    parts_by_parent = defaultdict(list)
    for part in part_features:
        parts_by_parent[part["properties"].get("building_id")].append(part)
    result, stats, warnings = [], Counter(), []
    minimum = config.get("minimum_footprint_m2", 12)
    for feature in sorted(building_features, key=lambda f: str(f.get("id", ""))):
        identifier, properties = feature.get("id"), feature["properties"]
        if not identifier:
            raise ValueError("Building has no stable feature ID")
        if identifier in exclusions:
            stats["excluded_buildings"] += 1
            stats["excluded_parts"] += len(parts_by_parent[identifier])
            continue
        if properties.get("is_underground"):
            stats["underground_skipped"] += 1
            continue
        geometry = transform(to_meters.transform, make_valid(shape(feature["geometry"])))
        if not geometry.intersects(area):
            continue
        geometry = geometry.intersection(area)
        if mask:
            geometry = geometry.difference(mask)
        if geometry.area < minimum:
            stats["small_footprints_skipped"] += 1
            continue
        stats["included_buildings"] += 1
        pieces, ground, elevated = [], [], []
        for part in parts_by_parent[identifier]:
            # Inherit usage/material, not the parent's maximum height/floors.
            # Otherwise a low podium with no height receives the tower height.
            vertical_fields = {"height", "min_height", "num_floors", "min_floor", "num_floors_underground", "roof_height"}
            inherited = {key: value for key, value in properties.items() if key not in vertical_fields}
            attributes = {**inherited, **part["properties"]}
            if attributes.get("is_underground"):
                continue
            try:
                footprint = transform(to_meters.transform, make_valid(shape(part["geometry"]))).intersection(geometry)
                bottom, top, method = height(attributes, defaults, overrides.get(part.get("id")))
            except (ValueError, TypeError) as error:
                warnings.append(f"part {part.get('id')}: {error}")
                continue
            if footprint.area < minimum:
                continue
            entry = (top, bottom, footprint, attributes, method, part["id"])
            (ground if bottom == 0 else elevated).append(entry)
        # Highest ground-reaching part wins overlapping planar regions; this
        # avoids duplicate full-building shells beneath stepped parts.
        occupied = GeometryCollection()
        for top, bottom, footprint, attributes, method, part_id in sorted(ground, key=lambda p: (-p[0], p[5])):
            visible = footprint.difference(occupied)
            occupied = unary_union([occupied, footprint])
            pieces.append((visible, bottom, top, attributes, method, part_id))
        for top, bottom, footprint, attributes, method, part_id in elevated:
            pieces.append((footprint, bottom, top, attributes, method, part_id))
        remaining = geometry.difference(occupied)
        try:
            bottom, top, method = height(properties, defaults, overrides.get(identifier))
            if ground:
                # Partial data should not turn uncovered podium slivers into
                # a tower-height block. This remains a documented estimate.
                coverage = occupied.intersection(geometry).area / geometry.area
                if coverage >= 0.9 or method == "type_estimate":
                    top = min(top, min(p[0] for p in ground))
                method = "parts_residual_estimate"
            pieces.append((remaining, bottom, top, properties, method, identifier))
        except ValueError as error:
            warnings.append(f"building {identifier}: {error}")
        seed = hashlib.sha256(identifier.encode()).digest()
        tint = tuple(0.88 + 0.12 * byte / 255 for byte in seed[:3])
        for footprint, bottom, top, attributes, method, part_id in pieces:
            for polygon in polygons(footprint):
                if polygon.area < minimum:
                    continue
                polygon = orient(polygon.simplify(0.15, preserve_topology=True))
                if polygon.is_empty or polygon.area < minimum:
                    continue
                result.append({"id": part_id, "building_id": identifier, "polygon": polygon, "bottom": bottom, "top": top, "method": method, "material": material_name(attributes), "color": tint})
                stats[method] += 1
                if attributes.get("roof_shape") not in (None, "flat"):
                    stats["nonflat_roofs_approximated"] += 1
    if not result:
        raise ValueError("No renderable buildings in the selected region")
    return result, stats, warnings, to_geo


def build(config_path, buildings_path, parts_path, output):
    config = read_json(config_path)
    for name, low, high in [("longitude_wgs84", -180, 180), ("latitude_wgs84", -89.9, 89.9)]:
        value = config.get(name)
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value) or not low <= value <= high:
            raise ValueError(f"Invalid {name}")
    if not 50 <= config["radius_m"] <= 20000 or not 100 <= config["tile_size_m"] <= 2000:
        raise ValueError("Unsupported radius/tile size")
    output = Path(output)
    if output.exists() and any(output.iterdir()):
        raise ValueError("Output directory must be empty; use a new version directory")
    output.mkdir(parents=True, exist_ok=True)
    (output / "tiles").mkdir()
    building_collection, part_collection = read_json(buildings_path), read_json(parts_path)
    provenance = {}
    for name, path, collection in [("buildings", buildings_path, building_collection), ("parts", parts_path, part_collection)]:
        declared = collection.get("overture_release")
        state = Path(str(path) + ".state")
        if not declared and state.exists():
            declared = read_json(state).get("last_release")
        if declared != config["release"]:
            raise ValueError(f"{name}: input release must be verified as {config['release']}")
        collection["overture_release"] = declared
        provenance[name] = {"release": declared, "sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest()}
    building_features, part_features = building_collection["features"], part_collection["features"]
    pieces, stats, warnings, to_geo = prepare_buildings(config, building_features, part_features)
    library = create_materials(output / "materials")
    groups = defaultdict(list)
    size = config["tile_size_m"]
    for piece in pieces:
        center = piece["polygon"].representative_point()
        groups[(math.floor(center.x / size), math.floor(center.y / size))].append(piece)
    children, world_corners, total_triangles = [], [], Counter()
    for (ix, iy), group in sorted(groups.items()):
        longitude, latitude = to_geo.transform((ix + 0.5) * size, (iy + 0.5) * size)
        origin, rotation, matrix = enu_frame(longitude, latitude)

        def project_to_local(x, y):
            lon, lat = to_geo.transform(x, y)
            return rotation.T @ (np.array(ECEF.transform(lon, lat, 0)) - origin)

        boxes = {}
        for level, tolerance in [("fine", 0), ("coarse", 1.8)]:
            buckets = new_buckets()
            for piece in group:
                polygon = piece["polygon"].simplify(tolerance, preserve_topology=True) if tolerance else piece["polygon"]
                if polygon.is_empty:
                    continue
                mesh_polygon(polygon, piece["bottom"], piece["top"], piece["color"], piece["material"], buckets, project_to_local)
            file = f"tiles/{ix}_{iy}-{level}.glb"
            box, triangles = write_glb(output / file, buckets, library, {"building_ids": sorted({p["building_id"] for p in group}), "height_methods": dict(Counter(p["method"] for p in group)), "ground_reference": "WGS84_ELLIPSOID_0"})
            boxes[level] = box
            total_triangles[level] += triangles
        bounds = boxes["fine"]
        for index in [3, 7, 11]:
            bounds[index] += 0.1
        center = np.asarray(bounds[:3])
        half = np.asarray([bounds[3], bounds[7], bounds[11]])
        for x in [-1, 1]:
            for y in [-1, 1]:
                for z in [-1, 1]:
                    world_corners.append(origin + rotation @ (center + half * [x, y, z]))
        children.append({"boundingVolume": {"box": bounds}, "transform": matrix, "geometricError": 8, "refine": "REPLACE", "content": {"uri": f"tiles/{ix}_{iy}-coarse.glb"}, "children": [{"boundingVolume": {"box": bounds}, "geometricError": 0, "content": {"uri": f"tiles/{ix}_{iy}-fine.glb"}}]})
    world = np.asarray(world_corners)
    center, half = (world.min(axis=0) + world.max(axis=0)) / 2, (world.max(axis=0) - world.min(axis=0)) / 2 + 0.1
    root_box = [*center.tolist(), half[0], 0, 0, 0, half[1], 0, 0, 0, half[2]]
    tileset = {"asset": {"version": "1.1", "copyright": "© OpenStreetMap contributors; Overture Maps Foundation (ODbL); Qian Shi et al. East Asian Buildings (CC BY 4.0). See metadata.json."}, "geometricError": 64, "root": {"boundingVolume": {"box": root_box}, "geometricError": 64, "refine": "REPLACE", "children": children}}
    scene = {"version": 1, "id": config["id"], "label": config["label"], "anchor": {"longitude_wgs84": config["longitude_wgs84"], "latitude_wgs84": config["latitude_wgs84"]}, "model": {"url": config["model_url"]}, "context": {"url": "tileset.json", "terrain": "ellipsoid", "maximum_anchor_distance_m": 5}, "attribution": [{"text": "© OpenStreetMap contributors", "url": "https://www.openstreetmap.org/copyright"}, {"text": "Overture Maps Foundation · ODbL", "url": "https://docs.overturemaps.org/attribution/"}], "notice": "真实建筑轮廓；缺失高度采用楼层/类型估算，立面和窗灯为程序化近似。周边按椭球体地形生成。"}
    sources = sorted({str(source.get("dataset")) for f in building_features for source in f["properties"].get("sources", [])})
    if "doi:10.5281/zenodo.8174931" in sources:
        scene["attribution"].append({"text": "Qian Shi et al. · East Asian Buildings (CC BY 4.0)", "url": "https://doi.org/10.5281/zenodo.8174931"})
    metadata = {"recipe_version": 1, "release": config["release"], "input_provenance": provenance, "source_buildings": len(building_features), "source_parts": len(part_features), "source_datasets": sources, "license": "ODbL-1.0", "sources_license_details": "https://docs.overturemaps.org/attribution/", "stats": dict(stats), "rendered_pieces": len(pieces), "tiles": len(groups), "triangles": dict(total_triangles), "warnings": warnings, "limitations": ["Missing heights estimated; source_height is not a surveyed accuracy claim", "Nonflat roofs approximated as flat", "Terrain must be the WGS84 ellipsoid surface", "Procedural facades and static window distribution; no real artificial-light transport"]}
    for filename, document in [("tileset.json", tileset), ("scene.json", scene), ("metadata.json", metadata), ("config.json", config)]:
        (output / filename).write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "sources").mkdir()
    for filename, collection in [("buildings.geojson.gz", building_collection), ("building-parts.geojson.gz", part_collection)]:
        with open(output / "sources" / filename, "wb") as raw:
            with gzip.GzipFile(fileobj=raw, mode="wb", mtime=0) as compressed:
                compressed.write(json.dumps(collection, ensure_ascii=False, separators=(",", ":")).encode())
    print(json.dumps(metadata, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--buildings", required=True)
    parser.add_argument("--parts", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    build(args.config, args.buildings, args.parts, args.output)


if __name__ == "__main__":
    main()
