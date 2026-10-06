"""Evidence/resource admission for an explicitly authorized format recovery."""
import argparse
import datetime as dt
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys

from admit_a_pts_stage import sha,read,evidence,require
ROOT = Path('/home/inspur/aic_video_work')
RUN = ROOT/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
CTRL,CODE,REC = RUN/'controller',RUN/'baseline_a_pts_v1',RUN/'baseline_a_format_recovery_v1'
LOCK = '86fc0da7cf631a2afe33c54fb5b66246bba88adfd95c1d8ce80ccbf73522d70d'
VARIANT = 'A_FORMAT_CONSTRAINED_RECOVERY_V1'

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase',choices=['probe','recover','schedule','space'])
    args = parser.parse_args()
    phase = args.phase
    sys.path[:0] = [str(CODE)]
    from run_pts import verify_vendor
    from pts_contract import load_clocks
    verify_vendor()
    require(sha(CODE/'source_lock.json') == LOCK,'frozen production changed')
    version_lock = read(REC/'source_lock.json')
    for name,digest in version_lock['files'].items():
        require(sha(REC/name) == digest,'format recovery source changed')
    helper = read(CTRL/'format_recovery_controller_lock.json')
    for name,digest in helper['files'].items():
        require(sha(CTRL/name) == digest,'format recovery controller changed')
    source_hashes = {n:sha(REC/n) for n in ('inference.py','constrained_json.py')}
    identity = evidence('real_processor_04','real_decoder_02',LOCK)
    n8 = CODE/'nontest_e2e_02/independent_validation.json'
    require(read(n8)['status'] == 'PASS_INDEPENDENT_STRICT_VALIDATION' and all(read(n8)['checks'].values()),
        'base NONTEST8 regression absent')
    identity.update(non_test_e2e_pass=True,non_test_evidence_sha256=sha(n8))
    receipt = read(RUN/'baseline_pts_v4'/('nontest_registry_01' if phase == 'probe' else 'scan_01')/'reaudit_receipt.json')
    manifest_path,registry_path = Path(receipt['clean_manifest']['path']),Path(receipt['clock_registry']['path'])
    require(sha(manifest_path) == receipt['clean_manifest']['sha256']
        and sha(registry_path) == receipt['clock_registry']['sha256'], 'source clocks changed')
    manifest = read(manifest_path)
    load_clocks(manifest,registry_path,sha(registry_path))
    probe_path = REC/'probe_01/report.json'
    if phase != 'probe':
        probe = read(probe_path)
        require(probe['status'] == 'PASS_REAL_NONTEST_FORMAT_CONSTRAINT_ONLY'
            and probe['cases'] == 10 and probe['failures'] == 0 and probe['source_hashes'] == source_hashes,
            'actual same-version ten-case non-test constrained generation absent')
        identity.update(format_probe_evidence_path=str(probe_path),format_probe_evidence_sha256=sha(probe_path))
    if phase in ('schedule','space'):
        rec_report_path = REC/'recover_01/report.json'
        rec_report = read(rec_report_path)
        require(rec_report['status'] == 'PASS_FIVE_PARSE_FAILURE_REGENERATIONS'
            and rec_report['source_hashes'] == source_hashes and rec_report['successful_windows_unchanged'] == 516
            and rec_report['total_videos'] == 426 and rec_report['total_windows'] == 521
            and rec_report['recovered_windows'] == 5 and rec_report['remaining_invalid_windows'] == 0
            and sha(REC/'recover_01/temporal.jsonl') == rec_report['output_sha256'],
            'failed windows are not completely recovered while preserving successful output')
        require(read(CTRL/'rematch_format_recover_01.resource.json')['status'] == 'completed',
            'recovery shared runner did not succeed')
        identity.update(format_recovery_evidence_path=str(rec_report_path),
            format_recovery_evidence_sha256=sha(rec_report_path))
    run_dir = REC/(phase+'_01') if phase in ('probe','recover') else CODE/'rematch_e2e_recovery_01'
    stages = {'probe':['temporal'],'recover':['temporal'],
        'schedule':['preflight','select','shots','anchors'],'space':['spatial','compose','package']}[phase]
    planned,max_seconds = (67108864,1800) if phase in ('probe','recover') else (536870912,7200)
    reason = 'ten fixed non-test generation cases; no semantic labels or test inputs' if phase == 'probe' else \
        'only five preserved parse-failed windows; 516 successful windows copied unchanged; one grammar generation attempt' \
        if phase == 'recover' else 'complete426 CPU selection/shot/anchor scheduling; source media remain unchanged'
    scheduling = None
    if phase == 'space':
        require(read(CTRL/'rematch_format_schedule_01.resource.json')['status'] == 'completed',
            'complete scheduling did not succeed')
        selection,shots,anchors = [read(run_dir/(s+'.stage.json')) for s in ('select','shots','anchors')]
        frames,calls = selection['selected_frames'],anchors['anchor_calls']
        require(frames == shots['frames'] == anchors['selected_frames'] and calls > 0
            and sha(run_dir/'selected.jsonl') == shots['selected_sha256'] == anchors['selected_sha256']
            and sha(run_dir/'shots.jsonl') == shots['output_sha256'] == anchors['shots_sha256']
            and sha(run_dir/'anchor_requests.jsonl') == anchors['output_sha256'],'actual scheduling inconsistent')
        per_anchor = read(CODE/'nontest_e2e_02/spatial.stage.json')['wall_seconds']/68
        max_seconds = math.ceil(per_anchor*calls*1.8+1200)
        planned = sum((run_dir/f).stat().st_size for f in ('selected.jsonl','shots.jsonl','anchor_requests.jsonl'))*3 \
            +frames*1536+calls*4096+33554432
        reason = f'actual {frames} selected frames/{calls} anchors, measured {per_anchor:.6f}s per anchor plus registered decode/teardown margin'
        scheduling = dict(selected_frames=frames,anchor_requests=calls,measured_seconds_per_anchor=per_anchor)
    work = int(subprocess.check_output(['du','-s','-B1',str(ROOT)],text=True).split()[0])
    free = shutil.disk_usage(ROOT).free
    compute = subprocess.check_output(['nvidia-smi','--query-compute-apps=pid,used_memory','--format=csv,noheader'],text=True).strip()
    require(not compute and not (ROOT/'improvement_round1/active_gpu_job.json').exists(),'live shared GPU busy')
    require(work+planned <= read(ROOT/'resource_policy.json')['added_disk_budget_gib']*2**30 and free >= planned,
        'capacity does not cover actual planned outputs')
    result = dict(phase=phase,recovery_variant=VARIANT,variant='A_NATIVE_PTS_COMPAT_V1',
        stage='A_PTS_NONTEST_E2E' if phase == 'probe' else 'A_PTS_REMATCH426_INFERENCE',
        authorized=True,user_authorization='2026-10-06 user explicitly instructed solve the failures and complete candidate',
        admitted_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
        manifest_path=str(manifest_path),manifest_sha256=sha(manifest_path),clock_registry_path=str(registry_path),
        clock_registry_sha256=sha(registry_path),source_lock_sha256=LOCK,
        recovery_source_hashes=source_hashes,recovery_controller_lock_sha256=sha(CTRL/'format_recovery_controller_lock.json'),
        run_dir=str(run_dir),allowed_stages=stages,resource_preflight_pass=True,shared_gpu_queue_approved=True,
        disk_peak_within_80gib=True,budget_runner_required=True,space_inference_admitted=phase == 'space',
        planned_output_bytes=planned,single_job_max_seconds=max_seconds,capacity_reason=reason,scheduling=scheduling,
        original_successes_must_be_unchanged=True,posthoc_clipping_or_deleting_or_empty=False,
        prompt_or_model_or_space_threshold_changed=False,formal_C_training_admitted=False,
        competition_upload_authorized=False,live_resources=dict(work_bytes=work,free_bytes=free,compute=compute),**identity)
    with (CTRL/('format_'+phase+'_01.admission.json')).open('x') as stream:
        json.dump(result,stream,indent=2)
        stream.write('\n')
    print(json.dumps(dict(phase=phase,scope=stages,scheduling=scheduling,single_job_max_seconds=max_seconds,
        planned_output_bytes=planned,upload_authorized=False)),flush=True)
