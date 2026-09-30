"""Tianfu Airport: built-condition photographic architectural reconstruction.
All geometry authored here. Meter scale, earth-level origin, standard PBR.
References: supplied aerials 0/3/4/5/8/9/10 and CSWADI project documentation.
Dimensions, parking positions and equipment are visual approximations.
"""
import bpy, math, random, json, bmesh
from pathlib import Path
from mathutils import Vector, Quaternion
from mathutils.geometry import tessellate_polygon
OUT=Path(r'C:\Users\JackieTang\Desktop\sample-data\chengdu-tianfu-airport')
OUT.mkdir(exist_ok=True)
# Rebuild only this authored study; preserve the user's unrelated scenes.
oldscenes=[s for s in bpy.data.scenes if s.name.startswith('TFU_Architectural_Portfolio')]
if bpy.context.window.scene in oldscenes:
    fallback=next((s for s in bpy.data.scenes if s not in oldscenes),None)
    bpy.context.window.scene=fallback or bpy.data.scenes.new('Workspace')
oldmaterials=set()
for sc in oldscenes:
    for ob in list(sc.objects):
        data=ob.data
        if ob.type=='MESH':oldmaterials.update(m for m in data.materials if m)
        bpy.data.objects.remove(ob,do_unlink=True)
        if data and data.users==0:
            for db in [bpy.data.meshes,bpy.data.lights,bpy.data.cameras]:
                if data.name in db and db.get(data.name)==data:db.remove(data);break
    bpy.data.scenes.remove(sc)
for m in oldmaterials:
    if m.users==0:bpy.data.materials.remove(m)
for c in list(bpy.data.collections):
    if c.name.startswith(('TFU_EXPORT','PRESENTATION_ONLY')) and c.users==0:bpy.data.collections.remove(c)
scene=bpy.data.scenes.new('TFU_Architectural_Portfolio')
bpy.context.window.scene=scene
scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
col=bpy.data.collections.new('TFU_EXPORT');scene.collection.children.link(col)
root=bpy.data.objects.new('Chengdu_Tianfu_International_Airport',None);col.objects.link(root)
root['description']='Built-condition photo-based architectural study, not survey or construction geometry'
root['reference_date']='2026-09-30';root['units']='meters';root['gate_count']=83
root['night_channel']='PBR Emissive; Cyber-Sight solar altitude drives day/night'
root['wgs84_longitude']=104.441;root['wgs84_latitude']=30.313
mats={};buf={};smooth_mats=set()
def mat(name,c,metal=0,rough=.5,em=None,power=1,smooth=False):
    m=bpy.data.materials.new(name);m.use_nodes=True
    n=next(n for n in m.node_tree.nodes if n.bl_idname=='ShaderNodeBsdfPrincipled')
    n.inputs['Base Color'].default_value=(*c,1);n.inputs['Metallic'].default_value=metal;n.inputs['Roughness'].default_value=rough
    if em:n.inputs['Emission Color'].default_value=(*em,1);n.inputs['Emission Strength'].default_value=power
    m.diffuse_color=(*c,1);mats[name]=m;buf[name]=[[],[]]
    if smooth:smooth_mats.add(name)
    return name
roof=mat('01_Standing_seam_silver_roof',(.58,.64,.66),.58,.34,smooth=True)
leaf=mat('02_Raised_feather_titanium',(.72,.76,.76),.58,.28,smooth=True)
rim=mat('03_Aluminium_edge_fascia',(.77,.80,.78),.65,.27)
seam=mat('04_Roof_panel_seams',(.30,.37,.40),.6,.44)
steel=mat('05_Structural_steel',(.57,.65,.65),.7,.34)
shadow=mat('06_Deep_recesses',(.028,.054,.062),.25,.6)
glasses=[mat('07_Curtainwall_glass_%d'%i,(.052+i*.012,.13+i*.015,.155+i*.02),.48,.18+i*.018) for i in range(4)]
warm=mat('08_Night_terminal_lobby',(.12,.19,.20),.42,.26,(1,.67,.32),1.7)
cool=mat('09_Night_gate_glass',(.10,.21,.25),.4,.22,(.46,.77,1),.55)
strip=mat('10_Night_roof_edge',(.68,.74,.75),.3,.36,(.50,.76,1),2.5)
gold=mat('11_Night_hotel_windows',(.21,.21,.17),.28,.3,(1,.64,.28),1.4)
light=mat('12_Night_landscape_lights',(.63,.60,.42),.15,.4,(1,.72,.39),3.2)
greenlight=mat('13_Taxiway_green_luminaires',(.08,.29,.17),0,.4,(.05,1,.26),3)
concrete=mat('14_Apron_concrete',(.48,.48,.44),0,.91)
paving=mat('15_Central_plaza_stone',(.39,.40,.35),0,.84)
joint=mat('16_Concrete_expansion_joints',(.34,.35,.32),0,.9)
asphalt=mat('17_Road_asphalt',(.09,.12,.13),0,.91)
white=mat('18_Road_and_stand_white',(.82,.83,.77),0,.75)
yellow=mat('19_Airside_yellow',(.72,.50,.035),0,.73)
red=mat('20_Stand_safety_red',(.38,.042,.032),0,.85)
stone=mat('21_Hotel_sandstone',(.55,.48,.32),.12,.72)
grass=mat('22_Terraced_roof_gardens',(.105,.19,.047),0,.95)
trees=[mat('23_Tree_canopy_%d'%i,(.07+i*.018,.14+i*.027,.043+i*.009),0,.95,smooth=True) for i in range(3)]
trunk=mat('24_Tree_trunks',(.15,.10,.055),0,.95)
water=mat('25_Landscape_reflecting_water',(.035,.13,.13),.35,.17,smooth=True)
plane=mat('26_Aircraft_ceramic_white',(.78,.81,.8),.15,.28,smooth=True)
engine=mat('27_Aircraft_engine_dark',(.10,.13,.14),.65,.33,smooth=True)
liveries=[mat('28_Aircraft_livery_%d'%i,c,.2,.35) for i,c in enumerate([(.45,.018,.015),(.035,.14,.31),(.085,.28,.37)])]
rubber=mat('29_Vehicle_tyres',(.028,.034,.034),0,.88)
carpaint=mat('30_Vehicle_paint',(.28,.35,.40),.45,.3)

def face(ps,m):
    vs,fs=buf[m];n=len(vs);vs.extend(tuple(p) for p in ps);fs.append(tuple(range(n,n+len(ps))))
def beam(a,b,w,m,depth=None):
    a,b=Vector(a),Vector(b);d=b-a
    if d.length<1e-5:return
    d.normalize();n=Vector((0,0,1)) if abs(d.z)<.95 else Vector((0,1,0))
    u=d.cross(n).normalized()*w/2;v=d.cross(u).normalized()*(depth or w)/2
    p=[a-u-v,a+u-v,a+u+v,a-u+v,b-u-v,b+u-v,b+u+v,b-u+v]
    for ids in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]:face([p[i] for i in ids],m)
def box(a,b,m):
    x,y,z=a;X,Y,Z=b;p=[(x,y,z),(X,y,z),(X,Y,z),(x,Y,z),(x,y,Z),(X,y,Z),(X,Y,Z),(x,Y,Z)]
    for ids in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]:face([p[i] for i in ids],m)
def poly(ps,m,z=0):
    vs=[Vector((p[0],p[1],z)) for p in ps]
    for tri in tessellate_polygon([vs]):face([vs[i] for i in tri] if isinstance(tri[0],int) else tri,m)
def line(ps,w,m,depth=None):
    for a,b in zip(ps,ps[1:]):beam(a,b,w,m,depth)
def cyl(a,b,r,m,n=10,r2=None):
    a,b=Vector(a),Vector(b);d=(b-a).normalized();u=d.cross(Vector((0,0,1)))
    if u.length<.1:u=d.cross(Vector((0,1,0)))
    u.normalize();v=d.cross(u);r2=r if r2 is None else r2
    pa=[a+(u*math.cos(i*math.tau/n)+v*math.sin(i*math.tau/n))*r for i in range(n)]
    pb=[b+(u*math.cos(i*math.tau/n)+v*math.sin(i*math.tau/n))*r2 for i in range(n)]
    face(pa[::-1],m);face(pb,m)
    for i in range(n):j=(i+1)%n;face([pa[i],pa[j],pb[j],pb[i]],m)
def ellipsoid(c,r,m,n=10,k=6,upper=False):
    for j in range(k):
        v0=(0 if upper else -math.pi/2)+j*(math.pi/2 if upper else math.pi)/k;v1=v0+(math.pi/2 if upper else math.pi)/k
        for i in range(n):
            u0=i*math.tau/n;u1=u0+math.tau/n
            face([(c[0]+r[0]*math.cos(v)*math.cos(u),c[1]+r[1]*math.cos(v)*math.sin(u),c[2]+r[2]*math.sin(v)) for u,v in [(u0,v0),(u1,v0),(u1,v1),(u0,v1)]],m)
def bez(p0,p1,p2,p3,t):return Vector(p0)*(1-t)**3+Vector(p1)*3*t*(1-t)**2+Vector(p2)*3*t*t*(1-t)+Vector(p3)*t**3
def bezpath(p0,p1,p2,p3,n=48):return [bez(p0,p1,p2,p3,i/n) for i in range(n+1)]
def capsule(cx,cy,w,l,z,m,n=24):
    r=w/2;h=(l-w)/2;ps=[]
    for i in range(n+1):t=i*math.pi/n;ps.append((cx+r*math.cos(t),cy+h+r*math.sin(t)))
    for i in range(n+1):t=math.pi+i*math.pi/n;ps.append((cx+r*math.cos(t),cy-h+r*math.sin(t)))
    poly(ps,m,z);return ps
def arc(cx,cy,r,z,start=0,end=math.tau,n=120):return [Vector((cx+r*math.cos(start+(end-start)*i/n),cy+r*math.sin(start+(end-start)*i/n),z)) for i in range(n+1)]
def annulus(cx,cy,ri,ro,z,m,start=0,end=math.tau,n=128):
    a=arc(cx,cy,ri,z,start,end,n);b=arc(cx,cy,ro,z,start,end,n)
    for i in range(n):face([a[i],b[i],b[i+1],a[i+1]],m)
def tree(x,y,z=1,s=1,seed=0):
    rng=random.Random(seed);h=rng.uniform(5,9)*s
    cyl((x,y,z),(x,y,z+h*.65),.3*s,trunk,6)
    ellipsoid((x,y,z+h*.7),(h*.36,h*.32,h*.44),trees[seed%3],8,5)
def roadpath(ps,w,z=1.2,elevated=False):
    p=[Vector((v[0],v[1],z)) for v in ps]
    line(p,w,asphalt,.6)
    for j,(a,b) in enumerate(zip(p,p[1:])):
        d=(b-a).normalized();n=Vector((-d.y,d.x,0));length=(b-a).length
        for off in [-w/2+.6,w/2-.6]:beam(a+n*off+Vector((0,0,.4)),b+n*off+Vector((0,0,.4)),.22,white,.05)
        if j%2==0:
            for off in [-w/6,w/6]:beam(a+n*off+Vector((0,0,.4)),a.lerp(b,.48)+n*off+Vector((0,0,.4)),.16,white,.04)
        if elevated:
            for off in [-w/2,w/2]:beam(a+n*off+Vector((0,0,.1)),b+n*off+Vector((0,0,.1)),.7,steel,1.4)
            if j%4==0:cyl((a.x,a.y,1),(a.x,a.y,z-.3),1.2,paving,8)

# Apron board, surface joins, taxiways and green islands.
box((-1050,-870,0),(1050,870,.65),concrete)
for x in range(-1030,1050,35):beam((x,-865,.68),(x,865,.68),.09,joint,.04)
for y in range(-850,870,35):beam((-1045,y,.68),(1045,y,.68),.09,joint,.04)
for x in [-975,975]:
    roadpath([(x,-850),(x,850)],48,.73)
    line([(x,-850,1.12),(x,850,1.12)],.3,yellow,.04)
    for y in range(-800,801,30):cyl((x,y,.9),(x,y,1.25),.25,greenlight,6)
for y in [-790,790]:
    line([(-920,y,.73),(920,y,.73)],38,asphalt,.15)
    line([(-920,y,.86),(920,y,.86)],.35,yellow,.04)
for s in [-1,1]:
    for y in [-590,-330,300,590]:
        capsule(s*900,y,30,150,.85,grass)
        ps=capsule(s*900,y,32,152,.87,paving);line([(x,y,1) for x,y in ps]+[(ps[0][0],ps[0][1],1)],.6,white,.06)
        capsule(s*900,y,28,146,.91,grass)

# A single continuous Y-outline per terminal. Roof height field forms the shell.
gate_number=0;gate_records=[]
def terminal(s):
    global gate_number
    xf=lambda p:Vector((s*(-p[0]),p[1],p[2] if len(p)>2 else 0))
    # s=-1 gives west terminal, s=+1 east terminal.
    curves=[
      [(-285,-620),(-165,-230),(-165,260),(-285,620)],
      [(-285,620),(-320,638),(-360,638),(-405,625)],
      [(-405,625),(-285,205),(-595,90),(-865,105)],
      [(-865,105),(-878,85),(-878,45),(-865,25)],
      [(-865,25),(-570,65),(-285,-230),(-405,-635)],
      [(-405,-635),(-355,-650),(-315,-645),(-285,-620)]
    ]
    paths=[bezpath(*c,80 if i in [0,2,4] else 12) for i,c in enumerate(curves)]
    outline=[p for ps in paths for p in ps[:-1]]
    def rh(x,y):return 22.5+7.8*math.exp(-((x+305)/180)**2-(y/390)**2)
    def tp(p,off=0):return xf((p.x,p.y,rh(p.x,p.y)+off))
    # Adaptive subdivision gives curved normals and no planar fan artefacts.
    def rooftri(a,b,c,level=0):
        lens=[(b-a).length,(c-b).length,(a-c).length];i=lens.index(max(lens))
        if max(lens)>28 and level<12:
            if i==0:q=(a+b)/2;rooftri(a,q,c,level+1);rooftri(q,b,c,level+1)
            elif i==1:q=(b+c)/2;rooftri(a,b,q,level+1);rooftri(a,q,c,level+1)
            else:q=(c+a)/2;rooftri(a,b,q,level+1);rooftri(q,b,c,level+1)
        else:
            ps=[tp(a),tp(b),tp(c)]
            if s==1:ps.reverse()
            face(ps,roof)
    for tri in tessellate_polygon([outline]):rooftri(*([outline[i] for i in tri] if isinstance(tri[0],int) else tri))
    poly([xf(p) for p in outline],shadow,1)
    # Glazed perimeter recessed behind the projecting metal fascia.
    for seg,(a,b) in enumerate(zip(outline,outline[1:]+outline[:1])):
        d=b-a;L=d.length;n=Vector((d.y,-d.x)).normalized();inset=-n*2.8
        za,zb=rh(*a),rh(*b)
        face([tp(a),tp(b),tp(b,-.65),tp(a,-.65)],rim)
        beam(tp(a,.12),tp(b,.12),.18,rim,.12)
        # Continuous eave light is a deliberately modest night channel.
        beam(tp(a,-.45),tp(b,-.45),.16,strip,.14)
        q0,q1=a+inset,b+inset
        count=max(1,math.ceil(L/4))
        for i in range(count):
            u0=i/count;u1=(i+1)/count
            p0,p1=q0.lerp(q1,u0),q0.lerp(q1,u1)
            z0,z1=za+(zb-za)*u0-1.7,za+(zb-za)*u1-1.7
            for floor in range(3):
                f0=1.3+(z0-1.3)*floor/3;f1=1.3+(z0-1.3)*(floor+1)/3-.22
                g0=1.3+(z1-1.3)*floor/3;g1=1.3+(z1-1.3)*(floor+1)/3-.22
                m=glasses[(seg+i+floor)%4]
                if floor==0:m=warm if (seg+i)%5 else glasses[1]
                elif (seg+i)%7==0:m=cool
                ps=[xf((*p0,f0)),xf((*p1,g0)),xf((*p1,g1)),xf((*p0,f1))]
                face(ps,m)
                beam(xf((*p0,f1+.12)),xf((*p1,g1+.12)),.22,steel,.14)
            beam(xf((*p0,1)),xf((*p0,z0)),.22,steel,.18)
        if seg%4==0:
            p=(a+b)/2+n*1.2
            beam(xf((*p,1)),xf((*p,za-.8)),.75,rim,.6)
            p2=p+n*5
            beam(xf((*p2,1)),xf((*p,za-.8)),.45,steel,.4)
    # Fine standing seam lines follow the actual roof section height.
    for y in range(-615,621,6):
        crossings=[]
        for a,b in zip(outline,outline[1:]+outline[:1]):
            if (a.y<=y<b.y) or (b.y<=y<a.y):crossings.append(a.x+(b.x-a.x)*(y-a.y)/(b.y-a.y))
        crossings.sort()
        for left,right in zip(crossings[::2],crossings[1::2]):
            ps=[xf((left+(right-left)*i/22,y,rh(left+(right-left)*i/22,y)+.06)) for i in range(23)]
            line(ps,.065,seam,.05)
    # The raised, elongated silver feather and its glazed ventilation clerestory.
    def lp(t,u):
        y=-355+735*t;x=-305+11*math.sin(t*math.pi)
        w=63*max(0,math.sin(math.pi*t))**.7
        xx=x+w*u;zz=rh(xx,y)+2.3+5.3*math.sin(math.pi*t)*math.sqrt(max(0,1-u*u))
        return xf((xx,y,zz))
    for j in range(90):
        for i in range(22):
            ps=[lp(j/90,-1+2*i/22),lp(j/90,-1+2*(i+1)/22),lp((j+1)/90,-1+2*(i+1)/22),lp((j+1)/90,-1+2*i/22)]
            if s==1:ps.reverse()
            face(ps,leaf)
        for u in [-1,1]:
            a,b=lp(j/90,u),lp((j+1)/90,u)
            face([a,b,b-Vector((0,0,2.3)),a-Vector((0,0,2.3))],cool)
            beam(a,b,.28,rim,.16)
            if j%2==0:beam(a,a-Vector((0,0,2.3)),.14,steel)
    for j in range(1,90):
        line([lp(j/90,-1+2*i/20)+Vector((0,0,.04)) for i in range(21)],.065,seam,.05)
    # Dark triangular courtyard skylights at the lateral finger junction.
    for coords in [[(-450,90),(-550,77),(-465,180)],[(-450,-95),(-560,30),(-460,-20)]]:
        ps=[Vector(p) for p in coords]
        face([tp(p,.22) for p in ps],glasses[1])
        line([tp(p,.25) for p in ps+[ps[0]]],1.2,rim,.35)
        for i in range(1,18):
            a=ps[0].lerp(ps[1],i/18);b=ps[0].lerp(ps[2],i/18);beam(tp(a,.28),tp(b,.28),.25,steel,.2)
    # Mechanical roof ventilators, kept small and organized.
    for y in [-400,-220,100,320]:
        for x in [-405,-417,-429]:
            p=xf((x,y,rh(x,y)+.7));cyl(p,p+Vector((0,0,.8)),1.6,rim,10)
    # 42 + 41 contact gates: curved outer piers plus both sides of terminal tips.
    samples=[]
    for ci in [2,4]:
        c=curves[ci]
        for j in range(13):samples.append((c,.045+.91*j/12,False))
    c=curves[0]
    for j in range(8):samples.append((c,.02+.205*j/7,False))
    for j in range(8 if s==-1 else 7):samples.append((c,.785+.19*j/7,False))
    for idx,(c,t,_) in enumerate(samples):
        p=bez(*c,t);d=(bez(*c,min(1,t+.001))-bez(*c,max(0,t-.001))).normalized();n=Vector((d.y,-d.x)).normalized()
        gate_number+=1
        # Dogleg bridge: slender opaque glazing and roof, with wheel bogie.
        a=xf((*p,7.7));b=xf((*(p+n*15),7.7));q=p+n*31+d*5;cpos=xf((*q,6.8))
        beam(a,b,3.8,glasses[2],3.0);beam(b,cpos,3.8,glasses[2],3.0)
        beam(a+Vector((0,0,1.55)),b+Vector((0,0,1.55)),4.0,rim,.2)
        beam(b+Vector((0,0,1.55)),cpos+Vector((0,0,1.55)),4.0,rim,.2)
        for k in range(1,7):
            h=b.lerp(cpos,k/7);beam(h-Vector((0,0,1.4)),h+Vector((0,0,1.4)),.15,steel)
        cyl((cpos.x,cpos.y,1),(cpos.x,cpos.y,5.7),.55,steel,8)
        for dx in [-1.1,1.1]:cyl((cpos.x+dx-.35,cpos.y,1.25),(cpos.x+dx+.35,cpos.y,1.25),.65,rubber,8)
        # Gate house and a roof sign plate.
        h=xf((*(p+n*6),9));box((h.x-2,h.y-2,1),(h.x+2,h.y+2,10),rim)
        # Stand lead-in and containment box in a local coordinate frame.
        def gp(u,v,z=1):return xf((*(p+n*u+d*v),z))
        line([gp(35,0),gp(95,0)],.24,yellow,.035)
        for u in [47,52,57]:line([gp(u,-2),gp(u,2)],.22,yellow,.035)
        line([gp(29,-27),gp(97,-27),gp(97,27),gp(29,27)],.18,white,.035)
        line([gp(23,-22),gp(31,-22),gp(31,22),gp(23,22)],.20,red,.035)
        for j in range(5):line([gp(24+j*1.5,-21),gp(24+j*1.5,21)],.11,red,.025)
        gate_records.append({'gate':gate_number,'terminal':'T1' if s==-1 else 'T2','position':[round(v,2) for v in a]})
        if idx<26 and (idx%4==1 or idx in [4,19]):aircraft(gp(56,0),xf((*n,0)),gate_number,1.15 if idx%3==0 else .92)
        if idx%3==0:
            h=gp(40,18);vehicle(h.x,h.y,h.z,idx,service=True)

def aircraft(pos,direction,seed,size=1):
    # Nose points toward the terminal. Body is a watertight ring loft.
    f=-Vector(direction);f.z=0;f.normalize();side=Vector((-f.y,f.x,0));base=Vector(pos)+Vector((0,0,3))
    def p(x,y,z):return base+side*x*size+f*y*size+Vector((0,0,z*size))
    sections=[(-24,.08),(-22,.65),(-17,1.7),(-11,2.1),(12,2.1),(18,1.6),(21,.7),(22,0.06)]
    rings=[[p(r*math.cos(i*math.tau/16),y,3+r*math.sin(i*math.tau/16)) for i in range(16)] for y,r in sections]
    for j in range(len(rings)-1):
        for i in range(16):k=(i+1)%16;face([rings[j][i],rings[j][k],rings[j+1][k],rings[j+1][i]],plane)
    face(rings[0][::-1],plane);face(rings[-1],plane)
    for s in [-1,1]:
        # Swept wings, stabilizers, upright winglets, two engines.
        wing=[p(s*1,6,2),p(s*20,-7,1.6),p(s*20,-10,1.5),p(s*4,-5,2)]
        face(wing,plane);face([q-Vector((0,0,.35)) for q in wing[::-1]],plane)
        face([p(s*20,-7,1.6),p(s*20,-10,1.5),p(s*20.7,-10,3.6),p(s*20.7,-8,3.6)],liveries[seed%3])
        face([p(s*.8,-17,4),p(s*8,-23,3),p(s*8,-25,3),p(s*1,-21,4)],plane)
        cyl(p(s*7,-1,1),p(s*7,5,1),1.6,plane,12)
        cyl(p(s*7,5.02,1),p(s*7,5.1,1),1.2,engine,12)
        for y in range(-11,15,2):
            a=p(s*2.06,y,3.5);b=p(s*2.06,y+.75,3.5);beam(a,b,.42,glasses[0],.5)
        cyl(p(s*2,-5,0),p(s*2,-5,2),.15,steel,6)
        cyl(p(s*2-.3,-5,0),p(s*2+.3,-5,0),.65,rubber,8)
    face([p(0,-23,3),p(0,-23,11),p(0,-18,11),p(0,-15,4)],liveries[seed%3])
    # Windshield and gear.
    face([p(-1.2,17,4),p(1.2,17,4),p(1,19,3.9),p(-1,19,3.9)],glasses[0])
    cyl(p(0,14,0),p(0,14,2),.16,steel,6)
    cyl(p(-.4,14,0),p(.4,14,0),.5,rubber,8)

def vehicle(x,y,z,seed,service=False):
    l=6.5 if service else 4.7;w=2.2 if service else 1.9
    box((x-w/2,y-l/2,z+.25),(x+w/2,y+l/2,z+1.3),white if seed%3==0 else carpaint)
    box((x-w*.42,y-l*.27,z+1.25),(x+w*.42,y+l*.22,z+2.0),glasses[1])
    box((x-w*.43,y-l*.24,z+1.98),(x+w*.43,y+l*.20,z+2.10),white if seed%3==0 else carpaint)
    for a in [-1,1]:
        for b in [-1,1]:cyl((x+a*w/2-.12,y+b*l*.32,z+.55),(x+a*w/2+.12,y+b*l*.32,z+.55),.48,rubber,8)

terminal(-1);terminal(1)

# Hotel / commercial C-ring with real open courtyard, horizontal floors and fins.
cx,cy=0,-330;ri,ro=90,132;start=math.radians(117);end=math.radians(423);N=144
annulus(cx,cy,ri,ro,1.0,paving,start,end,N)
annulus(cx,cy,ri-4,ro+3,34.5,stone,start,end,N)
annulus(cx,cy,ri-4,ro+3,33.8,rim,start,end,N)
for r in [ri,ro]:
    ps=arc(cx,cy,r,0,start,end,N)
    for j in range(N):
        a,b=ps[j],ps[j+1]
        face([a+Vector((0,0,2)),b+Vector((0,0,2)),b+Vector((0,0,33)),a+Vector((0,0,33))],shadow)
        for k in range(7):
            lo=3+k*4.2;hi=lo+3.4
            face([a+Vector((0,0,lo)),b+Vector((0,0,lo)),b+Vector((0,0,hi)),a+Vector((0,0,hi))],gold if (j+k)%6 else glasses[0])
            beam(a+Vector((0,0,hi+.3)),b+Vector((0,0,hi+.3)),.6,stone,.32)
        if j%2==0:beam(a+Vector((0,0,2)),a+Vector((0,0,33.8)),.4,stone,.4)
        if j%12==0:beam(a+Vector((0,0,2)),a+Vector((0,0,34.4)),2.2,stone,1.3)
    line(arc(cx,cy,r,34.55,start,end,N),.22,light,.12)
# Roof solar bands and metal parapet.
for a in [150,200,250,300,350,400]:
    annulus(cx,cy,107,117,34.55,glasses[0],math.radians(a),math.radians(a+18),16)
    for ang in range(a,a+18,2):line(arc(cx,cy,112,34.7,math.radians(ang),math.radians(ang+.1),2),10,steel,.06)
box((-38,-363,1),(38,-295,15),stone)
box((-32,-355,15),(32,-303,17),roof)
poly([(-35,-355),(35,-355),(35,-303),(-35,-303)],glasses[2],17.1)
for y in [-350,-330,-310]:line([(-32,y,17.2),(32,y,17.2)],.35,steel,.25)
for x in [-60,60]:
    for y in [-375,-320,-270]:tree(x,y,1,1.1,int(x+y))
# Sunbird medallion on roof: stylized authored mark, no image texture.
annulus(0,-458,0,8,34.7,shadow,n=48)
annulus(0,-458,3.8,4.5,34.74,stone,n=48)
for k in range(4):
    a=k*math.pi/2;line(arc(0,-458,6.1,34.76,a,a+1.12,16),.85,stone,.06)

# Elevated drop-off system running between both terminals and around the ring.
for s in [-1,1]:
    ps=bezpath((s*225,-630),(s*150,-230),(s*150,280),(s*225,650),100)
    roadpath(ps,24,12.8,True)
    ps2=bezpath((s*250,-630),(s*175,-230),(s*175,280),(s*250,650),100)
    roadpath(ps2,18,1.3)
    for j in range(0,100,6):
        p=ps[j];vehicle(p.x+3*s,p.y,13.45,j+s)
    for j in range(0,100,3):
        p=ps[j];beam((p.x+s*13,p.y,13),(p.x+s*13,p.y,17),.17,steel)
        beam((p.x+s*13,p.y,17),(p.x+s*10,p.y,17),.15,steel)
        beam((p.x+s*10,p.y,16.95),(p.x+s*12,p.y,16.95),.35,light,.12)
roadpath(arc(0,-330,169,0,math.pi,math.tau,72),22,12.8,True)
roadpath([(-225,-635),(-140,-575),(0,-565),(140,-575),(225,-635)],20,12.8,True)

# Airside interterminal connecting bridge along the southern apron edge.
box((-295,-584,7),(295,-570,12),glasses[1])
box((-295,-585,12),(295,-569,12.9),roof)
for x in range(-280,281,18):
    beam((x,-575,1),(x,-575,7),.75,steel)
    beam((x,-583,7),(x,-583,12),.25,rim)
    beam((x,-570,7),(x,-570,12),.25,rim)
line([(-295,-584,12.5),(295,-584,12.5)],.2,strip,.16)

# GTC: planted terraces with rectangular courts, capsule rooflights and paths.
box((-152,-150,.8),(152,345,8),paving)
box((-145,-143,8),(145,340,9),grass)
for s in [-1,1]:
    for y in [-55,80,215]:
        x=s*100
        box((x-35,y-52,8.9),(x+35,y+52,10),stone)
        box((x-33,y-50,10),(x+33,y+50,10.25),grass)
        for d in [-1,1]:line([(x+d*34,y-51,10.3),(x+d*34,y+51,10.3)],.45,light,.12)
        capsule(x,y,13,62,12,leaf)
        for j in range(7):tree(x+s*22,y-40+j*13,10.2,.48,j+int(y))
    line([(s*49,-140,9.2),(s*49,335,9.2)],9,stone,.2)
    for y in range(-110,341,28):
        box((s*34-1,y-2,9),(s*34+1,y+2,10.1),light)
capsule(0,97,66,216,9.3,stone)
capsule(0,97,59,209,10.7,glasses[2])
capsule(0,97,51,202,11.4,leaf)
for y in range(20,181,8):beam((-24,y,11.55),(24,y,11.55),.07,seam,.05)
for y in [-120,315]:line([(-145,y,9.2),(145,y,9.2)],9,stone,.25)

# North garden: sculpted planted landforms, concentric terrace edges and ponds.
poly([(-165,350),(165,350),(215,690),(0,735),(-215,690)],grass,1.1)
for sx,sy,rx,ry in [(-105,510,75,120),(105,552,75,125)]:
    ellipsoid((sx,sy,1.0),(rx,ry,9.5),grass,48,10,upper=True)
    for k in range(6):
        r=1-k*.10
        ps=[(sx+rx*r*math.cos(t),sy+ry*r*math.sin(t),1.2+9.5*math.sqrt(max(0,1-r*r))) for t in [i*math.tau/100 for i in range(101)]]
        line(ps,.75,stone,.20)
    for j in range(65):
        rng=random.Random(j*813+int(sx));a=rng.random()*math.tau;r=math.sqrt(rng.random())*.93
        x=sx+rx*r*math.cos(a);y=sy+ry*r*math.sin(a);z=1+9.5*math.sqrt(1-r*r)
        if j%3:tree(x,y,z,.7,j+int(sx))
pond=bezpath((-16,418),(-30,515),(30,556),(12,665),60)+bezpath((12,665),(-24,645),(8,530),(-16,418),60)
poly(pond,water,2.3);line([(v.x,v.y,2.32) for v in pond],1.6,stone,.25)
roadpath(bezpath((0,350),(-5,470),(65,520),(0,735),70),5,2.9)
for s in [-1,1]:
    for j in range(46):
        rng=random.Random(j*997+s);x=s*rng.uniform(120,196);y=rng.uniform(390,696)
        tree(x,y,1.1,rng.uniform(.7,1.1),j*13+s)
    for y in range(-115,690,18):tree(s*159,y,1.1,.67,y+s)
    roadpath([(s*250,665),(s*220,740),(s*85,800)],22,1.3)
for x in [-120,120]:
    box((x-40,716,1),(x+40,756,11),glasses[1]);box((x-42,715,11),(x+42,757,12),roof)
    for z in [4,7,10]:beam((x-40,716,z),(x+40,716,z),.5,rim,.25)

# Apron light towers and service vehicles; light meshes export, lamps do not.
for s in [-1,1]:
    for x,y in [(690,-495),(740,455),(575,705),(810,-225)]:
        x*=s;cyl((x,y,1),(x,y,29),.32,steel,8)
        beam((x-3,y,29),(x+3,y,29),.25,steel)
        for d in [-2.5,0,2.5]:box((x+d-.5,y-.6,28.6),(x+d+.5,y+.6,29.2),light)

# Mesh consolidation by material keeps GPU draw calls bounded.
stats=[]
for name,(vs,fs) in buf.items():
    if not fs:continue
    me=bpy.data.meshes.new(name+'_Geometry');me.from_pydata(vs,[],fs);me.materials.append(mats[name]);me.update()
    ob=bpy.data.objects.new(name,me);col.objects.link(ob);ob.parent=root
    # Roof surfaces and aircraft have smooth normals; architectural edges stay crisp.
    if name in smooth_mats:
        bm=bmesh.new();bm.from_mesh(me);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.0001);bm.to_mesh(me);bm.free();me.update()
        for p in me.polygons:p.use_smooth=True
    stats.append({'name':name,'vertices':len(vs),'faces':len(fs)})
root['authored_mesh_count']=len(stats)
OUT.joinpath('geometry-report.json').write_text(json.dumps({'gates':gate_records,'meshes':stats},indent=2),encoding='utf-8')

# Presentation stage is excluded from GLB.
stage=bpy.data.collections.new('PRESENTATION_ONLY');scene.collection.children.link(stage)
world=bpy.data.worlds.new('TFU_Sky');world.use_nodes=True
bg=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND')
bg.inputs['Color'].default_value=(.42,.53,.68,1);bg.inputs['Strength'].default_value=.65;scene.world=world
ld=bpy.data.lights.new('Portfolio_Sun','SUN');ld.energy=2.6;ld.angle=.15
sun=bpy.data.objects.new('Portfolio_Sun',ld);stage.objects.link(sun);sun.rotation_euler=(math.radians(29),math.radians(-28),math.radians(-34))
cd=bpy.data.cameras.new('Portfolio_Camera');cam=bpy.data.objects.new('Portfolio_Camera',cd);stage.objects.link(cam);scene.camera=cam
cam.location=(1400,-2350,2000);target=Vector((0,10,0));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cd.type='ORTHO';cd.ortho_scale=2580;cd.clip_end=20000
scene.render.engine='CYCLES';scene.cycles.samples=48;scene.cycles.use_denoising=True
scene.render.resolution_x=1800;scene.render.resolution_y=1350;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX';scene.render.image_settings.file_format='PNG'
scene.render.film_transparent=False
# Preserve emissive values in the exported asset. Day previews switch these off.
bpy.ops.object.select_all(action='DESELECT')
for ob in col.objects:ob.select_set(True)
bpy.context.view_layer.objects.active=root
bpy.ops.export_scene.gltf(filepath=str(OUT/'chengdu-tianfu-airport.glb'),export_format='GLB',use_selection=True,use_active_scene=True,export_extras=True,export_animations=False,export_cameras=False,export_lights=False,export_yup=True)
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            space=area.spaces.active;space.clip_end=20000;space.overlay.show_overlays=False
            space.shading.type='MATERIAL';space.region_3d.view_perspective='CAMERA'
            space.region_3d.view_camera_zoom=0
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'chengdu-tianfu-airport.blend'))
print(json.dumps({'status':'created','gates':gate_number,'meshes':len(stats),'vertices':sum(s['vertices'] for s in stats),'glb_bytes':(OUT/'chengdu-tianfu-airport.glb').stat().st_size}))
