"""Photo-based SWFC architectural model, built in live Blender through MCP.
Units: metres. Main tower 492 m, original square 58 m. Detail dimensions approximate.
"""
import bpy, math, random, bmesh, json
from pathlib import Path
from mathutils import Vector, Quaternion

OUT = Path(r'C:\Users\JackieTang\Desktop\sample-data\Shanghai-World-Financial-Center')
H, R = 492.0, 58.0 / math.sqrt(2)
HOLE_BOTTOM, HOLE_TOP = 424.0, 477.0
rng = random.Random(28092026)
scene = bpy.data.scenes.new('SWFC_Architecture')
bpy.context.window.scene = scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1
collection = bpy.data.collections.new('SWFC_EXPORT')
scene.collection.children.link(collection)
root = bpy.data.objects.new('Shanghai_World_Financial_Center_ROOT', None)
collection.objects.link(root)
root['height_m'] = H
root['longitude'] = 121.50306
root['latitude'] = 31.23655
root['ellipsoid_height_m'] = 0.0
root['description'] = 'Photo-based architectural visualization, not a survey model. PBR emission is the Geo night channel.'
materials = {}
def material(name, color, metal=0.0, rough=0.4, emission=None, strength=0):
    m=bpy.data.materials.new(name); m.use_nodes=True
    n=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    n.inputs['Base Color'].default_value=(*color,1)
    n.inputs['Metallic'].default_value=metal
    n.inputs['Roughness'].default_value=rough
    if emission:
        n.inputs['Emission Color'].default_value=(*emission,1)
        n.inputs['Emission Strength'].default_value=strength
    m.diffuse_color=(*color,1)
    materials[name]=m
    return name
dark=material('Facade_recess_and_gaskets',(0.026,0.049,0.069),0.45,0.30)
glass=[material('Blue_silver_glass_%02d'%i,(0.12+i*.004,0.205+i*.005,0.265+i*.006),0.62,0.23+i*.008) for i in range(5)]
warm=material('Night_office_warm',(0.17,0.25,0.30),0.48,0.27,(1,.66,.32),1.8)
dim=material('Night_office_dim',(0.15,0.225,0.28),0.53,0.28,(1,.75,.48),0.48)
cool=material('Night_office_neutral',(0.17,0.255,0.315),0.50,0.25,(.65,.82,1),1.2)
silver=material('Brushed_aluminium',(0.57,0.64,0.67),0.78,0.28)
seam=material('Curtainwall_fine_mullions',(0.30,0.39,0.44),0.7,0.33)
stone=material('Podium_pale_granite',(0.34,0.37,0.38),0.08,0.7)
roof=material('Roof_and_plant',(0.095,0.13,0.15),0.25,0.6)
edge=material('Night_crown_cool_white',(0.62,0.7,0.75),0.55,0.28,(.64,.82,1),3)
lobby=material('Night_lobby_warm',(0.20,0.25,0.27),0.40,0.27,(1,.69,.36),1.4)
front_materials={}
for name in glass+[warm,dim,cool]:
    original=materials[name]
    copied=original.copy();copied.name='Arc_'+name
    shader=next(n for n in copied.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    idx=glass.index(name) if name in glass else 2
    color=(.30+idx*.003,.395+idx*.004,.46+idx*.005,1)
    shader.inputs['Base Color'].default_value=color
    shader.inputs['Metallic'].default_value=.68
    copied.diffuse_color=color
    materials[copied.name]=copied;front_materials[name]=copied.name
buffers={}
def face(points, mat, normal=None):
    if len(points)<3: return
    points=[tuple(p) for p in points]
    if normal is not None and (Vector(points[1])-Vector(points[0])).cross(Vector(points[2])-Vector(points[0])).dot(Vector(normal))<0:
        points.reverse()
    verts,faces=buffers.setdefault(mat,([],[])); off=len(verts)
    verts.extend(points); faces.append(tuple(range(off,off+len(points))))
def box(center, size, mat):
    x,y,z=center; a,b,c=[v/2 for v in size]
    v=[(x+sx*a,y+sy*b,z+sz*c) for sz in (-1,1) for sy in (-1,1) for sx in (-1,1)]
    for ids in [(0,2,3,1),(4,5,7,6),(0,1,5,4),(2,6,7,3),(0,4,6,2),(1,3,7,5)]: face([v[i] for i in ids],mat)
def beam(a,b,width,mat,depth=None):
    a,b=Vector(a),Vector(b); direction=(b-a).normalized()
    u=direction.cross(Vector((0,0,1)))
    if u.length<0.01: u=Vector((1,0,0))
    else: u.normalize()
    v=direction.cross(u).normalized(); u*=width/2; v*=(depth or width)/2
    q=[a-u-v,a+u-v,a+u+v,a-u+v,b-u-v,b+u-v,b+u+v,b-u+v]
    for ids in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]: face([q[i] for i in ids],mat)
def d(z): return 1.05+(R-1.05)*(1-(max(0,min(H,z))/H)**1.40)
def outer(z): return R-d(z)
def hole(z): return 20.3+(z-HOLE_BOTTOM)/(HOLE_TOP-HOLE_BOTTOM)*8.0
def clip(poly, fn):
    result=[]
    for a,b in zip(poly,poly[1:]+poly[:1]):
        fa,fb=fn(a),fn(b)
        if fa>=-1e-7: result.append(a)
        if (fa<0)!=(fb<0):
            t=fa/(fa-fb); result.append((a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1])))
    return result
def broad(poly,sy,mat,offset=0):
    if len(poly)<3:return
    mat=front_materials.get(mat,mat)
    face([(x,sy*(d(z)+offset),z) for x,z in poly],mat,(0,sy,.07))
def side(poly,sx,sy,mat,offset=0):
    if len(poly)<3:return
    face([(sx*(x+offset*.707),sy*(R-x+offset*.707),z) for x,z in poly],mat,(sx,sy,0))
def front_clip(poly,z0,z1):
    slope=(outer(z1)-outer(z0))/(z1-z0)
    f=lambda z:outer(z0)+(z-z0)*slope
    poly=clip(poly,lambda p:f(p[1])-p[0]); poly=clip(poly,lambda p:f(p[1])+p[0])
    if z0>=HOLE_BOTTOM-1e-5 and z1<=HOLE_TOP+1e-5:
        return [clip(poly,lambda p:-hole(p[1])-p[0]),clip(poly,lambda p:p[0]-hole(p[1]))]
    return [poly]
def panel_mat(floor,col,facet):
    # Stable groups of adjacent offices, a subdued and irregular night occupancy.
    r=random.Random(floor*1721+(col//3)*79+facet*901).random()
    if floor<4:return lobby if col%4!=0 else glass[1]
    if r<.10:return warm
    if r<.22:return dim
    if r<.28:return cool
    return glass[(floor+col*3+facet)%len(glass)]

# Six-sided cross sections cut by two sweeping arcs; true trapezoidal aperture.
levels=sorted(set([0.,18.,H,HOLE_BOTTOM,HOLE_TOP]+[18+i*2.15 for i in range(221) if 18+i*2.15<H]))
for j,(z0,z1) in enumerate(zip(levels,levels[1:])):
    for sy in (-1,1):
        for p in front_clip([(-R,z0),(R,z0),(R,z1),(-R,z1)],z0,z1): broad(p,sy,dark)
        for col in range(-29,29):
            x0,x1=col*1.44+.04,(col+1)*1.44-.04
            p=[(x0,z0+.075),(x1,z0+.075),(x1,z1-.075),(x0,z1-.075)]
            for q in front_clip(p,z0,z1):broad(q,sy,panel_mat(int((z0-18)/4.3)+4,col,sy+2),.025)
        # Horizontal transom lines follow the arc and stop cleanly at the opening.
        for p in front_clip([(-R,z0),(R,z0),(R,min(z0+.11,z1)),(-R,min(z0+.11,z1))],z0,z1): broad(p,sy,seam,.055)
    for sx in (-1,1):
        for sy in (-1,1):
            f=lambda p:p[0]-(outer(z0)+(p[1]-z0)*(outer(z1)-outer(z0))/(z1-z0))
            full=clip([(0,z0),(R,z0),(R,z1),(0,z1)],f)
            side(full,sx,sy,dark)
            for col in range(40):
                x0,x1=col*1.04+.035,min(R,(col+1)*1.04-.035)
                if x0>=R:continue
                p=clip([(x0,z0+.07),(x1,z0+.07),(x1,z1-.07),(x0,z1-.07)],f)
                side(p,sx,sy,panel_mat(int((z0-18)/4.3)+4,col,sx*2+sy+6),.025)
            band=clip([(0,z0),(R,z0),(R,min(z0+.13,z1)),(0,min(z0+.13,z1))],f)
            side(band,sx,sy,silver,.075)
    # Continuous bright metal ridges, not a rectangular extruded tower.
    for sx in (-1,1):
        for sy in (-1,1):
            beam((sx*outer(z0),sy*d(z0),z0),(sx*outer(z1),sy*d(z1),z1),.32,silver)

# Knife edges at the two uncut corners.
for sx in (-1,1):beam((sx*R,0,.5),(sx*R,0,H-.2),.55,silver)
# Aperture inner reveals with full depth and top/bottom observation floors.
for sx in (-1,1):
    face([(sx*hole(HOLE_BOTTOM),-d(HOLE_BOTTOM),HOLE_BOTTOM),(sx*hole(HOLE_BOTTOM),d(HOLE_BOTTOM),HOLE_BOTTOM),(sx*hole(HOLE_TOP),d(HOLE_TOP),HOLE_TOP),(sx*hole(HOLE_TOP),-d(HOLE_TOP),HOLE_TOP)],silver,(-sx,0,0))
for z,n in [(HOLE_BOTTOM,(0,0,1)),(HOLE_TOP,(0,0,-1))]:
    face([(-hole(z),-d(z),z),(hole(z),-d(z),z),(hole(z),d(z),z),(-hole(z),d(z),z)],roof,n)
for sy in (-1,1):
    for sx in (-1,1):
        beam((sx*hole(HOLE_BOTTOM),sy*(d(HOLE_BOTTOM)+.10),HOLE_BOTTOM),(sx*hole(HOLE_TOP),sy*(d(HOLE_TOP)+.10),HOLE_TOP),.65,silver)
        beam((sx*hole(HOLE_BOTTOM),sy*(d(HOLE_BOTTOM)+.47),HOLE_BOTTOM),(sx*hole(HOLE_TOP),sy*(d(HOLE_TOP)+.47),HOLE_TOP),.16,edge)
    for z in (HOLE_BOTTOM,HOLE_TOP):
        beam((-hole(z),sy*(d(z)+.12),z),(hole(z),sy*(d(z)+.12),z),.65,silver)
        beam((-hole(z),sy*(d(z)+.48),z),(hole(z),sy*(d(z)+.48),z),.18,edge)
    # Upper sky bridge glazing, just above aperture; lower observation gallery.
    for z in (HOLE_BOTTOM-4,HOLE_TOP+2.0):
        for c in range(-18,18):
            x=c*1.12
            broad([(x,z),(x+1.02,z),(x+1.02,z+2.7),(x,z+2.7)],sy,lobby,.11)
    beam((-outer(H)-.05,sy*d(H),H-.3),(outer(H)+.05,sy*d(H),H-.3),.25,edge)
    for sx in (-1,1):
        # Delicate upper outline only; avoids inventing full-height neon strips.
        for z0,z1 in zip([400,424,447,470],[424,447,470,491.5]):
            beam((sx*outer(z0),sy*(d(z0)+.24),z0),(sx*outer(z1),sy*(d(z1)+.24),z1),.14,edge)

# Roof cap follows the six-sided plan, keeping the export at exactly 492 m.
face([(-R,0,H),(-outer(H),-d(H),H),(outer(H),-d(H),H),(R,0,H),(outer(H),d(H),H),(-outer(H),d(H),H)],silver,(0,0,1))
face([(-R,0,0),(0,R,0),(R,0,0),(0,-R,0)],stone,(0,0,-1))
# Stepped entrance plinth, low perimeter parapet and four entrance canopies.
for rad,z0,z1 in [(47,0,.45),(45,.45,.85),(43,.85,1.2)]:
    pts=[(-rad,0),(0,-rad),(rad,0),(0,rad)]
    face([(x,y,z1) for x,y in pts],stone,(0,0,1))
    for a,b in zip(pts,pts[1:]+pts[:1]):face([(*a,z0),(*b,z0),(*b,z1),(*a,z1)],stone)
for sx in (-1,1):
    for sy in (-1,1):
        # Canopy along each diagonal base face, matching square footprint.
        a=Vector((sx*12,sy*(R-12),8)); b=Vector((sx*26,sy*(R-26),8)); n=Vector((sx,sy,0)).normalized()*5
        face([a,b,b+n,a+n],silver,(0,0,1))
        beam(a+n,b+n,.22,silver)
        for p in (a+n,b+n):beam((p.x,p.y,1.2),p,.28,silver)
        for i in range(6):
            p=a.lerp(b,(i+.5)/6)
            beam((p.x,p.y,1.2),(p.x,p.y,7.9),.16,silver)

for name,(verts,faces) in buffers.items():
    verts=[(x,y,max(0.0,min(H,z))) for x,y,z in verts]
    mesh=bpy.data.meshes.new(name+'_mesh');mesh.from_pydata(verts,[],faces);mesh.materials.append(materials[name]);mesh.update()
    obj=bpy.data.objects.new(name,mesh);collection.objects.link(obj);obj.parent=root

# Separate preview rig; no lights/cameras/ground are exported.
rig=bpy.data.collections.new('PREVIEW_ONLY');scene.collection.children.link(rig)
def rig_obj(name,data,location):
    obj=bpy.data.objects.new(name,data);rig.objects.link(obj);obj.location=location;return obj
cam=rig_obj('Preview_camera',bpy.data.cameras.new('Architectural_camera'),(800,-1350,700))
cam.rotation_euler=(Vector((0,0,246))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=570;scene.camera=cam
cam.data.clip_start=1;cam.data.clip_end=5000
sun=rig_obj('Preview_sun',bpy.data.lights.new('Preview_sun','SUN'),(0,0,600));sun.rotation_euler=(math.radians(28),math.radians(-25),math.radians(-30));sun.data.energy=2.5;sun.data.angle=math.radians(15)
world=bpy.data.worlds.new('SWFC_studio_world');world.use_nodes=True;scene.world=world
bg=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs['Color'].default_value=(.32,.42,.55,1);bg.inputs['Strength'].default_value=.6
scene.render.resolution_x=1000;scene.render.resolution_y=1400;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
scene.render.film_transparent=False
for obj in bpy.context.selected_objects:obj.select_set(False)
for obj in collection.objects:obj.select_set(True)
bpy.context.view_layer.objects.active=root
for area in bpy.context.screen.areas:
    if area.type=='VIEW_3D':
        area.spaces.active.region_3d.view_rotation=cam.rotation_euler.to_quaternion()
        area.spaces.active.region_3d.view_distance=760
        area.spaces.active.region_3d.view_location=(0,0,246)
        area.spaces.active.clip_end=5000
        area.spaces.active.clip_start=1
        area.spaces.active.shading.color_type='MATERIAL'
OUT.mkdir(exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(OUT/'shanghai-world-financial-center.glb'),export_format='GLB',use_selection=True,export_extras=True,export_animations=False,export_cameras=False,export_lights=False,export_yup=True)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'shanghai-world-financial-center.blend'))
print(json.dumps({'objects':len(collection.objects),'vertices':sum(len(o.data.vertices) for o in collection.objects if o.type=='MESH'),'polygons':sum(len(o.data.polygons) for o in collection.objects if o.type=='MESH'),'glb_bytes':(OUT/'shanghai-world-financial-center.glb').stat().st_size}))
