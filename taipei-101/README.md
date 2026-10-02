# 台北101大厦 · Taipei 101

Original Blender architectural visualization for a portfolio and Cyber-Sight Geo.

## Architecture and modelling scope

508 m total height, 448 m roof and a 60 m pinnacle. Eight repeated, outward-flaring modules above a tapered base are the defining silhouette. The model includes chamfered corners, individual jade curtain-wall panels, pearl mullions, mechanical-floor louvres, projecting dragon/cloud ornaments, circular medallions with square apertures, stepped observation terraces, a faceted spire, monumental entrance, retail podium, folded roof seams, barrel-vault skylight, paving, trees and street furniture.

This is a photo/reference-based reconstruction, not a measured engineering or BIM model. Main modules span approximately 116–390 m. Facade bay counts, lower-floor elevations, decorative relief, podium/site footprint and landscaping are artistic estimates. The night lighting is an architectural presentation scheme inspired by photographs; it does not reproduce a specific weekday/event lighting program. Windows are opaque PBR glazing for efficient GIS rendering; there is no furnished interior or hidden structural simulation.

## Sources

- [C.Y. Lee & Partners, Taipei Financial Center](https://www.cylee.com/project/Taipei-101): architect's project description, 508 m height, eight-floor units and symbolic ornaments; official photographs checked for silhouette, facade, podium, entrance and metalwork.
- [Thornton Tomasetti, Taipei 101](https://www.thorntontomasetti.com/project/taipei-101): structural engineer's description of eight flaring modules, setbacks and retail skylight.
- [Leonard M. Joseph, Thornton Tomasetti, Taipei 101 chapter preview](https://siny.org/wp-content/uploads/2014/12/2014_TallandSupertallBuildings_Preview.pdf): architecture and structural-system context. A complete dimensioned architectural drawing set was not obtained.
- [Cyber-Sight external model rendering standard](https://github.com/tanghaojie/Cyber-Sight/blob/71d1d65bec7cfd007bef4130fff556403bdf917d/docs/platform/design/modules/geo-model-rendering.md), checked at repository revision `71d1d65bec7cfd007bef4130fff556403bdf917d`.

Reference photos/PDF are retained locally for study, attributed to their respective owners and excluded from the public model commit. No photographic imagery or third-party 3D model is embedded in the exported asset.

## Geo compatibility

Metre scale; origin at ground and tower centre; standard glTF Y-up from Blender Z-up. Geometry is batched by part/material. PBR base colour, metallic and roughness remain independent of the night channel. Occupied windows, terrace rims, corner lanterns, retail glazing, spire and plaza caps carry emissive materials. Cyber-Sight turns emissive off in daytime, on at night and interpolates at twilight using the model's WGS84 location and simulation clock. No runtime lights, cameras, bloom or required compression extension are exported. The studio cameras, soft lights and receiving ground belong only to the presentation rig.

Use `placement.json` with the [online GLB](https://sample-data-jt.vercel.app/taipei-101/taipei-101.glb) in Geo → 数据 → 外部数据 → 加载 glTF / GLB. Coordinates are approximate; ellipsoid height 0 m is the no-terrain preview placement and must be adjusted for terrain data.

## Files and reproduction

- `taipei-101.blend`: editable scene with original modelling and presentation rig.
- `taipei-101.glb`: self-contained runtime asset.
- `build_model.py`: original deterministic modelling script for Blender 5.2.
- `render_preview.py`: Cycles day/night, detail, podium and elevation renders.
- `preview-*.png`: portfolio images.
- `validation.json`, `gltf-validator-report.json`: geometry checks and Khronos validator evidence.
- `delivery-verification.json`, `geo-online-*.jpg`: separate publication/Chrome evidence.
- `verify_delivery.py`: repeatable Vercel status and deployed-file hash checks.

## Verified delivery

Khronos validation: 0 errors, 0 warnings. The 15,419,900-byte GLB contains 391,584 triangles, 220 material/part meshes, 25 materials and eight emissive channels. There are no external asset dependencies or exported presentation cameras/lights.

Model commit `0e4fa28fc84f0c48117f26951953bfd602e9503d` was pushed to `master`; Vercel reported successful deployment. The public endpoint returned HTTP 200, `model/gltf-binary`, CORS `*`, and SHA-256 `e303e71be0efc1c49490f92b330892ad76f45249958265fd4e7aaae91a52deb1`, matching the local GLB.

Chrome loaded the deployed GLB at WGS84 121.564472°, 25.033964°, scale 1. Geo explicitly recognised emissive material. Day (2026-10-02 03:43:14 UTC) and night (12:43:14 UTC) were visually inspected with the same camera: daytime windows unlit, night occupied windows/terrace rims/pinnacle/retail emissive. Screenshots preserve the Geo workspace and simulation-clock context. The night display tab is retained; loaded resources remain session-scoped by the Geo design.

Rebuild: `blender --background --python build_model.py`. Render: `blender --background taipei-101.blend --python render_preview.py -- all`. Validate with `node validate_glb.cjs` after making `gltf-validator` available through `NODE_PATH`.
