from launch import ROOT,read,sha,save
from pathlib import Path
from datetime import datetime,timezone
from fractions import Fraction
def key(p):return str(Path(p).resolve()).casefold()
a=ROOT/'resume_w11_network_recovery_v1';idx=read(a/'index.json');fr=read(a/'freeze.json');t=read(a/'terminal.json');w=idx['window'];issues=[];schema=[]
for p,s in fr['inputs'].items():
    if sha(p)!=s:issues.append(dict(reason='INHERITED_OR_NEW_INPUT_SHA_DRIFT',path=p))
assert sha(a/'stream.jsonl')==t['stream_sha256']
rows=[__import__('json').loads(s) for s in (a/'stream.jsonl').read_text(encoding='utf-8-sig').splitlines() if s.strip()]
calls=[r['step_update'] for r in rows if r.get('step_update',{}).get('state')=='DONE' and r['step_update'].get('step_type')=='tool']
expected=[('view_file',key(a/'index.json'))]+[('view_file',key(f['path'])) for f in idx['remaining_previews']]+[('write_to_file',key(w['proposal_path']))]
actual=[];written=False;selfreads=0;supply=[]
for c in calls:
    info=c.get('tool_info',{});p=info.get('parameters',{});name=c.get('tool_name');raw=p.get('AbsolutePath') or p.get('TargetFile');path=key(raw) if raw else None
    if c.get('conversation_id')!=idx['conversation_id']:issues.append(dict(reason='WRONG_RESUMED_CONVERSATION_ID',step=c.get('step_index')))
    if any(x in str(info.get('output','')).lower() for x in ('not found','cannot read','error reading','failed to')):issues.append(dict(reason='TOOL_FAILURE',step=c.get('step_index')))
    if name=='view_file' and path==key(w['proposal_path']) and written:
        selfreads+=1
        if selfreads>1:issues.append(dict(reason='SELF_READ_REPEAT'))
    else:actual.append((name,path))
    if name=='write_to_file':
        if written:issues.append(dict(reason='PROPOSAL_OVERWRITE'))
        written=True
    supply.append(dict(step=c.get('step_index'),tool=name,path=path))
if actual!=expected:issues.append(dict(reason='RESUME_SUPPLY_ORDER_OR_WHITELIST',expected=expected,actual=actual))
try:
    d=read(w['proposal_path']);assert set(d)=={'segments','events','student_visibility','limitations'}
    assert isinstance(d['events'],list) and isinstance(d['segments'],list) and d['segments'];cursor=Fraction(0);end=Fraction(w['domain_local_seconds'][1])
    for s in d['segments']:
        assert set(s)=={'decision','start_seconds','end_seconds','reason','fact_support','start_uncertainty_range_seconds','end_uncertainty_range_seconds'}
        assert s['decision'] in ('KEEP','NO','UNKNOWN') and s['reason'] and isinstance(s['fact_support'],list)
        lo=Fraction(str(s['start_seconds']));hi=Fraction(str(s['end_seconds']));assert lo==cursor and lo<hi<=end;cursor=hi
        for k in ('start_uncertainty_range_seconds','end_uncertainty_range_seconds'):
            z=s[k];assert len(z)==2 and 0<=Fraction(str(z[0]))<=Fraction(str(z[1]))<=end
        for f in s['fact_support']:assert set(f)=={'group','slot'} and f['group'] in range(16) and f['slot'] in range(4)
    assert cursor==end
    for e in d['events']:
        assert set(e)=={'description','decision','start_seconds','end_seconds','fact_support','boundary_reason'}
        assert e['decision'] in ('KEEP','NO','UNKNOWN') and e['description'] and e['boundary_reason']
except Exception as e:schema.append(dict(reason='PROPOSAL_SCHEMA_OR_COVERAGE',error=repr(e)))
old=ROOT.parent/'call00';oldidx=read(old/'index.json');oldaudit=read(old/'audit.json');inherited=oldaudit['windows'][0]
# Explicitly retain the old failed terminal. Only lawful completed supply and 64 bound static facts transfer.
assert inherited['bound_rows']==64 and not inherited['schema_issues'] and inherited['clip_read_done']
assert [f['frame_id'] for f in inherited['student_preview_read_done']]==['F00','F09','F18']
assert oldaudit['actual_nonself_tool_calls']==85 and not oldaudit['unfinished_tool_attempts']
assert all(i['reason']=='SUPPLY_ORDER_BARRIER_OR_WHITELIST' for i in oldaudit['tool_issues'])
oldrows=[__import__('json').loads(s) for s in (old/'stream.jsonl').read_text(encoding='utf-8-sig').splitlines() if s.strip()]
oldcalls=[r['step_update'] for r in oldrows if r.get('step_update',{}).get('state')=='DONE' and r['step_update'].get('step_type')=='tool']
oldexpected=[('view_file',key(old/'index.json'))]
for g in oldidx['windows'][0]['groups']:
    oldexpected += [('view_file',key(f['path'])) for f in g['frames']]+[('write_to_file',key(g['output_path']))]
oldexpected += [('view_file',key(w['clip_path']))]+[('view_file',key(f['path'])) for f in w['student_previews'][:3]]
oldactual=[]
for c in oldcalls:
    p=c.get('tool_info',{}).get('parameters',{});raw=p.get('AbsolutePath') or p.get('TargetFile');oldactual.append((c.get('tool_name'),key(raw) if raw else None))
if oldactual!=oldexpected:issues.append(dict(reason='INHERITED_ORIGINAL_SUPPLY_NOT_EXACT_LAWFUL_PREFIX'))
result=next((r.get('result',{}) for r in reversed(rows) if r.get('event')=='result'),{})
accepted=not issues and not schema and t['exit_code']==0 and result.get('status')=='SUCCESS'
out=dict(utc=datetime.now(timezone.utc).isoformat(),status='PASS_EXACT_INHERITED_AND_RESUMED_TOOL_STRUCTURE_PENDING_SEMANTIC_REVIEW' if accepted else 'STOP_RESUME_STRUCTURE_OR_COMPLETION_FAILED_KEEP_RAW',
  window_id=w['window_id'],job_index=3,conversation_id=idx['conversation_id'],inherited_native_pngs=64,new_native_pngs=0,inherited_fact_groups=16,new_fact_groups=0,
  inherited_clip_reads=1,new_clip_reads=0,inherited_student_preview_frames=['F00','F09','F18'],new_student_preview_frames=[f['frame_id'] for f in idx['remaining_previews']] if actual==expected else [],
  actual_student_input_frames=64,teacher_preview_frames_total=8,logical_proposal_count=1,own_output_self_reads=selfreads,tool_issues=issues,schema_issues=schema,
  actual_new_supply=supply,inherited_actual_supply=inherited['actual_supply'],inherited_program_bound_facts=dict(path=str(old/'w03_program_bound_facts.json'),sha256=sha(old/'w03_program_bound_facts.json')),
  native_geometry=[f['geometry'] for g in w['groups'] for f in g['frames']],student_geometry=[f['geometry'] for f in w['student_previews']],
  original_timeout_failure_preserved=True,original_terminal_sha256=sha(old/'terminal.json'),original_raw_sha256=sha(old/'stream.jsonl'),
  new_terminal_sha256=sha(a/'terminal.json'),new_raw_sha256=sha(a/'stream.jsonl'),freeze_sha256=sha(a/'freeze.json'),proposal_sha256=sha(w['proposal_path']) if Path(w['proposal_path']).exists() else None,
  actual_result_status=result.get('status'),actual_result_usage=result.get('usage'),CLI_after=26,cash_cost='UNKNOWN_NOT_ZERO',semantic_correctness='PENDING_ROOT_AND_INDEPENDENT_STUDENT_REVIEW',
  training_admitted=False,human_gold=False,independent_blind_observation=False,new_training=0,new_426=0,automatic_retry=False)
save(a/'audit.json',out);print(__import__('json').dumps(dict(status=out['status'],tool_issues=issues,schema_issues=schema,CLI_after=26),ensure_ascii=False),flush=True)
