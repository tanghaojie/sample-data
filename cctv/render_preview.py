import bpy, math
from mathutils import Vector
scene=bpy.data.scenes['CCTV_Architectural_Study']
bpy.context.window.scene=scene
out=r'C:\Users\JackieTang\Desktop\sample-data\cctv'
scene.render.engine='CYCLES';scene.cycles.samples=32
scene.render.resolution_x=1200;scene.render.resolution_y=1400
scene.render.film_transparent=False
world=scene.world;bg=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND')
emissions=[]
for m in bpy.data.materials:
    if m.use_nodes:
        for n in m.node_tree.nodes:
            if n.bl_idname=='ShaderNodeBsdfPrincipled':
                emissions.append((n,n.inputs['Emission Strength'].default_value))
sun=bpy.data.objects['Sun_Preview']
for n,v in emissions:n.inputs['Emission Strength'].default_value=0
scene.render.filepath=out+'\\preview-day.png'
bpy.ops.render.render(write_still=True)
for n,v in emissions:n.inputs['Emission Strength'].default_value=v
sun.data.energy=.055
bg.inputs['Color'].default_value=(.055,.10,.19,1);bg.inputs['Strength'].default_value=.22
scene.render.filepath=out+'\\preview-night.png'
bpy.ops.render.render(write_still=True)
sun.data.energy=2.4;bg.inputs['Color'].default_value=(.39,.49,.6,1);bg.inputs['Strength'].default_value=.55
for n,v in emissions:n.inputs['Emission Strength'].default_value=0
cam=scene.camera;cam.location=(330,-430,35);cam.rotation_euler=(Vector((0,0,130))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='PERSP';cam.data.lens=43
scene.render.filepath=out+'\\preview-structure.png'
bpy.ops.render.render(write_still=True)
