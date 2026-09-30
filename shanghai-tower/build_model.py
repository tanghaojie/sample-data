"""Shanghai Tower: reference-based architectural visualization, in metres.
Original parametric reconstruction, not surveyed engineering geometry.
Run in Blender 5.2; preserve existing scenes by creating a dedicated scene.
"""
import bpy, math, random, json, os
from mathutils import Vector
from mathutils.geometry import tessellate_polygon

OUT = os.path.dirname(os.path.abspath(__file__))
TAU = math.tau
rng = random.Random(632120)
scene = bpy.data.scenes.new('Shanghai_Tower_Architectural_Study')
bpy.context.window.scene = scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1
asset = bpy.data.collections.new('SHANGHAI_TOWER_EXPORT')
scene.collection.children.link(asset)
rig = bpy.data.collections.new('PRESENTATION_ONLY')
scene.collection.children.link(rig)
root = bpy.data.objects.new('Shanghai_Tower_632m', None)
asset.objects.link(root)
root['height_m'] = 632.0
root['twist_degrees'] = 120.0
root['description'] = 'Photo and Gensler technical-paper based architectural visualization. Podium and details are approximate, not survey geometry.'
root['night_channel'] = 'PBR emissive; Cyber-Sight solar-altitude controlled'
root['longitude_wgs84'] = 121.50110
root['latitude_wgs84'] = 31.23356
root['units'] = 'metres; ground-centred Blender Z-up, glTF Y-up'
mats, buffers = {}, {}

def material(name, color, metal=0, rough=.5, emission=None, power=0, alpha=1):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bs = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    for key, value in [('Base Color', (*color,1)), ('Metallic',metal), ('Roughness',rough), ('Alpha',alpha)]:
        bs.inputs[key].default_value = value
    bs.inputs['Coat Weight'].default_value = .22 if metal > .3 else 0
    bs.inputs['Coat Roughness'].default_value = .18
    if emission:
        bs.inputs['Emission Color'].default_value = (*emission,1)
        bs.inputs['Emission Strength'].default_value = power
        m['night_strength'] = power
    m.diffuse_color = (*color,alpha)
    mats[name] = m
    return name

glasses = [material('Glass / silver-blue %02d'%i, (.19+i*.011,.29+i*.011,.35+i*.011), .46, .21+i*.009) for i in range(7)]
shadow = material('Gaskets / recessed anthracite',(.024,.044,.055),.35,.39)
alum = material('Mullions / brushed silver',(.39,.46,.49),.74,.3)
steel = material('Atrium structure / graphite',(.095,.135,.155),.72,.32)
silver = material('Crown / satin titanium',(.53,.6,.62),.78,.25)
clear = material('Sky garden / transparent blue glazing',(.27,.43,.49),.16,.23,alpha=.38)
coreglass = material('Inner curtain wall / deep teal',(.08,.145,.175),.45,.24)
slab = material('Mechanical floors / shadow metal',(.09,.125,.15),.65,.43)
bronze = material('Podium / champagne bronze',(.44,.32,.18),.72,.34)
bronzedark = material('Podium / bronze panel variation',(.32,.23,.13),.69,.4)
stone = material('Plaza / pale granite',(.48,.48,.445),.05,.84)
paving = material('Plaza / charcoal granite',(.21,.24,.25),.02,.87)
joint = material('Plaza / stone joints',(.1,.125,.13),.04,.88)
grass = material('Landscape / evergreen',(.09,.15,.065),0,.95)
leaf = material('Landscape / foliage light',(.14,.23,.085),0,.92)
wood = material('Landscape / bark and timber',(.14,.09,.045),0,.85)
warm = material('Night / occupied office amber',(.23,.31,.35),.43,.27,(1,.72,.40),1.0)
dim = material('Night / office subdued',(.20,.29,.34),.46,.26,(1,.83,.62),.26)
cool = material('Night / office cool white',(.23,.33,.40),.45,.24,(.61,.80,1),.8)
lobby = material('Night / lobby and sky garden',(.29,.35,.34),.34,.28,(1,.77,.47),1.7)
crownlight = material('Night / crown pearl light',(.53,.6,.64),.5,.27,(.68,.88,1),2.2)
seamlight = material('Night / restrained spiral edge',(.34,.44,.5),.65,.28,(.48,.7,1),.55)
pathlight = material('Night / plaza luminaires',(.64,.59,.44),.12,.4,(1,.68,.32),3.0)

def face(points, mat, part='Facade', smooth=False, outward=None):
    ps = [Vector(p) for p in points]
    clean=[]
    for p in ps:
        if not any((p-q).length < .00002 for q in clean):clean.append(p)
    ps=clean
    if len(ps)<3:return
    if outward is not None and (ps[1]-ps[0]).cross(ps[2]-ps[0]).dot(Vector(outward)) < 0:
        ps.reverse()
    key=(part,mat,smooth)
    if key not in buffers: buffers[key]=[[],[],{}]
    vs,fs,lookup=buffers[key]
    ids=[]
    for p in ps:
        k=tuple(round(v,5) for v in p)
        if k not in lookup: lookup[k]=len(vs);vs.append(tuple(p))
        ids.append(lookup[k])
    fs.append(tuple(ids))

def beam(a,b,width,mat,part='Metalwork',depth=None):
    a,b=Vector(a),Vector(b)
    d=b-a
    if d.length<.0001:return
    d.normalize()
    ref=Vector((0,0,1)) if abs(d.z)<.95 else Vector((0,1,0))
    u=d.cross(ref).normalized()*width/2
    v=d.cross(u).normalized()*(depth or width)/2
    p=[a-u-v,a+u-v,a+u+v,a-u+v,b-u-v,b+u-v,b+u+v,b-u+v]
    sides=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
    if part in ['Horizontal mullions','Crown horizontal rails','Podium floor fascias']:
        sides=sides[2:5]  # Exposed front, top and bottom; hidden rear/caps omitted.
    elif part in ['Vertical mullions','Inner structure','Crown vertical rails']:
        sides=sides[2:]  # Contiguous curtain-wall rods do not need end caps.
    for f in sides:face([p[i] for i in f],mat,part)

def box(center,size,mat,part='Podium'):
    c=Vector(center);x,y,z=[v/2 for v in size]
    p=[c+Vector(v) for v in [(-x,-y,-z),(x,-y,-z),(x,y,-z),(-x,y,-z),(-x,-y,z),(x,-y,z),(x,y,z),(-x,y,z)]]
    for f in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]:face([p[i] for i in f],mat,part)

def ring(radius,z,mat,part='Inner structure',thick=.2,n=144,center=(0,0)):
    for i in range(n):
        a,b=TAU*i/n,TAU*(i+1)/n
        beam((center[0]+radius*math.cos(a),center[1]+radius*math.sin(a),z),(center[0]+radius*math.cos(b),center[1]+radius*math.sin(b),z),thick,mat,part)

def disk(radius,z,mat,part='Crown',n=144):
    for i in range(n):
        a,b=TAU*i/n,TAU*(i+1)/n
        face([(0,0,z),(radius*math.cos(a),radius*math.sin(a),z),(radius*math.cos(b),radius*math.sin(b),z)],mat,part)

def radius(z): return 60.5 * math.exp(math.log(.55)*z/632)

def profile(t,z,offset=0):
    # Soft triangular lobes and one overlapping, recessed helical closure.
    a=TAU*t
    r=(1+.115*math.cos(3*a)+.022*math.sin(a))
    r-=.155*math.exp(-((1-t)/.037)**2)
    r=radius(z)*r+offset
    angle=a+math.radians(-34+120*z/632)
    return Vector((r*math.cos(angle),r*math.sin(angle),z))

def radial(p): return Vector((p.x,p.y,0)).normalized()

def band(z,width,mat,part='Horizontal mullions',offset=.16):
    for j in range(N):
        t0,t1=j/N,(j+1)/N
        p0,p1=profile(t0,z,offset),profile(t1,z,offset)
        beam(p0,p1,width,mat,part,depth=.22)
    beam(profile(1,z,offset),profile(0,z,offset),width,mat,part,depth=.22)

N=144
COURSES=240
ZBASE=6
ZBODY=584
STEP=(ZBODY-ZBASE)/COURSES
zones=[62,127,194,262,331,400,470,536]
lit_pattern={}
occupancy={}
for floor in range(43):
    for col in range(48):
        occupancy[(floor,col)]=rng.random()
for floor in range(128):
    for col in range(N):
        cluster=occupancy[(floor//3,col//3)]
        v=rng.random()
        lit_pattern[(floor,col)] = warm if cluster<.14 and v<.84 else dim if cluster<.32 and v<.8 else cool if .4<cluster<.46 and v<.8 else None

# Main panelized outer skin; panel gaps and frame shadows are actual geometry.
for row in range(COURSES):
    z0=ZBASE+row*STEP+.055
    z1=ZBASE+(row+1)*STEP-.055
    zm=(z0+z1)/2
    mechanical=any(abs(zm-h)<2.5 for h in zones)
    atrium=any(2.5<zm-h<10 for h in zones)
    for j in range(N):
        t0=(j+.015)/N;t1=(j+.985)/N
        mi=glasses[(j*7+row*3+j//8)%len(glasses)]
        if mechanical: mi=slab
        elif atrium: mi=clear
        else: mi=lit_pattern[(min(127,row//2),j)] or mi
        ps=[profile(t0,z0),profile(t1,z0),profile(t1,z1),profile(t0,z1)]
        face(ps,mi,'Outer curtain wall',True,radial(ps[0]))
        # A slim dark vertical joint with a silver edge, two courses per module.
        if row%2==0:
            beam(profile(j/N,z0,.15),profile(j/N,min(ZBODY,z0+STEP*2),.15),.10,alum,'Vertical mullions',depth=.14)
    band(ZBASE+row*STEP,.22,alum)
band(ZBODY,.38,silver)

# Single rising overlap: visible dark return and articulated silver lips.
for row in range(COURSES):
    z0=ZBASE+row*STEP;z1=z0+STEP
    face([profile(1,z0,-.09),profile(0,z0,-.09),profile(0,z1,-.09),profile(1,z1,-.09)],shadow,'Spiral recessed return')
    beam(profile(0,z0,.27),profile(0,z1,.27),.48,silver,'Spiral leading lip',depth=.34)
    beam(profile(1,z0,.24),profile(1,z1,.24),.36,alum,'Spiral trailing lip')
    beam(profile(.0025,z0,.34),profile(.0025,z1,.34),.12,seamlight,'Spiral night accent')

# Circular inner skin, zoned sky lobbies, genuine radial trusses in cavity.
for row in range(128):
    z0=7+row*4.48;z1=min(582,z0+4.28)
    if z0>=582:break
    r=radius((z0+z1)/2)*.75
    for j in range(96):
        a,b=TAU*j/96,TAU*(j+1)/96
        ps=[(r*math.cos(a),r*math.sin(a),z0),(r*math.cos(b),r*math.sin(b),z0),(r*math.cos(b),r*math.sin(b),z1),(r*math.cos(a),r*math.sin(a),z1)]
        mi=lobby if any(0<z0-h<9 for h in zones) else coreglass
        face(ps,mi,'Inner circular curtain wall',True,(math.cos(a),math.sin(a),0))
    if row%2==0:ring(r,z0,slab,thick=.28,n=96)
for h in zones:
    band(h-.4,.65,steel,'Mechanical ring beams',-.42)
    band(h+9,.38,alum,'Atrium ring beams',-.34)
    r=radius(h)*.75
    disk(r,h+.1,paving,'Sky garden floors',96)
    for j in range(24):
        t=j/24;p=profile(t,h+1,-.8)
        q=radial(p)*r;q.z=h+1
        beam(q,p,.30,steel,'Radial atrium struts')
        p2=profile((j+1)/24,h+8,-.8)
        beam(q,p2,.16,steel,'Atrium diagonal braces')
        beam(profile(t,h+.3,-.6),profile(t,h+9,-.6),.13,alum,'Atrium suspension rods')

# Open, asymmetric crown. Maximum is exactly 632 m; no invented antenna.
def rim(t): return 606+26*math.sin(math.pi*t)**2
max_t=.5
ts=sorted(set([i/N for i in range(N+1)]+[max_t]))
for j in range(len(ts)-1):
    t0,t1=ts[j],ts[j+1]
    top0,top1=rim(t0),rim(t1)
    # Each crown horizontal course is clipped against the sloping parapet.
    z=584
    while z<max(top0,top1):
        low0,low1=min(z,top0),min(z,top1)
        high0,high1=min(z+2.35,top0),min(z+2.35,top1)
        if high0-low0>.01 or high1-low1>.01:
            ps=[profile(t0,low0,-.02),profile(t1,low1,-.02),profile(t1,high1,-.02),profile(t0,high0,-.02)]
            face(ps,glasses[(j//2)%7],'Crown outer glazing',True,radial(ps[0]))
            beam(profile(t0,low0,.14),profile(t1,low1,.14),.25,silver,'Crown horizontal rails')
        z+=2.35
    beam(profile(t0,584,.14),profile(t0,top0,.14),.20,alum,'Crown vertical rails')
    # Offset top lip down so geometry never exceeds the architectural height.
    a,b=profile(t0,top0-.28,.12),profile(t1,top1-.28,.12)
    beam(a,b,.48,silver,'Crown continuous coping',depth=.28)
    beam(profile(t0,top0-.95,.3),profile(t1,top1-.95,.3),.16,crownlight,'Crown pearl night rim')
    ia,ib=profile(t0,top0-.4,-1.2),profile(t1,top1-.4,-1.2)
    face([profile(t0,587,-1.2),profile(t1,587,-1.2),ib,ia],steel,'Crown inner wall',True,radial(ia)*-1)
    if j%2==0:
        beam(profile(t0,587,-1.75),profile(t0,top0-1.3,-1.75),.32,silver,'Crown inner ribs')
for t in [0,1]:
    beam(profile(t,584,.3),profile(t,606,.3),.55,silver,'Crown spiral lip')
    beam(profile(t,584,.45),profile(t,605,.45),.14,crownlight,'Crown spiral night lip')
for j in range(36):
    t=j/36
    p=profile(t,588,-2)
    q=radial(p)*22;q.z=588
    beam(q,p,.3,steel,'Crown radial structure')
    beam(profile(t,590,-2),profile((j+1)/36,601,-2),.18,alum,'Crown bracing')
disk(27,587,paving,'Crown maintenance terrace')
ring(18,588,silver,'Crown plant enclosure',thick=.45,n=72)
for j in range(14):
    a=TAU*j/14
    box((16*math.cos(a),16*math.sin(a),589),(2.4,2.1,2),slab,'Crown plant equipment')
    for k in range(3):box((16*math.cos(a),16*math.sin(a),590.05+k*.14),(2.6,2.3,.06),alum,'Crown equipment louvres')

# Entrance podium: bronze wave roof above a curved glazed retail base.
PN=192
def podium(t,z,expand=0):
    a=TAU*t
    return Vector((12+(84+expand)*math.cos(a),-8+(68+expand)*math.sin(a),z))
for j in range(PN):
    t0,t1=j/PN,(j+1)/PN
    a=TAU*(t0+t1)/2
    for f in range(4):
        z0=1.2+f*4.6;z1=z0+4.3
        ps=[podium(t0,z0),podium(t1,z0),podium(t1,z1),podium(t0,z1)]
        face(ps,lobby if j%11<5 and f==0 else glasses[(j+f)%7],'Podium retail glazing',True,(math.cos(a),math.sin(a),0))
        beam(podium(t0,z0,.15),podium(t1,z0,.15),.32,bronze,'Podium floor fascias')
    beam(podium(t0,1,.1),podium(t0,19.5,.1),.24,bronze,'Podium vertical mullions')
for j in range(PN):
    a0,a1=TAU*j/PN,TAU*(j+1)/PN
    # Roof ribbon lifts at two public entrances and falls into the bronze walls.
    h0=23+6*math.cos(2*a0-.7)+2*math.sin(a0)
    h1=23+6*math.cos(2*a1-.7)+2*math.sin(a1)
    p0,p1=podium(j/PN,h0,1.2),podium((j+1)/PN,h1,1.2)
    inner0=Vector((p0.x*.68,p0.y*.68,h0+2.4))
    inner1=Vector((p1.x*.68,p1.y*.68,h1+2.4))
    face([p0,p1,inner1,inner0],bronze if j%9 else bronzedark,'Sculpted bronze roof')
    face([podium(j/PN,18.7,1.2),podium((j+1)/PN,18.7,1.2),p1,p0],bronze if j%5 else bronzedark,'Bronze roof skirt')
    beam(p0,p1,.36,bronze,'Podium roof trim')
    # Narrow joint lines make the cladding read as fine laid panels.
    if j%2==0:beam(p0,inner0,.075,bronzedark,'Bronze roof panel seams')
    beam(podium(j/PN,19,.7),podium((j+1)/PN,19,.7),.12,pathlight,'Podium night cornice')

# Elliptical plazas fit the sculptural podium, with paving joints and tree beds.
for j in range(PN):
    a,b=TAU*j/PN,TAU*(j+1)/PN
    p0=(108*math.cos(a)+8,89*math.sin(a)-5,.08)
    p1=(108*math.cos(b)+8,89*math.sin(b)-5,.08)
    face([(8,-5,.08),p0,p1],stone,'Plaza stone apron')
    if j%4==0:beam((8,-5,.1),p0,.08,joint,'Paving radial joints',depth=.04)
for factor in [.80,.87,.94,1]:
    for j in range(PN):
        a,b=TAU*j/PN,TAU*(j+1)/PN
        beam((8+108*factor*math.cos(a),-5+89*factor*math.sin(a),.12),(8+108*factor*math.cos(b),-5+89*factor*math.sin(b),.12),.09,joint,'Paving perimeter joints',depth=.04)

def foliage(center,r,mat):
    cx,cy,cz=center
    for k in range(5):
        p0=-math.pi/2+math.pi*k/5;p1=-math.pi/2+math.pi*(k+1)/5
        for j in range(9):
            a,b=TAU*j/9,TAU*(j+1)/9
            ps=[(cx+r*math.cos(p)*math.cos(t),cy+r*math.cos(p)*math.sin(t),cz+r*1.12*math.sin(p)) for p,t in [(p0,a),(p0,b),(p1,b),(p1,a)]]
            face(ps,mat,'Landscape tree canopies',True)
for j in range(38):
    a=TAU*j/38
    x,y=8+102*math.cos(a),-5+83*math.sin(a)
    box((x,y,.22),(4.3,4.3,.3),paving,'Landscape planters')
    box((x,y,.4),(3.7,3.7,.09),grass,'Landscape planters')
    beam((x,y,.45),(x,y,4.2),.26,wood,'Landscape tree trunks')
    for k in range(3):
        foliage((x+rng.uniform(-1,1),y+rng.uniform(-1,1),4.8+rng.uniform(-.5,.8)),rng.uniform(1.6,2.2),grass if k%2 else leaf)
    if j%2==0:
        box((x-2,y-2,.5),(.55,.55,1),steel,'Plaza bollards')
        box((x-2,y-2,1.03),(.46,.46,.09),pathlight,'Plaza bollard lights')
for x,y in [(26,-75),(-26,-70),(91,-20)]:
    box((x,y,4.6),(13,7,.28),silver,'Public entrance canopies')
    box((x,y,4.38),(12.5,6.5,.10),lobby,'Canopy luminous soffits')
    for dx in [-5,5]:beam((x+dx,y,0),(x+dx,y,4.5),.28,alum,'Entrance canopy columns')

# Material-batched meshes make a detailed model practical for Cesium.
counts={}
for (part,mi,smooth),(vs,fs,_) in buffers.items():
    me=bpy.data.meshes.new(part+' mesh')
    me.from_pydata(vs,[],fs);me.materials.append(mats[mi]);me.validate(verbose=False);me.update()
    ob=bpy.data.objects.new(part+' | '+mi,me);asset.objects.link(ob);ob.parent=root
    if smooth:
        for p in me.polygons:p.use_smooth=True
    counts[part]=counts.get(part,0)+len(fs)
buffers.clear()

# Export only the architectural asset; rigs and world lighting stay in .blend.
for ob in scene.objects:ob.select_set(False)
for ob in asset.objects:ob.select_set(True)
bpy.context.view_layer.objects.active=next(o for o in asset.objects if o.type=='MESH')
export_args=dict(filepath=os.path.join(OUT,'shanghai-tower.glb'),use_selection=True,export_yup=True,export_apply=True,export_materials='EXPORT',export_extras=True,export_cameras=False,export_lights=False)
try:
    bpy.ops.export_scene.gltf(export_format='GLB',**export_args)
except TypeError as e:
    raise RuntimeError('Exporter format must be checked against installed dynamic enum: '+str(e))

# Presentation camera and sky. There are no baked daylight colors or lights in GLB.
def light(name,kind,location,energy,color,size=None):
    data=bpy.data.lights.new(name,kind);data.energy=energy;data.color=color
    if size is not None:data.size=size
    ob=bpy.data.objects.new(name,data);rig.objects.link(ob);ob.location=location
    ob.rotation_euler=(Vector((0,0,310))-ob.location).to_track_quat('-Z','Y').to_euler()
    return ob
world=bpy.data.worlds.new('Shanghai presentation sky');world.use_nodes=True;scene.world=world
bg=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND')
sky=world.node_tree.nodes.new('ShaderNodeTexSky');sky.sky_type='MULTIPLE_SCATTERING'
sky.sun_elevation=math.radians(28);sky.sun_rotation=math.radians(125);sky.sun_size=math.radians(3)
world.node_tree.links.new(sky.outputs['Color'],bg.inputs['Color']);bg.inputs['Strength'].default_value=.35
for link in list(bg.inputs['Color'].links):world.node_tree.links.remove(link)
bg.inputs['Color'].default_value=(.12,.19,.28,1);bg.inputs['Strength'].default_value=.65
sun=light('Preview sun','SUN',(600,-500,900),2.5,(1,.86,.70));sun.data.angle=math.radians(5)
light('Preview facade fill','AREA',(450,330,520),1600000,(.69,.84,1),340)
camdata=bpy.data.cameras.new('Architecture hero camera');camdata.type='ORTHO';camdata.ortho_scale=758
camdata.clip_start=.1;camdata.clip_end=10000
cam=bpy.data.objects.new('Architecture hero camera',camdata);rig.objects.link(cam);cam.location=(1250,580,710)
cam.rotation_euler=(Vector((0,0,316))-cam.location).to_track_quat('-Z','Y').to_euler();scene.camera=cam
scene.render.engine='BLENDER_EEVEE'
scene.render.resolution_x=1440;scene.render.resolution_y=1800;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.view_settings.exposure=0
for area in bpy.context.screen.areas if bpy.context.screen else []:
    if area.type=='VIEW_3D':
        area.spaces.active.region_3d.view_distance=1600
        area.spaces.active.region_3d.view_perspective='CAMERA'
        area.spaces.active.region_3d.view_camera_zoom=10
        area.spaces.active.region_3d.view_location=(0,0,316)
        area.spaces.active.region_3d.view_rotation=cam.rotation_euler.to_quaternion()
        area.spaces.active.clip_end=10000
        area.spaces.active.shading.type='MATERIAL'
        area.spaces.active.shading.use_scene_world=True
        area.spaces.active.shading.use_scene_lights=True
        area.spaces.active.overlay.show_overlays=False
for ob in scene.objects:ob.select_set(False)
for m in mats.values():
    if m.get('night_strength') is not None:
        next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED').inputs['Emission Strength'].default_value=0
scene['asset_collection']='SHANGHAI_TOWER_EXPORT'
scene['documentation']='See README.md for sources, modelling scope and Geo placement.'
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'shanghai-tower.blend'))
summary={'height_m':632,'twist_degrees':120,'outer_facade_courses':COURSES,'panels_per_course':N,'mesh_count':sum(o.type=='MESH' for o in asset.objects),'parts_faces':counts}
with open(os.path.join(OUT,'build-summary.json'),'w',encoding='utf-8') as f:json.dump(summary,f,indent=2)
print('SHANGHAI_TOWER_COMPLETE '+json.dumps(summary))
