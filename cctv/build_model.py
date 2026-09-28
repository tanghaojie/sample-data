"""CCTV Headquarters / photographic architectural study.
234 m crown, 6 degree double-axis leaning towers, opposite L base/overhang.
Built in the live Blender application via Blender MCP. No imported mesh assets.
"""
import bpy, math, random, bmesh
from mathutils import Vector
from mathutils.geometry import tessellate_polygon

OUT = r'C:\Users\JackieTang\Desktop\sample-data\cctv'
previous=bpy.data.scenes.get('CCTV_Architectural_Study')
if previous:
    for ob in list(previous.objects):bpy.data.objects.remove(ob,do_unlink=True)
    bpy.data.scenes.remove(previous)
scene=bpy.data.scenes.new('CCTV_Architectural_Study')
bpy.context.window.scene=scene
scene.unit_settings.system='METRIC'
scene.unit_settings.scale_length=1
col=bpy.data.collections.new('CCTV_EXPORT');scene.collection.children.link(col)
root=bpy.data.objects.new('CCTV_Headquarters_234m',None);col.objects.link(root)
root['description']='Photo-based architectural study; detail dimensions approximate, not survey or engineering geometry.'
root['height_m']=234.0;root['night_channel']='PBR Emissive, controlled by Cyber-Sight solar altitude'
root['longitude']=116.4577;root['latitude']=39.9123
mats={};buf={}
def mat(name,c,metal=0,rough=.5,em=None,power=0):
    m=bpy.data.materials.new(name);m.use_nodes=True
    n=next(n for n in m.node_tree.nodes if n.bl_idname=='ShaderNodeBsdfPrincipled')
    n.inputs['Base Color'].default_value=(*c,1);n.inputs['Metallic'].default_value=metal;n.inputs['Roughness'].default_value=rough
    if em:
        n.inputs['Emission Color'].default_value=(*em,1);n.inputs['Emission Strength'].default_value=power
    m.diffuse_color=(*c,1);mats[name]=m;buf[name]=[[],[]];return name
shell=mat('01_Recessed_shadow_gaskets',(.032,.055,.068),.35,.36)
glass=[mat('02_Silver_blue_glazing_%02d'%i,(.21+i*.009,.30+i*.009,.34+i*.009),.48,.20+i*.012) for i in range(6)]
steel=mat('03_Exposed_diagrid_graphite',(.105,.15,.17),.78,.31)
edge=mat('04_Diagrid_silver_edge',(.39,.46,.48),.78,.28)
mull=mat('05_Fine_curtainwall_mullions',(.24,.32,.35),.62,.37)
roof=mat('06_Roof_titanium',(.22,.28,.29),.52,.4)
stone=mat('07_Limestone_plinth',(.49,.48,.43),.06,.8)
paving=mat('08_Plaza_granite',(.3,.32,.31),.03,.86)
darkstone=mat('09_Paving_joints',(.12,.15,.15),.04,.86)
grass=mat('10_Terrace_planting',(.105,.145,.087),0,.95)
warm=mat('11_Night_office_warm',(.21,.28,.30),.48,.3,(1,.71,.41),.9)
dim=mat('12_Night_office_dim',(.20,.28,.31),.56,.29,(1,.8,.56),.18)
cool=mat('13_Night_office_cool',(.22,.31,.36),.5,.28,(.66,.86,1),.65)
wash=mat('14_Night_inner_facade_wash',(.29,.38,.39),.55,.29,(.55,.76,.8),.14)
soff=mat('15_Night_luminous_soffit',(.32,.39,.4),.5,.34,(.66,.88,.91),.65)
lobby=mat('16_Night_lobby',(.25,.28,.27),.4,.3,(1,.76,.43),2.2)
light=mat('17_Night_landscape_luminaires',(.64,.62,.5),.15,.42,(1,.72,.35),3)
dishmat=mat('18_Satellite_porcelain',(.73,.75,.71),.25,.4)
def face(points,m,normal=None):
    ps=[Vector(p) for p in points]
    if normal is not None and (ps[1]-ps[0]).cross(ps[2]-ps[0]).dot(Vector(normal))<0: ps.reverse()
    vs,fs=buf[m];i=len(vs);vs.extend(tuple(p) for p in ps);fs.append(tuple(range(i,i+len(ps))))
def beam(a,b,w,m,depth=None,n=None):
    a,b=Vector(a),Vector(b);d=b-a
    if d.length<.001:return
    d.normalize();normal=Vector(n).normalized() if n is not None else Vector((0,0,1))
    if abs(d.dot(normal))>.98:normal=Vector((0,1,0))
    u=d.cross(normal).normalized()*w/2;v=d.cross(u).normalized()*(depth or w)/2
    p=[a-u-v,a+u-v,a+u+v,a-u+v,b-u-v,b+u-v,b+u+v,b-u+v]
    for ids in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]:face([p[i] for i in ids],m)
def box(a,b,m):
    x,y,z=a;X,Y,Z=b;p=[(x,y,z),(X,y,z),(X,Y,z),(x,Y,z),(x,y,Z),(X,y,Z),(X,Y,Z),(x,Y,Z)]
    for ids in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]:face([p[i] for i in ids],m)
def disk(c,r,n,m,segments=24):
    c,n=Vector(c),Vector(n).normalized();u=n.cross(Vector((1,0,0)))
    if u.length<.1:u=n.cross(Vector((0,1,0)))
    u.normalize();v=n.cross(u)
    face([c+(u*math.cos(i*math.tau/segments)+v*math.sin(i*math.tau/segments))*r for i in range(segments)],m,n)

facade_id=0
def facade(p0,p1,p2,p3,inner=False,spacing=16,detail=True,soffit=False):
    global facade_id
    facade_id+=1;fid=facade_id
    a,b,c,d=map(Vector,(p0,p1,p2,p3));n=(b-a).cross(d-a).normalized()
    W=((b-a).length+(c-d).length)/2;H=((d-a).length+(c-b).length)/2
    def p(u,v,off=0):return a.lerp(b,u).lerp(d.lerp(c,u),v)+n*off
    face([a,b,c,d],shell,n)
    nx=max(1,round(W/(1.5 if detail else 3)));ny=max(1,round(H/(3.85 if not soffit else 3)))
    # Individual opaque PBR panes provide reliable depth and avoid alpha sorting.
    for j in range(ny):
        for i in range(nx):
            r=random.Random(fid*19191+j*737+(i//3)*41).random()
            m=glass[(i//3+j*2+fid)%6]
            if soffit:m=soff
            elif j<2 and a.z<1:m=lobby if i%6 else glass[1]
            elif r<.07:m=warm
            elif r<.15:m=dim
            elif r<.20:m=cool
            elif inner:m=wash
            du=.035/W;dv=.055/H
            face([p(i/nx+du,j/ny+dv,.025),p((i+1)/nx-du,j/ny+dv,.025),p((i+1)/nx-du,(j+1)/ny-dv,.025),p(i/nx+du,(j+1)/ny-dv,.025)],m,n)
            if not soffit:
                # Opaque spandrel hides the slab edge and gives illuminated offices a believable clear height.
                face([p(i/nx+du,j/ny+dv,.04),p((i+1)/nx-du,j/ny+dv,.04),p((i+1)/nx-du,(j+.24)/ny,.04),p(i/nx+du,(j+.24)/ny,.04)],glass[1],n)
    for i in range(nx+1):beam(p(i/nx,0,.07),p(i/nx,1,.07),.065,mull,.06,n)
    for j in range(ny+1):beam(p(0,j/ny,.07),p(1,j/ny,.07),.10,mull,.075,n)
    # Structural diamonds. Secondary diagonals are concentrated around base and transfer zone.
    def diag(sign,k,vlo=0,vhi=1,width=.43):
        slope=sign*.63*H/W
        bounds=[vlo,vhi]
        for u in (0,1):
            v=(u-k)/slope
            if vlo<v<vhi:bounds.append(v)
        bounds.sort()
        for l,h in zip(bounds,bounds[1:]):
            mid=k+slope*(l+h)/2
            if 0<=mid<=1:
                u0=max(0,min(1,k+slope*l));u1=max(0,min(1,k+slope*h))
                beam(p(u0,l,.18),p(u1,h,.18),width,steel,.23,n)
                beam(p(u0,l,.305),p(u1,h,.305),width*.15,edge,.035,n)
    step=spacing/W
    for sign in (-1,1):
        for k in range(-int(H/spacing)-3,int((W+H)/spacing)+4):
            phase=(sign*.63*a.z/W)%step if not soffit else 0
            diag(sign,k*step+phase)
            if not soffit and H>50:
                for low,high in [(0,48),(132,176)]:
                    vlo=max(0,(low-a.z)/max(1,d.z-a.z));vhi=min(1,(high-a.z)/max(1,d.z-a.z))
                    if vhi>vlo:diag(sign,(k+.5)*step+phase,vlo,vhi,.26)
    for a0,b0 in [((0,0),(1,0)),((0,1),(1,1)),((0,0),(0,1)),((1,0),(1,1))]:
        beam(p(*a0,.14),p(*b0,.14),.32,steel,.25,n)

s=math.tan(math.radians(6))
def rect(t,z):
    k=s*z
    return (-81+k,-39+k,-75+k,-15+k) if t==0 else (25-k,85-k,34-k,76-k)
def corners(t,z):
    x,X,y,Y=rect(t,z);return [(x,y,z),(X,y,z),(X,Y,z),(x,Y,z)]
for t in (0,1):
    for z0,z1 in [(0,46.45),(46.45,161)]:
        a=corners(t,z0);b=corners(t,z1)
        for i in range(4):
            # Podium joins rear of the left tower and left side of right tower.
            if z0==0 and ((t==0 and i==2) or(t==1 and i==3)):continue
            facade(a[i],a[(i+1)%4],b[(i+1)%4],b[i],inner=(t==0 and i==1)or(t==1 and i==0))

def outline(z):
    a,A,b,B=rect(0,z);c,C,d,D=rect(1,z)
    return [(a,b,z),(C,b,z),(C,D,z),(c,D,z),(c,B,z),(a,B,z)]
bottom=outline(161)
# Each crown vertex lies on the same sloping roof plane; high point exactly 234m.
top=[]
def roof_height(x,y):return 234-.067*(x-(-81+s*234))-.12*(y-(-75+s*234))
for i in range(6):
    z=226
    for _ in range(12):
        x,y,_=outline(z)[i];z=roof_height(x,y)
    x,y,_=outline(z)[i];top.append((x,y,z))
for i in range(6):facade(bottom[i],bottom[(i+1)%6],top[(i+1)%6],top[i],inner=i in(3,4),spacing=16)
# Sloped roof split across the concave L, avoiding concave-fan export artifacts.
for tri in tessellate_polygon([[Vector(p) for p in top]]):face([top[i] for i in tri],roof,(0,0,1))
for a,b in zip(top,top[1:]+top[:1]):beam(a,b,.28,edge)
# Soffit closes only the unsupported arms; the void remains open all the way through.
a,A,b,B=rect(0,161);c,C,d,D=rect(1,161)
facade((A,B,161),(C,B,161),(C,b,161),(A,b,161),spacing=16,soffit=True)
facade((c,d,161),(C,d,161),(C,B,161),(c,B,161),spacing=16,soffit=True)
for x,y in [(A+14,b+18),(A+31,b+18),(A+48,b+18)]:
    disk((x,y,160.61),2.1,(0,0,-1),steel)
    disk((x,y,160.58),1.58,(0,0,-1),shell)
    for ang in range(0,360,45):
        aa=math.radians(ang);beam((x+1.55*math.cos(aa),y+1.55*math.sin(aa),160.53),(x+2*math.cos(aa),y+2*math.sin(aa),160.53),.10,edge)

# Low L-shaped production base, opposite the cantilever, completes the continuous loop.
z=46.45;a,A,b,B=rect(0,z);c,C,d,D=rect(1,z)
basepoly=[(-81,-15),(A,B),(A,d),(c,d),(c,D),(-81,D)]
# Deliberately join the two towers with broad 9-storey wings.
for i,j in [(1,2),(2,3),(4,5),(5,0)]:
    x,y=basepoly[i];X,Y=basepoly[j]
    facade((x,y,1.4),(X,Y,1.4),(X,Y,z),(x,y,z),inner=i in (1,2),spacing=17)
face([(-81,-15,z),(A,B,z),(A,d,z),(-81,D,z)],roof,(0,0,1))
face([(-81,D,z),(A,d,z),(c,d,z),(c,D,z)],roof,(0,0,1))
for x in [-58,-45,-32,-19,-6,7]:
    center=Vector((x,53,z+3.2));normal=Vector((.05,-.55,.835)).normalized()
    u=Vector((1,0,0));v=normal.cross(u)
    beam((x,53,z),(x,53,z+3),.3,steel)
    # Shallow parabolic satellite reflector, 32 segments and concentric rings.
    for j in range(4):
        r0=j*2.1/4;r1=(j+1)*2.1/4
        for k in range(32):
            points=[]
            for r,ang in [(r0,k),(r1,k),(r1,k+1),(r0,k+1)]:
                aa=ang*math.tau/32;points.append(center+u*(r*math.cos(aa))+v*(r*math.sin(aa))+normal*(r*r*.10))
            if j==0:face(points[1:]+points[:1],dishmat)
            else:face(points,dishmat)
    beam(center,center+normal*1.6,.10,steel)
    disk(center+normal*1.65,.21,normal,steel)

# Crisp terraced podium and a restrained architectural plaza.
box((-98,-94,0),(101,91,.65),paving)
box((-91,-86,.65),(95,85,1.3),stone)
for x in range(-88,96,8):beam((x,-85,1.31),(x,84,1.31),.045,darkstone,.012)
for y in range(-82,86,8):beam((-90,y,1.31),(94,y,1.31),.045,darkstone,.012)
for k in range(4):box((-38,-88-k*1.4,.15*k),(30,-86-k*1.4,.15*(k+1)),stone)
for x0,x1,y0,y1 in [(-28,13,-62,-41),(-21,15,-24,-5),(-7,16,8,23),(-78,-60,4,19)]:
    box((x0,y0,1.3),(x1,y1,1.8),darkstone);box((x0+.4,y0+.4,1.8),(x1-.4,y1-.4,1.95),grass)
    beam((x0,y0,1.85),(x1,y0,1.85),.09,light)
# Glass entry canopy and expressed slender columns.
for a,b in [((-73,-79,5.6),(-48,-79,5.6)),((43,78,5.6),(72,78,5.6))]:
    a,b=Vector(a),Vector(b);ext=Vector((0,-4 if a.y<0 else 4,0))
    face([a,b,b+ext,a+ext],glass[4],(0,0,1))
    for p in [a+ext,b+ext]:beam((p.x,p.y,1.3),p,.16,edge)
    beam(a+ext,b+ext,.20,edge);beam(a+ext-Vector((0,0,.1)),b+ext-Vector((0,0,.1)),.09,light)
for x in range(-82,91,12):
    box((x,-83,1.3),(x+.32,-82.68,2.25),steel);box((x,-83.03,1.95),(x+.32,-82.66,2.12),light)

# Material batching: a small number of draws even with thousands of individual panes.
for name,(vs,fs) in buf.items():
    if not vs:continue
    mesh=bpy.data.meshes.new(name+'_mesh');mesh.from_pydata(vs,[],fs);mesh.materials.append(mats[name]);mesh.update()
    bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
    obj=bpy.data.objects.new(name,mesh);col.objects.link(obj);obj.parent=root

rig=bpy.data.collections.new('STUDIO_not_exported');scene.collection.children.link(rig)
def rigobj(name,data,loc):
    ob=bpy.data.objects.new(name,data);rig.objects.link(ob);ob.location=loc;return ob
cam=rigobj('Camera_Hero',bpy.data.cameras.new('CCTV_Architecture_50mm'),(400,-510,300))
cam.rotation_euler=(Vector((0,0,108))-cam.location).to_track_quat('-Z','Y').to_euler()
cam.data.type='ORTHO';cam.data.ortho_scale=335;cam.data.clip_end=5000;scene.camera=cam
sun=rigobj('Sun_Preview',bpy.data.lights.new('Sun_Preview','SUN'),(300,-400,600));sun.rotation_euler=(Vector((0,0,90))-sun.location).to_track_quat('-Z','Y').to_euler();sun.data.energy=2.6;sun.data.angle=.12
world=bpy.data.worlds.new('CCTV_Studio');world.use_nodes=True;scene.world=world
bg=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs['Color'].default_value=(.39,.49,.6,1);bg.inputs['Strength'].default_value=.55
scene.render.engine='CYCLES';scene.cycles.samples=40;scene.cycles.use_denoising=True
scene.render.resolution_x=1400;scene.render.resolution_y=1600;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.film_transparent=True
for ob in bpy.context.selected_objects:ob.select_set(False)
for ob in col.objects:ob.select_set(True)
bpy.context.view_layer.objects.active=root
for area in bpy.context.screen.areas:
    if area.type=='VIEW_3D':
        sp=area.spaces.active;sp.region_3d.view_rotation=cam.rotation_euler.to_quaternion();sp.region_3d.view_distance=450;sp.region_3d.view_location=(0,0,110);sp.clip_end=5000;sp.shading.color_type='MATERIAL'
bpy.ops.export_scene.gltf(filepath=OUT+'\\cctv-headquarters.glb',export_format='GLB',use_selection=True,export_extras=True,export_animations=False,export_cameras=False,export_lights=False,export_yup=True)
bpy.ops.wm.save_as_mainfile(filepath=OUT+'\\cctv-headquarters.blend')
print({'export_objects':len(col.objects),'vertices':sum(len(o.data.vertices) for o in col.objects if o.type=='MESH'),'faces':sum(len(o.data.polygons) for o in col.objects if o.type=='MESH')})
