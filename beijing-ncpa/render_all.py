"""One CPU render process; each view reopens the canonical source scene."""
import bpy,sys,runpy
from pathlib import Path
root=Path(__file__).resolve().parent
for view in ['day','night','sunset','aerial','detail','entrance','elevation']:
    bpy.ops.wm.open_mainfile(filepath=str(root/'beijing-ncpa.blend'))
    sys.argv=['render_preview.py','--',view]
    runpy.run_path(str(root/'render_preview.py'),run_name='__main__')
