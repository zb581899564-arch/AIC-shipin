"""First equal-count B/MAP selected-state identifiability audit, metadata only."""
import hashlib,json,sys,time
from fractions import Fraction
from pathlib import Path

def ref(p):
 p=Path(p).resolve(strict=True);b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())

def main():
 n=Path(__file__).resolve().parent;w=n.parent.parent;started=time.monotonic()
 reg=json.loads((n/'registration38.json').read_text());assert reg['code_ref']==ref(__file__)
 def read(rr):
  p=Path(rr['path']).resolve(strict=True);assert p.is_relative_to(w)and ref(p)==rr
  return json.loads(p.read_text())
 protocol=read(reg['protocol_ref']);complete=read(reg['completion32_ref']);done33=read(reg['completion33_ref'])
 assert done33['status']=='COMPLETE_FULL_PROGRAM_COUPLING_NOVELTY_DIAGNOSTIC_ONLY'
 rr=Path(reg['completion32_ref']['path']).parent
 assert ref(rr/'acceptable_program32_math.py')==reg['math_ref']
 sys.path.insert(0,str(rr));from acceptable_program32_math import exact_utility
 # Different context quality at exactly the same context count can matter.
 lo=exact_utility(8,[2],[5])-exact_utility(5,[1],[5])
 hi=exact_utility(8,[5],[5])-exact_utility(5,[4],[5])
 assert lo==Fraction(7,65)and hi==Fraction(-2,65)
 rows=[]
 for reference in complete['outputs']:
  inferred=read(reference)
  if inferred['arm']!='real':continue
  target=read(inferred['target_ref']);wins=target['windows'];M=inferred['MAP']['choices'];B=target['baseline_program'];G=inferred['highest_score_acceptable']['choices']
  sets=[]
  for win in wins:
   groups=[]
   for g in win['groups']:
    first=None
    for v in g['variants']:
     if v['kind']=='OLD_ACCEPTED_SUFFIX':a=read(v['window_ref'])['slots'][v['slot']]['selected_ordinals']
     else:
      assert v['kind']=='NEW_EXACT_BASELINE_NOOP'
      a=next(q for q in read(v['source_noop_ref'])['windows']if q['uid']==win['uid'])['selected_ordinals']
     ss=set(a);assert len(ss)==g['native_count']
     if first is None:first=ss
     assert ss==first
    groups.append(first)
   sets.append(groups)
  def state(program,skip):
   chosen=set();tp=[0]*len(target['gt']);count=0
   for i,j in enumerate(program):
    if i==skip:continue
    assert not(chosen&sets[i][j]);chosen|=sets[i][j]
    group=wins[i]['groups'][j];count+=group['native_count'];tp=[a+b for a,b in zip(tp,group['TP'])]
   assert count==len(chosen);return chosen,tp
  pairs=[]
  for i,(mi,gi)in enumerate(zip(M,G)):
   if mi==gi:continue
   win=wins[i];ma=win['groups'][mi];gold=win['groups'][gi]
   req=read(win['request_ref']);overview=[v for v in req['plan']['videos']if v['role']=='Overview'];assert len(overview)==1
   obs=overview[0];assert obs['owner']['source_id']==target['sid']and obs['owner']['source_sha256']==target['source_sha256']
   samples=obs['native_ordinals'];assert len(samples)==64
   contexts={};members={}
   for label,program in [('B',B),('MAP',M)]:
    ss,tp=state(program,i);members[label]=ss
    delta=exact_utility(len(ss)+gold['native_count'],[a+b for a,b in zip(tp,gold['TP'])],target['gt'])-exact_utility(len(ss)+ma['native_count'],[a+b for a,b in zip(tp,ma['TP'])],target['gt'])
    contexts[label]=dict(count=len(ss),TP=tp,delta_fraction=str(delta),sign=(delta>0)-(delta<0),overview_selected_marks=[int(k in ss)for k in samples])
   equal=contexts['B']['count']==contexts['MAP']['count'];different=members['B']!=members['MAP']
   reversal=contexts['B']['sign']*contexts['MAP']['sign']<0
   visible=contexts['B']['overview_selected_marks']!=contexts['MAP']['overview_selected_marks']
   if equal and ma['native_count']==gold['native_count']:
    assert contexts['B']['delta_fraction']==contexts['MAP']['delta_fraction'],'Equal-current-count F1 context TP must cancel at equal outside count'
   pairs.append(dict(uid=win['uid'],MAP_group=mi,gold_group=gi,current_counts=dict(MAP=ma['native_count'],gold=gold['native_count']),contexts=contexts,
       equal_outside_count=equal,different_outside_members=different,strict_reversal=reversal,overview_marks_distinguish=visible,
       necessary_visible_example=bool(equal and different and reversal and visible),unidentifiable_example=bool(equal and different and reversal and not visible)))
  rows.append(dict(sid=target['sid'],role=target['cohort'],pairs=pairs))
 assert len(rows)==7 and sum(len(r['pairs'])for r in rows)==34
 summary={role:dict(pairs=sum(len(r['pairs'])for r in rows if r['role']==role),
     equal_count_distinct_pairs=sum(p['equal_outside_count']and p['different_outside_members']for r in rows if r['role']==role for p in r['pairs']),
     equal_count_strict_reversals=sum(p['equal_outside_count']and p['different_outside_members']and p['strict_reversal']for r in rows if r['role']==role for p in r['pairs']),
     visible_necessary_sources=sum(any(p['necessary_visible_example']for p in r['pairs'])for r in rows if r['role']==role),
     unidentifiable_examples=sum(p['unidentifiable_example']for r in rows if r['role']==role for p in r['pairs']))for role in ['fit','process']}
 if all(v['visible_necessary_sources']>=1 for v in summary.values()):status='NECESSARY_STATE_INFORMATION_EXAMPLES_EXIST_SEPARATE_REVIEW_ONLY'
 elif not any(v['equal_count_distinct_pairs']for v in summary.values()):status='UNKNOWN_NO_MATCHED_EQUAL_COUNT_DISTINCT_B_MAP_CONTEXT_STOP_MODEL_ADMISSION'
 elif any(v['unidentifiable_examples']for v in summary.values()):status='STOP_UNIDENTIFIABLE_OVERVIEW_SELECTED_MARK_STATE'
 else:status='STOP_NO_SUPPORTED_CONTENT_STATE_REVERSAL_IN_FIXED_CONTEXTS'
 out=dict(status=status,summary=summary,rows=rows,analytic_fixture='PASS_EQUAL_OUTSIDE_P4_TP0_vs3_DELTA7over65_vs_minus2over65',
     scope='Only original accepted B/MAP outside states, same34 pairs. gold supplies target/action comparison only, never outside context; no oracle state proposed as deployment input. Absence of a matched natural state is UNKNOWN, not proof all state-conditioning useless.',
     completion32_ref=reg['completion32_ref'],completion33_ref=reg['completion33_ref'],seconds=time.monotonic()-started,new_model_calls=0,new_updates=0,new_decode=0,new_tokenization=0,automatic_GPU=False,production_admitted=False,new_ZIP=0,official_submissions=0)
 assert out['seconds']<protocol['maximum_CPU_seconds']
 with(n/'completion38.json').open('x')as f:json.dump(out,f,indent=2,allow_nan=False)
 print(json.dumps(dict(completion_ref=ref(n/'completion38.json'),receipt={k:v for k,v in out.items()if k!='rows'})))

if __name__=='__main__':main()
