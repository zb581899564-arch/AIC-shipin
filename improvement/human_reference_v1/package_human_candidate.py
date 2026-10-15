"""A separately gated CPU package for one pre-registered human-reference arm."""
import json
import subprocess
import sys
import zipfile
from collections import defaultdict
from fractions import Fraction as F
from pathlib import Path

from evaluate_candidates_v3 import ROOT, REPORT, ARMS, read, sha, save, admission as input_admission

PRIOR = ROOT/'reports/boundary_refinement_20261012_v1'
INPUT = PRIOR/'input_01'
DEPS = PRIOR/'input_dependencies'
PARAMETER_VALIDATOR = ROOT/'improvement/reliable_reference_v1/validate_parameter_field.py'
EXTERNAL = REPORT/'external_export_01'
sys.path.insert(0, str(ROOT/'improvement/boundary_refinement_v1'))
from intervals import expanded_windows, native_membership

NAMES = {'A': 'HUMAN_REF_PRE100_POST050_8B', 'B': 'HUMAN_REF_PRE075_POST075_8B',
         'C': 'HUMAN_REF_PRE100_POST075_8B'}


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


def admission(arm):
    comparison_path = REPORT/'comparison_v3_01/human_comparison.json'
    veto_path = REPORT/'comparison_v3_01/partial_silver_veto.json'
    selection_path = REPORT/'comparison_v3_01/screen_selection.json'
    comparison, veto, selection = read(comparison_path), read(veto_path), read(selection_path)
    if (comparison['status'] != 'HUMAN_PROXY_COMPLETE_PENDING_PARTIAL_SILVER_FACT_VETO' or
            arm not in comparison['human_eligible'] or
            veto['status'] != 'PASS_HUMAN_PROXY_AND_PARTIAL_FACT_RISK_SCREEN' or
            arm not in veto['eligible'] or veto['bindings']['human_comparison_sha256'] != sha(comparison_path) or
            veto['padding_exact'][arm] != list(ARMS[arm]) or
            comparison['screen_selection_sha256'] != sha(selection_path) or
            not selection['frozen_before_confirm_metrics'] or arm not in selection['chosen'] or
            selection['padding_exact'][arm] != list(ARMS[arm]) or
            not comparison['screen'][arm]['diagnostic_risk_pass'] or
            not comparison['confirm'][arm]['diagnostic_risk_pass'] or
            not veto['old_reference_quality_failed_preserved'] or
            len(veto['checks'][arm]) != 40 or
            len({row['case_id'] for row in veto['checks'][arm]}) != 40 or
            not all(row['known_point_veto_pass'] and not row['core_lost'] and
                    not row['ordinary_added'] for row in veto['checks'][arm])):
        raise ValueError('Both fixed human-reference and partial fact gates must pass for this arm')
    lineage = [REPORT/'comparison_v3_01/launch_claim.json',
        EXTERNAL/'native_input_acceptance.json', EXTERNAL/'developer_export_acceptance.json',
        EXTERNAL/'developer_prediction_export.json', EXTERNAL/'human_chain_01/completion.json',
        EXTERNAL/'human_gpu_01/completion.json', EXTERNAL/'human_replay_01/completion.json',
        EXTERNAL/'resource.json', EXTERNAL/'matching_gpu_ledger.json', EXTERNAL/'terminal_audit.json',
        EXTERNAL/'transfer_receipt.json', REPORT/'source_receipts_01/human_source_lock_01.json',
        REPORT/'source_receipts_01/human_gpu_01/model_identity.json',
        ROOT/'reports/reliable_reference_20261012_v1/coverage_diagnostic_01.json',
        PRIOR/'developer_readonly_export.json']
    accepted = input_admission(EXTERNAL)
    launch, export, chain, gpu, replay = [read(path) for path in [lineage[0], lineage[2],
        lineage[4], lineage[5], lineage[6]]]
    resource, ledger, audit, transfer = [read(path) for path in lineage[7:11]]
    if (launch['admission_sha256'] != sha(lineage[1]) or
            launch['export_acceptance_sha256'] != sha(lineage[2]) or
            launch['export_sha256'] != sha(lineage[3]) or
            launch['script_sha256'] != sha(Path(__file__).with_name('evaluate_candidates_v3.py')) or
            chain['status'] != 'PASS_EXTERNAL_B_EXPORT_PENDING_LOCAL_HUMAN_QUALITY_COMPARISON' or
            chain['developer_export_acceptance_sha256'] != sha(lineage[2]) or
            chain['prediction_export_sha256'] != sha(lineage[3]) or
            gpu['status'] != 'PASS_COMPLETE_ORIGINAL_B_EXTERNAL_NATIVE64_CALLS_NOT_QUALITY' or
            replay['status'] != 'PASS_ALL_HUMAN_EXTERNAL_B_INDEPENDENT_CPU_REPLAYS' or
            export['status'] != 'PASS_COMPLETE_B_EXPORT_AND_INDEPENDENT_CPU_REPLAY' or
            gpu['actual_model_calls'] != gpu['successful_windows'] or
            gpu['successful_windows'] != accepted['accepted_windows'] or
            accepted['accepted_windows'] != 116 or len(replay['proofs']) != 116 or
            len({row['case_id'] for row in replay['proofs']}) != 116 or
            gpu['model_parameters'] != 8782459120 or gpu['new_optimizer_updates'] != 0 or
            gpu['reference_labels_read'] or gpu['source_lock_sha256'] != sha(lineage[11]) or
            gpu['model_identity_sha256'] != sha(lineage[12]) or
            replay['windows'] != gpu['successful_windows'] or not replay['CPU_only'] or
            replay['CUDA_initialized'] or replay['gpu_completion_sha256'] != sha(lineage[5]) or
            export['independent_replay_completion_sha256'] != sha(lineage[6]) or
            export['developer_prediction_export_sha256'] != sha(lineage[3]) or
            resource['name'] != 'human_summe20_original_b_native64_20261013_v1' or
            resource['status'] != 'completed' or resource['exit_code'] != 0 or ledger != [resource] or
            chain['resource_terminal_sha256'] != sha(lineage[7]) or
            export['unique_resource_terminal_sha256'] != sha(lineage[7]) or
            audit['status'] != 'PASS_COMPLETE_UNIQUE_GPU_AND_CPU_EXPORT_CHAIN' or
            transfer['status'] != 'PASS_WINDOWS_LINUX_BYTES_SHA_CRC_AND_ALL_EXPORT_MEMBER_SHA' or
            veto['bindings']['partial_reference_sha256'] != sha(lineage[13]) or
            veto['bindings']['external_B_export_sha256'] != sha(lineage[14])):
        raise ValueError('Successful original B export/CPU/unique ledger/comparison lineage changed')
    for member, expected in transfer['manifest'].items():
        member_path = EXTERNAL/member
        if member_path.stat().st_size != expected['bytes'] or sha(member_path) != expected['sha256']:
            raise ValueError('Transferred external export member changed: '+member)
    rules_path = REPORT/'official_rule_check_before_package.json'
    rule = read(rules_path)
    if (rule['official_current_sources_rechecked'] is not True or
            rule['automatic_uniform_boundary_interpretation_allowed'] is not True or
            rule['max_inference_parameters_b'] != 9 or not rule['test_labeling_training_prohibited']):
        raise ValueError('Current official body/attachment/notices must be reviewed before packaging')
    return comparison_path, veto_path, selection_path, rules_path, *lineage


def main(arm):
    if arm not in NAMES:
        raise ValueError('Only pre-registered arms A/B/C')
    bound = list(admission(arm))  # No test membership read before actual external quality acceptance.
    name, padding = NAMES[arm], ARMS[arm]
    registration_path = REPORT/('production_registration_'+arm+'_01.json')
    save(registration_path, dict(candidate=name, arm=arm, padding_exact=padding,
        human_comparison_sha256=sha(bound[0]), partial_fact_veto_sha256=sha(bound[1]),
        selection_before_production_membership=True, model_parameters=8782459120,
        new_model_calls=0, optimizer_updates=0, official_score='UNKNOWN'))
    prior_lock_path = PRIOR/'production_source_lock.json'
    old_lock = read(prior_lock_path)
    for path, digest in old_lock['files'].items():
        if sha(path) != digest:
            raise ValueError('Accepted original production input changed: '+path)
    baseline_path = ROOT/'deliveries/ASYMMETRIC_BOUNDARY_PRE075_POST050_8B_20261012/candidate_ASYMMETRIC_BOUNDARY_PRE075_POST050_8B.zip'
    if sha(baseline_path) != 'cbfacd675aca7b6bbc3287ccebfd81e605945501cd1fef392681ff2e9761fec3':
        raise ValueError('User-reported40.42 baseline changed')
    bound += [registration_path, prior_lock_path, baseline_path, Path(__file__), PARAMETER_VALIDATOR,
        REPORT/'EVALUATION_POLICY.md', REPORT/'human_source_registration_01.json',
        REPORT/'NATIVE_MAPPING_CONTRACT_V3.md', Path(__file__).with_name('evaluate_candidates_v3.py'),
        Path(__file__).with_name('partial_silver_veto_v3.py')]
    lock_path = REPORT/('production_source_lock_'+arm+'_01.json')
    save(lock_path, dict(inherited_files=old_lock['files'],
        new_files={str(path.resolve()): sha(path) for path in bound},
        model_parameters=8782459120, candidate=name, padding_exact=padding,
        original_reference_failed_preserved=True, new_model_calls=0, new_optimizer_updates=0))
    out = REPORT/('candidate_'+arm+'_01')
    out.mkdir(exist_ok=False)
    save(out/'launch_claim.json', dict(source_lock_sha256=sha(lock_path),
        purpose='ONE_PRE_REGISTERED_HUMAN_PROXY_SCREENED_RISK_PACKAGE', new_model_calls=0))
    with zipfile.ZipFile(baseline_path) as z:
        if z.namelist() != ['predictions.jsonl'] or z.testzip() is not None:
            raise ValueError('Baseline package member/CRC changed')
        baseline = keymap([json.loads(line) for line in z.read('predictions.jsonl').splitlines()])
    if len(baseline) != 121266:
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
        old = native_membership(points, expanded_windows(windows, *ARMS['baseline']), domain)
        new = native_membership(points, expanded_windows(windows, *padding), domain)
        original_core = native_membership(points, expanded_windows(windows, '0', '0'), domain)
        # Independently compare bisect membership with the direct exact PTS predicate.
        spans = expanded_windows(windows, *padding)
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
    for history in list((ROOT/'deliveries').rglob('candidate_*.zip'))+list(REPORT.glob('candidate_*/candidate_*.zip')):
        if history.resolve() == pending.resolve():
            continue
        if sha(history) == sha(pending):
            raise ValueError('Candidate duplicates a prior ZIP')
        with zipfile.ZipFile(history) as z:
            if z.namelist() == ['predictions.jsonl'] and __import__('hashlib').sha256(z.read('predictions.jsonl')).hexdigest() == sha(out/'predictions.jsonl'):
                raise ValueError('Candidate duplicates historical prediction content')
    final = out/('candidate_'+name+'.zip')
    pending.rename(final)
    receipt = dict(status='PASS_ONE_NEW_HUMAN_REFERENCE_SCREENED_RISK_ZIP', candidate=name, arm=arm,
        padding_exact=padding, zip_path=str(final.resolve()), bytes=final.stat().st_size, sha256=sha(final),
        frames=len(target), added=len(target-reproduced), removed=0, baseline_boxes_unchanged=True,
        model_params_b=8.78245912, new_model_calls=0, optimizer_updates=0, official_score='UNKNOWN',
        source_lock_sha256=sha(lock_path), independent_validation='independent_validation.json',
        human_summary_proxy_not_official_crop_quality=True, old_reference_failed_preserved=True,
        geometry_checks=geometry)
    save(out/'completion.json', receipt)
    print(json.dumps(receipt,ensure_ascii=False))


if __name__ == '__main__':
    main(sys.argv[1])
