"""Durable live handoff: active teacher work, one newly accepted eval reference."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
R=Path(__file__).parent
V=R/'teacher_expansion/engineering_CLI36_37_split_fragment_v8v5'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bind(p):return {'path':str(p),'sha256':sha(p)}
registry=R/'denominator24_v17.json';reg=read(registry)
assert reg['qualified_references']==16 and reg['pending_references']==4 and reg['accepted_train_windows']==8
scope=V/'call36/w19_completed_scope_audit.json';sc=read(scope)
assert sc['status']=='PASS_IMMUTABLE_ACTUAL_SCOPE_PENDING_ROOT_SEMANTIC'
bindings={n:bind(R/n) for n in ['denominator24_v17.json','19_j0n_w11_lawful_observation_completion_v2.json','19_j0n_w11_root_eval_decision.json','19_j0n_w11_final_main_review.json','19_j0n_w11_complete_reference.json','19_j0n_w11_root_actual_postteacher_pixels_v1.json','root_fragment_v8_serialization_failure_preserved_v1.json','accept_teacher_fragment_scope_v8_root_v2.py','read_completed_teacher_facts_v8.py','read_fragment_teacher_progress_v8.py','prepare_linux_projection.py']}
for row in reg['records'].values():
 if row.get('reference'):assert sha(Path(row['reference']['path']))==row['reference']['sha256']
d={'status':'LIVE_FRESH_CLI36_AND_REFERENCE16_CHECKPOINT_NOT_TRAINING','utc':datetime.now(timezone.utc).isoformat(),'registry_counts':{k:reg[k] for k in ['fixed_denominator','qualified_references','rejected_references','pending_references','accepted_train_windows']},'bindings':bindings,'root_start_gate':bind(V/'root_start_admission.json'),'execution_binding':bind(V/'execution_code_binding.json'),'actual_controller_registration':read(V/'registered.json'),'actual_observer_registration':read(V/'observer_registered.json'),'actual_CLI36_process':read(V/'call36/process.json'),'actual_CLI36_request':bind(V/'call36/request.json'),'CLI36_terminal_present':(V/'call36/terminal.json').exists(),'CLI37_request_present':(V/'call37/request.json').exists(),'accepted19_scope':bind(scope),'accepted19_prefix':sc['immutable_prefix'],'remaining_eval_job_indices':[20,21,22,23],'parent_session_success_not_inferred':True,'active_cost':'PENDING_ACTUAL_TERMINAL_NOT_ZERO','source_transfer_permission':'STILL_PENDING_NO_UPLOAD','source_transfer_package':bind(R/'source_transfer_v1/fixed12_native_sources.zip'),'source_bytes':196570456,'source_route':'Windows -> Mac mini -> Linux','possible_billed_payload_bytes_both_hops':393140912,'old_37_66_backup_preserved':True,'new_optimizer_updates':0,'new_GPU_jobs':0,'new_submission_zip':None,'resume_rules':['Never launch controller/observer again; inspect actual processes and existing requests first.','Only first36 actual whole SUCCESS, exit0, null stop and all immutable scope proofs allow37.','Review completed20..23 all64 teacher facts and original critical images; keep20/21 consequential UNKNOWN.','Finalize and register each independently qualified reference, then prepare Linux projection only after all12 eval references and frozen coverage gates.','No source upload without the pending explicit large-flow permission; all transfers via online Mac workspace.','Do not run old successful model/CPU stages again or rewrite any frozen source, old failure, raw, unknown or cost.']}
text=json.dumps(d,ensure_ascii=False,indent=2)
out=R/'root_live_CLI36_reference16_checkpoint_v1.json'
with out.open('x',encoding='utf-8') as f:f.write(text)
print(json.dumps(bind(out),ensure_ascii=False))
