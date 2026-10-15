"""Create a new ROOT actual-scope verifier; preserve earlier unexecuted prototype."""
from pathlib import Path
import ast
R = Path(__file__).parent
src = (R/'accept_teacher_fragment_scope_v7_root.py').read_text(encoding='utf-8')
src = src.replace("V=R/'teacher_expansion/engineering_CLI36_five_window_fragment_v7'", "V=R/'teacher_expansion/engineering_CLI36_37_split_fragment_v8v4'")
src = src.replace("c=V/'call36';ap=", "assert job in range(19,24)\n n=36 if job<21 else 37\n c=V/f'call{n}';ap=")
src = src.replace("req['CLI_after']==36", "req['CLI_after']==n")
src = src.replace("fr['global_cap']==36", "fr['global_cap']==37")
src = src.replace("len(core)==102+100*(job-19)", "len(core)==2+100*len(active)")
src = src.replace("global_CLI=36", "global_CLI=n")
src = src.replace("rows=list(map(json.loads,prefix.splitlines()));states={};bare=[]", "rows=list(map(json.loads,prefix.splitlines()));validate_all_updates(rows,fr);states={};bare=[]")
src = src.replace("selfchecks.append(dict(step=t['step_index'],path=p));continue", "full_text_read(t,p);selfchecks.append(dict(step=t['step_index'],path=p));continue")
src = src.replace("selfcount[p]=selfcount.get(p,0)+1;assert selfcount[p]==1;continue", "selfcount[p]=selfcount.get(p,0)+1;assert selfcount[p]==1;full_text_read(t,p);continue")
src = src.replace("receipt=read(w['original_student_receipt']['path']);", "for group in w['groups']:\n  batch=[next(t for t in tools if t['tool_name']=='view_file' and key(t['tool_info']['parameters']['AbsolutePath'])==key(f['path'])) for f in group['frames']]\n  actual_same_response(rows,batch)\n for first in (0,4):\n  batch=[next(t for t in tools if t['tool_name']=='view_file' and key(t['tool_info']['parameters']['AbsolutePath'])==key(f['path'])) for f in w['student_previews'][first:first+4]]\n  actual_same_response(rows,batch)\n receipt=read(w['original_student_receipt']['path']);")
helpers = '''
def full_text_read(t,path):
 payload=Path(path).read_bytes();text=str(t['tool_info'].get('output',''))
 n=re.search(r'(\\d+) bytes',text);lines=re.search(r'(\\d+) lines',text)
 assert len(payload)<30000 and payload.endswith(b'\\n') and b'\\r' not in payload
 assert n and int(n.group(1))==len(payload) and lines and int(lines.group(1))==len(payload.split(b'\\n'))
 assert not any(x in text.lower() for x in ('truncat','not found','cannot read','failed','error'))

def validate_all_updates(rows,fr):
 reads=set(map(key,fr['read_whitelist']+fr['self_read_whitelist']));writes=set(map(key,fr['write_whitelist']))
 identity={}
 for row in rows:
  t=row.get('step_update',{})
  if t.get('step_type')!='tool':continue
  assert t.get('state')!='ERROR'
  name=t.get('tool_name');params=t.get('tool_info',{}).get('parameters',{})
  assert name in ('view_file','write_to_file')
  if name=='view_file':
   assert set(params)=={'AbsolutePath'} and key(params['AbsolutePath']) in reads
  else:assert key(params.get('TargetFile')) in writes
  ident=(name,json.dumps(params,sort_keys=True,ensure_ascii=False))
  step=t['step_index']
  if step in identity:assert identity[step]==ident
  identity[step]=ident

def actual_same_response(rows,batch):
 assert len(batch)==4
 planning=[];done=[]
 for t in batch:
  step=t['step_index']
  active=[i for i,r in enumerate(rows) if r.get('step_update',{}).get('step_type')=='tool' and r['step_update'].get('step_index')==step and r['step_update'].get('state')=='ACTIVE']
  completed=[i for i,r in enumerate(rows) if r.get('step_update',{}).get('step_type')=='tool' and r['step_update'].get('step_index')==step and r['step_update'].get('state')=='DONE']
  assert active and completed and active[0]>=0 and active[0]<completed[0]
  prior=[i for i,r in enumerate(rows[:active[0]]) if r.get('step_update',{}).get('step_type')=='agent_response' and r['step_update'].get('state')=='DONE']
  assert prior
  planning.append(prior[-1]);done.append(completed[0])
 assert len(set(planning))==1
 return dict(planning_response=planning[0],native_DONE=done)

'''
src = src.replace('def accept(job,output):', helpers+'def accept(job,output):')
ast.parse(src)
target=R/'accept_teacher_fragment_scope_v8_root.py'
with target.open('x',encoding='utf-8') as f:f.write(src)
print(target)
