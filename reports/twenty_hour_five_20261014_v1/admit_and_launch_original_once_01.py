"""Main-reviewed bounded risk admission after real technical completion only."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess

R = Path('/home/inspur/aic_video_work/twenty_hour_five_20261014_v1')
P = R / 'temporal_family_native_package_v3'
W = R / 'cpu_finalization_control7_03'
C = R / 'temporal_global_recovery_control7_v1'
PY = '/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'


def ref(path):
    return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def read(path):
    return json.loads(path.read_text())


def save(path, value):
    with path.open('x', encoding='utf8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
        f.flush()
        os.fsync(f.fileno())


def main():
    assert socket.gethostname() == 'inspur-NP5570M5'
    natural = read(W / 'binder/natural_terminal.json')
    technical = read(P / 'technical_preparation_receipt.json')
    global_done = read(C / 'exports_01/global_completion.json')
    assert natural['exit_code'] == 0 and natural['naturally_completed'] is True
    assert natural['process_was_killed_or_restarted'] is False
    assert natural['completion_ref'] == ref(P / 'technical_preparation_receipt.json')
    assert technical['status'] == 'TECHNICAL_PACKAGE_BINDINGS_READY_NO_ADMISSION_NO_ZIP_NO_QUALITY_CLAIM'
    assert (technical['source_count'], technical['actual_MODEL_proofs'], technical['structural_no_MODEL_proofs']) == (426, 1992, 3)
    assert technical['scientific_quality_claim'] is False and technical['old_success_files_or_failed_gates_modified'] is False
    assert global_done['engineering_failed_requests'] == global_done['missing_requests'] == 0
    assert global_done['test_GT_or_annotation_read'] is False and global_done['optimizer_updates'] == 0
    assert ref(P / 'code/package_family.py')['sha256'] == '9a0369a1034b96e16a570ca4864032beeb606842b1fc897e833c492094c7962e'
    assert ref(P / 'code/combine_events.py')['sha256'] == '8e508a7d8065edd0b282d2c235cdb2619730a2bce6bb416e82ea1240668b6ce6'
    assert ref(P / 'protocol.json')['sha256'] == 'fe075b5f38d7174efa980f22104c1c80cff1ba50fea000a5096a20cf12979143'
    assert ref(P / 'official_rule_check.json')['sha256'] == '7450752081c20971616444c43c21e57d44cf09d552ef5247c9c97d9e7eb9df68'
    assert not (W / 'original').exists() and not (W / 'original_wrapper_launch.json').exists()
    assert not (P / 'package_admission.json').exists() and not (P / 'completion.json').exists()
    scope = dict(schema='MAIN_BOUNDED_KNOWN_SEVERE_FACT_VETO_REVIEW_V1',
        utc=dt.datetime.now(dt.timezone.utc).isoformat(),
        purpose='Explicit unknown-effect risk packages under the human five-new-package authorization',
        independent_static_review='final_package_admission_review_01; original frozen combine and renderer mechanisms',
        technical_receipt_ref=ref(P / 'technical_preparation_receipt.json'),
        actual_production_completion_ref=ref(C / 'exports_01/global_completion.json'),
        fixed_protocol_ref=ref(P / 'protocol.json'), rule_check_ref=ref(P / 'official_rule_check.json'),
        bounded_veto_evidence=[
            'Invalid decisions and escaped native endpoints are engineering failures, not successful fallbacks',
            'KEEP/UNKNOWN and paired-conflict guards preserve the original accepted cut',
            'Original D8 padding eligibility is computed from the original event length',
            'SOURCE widening is limited to the actually changed REFINE side and declared as unknown risk',
            'VERIFY drops an event, overlapping events retain their union, empty source restores D8',
            'Actual renderer must reproduce D8 122050 frames, retain surviving D8 boxes, check426/PTS/11strict',
            'Fixed pre-result priorities and real canonical differences determine publication, not scores',
            'Old rejected base-only/spatial/shrink recipes and scientific failures are not reclassified or used'],
        known_severe_fact_or_engineering_veto_triggered=False,
        veto_scope='Existing specific known facts and fixed mechanism/identity gates only; UNKNOWN is not evidence of safety',
        uncertainty=['No dense human highlight truth qualification for these production outputs',
                     'Frame removals may reduce recall; source padding may exceed local observation support',
                     'Engineering success and a static bounded veto cannot prove official score improvement'],
        risk_quality_status='UNVERIFIED_EXPLICIT_RISK', scientific_quality_claim=False,
        formal_test_video_or_GT_examined_for_this_decision=False, leaderboard_used_to_choose_arm=False,
        human_authorization_ref=ref(P / 'authorization.json'), peer_messages_sent=0,
        original_C6_failure_preserved=True, new_model_or_first_QA_calls=0)
    save(P / 'main_risk_veto_review_01.json', scope)
    permit = dict(status='PASS_COMPLETE_REAL_TEMPORAL_PRODUCTION_AND_EXPLICIT_RISK_PACKAGE_ADMISSION',
        model_parameters=8782459120, old_scientific_failed_gates_changed=False,
        known_severe_degradation_veto_passed=True, test_labels_or_manual_edits_used=False,
        source_package_lock_sha256=ref(P / 'source_package_lock.json')['sha256'],
        production_completion_sha256=ref(C / 'exports_01/global_completion.json')['sha256'],
        bounded_risk_review_ref=ref(P / 'main_risk_veto_review_01.json'),
        scientific_quality_claim=False, official_score='UNKNOWN',
        approval_is_not_official_special_permission=True, original_C6_failure_not_reclassified=True,
        original_failed_scientific_gates_preserved=True, no_new_experiment_or_model=True,
        utc=dt.datetime.now(dt.timezone.utc).isoformat())
    save(P / 'package_admission.json', permit)
    argv = [PY, '-B', '-u', str(W / 'run_once_01.py'), '--stage', 'original']
    with (W / 'original_wrapper.log').open('xb') as log:
        child = subprocess.Popen(argv, cwd=R, env=dict(os.environ, CUDA_VISIBLE_DEVICES='', PYTHONDONTWRITEBYTECODE='1'),
                                 stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    ticks = int((Path('/proc') / str(child.pid) / 'stat').read_text().rsplit(')', 1)[1].split()[19])
    value = dict(pid=child.pid, start_ticks=ticks, argv=argv, admission_ref=ref(P / 'package_admission.json'),
                 utc=dt.datetime.now(dt.timezone.utc).isoformat())
    save(W / 'original_wrapper_launch.json', value)
    print(json.dumps(value))


if __name__ == '__main__':
    main()
