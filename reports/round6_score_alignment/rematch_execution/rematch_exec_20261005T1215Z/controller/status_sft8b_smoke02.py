"""Read-only numerical status; no video, target text or model outputs displayed."""
import datetime as dt
import json
from pathlib import Path

RUN = Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
CTRL = RUN/'controller'
OUT = RUN/'temporal_sft8b_v1/smoke_01'

def optional(path):
    return json.loads(path.read_text()) if path.exists() else None

active = optional(Path('/home/inspur/aic_video_work/improvement_round1/active_gpu_job.json'))
owned = active if active and active.get('name') == 'rematch_sft8b_smoke_02' else None
report = optional(OUT/'train_report.json')
resource = optional(CTRL/'rematch_sft8b_smoke_02.resource.json')
count, last = 0, None
evidence = OUT/'example_evidence.jsonl'
if evidence.exists():
    for line in evidence.open():
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        count += 1
        last = {key: item[key] for key in ['effective_batch', 'loss', 'expanded_sequence_length']}
updates = []
log = CTRL/'rematch_sft8b_smoke_02.log'
if log.exists():
    for line in log.read_text(errors='replace').splitlines():
        try:
            item = json.loads(line)
        except (ValueError, TypeError):
            continue
        if isinstance(item, dict) and 'optimizer_step' in item:
            updates.append({key: item[key] for key in ['optimizer_step', 'effective_batches', 'gradient_norm', 'changed_lora_tensors']})
status = dict(checked_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
    stage=report['status'] if report else 'RUNNING_REGISTERED_SFT_SMOKE' if owned else 'NO_ACTIVE_OWNED_JOB_NO_FINAL_REPORT',
    observed_effective_batches=count, observed_optimizer_updates=len(updates), planned_effective_batches=80,
    planned_optimizer_updates=5, last_numeric_evidence=last, observed_updates=updates,
    owned_child_pid=owned.get('child_pid') if owned else None,
    owned_child_process_exists=bool(owned and Path('/proc/'+str(owned.get('child_pid'))).exists()),
    sampled_peak_memory_mib=owned.get('sampled_peak_memory_mib') if owned else None,
    formal_c_bce_admitted=False, full_training_completed=False, uploaded=False)
if report:
    status['final_report'] = {key: report[key] for key in ['status', 'optimizer_steps', 'effective_batches', 'wall_seconds',
        'base_frozen', 'vision_frozen', 'adapter_reload_succeeded', 'adapter_model_sha256', 'failure'] if key in report}
if resource:
    status['final_resource'] = {key: resource[key] for key in ['status', 'exit_code', 'charged_seconds']}
addendum = optional(RUN/'temporal_sft8b_v1/saved_adapter_check_01/verification_report.json')
verification_resource = optional(CTRL/'rematch_sft8b_saved_adapter_check_01.resource.json')
if active and active.get('name') == 'rematch_sft8b_saved_adapter_check_01':
    status['stage'] = 'VERIFYING_SAVED_FIVE_UPDATE_ADAPTER_NO_NEW_UPDATES'
    status['verification_child_pid'] = active.get('child_pid')
    status['verification_elapsed_seconds'] = active.get('elapsed_seconds')
if addendum:
    status['saved_adapter_addendum'] = {key: addendum[key] for key in ['status', 'exact_reloaded_language_modules',
        'reloaded_lora_tensors', 'adapter_model_sha256', 'adapter_reload_succeeded', 'failure',
        'original_training_freeze_evidence_kind', 'wall_seconds'] if key in addendum}
    if addendum['status'] == 'PASS_SAVED_ADAPTER_SEMANTIC_RELOAD_ADDENDUM':
        status['stage'] = 'PASS_FIVE_UPDATE_SMOKE_WITH_RELOAD_ADDENDUM' if verification_resource and \
            verification_resource.get('status') == 'completed' and verification_resource.get('exit_code') == 0 else \
            'RELOAD_ADDENDUM_PASS_WAITING_WRAPPER_FINALIZATION'
    else:
        status['stage'] = 'STOP_SAVED_ADAPTER_RELOAD_ADDENDUM'
if verification_resource:
    status['saved_adapter_verification_resource'] = {key: verification_resource[key] for key in ['status', 'exit_code', 'charged_seconds']}
print(json.dumps(status), flush=True)
