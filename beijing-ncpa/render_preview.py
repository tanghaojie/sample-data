"""Cycles presentation renders. Render lights/cameras are deliberately not in GLB."""
import bpy,sys,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parent
scene=bpy.context.scene
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['day']
name=args[0]
draft='draft' in args
scene.render.resolution_x=1400 if draft else 1800
scene.render.resolution_y=950 if draft else 1200
scene.cycles.samples=12 if draft else 32
scene.cycles.use_denoising=True
scene.cycles.max_bounces=8
scene.cycles.transparent_max_bounces=12
scene.render.threads_mode='FIXED';scene.render.threads=6
world=scene.world;nt=world.node_tree
sky=next(n for n in nt.nodes if n.bl_idname=='ShaderNodeTexSky')
bg=next(n for n in nt.nodes if n.bl_idname=='ShaderNodeBackground')
sun=bpy.data.objects['Sun | day']
for m in bpy.data.materials:
    if not m.use_nodes:continue
    bs=next((n for n in m.node_tree.nodes if n.bl_idname=='ShaderNodeBsdfPrincipled'),None)
    if bs and m.name.startswith('Night |'):
        bs.inputs['Emission Strength'].default_value=bs.inputs['Emission Strength'].default_value if name=='night' else (bs.inputs['Emission Strength'].default_value*.35 if name=='sunset' else 0)
for o in bpy.data.collections['90 Presentation rig'].objects:
    if o.type=='LIGHT' and o.data.type=='AREA':o.hide_render=name!='night'
if name=='night':
    nt.links.remove(bg.inputs['Color'].links[0]);bg.inputs['Color'].default_value=(.035,.055,.105,1);bg.inputs['Strength'].default_value=.32
    sun.data.energy=.025;sun.data.color=(.34,.49,.75)
    scene.camera=bpy.data.objects['Hero night | low lake reflection']
    scene.view_settings.exposure=.9
elif name=='sunset':
    sky.sun_elevation=.09;sky.sun_rotation=2.6;bg.inputs['Strength'].default_value=.4
    sun.data.energy=1.8;sun.data.color=(1,.58,.3);sun.rotation_euler=(1.42,-.08,-1.2)
    scene.camera=bpy.data.objects['Hero day | northeast lake']
elif name=='aerial':scene.camera=bpy.data.objects['Aerial | plan and landscape']
elif name=='detail':scene.camera=bpy.data.objects['Detail | titanium glass junction']
elif name=='elevation':scene.camera=bpy.data.objects['Elevation | north']
elif name=='entrance':
    cam=bpy.data.objects['Hero day | northeast lake'];cam.location=(25,174,13)
    from mathutils import Vector
    cam.rotation_euler=(Vector((0,97,5))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=40;scene.camera=cam
else:scene.camera=bpy.data.objects['Hero day | northeast lake']
scene.render.filepath=str(ROOT/(f'draft-{name}.png' if draft else f'renders/{name}.png'))
print('NCPA_RENDER_START',name,flush=True)
bpy.ops.render.render(write_still=True)
print('NCPA_RENDER_COMPLETE',name,flush=True)
