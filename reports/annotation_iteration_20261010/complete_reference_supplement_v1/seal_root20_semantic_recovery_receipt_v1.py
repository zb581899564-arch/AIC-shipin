"""Seal actual accepted ROOT20 finite reference, preserving teacher rejection."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

R = Path(__file__).resolve().parent
OLD = R.parent / 'slot6_silver24_v1'

def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def bind(path):
    path = Path(path).resolve(strict=True)
    return {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}

def main():
    reference_path = R / '20_cjibt_w13_complete_reference_v1.json'
    acceptance_path = R / '20_cjibt_w13_complete_reference_v1_acceptance.json'
    review_path = R / 'plan_review' / 'ROOT20_actual_reference_independent_review_v1.json'
    reference = read(reference_path)
    acceptance = read(acceptance_path)
    review = read(review_path)
    plan_path = OLD / 'source_window_plan.json'
    job = next(j for j in read(plan_path)['jobs'] if j['window']['window_id'] == reference['window_id'])
    assert reference['window_id'] == 'cjibtmSLxQ4:SLOT6:13'
    assert reference['reference_kind'] == 'FINITE_OBSERVATION_SILVER_EDITING_ADVICE_NOT_GOLD'
    assert reference['training_admitted'] is False and job['role'] == 'locked_evaluation'
    assert reference['source_sha256'] == job['window']['source_sha256']
    assert acceptance['status'] == 'PASS_BOUND_COMPLETE_FINITE_REFERENCE_NOT_BATCH_ADMISSION'
    assert acceptance['reference'] == bind(reference_path)
    assert acceptance['verified']['window_id'] == reference['window_id']
    assert acceptance['verified']['role'] == 'locked_evaluation'
    assert acceptance['verified']['admitted'] is False
    assert review['status'] == 'PASS_INDEPENDENT_ACTUAL_ROOT20_FINITE_REFERENCE_NOT_TRAINING'
    assert review['reference'] == bind(reference_path)
    assert any(u['first'] == 15 and u['last'] == 18 for u in reference['consequential_unknowns'])
    assert reference['unknown_global_exact'] == [['793793/2000', '249249/625']]
    geometry_path = R / '20_cjibt_w13_root_new_reference_geometry_v1.json'
    geometry = read(geometry_path)
    assert geometry['original_teacher_scope_pass'] is False
    assert geometry['original_teacher_proposal_pass'] is False
    assert geometry['whole_CLI36_pass'] is False
    for evidence in reference['evidence'].values():
        assert bind(evidence['path']) == evidence
    reference_binding = dict(bind(reference_path), window_id=reference['window_id'],
        reference_kind=reference['reference_kind'], source_sha256=reference['source_sha256'],
        source_window=bind(plan_path), training_admitted=False)
    receipt = dict(status='PASS_ROOT20_INDEPENDENT_FINITE_REFERENCE_WITH_UNKNOWN_PRESERVED_NOT_TRAINING',
        utc=datetime.now(timezone.utc).isoformat(), window_id=reference['window_id'],
        reference_binding=reference_binding, original_silver_contract_actual_verified=True,
        original_silver_acceptance=bind(acceptance_path), independent_actual_result_review=bind(review_path),
        original_silver_contract=bind(OLD / 'silver_contract.py'),
        actual_serializer=bind(R / 'build_reference_from_main.py'),
        new_root_geometry=bind(geometry_path), new_root_decision=bind(R / '20_cjibt_w13_root_eval_decision_v1.json'),
        original_teacher_scope_pass=False, original_teacher_proposal_pass=False, whole_CLI36_pass=False,
        training_admitted=False, consequential15_18UNKNOWN_preserved=True,
        known_keep_seconds=acceptance['verified']['known_keep_seconds'],
        known_no_seconds=acceptance['verified']['known_no_seconds'],
        unknown_seconds=acceptance['verified']['unknown_seconds'],
        scientific_batch_training_admission=False, new_model_calls=0, new_optimizer_updates=0,
        source=bind(__file__))
    output = R / '20_cjibt_w13_root_semantic_recovery_receipt_v1.json'
    with output.open('x', encoding='utf-8') as stream:
        json.dump(receipt, stream, ensure_ascii=False, indent=2)
    print(json.dumps({'receipt': bind(output), 'reference_binding': reference_binding}, ensure_ascii=False))

if __name__ == '__main__':
    main()
