"""Manual quality variants, retaining the same GEO_ROOT/scale/orientation."""
import bpy,sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from finalize_glb import finalize
records=[]
for quality in ['balanced','compatible']:
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'beijing-ncpa.blend'))
    bpy.ops.object.select_all(action='DESELECT')
    remove=[]
    for c in bpy.data.collections:
        if c.name.startswith('90'):continue
        for ob in c.objects:
            if ob.type=='EMPTY':ob.select_set(True);continue
            if ob.type!='MESH':continue
            name=ob.name
            if 'fasteners' in name or (quality=='compatible' and any(s in name for s in ['Titanium panels tone','truss diagonals','structural inner ribs','inner cross members','delicate vertical bronze mesh','Promenade concentric paving joints','Promenade radial paving joints'])):
                remove.append(ob);continue
            if quality=='compatible' and name=='Shell joint backing':
                ob.data.materials.clear();ob.data.materials.append(bpy.data.materials['Titanium | brushed silver 3'])
            factor=1
            if 'canopies' in name:factor=.40 if quality=='balanced' else .10
            elif any(s in name for s in ['mullions','structural','ribs','rail','gallery light','branches','columns','fascia']):factor=.6 if quality=='balanced' else .28
            if factor<1:
                mod=ob.modifiers.new('Quality reduction','DECIMATE');mod.ratio=factor
                bpy.context.view_layer.objects.active=ob
                bpy.ops.object.modifier_apply(modifier=mod.name)
            ob.select_set(True)
    for ob in remove:bpy.data.objects.remove(ob,do_unlink=True)
    file=ROOT/f'beijing-ncpa-{quality}.glb'
    bpy.ops.export_scene.gltf(filepath=str(file),export_format='GLB',use_selection=True,export_yup=True,export_apply=True,export_texcoords=True,export_normals=True,export_tangents=True,export_materials='EXPORT',export_cameras=False,export_lights=False,export_extras=True,export_image_format='AUTO')
    finalize(file)
    records.append({'quality':quality,'file':file.name,'notes':'Reduced trees and small structural members' if quality=='balanced' else 'Continuous titanium envelope, fewer interior ribs, reduced landscape; same primary silhouette and night channels'})
(ROOT/'quality-variants.json').write_text(json.dumps(records,indent=2)+'\n',encoding='utf-8')
