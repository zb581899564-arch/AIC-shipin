"""Immutable media scope receipts and separate honest whole-session audit."""
from common import ROOT,BASE,read,sha,key,save
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,re,struct,sys,time
import engine
def parsed(raw):
 out=[]
 for line in raw.splitlines():
  try:out.append(json.loads(line))
  except Exception:break
 return out
def pathinfo(t):
 p=t.get('tool_info',{}).get('parameters',{})
 return t.get('tool_name'),key(p.get('AbsolutePath') or p.get('TargetFile'))
def verify_png_pixels(w):
 import numpy as np
 from PIL import Image
 checks=[]
 for kind,frames in [('native',[f for g in w['groups'] for f in g['frames']]),('effective',w['student_previews'])]:
  for f in frames:
   p=Path(f['path']);b=p.read_bytes();assert sha(p)==f['png_sha256']
   assert list(struct.unpack('>II',b[16:24]))==f['geometry']
   with Image.open(p) as im:arr=np.asarray(im.convert('RGB'))
   rgb=hashlib.sha256(arr.tobytes()).hexdigest();assert rgb==f['rgb_pixel_sha256'],(kind,f['frame_id'],'RGB_MISMATCH')
   checks.append(dict(kind=kind,frame_id=f['frame_id'],alias_path=f['path'],original_path=f['original_path'],png_sha256=f['png_sha256'],rgb_pixel_sha256=rgb,geometry=f['geometry']))
 return checks
def seal_scope(number,job):
 a=ROOT/f'call{number}';target=a/f'w{job:02d}_completed_scope_audit.json'
 if target.exists():return read(target)
 lock=a/f'w{job:02d}_scope_seal.lock'
 try:
  with lock.open('x',encoding='utf-8') as f:f.write(str(__import__('os').getpid()))
 except FileExistsError:
  for _ in range(60):
   if target.exists():return read(target)
   time.sleep(1)
  raise RuntimeError('INCOMPLETE_EXISTING_SCOPE_SEAL_NO_REWRITE')
 return _seal_scope(number,job)

def _seal_scope(number,job):
 a=ROOT/f'call{number}';idx=read(a/'index.json');w=next(w for w in idx['windows'] if w['job_index']==job)
 raw=(a/'stream.jsonl').read_bytes();position=0;cut=None
 for line in raw.splitlines(keepends=True):
  position+=len(line)
  try:r=json.loads(line)
  except Exception:break
  t=r.get('step_update',{})
  if t.get('state')=='DONE' and pathinfo(t)==('write_to_file',key(w['proposal_path'])):cut=position;break
 assert cut is not None
 prefix=a/f'w{job:02d}_completed_scope_stream_prefix.jsonl'
 with prefix.open('xb') as f:f.write(raw[:cut])
 evidence=engine.inspect(a,raw[:cut],job);current=evidence['windows'][-1];extra=[];pixels=[]
 success_outputs={key(g['output_path']) for g in w['groups']}|{key(w['proposal_path'])}
 for r in parsed(raw[cut:]):
  t=r.get('step_update',{})
  if t.get('step_type')=='tool' and pathinfo(t)[0]=='write_to_file' and pathinfo(t)[1] in success_outputs:extra.append(dict(reason='OUTPUT_WRITE_AFTER_PREFIX_BEFORE_SEAL',step=t['step_index'],path=pathinfo(t)[1]))
 try:pixels=verify_png_pixels(w)
 except Exception as e:extra.append(dict(reason='ACTUAL_PNG_PIXEL_OR_GEOMETRY',error=repr(e)))
 immutable=[];folder=a/f'w{job:02d}_sealed_actual_outputs';folder.mkdir()
 outputs=[g['output_path'] for g in w['groups']]+[w['proposal_path']]
 outputs=[p['ack_path'] for p in idx['text_fragments'] if p['job_index']==job or (p['job_index'] is None and job==idx['windows'][0]['job_index'])]+outputs
 for p in outputs:
  original=Path(p)
  if not original.exists():extra.append(dict(reason='MISSING_ACTUAL_OUTPUT',path=p));continue
  frozen=folder/original.name
  with frozen.open('xb') as f:f.write(original.read_bytes())
  immutable.append(dict(original_path=p,sha256=sha(original),sealed_copy_path=str(frozen),sealed_copy_sha256=sha(frozen)))
 # Re-read actualstream after CPU/output copying, so an overwrite that raced the
 # observer is not labelled a lawful first-proposal scope. Never rewrite prefix.
 after_snapshot=(a/'stream.jsonl').read_bytes()
 if after_snapshot[:cut]!=raw[:cut]:extra.append(dict(reason='RAW_PREFIX_CHANGED_DURING_SEAL'))
 for r in parsed(after_snapshot[cut:]):
  t=r.get('step_update',{})
  if t.get('step_type')=='tool' and pathinfo(t)[0]=='write_to_file' and pathinfo(t)[1] in success_outputs:extra.append(dict(reason='OUTPUT_WRITE_AFTER_PREFIX_DURING_SEAL',step=t['step_index'],path=pathinfo(t)[1]))
 for o in immutable:
  if not Path(o['original_path']).exists() or sha(o['original_path'])!=o['sha256']:extra.append(dict(reason='OUTPUT_BYTE_CHANGED_DURING_SEAL',path=o['original_path']))
 if any(r.get('event')=='result' for r in parsed(raw[:cut])):extra.append(dict(reason='TERMINAL_RESULT_BEFORE_SCOPE_COMPLETION'))
 good=not evidence['tool_issues'] and not evidence['errored_tool_attempts'] and not evidence['unfinished_tool_attempts'] and not evidence['reported_nonmedia_errors'] and evidence['bootstrap_successful_complete'] and evidence['bootstrap_ack_complete'] and all(x['status'].startswith('PASS_') for x in evidence['windows']) and not extra
 evidence.update(status='PASS_IMMUTABLE_ACTUAL_SCOPE_PENDING_ROOT_SEMANTIC' if good else 'REJECT_ACTUAL_SCOPE_KEEP_RAW_NO_RETRY',immutable_prefix=dict(path=str(prefix),sha256=sha(prefix),bytes=cut),immutable_actual_outputs=immutable,actual_png_pixel_checks=pixels,additional_scope_issues=extra,parent_terminal_present=(a/'terminal.json').exists(),whole_CLI_status_not_inferred=True,training_admitted=False)
 target=a/f'w{job:02d}_completed_scope_audit.json';save(target,evidence)
 print(json.dumps(dict(event='SCOPE_SEALED',CLI=number,job=job,status=evidence['status'],audit_path=str(target),audit_sha256=sha(target),immutable_prefix=evidence['immutable_prefix'],proposal_sha256=current['proposal_sha256']),ensure_ascii=False),flush=True)
 return evidence
def ensure_scopes(number):
 a=ROOT/f'call{number}';idx=read(a/'index.json');raw=(a/'stream.jsonl').read_bytes()
 done=[r['step_update'] for r in parsed(raw) if r.get('step_update',{}).get('state')=='DONE' and r['step_update'].get('step_type')=='tool']
 for w in idx['windows']:
  target=a/f"w{w['job_index']:02d}_completed_scope_audit.json"
  if not target.exists() and any(pathinfo(t)==('write_to_file',key(w['proposal_path'])) for t in done):seal_scope(number,w['job_index'])
def continuation_decision(scopes,terminal,whole,post,drift,media_repeats,late_writes,network_error_after_last_proposal=False,pre_completion_error=False):
 issues=[]
 if not scopes or not all(s.get('status')=='PASS_IMMUTABLE_ACTUAL_SCOPE_PENDING_ROOT_SEMANTIC' for s in scopes):issues.append('MISSING_OR_REJECTED_IMMUTABLE_SCOPE')
 if drift:issues.append('OUTPUT_OR_PREFIX_BYTE_DRIFT')
 if media_repeats:issues.append('REPEATED_SUCCESSFUL_MEDIA')
 if late_writes:issues.append('REWRITTEN_SUCCESSFUL_FACT_OR_PROPOSAL')
 if post:issues.append('TOOL_AFTER_FINAL_PROPOSAL_TERMINAL_INSTRUCTION')
 if pre_completion_error:issues.append('EXPLICIT_ERROR_BEFORE_ALL_PROPOSALS')
 if whole['errored_tool_attempts'] or whole['unfinished_tool_attempts']:issues.append('ACTUAL_TOOL_ERROR_OR_UNFINISHED')
 # Honest whole status and continuation are separate. Only precise post-completion
 # nonmedia network failure is eligible; outside paths/media failures are not ignored.
 forbidden=[i for i in whole['tool_issues'] if i['reason'] not in ('CORE_MEDIA_ORDER_OR_MISSING','CONTEXT_OR_SUPPLY_ORDER_OR_MISSING')]
 if forbidden:issues.append('ACTUAL_OTHER_TOOL_OR_WHITELIST_FAILURE')
 if whole['reported_nonmedia_errors']:issues.append('REPORTED_NONMEDIA_ERROR_REQUIRES_STOP')
 normal=terminal.get('child_process_created') is True and terminal['exit_code']==0 and terminal.get('stop_reason') is None and whole['actual_result_status']=='SUCCESS' and not whole['tool_issues']
 network=bool(re.search(r'(request failed|connection|eof|wsasend|tcp|transport|deadline|timeout)',str(whole.get('actual_result_error','')),re.I)) and not re.search(r'401|unauth|credential|403|permission',str(whole.get('actual_result_error','')),re.I)
 post_network=False # globalcap36: wholeERROR stays REJECTED; no later CLI exists.
 if not normal and not post_network:issues.append('WHOLE_FAILURE_NOT_ELIGIBLE_POST_COMPLETION_NETWORK_ONLY')
 return dict(eligible=not issues,issues=issues,whole_success=normal,post_completion_network_failure_only=post_network,whole_failed_not_reclassified=not normal,further_CLI_allowed=False,global_cap=36)
def final(number):
 a=ROOT/f'call{number}';idx=read(a/'index.json');terminal=read(a/'terminal.json');raw=(a/'stream.jsonl').read_bytes();assert sha(a/'stream.jsonl')==terminal['stream_sha256']
 ensure_scopes(number);whole=engine.inspect(a,raw,terminal=terminal);scopes=[];drift=[];last=0
 for w in idx['windows']:
  p=a/f"w{w['job_index']:02d}_completed_scope_audit.json"
  if not p.exists():scopes.append(dict(status='MISSING_SCOPE',job_index=w['job_index']));continue
  d=read(p);scopes.append(dict(status=d['status'],job_index=w['job_index'],audit_path=str(p),audit_sha256=sha(p),immutable_prefix=d['immutable_prefix']))
  pref=Path(d['immutable_prefix']['path']);last=max(last,d['immutable_prefix']['bytes'])
  if not pref.exists() or sha(pref)!=d['immutable_prefix']['sha256'] or raw[:d['immutable_prefix']['bytes']]!=pref.read_bytes():drift.append(dict(reason='PREFIX_BYTE_DRIFT',job=w['job_index']))
  for output in d['immutable_actual_outputs']:
   if not Path(output['original_path']).exists() or not Path(output['sealed_copy_path']).exists() or sha(output['original_path'])!=output['sha256'] or sha(output['sealed_copy_path'])!=output['sealed_copy_sha256']:drift.append(dict(reason='SUCCESSFUL_OUTPUT_BYTE_DRIFT',path=output['original_path']))
 postrows=parsed(raw[last:]) if last else parsed(raw);post=[r['step_update'] for r in postrows if r.get('step_update',{}).get('step_type')=='tool'] if last else []
 latest={t['step_index']:t for r in parsed(raw) if (t:=r.get('step_update',{})).get('step_type')=='tool'}
 media={key(p) for w in idx['windows'] for p in [w['clip_path'],*(f['path'] for g in w['groups'] for f in g['frames']),*(f['path'] for f in w['student_previews'])]};writes={key(p) for p in read(a/'freeze.json')['write_whitelist']}
 counts={};media_repeats=[];late_writes=[]
 for t in latest.values():
  name,p=pathinfo(t)
  if name=='view_file' and p in media:
   counts[p]=counts.get(p,0)+1
   if counts[p]>1:media_repeats.append(dict(step=t['step_index'],path=p))
  if name=='write_to_file' and p in writes:
   k=('write',p);counts[k]=counts.get(k,0)+1
   if counts[k]>1:late_writes.append(dict(step=t['step_index'],path=p))
 pre_result_errors=[r for r in parsed(raw[:last]) if r.get('event')=='result']
 post_result_errors=[r for r in postrows if r.get('event')=='result' and r.get('result',{}).get('status')=='ERROR']
 after=bool(last and post_result_errors and post_result_errors[-1]['result'].get('error')==whole['actual_result_error'])
 decision=continuation_decision(scopes,terminal,whole,post,drift,media_repeats,late_writes,network_error_after_last_proposal=after,pre_completion_error=bool(pre_result_errors))
 status='PASS_WHOLE_ACTUAL_CLI_PENDING_ROOT_SEMANTIC' if decision['whole_success'] and decision['eligible'] else 'REJECTED_WHOLE_CLI_KEEP_ALL_ACTUAL_RAW_COST'
 whole.update(status=status,actual_scope_receipts=scopes,actual_post_last_proposal_tool_updates=post,actual_pre_completion_result_ERRORS=pre_result_errors,actual_post_completion_result_ERRORS=post_result_errors,exact_final_network_error_after_last_proposal=after,immutable_drift=drift,repeated_media_attempts=media_repeats,rewritten_output_attempts=late_writes,continuation_decision=decision,whole_failed_not_reclassified=status.startswith('REJECTED'),semantic_correctness='ROOT_INDEPENDENT_PENDING',training_admitted=False)
 save(a/'audit.json',whole)
 print(json.dumps(dict(event='HONEST_WHOLE_TERMINAL_AUDIT',CLI=number,status=status,result=whole['actual_result_status'],continuation=decision,scopes=scopes),ensure_ascii=False),flush=True)
 return whole
if __name__=='__main__':
 if sys.argv[1]=='scope':seal_scope(int(sys.argv[2]),int(sys.argv[3]))
 else:final(int(sys.argv[1]))
