import bpy,math
from pathlib import Path
from mathutils import Vector
OUT=Path(__file__).parent
scene=bpy.context.scene
scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True
scene.render.resolution_x=1800;scene.render.resolution_y=1250;scene.render.resolution_percentage=100
scene.render.threads_mode='AUTO'
cam=scene.camera
cam.location=(150,-2350,1470);cam.rotation_euler=(Vector((0,30,0))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=2340
bg=next(n for n in scene.world.node_tree.nodes if n.type=='BACKGROUND')
sun=next(o for o in scene.objects if o.type=='LIGHT' and o.data.type=='SUN')
em=[]
for ob in scene.objects:
    if ob.type=='MESH':
        for m in ob.data.materials:
            if m.use_nodes:
                n=next(n for n in m.node_tree.nodes if n.bl_idname=='ShaderNodeBsdfPrincipled')
                if n.inputs['Emission Strength'].default_value>0 and any(n.inputs['Emission Color'].default_value[:3]):em.append((n,n.inputs['Emission Strength'].default_value))
for n,v in em:n.inputs['Emission Strength'].default_value=0
bg.inputs['Color'].default_value=(.46,.58,.73,1);bg.inputs['Strength'].default_value=.38
sun.data.energy=3.0;sun.data.color=(1,.9,.75);sun.rotation_euler=(math.radians(58),math.radians(-18),math.radians(-32))
scene.render.filepath=str(OUT/'preview-day.png');bpy.ops.render.render(write_still=True)
for n,v in em:n.inputs['Emission Strength'].default_value=v
bg.inputs['Color'].default_value=(.05,.10,.19,1);bg.inputs['Strength'].default_value=.24
sun.data.energy=.08
scene.render.filepath=str(OUT/'preview-night.png');bpy.ops.render.render(write_still=True)
for n,v in em:n.inputs['Emission Strength'].default_value=0
bg.inputs['Color'].default_value=(.46,.58,.73,1);bg.inputs['Strength'].default_value=.38;sun.data.energy=3.0
cam.location=(810,-950,475);cam.rotation_euler=(Vector((120,-95,12))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=1180
scene.render.filepath=str(OUT/'preview-detail.png');bpy.ops.render.render(write_still=True)
cam.location=(0,0,2300);cam.rotation_euler=(0,0,0);cam.data.ortho_scale=2280
scene.render.resolution_x=1600;scene.render.resolution_y=1450
scene.render.filepath=str(OUT/'preview-plan.png');bpy.ops.render.render(write_still=True)
