"""Bind independently reviewed prospective CLI37, without starting a process."""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

R = Path(__file__).resolve().parent
T = R / 'teacher_expansion' / 'prospective_CLI37_schema_local_v2'

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def bind(path):
    path = Path(path).resolve(strict=True)
    return {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}

def main():
    review_path = R / 'plan_review' / 'CLI37_schema_local_v2_independent_static_review.json'
    review = read(review_path)
    assert review['status'] == 'PASS_INDEPENDENT_PROSPECTIVE_CLI37_V2_STATIC_BEFORE_LAUNCH'
    assert review['execution_binding'] == bind(T / 'execution_code_binding.json')
    receipt_path = R / '20_cjibt_w13_root_semantic_recovery_receipt_v1.json'
    receipt = read(receipt_path)
    assert review['w20_receipt'] == bind(receipt_path)
    assert receipt['status'] == 'PASS_ROOT20_INDEPENDENT_FINITE_REFERENCE_WITH_UNKNOWN_PRESERVED_NOT_TRAINING'
    dry = read(T / 'dry_run_acceptance.json')
    assert dry['execution_binding_sha256'] == bind(T / 'execution_code_binding.json')['sha256']
    assert dry['new_model_calls'] == 0 and dry['new_video_decode'] == 0
    assert dry['routing'] == [{'CLI':37,'jobs':[21,22,23],'core':308,'scope_cores':[104,206,308],
        'parts':19,'max_text_bytes':29249,'argv_units':762}]
    for source in dry['AST']:
        assert bind(source['path'])['sha256'] == source['sha256']
    negative = read(T / 'independent_CPU_negative_acceptance.json')
    assert negative['source_binding_sha256'] == bind(T / 'execution_code_binding.json')['sha256']
    freeze_path = T / 'call37' / 'freeze.json'
    assert dry['freezes'][0]['sha256'] == bind(freeze_path)['sha256']
    freeze = read(freeze_path)
    assert freeze['fixed_job_indices'] == [21,22,23] and freeze['global_cap'] == 37
    assert freeze['timeout_seconds'] == 7200 and freeze['CLI_before'] == 36
    assert not any((R / 'teacher_expansion').rglob('call37/request.json'))
    assert all(not Path(path).exists() for path in freeze['write_whitelist'])
    gate = dict(status='ROOT_APPROVED_START_SCHEMA_LOCAL_FRESH37_FIXED21_23_AFTER_ROOT20_RECOVERY',
        utc=datetime.now(timezone.utc).isoformat(),execution_binding_sha256=bind(T / 'execution_code_binding.json')['sha256'],
        dry_run_sha256=bind(T / 'dry_run_acceptance.json')['sha256'],
        negative_receipt_sha256=bind(T / 'independent_CPU_negative_acceptance.json')['sha256'],
        independent_static_review=bind(review_path), ROOT_w20_complete_independent_semantic_recovery_PASS=True,
        w20_semantic_recovery_receipt=dict(bind(receipt_path),status=receipt['status']),
        w20_reference_binding=receipt['reference_binding'],
        old_teacher_scope_pass=False,old_teacher_proposal_pass=False,old_whole_CLI36_pass=False,
        separate_prospective_root_route=True,fixed_job_indices=[21,22,23],CLI=37,no38=True,no_retry=True,
        scientific_batch_training_admission=False,new_optimizer_updates=0,source=bind(__file__))
    sys.path.insert(0,str(T))
    from launch import verify_w20_recovery
    verify_w20_recovery(gate)
    output = T / 'root_start_admission.json'
    with output.open('x',encoding='utf-8') as stream:
        json.dump(gate,stream,ensure_ascii=False,indent=2)
    print(json.dumps({'gate':bind(output),'status':gate['status'],'process_started':False},ensure_ascii=False))

if __name__ == '__main__':
    main()
