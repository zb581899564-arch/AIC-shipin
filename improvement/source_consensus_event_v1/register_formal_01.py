"""One new formal visual gate; adopt immutable proposal/media bindings."""
import ast, base64, datetime as dt, hashlib, json, os, pathlib, subprocess, time
import numpy as np
W=pathlib.Path('/home/inspur/aic_video_work')
F=W/'visual_pair_formal_20261018_v1'; V=W/'visual_pair_reject_20261018_v1'
E=W/'meaningful_residual_20261018_v1'; R=W/'relative_precision_event_20261018_v1'
PY=W/'env/qwen3vl_isolated_20260910/bin/python'
def read(p):return json.loads(pathlib.Path(p).read_text())
def ref(p):
    p=pathlib.Path(p);return dict(path=str(p),bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest())
def bound(r):
    p=pathlib.Path(r['path']);assert ref(p)==r;return p
def save(p,x):
    with pathlib.Path(p).open('x') as s:json.dump(x,s,ensure_ascii=False,indent=2,allow_nan=False)
assert os.uname().nodename=='inspur-NP5570M5'
assert not F.exists(), 'Unique formal root must not already exist'
F.mkdir();(F/'code_v1').mkdir()
payload=read('/dev/stdin') if False else PAYLOAD
for name,item in payload.items():
    data=base64.b64decode(item['base64']);assert len(data)==item['bytes'] and hashlib.sha256(data).hexdigest()==item['sha256']
    ast.parse(data);(F/'code_v1'/name).write_bytes(data)
reg=read(V/'registration_01.json')
visual={}
for value in read(E/'formal_inputs_01/completion.json')['sources']:
    item=read(bound(value));visual[item['sid']]=item
media={}
for value in read(E/'formal_audio_01/completion.json')['sources']:
    item=read(bound(value));manifest=read(bound(item['manifest_ref']))
    media[item['sid']]=dict(clock_ref=item['clock_ref'],media_ref=manifest['media_ref'])
decisions=read(R/'production_01/completion.json')['decisions'];cases=[]
for d in sorted(decisions,key=lambda v:int(v['sid'])):
    if d['chosen'] is None:continue
    sid=d['sid'];v=visual[sid];m=media[sid];clock=read(bound(m['clock_ref']))
    assert v['clock_ref']==m['clock_ref']
    arr=np.load(bound(v['input_ref']),allow_pickle=False);base=arr['baseline'].astype(bool)
    left=d['chosen']['left'];right=d['chosen']['right']
    a=np.flatnonzero(base);b=np.flatnonzero(~base[left:right])+left
    assert len(a)>0 and len(b)==d['chosen']['added_frames'] and len(base)==len(clock['original_exact_pts'])
    sample=lambda values:[int(x) for x in values[np.linspace(0,len(values)-1,4).round().astype(int)]]
    cases.append(dict(sid=sid,cohort='FORMAL_NO_LABELS',source={'sid':sid},original_choice=d,original_input_ref=v['input_ref'],clock_ref=m['clock_ref'],media_ref=m['media_ref'],anchor_ordinals=sample(a),candidate_ordinals=sample(b)))
assert len(cases)==158 and len(visual)==426 and len(media)==426
admission=dict(status='EXPLICIT_LIMITED_EXTERNAL_OUTPUT_EVIDENCE_PRODUCTION_REVIEW',human_authorization='那你现在赶紧去解决',baseline_score=40.47,pilot_outputs_ref=ref(V/'adopted_output_registration_03.json'),pilot_result_ref=ref(V/'result_03.json'),pilot_gpu_authority='FAILED exit1 after34savedoutputs at terminalflagguard; never relabel completed. All34 outputs independently adopted for limiteddiagnosis only.',limitations='17previouslyexposed cases;2beneficial and1harmful kept;10harmful and4beneficial rejected. Gain concentratedQ01. Not blind/not fullpilot chainPASS/not officialquality.',decision='One conditional formal gate with same frozen sparseimage/orderpolicy. No thresholds/fit/reranking; all316 inputs/outputs and true terminalbyte/flag checks mandatory. Failure blocks packaging.',official_rule_ref=ref(W/'calibrated_event_20261018_v1/official_current_04/content_comparison_acceptance.json'),original_proposals_ref=ref(R/'production_01/completion.json'),original_baseline_ref=read(E/'formal_inputs_01/completion.json')['baseline_ref'],deadline_utc='2026-10-18T16:00:00Z',utc=dt.datetime.now(dt.timezone.utc).isoformat())
save(F/'production_admission_01.json',admission)
reg.update(schema='ONE_FORMAL_FROZEN_PROPOSAL_VISUAL_REJECTION_GATE',cases=cases,expected_sources=158,expected_calls=316,production_cutoff_utc='2026-10-18T15:50:00Z',max_gpu_seconds=900,automatic_production=False,actual_pipeline_parameters=8782692681,official_data_read='Only registered official inference media; no labels/teacher/training/manualcontent selection',admission_ref=ref(F/'production_admission_01.json'),annotation='Sparse4image comparison,notcontinuousvideo; no inference of official preference from scores; same frozen17pilot policy; formal nohumanlabels',utc=dt.datetime.now(dt.timezone.utc).isoformat())
save(F/'registration_01.json',reg)
code=F/'code_v1/visual_pair_formal_v1.py'
check=subprocess.run([str(PY),'-B','-c',"import os,runpy;os.environ['CUDA_VISIBLE_DEVICES']='0';runpy.run_path("+repr(str(code))+",run_name='import_regression');assert os.environ['CUDA_VISIBLE_DEVICES']=='0'"],capture_output=True,text=True)
assert check.returncode==0,check.stderr
with (F/'prepare_pilot8.log').open('xb') as log:
    p=subprocess.Popen([str(PY),'-B',str(code),'prepare_pilot8'],stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT,start_new_session=True,env=dict(os.environ,CUDA_VISIBLE_DEVICES='0'))
stat=pathlib.Path('/proc/'+str(p.pid)+'/stat').read_text().rsplit(') ',1)[1].split()
save(F/'prepare_pilot8_launch.json',dict(pid=p.pid,start_ticks=int(stat[19]),argv=[str(PY),'-B',str(code),'prepare_pilot8'],registration_ref=ref(F/'registration_01.json'),utc=dt.datetime.now(dt.timezone.utc).isoformat()))
print(json.dumps(dict(status='UNIQUE_FORMAL_FIRST8_PREPARE_STARTED',pid=p.pid,cases=158,calls=316,code=ref(code),registration=ref(F/'registration_01.json'))))
