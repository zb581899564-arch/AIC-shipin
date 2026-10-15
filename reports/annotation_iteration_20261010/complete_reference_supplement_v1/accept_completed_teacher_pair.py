"""Independent root byte/tool acceptance of one clean completed fixed teacher pair."""
import argparse,json,hashlib
from pathlib import Path
from fractions import Fraction as F
from datetime import datetime,timezone
from PIL import Image
ROOT=Path(__file__).resolve().parent
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bind(p):return dict(path=str(p),sha256=sha(p))
def norm(p):return str(Path(p).resolve()).casefold()
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--call-directory',required=True);a=ap.parse_args()
 c=Path(a.call_directory).resolve(strict=True);assert c.parent==ROOT/'teacher_expansion/capacity_v4_tool_batches'
 audit=read(c/'audit.json');terminal=read(c/'terminal.json');freeze=read(c/'freeze.json');index=read(c/'index.json')
 assert terminal['exit_code']==0 and terminal['stop_reason'] is None and audit['actual_result_status']=='SUCCESS'
 assert not audit['tool_issues'] and not audit['unfinished_tool_attempts'] and not audit['error_message_steps']
 assert sha(c/'stream.jsonl')==terminal['stream_sha256']==audit['stream_sha256']
 assert sha(c/'terminal.json')==audit['terminal_sha256'] and sha(c/'freeze.json')==audit['freeze_sha256']
 for p,h in freeze['inputs'].items():assert sha(p)==h
 steps={}
 for line in (c/'stream.jsonl').read_text(encoding='utf-8-sig').splitlines():
  d=json.loads(line)
  if d.get('event')=='step_update':steps[d['step_update']['step_index']]=d['step_update']
 actual=[];written=set();self_reads={}
 for ix,s in sorted(steps.items()):
  if s['step_type']!='tool':continue
  assert s['state']=='DONE' and s['tool_name'] in ('view_file','write_to_file')
  par=s['tool_info']['parameters'];path=norm(par.get('AbsolutePath') or par.get('TargetFile'));name=s['tool_name']
  if name=='view_file' and path in written:
   self_reads[path]=self_reads.get(path,0)+1;assert self_reads[path]<=1
  else:actual.append((name,path))
  if name=='write_to_file':assert path not in written;written.add(path)
 expected=[('view_file',norm(c/'index.json'))]
 outputs=[]
 for w in index['windows']:
  idx=w['job_index'];ar=next(r for r in audit['windows'] if r['job_index']==idx)
  assert ar['status']=='PASS_TOOL_STRUCTURE_PENDING_SEMANTIC_REVIEW' and ar['window_tool_sequence_complete'] is True
  assert not ar['schema_issues'] and not ar['proposal_issues'] and len(ar['native_read_done'])==64 and len(ar['student_preview_read_done'])==8
  for g in w['groups']:
   for fr in g['frames']:
    assert sha(fr['path'])==fr['png_sha256']
    with Image.open(fr['path']) as im:assert list(im.size)==fr['geometry']
    expected.append(('view_file',norm(fr['path'])))
   expected.append(('write_to_file',norm(g['output_path'])))
  expected.append(('view_file',norm(w['clip_path'])))
  for fr in w['student_previews']:
   assert sha(fr['path'])==fr['png_sha256']
   with Image.open(fr['path']) as im:assert list(im.size)==fr['geometry']
   expected.append(('view_file',norm(fr['path'])))
  expected.append(('write_to_file',norm(w['proposal_path'])))
  bp=c/f'w{idx:02d}_program_bound_facts.json';assert sha(bp)==ar['program_bound_facts_sha256']
  rows=read(bp)['rows'];assert len(rows)==64
  for i,row in enumerate(rows):
   g=w['groups'][i//4];fr=g['frames'][i%4]
   assert row['frame_id']==fr['frame_id'] and row['source_ordinal']==fr['source_ordinal'] and row['png_sha256']==fr['png_sha256']
   assert row['raw_output_sha256']==sha(g['output_path']) and row['identity_generated_by_program'] is True
   assert row['facts']==read(g['output_path'])['items'][i%4]
  assert sha(w['proposal_path'])==ar['proposal_sha256']
  cursor=F(0)
  for seg in read(w['proposal_path'])['segments']:
   assert seg['decision'] in ('KEEP','NO','UNKNOWN') and F(str(seg['start_seconds']))==cursor
   hi=F(str(seg['end_seconds']));assert cursor<hi<=F(w['domain_local_seconds'][1]);cursor=hi
  assert cursor==F(w['domain_local_seconds'][1])
  outputs.append((w,bp))
 assert actual==expected and len(actual)==181
 for w,bp in outputs:
  idx=w['job_index'];out=ROOT/f'{idx:02d}_teacher_completed_pair_observation.json'
  receipt=dict(status='PASS_ROOT_ACTUAL_COMPLETE_CLEAN_TEACHER_WINDOW_SUPPLY_SEMANTIC_REFERENCE_PENDING',utc=datetime.now(timezone.utc).isoformat(),
   window_id=w['window_id'],original_pngs_delivered=64,effective_pngs_delivered=8,native_video_delivered=True,tool_issues=[],proposal_geometry_identity_issues=[],
   actual_pair_tools=181,pair_audit=bind(c/'audit.json'),terminal=bind(c/'terminal.json'),raw=bind(c/'stream.jsonl'),freeze=bind(c/'freeze.json'),
   proposal=bind(w['proposal_path']),program_bound_facts=bind(bp),actual_CLI_status='SUCCESS',global_CLI=terminal['CLI_after'],
   actual_pair_wall_seconds=terminal['wall_seconds'],cash_cost='UNKNOWN_NOT_ZERO',teacher_semantics_not_truth=True,training_admitted=False,new_optimizer_updates=0)
  with out.open('x',encoding='utf-8') as f:json.dump(receipt,f,ensure_ascii=False,indent=2)
 print(json.dumps(dict(status='PASS_TWO_WINDOW_ACTUAL_TEACHER_SUPPLY_NOT_SEMANTIC_ADMISSION',job_indices=[w['job_index'] for w,bp in outputs],training_admitted=False)))
if __name__=='__main__':main()
