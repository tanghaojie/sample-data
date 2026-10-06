"""Original, reproducible NCPA reconstruction for Blender 5.2 / Cyber-Sight.

Metres, X east, Y north, Z up. No downloaded geometry or imagery in the asset.
Published dimensions are fixed; curtain geometry and site details are reconstructed.
"""
import bpy, math, random, json
from pathlib import Path
from mathutils import Vector
from collections import defaultdict
from math import sin, cos, pi, sqrt

ROOT = Path(__file__).resolve().parent
random.seed(2007)
A, B, H = 106.1, 71.82, 46.285
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for c in list(bpy.data.collections):
    if c.users == 0: bpy.data.collections.remove(c)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1
scene.render.engine = 'CYCLES'
scene.cycles.samples = 32
scene.cycles.use_denoising = True
scene.render.resolution_x = 1600
scene.render.resolution_y = 1100
scene.render.resolution_percentage = 100
scene.view_settings.view_transform = 'AgX'
scene.render.image_settings.file_format = 'PNG'
scene.render.film_transparent = False
scene.render.threads_mode = 'FIXED'
scene.render.threads = 6
collections = {}
for name in ['01 Titanium envelope', '02 Glass curtain', '03 Curtain structure', '04 Inner venues', '05 Reflecting pool and arrival', '06 Landscape and furniture', '90 Presentation rig']:
    c=bpy.data.collections.new(name); scene.collection.children.link(c); collections[name[:2]]=c

def material(name, color, metal=0, rough=.45, alpha=1, emission=None, strength=1):
    m=bpy.data.materials.new(name); m.use_nodes=True
    bs=next(n for n in m.node_tree.nodes if n.bl_idname=='ShaderNodeBsdfPrincipled')
    bs.inputs['Base Color'].default_value=(*color,alpha)
    bs.inputs['Metallic'].default_value=metal
    bs.inputs['Roughness'].default_value=rough
    bs.inputs['Alpha'].default_value=alpha
    if emission:
        bs.inputs['Emission Color'].default_value=(*emission,1)
        bs.inputs['Emission Strength'].default_value=strength
    m.diffuse_color=(*color,alpha)
    m.use_backface_culling=True
    if alpha<1:
        m.surface_render_method='DITHERED'
        m.use_transparency_overlap=False
    return m

titanium=[material(f'Titanium | brushed silver {i+1}',(.43+i*.008,.445+i*.008,.47+i*.008),1,.34+i*.01) for i in range(5)]
seam=material('Recessed graphite joints',(.038,.044,.05),.5,.5)
glass=[material(f'Ultra clear curtain | subtle sky tint {i+1}',(.21+i*.014,.31+i*.015,.36+i*.018),0,.14+i*.018,.24+i*.025) for i in range(3)]
steel=material('Curtain mullions | satin stainless steel',(.48,.52,.53),.75,.3)
truss=material('Structural ribs | warm white steel',(.69,.71,.69),.42,.33)
bronze=material('Opera house | bronze gold mesh',(.34,.19,.058),.68,.38)
bronzedark=material('Opera house | dark mesh recess',(.16,.083,.021),.6,.48)
stone=material('Arrival and paving | honed limestone',(.49,.47,.42),0,.74)
stone2=material('Paving | pale granite',(.64,.64,.6),.04,.7)
black=material('Basalt coping and handrails',(.045,.055,.063),.25,.4)
wood=material('Venue interior | warm timber',(.23,.085,.035),.1,.55)
grass=material('Landscape | lawn',(.087,.16,.055),0,.9)
soil=material('Tree bark',(.12,.075,.039),0,.93)
foliage=[material(f'Landscape | canopy tone {i+1}',(.048+i*.012,.112+i*.018,.038+i*.007),0,.91) for i in range(4)]
water=material('Reflecting pool | calm water',(.045,.105,.115),0,.07,.80)
warm=material('Night | interior warm linear light',(.56,.38,.17),.15,.32,emission=(1,.57,.21),strength=3.2)
goldlight=material('Night | opera mesh backlight',(.4,.215,.065),.55,.36,emission=(1,.45,.1),strength=.85)
cool=material('Night | titanium star points',(.58,.64,.66),.25,.22,emission=(.72,.85,1),strength=5)
pathlight=material('Night | arrival and landscape lamps',(.63,.55,.38),.1,.3,emission=(1,.64,.28),strength=3)

# Authored texture, packed into the blend and GLB; no third-party images.
import numpy as np
rng=np.random.default_rng(2007)
n=256
im=bpy.data.images.new('Original titanium micrograin roughness',width=n,height=n)
noise=rng.normal(0,.018,(n,n)) + rng.normal(0,.014,(n,1))
px=np.ones((n,n,4),dtype=np.float32); px[:,:,:3]=np.clip(.35+noise[:,:,None],.27,.45)
im.colorspace_settings.name='Non-Color'; im.pixels.foreach_set(px.ravel()); im.pack()
for m in titanium:
    nt=m.node_tree; bs=next(x for x in nt.nodes if x.bl_idname=='ShaderNodeBsdfPrincipled')
    tex=nt.nodes.new('ShaderNodeTexImage'); tex.image=im
    nt.links.new(tex.outputs['Color'],bs.inputs['Roughness'])

def texture_image(name,values,space):
    im=bpy.data.images.new(name,width=n,height=n)
    pixels=np.ones((n,n,4),dtype=np.float32)
    pixels[:,:,:3]=values if values.ndim==3 else values[:,:,None]
    im.colorspace_settings.name=space;im.pixels.foreach_set(pixels.ravel());im.pack()
    (ROOT/'textures').mkdir(exist_ok=True)
    im.filepath_raw=str(ROOT/'textures'/(name+'.png'));im.file_format='PNG';im.save()
    return im

def surface_maps(m,kind,tile_size=1):
    nt=m.node_tree;bs=next(x for x in nt.nodes if x.bl_idname=='ShaderNodeBsdfPrincipled')
    yy,xx=np.mgrid[0:n,0:n]/n
    if kind=='stone':height=rng.normal(0,.1,(n,n)); variation=rng.normal(0,.022,(n,n))
    elif kind=='wood':
        wave=np.sin(xx*2*pi*38+np.sin(yy*2*pi*2)*.7)
        height=wave*.025;variation=wave*.055+rng.normal(0,.018,(n,n))
    else:
        height=rng.normal(0,.07,(n,n));variation=rng.normal(0,.03,(n,n))
    color=np.array(bs.inputs['Base Color'].default_value[:3])
    base=np.clip(color[None,None,:]*(1+variation[:,:,None]*2),0,1)
    tex=nt.nodes.new('ShaderNodeTexImage');tex.image=texture_image(kind+'-'+m.name.replace(' | ','-').replace(' ','_')+'-basecolor',base,'sRGB')
    nt.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
    rough=np.clip(float(bs.inputs['Roughness'].default_value)+variation*.3,.05,1)
    tr=nt.nodes.new('ShaderNodeTexImage');tr.image=texture_image(kind+'-'+m.name.replace(' | ','-').replace(' ','_')+'-roughness',rough,'Non-Color');nt.links.new(tr.outputs['Color'],bs.inputs['Roughness'])
    dx=np.roll(height,-1,axis=1)-np.roll(height,1,axis=1);dy=np.roll(height,-1,axis=0)-np.roll(height,1,axis=0)
    nor=np.stack([-dx,-dy,np.ones_like(dx)],axis=2);nor/=np.linalg.norm(nor,axis=2,keepdims=True)
    nm=nt.nodes.new('ShaderNodeTexImage');nm.image=texture_image(kind+'-'+m.name.replace(' | ','-').replace(' ','_')+'-normal',nor*.5+.5,'Non-Color')
    node=nt.nodes.new('ShaderNodeNormalMap');node.inputs['Strength'].default_value=.3;nt.links.new(nm.outputs['Color'],node.inputs['Color']);nt.links.new(node.outputs['Normal'],bs.inputs['Normal'])
    m['tile_size_m']=tile_size

for mat in [stone,stone2,black]:surface_maps(mat,'stone',1)
for mat in [wood,soil]:surface_maps(mat,'wood',1)
surface_maps(grass,'grass',.75)
for m in glass:
    bs=next(x for x in m.node_tree.nodes if x.bl_idname=='ShaderNodeBsdfPrincipled');bs.inputs['Coat Weight'].default_value=.22;bs.inputs['Coat Roughness'].default_value=.10

class Batch:
    def __init__(self,name,mat,col,smooth=False):
        self.name,self.mat,self.col,self.smooth=name,mat,col,smooth
        self.v=[];self.f=[];self.uv=[]
    def face(self,verts,uv=None):
        ix=len(self.v);self.v.extend(tuple(v) for v in verts);self.f.append(tuple(range(ix,ix+len(verts))))
        if uv is None and 'tile_size_m' in self.mat:
            normal=(Vector(verts[1])-Vector(verts[0])).cross(Vector(verts[2])-Vector(verts[0]))
            axis=max(range(3),key=lambda i:abs(normal[i]));axes=[i for i in range(3) if i!=axis];tile=self.mat['tile_size_m']
            uv=[(v[axes[0]]/tile,v[axes[1]]/tile) for v in verts]
        self.uv.extend(uv or [(0,0),(1,0),(1,1),(0,1)][:len(verts)])
    def quad(self,a,b,c,d): self.face([a,b,c,d])
    def box(self,center,size):
        x,y,z=center;u,v,w=[s/2 for s in size]
        q=[(x-u,y-v,z-w),(x+u,y-v,z-w),(x+u,y+v,z-w),(x-u,y+v,z-w),(x-u,y-v,z+w),(x+u,y-v,z+w),(x+u,y+v,z+w),(x-u,y+v,z+w)]
        for f in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]: self.face([q[i] for i in f])
    def beam(self,p,q,r=.05,sides=6):
        p,q=Vector(p),Vector(q); d=q-p
        if d.length<.0001:return
        d.normalize();ref=Vector((0,0,1)) if abs(d.z)<.9 else Vector((1,0,0))
        u=d.cross(ref).normalized()*r;v=d.cross(u).normalized()*r
        a=[p+u*cos(i*2*pi/sides)+v*sin(i*2*pi/sides) for i in range(sides)]
        b=[q+u*cos(i*2*pi/sides)+v*sin(i*2*pi/sides) for i in range(sides)]
        for i in range(sides):self.quad(a[i],a[(i+1)%sides],b[(i+1)%sides],b[i])
        capuv=[(.5+.5*cos(i*2*pi/sides),.5+.5*sin(i*2*pi/sides)) for i in range(sides)]
        self.face(list(reversed(a)),list(reversed(capuv)));self.face(b,capuv)
    def polyline(self,pts,r=.05,sides=6):
        for p,q in zip(pts[:-1],pts[1:]):self.beam(p,q,r,sides)
    def sphere(self,center,scale,rings=6,sectors=10):
        x,y,z=center
        def point(t,p):return (x+scale[0]*sin(t)*cos(p),y+scale[1]*sin(t)*sin(p),z+scale[2]*cos(t))
        for j in range(rings):
            t0=j*pi/rings;t1=(j+1)*pi/rings
            for i in range(sectors):
                p0=i*2*pi/sectors;p1=(i+1)*2*pi/sectors
                if j==0:self.face([point(t0,p0),point(t1,p0),point(t1,p1)],[(0,0)]*3)
                elif j==rings-1:self.face([point(t0,p0),point(t1,p0),point(t0,p1)],[(0,0)]*3)
                else:self.quad(point(t0,p0),point(t1,p0),point(t1,p1),point(t0,p1))
    def finish(self):
        if not self.f:return None
        me=bpy.data.meshes.new(self.name);me.from_pydata(self.v,[],self.f);me.update()
        ob=bpy.data.objects.new(self.name,me);collections[self.col].objects.link(ob);me.materials.append(self.mat)
        for p in me.polygons:p.use_smooth=self.smooth
        uv=me.uv_layers.new(name='UVMap')
        uv.data.foreach_set('uv',[q for pair in self.uv for q in pair])
        # Stable triangulation provides tangent space for every textured primitive.
        import bmesh
        bm=bmesh.new();bm.from_mesh(me);bmesh.ops.triangulate(bm,faces=list(bm.faces),quad_method='FIXED',ngon_method='EAR_CLIP');bm.to_mesh(me);bm.free();me.update()
        ob['model_unit']='metre';ob['part']=collections[self.col].name
        return ob

batches={}
def batch(name,mat,col,smooth=False):
    if name not in batches:batches[name]=Batch(name,mat,col,smooth)
    return batches[name]

def shell(t,p,offset=0):
    x=A*cos(t)*cos(p);y=B*cos(t)*sin(p);z=H*sin(t)
    nor=Vector((x/A**2,y/B**2,z/H**2)).normalized()
    return Vector((x,y,z))+nor*offset

def curtain(t,north=True):
    mid=pi/2 if north else 3*pi/2
    # Curved silhouette fitted to exterior photographs; an estimate, not survey data.
    shift=.18*sin(2*t)+.04*sin(t)
    if not north:shift=-shift
    hw=.492+.22*sin(t)**1.3
    return mid+shift-hw,mid+shift+hw

panel_count=0
for j in range(72):
    t0=j*pi/144;t1=(j+1)*pi/144;tm=(t0+t1)/2
    cnt=max(10,round(172*cos(tm)**.45))
    for side in range(2):
        north_l,north_r=curtain(tm,True);south_l,south_r=curtain(tm,False)
        p0=north_r if side==0 else south_r
        p1=south_l if side==0 else north_l+2*pi
        for i in range(cnt):
            f0=i/cnt;f1=(i+1)/cnt
            def bounds(t):
                nl,nr=curtain(t,True);sl,sr=curtain(t,False)
                return (nr,sl) if side==0 else (sr,nl+2*pi)
            a0,a1=bounds(t0);b0,b1=bounds(t1)
            gap_t=.00035;gap_p=.00025/max(cos(tm),.1)
            corners=[shell(t0+gap_t,a0+(a1-a0)*f0+gap_p,.013),shell(t0+gap_t,a0+(a1-a0)*f1-gap_p,.013),shell(t1-gap_t,b0+(b1-b0)*f1-gap_p,.013),shell(t1-gap_t,b0+(b1-b0)*f0+gap_p,.013)]
            batch(f'Titanium panels tone {((i*7+j*13)%5)+1}',titanium[(i*7+j*13)%5],'01',True).face(corners)
            panel_count+=1
            # Fine square fastener tabs are visible only at close range.
            if j%2==0 and i%3==0 and j<66:
                p=(a0+(a1-a0)*(f0+f1)/2)
                q=shell(tm,p,.03);nor=Vector((q.x/A**2,q.y/B**2,q.z/H**2)).normalized()
                tangent=Vector((-sin(p),cos(p),0))*.035
                vertical=nor.cross(tangent).normalized()*.05
                batch('Titanium stainless fasteners',steel,'01').face([q-tangent-vertical,q+tangent-vertical,q+tangent+vertical,q-tangent+vertical])
            if j in [8,18,29,41,52,61] and i%11==3:
                q=shell(tm,(a0+(a1-a0)*(f0+f1)/2),.04)
                batch('Scattered star point glazing',cool,'01',True).sphere(q,(.12,.12,.12),4,6)
        # Dark backing fills the separated panel joints without covering glass.
        a0,a1=bounds(t0);b0,b1=bounds(t1)
        for i in range(100):
            f0=i/100;f1=(i+1)/100
            batch('Shell joint backing',seam,'01',True).face([shell(t0,a0+(a1-a0)*f0,-.045),shell(t0,a0+(a1-a0)*f1,-.045),shell(t1,b0+(b1-b0)*f1,-.045),shell(t1,b0+(b1-b0)*f0,-.045)])

pane_count=0
for north in [True,False]:
    side='North' if north else 'South'
    def cp(t,f,offset=0):
        a,b=curtain(t,north);return shell(t,a+(b-a)*f,offset)
    for j in range(46):
        t0=j*pi/92;t1=min((j+1)*pi/92,pi/2-.0005)
        for i in range(14):
            f0=i/14+.0005;f1=(i+1)/14-.0005
            bb=batch(f'{side} glass panes tint {i%3+1}',glass[i%3],'02',True)
            for y in range(2):
                for x in range(2):
                    ta=t0+(t1-t0)*y/2+.0001;tb=t0+(t1-t0)*(y+1)/2-.0001
                    fa=f0+(f1-f0)*x/2;fb=f0+(f1-f0)*(x+1)/2
                    bb.face([cp(ta,fa),cp(ta,fb),cp(tb,fb),cp(tb,fa)])
            pane_count+=1
    # Exterior cap, secondary mullions and paired deep interior truss chords.
    for i in range(15):
        f=i/14
        batch(side+' meridian mullions',steel,'03',True).polyline([cp(k*pi/184,f,.045) for k in range(93)],.048,6)
        batch(side+' structural outer ribs',truss,'03',True).polyline([cp(k*pi/92,f,-.55) for k in range(47)],.105,8)
        if i%2==0:
            batch(side+' structural inner ribs',truss,'03',True).polyline([cp(k*pi/92,f,-1.6) for k in range(47)],.13,8)
            for k in range(46):
                batch(side+' truss diagonals',truss,'03',True).beam(cp(k*pi/92,f,-.55),cp((k+1)*pi/92,f,-1.6),.045)
    for j in range(47):
        t=j*pi/92
        batch(side+' horizontal mullions',steel,'03',True).polyline([cp(t,k/56,.025) for k in range(57)],.052,6)
        if j%4==0:
            batch(side+' inner cross members',truss,'03',True).polyline([cp(t,k/28,-.65) for k in range(29)],.10,6)
    for f in [0,1]:
        batch(side+' curved curtain edge fascia',steel,'03',True).polyline([cp(k*pi/184,f,.045) for k in range(93)],.19,8)

# A narrow polished base rim, set at the waterline. No above-ground entrance.
for j in range(360):
    p0=j*2*pi/360;p1=(j+1)*2*pi/360
    batch('Continuous waterline plinth',black,'01').face([(A*cos(p0),B*sin(p0),.22),(A*cos(p1),B*sin(p1),.22),(A*cos(p1),B*sin(p1),.88),(A*cos(p0),B*sin(p0),.88)])
    batch('Polished waterline coping',steel,'01').face([(A*cos(p0),B*sin(p0),.88),(A*cos(p1),B*sin(p1),.88),((A+.48)*cos(p1),(B+.48)*sin(p1),.88),((A+.48)*cos(p0),(B+.48)*sin(p0),.88)])

def elliptic_wall(name,cx,cy,rx,ry,z0,z1,mat,col,segments=100):
    bb=batch(name,mat,col,True)
    for i in range(segments):
        a=i*2*pi/segments;b=(i+1)*2*pi/segments
        bb.face([(cx+rx*cos(a),cy+ry*sin(a),z0),(cx+rx*cos(b),cy+ry*sin(b),z0),(cx+rx*cos(b),cy+ry*sin(b),z1),(cx+rx*cos(a),cy+ry*sin(a),z1)])

# Visible pavilion envelopes based on published plan/sections. Interiors are partial.
elliptic_wall('Central opera gold envelope',0,-8,35,38,1,27,bronze,'04',144)
elliptic_wall('Opera illuminated gold band',0,-8,35.04,38.04,18,19.6,goldlight,'04',144)
elliptic_wall('Concert hall outer envelope',-62,0,22,37,1,22,wood,'04')
elliptic_wall('Theatre outer envelope',62,0,21,33,1,19,stone,'04')
for z in [4.8,9.6,14.4,19.2,24]:
    bb=batch('Opera ring galleries and caps',bronzedark,'04',True)
    for i in range(144):
        a=i*2*pi/144;b=(i+1)*2*pi/144
        bb.face([(35*cos(a),-8+38*sin(a),z),(35*cos(b),-8+38*sin(b),z),(36.1*cos(b),-8+39.1*sin(b),z),(36.1*cos(a),-8+39.1*sin(a),z)])
        batch('Opera gallery light ribbons',warm,'04',True).beam((36.13*cos(a),-8+39.13*sin(a),z+.1),(36.13*cos(b),-8+39.13*sin(b),z+.1),.055)
for i in range(280):
    a=i*2*pi/280
    batch('Opera delicate vertical bronze mesh',bronze,'04').beam((35.13*cos(a),-8+38.13*sin(a),1),(35.13*cos(a),-8+38.13*sin(a),27),.028,4)
for i in range(144):
    a=i*2*pi/144;b=(i+1)*2*pi/144
    batch('Opera flat roof',wood,'04').face([(0,-8,27),(35*cos(a),-8+38*sin(a),27),(35*cos(b),-8+38*sin(b),27)],[(.5,.5),(0,0),(1,1)])
for y in [42,-49]:
    for x in range(-42,43,7):
        batch('Public foyer columns',truss,'04').beam((x,y,1),(x,y,15),.22,10)
    for z in [3.8,7.6,11.4]:
        batch('Public foyer mezzanines',stone,'04').box((0,y,z),(91,8,.28))
        batch('Foyer warm ceiling lines',warm,'04').box((0,y+3,z-.21),(88,.10,.09))
        batch('Foyer horizontal rails',steel,'04').beam((-44,y+4,z+1),(44,y+4,z+1),.035)
        for x in range(-44,45,4):
            batch('Foyer rail posts',steel,'04').beam((x,y+4,z),(x,y+4,z+1),.025,4)

# Site: scaled from architect's site plan. Approximate rounded-rectangle pool.
def squircle(a,rx=145,ry=108,exponent=4.8):
    c,s=cos(a),sin(a)
    return (rx*math.copysign(abs(c)**(2/exponent),c),ry*math.copysign(abs(s)**(2/exponent),s))
N=360
for i in range(N):
    a=i*2*pi/N;b=(i+1)*2*pi/N
    x0,y0=squircle(a);x1,y1=squircle(b)
    ix0,iy0=(A+.52)*cos(a),(B+.52)*sin(a)
    ix1,iy1=(A+.52)*cos(b),(B+.52)*sin(b)
    batch('Reflecting pool surface',water,'05',True).face([(ix0,iy0,.35),(x0,y0,.35),(x1,y1,.35),(ix1,iy1,.35)])
    # The underwater roof is a modeled object, not a fake bridge.
    if abs(x0)>12 and abs(x1)>12:
        batch('Pool dark basin',black,'05').face([(ix0,iy0,.02),(x0,y0,.02),(x1,y1,.02),(ix1,iy1,.02)])
    x2,y2=squircle(a,148.8,111.8);x3,y3=squircle(b,148.8,111.8)
    batch('Pool perimeter stone coping',stone2,'05').face([(x0,y0,.45),(x1,y1,.45),(x3,y3,.45),(x2,y2,.45)])
    batch('Pool perimeter retaining face',black,'05').face([(x0,y0,.02),(x1,y1,.02),(x1,y1,.45),(x0,y0,.45)])
    x4,y4=squircle(a,166,130);x5,y5=squircle(b,166,130)
    if not (abs(x2)<21 and abs(y2)>108):
        batch('Circumferential promenade',stone,'05').face([(x2,y2,.43),(x3,y3,.43),(x5,y5,.43),(x4,y4,.43)])
    if i%3==0:
        batch('Promenade radial paving joints',seam,'05').beam((x2,y2,.439),(x4,y4,.439),.014,4)
for scale in [1.018,1.04,1.066,1.09]:
    batch('Promenade concentric paving joints',seam,'05').polyline([(*squircle(k*2*pi/N,145*scale,108*scale),.44) for k in range(N+1)],.012,4)
for k in range(22):
    a=k*2*pi/22
    p=(A+.65)*cos(a),(B+.65)*sin(a),.4
    x,y=squircle(a)
    # thin flush pool compartment walls seen in the source photographs
    batch('Twenty two flush basin dividers',stone2,'05').beam(p,(x,y,.4),.11,4)

# North and south under-water arrival galleries.
for sign in [-1,1]:
    y0=sign*72;y1=sign*108
    batch('Submerged gallery transparent roof',glass[0],'05').box((0,(y0+y1)/2,.28),(22,abs(y1-y0),.10))
    for x in [-11,11]:
        batch('Submerged gallery edge',stone2,'05').box((x,(y0+y1)/2,.24),(.22,abs(y1-y0),.18))
    for j in range(14):
        y=y0+(y1-y0)*j/13
        batch('Submerged gallery roof grid',steel,'05').box((0,y,.25),(22,.12,.18))
        batch('Submerged gallery luminous slats',warm,'05').box((0,y,.13),(18,.08,.06))
    batch('Submerged arrival gallery floor',stone,'05').box((0,(y0+y1)/2,-4.78),(22,abs(y1-y0),.22))
    for x in [-11.4,11.4]:
        batch('Submerged arrival gallery side walls',stone,'05').box((x,(y0+y1)/2,-2.25),(.38,abs(y1-y0),5.1))
    # Broad open staircourt descends from park level to the submerged gallery.
    for j in range(32):
        y=sign*(109+j*1.32)
        z=-4.5+j*.154
        batch('Sunken arrival stair treads',stone2,'05').box((0,y,(-4.9+z)/2),(22+j*.44,1.34,z+4.9))
    for x in [-18,18]:
        batch('Sunken staircourt retaining walls',stone,'05').box((x,sign*129,-2.2),(.55,42,5.3))
    for x in [-8,8]:
        batch('Sunken arrival handrails',steel,'05').polyline([(x,sign*109,-3.5),(x,sign*150,1.27)],.05,8)
        for j in range(11):
            y=sign*(109+j*4);z=-4.5+j*.466
            batch('Arrival handrail posts',steel,'05').beam((x,y,z),(x,y,z+1),.038,6)

# Landscape frontage and southern garden: deliberately limited to immediate site.
for x in [-108,108]:batch('Site supporting ground',grass,'06').box((x,0,.015),(176,402,.03))
batch('Site supporting ground',grass,'06').box((0,0,.015),(40,216,.03))
for y in [-177,177]:batch('Site supporting ground',grass,'06').box((0,y,.015),(40,48,.03))
for sign in [-1,1]:
    for x in [-46,46]:batch('North south arrival plaza',stone,'05').box((x,sign*154,.13),(50,42,.25))
    batch('North south arrival plaza',stone,'05').box((0,sign*166,.13),(42,18,.25))
    batch('Tree line walkway',stone,'05').box((sign*186,0,.13),(12,362,.25))
for x in [-68,68]:
    for y in [-172,168]:
        batch('Raised elliptical garden edging',stone2,'06',True).sphere((x,y,.24),(26,18,.32),4,48)
        batch('Elliptical lawn garden',grass,'06',True).sphere((x,y,.36),(25.5,17.5,.16),4,48)
def tree(x,y,size=1):
    h=(6.0+random.random()*1.8)*size
    batch('Tree trunks and branches',soil,'06',True).beam((x,y,.15),(x,y,h*.75),.17*size,7)
    tone=random.randrange(4)
    for k in range(8):
        a=k*2*pi/8+random.uniform(-.2,.2);r=random.uniform(1.1,2.4)*size
        c=(x+cos(a)*r,y+sin(a)*r,h*.76+random.uniform(-.6,1.4)*size)
        batch(f'Tree canopies {tone+1}',foliage[tone],'06',True).sphere(c,(2.3*size,2.2*size,2.5*size),6,10)
        if k%2==0:batch('Tree trunks and branches',soil,'06',True).beam((x,y,h*.4),c,.065*size)
for x in [-186,186]:
    for y in range(-181,182,13):tree(x+random.uniform(-1,1),y,.8)
for y in [-190,192]:
    for x in range(-171,172,14):tree(x,y,.85)
for x in [-66,66]:
    for y in [-175,170]:
        for k in range(7):
            a=k*2*pi/7;tree(x+17*cos(a),y+9*sin(a),.68)
for x in [-171,171]:
    for y in range(-108,109,24):
        batch('Timber benches',wood,'06').box((x,y,.68),(3.2,.68,.15))
        for xx in [-1.1,1.1]:batch('Bench stainless legs',steel,'06').box((x+xx,y,.36),(.12,.57,.62))
        batch('Landscape lamp housings',black,'06').box((x,y+3,.6),(.20,.20,1.12))
        batch('Landscape warm lamp lenses',pathlight,'06').box((x,y+3,1.1),(.22,.22,.15))
for x in range(-70,71,14):
    for sign in [-1,1]:
        batch('Arrival bollards',black,'06',True).beam((x,sign*151,.2),(x,sign*151,1.1),.08,8)
        batch('Arrival bollard light caps',pathlight,'06',True).sphere((x,sign*151,1.08),(.12,.12,.09),4,8)

asset_objects=[]
for bb in batches.values():
    ob=bb.finish()
    if ob:asset_objects.append(ob)

# Analytic curved-shell normals avoid faceted highlights on isolated metal panels.
for ob in asset_objects:
    if ob.name.startswith('Titanium panels') or 'glass panes' in ob.name or ob.name=='Shell joint backing':
        normals=[]
        for v in ob.data.vertices:
            x,y,z=v.co; normals.append(Vector((x/A**2,y/B**2,z/H**2)).normalized())
        ob.data.normals_split_custom_set_from_vertices(normals)

for ob in asset_objects:
    # Named export selection keeps studio objects out of the runtime asset.
    ob.select_set(True)
scene['asset_title']='北京国家大剧院 | National Centre for the Performing Arts'
scene['architect']='Paul Andreu with ADPI / BIAD'
scene['source_basis']='212.2 x 143.64 x 46.285 m; source-based reconstruction, approximate facade and landscape'
scene['runtime_standard']='Cyber-Sight Geo: meter scale, local Z-up, PBR emissive night channel'
scene['titanium_panel_count']=panel_count;scene['curtain_pane_count']=pane_count

# Architectural visualization rig, excluded from GLB.
def link_rig(ob):
    for c in list(ob.users_collection):c.objects.unlink(ob)
    collections['90'].objects.link(ob)
def camera(name,loc,target,lens=50):
    d=bpy.data.cameras.new(name);o=bpy.data.objects.new(name,d);collections['90'].objects.link(o)
    o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();d.lens=lens;d.clip_end=5000
    return o
camera('Hero day | northeast lake', (230,365,87),(0,0,18),58)
camera('Hero night | low lake reflection', (165,335,64),(0,0,14),56)
camera('Aerial | plan and landscape',(245,335,365),(0,0,0),48)
camera('Detail | titanium glass junction',(132,154,45),(32,54,24),58)
camera('Elevation | north',(0,330,40),(0,0,19),48)
sun_data=bpy.data.lights.new('Sun | day','SUN');sun_data.energy=3;sun_data.angle=.08
sun=bpy.data.objects.new('Sun | day',sun_data);collections['90'].objects.link(sun);sun.rotation_euler=(.6,-.5,-.65)
world=bpy.data.worlds.new('Architectural sky');world.use_nodes=True;scene.world=world
nt=world.node_tree;nt.nodes.clear();out=nt.nodes.new('ShaderNodeOutputWorld');bg=nt.nodes.new('ShaderNodeBackground');sky=nt.nodes.new('ShaderNodeTexSky')
sky.sky_type='SINGLE_SCATTERING';sky.sun_elevation=.48;sky.sun_rotation=2.3;sky.altitude=.2;sky.air_density=1;sky.aerosol_density=.6;sky.sun_disc=False
bg.inputs['Strength'].default_value=.45;nt.links.new(sky.outputs['Color'],bg.inputs['Color']);nt.links.new(bg.outputs['Background'],out.inputs['Surface'])
scene.camera=bpy.data.objects.get('Hero day | northeast lake')

def area(name,loc,target,power,color,size):
    d=bpy.data.lights.new(name,'AREA');d.energy=power;d.color=color;d.shape='DISK';d.size=size
    o=bpy.data.objects.new(name,d);collections['90'].objects.link(o);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
    o.hide_render=True;return o
area('Night | warm lake facade', (20,132,28),(0,0,23),120000,(1,.55,.25),105)
area('Night | cool titanium rim',(100,-120,110),(0,0,22),130000,(.57,.70,1),135)
area('Night | gallery glow',(0,47,17),(0,78,22),55000,(1,.66,.34),70)
area('Night | southern gallery',(0,-47,17),(0,-78,22),50000,(1,.66,.34),70)
# Large neutral ground receiver is presentation-only.
bpy.ops.mesh.primitive_plane_add(size=20000,location=(0,0,-.015));o=bpy.context.object;o.name='Presentation ground receiver';link_rig(o);o.data.materials.append(material('Presentation ground | neutral',(.13,.16,.17),0,.85))
o.select_set(False)

# Source working frame X=east/Y=north is calibrated into Cesium's glTF frame.
# After Y-up export: glTF +Z=east, +X=north, +Y=up at heading=0.
geo=bpy.data.objects.new('GEO_ROOT',None);collections['01'].objects.link(geo)
geo.rotation_euler.z=-pi/2
metadata={'geo_metadata_version':1,'horizontal_crs':'EPSG:4326','vertical_reference':'WGS84_ELLIPSOID','longitude_wgs84':116.38355,'latitude_wgs84':39.90334,'coordinate_source':'OpenStreetMap way 4974233 building centre, cross-checked against Brown Archivision GPS; public reference, not surveyed','coordinate_accuracy':'approximate','height_source':'terrain_at_load','units':'meters','local_origin':'ground_waterline_datum_at_building_plan_center; arrival stairs extend to -4.9 m','height_m':46.285}
for k,v in metadata.items():geo[k]=v
for o in asset_objects:o.parent=geo
for o in list(collections['90'].objects):o.parent=geo
(ROOT/'placement.json').write_text(json.dumps({**metadata,'url':'https://sample-data-jt.vercel.app/beijing-ncpa/beijing-ncpa.glb','scale':1,'heading':0,'pitch':0,'roll':0,'orientation':'Calibrated root: glTF +X north, +Z east. North entrance toward +X.','manual_preview_height_m':0,'manual_preview_height_note':'0 is only for ellipsoid/no-terrain preview, not a measured elevation.'},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

bpy.ops.object.select_all(action='DESELECT')
for o in asset_objects:o.select_set(True)
geo.select_set(True)
bpy.context.view_layer.objects.active=asset_objects[0]
for a in bpy.context.screen.areas if bpy.context.screen else []:
    if a.type=='VIEW_3D':
        a.spaces.active.region_3d.view_distance=430
        a.spaces.active.region_3d.view_location=(0,0,16)
        a.spaces.active.clip_end=5000
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'beijing-ncpa.blend'))
export_path=ROOT/'beijing-ncpa-export.glb'
bpy.ops.export_scene.gltf(filepath=str(export_path),export_format='GLB',use_selection=True,export_yup=True,export_apply=True,export_texcoords=True,export_normals=True,export_tangents=True,export_materials='EXPORT',export_cameras=False,export_lights=False,export_extras=True,export_image_format='AUTO')
import sys
sys.path.insert(0,str(ROOT))
from finalize_glb import finalize
finalize(export_path)
export_path.replace(ROOT/'beijing-ncpa.glb')
record={'building_dimensions_m':[212.2,143.64,46.285],'titaniumPanels':panel_count,'glassPanes':pane_count,'objects':len(asset_objects),'triangles_blender':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in asset_objects),'materials':len(set(o.data.materials[0].name for o in asset_objects)),'modeling_basis':'Published dimensions; photograph/plan reconstruction. Facade partition, interior envelopes and landscape approximate.','export':'metres, Blender Z-up to glTF Y-up, ground-centre origin, self-contained GLB'}
(ROOT/'model-manifest.json').write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('NCPA_BUILD_COMPLETE',json.dumps(record))
