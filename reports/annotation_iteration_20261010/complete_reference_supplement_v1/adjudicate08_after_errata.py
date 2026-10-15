"""Accountable empty visual target after actual student fact correction."""
from pathlib import Path
from datetime import datetime, timezone
import json, hashlib
from PIL import Image

R = Path(__file__).resolve().parent
O = R.parent / 'slot6_silver24_v1'
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bind(p): return {'path': str(p), 'sha256': sha(p)}
def write(p, x):
    with p.open('x', encoding='utf-8') as f: json.dump(x, f, ensure_ascii=False, indent=2)

e_path = R / 'student_reviews/08_WxtbjNsCQ8A_W00.student64_fact_errata_reinspection_v1.json'
e = read(e_path)
assert sha(e_path) == 'ca255ab22bed4b25515d5bcd018574f2ed89cecbaf664d3f6c9138830ace2537'
assert e['is_new_blind_initial'] is False and e['root_fact_correction_exposure'] is True
assert not e['teacher_content_received'] and not e['candidate_predictions_received']
assert sha(e['original_review_path']) == e['original_review_sha256']
receipt_path = O / 'observations/08_WxtbjNsCQ8A_W00/student_views/receipt.json'
receipt = read(receipt_path)
assert sha(receipt_path) == e['machine_binding']['student_receipt_sha256']
assert receipt['normalized_tensor_sha256'] == e['machine_binding']['normalized_tensor_sha256']
rows = e['slot_comparison_inventory']
assert len(rows) == 64 and receipt['patch_inverse_exact'] is True
for i, (row, original) in enumerate(zip(rows, receipt['frames'])):
    for key in ('frame_id', 'path', 'source_ordinal', 'global_seconds_exact', 'local_seconds_exact', 'png_sha256', 'rgb_pixel_sha256'):
        assert row[key] == original[key], (i, key)
    assert row['frame_id'] == f'F{i:02d}' and row['batch_index'] == i // 4
    assert row['tool_supply']['slot'] == i and row['tool_supply']['path'] == row['path']
    assert row['tool_supply']['status'] == 'SUCCESS_IMAGE_RETURNED_AND_EMITTED'
    assert row['tool_supply']['detail'] == 'original'
    assert sha(row['path']) == row['png_sha256'] == row['actual_png_sha256']
    with Image.open(row['path']) as image:
        rgb = image.convert('RGB')
        assert list(rgb.size) == row['size']
        assert hashlib.sha256(rgb.tobytes()).hexdigest() == row['rgb_pixel_sha256'] == row['actual_rgb_pixel_sha256']
    assert row['old_visible_static_fact'] and row['reinspection_visible_static_fact']
native_path = R / 'native_reviews/08_WxtbjNsCQ8A_W00.native_review.json'
native = read(native_path)
assert native['frame_count'] == 64
assert native['teacher_content_received'] is False and native['student_content_received'] is False
assert native['candidatePredictionExposure'] is False
wrapper = R / '08_wxt_w00_independent_native_blind_binding.json'
write(wrapper, dict(status='BOUND_REAL_PRETEACHER_NATIVE64_REVIEW_NOT_NEW_IMAGE_OBSERVATION',
    window_id=native['window_id'], blind_attestation=dict(teacher_content_received=False, candidate_prediction_received=False, student_content_received=False),
    sealed_native_review=bind(native_path), actual_native_images=64, root_not_blind=True, training_admitted=False))
errata_acceptance = R / '08_wxt_w00_student_fact_errata_acceptance.json'
write(errata_acceptance, dict(status='PASS_ROOT_READ_ALL64_ERRATA_AND_RECHECK_ACTUAL64_BINDINGS_NOT_NEW_BLIND_REVIEW',
    utc=datetime.now(timezone.utc).isoformat(), original_blind_review=bind(e['original_review_path']), corrected_nonblind_review=bind(e_path),
    actual_reinspection_by_delegate=64, root_read_all64_comparisons=True, root_current_PNG_RGB_receipt_bindings=64,
    root_direct64_image_inspection=False, original_semantic_error_cause='UNKNOWN', unsupported_black_claims_corrected=e['pure_black_errors'],
    remaining_student_initial_target_observable='UNKNOWN_PRESERVED', teacher_exposure=False, new_model_calls=0, new_optimizer_updates=0))
pre = read(R / '08_wxt_w00_main_preteacher_review.json')
final = dict(status='ROOT_FINAL_COMPLETE_FINITE_EDITORIAL_REFERENCE_ADJUDICATED',
    utc=datetime.now(timezone.utc).isoformat(), window_id=native['window_id'], root_semantic_adjudication_complete=True,
    candidate_prediction_exposure_before_freeze=False, keep_local_exact=[], no_local_exact=[['0','30']], unknown_local_exact=[],
    events=[], boundary_decisions=[], consequential_unknowns=[], explicit_no_highlight=True,
    all_target_boundaries_adjudicated=True, student_observable_complete_target=True, training_admitted=True,
    main_review_assertions={k: True for k in ('direct_visible_facts_checked','all_NO_ranges_explicitly_reviewed','no_audio_content_invented',
        'necessary_preparation_and_result_considered','no_artificial_event_merging','no_candidate_prediction_exposure_before_reference_freeze','student_visibility_checked')},
    evidence=dict(teacher_observation_audit=bind(R / '08_teacher_completed_pair_observation.json'), blind_initial=bind(wrapper),
        blind_student_visibility=bind(e['original_review_path']), student_processor=bind(receipt_path),
        student_fact_errata=bind(e_path), student_fact_errata_acceptance=bind(errata_acceptance), preteacher_main_review=bind(R / '08_wxt_w00_main_preteacher_review.json')),
    actual_root_observation_scope=dict(native_sample_indices=pre['root_actually_viewed_native_samples'],student_sample_indices=pre['root_actually_viewed_student_samples'],
        read_native_static_facts=64,read_original_student_facts=64,read_corrected_student_facts=64,root_direct64_image_review=False),
    all_NO_ranges=pre['decision']['all_NO_ranges'],
    differences_adjudicated=[
        'Original student false black claims are material semantic errors, corrected in a separate exposed erratum. Original blind judgment, original files and UNKNOWN remain unchanged.',
        'Corrected title pixels do not establish a highlight. Title fade, ordinary interview head/mouth movement, and walk toward boxes show no box operation or visually notable result in this finite window.',
        'Student initial UNKNOWN concerns target semantics beyond observations. Root separately adopts a complete empty finite visual editing target after all64 corrected facts, both independent native/student reviews, direct samples and complete lawful teacher observation. It does not claim no highlight at unsampled instants or from unheard speech.',
        'Teacher all-NO agrees but is not the sole truth source. No numerical quota, candidate answer, official score or unseen action determines this empty target.'
    ],
    reference_scope_and_reason='Complete empty finite visual editing silver reference after accountable student fact correction; not human gold or exhaustive native-frame/audio truth.')
write(R / '08_wxt_w00_final_main_review.json', final)
print(json.dumps(dict(status='PASS_ROOT_ADJUDICATION_AND_ERRATA_BINDINGS', final_main_review=bind(R / '08_wxt_w00_final_main_review.json'), new_optimizer_updates=0),ensure_ascii=False))
