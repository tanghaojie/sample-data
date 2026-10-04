"""Asset-generator checks; these do not import or test the Sight frontend."""

import unittest

import numpy as np
from shapely.geometry import Polygon

from build_context import enu_frame, height, mesh_polygon, prepare_buildings
from fetch_context import query_boxes
from glb import new_buckets


class ContextGeometryTests(unittest.TestCase):
    def test_osm_floating_height_is_top_not_extent(self):
        bottom, top, method = height({"height": 439, "min_height": 390.6, "sources": [{"provider": "osm"}]}, {"default": 9})
        self.assertEqual((bottom, top, method), (390.6, 439, "source_height"))

    def test_floor_and_type_estimates_are_distinguished(self):
        self.assertEqual(height({"num_floors": 8, "min_floor": 7}, {"default": 9}), (21, 24, "floors_estimate"))
        self.assertEqual(height({}, {"default": 9}), (0, 9, "type_estimate"))
        with self.assertRaises(ValueError):
            height({"height": 10, "min_height": 20, "sources": [{"provider": "osm"}]}, {"default": 9})

    def test_roof_hole_is_not_filled_and_faces_point_outward(self):
        polygon = Polygon([(0, 0), (10, 0), (10, 10), (0, 10)], [[(3, 3), (3, 7), (7, 7), (7, 3)]])
        buckets = new_buckets()
        mesh_polygon(polygon, 0, 12, (1, 1, 1), "concrete", buckets, lambda x, y: (x, y, 0))
        roof = buckets["roof"]
        vertices = np.asarray(roof.positions)
        indices = np.asarray(roof.indices).reshape(-1, 3)
        cross = np.cross(vertices[indices[:, 1]] - vertices[indices[:, 0]], vertices[indices[:, 2]] - vertices[indices[:, 0]])
        self.assertAlmostEqual(float(np.linalg.norm(cross, axis=1).sum() / 2), 84)
        self.assertTrue((cross[:, 1] > 0).all())
        wall = buckets["concrete"]
        vertices = np.asarray(wall.positions)
        indices = np.asarray(wall.indices).reshape(-1, 3)
        cross = np.cross(vertices[indices[:, 1]] - vertices[indices[:, 0]], vertices[indices[:, 2]] - vertices[indices[:, 0]])
        self.assertTrue((np.einsum("ij,ij->i", cross, np.asarray(wall.normals)[indices[:, 0]]) > 0).all())

    def test_enu_frame_is_right_handed_at_equator_and_taipei(self):
        for lon, lat in [(0, 0), (121.564472, 25.033964)]:
            origin, rotation, matrix = enu_frame(lon, lat)
            self.assertTrue(np.allclose(rotation.T @ rotation, np.eye(3)))
            self.assertAlmostEqual(float(np.linalg.det(rotation)), 1)
            self.assertTrue(np.allclose(np.asarray(matrix).reshape(4, 4).T[:3, 3], origin))
        _, rotation, _ = enu_frame(0, 0)
        self.assertTrue(np.allclose(rotation[:, 0], [0, 1, 0]))
        self.assertTrue(np.allclose(rotation[:, 1], [0, 0, 1]))

    def test_excluding_parent_also_excludes_parts(self):
        geometry = {"type": "Polygon", "coordinates": [[[0, 0], [0.0001, 0], [0.0001, 0.0001], [0, 0.0001], [0, 0]]]}
        def feature(identifier, properties):
            return {"type": "Feature", "id": identifier, "geometry": geometry, "properties": properties}
        config = {"longitude_wgs84": 0, "latitude_wgs84": 0, "radius_m": 200, "height_defaults_m": {"default": 9}, "exclude_building_ids": ["hero"]}
        pieces, stats, _, _ = prepare_buildings(config, [feature("hero", {}), feature("neighbor", {})], [feature("hero-part", {"building_id": "hero", "height": 100})])
        self.assertEqual(stats["excluded_buildings"], 1)
        self.assertEqual(stats["excluded_parts"], 1)
        self.assertEqual({p["building_id"] for p in pieces}, {"neighbor"})

    def test_query_splits_at_date_line(self):
        boxes = query_boxes({"longitude_wgs84": 179.995, "latitude_wgs84": 20, "radius_m": 2000})
        self.assertEqual(len(boxes), 2)
        for west, south, east, north in boxes:
            self.assertTrue(-180 <= west < east <= 180)
            self.assertLess(east - west, 1)

    def test_podium_does_not_inherit_tower_height(self):
        geometry = {"type": "Polygon", "coordinates": [[[0, 0], [0.0001, 0], [0.0001, 0.0001], [0, 0.0001], [0, 0]]]}
        building = {"id": "tower", "geometry": geometry, "properties": {"height": 200, "class": "office", "sources": [{"provider": "osm"}]}}
        part = {"id": "podium", "geometry": geometry, "properties": {"building_id": "tower", "num_floors": 2}}
        config = {"longitude_wgs84": 0, "latitude_wgs84": 0, "radius_m": 200, "height_defaults_m": {"default": 9}}
        pieces, _, _, _ = prepare_buildings(config, [building], [part])
        self.assertEqual(len(pieces), 1)
        self.assertAlmostEqual(pieces[0]["top"], 6.6)
        self.assertEqual(pieces[0]["method"], "floors_estimate")


if __name__ == "__main__":
    unittest.main()
