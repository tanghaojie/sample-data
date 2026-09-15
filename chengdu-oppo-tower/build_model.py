"""Run in Blender through Blender MCP. Photo-based simplified OPPO tower."""
import bpy, math, random, json
from mathutils import Vector, Quaternion
from pathlib import Path

OUT = Path('C:/Users/JackieTang/Desktop/sample-data/chengdu-oppo-tower')
scene = bpy.data.scenes.new('Chengdu OPPO Tower')
bpy.context.window.scene = scene
scene.unit_settings.scale_length = 1.0
random.seed(42)
mats = []
def material(name, color, metal, rough, emission=None, strength=0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    n = next(n for n in m.node_tree.nodes if n.bl_idname == 'ShaderNodeBsdfPrincipled')
    n.inputs['Base Color'].default_value = (*color, 1)
    n.inputs['Metallic'].default_value = metal
    n.inputs['Roughness'].default_value = rough
    if emission:
        n.inputs['Emission Color'].default_value = (*emission, 1)
        n.inputs['Emission Strength'].default_value = strength
    m.diffuse_color = (*color, 1)
    mats.append(m)
    return len(mats)-1
glass = [material('Glass blue grey %02d'%i, (0.105+i*.016, .17+i*.019, .22+i*.022), .42, .25) for i in range(5)]
silver = material('Silver vertical fins', (.51,.57,.61), .72,.29)
dark = material('Recess and floor joints', (.033,.052,.067), .25,.4)
spandrel = material('Silver grey spandrel panels', (.3,.37,.41), .46,.32)
warm = material('Office windows NIGHT', (.22,.27,.29), .25,.3, (1,.61,.27), 2.8)
logo = material('OPPO white sign NIGHT', (.88,.90,.88), .12,.28, (1,.88,.66), 2.0)
base = material('Stone plinth', (.30,.32,.33), .08,.65)
verts, faces, indices = [], [], []
def box(x,y,z,w,d,h,mi):
    k=len(verts)
    verts.extend([(x+sx*w/2,y+sy*d/2,z+sz*h/2) for sx,sy,sz in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]])
    faces.extend([tuple(k+i for i in f) for f in [(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]])
    indices.extend([mi]*6)
def pane(cx,cy,z,w,h,axis,mi,sign=1):
    k=len(verts)
    if axis==0:
        verts.extend([(cx-w/2,cy,z-h/2),(cx+w/2,cy,z-h/2),(cx+w/2,cy,z+h/2),(cx-w/2,cy,z+h/2)])
        order=(0,1,2,3) if sign<0 else (3,2,1,0)
    else:
        verts.extend([(cx,cy-w/2,z-h/2),(cx,cy+w/2,z-h/2),(cx,cy+w/2,z+h/2),(cx,cy-w/2,z+h/2)])
        order=(0,1,2,3) if sign>0 else (3,2,1,0)
    faces.append(tuple(k+i for i in order)); indices.append(mi)

# Narrow blades around an offset core: elevations inferred from supplied photos.
blades=[(-28,1,6,28,114),(-21,0,8,35,164),(-11,0,12,36,206),(-3,2,4,31,191),(5,-1,12,34,196),(14,2,6,37,201),(21,0,8,30,146)]
box(-1,0,.4,65,42,.8,base)
box(-1,0,3.2,56,32,5.6,dark)
for bi,(cx,cy,w,d,h) in enumerate(blades):
    box(cx,cy,(h+.8)/2,w,d,h-.8,glass[bi%5])
    # Each facade uses actual PBR panels; no baked lighting or external textures.
    for axis,span,center,normalcenter in [(0,w,cx,cy),(1,d,cy,cx)]:
        ncols=max(2,round(span/1.45)); step=span/ncols
        for sign in [-1,1]:
            normal=normalcenter+sign*((d if axis==0 else w)/2+.055)
            for j in range(ncols):
                along=center-span/2+(j+.5)*step
                for fl in range(1,int((h-2)/4.6)):
                    z=fl*4.6+2.0
                    if z+1.8>h: continue
                    r=random.random()
                    mi=warm if (fl>5 and r<.17) else (spandrel if r<.34 else glass[random.randrange(5)])
                    px,py=(along,normal) if axis==0 else (normal,along)
                    pane(px,py,z,step-.11,3.75,axis,mi,sign)
            for j in range(ncols+1):
                along=center-span/2+j*step
                px,py=(along,normal+sign*.07) if axis==0 else (normal+sign*.07,along)
                if axis==0: box(px,py,h/2,.10,.19,h,silver)
                else: box(px,py,h/2,.19,.10,h,silver)
            for fl in range(1,int(h/4.6)+1):
                z=fl*4.6
                if z>h: continue
                px,py=(center,normal) if axis==0 else (normal,center)
                pane(px,py,z,span,.115,axis,dark,sign)
    box(cx,cy,h-.2,w-.25,d-.25,.4,silver)
    # Crisp metal corners strengthen the characteristic narrow vertical blades.
    for xx in [cx-w/2,cx+w/2]:
        for yy in [cy-d/2,cy+d/2]: box(xx,yy,h/2,.23,.23,h,silver)

mesh=bpy.data.meshes.new('Tower joined facade mesh')
mesh.from_pydata(verts,[],faces); mesh.materials.clear()
for m in mats: mesh.materials.append(m)
for p,mi in zip(mesh.polygons,indices): p.material_index=mi
mesh.update()
tower=bpy.data.objects.new('Chengdu_OPPO_Tower',mesh); scene.collection.objects.link(tower)
tower['longitude']=104.07807; tower['latitude']=30.51732
tower['crs']='EPSG:4326'; tower['height']=0.0
tower['height_note']='0 m for ellipsoid-only Geo scene; survey ground height unknown'
tower['building_height_m']=206.0

# Thin outlined lowercase logo, built as geometry for portable glTF export.
def stroke(name,points,sign):
    c=bpy.data.curves.new(name,'CURVE'); c.dimensions='3D'; c.bevel_depth=.14; c.bevel_resolution=2
    s=c.splines.new('POLY'); s.points.add(len(points)-1)
    for p,co in zip(s.points,points): p.co=(*co,1)
    ob=bpy.data.objects.new(name,c); scene.collection.objects.link(ob); ob.data.materials.append(mats[logo])
    bpy.context.view_layer.objects.active=ob; ob.select_set(True)
    bpy.ops.object.convert(target='MESH'); ob.select_set(False)
for side in [-1,1]:
    # On both broad faces of the tallest slab, small enough to stay within its width.
    for j,letter in enumerate('oppo'):
        x=-15.25+j*2.85; y=side*18.29; z=198
        points=[(x+1.17*math.cos(t*math.tau/40),y,z+.78*math.sin(t*math.tau/40)) for t in range(41)]
        stroke('OPPO ring '+str(side)+' '+str(j),points,side)
        if letter=='p': stroke('OPPO stem '+str(side)+' '+str(j),[(x+side*1.17,y,z+.6),(x+side*1.17,y,z-1.8)],side)

for ob in scene.objects:
    ob.rotation_euler.z = math.pi/2
    ob.select_set(True)
bpy.context.view_layer.objects.active=tower
# Standard exporter uses glTF Y-up; Cesium restores the local Z-up model frame.
bpy.ops.export_scene.gltf(filepath=str(OUT/'chengdu-oppo-tower.glb'), use_selection=True, export_yup=True, export_extras=True, export_cameras=False, export_lights=False)
for ob in scene.objects: ob.select_set(False)
tower.select_set(True)
for area in bpy.context.screen.areas:
    if area.type=='VIEW_3D':
        area.spaces.active.region_3d.view_distance=470
        area.spaces.active.region_3d.view_location=Vector((0,0,103))
        area.spaces.active.region_3d.view_rotation=(Vector((300,-490,240))-Vector((0,0,103))).to_track_quat('Z','Y')
        area.spaces.active.clip_end=5000
        area.spaces.active.shading.color_type='MATERIAL'
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'chengdu-oppo-tower.blend'))
print(json.dumps({'objects':len(scene.objects),'vertices':len(verts),'triangles':len(faces)*2,'height_m':206,'glb_bytes':(OUT/'chengdu-oppo-tower.glb').stat().st_size}))
