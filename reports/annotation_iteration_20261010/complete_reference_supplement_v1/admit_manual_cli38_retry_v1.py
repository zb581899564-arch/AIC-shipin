"""ROOT actual new routing review and one human-authorized retry gate."""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

R = Path(__file__).resolve().parent
OLD = R / 'teacher_expansion' / 'prospective_CLI37_schema_local_v2'
T = R / 'teacher_expansion' / 'manual_CLI38_retry_v1'
def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))
def bind(path):
    path = Path(path).resolve(strict=True)
    return {'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
def project(value):
    if isinstance(value,str):
        return value.replace(str(OLD / 'call37'),str(T / 'call38'))
    if isinstance(value,list):
        return [project(x) for x in value]
    if isinstance(value,dict):
        return {k:project(v) for k,v in value.items()}
    return value

def main():
    binding = read(T / 'execution_code_binding.json')
    for path,sha in binding['sources'].items():
        assert bind(path)['sha256'] == sha
    dry = read(T / 'dry_run_acceptance.json')
    assert dry['status'] == 'PASS_MANUAL38_AST_TEXT_PATH_PROJECTION_SHA_PREP_ONLY_NO_MODEL'
    assert dry['source_binding_sha256'] == bind(T / 'execution_code_binding.json')['sha256']
    negative = read(T / 'independent_CPU_negative_acceptance.json')
    assert negative['source_binding_sha256'] == bind(T / 'execution_code_binding.json')['sha256']
    assert negative['status'].startswith('PASS_') and negative['new_model_calls'] == 0
    a = T / 'call38'
    old = OLD / 'call37'
    index = read(a / 'index.json')
    projected = project(read(old / 'index.json'))
    assert index['windows'] == projected['windows']
    assert read(a / 'literal_execution_parameters.json') == project(read(old / 'literal_execution_parameters.json'))
    science = (a / 'science_verbatim_program_only.txt').read_bytes()
    assert science == (old / 'science_verbatim_program_only.txt').read_bytes()
    assert Path(index['main_instruction_path']).read_bytes().count(science) == 1
    assert all(bind(T / name)['sha256'] == bind(OLD / name)['sha256'] for name in ('common.py','engine.py','run_call.py'))
    for fragment in index['text_fragments']:
        text = Path(fragment['path']).read_bytes()
        assert hashlib.sha256(text).hexdigest() == fragment['input_sha256']
        assert len(text) < 30000 and text.endswith(b'\n') and b'\r' not in text
        assert bind(fragment['expected_ACK_path'])['sha256'] == fragment['expected_ACK_sha256']
    freeze = read(a / 'freeze.json')
    assert freeze['CLI_before'] == 37 and freeze['CLI_after'] == 38 and freeze['global_cap'] == 38
    assert freeze['fixed_job_indices'] == [21,22,23] and freeze['timeout_seconds'] == 7200
    assert freeze['expected_core_tool_calls'] == 308 and freeze['scope_core_counts'] == [104,206,308]
    assert dry['freeze_sha256'] == bind(a / 'freeze.json')['sha256']
    assert all(not Path(path).exists() for path in freeze['write_whitelist'])
    assert not any((R / 'teacher_expansion').rglob('call38/request.json'))
    for path,sha in freeze['inputs'].items():
        assert bind(path)['sha256'] == sha
    recovery_path = R / '20_cjibt_w13_root_semantic_recovery_receipt_v1.json'
    recovery = read(recovery_path)
    gate = dict(status='ROOT_APPROVED_START_MANUAL_CLI38_ONCE_FIXED21_23_AFTER_ZERO_TOOL_LOCATION37',
        utc=datetime.now(timezone.utc).isoformat(),execution_binding_sha256=bind(T / 'execution_code_binding.json')['sha256'],
        dry_run_sha256=bind(T / 'dry_run_acceptance.json')['sha256'],
        negative_receipt_sha256=bind(T / 'independent_CPU_negative_acceptance.json')['sha256'],
        manual_user_authorization=bind(R / 'manual_CLI38_user_retry_authorization_v1.json'),
        ROOT_w20_complete_independent_semantic_recovery_PASS=True,
        w20_semantic_recovery_receipt=dict(bind(recovery_path),status=recovery['status']),
        w20_reference_binding=recovery['reference_binding'],CLI=38,global_cap=38,no39=True,
        automatic_retry=False,fixed_job_indices=[21,22,23],timeout_seconds=7200,
        prior37_actual_ERROR_preserved=True,IP_recovery_not_yet_verified=True,
        scientific_batch_training_admission=False,new_optimizer_updates=0,source=bind(__file__))
    sys.path.insert(0,str(T))
    from launch import verify_w20_recovery,verify_manual38_admission
    verify_w20_recovery(gate)
    verify_manual38_admission(gate)
    review = dict(status='PASS_ROOT_MANUAL38_SOURCE_AND_EXACT_SCIENCE_ROUTING_BEFORE_LAUNCH',
        utc=datetime.now(timezone.utc).isoformat(),execution_binding=bind(T / 'execution_code_binding.json'),
        window_and_literal_projection_exact=True,scientific_six_paragraphs_byte_exact=True,
        engine_common_run_call_byte_exact=True,original37_region_error_preserved=True,
        original_24_schema_and_51_runtime_tests_not_repeated=True,
        typed_manual_retry_and_w20_functions_actual_checked=True,
        new_model_calls=0,new_optimizer_updates=0,teacher_success=False,
        IP_recovery_verified=False,source=bind(__file__))
    review_path = R / 'plan_review' / 'ROOT_manual_CLI38_retry_source_review_v1.json'
    with review_path.open('x',encoding='utf-8') as stream:
        json.dump(review,stream,ensure_ascii=False,indent=2)
    gate['root_actual_source_review'] = bind(review_path)
    output = T / 'root_start_admission.json'
    with output.open('x',encoding='utf-8') as stream:
        json.dump(gate,stream,ensure_ascii=False,indent=2)
    print(json.dumps({'gate':bind(output),'review':bind(review_path),'process_started':False},ensure_ascii=False))

if __name__ == '__main__':
    main()
