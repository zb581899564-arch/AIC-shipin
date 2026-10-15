"""Preserve original serializer; add only explicit historical NO wording correction."""
from pathlib import Path
import hashlib,ast
R=Path(__file__).resolve().parent;p=R/'finalize_eval_window_v2.py';raw=p.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='e82752c7e79b22f21c273b49558adb1d330a6efdcbb3780264db32e4ada702ad'
source=raw.decode('utf-8')
old="all_NO_sample_ranges=[v for v in pre['complete_domain_editorial_decision_by_samples'] if v['decision']=='NO']"
assert source.count(old)==1
helper='''def corrected_no_notes(pre,d):
 rows=[dict(v) for v in pre['complete_domain_editorial_decision_by_samples'] if v['decision']=='NO']
 for correction in d.get('historical_NO_reason_corrections',[]):
  matches=[v for v in rows if (v['first'],v['last'])==(correction['first'],correction['last'])]
  assert len(matches)==1
  v=matches[0];assert v['reason']==correction['original_reason']
  v['original_preteacher_reason_preserved']=v['reason'];v['reason']=correction['corrected_reason']
  v['reason_correction_only_no_target_or_range_change']=True
 return rows

'''
source=source.replace('def main():',helper+'def main():',1).replace(old,'all_NO_sample_ranges=corrected_no_notes(pre,d)')
source="# Original serializer SHA e82752c7e79b22f21c273b49558adb1d330a6efdcbb3780264db32e4ada702ad; only explicit NO note correction.\n"+source
ast.parse(source)
out=R/'finalize_eval_window_NO_note_v3.py'
with out.open('x',encoding='utf-8',newline='') as f:f.write(source)
print(hashlib.sha256(out.read_bytes()).hexdigest())
