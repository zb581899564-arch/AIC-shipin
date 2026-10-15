"""Independent L16 CPU package only after completed fixed human proxy gates."""
import json
import subprocess
import sys
import zipfile
from collections import defaultdict
from fractions import Fraction as F
from pathlib import Path

from stage_common_04 import read,sha,save
from deploy_direct_media_05 import REPORT
from qualify_l16_08 import admission as export_admission,OUT as COMPARISON,EXTERNAL
from lead_guard_v2 import window_spans
ROOT=Path(__file__).resolve().parents[2]
PRIOR=ROOT/'reports/boundary_refinement_20261012_v1'
INPUT=PRIOR/'input_01'
DEPS=PRIOR/'input_dependencies'
PARAMETER_VALIDATOR=ROOT/'improvement/reliable_reference_v1/validate_parameter_field.py'
sys.path.insert(0,str(ROOT/'improvement/boundary_refinement_v1'))
from intervals import expanded_windows,native_membership

def rows(path):
    with Path(path).open(encoding='utf-8') as f:
        return [json.loads(line) for line in f if line.strip()]


def write_rows(path, values):
    with Path(path).open('x', encoding='utf-8') as f:
        for value in values:
            f.write(json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)+'\n')


def keymap(values):
    keys = {(row['video_id'], p['frame']): p['bboxes'] for row in values for p in row['predictions']}
    if len(keys) != sum(len(row['predictions']) for row in values):
        raise ValueError('Duplicate source frame predictions')
    return keys


def admission():
    export_admission() # All transferred completed evidence, no test membership yet.
    result=read(COMPARISON/'result.json')
    if result['status']!='PASS_L16_FIXED_SCREEN_FACT_AND_CONFIRM_RISK_ADMISSION' or not result['qualified'] or not result['no_threshold_retuning']:
        raise ValueError('Fixed L16 screen and confirmation must actually pass')
    for key,name in [('screen_sha256','screen_result.json'),('confirm_sha256','confirm_result.json'),('selection_sha256','selection_before_confirm.json'),('launch_sha256','launch_claim.json')]:
        if result[key]!=sha(COMPARISON/name):raise ValueError('Frozen actual comparison evidence changed')
    for name in ['screen_result.json','confirm_result.json']:
        value=read(COMPARISON/name)
        if not value['original_fixed_gates_pass'] or value['actual_changed_sources']<3:raise ValueError('Original group quality/activation gate failed')
    launch=read(COMPARISON/'launch_claim.json')
    for key,name in [('script_sha256','qualify_l16_08.py'),('metric_sha256','evaluate_l16_intervals_07.py'),('interval_rule_sha256','lead_guard_v2.py')]:
        if launch[key]!=sha(Path(__file__).with_name(name)):raise ValueError('Completed comparison/rule code changed')
    rule=read(REPORT/'official_rule_check_before_package_09.json')
    if not rule['official_current_sources_rechecked'] or not rule['automatic_uniform_boundary_interpretation_allowed'] or rule['max_inference_parameters_b']!=9 or not rule['test_labeling_training_prohibited']:
        raise ValueError('Fresh official rules review required before packaging')
    return [COMPARISON/name for name in ['result.json','screen_result.json','confirm_result.json','selection_before_confirm.json','launch_claim.json']]+[
        REPORT/'official_rule_check_before_package_09.json',REPORT/'followup_fact_veto_02.json',EXTERNAL/'transfer_acceptance.json',
        *[EXTERNAL/name for name in read(EXTERNAL/'transfer_acceptance.json')['manifest']],
        ROOT/'reports/reliable_reference_20261012_v1/coverage_diagnostic_01.json',PRIOR/'developer_readonly_export.json']


def main():
    arm='L16'
    bound=list(admission())
    name='LONG16_LEAD025_8B'
    padding=dict(base_pre_exact='3/4',extra_pre_exact='1/4',minimum_raw_length_for_extra_pre='16',
        base_post_exact='1/2',extra_post_exact='1/4',minimum_raw_length_for_extra_post='8')
    registration_path=REPORT/'production_registration_L16_09.json'
    save(registration_path,dict(candidate=name,arm=arm,padding_exact=padding,
        confirmation_sha256=sha(COMPARISON/'result.json'),selection_before_production_membership=True,
        baseline='D8_USER_REPORTED40.44',model_parameters=8782459120,new_model_calls=0,optimizer_updates=0,official_score='UNKNOWN'))
    prior_lock_path = PRIOR/'production_source_lock.json'
    old_lock = read(prior_lock_path)
    for path, digest in old_lock['files'].items():
        if sha(path) != digest:
            raise ValueError('Accepted original production input changed: '+path)
    baseline_path = ROOT/'deliveries/DURATION_GUARD_D8_8B_20261013/candidate_DURATION_GUARD_D8_8B.zip'
    if sha(baseline_path) != '8aec42ae06a8cacab93aa8e052d89d5df41dc57e56d73a79cdef6dd02c6cb4ad':
        raise ValueError('User-reported D8 40.44 baseline changed')
    bound += [registration_path, prior_lock_path, baseline_path, Path(__file__), PARAMETER_VALIDATOR,
        REPORT/'FOLLOWUP_PROTOCOL_02.md', REPORT/'NATIVE_MAPPING_CONTRACT_03.md',
        Path(__file__).with_name('qualify_l16_08.py'), Path(__file__).with_name('lead_guard_v2.py')]
    lock_path = REPORT/('production_source_lock_'+arm+'_01.json')
    save(lock_path, dict(inherited_files=old_lock['files'],
        new_files={str(path.resolve()): sha(path) for path in bound},
        model_parameters=8782459120, candidate=name, padding_exact=padding,
        original_reference_failed_preserved=True, new_model_calls=0, new_optimizer_updates=0))
    out = REPORT/('candidate_'+arm+'_01')
    out.mkdir(exist_ok=False)
    save(out/'launch_claim.json', dict(source_lock_sha256=sha(lock_path),
        purpose='ONE_FROZEN_L16_NEW20_CONFIRMED_RISK_PACKAGE', new_model_calls=0))
    with zipfile.ZipFile(baseline_path) as z:
        if z.namelist() != ['predictions.jsonl'] or z.testzip() is not None:
            raise ValueError('Baseline package member/CRC changed')
        baseline = keymap([json.loads(line) for line in z.read('predictions.jsonl').splitlines()])
    if len(baseline) != 122050:
        raise ValueError('Baseline frame count changed')
    metadata = read(INPUT/'metadata.json')
    meta = {row['video_id']: row for row in metadata['records']}
    clocks = read(INPUT/'clocks.json')
    temporal = read(INPUT/'temporal_inputs.json')
    original = {row['video_id']: row for row in temporal['records']}
    ids = {str(i) for i in range(426)}
    if not (len(meta) == len(original) == len(clocks) == 426 and set(meta) == set(original) == set(clocks) == ids):
        raise ValueError('Full426 native source denominator changed')
    field_rows = rows(INPUT/'full_selected.jsonl')
    fields = {(row['video_id'], row['source_frame']): row for row in field_rows}
    if len(fields) != len(field_rows) or len(fields) != 234158:
        raise ValueError('Accepted full-source spatial field changed')
    field_frames = defaultdict(list)
    for row in field_rows:
        source = meta[row['video_id']]
        if (row['source_path'] != source['source_path'] or row['source_n_frames'] != source['n_frames'] or
                row['source_width'] != source['width'] or row['source_height'] != source['height'] or
                row['target_ratio_wh'] != source['targetRatioWH']):
            raise ValueError('Spatial field source geometry/provenance changed')
        field_frames[row['video_id']].append(row['source_frame'])
    target, reproduced, core, proofs = set(), set(), set(), []
    if sum(len(row['windows']) for row in original.values()) != temporal['windows'] or temporal['windows'] != 521:
        raise ValueError('Accepted521 original temporal windows changed')
    for vid in sorted(meta):
        clock = clocks[vid]
        tick = F(clock['raw_time_base'])
        origin = clock['raw_first_pts_ticks']*tick
        points = [p*tick-origin for p in clock['native_pts_ticks']]
        if len(points) != meta[vid]['n_frames'] or points[0] != 0 or any(a >= b for a,b in zip(points,points[1:])):
            raise ValueError('Complete original native source clock changed')
        ordinals = sorted(field_frames[vid])
        if ordinals != list(range(ordinals[0], ordinals[-1]+1)):
            raise ValueError('Frozen full-source field has a hole')
        domain = (ordinals[0], ordinals[-1]+1)
        windows = original[vid]['windows']
        for window in windows:
            if (window['clock_record_sha256'] != clock['clock_record_sha256'] or
                    window['original_status'] != ('MODEL_OK' if window['segments'] else 'LEGAL_EMPTY')):
                raise ValueError('Original actual time response failed or changed')
        old = native_membership(points, window_spans(windows, 'D8_BASELINE'), domain)
        new = native_membership(points, window_spans(windows, 'L16'), domain)
        original_core = native_membership(points, expanded_windows(windows, '0', '0'), domain)
        # Independently compare bisect membership with the direct exact PTS predicate.
        spans = window_spans(windows, 'L16')
        direct = {i for i,p in enumerate(points) if domain[0] <= i < domain[1] and any(a <= p < b for a,b in spans)}
        if new != direct or not original_core <= old <= new:
            raise ValueError('Exact native predicate or baseline retention failed')
        reproduced.update((vid,i) for i in old)
        target.update((vid,i) for i in new)
        core.update((vid,i) for i in original_core)
        proofs.append(dict(video_id=vid, n_frames=len(points), field_domain=list(domain),
            baseline_frames=len(old), candidate_frames=len(new), added=len(new-old), removed=0,
            independent_pts_predicate_equals_bisect=True))
    if reproduced != set(baseline) or len(core) != 102112 or not core <= target or target == reproduced or not target <= set(fields):
        raise ValueError('Full baseline reproduction/core retention/new prediction difference failed')
    full = rows(INPUT/'full_predictions.jsonl')
    boxes = keymap(full)
    if set(boxes) != set(fields) or any(boxes[key] != value for key,value in baseline.items()):
        raise ValueError('Accepted baseline boxes changed')
    selected = [fields[key] for key in sorted(target)]
    predictions = [dict(row, model_params_b=8.78245912,
        predictions=[p for p in row['predictions'] if (row['video_id'],p['frame']) in target]) for row in full]
    provenance = [row for row in rows(INPUT/'full_provenance.jsonl') if (row['video_id'],row['source_frame']) in target]
    if len(provenance) != len(target) or any(not row['predictions'] for row in predictions):
        raise ValueError('Full nonempty426/provenance coverage failed')
    sys.path[:0] = [str(DEPS), str(INPUT/'validator')]
    from package_contract import validate_predictions, package
    geometry = validate_predictions(read(DEPS/'legacy_spatial_manifest.json')['manifest'],
        [{k:v for k,v in row.items() if k != 'model_params_b'} for row in predictions], target, provenance)
    for stem, values in [('predictions',predictions), ('selected',selected), ('provenance',provenance)]:
        write_rows(out/(stem+'.jsonl'), values)
    save(out/'metadata.json', metadata)
    save(out/'native_selection_acceptance.json', dict(rows=proofs, baseline_frames=len(baseline),
        candidate_frames=len(target), added=len(target-reproduced), removed=0,
        original_core_frames=len(core), all_retained_baseline_boxes_unchanged=True,
        source_lock_sha256=sha(lock_path)))
    del fields, field_rows, boxes, full, selected, clocks, temporal, original
    subprocess.run([sys.executable,'-B',str(PARAMETER_VALIDATOR),str(out/'predictions.jsonl'),
                    str(out/'parameter_validation.json')],check=True)
    pending = out/('candidate_'+name+'.PENDING.zip')
    packaged = package(out/'predictions.jsonl', pending)
    subprocess.run([sys.executable,'-B',str(INPUT/'validator/independent_validate.py'),
        '--strict-loader-root',str(INPUT/'validator/frozen_strict_loader'),'--metadata',str(out/'metadata.json'),
        '--selected',str(out/'selected.jsonl'),'--predictions',str(out/'predictions.jsonl'),
        '--provenance',str(out/'provenance.jsonl'),'--zip',str(pending),
        '--report',str(out/'independent_validation.json')],check=True)
    validation = read(out/'independent_validation.json')
    if (len(validation['checks']) != 11 or not all(validation['checks'].values()) or
            validation['video_records'] != 426 or validation['prediction_frames'] != len(target) or
            validation['zip_sha256'] != sha(pending) or packaged['zip_sha256'] != sha(pending) or
            validation['predictions_sha256'] != sha(out/'predictions.jsonl')):
        raise ValueError('Independent11strict/package acceptance failed')
    actual_current = keymap(predictions)
    for history in list((ROOT/'deliveries').rglob('candidate_*.zip'))+list(REPORT.glob('candidate_*/candidate_*.zip')):
        if history.resolve() == pending.resolve():
            continue
        if sha(history) == sha(pending):
            raise ValueError('Candidate duplicates a prior ZIP')
        with zipfile.ZipFile(history) as z:
            if z.namelist() == ['predictions.jsonl'] and __import__('hashlib').sha256(z.read('predictions.jsonl')).hexdigest() == sha(out/'predictions.jsonl'):
                raise ValueError('Candidate duplicates historical prediction content')
            if z.namelist() == ['predictions.jsonl'] and keymap([json.loads(line) for line in z.read('predictions.jsonl').splitlines()]) == actual_current:
                raise ValueError('Candidate duplicates actual historical frame and bbox predictions')
    final = out/('candidate_'+name+'.zip')
    pending.rename(final)
    receipt = dict(status='PASS_ONE_NEW_L16_CONFIRMED_RISK_ZIP', candidate=name, arm=arm,
        padding_exact=padding, zip_path=str(final.resolve()), bytes=final.stat().st_size, sha256=sha(final),
        frames=len(target), added=len(target-reproduced), removed=0, baseline_boxes_unchanged=True,
        model_params_b=8.78245912, new_model_calls=0, optimizer_updates=0, official_score='UNKNOWN',
        source_lock_sha256=sha(lock_path), independent_validation='independent_validation.json',
        human_summary_proxy_not_official_crop_quality=True, old_reference_failed_preserved=True,
        geometry_checks=geometry)
    save(out/'completion.json', receipt)
    print(json.dumps(receipt,ensure_ascii=False))


if __name__=='__main__':
    try:main()
    except BaseException:
        failure=REPORT/'package_failure_L16_09.json'
        if not failure.exists():save(failure,dict(status='FAILED_L16_PACKAGE_KEEP_ALL_OLD_AND_NEW_EVIDENCE',traceback=__import__('traceback').format_exc(),new_model_calls=0))
        raise
