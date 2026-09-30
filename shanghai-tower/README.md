# 上海中心大厦 · Shanghai Tower

Original architectural visualization built in Blender 5.2.1 LTS from the supplied site photographs and Gensler's facade-design paper. Model height is 632 metres and the profile rotates 120 degrees. The soft triangular shell tapers exponentially. The modelling study includes a recessed helical overlap, 34,560 exterior panels, fine metallic mullions, inner circular curtain wall, eight intermediate sky-garden/mechanical zones, radial facade supports, an open asymmetric crown with exposed ribs and equipment, a bronze wave-roof retail podium, entrance canopies and landscaped paving.

This is a reference-based visualization for portfolio and real-time geographic display. It is not surveyed geometry, construction documentation or an engineering replica. Zone elevations, crown ribs/equipment, podium and planting are visually reconstructed approximations. Architectural authorship of the real building belongs to Gensler and its project team. The reference photographs are not embedded in the GLB or redistributed with this deliverable.

## Files

- `shanghai-tower.glb`: self-contained PBR asset for Cyber-Sight Geo.
- `shanghai-tower.blend`: editable model with separate presentation camera and lights.
- `build_model.py`: original parameterized mesh-generation source; creates its own scene.
- `render_preview.py`: Cycles daylight, night and crown studies. Studio ground and lighting are preview-only.
- `preview-day.png`, `preview-night.png`, `preview-crown.png`: portfolio renders.
- `placement.json`: URL and suggested WGS84 placement/time examples.
- `validation.json`, `gltf-validator-report.json`: binary bounds/material/dependency checks and Khronos validation.

## Geo rendering

The asset uses metre-scale, ground-centred local coordinates. Blender Z-up is converted to standard glTF Y-up on export. Set scale to 1. PBR base color, metallic, roughness, clearcoat and normals are retained. Sky-garden glazing uses standard alpha blending. Camera, studio floor, sun and fill lights are excluded from the GLB.

Emissive office windows, sky-lobby glazing, restrained spiral lighting, crown rim and plaza lights are night channels. Cyber-Sight multiplies emissive by zero in daylight and by one at night, using model location and simulation time. No baked shadows, Bloom dependency or Unlit materials are used. Blender previews manually apply the same day/night material distinction; they are lighting studies, not pixel-equivalent copies of the Cesium renderer.

Load `https://sample-data-jt.vercel.app/shanghai-tower/shanghai-tower.glb` at longitude `121.5011`, latitude `31.23356`, ellipsoid height `0`, scale `1`. The placement is approximate; height can be adjusted for the selected terrain. On 2026-10-01, `04:00 UTC` corresponds to Shanghai noon and `12:00 UTC` to 20:00 local time.

## References

- [Gensler: Shanghai Tower](https://www.gensler.com/projects/shanghai-tower): height, double skin and architectural intent.
- [Gensler: Shanghai Tower Facade Design Process](https://www.gensler.com/uploads/document/242/file/Shanghai_Tower_Facade_Design_Process_11_10_2011.pdf): soft triangular profile, exponential taper, 120-degree rotation and facade support principles. This is a design-stage technical paper; final crown and podium appearance is read from supplied photographs.
- [Gensler: Shanghai Tower Retail Podium](https://www.gensler.com/projects/shanghai-tower-retail-podium): retail podium context.
- [Cyber-Sight Geo external-model rendering standard](https://github.com/tanghaojie/Cyber-Sight/blob/master/docs/platform/design/modules/geo-model-rendering.md): solar-altitude-controlled PBR emissive and model lighting.
- User-supplied `参考图/`: low-angle facade photos, full-tower views and aerial crown detail. Used for reference only.

## Reproduce

Run `build_model.py` in Blender's Python environment, then open the resulting `.blend` and run `render_preview.py` with `-- all` in background Blender. Run `node validate_glb.cjs` with the official `gltf-validator` npm module available on `NODE_PATH`. Validation checks all exported positions, height/origin, embedded dependencies, normals and night channels, then calls the Khronos validator.
