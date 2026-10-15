"""Preserve pre-model engineering failures; new versions change serialization/cache only."""
from pathlib import Path
import json
H=Path(__file__).resolve().parent
def exclusive(name,text):
    with (H/name).open('x',encoding='utf-8') as f:f.write(text)
source=(H/'controller.py').read_text(encoding='utf-8')
assert "'command':args" in source
exclusive('controller_v2.py',source.replace("'command':args","'command':list(map(str,args))"))
deploy=(H/'deploy.py').read_text(encoding='utf-8')
deploy=deploy.replace('controller.py','controller_v2.py').replace('annotation_iteration_20261010_v1','annotation_iteration_20261010_v2')
# Separate launch receipt and retained v1 source files.
deploy=deploy.replace("H/'launch.json'","H/'launch_v2.json'")
exclusive('deploy_v2.py',deploy)
annotation=(H/'agy_short_clips.py').read_text(encoding='utf-8')
assert 'source=inp.streams.video[0];base=source.time_base' in annotation
annotation=annotation.replace('source=inp.streams.video[0];base=source.time_base','source=inp.streams.video[0];rate=source.average_rate;base=source.time_base')
annotation=annotation.replace("Fraction(1,1)/source.average_rate","Fraction(1,1)/rate").replace("H/'agy'","H/'agy_v2'").replace("H/'agy/","H/'agy_v2/")
exclusive('agy_short_clips_v2.py',annotation)
exclusive('engineering_v1_failures.json',json.dumps({'remote_controller':'v1 Path serialization failed before GPU job; no optimizer/model calls',
    'local_annotation':'PyAV source.average_rate unavailable after closing container; first prepared clip retained, agy calls zero',
    'fixes':'String command receipt; cache immutable rate before source close; independent v2 paths','old_files_preserved':True},indent=2))
