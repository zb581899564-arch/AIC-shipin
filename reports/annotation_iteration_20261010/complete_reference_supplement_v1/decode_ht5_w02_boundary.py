"""One actual registered interior observation; no reuse of W01 STOP metadata."""
from pathlib import Path
original=Path(__file__).with_name('decode_w02_boundary.py')
source=original.read_text(encoding='utf-8')
source=source.replace("observations/01_kLxoNp-UchI_W02","observations/04_HT5vyqe0Xaw_W02")
source=source.replace("ROOT.parents[2]/'round6_score_alignment", "ROOT.parents[1]/'round6_score_alignment")
source=source.replace("OUT=ROOT/'boundary_w02_v1'","OUT=ROOT/'boundary_ht5_w02_end_v1'")
source=source.replace("manifest['frames'][15],manifest['frames'][16]","manifest['frames'][39],manifest['frames'][40]")
source=source.replace('New W02 end of lying-face sequence','New HT5 W02 end of short representative frontal truck image')
source=source.replace("main_observations_sha256=sha(ROOT/'01_w02_main_native_observations.json')","main_observations_sha256=sha(ROOT/'04_ht5_w02_main_preteacher_review.json')")
exec(compile(source,str(__file__),'exec'))
