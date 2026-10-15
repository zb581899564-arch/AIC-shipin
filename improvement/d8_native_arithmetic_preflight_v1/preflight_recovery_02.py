"""One immutable metadata-only D8/synthetic-KEEP arithmetic compatibility check.

No media, labels, field composition, processor, model, old package, or output ZIP.
All discrepancies are aggregate diagnostics; no per-source repair is performed.
"""
import argparse
from bisect import bisect_left
from collections import Counter
import datetime as dt
from fractions import Fraction as F
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import resource
import socket
import sys
import traceback
import zipfile

HOME = Path('/home/inspur/aic_video_work')
RUN = HOME/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
ROOT = HOME/'twenty_hour_five_20261014_v1/d8_native_arithmetic_preflight_v1'
INPUTS = dict(plan=RUN/'balanced_two_window_risk_v3/input_01/rematch_plan.json',
    temporal=RUN/'balanced_two_window_risk_v3/rematch_01/temporal.jsonl',
    registry=RUN/'baseline_pts_v4/scan_01/clock_registry.json',
    baseline_zip=HOME/'rapid_risk_three_20261013_v1/recovery_01/control/baseline_D8.zip')
SCHEMA = 'D8_SYNTHETIC_KEEP_NATIVE_ARITHMETIC_METADATA_PREFLIGHT_V1'


def require(value, message):
    if not value:
        raise ValueError(message)


def sha_bytes(value):
    return hashlib.sha256(value).hexdigest()


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''):
            h.update(block)
    return h.hexdigest()


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.flush()
        os.fsync(stream.fileno())


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def host():
    require(socket.gethostname() == 'inspur-NP5570M5' and sys.platform == 'linux' and
            os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'Verified Linux CPU child only')
    require(Path(__file__).resolve() == ROOT/'code/preflight_recovery_02.py', 'Independent registered recovery02 code path required')


def freeze():
    host()
    require(not (ROOT/'registration_02.json').exists() and not (ROOT/'run_02').exists(), 'No repeat freeze or successful recovery02')
    prior_path=ROOT/'registration_01.json'
    require(sha(prior_path)=='5049c5fd0f038e8a869ffd12225d2b1900e9d35384c84259febc1fb66dcb1f5d', 'Immutable original preflight binding changed')
    prior=read(prior_path)
    require((ROOT/'run_01/failure.json').is_file(), 'Explicit preserved01 failure required, never rerun a success')
    files=dict(prior['code_files'])
    for path in (ROOT/'code/preflight_recovery_02.py',ROOT/'code_snapshots/tp_contract_v2_frozen.py'):
        files[str(path)]=dict(sha256=sha(path),bytes=path.stat().st_size)
    for path,value in files.items():require(sha(path)==value['sha256'],'Immutable old/new code snapshot changed')
    refs,array_refs=prior['inputs'],prior['original_clock_array_refs']
    save(ROOT/'registration_02.json', dict(schema=SCHEMA,
        status='FROZEN_BEFORE_FIRST_METADATA_ARITHMETIC_EXECUTION', created_utc=utc(), code_files=files,
        inputs=refs, original_clock_array_refs=array_refs, source_count=426, window_count=521,
        original_candidate_count=665, protected_D8_frame_count=122050,
        formula=dict(original_coarse_length_threshold_exact='8', lead_exact='3/4', tail_exact='1/2',
                     eligible_extra_tail_exact='1/4', clip='ORIGINAL_WINDOW', native_membership='HALF_OPEN_BISECT_ORIGINAL_EXACT_PTS'),
        source_projection='Fraction(str(part.start_sec/end_sec)) plus Fraction(str(parsed_segments))',
        model_answers='SYNTHETIC_KEEP_CONSTANT_ARITHMETIC_ONLY_NOT_INFERENCE',
        permitted_reads='Four frozen metadata/artifact inputs and originalclock arrays; only combine/tp_contract stdlib imports. Project snapshot is source text identity only, never imported.',
        recovery_from_registration_ref=dict(path=str(prior_path),sha256=sha(prior_path)),
        recovery_from_failure_ref=dict(path=str(ROOT/'run_01/failure.json'),sha256=sha(ROOT/'run_01/failure.json')),
        changed_only_planning_evidence='416 explicit oldCFR N/fps planning with nullticks;10 explicit old endticks. No native measurement or old gate changed.',
        metadata_arithmetic_executions=1, new_media_reads=0, GT_reads=0, processor_calls=0,
        model_calls=0, field_composition_calls=0, old_package_runs=0, output_ZIPs=0,
        per_case_fixes_or_rule_selection=False, old_CFR416_not_new_native_endpoint_measurement=True))
    print(json.dumps(dict(status='FROZEN_NEW_METADATA_ARITHMETIC_RECOVERY02_SCOPE', registration_sha256=sha(ROOT/'registration_02.json'),
                         input_bytes=sum(r['bytes'] for r in refs.values()), clock_array_bytes=sum(r['bytes'] for r in array_refs), model_calls=0)))


def load_frozen(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def fraction(value):
    require(not isinstance(value, bool) and isinstance(value, (str, int, float)), 'Original explicit seconds scalar required')
    if isinstance(value, float):
        require(math.isfinite(value), 'Nonfinite original scalar cannot be repaired')
    return F(str(value))


def native_union(points, intervals):
    chosen = set()
    for a, b in intervals:
        require(a < b, 'Original selected interval is empty or reversed')
        chosen.update(range(bisect_left(points, a), bisect_left(points, b)))
    direct = {i for i, p in enumerate(points) if any(a <= p < b for a, b in intervals)}
    require(chosen == direct, 'Independent exact half-open predicate differs from bisect')
    return chosen


def formula(lo, hi, a, b):
    lead, tail = F(3, 4), F(1, 2)+(F(1, 4) if b-a >= 8 else 0)
    return max(lo, a-lead), min(hi, b+tail)


def frame_boxes_hash(rows):
    projected = [dict(video_id=row['video_id'], targetRatioWH=row['targetRatioWH'], predictions=row['predictions'])
                 for row in sorted(rows, key=lambda r: r['video_id'])]
    return sha_bytes(json.dumps(projected, sort_keys=True, separators=(',', ':'), allow_nan=False).encode())


def run():
    host()
    out = ROOT/'run_02'
    out.mkdir(exist_ok=False)
    save(out/'launch_claim.json', dict(pid=os.getpid(), argv=sys.argv, utc=utc(), CPU_only=True,
        registration_sha256=sha(ROOT/'registration_02.json'), new_media_reads=0, GT_reads=0,
        processor_calls=0, model_calls=0, old_package_runs=0, output_ZIPs=0))
    try:
        reg = read(ROOT/'registration_02.json')
        require(reg['schema'] == SCHEMA and reg['status'] == 'FROZEN_BEFORE_FIRST_METADATA_ARITHMETIC_EXECUTION', 'New scope must be frozen first')
        for path, value in reg['code_files'].items():
            require(sha(path) == value['sha256'], 'Frozen source changed before computation')
        blobs = {}
        for key, ref in reg['inputs'].items():
            require(ref['path'] == str(INPUTS[key]), 'Unexpected input or media path')
            data = Path(ref['path']).read_bytes()
            require(len(data) == ref['bytes'] and sha_bytes(data) == ref['sha256'], 'Original frozen metadata/artifact bytes changed')
            if key != 'baseline_zip':
                blobs[key] = data
        plan, registry = json.loads(blobs.pop('plan')), json.loads(blobs.pop('registry'))
        temporal = [json.loads(line) for line in blobs.pop('temporal').splitlines() if line.strip()]
        jobs = {row['video_id']: row for row in plan['jobs']}
        records = {row['video_id']: row for row in registry['records']}
        answers = {row['video_id']: row for row in temporal}
        require(len(jobs) == len(records) == len(answers) == 426 and
                set(jobs) == set(records) == set(answers) == {str(i) for i in range(426)}, '426source identity/count mismatch')
        require(plan['input_ref']['registry_sha256'] == reg['inputs']['registry']['sha256'], 'Original plan/clock registry identity differs')
        with zipfile.ZipFile(INPUTS['baseline_zip']) as archive:
            require(archive.namelist() == ['predictions.jsonl'], 'Protected D8 single member changed')
            payload = archive.read('predictions.jsonl')  # ZIP CRC checked on this single read.
            baseline = [json.loads(line) for line in payload.splitlines() if line.strip()]
        require(len(baseline) == 426 and {r['video_id'] for r in baseline} == set(jobs) and all(r['predictions'] for r in baseline),
                'Protected D8 source/nonempty format changed')
        wanted = {(row['video_id'], p['frame']) for row in baseline for p in row['predictions']}
        require(len(wanted) == sum(len(r['predictions']) for r in baseline) == 122050, 'Protected D8 keys duplicate or incorrect')
        old_boxes = {(row['video_id'], p['frame']): p['bboxes'] for row in baseline for p in row['predictions']}
        by_baseline = {row['video_id']: row for row in baseline}
        combine = load_frozen('_D8_prefight_frozen_combine', ROOT/'code_snapshots/combine_events_frozen.py')
        prototype = load_frozen('_D8_preflight_v2_frozen_contract', ROOT/'code_snapshots/tp_contract_v2_frozen.py')
        frozen_arrays = {row['video_id']: row for row in reg['original_clock_array_refs']}
        selected, hypothetical_ceil = set(), set()
        counts, schema_types, fields_presence, exact_field_domain = Counter(), Counter(), Counter(), Counter()
        branch_counts, branch_selected, branch_added, branch_removed, planning_end_counts = Counter(), Counter(), Counter(), Counter(), Counter()
        domain_delta = []
        domain_sources, strict_candidate_sources, selection_changed_sources = set(), set(), set()
        retained_rows = []
        baseline_keys_CFR = set()
        for vid in sorted(jobs, key=int):
            job, record, answer = jobs[vid], records[vid], answers[vid]
            ref = frozen_arrays[vid]
            data = Path(ref['path']).read_bytes()
            require(len(data) == ref['bytes'] and sha_bytes(data) == ref['sha256'], 'Old accepted integer clock-array bytes changed')
            value = json.loads(data)
            arrays = value.get('arrays', value)
            require(arrays['source_sha256'] == record['source_sha256'] == job['metadata']['source_sha256'], 'Original source byte identities differ')
            require(arrays['video_id'] == vid and len(arrays['native_pts_ticks']) ==
                    arrays['n_frames'] == record['n_frames'] == job['metadata']['n_frames'], 'Original complete integer array denominator differs')
            old_clock = prototype.old_clock(arrays, record)
            points = list(map(F, old_clock['normalized_exact_pts']))
            end = F(old_clock['planned_physical_end_exact'])
            tick, origin = F(arrays['raw_time_base']), F(arrays['raw_first_pts_ticks'])*F(arrays['raw_time_base'])
            require(points == [F(p)*tick-origin for p in arrays['native_pts_ticks']] and
                    end == (F(record['n_frames']*record['fps_den'],record['fps_num']) if arrays['native_frame_end_pts_ticks'] is None else
                            F(arrays['native_frame_end_pts_ticks'][-1])*tick-origin),
                    'Prototype oldclock exact tick/origin/planned end differs')
            planning_end_counts[old_clock['planned_end_provenance']]+=1
            branch = record['clock_branch']
            branch_counts[branch] += 1
            require(len(job['windows']) == len(answer['windows']), 'Original source window denominator differs')
            intervals, ceil_ordinals = [], set()
            for ix, (part, done) in enumerate(zip(job['windows'], answer['windows'])):
                counts['windows'] += 1
                require(done['output_valid'] is True and not done['parse_errors'] and done['status'] in ('MODEL_OK', 'LEGAL_EMPTY'),
                        'Failed coarse output cannot enter arithmetic reconstruction')
                require(done['video_identity']['source_sha256'] == record['source_sha256'] and
                        done['video_identity']['source_frame_ids'] == part['window']['planned_source_frame_ordinals'],
                        'Original accepted model input/source plan identity differs')
                lo, hi = fraction(part['start_sec']), fraction(part['end_sec'])
                require(lo < hi, 'Original window reversed; no repair')
                window_domain_valid = 0 <= lo < hi <= end
                if not window_domain_valid:
                    counts['windows_outside_exact_planned_source_domain'] += 1
                    domain_sources.add(vid)
                    if hi > end:
                        counts['window_end_above_planned_end'] += 1
                        domain_delta.append(hi-end)
                    if lo < 0:
                        counts['window_start_below_zero'] += 1
                if hi-lo > 30:
                    counts['windows_exact_decimal_duration_over30'] += 1
                require(done['start_sec'] == part['start_sec'] and done['end_sec'] == part['end_sec'],
                        'Old temporal and plan original window origin/end differ')
                for role, holder in (('part', part['window']), ('done', done['window'])):
                    for key, item in holder.items():
                        fields_presence[role+'.'+key] += 1
                        schema_types[role+'.'+key+'.'+type(item).__name__] += 1
                        if key in ('window_pts_start_sec', 'window_pts_end_exclusive_sec'):
                            scalar = fraction(item)
                            exact_field_domain[role+'.'+key+'.in_exact_source_domain'] += int(0 <= scalar <= end)
                            exact_field_domain[role+'.'+key+'.string_fraction_or_integer'] += int(isinstance(item, str))
                            equal = scalar == (lo if key.endswith('start_sec') else hi)
                            exact_field_domain[role+'.'+key+'.equals_top_decimal_scalar'] += int(equal)
                ordinals = done['video_identity']['source_frame_ids']
                if not (len(ordinals) == len(set(ordinals)) == 64 and all(type(i) is int and 0 <= i < len(points) for i in ordinals)
                        and all(a < b for a, b in zip(ordinals, ordinals[1:])) and all(lo <= points[i] < hi for i in ordinals)):
                    counts['request_skeleton_original_visual64_domain_invalid_windows'] += 1
                if not done['parsed_segments']:
                    counts['legal_empty_windows'] += 1
                for seg, raw_pair in enumerate(done['parsed_segments']):
                    counts['events'] += 1
                    require(len(raw_pair) == 2, 'Original segment shape changed')
                    a_local, b_local = map(fraction, raw_pair)
                    require(0 <= a_local < b_local, 'Original segment reversed; no repair')
                    a, b = lo+a_local, lo+b_local
                    if not 0 <= lo <= a < b <= hi or hi-lo > 30:
                        counts['request_skeleton_event_window_domain_invalid_events'] += 1
                    if b > end:
                        counts['original_coarse_event_end_above_planned_end'] += 1
                    if b-a >= 8:
                        counts['original_length_eligible8_events'] += 1
                    interval = formula(lo, hi, a, b)
                    require(interval[0] < interval[1], 'Pure original formula interval empty; no fallback')
                    intervals.append(interval)
                    event_id = 'SYNTHETIC_KEEP_'+vid+'_'+str(ix)+'_'+str(seg)
                    event = dict(event_id=event_id, source_id=vid, original_interval_exact=[str(a), str(b)],
                                 original_window_exact=[str(lo), str(hi)], physical_end_exact=str(end))
                    endpoints = {event_id+'.'+side: dict(event_id=event_id, side=side, applied_decision='KEEP',
                        original_endpoint_exact=str(point), endpoint_exact=str(point)) for side, point in (('start', a), ('end', b))}
                    verification = {event_id: dict(event_id=event_id, decision='KEEP')}
                    try:
                        result = combine.candidate(event, endpoints, verification, 'BOTH')
                    except ValueError:
                        counts['strict_root_candidate_domain_rejected_events'] += 1
                        strict_candidate_sources.add(vid)
                    else:
                        require(tuple(map(F, result['selected_interval_exact'])) == interval, 'Root and independent D8 padding formula differ')
                    if branch == 'CFR_LEGACY':
                        # This is a diagnostic comparator, not an asserted old D8
                        # recipe or an authorized new converter for any source.
                        fps = job['metadata']['fps_num']/job['metadata']['fps_den']
                        f_a, f_b = map(float, raw_pair)
                        f_lo, f_hi = float(part['start_sec']), float(part['end_sec'])
                        f_tail = 0.5+(0.25 if f_b-f_a >= 8 else 0.0)
                        x, y = max(f_lo, f_lo+f_a-0.75), min(f_hi, f_lo+f_b+f_tail)
                        ceil_ordinals.update(range(max(0, math.ceil(x*fps)), min(len(points), math.ceil(y*fps))))
            native = native_union(points, intervals)
            source_selected = {(vid, i) for i in native}
            selected.update(source_selected)
            wanted_source = {(vid, p['frame']) for p in by_baseline[vid]['predictions']}
            require(all(type(i) is int and 0 <= i < len(points) for _, i in wanted_source), 'Protected D8 frame ordinal outside original fullclock')
            if source_selected != wanted_source:
                selection_changed_sources.add(vid)
            branch_selected[branch] += len(source_selected)
            branch_added[branch] += len(source_selected-wanted_source)
            branch_removed[branch] += len(wanted_source-source_selected)
            kept_predictions = [p for p in by_baseline[vid]['predictions'] if p['frame'] in native]
            retained_rows.append(dict(by_baseline[vid], predictions=kept_predictions))
            if branch == 'CFR_LEGACY':
                hypothetical_ceil.update((vid, i) for i in ceil_ordinals)
                baseline_keys_CFR.update(wanted_source)
        require(counts['windows'] == 521 and counts['events'] == 665, 'Original426/521/665 denominator differs')
        kept = {(row['video_id'], p['frame']): p['bboxes'] for row in retained_rows for p in row['predictions']}
        require(set(kept) == wanted & selected and all(value == old_boxes[key] for key, value in kept.items()), 'Literal original kept frame boxes changed')
        exact_CFR = {key for key in selected if records[key[0]]['clock_branch'] == 'CFR_LEGACY'}
        mismatch = selected != wanted
        result = dict(schema=SCHEMA,
            status='PASS_SYNTHETIC_KEEP_D8_ARITHMETIC_COMPATIBILITY' if not mismatch and not counts['windows_outside_exact_planned_source_domain'] and
                not counts['windows_exact_decimal_duration_over30'] and not counts['strict_root_candidate_domain_rejected_events'] and
                not counts['request_skeleton_event_window_domain_invalid_events'] and not counts['request_skeleton_original_visual64_domain_invalid_windows'] else
                'STOP_PROSPECTIVE_PREP_ADMISSION_ARITHMETIC_OR_EXACT_DOMAIN_INCOMPATIBLE_KEEP_OLD_D8',
            actual_sources=426, actual_windows=521, actual_original_candidates=665, protected_D8_frames=122050,
            reconstructed_original_formula_frames=len(selected), framekey_equal=not mismatch,
            added_vs_D8=len(selected-wanted), removed_vs_D8=len(wanted-selected), symmetric_difference_vs_D8=len(selected^wanted),
            sources_with_framekey_difference=len(selection_changed_sources), counts=dict(counts),
            clock_branch_counts=dict(branch_counts), branch_reconstructed_frames=dict(branch_selected),
            planning_end_evidence_counts=dict(planning_end_counts),
            branch_added_frames=dict(branch_added), branch_removed_frames=dict(branch_removed),
            source_domain_violating_sources=len(domain_sources), strict_root_candidate_rejected_sources=len(strict_candidate_sources),
            above_source_end_delta_seconds=dict(count=len(domain_delta), min_exact=str(min(domain_delta)) if domain_delta else None,
                max_exact=str(max(domain_delta)) if domain_delta else None),
            existing_window_schema_field_presence=dict(fields_presence), existing_window_schema_types=dict(schema_types),
            existing_window_clock_field_domain=dict(exact_field_domain),
            hypothetical_float_ceil_CFR_only=dict(assumed_old_D8_converter=False, sources=branch_counts['CFR_LEGACY'],
                frames=len(hypothetical_ceil), added_vs_protected_D8_CFR=len(hypothetical_ceil-baseline_keys_CFR),
                removed_vs_protected_D8_CFR=len(baseline_keys_CFR-hypothetical_ceil),
                symmetric_difference_vs_exact_native_CFR=len(hypothetical_ceil^exact_CFR)),
            original_kept_boxes_preserved=True, original_kept_box_frames=len(kept), boxes_recomposed=False,
            protected_D8_canonical_frame_boxes_sha256=frame_boxes_hash(baseline),
            retained_original_frame_boxes_sha256=frame_boxes_hash(retained_rows),
            complete_box_equality_without_added_frame_fields=(not mismatch and frame_boxes_hash(baseline) == frame_boxes_hash(retained_rows)),
            registration_sha256=sha(ROOT/'registration_02.json'), original_D8_zip_sha256=reg['inputs']['baseline_zip']['sha256'],
            checked_clock_arrays=426, original_clock_arrays_overwritten=False, old_CFR416_is_new_measured_terminal=False,
            diagnostic_uses_old_tick_end_as_planning_only=True, newly_measured_native_terminal_evidence=False,
            synthetic_KEEP_is_model_answer=False, new_media_reads=0, GT_reads=0, processor_calls=0, model_calls=0,
            field_composition_calls=0, old_package_runs=0, output_ZIPs=0, per_case_repairs=0,
            source_output_params_unchanged=True, process_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss, utc=utc())
        save(out/'completion.json', result)
        print(json.dumps(result))
    except BaseException as error:
        save(out/'failure.json', dict(error=repr(error), traceback=traceback.format_exc(), preserve_all_old_successes=True,
            no_automatic_retry=True, new_media_reads=0, GT_reads=0, model_calls=0, utc=utc()))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('operation', choices=('freeze', 'run'))
    args = parser.parse_args()
    os.environ['CUDA_VISIBLE_DEVICES'] = ''
    (freeze if args.operation == 'freeze' else run)()
