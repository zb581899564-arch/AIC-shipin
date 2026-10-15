"""Final tool supply and identity audit; never a semantic acceptance score."""
from pathlib import Path
from fractions import Fraction as F
import json, hashlib, sys
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT.parent/'slot6_silver24_v1'))
from quality_contract import reference
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def key(p): return str(Path(p).resolve()).casefold()
packet=read(ROOT/'teacher_packet.json'); attempt=ROOT/'teacher_attempt01'
terminal=read(attempt/'terminal.json')
rows=[json.loads(s) for s in (attempt/'stream.jsonl').read_text(encoding='utf-8-sig').splitlines() if s.strip()]
calls=[r['step_update'] for r in rows if r.get('step_update',{}).get('state')=='DONE' and r['step_update'].get('step_type')=='tool']
original={key(r['path']):r for r in packet['original_frames']}
effective={key(r['path']):r for r in packet['effective_frames']}
clip=key(packet['clip_path']); metadata=key(ROOT/'teacher_packet.json')
allowed=set(original)|set(effective)|{clip,metadata}; delivered=set(); reads={}; issues=[]
for c in calls:
    info=c.get('tool_info',{}); pars=info.get('parameters',{}); name=c.get('tool_name')
    path=pars.get('AbsolutePath') or pars.get('TargetFile'); path=key(path) if path else None
    output=str(info.get('output',''))
    if name=='view_file':
        reads[path]=reads.get(path,0)+1
        if path not in allowed: issues.append({'tool':name,'path':path,'reason':'OUTSIDE_WHITELIST'})
        elif any(s in output.lower() for s in ('not found','cannot read','failed to','error reading')):
            issues.append({'tool':name,'path':path,'reason':'REPORTED_READ_FAILURE'})
        else: delivered.add(path)
    elif name=='write_to_file':
        if path!=key(attempt/'proposal.json'): issues.append({'tool':name,'path':path,'reason':'UNEXPECTED_WRITE'})
    else: issues.append({'tool':name,'path':path,'reason':'UNEXPECTED_TOOL'})
doc=read(attempt/'proposal.json'); geometry=[]
for k in ('window_id','source_sha256','clip_sha256'):
    if doc.get(k)!=packet[k]: geometry.append('IDENTITY:'+k)
for name,expected in [('frame_observations',packet['original_frames']),('effective_view_observations',packet['effective_frames'])]:
    observed=doc.get(name,[])
    if len(observed)!=len(expected): geometry.append(name+':COUNT')
    for r,f in zip(observed,expected):
        if any(r.get(k)!=f[k] for k in ('frame_id','source_ordinal')): geometry.append(name+':FRAME_IDENTITY')
        if F(r['local_seconds_exact'])!=F(f['local_seconds_exact']): geometry.append(name+':PTS')
        if r.get('observed') is not True: geometry.append(name+':UNOBSERVED')
parts={k:[] for k in ('KEEP','NO','UNKNOWN')}
for c in doc['window_coverage']: parts[c['label']].append((c['start'],c['end']))
try: reference([(0,30)],parts['KEEP'],parts['NO'],parts['UNKNOWN'])
except Exception as e: geometry.append('COVERAGE:'+repr(e))
if doc.get('full_native_frames_observed') is not False or doc.get('training_admitted') is not False:
    geometry.append('UNSUPPORTED_ADMISSION_OR_FULL_NATIVE_CLAIM')
init=next((r.get('init',{}) for r in rows if r.get('event')=='init'),{})
result=next((r.get('result',{}) for r in reversed(rows) if r.get('event')=='result'),{})
out=dict(status='TOOL_SUPPLY_AUDITED_NOT_SEMANTIC_ACCEPTANCE',window_id=packet['window_id'],
 original_pngs_delivered=len(set(original)&delivered),effective_pngs_delivered=len(set(effective)&delivered),
 native_video_delivered=clip in delivered,missing_original=[v['frame_id'] for k,v in original.items() if k not in delivered],
 tool_issues=issues,proposal_geometry_identity_issues=geometry,actual_completed_tool_count=len(calls),read_counts=reads,
 actual_model=init.get('model'),actual_result_status=result.get('status'),actual_result_usage=result.get('usage'),
 proposal_sha256=sha(attempt/'proposal.json'),stream_sha256=sha(attempt/'stream.jsonl'),terminal_sha256=sha(attempt/'terminal.json'),
 native_video_observation_scope=doc.get('native_video_actual_scope'),full_native_frames_observed=False,
 student_actual_frames=64,teacher_effective_preview_only=8,teacher_claim_student_has_only8_frames_is_incorrect=True,
 training_admitted=False,new_optimizer_updates=0,cash_cost='UNKNOWN_NOT_ZERO')
with (attempt/'audit.json').open('x',encoding='utf-8') as f: json.dump(out,f,ensure_ascii=False,indent=2)
print(json.dumps({k:v for k,v in out.items() if k!='read_counts'},ensure_ascii=False))
