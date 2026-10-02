"""Portfolio renders using the saved Blender scene; presentation rig excluded from GLB."""
import bpy, math, os, sys
from mathutils import Vector
OUT=os.path.dirname(os.path.abspath(__file__))
scene=bpy.data.scenes['Taipei_101_Portfolio'];bpy.context.window.scene=scene
scene.render.engine='CYCLES';scene.cycles.samples=48;scene.cycles.use_denoising=True;scene.cycles.max_bounces=6
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences
    for backend in ['OPTIX','CUDA']:
        try:prefs.compute_device_type=backend;prefs.get_devices()
        except (TypeError,RuntimeError):continue
        gpu=[d for d in prefs.devices if d.type!='CPU']
        if gpu:
            for d in prefs.devices:d.use=d in gpu
            scene.cycles.device='GPU';print('GPU',[(d.name,d.type) for d in gpu]);break
except Exception as e:print('GPU unavailable',e)
cam=scene.camera;bg=next(n for n in scene.world.node_tree.nodes if n.type=='BACKGROUND')
sun=bpy.data.objects['101 preview sun'];fill=bpy.data.objects['101 large soft fill']
emissions=[]
for ob in bpy.data.collections['TAIPEI_101_EXPORT'].all_objects:
    if ob.type!='MESH':continue
    for mat in ob.data.materials:
        if mat and mat.get('night_strength') is not None and mat not in [m[0] for m in emissions]:
            emissions.append((mat,next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),mat['night_strength']))
# A studio backdrop receives real geometry shadows. It is outside the exported architecture.
ground=bpy.data.meshes.new('101 studio ground');ground.from_pydata([(-4000,-4000,-.04),(4000,-4000,-.04),(4000,4000,-.04),(-4000,4000,-.04)],[],[(0,1,2,3)])
m=bpy.data.materials.new('101 studio graphite');m.use_nodes=True
bs=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bs.inputs['Base Color'].default_value=(.085,.125,.155,1);bs.inputs['Roughness'].default_value=.84
ground.materials.append(m);ob=bpy.data.objects.new('101 studio ground',ground);scene.collection.objects.link(ob)
def camera(pos,target,scale):
    cam.location=pos;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
def daylight():
    for _,bs,_ in emissions:bs.inputs['Emission Strength'].default_value=0
    bg.inputs['Color'].default_value=(.13,.22,.30,1);bg.inputs['Strength'].default_value=.65
    sun.data.energy=2.7;sun.data.color=(1,.85,.66);fill.data.energy=1600000;fill.data.color=(.55,.8,1);scene.view_settings.exposure=0
def render(name):
    scene.render.filepath=os.path.join(OUT,name+'.png');bpy.ops.render.render(write_still=True);print('RENDER_COMPLETE',name,flush=True)
mode=sys.argv[sys.argv.index('--')+1] if '--' in sys.argv else 'all'
daylight();camera((780,-1050,655),(-10,-12,240),615)
scene.render.resolution_x=1440;scene.render.resolution_y=1800;scene.render.resolution_percentage=100
if mode=='draft':
    scene.cycles.samples=12;scene.render.resolution_percentage=45;render('draft-day')
else:
    if mode in ['all','day']:render('preview-day')
    if mode in ['all','night']:
        for _,bs,power in emissions:bs.inputs['Emission Strength'].default_value=power
        bg.inputs['Color'].default_value=(.018,.039,.09,1);bg.inputs['Strength'].default_value=.42
        sun.data.energy=.06;sun.data.color=(.45,.65,1);fill.data.energy=580000;fill.data.color=(.33,.54,1);scene.view_settings.exposure=.45
        render('preview-night')
    if mode in ['all','detail']:
        daylight();camera((135,-175,321),(0,0,306),112);scene.render.resolution_x=1600;scene.render.resolution_y=1200
        render('preview-detail')
    if mode in ['all','podium']:
        daylight();camera((190,-230,126),(-24,-28,30),212);scene.render.resolution_x=1600;scene.render.resolution_y=1200
        render('preview-podium')
    if mode in ['all','elevation']:
        daylight();camera((0,-1300,254),(0,0,254),565);scene.render.resolution_x=1200;scene.render.resolution_y=1800
        render('preview-elevation')
