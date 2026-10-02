"""Original Taipei 101 architectural reconstruction, metres, Blender 5.2.
Sources and estimated dimensions are documented in README.md.
Execute successive stages with exec(compile(...)); build_body(), build_site(), finish().
"""
import bpy, math, random, os, json
from mathutils import Vector
OUT=os.path.dirname(os.path.abspath(__file__))
rng=random.Random(101508)
scene=bpy.data.scenes.new('Taipei_101_Portfolio')
bpy.context.window.scene=scene
scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
asset=bpy.data.collections.new('TAIPEI_101_EXPORT');scene.collection.children.link(asset)
rig=bpy.data.collections.new('PRESENTATION_ONLY_101');scene.collection.children.link(rig)
root=bpy.data.objects.new('Taipei101_508m_GroundOrigin',None);asset.objects.link(root)
root['height_m']=508.;root['longitude_wgs84']=121.564472;root['latitude_wgs84']=25.033964
root['scope']='Original photo/engineering-reference architectural visualization; estimated facade, podium and landscape. Not survey/BIM geometry.'
root['night_channel']='PBR emissive for Cyber-Sight solar-altitude control. No runtime lights or bloom.'
mats={};buf={}
def mat(name,col,metal=0,rough=.5,emit=None,power=0):
    m=bpy.data.materials.new(name);m.use_nodes=True
    bs=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    bs.inputs['Base Color'].default_value=(*col,1);bs.inputs['Metallic'].default_value=metal;bs.inputs['Roughness'].default_value=rough
    bs.inputs['Coat Weight'].default_value=.3 if metal>.2 else 0
    bs.inputs['Coat Roughness'].default_value=.18
    m.diffuse_color=(*col,1)
    if emit:
        bs.inputs['Emission Color'].default_value=(*emit,1);bs.inputs['Emission Strength'].default_value=power;m['night_strength']=power
    mats[name]=m;return name
glass=[mat('Jade curtain glass %02d'%i,(.095+i*.012,.245+i*.012,.255+i*.013),.44,.20+i*.013) for i in range(7)]
silver=mat('Pearl aluminium frames',(.56,.62,.60),.72,.27)
dark=mat('Recessed graphite seals',(.025,.055,.060),.28,.48)
jade=mat('Patinated teal corner ornaments',(.105,.235,.22),.66,.32)
stone=mat('Ivory limestone cladding',(.55,.52,.44),.02,.7)
granite=mat('Warm grey plaza granite',(.38,.39,.365),0,.88)
paving=mat('Basalt paving and joints',(.105,.15,.16),0,.87)
bronze=mat('Champagne bronze entrance metal',(.43,.32,.17),.7,.30)
wood=mat('Timber and bark',(.13,.073,.029),0,.89)
leaf=mat('Taiwan evergreen foliage',(.065,.16,.061),0,.92)
leaf2=mat('Tree canopy highlights',(.15,.26,.087),0,.9)
warm=mat('Night office warm',(.15,.265,.255),.39,.27,(1,.74,.46),.9)
dim=mat('Night office low occupancy',(.12,.25,.255),.43,.25,(1,.80,.57),.25)
cool=mat('Night office cool',(.14,.29,.32),.39,.26,(.64,.84,1),.65)
rim=mat('Night architectural cornice champagne',(.45,.50,.43),.64,.31,(1,.73,.39),1.5)
lantern=mat('Night dragon lantern amber',(.5,.45,.28),.45,.35,(1,.62,.26),2.2)
lobby=mat('Night retail warm interior',(.15,.26,.25),.28,.25,(1,.73,.43),1.3)
spirelight=mat('Night pinnacle pearl',(.44,.57,.6),.55,.27,(.61,.85,1),1.6)
pathlight=mat('Night plaza lamps',(.65,.5,.29),.35,.35,(1,.64,.28),2.8)
def face(ps,mi,part='Facade',smooth=False):
    ps=[Vector(p) for p in ps];clean=[]
    for p in ps:
        if not any((p-q).length<.00001 for q in clean):clean.append(p)
    if len(clean)<3:return
    key=(part,mi,smooth)
    if key not in buf:buf[key]=[[],[],{}]
    vs,fs,lookup=buf[key];ids=[]
    for p in clean:
        keyp=tuple(round(x,5) for x in p)
        if keyp not in lookup:lookup[keyp]=len(vs);vs.append(tuple(p))
        ids.append(lookup[keyp])
    fs.append(tuple(ids))
def box(c,size,mi,part='Structure'):
    c=Vector(c);x,y,z=[v/2 for v in size]
    ps=[c+Vector(p) for p in [(-x,-y,-z),(x,-y,-z),(x,y,-z),(-x,y,-z),(-x,-y,z),(x,-y,z),(x,y,z),(-x,y,z)]]
    for f in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]:face([ps[i] for i in f],mi,part)
def beam(a,b,w,mi,part='Frames',depth=None):
    a,b=Vector(a),Vector(b);d=b-a
    if d.length<.00001:return
    d.normalize();ref=Vector((0,0,1)) if abs(d.z)<.95 else Vector((0,1,0))
    u=d.cross(ref).normalized()*w/2;v=d.cross(u).normalized()*(depth or w)/2
    ps=[a-u-v,a+u-v,a+u+v,a-u+v,b-u-v,b+u-v,b+u+v,b-u+v]
    for f in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]:face([ps[i] for i in f],mi,part)
def tube(a,b,r,mi,part='Ornaments',n=12,r1=None):
    a,b=Vector(a),Vector(b);d=(b-a).normalized();ref=Vector((0,0,1)) if abs(d.z)<.95 else Vector((0,1,0))
    u=d.cross(ref).normalized();v=d.cross(u).normalized();r1=r if r1 is None else r1
    pa=[a+r*(u*math.cos(math.tau*i/n)+v*math.sin(math.tau*i/n)) for i in range(n)]
    pb=[b+r1*(u*math.cos(math.tau*i/n)+v*math.sin(math.tau*i/n)) for i in range(n)]
    for i in range(n):j=(i+1)%n;face([pa[i],pa[j],pb[j],pb[i]],mi,part,True)
    face(list(reversed(pa)),mi,part);face(pb,mi,part)
def poly(h,z,c=2.2):
    return [Vector((x,y,z)) for x,y in [(-h+c,-h),(h-c,-h),(h,-h+c),(h,h-c),(h-c,h),(-h+c,h),(-h,h-c),(-h,-h+c)]]
def band(h,z,w,mi,part,c=2.2):
    ps=poly(h,z,c)
    for i in range(8):beam(ps[i],ps[(i+1)%8],w,mi,part)
def shell(z0,z1,h0,h1,mi,part,c=2.2):
    a,b=poly(h0,z0,c),poly(h1,z1,c)
    for i in range(8):j=(i+1)%8;face([a[i],a[j],b[j],b[i]],mi,part)
    face(b,mi,part)
def facade(z0,z1,h0,h1,rows,part,lit=True,c=2.2):
    a,b=poly(h0,z0,c),poly(h1,z1,c)
    for side in range(8):
        j=(side+1)%8;cols=24 if side%2==0 else 3
        for row in range(rows):
            t0=row/rows;t1=(row+1)/rows
            A=a[side].lerp(b[side],t0);B=a[j].lerp(b[j],t0);C=a[side].lerp(b[side],t1);D=a[j].lerp(b[j],t1)
            for k in range(cols):
                u0=(k+.065)/cols;u1=(k+.935)/cols
                p=[A.lerp(B,u0),A.lerp(B,u1),C.lerp(D,u1),C.lerp(D,u0)]
                # Insets and non-uniform vertical occupancy avoid a checkerboard night map.
                rnd=random.Random(101+side*919+row//2*123+k//3*47+int(z0)*37).random()
                mi=warm if lit and rnd<.14 else dim if lit and rnd<.28 else cool if lit and .56<rnd<.62 else glass[(k+row+side)%7]
                face(p,mi,part+' glazing')
            beam(A,B,.17,silver,part+' horizontal transoms',depth=.24)
        beam(b[side],b[j],.20,silver,part+' horizontal transoms')
        for k in range(cols+1):
            u=k/cols;beam(a[side].lerp(a[j],u),b[side].lerp(b[j],u),.16,silver,part+' vertical mullions',depth=.25)
        beam(a[side],b[side],.48,jade,part+' corner ribs',depth=.50)
    face(poly(h1,z1,c),dark,part+' roof closure')
def scroll(center,u,v,r,mi,part='Ruyi and dragon scrollwork'):
    center,u,v=Vector(center),Vector(u),Vector(v)
    pts=[]
    for k in range(49):
        t=k/48;ang=math.tau*1.45*t;rr=r*(1-.83*t)
        pts.append(center+u*rr*math.cos(ang)+v*rr*math.sin(ang))
    for a,b in zip(pts,pts[1:]):tube(a,b,r*.075,mi,part,n=8)
def medallion(center,normal,r):
    n=Vector(normal);u=Vector((n.y,-n.x,0));v=Vector((0,0,1));center=Vector(center)
    tube(center-n*.24,center+n*.24,r,jade,'24F coin medallion backing',n=64)
    for rad,mi in [(r,bronze),(r*.87,silver),(r*.71,bronze)]:
        ps=[center+n*.3+rad*(u*math.cos(math.tau*k/64)+v*math.sin(math.tau*k/64)) for k in range(65)]
        for a,b in zip(ps,ps[1:]):tube(a,b,.12,mi,'Coin medallion relief',n=8)
    p=center+n*.4;sz=r*.35
    face([p+u*x+v*y for x,y in [(-sz,-sz),(sz,-sz),(sz,sz),(-sz,sz)]],dark,'Square coin aperture')
    for a,b in [((-sz,-sz),(sz,-sz)),((sz,-sz),(sz,sz)),((sz,sz),(-sz,sz)),((-sz,sz),(-sz,-sz))]:beam(p+u*a[0]+v*a[1],p+u*b[0]+v*b[1],.18,bronze,'Coin square border')
def build_body():
    shell(0,6,31.75,31.2,dark,'Lobby core')
    facade(1,108,31.7,23.4,52,'Lower tapered tower')
    for z in [6,23.5,41,58.5,76,93.5,108]:band(31.7-(31.7-23.4)*(z-1)/107+.13,z,.40,silver,'Lower tower structural bands')
    shell(108,116,23.4,23.3,dark,'26F transition mechanical floor')
    for z in [108.4,109.1,109.8,110.5,111.2,111.9,112.6,113.3]:band(23.65,z,.18,silver,'Transition louvres')
    for normal in [(0,-1,0),(1,0,0),(0,1,0),(-1,0,0)]:medallion(Vector(normal)*24.4+Vector((0,0,108)),normal,4.5)
    band(24.6,114.5,.45,rim,'Transition night cornice')
    for tier in range(8):
        z0=116+tier*34.25;zt=z0+34.25
        facade(z0,zt-2.0,23.25,27.2,16,'Bamboo module %02d'%(tier+1))
        shell(zt-2,zt-.35,27.2,27.38,dark,'Module recessed mechanical fascia')
        for k in range(5):band(27.49,zt-1.75+k*.28,.11,silver,'Module fascia ventilation louvres')
        band(27.52,zt-.22,.48,silver,'Eight module pearl copings')
        band(27.65,zt-.82,.13,rim,'Eight module champagne night rim')
        # Projecting layered corner brackets and twin cloud curls, derived from photos.
        for sx,sy in [(-1,-1),(1,-1),(1,1),(-1,1)]:
            n=Vector((sx,sy,0)).normalized();u=Vector((sy,-sx,0)).normalized();v=Vector((0,0,1))
            p=Vector((sx*26.3,sy*26.3,zt-1.6))
            for k in range(4):
                a=p+n*(.35+k*.38)-v*(k*.7);beam(a-u*1.4,a+u*1.4,.23,jade,'Dragon corner stacked brackets')
            tube(p+n*.5-v*2.8,p+n*1.2+v*.6,.55,jade,'Dragon corner vertical fin',n=12)
            scroll(p+n*1.8-u*.75-v*.7,u,v,1.03,jade);scroll(p+n*1.8+u*.75-v*.7,-u,v,1.03,jade)
            box(p+n*1.85-v*1.4,(.8,.8,.65),lantern,'Corner amber lanterns')
    # Narrow observation/equipment pinnacle above 90F, with pronounced setbacks.
    for z0,z1,h0,h1,rows in [(390,401,16.8,15.7,5),(401,418,12.2,14.3,8),(418,434,9.2,11.3,8),(434,448,6.2,7.3,6)]:
        facade(z0,z1,h0,h1,rows,'Observation pinnacle',c=1.1)
        band(h1+.35,z1-.4,.5,silver,'Observation terrace coping',c=1.1)
        band(h1+.45,z1-1.1,.17,spirelight,'Observation pearl night rings',c=1.1)
        for dz in [.4,1.1,1.8]:band(h1+.25,z1-dz,.15,silver,'Observation horizontal ribs',c=1.1)
    # 60 m steel spire, concentric collars and vertical facets.
    for z0,z1,r0,r1 in [(448,452,3.7,3.7),(452,466,2.9,2.1),(466,489,1.8,.9),(489,507.8,.9,.22)]:
        tube((0,0,z0),(0,0,z1),r0,silver,'Spire steel shell',n=24,r1=r1)
        for k in range(8):
            a=math.tau*k/8;tube((r0*math.cos(a),r0*math.sin(a),z0),(r1*math.cos(a),r1*math.sin(a),z1),.06,spirelight,'Pinnacle vertical light ribs',n=6)
    tube((0,0,507.65),(0,0,508),.21,lantern,'Aviation beacon',n=12,r1=.05)
    for z,r in [(449,3.8),(452,3),(458,2.7),(466,2.15),(478,1.45),(489,1)]:tube((0,0,z-.22),(0,0,z+.22),r,jade,'Spire structural collars',n=24)
    print('BODY_READY',len(buf))
def retail_block(cx,cy,w,d,h):
    box((cx,cy,h/2),(w,d,h),dark,'Retail podium core')
    for side in range(4):
        if side==0:a,b=Vector((cx-w/2,cy-d/2,0)),Vector((cx+w/2,cy-d/2,0))
        elif side==1:a,b=Vector((cx+w/2,cy-d/2,0)),Vector((cx+w/2,cy+d/2,0))
        elif side==2:a,b=Vector((cx+w/2,cy+d/2,0)),Vector((cx-w/2,cy+d/2,0))
        else:a,b=Vector((cx-w/2,cy+d/2,0)),Vector((cx-w/2,cy-d/2,0))
        n=Vector(((b-a).y,-(b-a).x,0)).normalized();a+=n*.1;b+=n*.1
        cols=int((b-a).length/2.1)
        for f in range(6):
            z0=.7+f*(h-.7)/6;z1=z0+(h-.7)/6-.22
            for k in range(cols):
                p=a.lerp(b,(k+.07)/cols);q=a.lerp(b,(k+.93)/cols)
                face([p+Vector((0,0,z0)),q+Vector((0,0,z0)),q+Vector((0,0,z1)),p+Vector((0,0,z1))],lobby if f<2 and k%7<4 else glass[(k+f)%7],'Retail curtain wall')
            beam(a+Vector((0,0,z0)),b+Vector((0,0,z0)),.32,silver,'Retail floor fascias')
        for k in range(cols+1):beam(a.lerp(b,k/cols),a.lerp(b,k/cols)+Vector((0,0,h)),.16,silver,'Retail mullions')
        beam(a+Vector((0,0,h-.65)),b+Vector((0,0,h-.65)),.13,rim,'Retail night cornice')
        for k in range(1,cols,4):
            p=a.lerp(b,k/cols)+n*.5
            box(p+Vector((0,0,h/2)),(1.2,1.2,h),stone,'Retail limestone piers')
            for dz in range(10):beam(p+Vector((0,0,h-4+dz*.35))-n*.2,p+Vector((0,0,h-4+dz*.35))+n*1.1,.14,silver,'Retail ruyi pier horizontal relief')
            scroll(p+n*.72+Vector((0,0,h-7)),Vector((n.y,-n.x,0)),Vector((0,0,1)),.63,jade,'Retail ruyi pier emblems')
    # Slender roof ridges sweep up at the ends, echoing the phoenix tail silhouette.
    for row in range(8):
        y=cy-d/2+row*d/8
        for i in range(24):
            x0=cx-w/2+w*i/24;x1=cx-w/2+w*(i+1)/24
            z0=h+1.7+3*(abs((x0-cx)/(w/2))**4);z1=h+1.7+3*(abs((x1-cx)/(w/2))**4)
            face([(x0,y,z0),(x1,y,z1),(x1,y+d/8,z1),(x0,y+d/8,z0)],jade,'Phoenix tail folded roof')
            beam((x0,y,z0+.04),(x1,y,z1+.04),.12,silver,'Phoenix roof seams')
def tree(x,y,scale=1):
    box((x,y,.30),(4,4,.5),paving,'Landscape planters');box((x,y,.6),(3.5,3.5,.12),leaf,'Landscape planters')
    tube((x,y,.65),(x,y,4.7*scale),.22*scale,wood,'Tree trunks',n=8)
    for k in range(3):
        cx=x+rng.uniform(-1,1);cy=y+rng.uniform(-1,1);cz=(4.8+k*.65)*scale;r=(1.8-k*.15)*scale
        for a in range(10):
            for b in range(6):
                pts=[]
                for aa,bb in [(a,b),(a+1,b),(a+1,b+1),(a,b+1)]:
                    ang=math.tau*aa/10;phi=-math.pi/2+math.pi*bb/6
                    pts.append((cx+r*math.cos(phi)*math.cos(ang),cy+r*math.cos(phi)*math.sin(ang),cz+r*math.sin(phi)))
                face(pts,leaf if k%2 else leaf2,'Landscape canopies',True)
def build_site():
    # Estimated podium/site plan, tower at north-east of a landscaped retail complex.
    box((-24,-27,.15),(168,154,.3),granite,'Site stone apron')
    retail_block(-64,-23,56,118,28)
    retail_block(0,-62,72,40,25)
    retail_block(-56,28,75,28,24)
    # Barrel-vaulted long-span skylight over mall atrium.
    for i in range(28):
        x0=-54+i*1.5;x1=x0+1.5
        for j in range(16):
            a=-math.pi/2+math.pi*j/16;b=-math.pi/2+math.pi*(j+1)/16
            p=[(x,-20+10*math.sin(t),28+7*math.cos(t)) for x,t in [(x0,a),(x1,a),(x1,b),(x0,b)]]
            face(p,glass[3],'Mall barrel skylight');beam(p[0],p[3],.15,silver,'Atrium arch ribs');beam(p[0],p[1],.12,silver,'Atrium long purlins')
    # Photo-based monumental recessed entrance, transom glazing and bronze canopy.
    box((0,-31.5,14),(27,1.5,27),stone,'Tower entrance limestone portal')
    box((0,-32.35,13),(20,.35,20),jade,'Recessed entrance inner frame')
    box((0,-32.65,12),(16,.25,16),dark,'Entrance deep reveal')
    for x in range(-7,8,2):
        box((x,-32.82,10),(1.82,.12,12),lobby,'Entrance glazed screen');beam((x-1,-32.95,4),(x-1,-32.95,16),.10,bronze,'Entrance bronze mullions')
    box((0,-36,6.3),(26,8,.55),bronze,'Entry projecting canopy')
    box((0,-36,5.96),(25,7.4,.13),lobby,'Entry illuminated soffit')
    for x in range(-11,12,2):beam((x,-32,4.8),(x,-39,6.3),.24,bronze,'Entry canopy sculpted brackets')
    for x in [-12,12]:beam((x,-37,0),(x,-37,6.3),.35,silver,'Entry canopy posts')
    for k in range(4):box((0,-39-k*.48,.1+.12*(3-k)),(26+2*k,.95,.22),stone,'Public entry steps')
    # Raised ruyi emblem on portal rather than image decals.
    scroll((-1,-32.65,26),(1,0,0),(0,0,1),1.15,jade,'Entry ruyi crest');scroll((1,-32.65,26),(-1,0,0),(0,0,1),1.15,jade,'Entry ruyi crest')
    beam((0,-32.7,23),(0,-32.7,26),.3,jade,'Entry ruyi crest')
    for x in range(-100,60,8):beam((x,-104,.33),(x,50,.33),.045,paving,'Plaza paving joints',depth=.03)
    for y in range(-100,51,8):beam((-108,y,.33),(60,y,.33),.045,paving,'Plaza paving joints',depth=.03)
    for x,y in [(x,-96) for x in range(-96,55,12)]+[(52,y) for y in range(-78,48,12)]+[(x,44) for x in range(-94,45,12)]:
        tree(x,y,rng.uniform(.83,1.17))
        box((x+3,y-3,.8),(.6,.6,1.6),dark,'Plaza bollards');box((x+3,y-3,1.55),(.53,.53,.12),pathlight,'Bollard luminous cap')
    for x,y in [(-20,-89),(12,-88),(42,-15),(-100,15)]:
        box((x,y,.7),(6,1.4,.3),wood,'Street furniture benches')
        for dx in [-2,2]:box((x+dx,y,.4),(.4,1,.6),silver,'Bench supports')
    # Tower lobby corners have recessed openings and restrained night wash.
    for sx,sy in [(-1,-1),(1,-1),(1,1),(-1,1)]:
        beam((sx*29,sy*29,.4),(sx*29,sy*29,7),.8,stone,'Lobby corner piers')
    print('SITE_READY',len(buf))
def flush():
    for (part,mi,smooth),(vs,fs,_) in buf.items():
        me=bpy.data.meshes.new(part+' mesh');me.from_pydata(vs,[],fs);me.materials.append(mats[mi]);me.validate();me.update()
        ob=bpy.data.objects.new(part+' | '+mi,me);asset.objects.link(ob);ob.parent=root
        if smooth:
            for p in me.polygons:p.use_smooth=True
    buf.clear()
def finish():
    flush()
    for ob in scene.objects:ob.select_set(False)
    for ob in asset.objects:ob.select_set(True)
    bpy.context.view_layer.objects.active=next(o for o in asset.objects if o.type=='MESH')
    bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,'taipei-101.glb'),export_format='GLB',use_selection=True,export_yup=True,export_apply=True,export_materials='EXPORT',export_extras=True,export_cameras=False,export_lights=False)
    # Studio rig is deliberately outside the export collection.
    world=bpy.data.worlds.new('Taipei studio world');world.use_nodes=True;scene.world=world
    bg=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs['Color'].default_value=(.13,.22,.30,1);bg.inputs['Strength'].default_value=.6
    def light(name,kind,pos,energy,col,size=0):
        data=bpy.data.lights.new(name,kind);data.energy=energy;data.color=col
        if size:data.size=size
        ob=bpy.data.objects.new(name,data);rig.objects.link(ob);ob.location=pos;ob.rotation_euler=(Vector((0,0,250))-ob.location).to_track_quat('-Z','Y').to_euler();return ob
    sun=light('101 preview sun','SUN',(500,-700,850),2.7,(1,.85,.66));sun.data.angle=math.radians(4)
    light('101 large soft fill','AREA',(300,400,600),1600000,(.55,.8,1),400)
    camdata=bpy.data.cameras.new('101 architecture camera');camdata.type='ORTHO';camdata.ortho_scale=625;camdata.clip_end=10000
    cam=bpy.data.objects.new('101 architecture camera',camdata);rig.objects.link(cam);cam.location=(780,-1050,655);cam.rotation_euler=(Vector((-10,-12,240))-cam.location).to_track_quat('-Z','Y').to_euler();scene.camera=cam
    scene.render.engine='BLENDER_EEVEE';scene.render.resolution_x=1440;scene.render.resolution_y=1800;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG'
    for mi in mats.values():
        if mi.get('night_strength') is not None:next(n for n in mi.node_tree.nodes if n.type=='BSDF_PRINCIPLED').inputs['Emission Strength'].default_value=0
    for ob in scene.objects:ob.select_set(False)
    if bpy.context.screen:
        for area in bpy.context.screen.areas:
            if area.type=='VIEW_3D':
                sp=area.spaces.active;sp.clip_end=10000;sp.overlay.show_overlays=False;sp.shading.type='MATERIAL';sp.shading.use_scene_world=True;sp.shading.use_scene_lights=True
                sp.region_3d.view_perspective='CAMERA';sp.region_3d.view_camera_zoom=4
    scene['asset_collection']='TAIPEI_101_EXPORT'
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'taipei-101.blend'))
    summary={'height_m':508,'main_modules':8,'floors_per_module':8,'main_module_range_m':[116,390],'roof_m':448,'spire_m':60,'mesh_count':sum(o.type=='MESH' for o in asset.objects),'materials':len(mats),'faces':sum(len(o.data.polygons) for o in asset.objects if o.type=='MESH')}
    with open(os.path.join(OUT,'build-summary.json'),'w') as f:json.dump(summary,f,indent=2)
    print('TAIPEI_101_COMPLETE',summary)
if __name__=='__main__':build_body();build_site();finish()
