"""Re-export the editable source without rebuilding geometry or its presentation rig."""
import bpy,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from finalize_glb import finalize
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'beijing-ncpa.blend'))
bpy.ops.object.select_all(action='DESELECT')
for collection in bpy.data.collections:
    if collection.name.startswith('90'):continue
    for ob in collection.objects:
        if ob.type in {'MESH','EMPTY'}:ob.select_set(True)
path=ROOT/'beijing-ncpa.glb'
bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_yup=True,export_apply=True,export_texcoords=True,export_normals=True,export_tangents=True,export_materials='EXPORT',export_cameras=False,export_lights=False,export_extras=True,export_image_format='AUTO')
finalize(path)
