"""First read-only error diagnosis of an already rejected/exposed confirmation.

No model, tensor, media, processor, quality re-evaluation or rule application.
Exports only a small byte-bound diagnostic receipt; all raw stays on Linux.
"""
import base64,json,hashlib,subprocess
from pathlib import Path

REMOTE=r'''
import base64,datetime,hashlib,json,os,pathlib,socket,subprocess
from bisect import bisect_left
from fractions import Fraction as F
root=pathlib.Path('/home/inspur/aic_video_work/recall_consensus_verify40_46_20261015_v1')
assert socket.gethostname()=='inspur-NP5570M5'
def read(p):return json.loads(pathlib.Path(p).read_text())
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def ref(p):return dict(path=str(p),sha256=sha(p))
def frames(spans,pts):
 result=set()
 for a,b in spans:
  a,b=F(a),F(b);assert 0<=a<b
  result.update(range(bisect_left(pts,a),bisect_left(pts,b)))
 return result
chain_path=root/'confirm/chain_02/completion.json';chain=read(chain_path)
result_path=root/'confirm/comparison_01/result.json';result=read(result_path)
assert chain['status']==result['status']=='STOP_CONSENSUS_FRESH_CONFIRM_REJECTED'
assert chain['comparison_ref']==ref(result_path) and sha(result_path)=='0b687aff7bee1409391df7c4bfaf924eb97800cfa2eac1ee387fdaaab7fbb0ec'
assert result['conditions']['macro_precision_not_lower'] is False and len(result['cases'])==4
cpu_path=root/'cpu_acceptance_confirm_v2.json';cpu=read(cpu_path)
inputs={}
for row in cpu['entries']:
 assert sha(row['input_path'])==row['input_sha256'];inputs[row['case_id']]=read(row['input_path'])
assert len(inputs)==32
export_path=root/'confirm/VERIFY/verification_export.json';export=read(export_path)
assert export['status']=='PASS_RECALL_VERIFY_EXECUTION_AND_REPLAY_NOT_QUALITY' and len(export['events'])==44
for stage in ['B0','VERIFY']:
 qpath=root/'confirm'/stage/'replay_01/completion.json';q=read(qpath)
 assert q['status']=='PASS_ALL_RECALL_'+stage+'_INDEPENDENT_REPLAYS_NOT_QUALITY'
 assert chain[stage]['first_QA_completion_ref']==ref(qpath) and q['calls']==len(q['proofs'])==(32 if stage=='B0' else 44)
pointer=read(root/'reference_completion_confirm.json');assert sha(pointer['path'])==pointer['sha256']
sources={s['video_id']:s for s in read(pointer['path'])['accepted']}
cases=[]
for case in result['cases']:
 vid=case['video_id'];source=sources[vid];clock=read(source['clock_path']);pts=list(map(F,clock['original_exact_pts']))
 assert sha(source['clock_path'])==source['clock_sha256'] and sha(source['reference_path'])==source['reference_sha256']
 assert all(meta['source_sha256']==source['media']['sha256'] for meta in inputs.values() if meta['source_name']==vid)
 assert pts[0]==0
 before=frames(case['baseline_spans'],pts);after=frames(case['augmented_spans'],pts);added=sorted(after-before)
 assert before<=after and len(added)==case['added_native_frames']
 support={key:set() for key in ['KEEP','UNKNOWN','DROP']};long_events={key:[] for key in support}
 for event in export['events']:
  if event['source_name']!=vid:continue
  meta=inputs[event['original_case_id']]
  if 'baseline' not in meta.get('view_roles',[meta['window_role']]):continue
  decision=event['decision_result'];assert decision['successful_model_call_required'] is True
  label=decision['decision'];assert label in support
  interval=event['original_interval_exact'];support[label]|=frames([interval],pts)
  long_events[label].append(dict(event_id=event['event_id'],original_interval_exact=interval,window_start=meta['window_start'],window_end=meta['window_end']))
 reference=read(source['reference_path']);reviewers=reference['annotator_intervals_exact_seconds']
 assert len(reviewers)==reference['annotator_count']>=2
 reviewers=[frames(spans,pts) for spans in reviewers]
 hist={str(i):0 for i in range(len(reviewers)+1)};dropped_hist=hist.copy();details=[]
 for i in added:
  votes=sum(i in selected for selected in reviewers);hist[str(votes)]+=1
  if i in support['DROP']:dropped_hist[str(votes)]+=1
  details.append(dict(native_ordinal=i,exact_PTS=str(pts[i]),human_summary_selected_reviewers=votes,total_reviewers=len(reviewers),
                      prior_baseline_context_explicit_DROP=i in support['DROP'],prior_baseline_context_UNKNOWN=i in support['UNKNOWN'],
                      prior_baseline_context_KEEP=i in support['KEEP']))
 cases.append(dict(video_id=vid,added_native_frames=len(added),annotator_count=len(reviewers),
   baseline_context_explicit_DROP_event_count=len(long_events['DROP']),
   added_frames_with_baseline_context_DROP=sum(i in support['DROP'] for i in added),
   added_frames_with_baseline_context_UNKNOWN=sum(i in support['UNKNOWN'] for i in added),
   added_frames_with_baseline_context_KEEP=sum(i in support['KEEP'] for i in added),
   added_frames_human_summary_reviewer_vote_histogram=hist,baseline_DROP_added_frames_reviewer_vote_histogram=dropped_hist,
   baseline_context_DROP_events=long_events['DROP'],added_frame_diagnostics=details,
   source_ref=dict(path=source['media']['path'],sha256=source['media']['sha256']),clock_ref=ref(source['clock_path']),reference_ref=ref(source['reference_path'])))
value=dict(schema='REJECTED_CONSENSUS_ADDITION_BASELINE_CONFLICT_DIAGNOSIS_V1',utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
 status='DESCRIPTIVE_EXPOSED_CONFIRMATION_ERROR_DIAGNOSIS_NOT_NEW_CANDIDATE_OR_QUALITY_PASS',
 result_ref=ref(result_path),chain_completion_ref=ref(chain_path),CPU_acceptance_ref=ref(cpu_path),verification_export_ref=ref(export_path),
 cases=cases,total_added_native_frames=sum(c['added_native_frames'] for c in cases),
 added_frames_with_baseline_context_DROP=sum(c['added_frames_with_baseline_context_DROP'] for c in cases),
 source_metrics_already_exposed=True,fresh_confirm_sources_cannot_be_reused_as_unseen=True,
 human_summary_not_selected_is_not_ORDINARY=True,baseline_context_DROP_is_model_evidence_not_human_gold=True,
 original_failed_gates_or_decisions_changed=False,new_candidate_evaluated=False,new_threshold_selected=False,
 model_calls=0,media_body_reads=0,tensor_loads=0,media_decodes=0,vision_processor_calls=0,first_QA_repeated=0,production_admitted=False)
out=root/'error_diagnosis_01';out.mkdir(exist_ok=False)
with (out/'result.json').open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.flush();os.fsync(f.fileno())
payload=(json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode()
print(json.dumps(dict(bytes=len(payload),sha256=hashlib.sha256(payload).hexdigest(),base64=base64.b64encode(payload).decode())))
'''

def main():
    output=Path(__file__).with_name('rejected_additions_diagnosis_25.json')
    assert not output.exists(),'Do not overwrite/repeat successful diagnosis'
    command='python3 -c "import base64;exec(base64.b64decode(\''+base64.b64encode(REMOTE.encode()).decode()+'\'))"'
    p=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=12','aic-inspur-home',command],capture_output=True,text=True,timeout=45)
    if p.returncode:raise RuntimeError(p.stderr)
    packet=json.loads(p.stdout);data=base64.b64decode(packet['base64'],validate=True)
    assert len(data)==packet['bytes'] and hashlib.sha256(data).hexdigest()==packet['sha256']
    with output.open('xb') as f:f.write(data)
    d=json.loads(data)
    print(json.dumps(dict(status=d['status'],total_added_native_frames=d['total_added_native_frames'],added_frames_with_baseline_context_DROP=d['added_frames_with_baseline_context_DROP'],
       cases=[{k:c[k] for k in ['video_id','added_native_frames','added_frames_with_baseline_context_DROP','added_frames_with_baseline_context_UNKNOWN','added_frames_with_baseline_context_KEEP']} for c in d['cases']],
       receipt_bytes=len(data),receipt_sha256=packet['sha256']),ensure_ascii=False))

if __name__=='__main__':main()
