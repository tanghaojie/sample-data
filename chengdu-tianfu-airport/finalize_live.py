import bpy,json
from pathlib import Path
OUT=Path(r'C:\Users\JackieTang\Desktop\sample-data\chengdu-tianfu-airport')
scene=bpy.context.scene
bpy.ops.export_scene.gltf(filepath=str(OUT/'chengdu-tianfu-airport.glb'),export_format='GLB',use_selection=True,use_active_scene=True,export_extras=True,export_animations=False,export_cameras=False,export_lights=False,export_yup=True)
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            space=area.spaces.active;space.clip_end=20000;space.overlay.show_overlays=False
            space.shading.type='MATERIAL';space.region_3d.view_perspective='CAMERA';space.region_3d.view_camera_zoom=0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'chengdu-tianfu-airport.blend'))
print(json.dumps({'scene':scene.name,'bytes':(OUT/'chengdu-tianfu-airport.glb').stat().st_size}))
