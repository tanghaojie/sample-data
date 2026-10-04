"""Fetch a pinned Overture release once, including source OSM attributes.

No map API key is needed. HTTPS proxy configuration is respected for S3 reads.
The resulting files can be archived and used without live requests while recording.
"""

import argparse
import json
import math
import urllib.request
from pathlib import Path

import pyarrow.fs as arrow_fs
from overturemaps.core import record_batch_reader
from pyproj import Geod
from shapely import from_wkb
from shapely.geometry import mapping

from build_context import read_json


def query_boxes(config):
    longitude, latitude = config["longitude_wgs84"], config["latitude_wgs84"]
    geod = Geod(ellps="WGS84")
    edge = [geod.fwd(longitude, latitude, angle, config["radius_m"] * 1.04) for angle in range(0, 360, 5)]
    unwrapped = [longitude + ((p[0] - longitude + 180) % 360 - 180) for p in edge]
    west, east = min(unwrapped), max(unwrapped)
    south, north = min(p[1] for p in edge), max(p[1] for p in edge)
    if west < -180:
        return [(west + 360, south, 180, north), (-180, south, east, north)]
    if east > 180:
        return [(west, south, 180, north), (-180, south, east - 360, north)]
    return [(west, south, east, north)]


def fetch(config, output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    proxy = urllib.request.getproxies().get("https")
    original = arrow_fs.S3FileSystem

    def filesystem(**kwargs):
        if proxy:
            kwargs["proxy_options"] = proxy
        return original(**kwargs)

    # The pinned official reader constructs its filesystem internally. Limit
    # proxy adaptation to this command and restore the public class afterwards.
    arrow_fs.S3FileSystem = filesystem
    try:
        for data_type in ["building", "building_part"]:
            features = {}
            for bbox in query_boxes(config):
                reader = record_batch_reader(data_type, bbox=bbox, release=config["release"], stac=True, connect_timeout=30, request_timeout=60)
                if reader is None:
                    continue
                for batch in reader:
                    for row in batch.to_pylist():
                        identifier = row["id"]
                        geometry = mapping(from_wkb(row["geometry"]))
                        properties = {k: v for k, v in row.items() if k not in {"id", "geometry", "bbox", "theme", "type"} and v is not None}
                        features[identifier] = {"type": "Feature", "id": identifier, "geometry": geometry, "properties": properties}
            document = {"type": "FeatureCollection", "overture_release": config["release"], "features": [features[key] for key in sorted(features)]}
            path = output / f"{data_type}.geojson"
            path.write_text(json.dumps(document, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
            print(f"{data_type}: {len(features)} features -> {path}")
    finally:
        arrow_fs.S3FileSystem = original


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    fetch(read_json(args.config), args.output)
