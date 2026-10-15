"""Path repair only; preserve the prior registration and failed output directory."""
from pathlib import Path
import hashlib,json
HERE=Path(__file__).resolve().parent
old=HERE/'decode_w02_boundary.py'
text=old.read_text(encoding='utf-8')
assert "RUN=ROOT.parents[2]/'round6_score_alignment/" in text
text=text.replace("RUN=ROOT.parents[2]/'round6_score_alignment/","RUN=ROOT.parents[1]/'round6_score_alignment/",1)
text=text.replace("OUT=ROOT/'boundary_w02_v1'","OUT=ROOT/'boundary_w02_v2'",1)
assert not (HERE/'boundary_w02_v1/receipt.json').exists()
original=json.loads((HERE/'boundary_w02_v1/registration.json').read_text(encoding='utf-8'))
assert original['interior_registered']['source_ordinal']==2019
exec(compile(text,str(old),'exec'),{'__file__':str(old),'__name__':'__main__'})
