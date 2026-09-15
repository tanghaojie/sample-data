# Chengdu OPPO Tower

Lightweight, georeferenced GLB asset for the Cyber-Sight Geo external-model loader.

## Geo loading values

- Model URL path: `/chengdu-oppo-tower/chengdu-oppo-tower.glb`
- WGS84 longitude: `104.078051`
- WGS84 latitude: `30.517354`
- Ellipsoid height: `0 m`
- Scale: `1`
- Heading / pitch / roll: `0 / 0 / 0 degrees`

The mesh uses local metres, Y-up in the exported glTF, and a bottom-centre origin. The Blender source remains Z-up. Geographic placement is applied by Cyber-Sight through its WGS84 model transform; the same values are also stored as glTF node extras on `Chengdu_OPPO_Tower_ROOT`.

## Rendering

- Cool blue metallic-glass facade and stainless-steel vertical fins.
- Warm office windows use PBR emissive color and `KHR_materials_emissive_strength` (`4.0`).
- The OPPO wordmark uses white PBR emissive material (`2.5`).
- No embedded lights, camera, ground plane, or Bloom are exported. Cyber-Sight controls sunlight and the day/night emissive channel from simulation time and model position.

## Dimensions and files

- Overall exported bounds: approximately `71 x 32 x 206.72 m` (width x depth x height).
- `chengdu-oppo-tower.glb`: production asset.
- `chengdu-oppo-tower.blend`: editable Blender source and preview setup.
- `chengdu-oppo-tower-preview.png`: Blender dusk preview.

Coordinate and height references: OpenStreetMap way `1212154634` and public building records listing a 206 m main tower.
