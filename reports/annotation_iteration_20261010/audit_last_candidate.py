"""Inspect teacher claimed observation instants; never shifts or repairs labels."""
import json
from pathlib import Path
from fractions import Fraction
import av
H=Path(__file__).resolve().parent;F=H/'agy_v2/91IHQYk1IQM_01'
m=json.loads((F/'manifest.json').read_text(encoding='utf-8'));wanted={}
for t in (28,29):
    frame=next(x for x in m['source_mapping'] if Fraction(x['local_seconds_exact'])>=t)
    wanted[frame['ordinal']]=t
source=H.parent/'qwen8b_annotation_20261009_v1/input/91IHQYk1IQM/91IHQYk1IQM.mp4'
proof=[]
with av.open(str(source)) as container:
    for ordinal,frame in enumerate(container.decode(video=0)):
        if ordinal in wanted:
            name=f'audit_observation_{wanted[ordinal]}s.png';p=F/name;assert not p.exists()
            frame.to_image().save(p)
            proof.append({'instant':wanted[ordinal],'native_ordinal':ordinal,'source_pts':frame.pts,'file':name})
        if ordinal>=max(wanted):break
assert len(proof)==2
with (F/'observation_audit.json').open('x') as f:json.dump(proof,f,indent=2)
print(json.dumps(proof))
