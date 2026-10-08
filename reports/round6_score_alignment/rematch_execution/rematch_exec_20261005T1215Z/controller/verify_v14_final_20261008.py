"""Independent Linux final artifact/selection/accounting audit; return aggregates only."""
from pathlib import Path
import hashlib
import json
from register_b2_package_v1 import remote

RUN = Path(__file__).resolve().parent.parent
RECEIPT = 'V14_final_acceptance_20261008.json'
SCRIPT = r'''
from pathlib import Path
from datetime import datetime,timezone
from itertools import zip_longest
import hashlib,json,math,socket,subprocess,zipfile

assert socket.gethostname()=='inspur-NP5570M5'
run=Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
entry=run/'teacher_student_autopilot_v14'
proof=run/'controller/V14_final_acceptance_20261008.json'
assert not proof.exists(),'final audit already exists; do not repeat'
lock_sha='5295e8bc0f2b6a651e73321a5798b259816ccbe9a0582753dc3c200b5ef080e0'
adapter_sha='8e2cca463d8aac39f7a709bdf562373e3e47a3a8da490991c303d5e03b803b23'
base_sha='74bcce81cfcb0893cf4b4c25ae36ec908d6ea669583aedd0f3940063080b8b59'
checks={'strict_loader_ok','video_record_set_exact','selected_key_set_exact','ratio_fields_exact','frames_sorted','provenance_key_set_exact','provenance_boxes_match_predictions','provenance_all_legal','provenance_sources_allowed','archive_single_file','archive_roundtrip_exact'}
def sha(path):
 d=hashlib.sha256()
 with Path(path).open('rb') as f:
  for part in iter(lambda:f.read(8<<20),b''):d.update(part)
 return d.hexdigest()
def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def rows(path):
 with Path(path).open(encoding='utf-8-sig') as f:
  for line in f:
   if line.strip():yield json.loads(line)

completion=read(entry/'completion.json')
assert completion['status']=='PASS_AUTOPILOT_FINAL_T_ZIP_ON_LINUX'
assert sha(entry/'source_lock.json')==completion['source_lock_sha256']==lock_sha
lock=read(entry/'source_lock.json');assert len(lock['files'])==16502
for name,digest in lock['files'].items():assert sha(name)==digest,'frozen file changed: '+name
for source_lock in run.glob('*/source_lock.json'):
 v=read(source_lock);e=v.get('files',v.get('production_files'))
 if isinstance(e,dict):names=list(e)
 elif isinstance(e,list) and all(isinstance(x,dict) and isinstance(x.get('path'),str) for x in e):names=[x['path'] for x in e]
 else:raise RuntimeError('unknown source lock schema')
 assert str(proof.resolve()) not in {str((source_lock.parent/n).resolve()) for n in names}
assert completion['automatic_return'] is completion['uploaded'] is False
assert completion['official_score'] is None and completion['new_T_improvement_claimed'] is False
student=read(entry/'student_01/student_completion.json')
assert student['status']=='PASS_TRAINED_SELECTED_STUDENT_ADAPTER'
assert student['optimizer_steps']==student['total_updates']==student['total_planned_updates']==15
assert student['backward_examples']==195 and student['prefix_completed_updates']==4
assert student['registered_schedule_completed'] is student['base_frozen'] is student['vision_frozen'] is student['adapter_reload_succeeded'] is True
assert sha(entry/'student_config.json')==student['config_sha256']
updates=student['updates'];assert [x['update'] for x in updates]==list(range(1,16))
assert sum(x['windows'] for x in updates)==195
for epoch in (1,2,3):
 epoch_updates=[x for x in updates if x['epoch']==epoch]
 assert len(epoch_updates)==5 and sum(x['windows'] for x in epoch_updates)==65
for x in updates:
 assert math.isfinite(x['mean_loss']) and math.isfinite(x['gradient_norm']) and x['gradient_norm']>0
 assert x['changed_lora_tensors']==288
 for kind in ('lora_A','lora_B'):
  assert all(x['gradient_evidence'][kind][k]==144 for k in ('tensors','connected','finite','nonzero'))
assert all(x['sha256']==base_sha and x['parameters']==8767123696 for x in student['base_frozen_evidence'].values())
for kind in ('positive','explicit_empty'):
 ce=student['real_assistant_ce_acceptance'][kind]
 assert ce['status']=='PASS_REAL_ASSISTANT_CE' and ce['optimizer_updates']==0 and math.isfinite(ce['loss'])
prefix=read(entry/'student_01/prefix_gate.json')
reload=read(entry/'student_01/prefix_adapter_reload.json')
assert prefix==student['prefix_gate'] and prefix['status']=='PASS_SAME_RUN_EARLY_UPDATE_PREFIX'
assert prefix['completed_updates']==4 and prefix['same_optimizer_rng_data_position'] is True and prefix['extra_epochs_started'] is False
assert sha(prefix['state_path'])==prefix['state_sha256']
roundtrip=prefix['state_roundtrip'];assert roundtrip['status']=='PASS_TRUSTED_PREFIX_STATE_ROUNDTRIP'
assert roundtrip['optimizer_updates_performed']==0
for k in ('optimizer_tensor_metadata_and_bytes_equal','lora_tensor_metadata_and_bytes_equal','python_numpy_torch_cuda_rng_equal','schedule_and_pending_epoch_state_equal','active_optimizer_reference_unchanged','active_parameter_references_unchanged','active_rng_unchanged'):
 assert roundtrip[k] is True
assert reload==prefix['independent_adapter_reload']
assert reload['status']=='PASS_INDEPENDENT_PREFIX_ADAPTER_CPU_RELOAD' and reload['lora_tensors']==288 and reload['device']=='cpu' and reload['optimizer_updates']==0
assert reload['base_frozen']['sha256']==reload['adapter_off']['sha256']==base_sha
assert sha(Path(reload['adapter_dir'])/'adapter_model.safetensors')==reload['adapter_model_sha256']
assert sha(Path(reload['adapter_dir'])/'adapter_config.json')==reload['adapter_config_sha256']
candidates=student['candidates'];assert len(candidates)==4
for candidate in candidates:
 assert sha(Path(candidate['adapter_dir'])/'adapter_model.safetensors')==candidate['adapter_model_sha256']
 assert sha(Path(candidate['adapter_dir'])/'adapter_config.json')==candidate['adapter_config_sha256']
best=min((x for x in candidates if x['candidate_eligible']),key=lambda x:(-x['video_macro_f1'],x['epoch']))
assert best['epoch']==student['selected_epoch']==completion['selected_epoch']==0
assert best['adapter_model_sha256']==student['selected_adapter_sha256']==completion['selected_adapter_sha256']==adapter_sha
assert student['selected_candidate_original_B'] is completion['selected_candidate_original_B'] is True
assert student['trained_candidate_selected'] is student['selected_new_T_improvement_claim'] is student['quality_claim'] is False
teacher=read(entry/'full_resume_handoff.json')
assert teacher['status']=='PASS_EXACT_V13_COMPLETE_TEACHER_HANDOFF_NO_NEW_CALLS'
config=read(run/'b_score_aligned_package_v4/config.json')
scopes={};anchors_total=0
for scope,count,frames in [('nontest',8,447),('rematch',426,102470)]:
 out=entry/(scope+'_01');inputs=config['inputs'][scope]
 assert sha(inputs['manifest'])==inputs['manifest_sha256'] and sha(inputs['registry'])==inputs['registry_sha256']
 manifest=read(inputs['manifest']);expected={x['video_id'] for x in manifest['records']}
 assert len(manifest['records'])==len(expected)==count
 package=read(out/'package.stage.json');strict=read(out/'independent_validation.json')
 assert package['status']=='PASS_COMPLETE_T_8B_PACKAGE_ON_LINUX' and package['video_records']==count and package['issues']==[]
 assert package['weak_roi_inputs_used']==package['old_test_boxes_used']==package['silent_fallbacks']==0
 assert package['complete_pipeline_parameters']==8782459120 and package['selected_adapter_sha256']==adapter_sha
 assert strict['status']=='PASS_INDEPENDENT_STRICT_VALIDATION' and set(strict['checks'])==checks and all(x is True for x in strict['checks'].values())
 assert strict['strict_loader_issues']==[] and strict['missing']==strict['extra']==strict['duplicate_frames']==0
 assert strict['video_records']==count and strict['expected_frames']==strict['prediction_frames']==package['prediction_frames']==frames
 assert sha(run/'baseline_a_pts_v1/vendor/frozen_strict_loader/aic6/scoring.py')==strict['strict_loader_sha256']
 candidate=out/'candidate_T_8B.zip';assert str(candidate)==package['candidate']
 assert candidate.stat().st_size==package['zip_bytes'] and sha(candidate)==package['zip_sha256']==strict['zip_sha256']
 with zipfile.ZipFile(candidate) as archive:
  assert archive.namelist()==['predictions.jsonl'] and archive.testzip() is None
  member=archive.read('predictions.jsonl')
 assert member==(out/'predictions.jsonl').read_bytes()
 assert hashlib.sha256(member).hexdigest()==package['predictions_sha256']==strict['predictions_sha256']
 assert sha(out/'provenance.jsonl')==strict['provenance_sha256']
 ids=[x['video_id'] for x in rows(out/'predictions.jsonl')]
 assert len(ids)==len(set(ids))==count and set(ids)==expected
 assert sum(1 for _ in rows(out/'selected.jsonl'))==frames
 temporal=read(out/'temporal.stage.json')
 assert temporal['status']=='PASS_TEMPORAL_EXECUTION' and temporal['videos']==count and temporal['invalid_windows']==0 and temporal['selected_adapter_sha256']==adapter_sha
 assert temporal['windows']==(8 if scope=='nontest' else 521) and sha(out/'temporal.jsonl')==temporal['output_sha256']
 schedule=read(out/'schedule.stage.json');space=read(out/'spatial.stage.json')
 assert schedule['selected_frames']==frames and schedule['temporal_selection_used_for_boundaries'] is False
 for filename,field in [('field_frames.jsonl','field_frames_sha256'),('field_shots.jsonl','shots_sha256'),('anchor_requests.jsonl','requests_sha256')]:assert sha(out/filename)==schedule[field]
 anchors=0
 for request,result in zip_longest(rows(out/'anchor_requests.jsonl'),rows(out/'anchor_output.jsonl')):
  assert request is not None and result is not None
  assert result['status']=='MODEL_OK' and result['used_fallback'] is False
  assert all(result[k]==request[k] for k in ('video_id','source_frame','anchor_request_sha256'))
  assert result['decoded_pixel_sha256']==request['expected_pixel_sha256'];anchors+=1
 assert anchors==schedule['anchors']==space['rows']==space['model_calls']==(206 if scope=='nontest' else 31295)
 assert space['status']=='PASS_STRICT_SOURCE_FIELD_SPATIAL' and space['invalid']==space['failure_to_empty_conversions']==space['model_calls_this_T_candidate']==0
 assert space['time_adapter_enabled'] is False and space['reused_cache'] is True
 assert sha(out/'anchor_output.jsonl')==space['anchor_output_sha256']
 assert sha(out/'anchor_output.jsonl')==sha(Path(space['source_cache'])/'anchor_output.jsonl')
 anchors_total+=anchors
 scopes[scope]=dict(videos=count,prediction_frames=frames,strict_checks=strict['checks'],independent_report_sha256=sha(out/'independent_validation.json'),manifest_sha256=inputs['manifest_sha256'],registry_sha256=inputs['registry_sha256'],candidate=str(candidate),zip_bytes=candidate.stat().st_size,zip_sha256=sha(candidate),predictions_sha256=package['predictions_sha256'],provenance_sha256=strict['provenance_sha256'],crc_pass=True,archive_names=['predictions.jsonl'],archive_roundtrip_exact=True,source_ids_exact=True,duplicate_source_ids=0,temporal_windows=temporal['windows'],invalid_temporal_windows=0,source_anchors=anchors,new_spatial_model_calls=0,original_spatial_wall_seconds=space['wall_seconds'])
assert completion['candidate']==scopes['rematch']['candidate']
assert completion['candidate_bytes']==scopes['rematch']['zip_bytes']==308278
assert completion['candidate_sha256']==scopes['rematch']['zip_sha256']=='95173d936d09cfcf84bcff5755336e50dbfff94ac5a7e4cfba2953064022f3a2'
ledger_path=Path('/home/inspur/aic_video_work/improvement_round1/gpu_ledger.jsonl');ledger=list(rows(ledger_path));resources={}
for suffix in ('student_train','nontest_temporal','rematch_temporal'):
 name='rematch_TAUTO_v14_'+suffix;path=run/'controller'/(name+'.resource.json');resource=read(path)
 matches=[x for x in ledger if x.get('name')==name]
 assert len(matches)==1 and matches[0]==resource
 assert resource['status']=='completed' and resource['exit_code']==0 and resource['stop_reason'] is None and resource['charged_seconds']>0
 resources[name]=dict(receipt_sha256=sha(path),charged_seconds=resource['charged_seconds'],sampled_peak_memory_mib=resource['sampled_peak_memory_mib'],ledger_exact=True,exit_code=0,stop_reason=None)
ps=subprocess.check_output(['ps','-eo','args'],text=True)
owned=[x for x in ps.splitlines() if str(entry)+'/' in x or 'gpu_run.py --name rematch_TAUTO_v14' in x]
assert owned==[]
receipt=dict(status='PASS_INDEPENDENT_V14_FINAL_ZIP_TRAINING_SELECTION_AND_ACCOUNTING',utc=datetime.now(timezone.utc).isoformat(),host=socket.gethostname(),entry=entry.name,source_lock_sha256=lock_sha,frozen_files_verified=16502,verifier_source_sha256='__VERIFIER_SHA__',completion_sha256=sha(entry/'completion.json'),completion_status=completion['status'],scopes=scopes,actual_T_optimizer_updates=15,actual_backward_examples=195,epochs_completed=3,finite_loss_gradient_all_updates=True,changed_adapter_tensors_each_update=288,frozen_base_runtime_sha256=base_sha,frozen_base_receipts_equal=True,prefix_state_current_sha256=prefix['state_sha256'],prefix_updates=4,original_independent_CPU_reload_sha256=sha(entry/'student_01/prefix_adapter_reload.json'),independent_CPU_reload_was_288_adapter_PASS=True,CPU_reload_repeated_by_this_audit=False,candidate_artifact_SHAs_pass=True,weak_dev_candidates=[dict(epoch=x['epoch'],video_macro_f1=x['video_macro_f1']) for x in candidates],independent_selection_recomputed=True,selected_epoch=0,selected_original_B=True,trained_candidate_selected=False,selected_adapter_sha256=adapter_sha,new_T_improvement_claim=False,teacher_original_labels=160,teacher_original_reviews=160,supported_train=65,supported_dev=14,UNKNOWN_preserved=81,same_teacher_consistency_weak_not_truth=True,resources=resources,gpu_ledger_records=len(ledger),gpu_ledger_sha256=sha(ledger_path),gpu_ledger_not_modified=True,historical_offset_seconds_preserved=7200,owned_processes=[],logical_parameters=8782459120,model_calls_by_this_audit=0,optimizer_updates_by_this_audit=0,teacher_calls_by_this_audit=0,per_frame_data_exported=False,raw_answers_exported=False,large_transfer_bytes=0,official_score=None,automatic_return=False,uploaded=False)
body=(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n').encode()
with proof.open('xb') as f:f.write(body)
print(body.decode(),end='')
'''

def main():
    path=RUN/'controller'/RECEIPT
    if path.exists():
        raise RuntimeError('Already audited; refusing repeat.')
    digest=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    body=remote(SCRIPT.replace('__VERIFIER_SHA__',digest),echo=False)
    value=json.loads(body)
    assert value['status']=='PASS_INDEPENDENT_V14_FINAL_ZIP_TRAINING_SELECTION_AND_ACCOUNTING'
    assert value['verifier_source_sha256']==digest
    with path.open('xb') as f:f.write(body)
    print(json.dumps(dict(status=value['status'],receipt=RECEIPT,receipt_sha256=hashlib.sha256(body).hexdigest(),candidate=value['scopes']['rematch'],T_updates=15,selected_original_B=True),ensure_ascii=False))

if __name__=='__main__':main()
