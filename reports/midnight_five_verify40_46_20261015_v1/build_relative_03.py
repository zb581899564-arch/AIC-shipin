"""Register a distinct relative-ranking development arm after zero-change absolute review."""
from pathlib import Path
import ast,hashlib,json,subprocess,zipfile
W=Path(__file__).resolve().parents[2];R=Path(__file__).resolve().parent
ROOT='/home/inspur/aic_video_work/midnight_five_verify40_46_20261015_v1';PY='/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'
source=W/'improvement/midnight_five_runtime_v1';dest=W/'improvement/midnight_relative_runtime_v1';dest.mkdir(exist_ok=False)
for p in source.glob('*.py'):(dest/p.name).write_text(p.read_text(encoding='utf8'),encoding='utf8')
p=dest/'mf_common.py';s=p.read_text(encoding='utf8').replace('def prompt(req):','def original_absolute_prompt(req):',1)
s+='''

def prompt(req):
    original=original_absolute_prompt(req)
    start=original.index('Return five independent judgments. ordinary:')
    end=original.index('Then propose at most ONE additional interval')
    rank=('First rank ONLY the listed current candidate intervals by how visually distinctive, informative, compelling, and worth keeping they are relative to one another in THIS visible window. '
      'This is a comparative edit, not a claim that rejected content is objectively ordinary. '
      'If there are two or more candidates, choose the SINGLE strongest candidate. In ordinary put all the OTHER candidate IDs, sorted ascending. '
      'In redundant put ONLY the SINGLE weakest candidate ID, which must also appear in ordinary. '
      'When only one candidate exists, both arrays are empty. Compare actual visible action, meaningful results, expressive reactions and information; do not rank merely by earlier time or candidate number. '
      'The two resulting edits are independent: ordinary keeps the strongest per window; redundant removes only the weakest per multi-candidate window. ')
    return original[:start]+rank+original[end:]

_base_validate=validate
def validate(value,n):
    _base_validate(value,n)
    require(len(value['ordinary'])==max(0,n-1) and len(value['redundant'])==(1 if n>1 else 0),'Relative ranking must account for each actual candidate')
    require(set(value['redundant'])<=set(value['ordinary']),'Weakest must be among candidates outside the strongest')
    return value
'''
p.write_text(s,encoding='utf8')
p=dest/'grammar.py';s=p.read_text(encoding='utf8');a=s.index('def expression(n):');b=s.index('\nclass Constraint:',a)
replacement='''def expression(n):
    prefixes=[]
    if n<=1:
        prefixes=[re.escape('{"ordinary":[],"redundant":[],')]
    else:
        for best in range(n):
            others=[i for i in range(n) if i!=best]
            for worst in others:
                text='{"ordinary":'+json.dumps(others,separators=(',',':'))+',"redundant":['+str(worst)+'],'
                prefixes.append(re.escape(text))
    ranges=['\\\\[\\\\]']
    for a in range(64):
        ranges.append('\\\\['+str(a)+',(?:'+'|'.join(map(str,range(a+1,65)))+')\\\\]')
    interval='(?:'+'|'.join(ranges)+')'
    return '(?:'+'|'.join(prefixes)+')'+','.join(re.escape('"'+f+'":')+interval for f in FIELDS[2:])+'\\\\}'
'''
s=s[:a]+replacement+s[b:];p.write_text(s,encoding='utf8')
for p in dest.glob('*.py'):ast.parse(p.read_text(encoding='utf8'))
proto=json.loads((R/'protocol.json').read_text(encoding='utf8'));proto.update(schema='MIDNIGHT_RELATIVE_RANKING_AND_THREE_UNSCREENED_RECALL_V1',
    deletion_arm_semantics={'ORDINARY':'RELATIVE_KEEP_BEST_ONE_PER_MULTICANDIDATE_WINDOW','REDUNDANT':'RELATIVE_DROP_WORST_ONE_PER_MULTICANDIDATE_WINDOW'},
    independent_new_development=True,prior_absolute_development='STOP_NO_ACTUAL_CHANGE_NOT_A_NEW_PACKAGE',
    empty_source_guard='PRESERVE_ORIGINAL_VERIFY40_46_SOURCE_SELECTION',test_content_or_leaderboard_parameter_selection=False,
    no_quality_filtering_for_three_semantic_risk_arms=True,baseline_original_zip_unchanged=True)
pp=R/'relative_protocol_03.json'
with pp.open('x',encoding='utf8') as f:json.dump(proto,f,ensure_ascii=False,indent=2)
archive=R/'relative_control_03.zip';files={'relative_code_v1/'+p.name:p for p in dest.glob('*.py')};files['relative_protocol_03.json']=pp
manifest={n:hashlib.sha256(p.read_bytes()).hexdigest() for n,p in files.items()}
with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as z:
 for n,p in files.items():z.write(p,n)
 z.writestr('manifest.json',json.dumps(manifest))
size=archive.stat().st_size;digest=hashlib.sha256(archive.read_bytes()).hexdigest()
subprocess.run(['scp','-o','BatchMode=yes','-o','ConnectTimeout=12',str(archive),'aic-inspur-home:'+ROOT+'/'+archive.name],check=True,capture_output=True)
code=f'''from pathlib import Path
import json,hashlib,zipfile,subprocess,os,sys
r=Path({ROOT!r});p=r/{archive.name!r}
assert (r/'dev_deletion_comparison_01.json').exists()
assert not json.loads((r/'dev_deletion_comparison_01.json').read_text())['passed_arms']
assert p.stat().st_size=={size} and hashlib.sha256(p.read_bytes()).hexdigest()=={digest!r}
with zipfile.ZipFile(p) as z:
 assert z.testzip() is None;m=json.loads(z.read('manifest.json'))
 assert set(z.namelist())==set(m)|{{'manifest.json'}}
 for n,d in m.items():
  assert not Path(n).is_absolute() and '..' not in Path(n).parts and hashlib.sha256(z.read(n)).hexdigest()==d
  f=r/n;f.parent.mkdir(exist_ok=True)
  with f.open('xb') as h:h.write(z.read(n))
ref=lambda p:dict(path=str(p),sha256=hashlib.sha256(p.read_bytes()).hexdigest())
mapping=r/'relative_dev_mapping';mapping.mkdir()
old=r/'dev_mapping'
for n in ['inference_entries.json','evaluation_manifest.json']:
 j=json.loads((old/n).read_text());j['protocol_ref']=ref(r/'relative_protocol_03.json');j['adopted_existing_metadata_ref']=ref(old/n)
 if n=='evaluation_manifest.json':j['inputs_ref']=ref(mapping/'inference_entries.json')
 (mapping/n).write_text(json.dumps(j,indent=2))
stage=r/'relative_dev_03';stage.mkdir()
reg=json.loads((r/'dev_recovery_02/registration.json').read_text());reg.update(stage=stage.name,requests_ref=ref(mapping/'inference_entries.json'),protocol_ref=ref(r/'relative_protocol_03.json'),code_files={{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (r/'relative_code_v1').glob('*.py')}},gpu_job_name='midnight_relative_rank_dev8_20261015_v1',new_prompt_same_native_vision=True,prior_development_ref=ref(r/'dev_deletion_comparison_01.json'))
reg.pop('explicit_recovery_from_failure_ref',None)
(stage/'registration.json').write_text(json.dumps(reg,indent=2))
env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',TOKENIZERS_PARALLELISM='false')
probe='import sys;sys.path.insert(0,'+repr(str(r/'relative_code_v1'))+');import mf_common; mf_common.library();import grammar; import regex; assert regex.fullmatch(grammar.expression(2),'+repr('{{"ordinary":[1],"redundant":[1],"action":[],"reaction":[],"information":[]}}')+');print("RELATIVE_IMPORT_AND_FINITE_SCHEMA_PASS")'
subprocess.run([{PY!r},'-B','-c',probe],env=env,check=True)
env['CUDA_VISIBLE_DEVICES']='0'
with (stage/'parent.log').open('x') as log:
 proc=subprocess.Popen([{PY!r},'-B',str(r/'relative_code_v1/controller.py'),'--stage',stage.name],env=env,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
launch=dict(pid=proc.pid,start_ticks=Path('/proc/'+str(proc.pid)+'/stat').read_text().split()[21],stage=stage.name,argv=[{PY!r},'-B',str(r/'relative_code_v1/controller.py'),'--stage',stage.name],registration_ref=ref(stage/'registration.json'),control_bytes={size},control_sha256={digest!r})
(r/'relative_dev_launch_03.json').write_text(json.dumps(launch,indent=2));print(json.dumps(launch))
'''
result=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=12','aic-inspur-home','python3','-'],input=code,text=True,capture_output=True)
print(result.stdout);print(result.stderr[-2000:] if result.returncode else '');result.check_returncode()
with (R/'relative_dev_launch_03.json').open('x',encoding='utf8') as f:json.dump(dict(bytes=size,sha256=digest,output=result.stdout),f,indent=2)
