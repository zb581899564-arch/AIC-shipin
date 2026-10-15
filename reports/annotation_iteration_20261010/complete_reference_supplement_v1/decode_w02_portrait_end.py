"""New one-image request for a separate observed 0.5005s portrait trimming gap."""
from pathlib import Path
HERE=Path(__file__).resolve().parent
old=HERE/'decode_w02_boundary.py'
text=old.read_text(encoding='utf-8')
text=text.replace("RUN=ROOT.parents[2]/'round6_score_alignment/","RUN=ROOT.parents[1]/'round6_score_alignment/",1)
text=text.replace("OUT=ROOT/'boundary_w02_v1'","OUT=ROOT/'boundary_w02_portrait_end_v1'",1)
text=text.replace("manifest['frames'][15],manifest['frames'][16]","manifest['frames'][43],manifest['frames'][44]",1)
text=text.replace('New W02 end of lying-face sequence','New W02 end of established side portrait before repeated hold',1)
exec(compile(text,str(old),'exec'),{'__file__':str(old),'__name__':'__main__'})
