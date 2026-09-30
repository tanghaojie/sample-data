"""Render portfolio views. Preview lighting is never included in exported GLB."""
import bpy, os, math, sys
from mathutils import Vector
OUT=os.path.dirname(os.path.abspath(__file__))
scene=bpy.data.scenes['Shanghai_Tower_Architectural_Study']
bpy.context.window.scene=scene
scene.render.engine='CYCLES'
scene.cycles.samples=48
scene.cycles.use_denoising=True
scene.cycles.max_bounces=6
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences
    prefs.get_devices()
    devices=list(prefs.devices)
    gpu=[d for d in devices if d.type!='CPU']
    if gpu:
        for d in devices:d.use=d in gpu
        scene.cycles.device='GPU'
except Exception as e:print('GPU detection:',e)
scene.render.resolution_x=1440;scene.render.resolution_y=1800
scene.render.resolution_percentage=100
cam=scene.camera
cam.data.clip_start=.1;cam.data.clip_end=10000
sun=bpy.data.objects['Preview sun'];fill=bpy.data.objects['Preview facade fill']
bg=next(n for n in scene.world.node_tree.nodes if n.type=='BACKGROUND')
sky=next(n for n in scene.world.node_tree.nodes if n.type=='TEX_SKY')
for link in list(bg.inputs['Color'].links):scene.world.node_tree.links.remove(link)
bg.inputs['Color'].default_value=(.12,.19,.28,1);bg.inputs['Strength'].default_value=.65
sun.data.energy=2.5;fill.data.energy=1600000
fill.location=(450,330,520)
fill.rotation_euler=(Vector((0,0,300))-fill.location).to_track_quat('-Z','Y').to_euler()
scene.view_settings.exposure=0
# A broad studio ground receives the actual podium/tree shadows, outside GLB.
ground_mesh=bpy.data.meshes.new('Preview ground')
ground_mesh.from_pydata([(-5000,-5000,-.08),(5000,-5000,-.08),(5000,5000,-.08),(-5000,5000,-.08)],[],[(0,1,2,3)])
ground_mat=bpy.data.materials.new('Preview ground slate');ground_mat.use_nodes=True
gbs=next(n for n in ground_mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
gbs.inputs['Base Color'].default_value=(.085,.12,.16,1);gbs.inputs['Roughness'].default_value=.8
ground_mesh.materials.append(ground_mat)
ground=bpy.data.objects.new('Preview ground',ground_mesh);scene.collection.objects.link(ground)
emissions=[]
for m in bpy.data.collections['SHANGHAI_TOWER_EXPORT'].all_objects:
    if m.type!='MESH':continue
    for mat in m.data.materials:
        if mat and mat.get('night_strength') is not None and mat not in [x[0] for x in emissions]:
            bs=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
            emissions.append((mat,bs,float(mat['night_strength'])))

def camera(pos,target,scale):
    cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
def render(name):
    scene.render.filepath=os.path.join(OUT,name+'.png')
    bpy.ops.render.render(write_still=True)
    print('RENDER_COMPLETE',name,flush=True)

mode=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'all'
for _,bs,_ in emissions:bs.inputs['Emission Strength'].default_value=0
camera((1250,580,710),(0,0,316),758)
if mode=='draft':
    scene.cycles.samples=12;scene.render.resolution_percentage=45
    render('draft-day')
else:
    if mode in ['all','day']:render('preview-day')
    if mode in ['all','night']:
        for _,bs,power in emissions:bs.inputs['Emission Strength'].default_value=power
        for link in list(bg.inputs['Color'].links):scene.world.node_tree.links.remove(link)
        bg.inputs['Color'].default_value=(.028,.052,.105,1);bg.inputs['Strength'].default_value=.45
        sun.data.energy=.08;sun.data.color=(.55,.7,1)
        fill.data.energy=650000;fill.data.color=(.38,.57,1)
        scene.view_settings.exposure=.45
        render('preview-night')
    if mode in ['all','crown']:
        for _,bs,_ in emissions:bs.inputs['Emission Strength'].default_value=0
        bg.inputs['Color'].default_value=(.12,.19,.28,1);bg.inputs['Strength'].default_value=.65
        sun.data.energy=2.5;sun.data.color=(1,.86,.70);fill.data.energy=1600000;fill.data.color=(.69,.84,1)
        scene.view_settings.exposure=0
        camera((290,150,850),(0,0,590),145)
        scene.render.resolution_x=1440;scene.render.resolution_y=1440
        render('preview-crown')
