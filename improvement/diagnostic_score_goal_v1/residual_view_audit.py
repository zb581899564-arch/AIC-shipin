"""Metadata-only native64 eligibility of original B0 candidate residuals.

Uses saved VERIFY baseline spans and the already frozen historical evidence.
No human-reference file, model, pixel payload or processor is read. Metric
fields in adopted JSONs are not consulted. A cache reference is not new QA.
"""
from __future__ import annotations

import argparse
from bisect import bisect_left
from collections import Counter
from fractions import Fraction as F
import hashlib
import json
import os
from pathlib import Path
import sys
import traceback

WORK = Path('/home/inspur/aic_video_work')
PRIOR = WORK/'recall_expansion_verify40_46_20261014_v1'
NATIVE_FRAMES = 64  # Inherited physical-input contract, never a fitted threshold.
ELIGIBILITY_STATES = ('NOT_APPLICABLE_FEWER_THAN64_DISTINCT_NATIVE_FRAMES',
                      'UNKNOWN_FEWER_THAN64_PRESENT_CACHE_REFERENCED_SAMPLES',
                      'METADATA_ELIGIBLE64_CACHE_REFERENCES_NOT_INPUT_QA')


def require(value, message):
    if not value:
        raise ValueError(message)


def exact(value):
    require(isinstance(value, (int, str, F)) and not isinstance(value, bool),
            'Exact PTS must be an integer/fraction string, never float/bool')
    return F(value)


def clock_points(points, physical_end):
    pts, end = tuple(map(exact, points)), exact(physical_end)
    require(pts and pts[0] == 0 and all(a < b for a, b in zip(pts, pts[1:]))
            and end > pts[-1], 'Complete strictly increasing zero-origin native clock required')
    return pts, end


def merge_ranges(ranges):
    result = []
    for a, b in sorted(ranges):
        require(type(a) is int and type(b) is int and 0 <= a < b,
                'Positive half-open native ordinal ranges required')
        if result and a <= result[-1][1]:
            result[-1][1] = max(result[-1][1], b)
        else:
            result.append([a, b])
    return result


def native_ranges(spans, pts, physical_end):
    result = []
    for first, last in spans:
        a, b = exact(first), exact(last)
        require(0 <= a < b <= physical_end, 'Interval escaped the original physical source')
        lo, hi = bisect_left(pts, a), bisect_left(pts, b)
        if lo < hi:
            result.append([lo, hi])
    return merge_ranges(result)


def subtract_ranges(candidate, baseline):
    """Maximal consecutive-ordinal components of candidate minus baseline."""
    result = []
    base = merge_ranges(baseline)
    for lo, hi in merge_ranges(candidate):
        cursor = lo
        for a, b in base:
            if b <= cursor:
                continue
            if a >= hi:
                break
            if cursor < a:
                result.append([cursor, min(a, hi)])
            cursor = max(cursor, b)
            if cursor >= hi:
                break
        if cursor < hi:
            result.append([cursor, hi])
    return result


def component_id(source_sha256, ordinal_range):
    require(isinstance(source_sha256, str) and len(source_sha256) == 64
            and all(c in '0123456789abcdef' for c in source_sha256), 'Explicit source SHA256 required')
    a, b = ordinal_range
    merge_ranges([[a, b]])
    return hashlib.sha256((source_sha256+'|'+str(a)+'|'+str(b)).encode()).hexdigest()


def eligibility_status(native_count, present_samples):
    if native_count < NATIVE_FRAMES:
        return ELIGIBILITY_STATES[0]
    if present_samples < NATIVE_FRAMES:
        return ELIGIBILITY_STATES[1]
    return ELIGIBILITY_STATES[2]


def status_counts(components):
    counts = Counter(c['eligibility_status'] for c in components)
    return {state: counts[state] for state in ELIGIBILITY_STATES}


def describe_component(source_sha256, ordinal_range, pts, physical_end, views):
    """Pure metadata coverage; caller supplies stat-only cache availability."""
    a, b = ordinal_range
    merge_ranges([[a, b]])
    require(b <= len(pts), 'Component escaped full source clock')
    samples = {}
    for view in views:
        require(type(view['cache_present']) is bool, 'Explicit cache availability required')
        ordinals, pixels = view['ordinals'], view['pixel_sha256']
        require(len(ordinals) == len(pixels) == NATIVE_FRAMES
                and len(set(ordinals)) == NATIVE_FRAMES and ordinals == sorted(ordinals),
                'Original input must contain64 distinct native samples')
        for index, (ordinal, pixel) in enumerate(zip(ordinals, pixels)):
            require(type(ordinal) is int and 0 <= ordinal < len(pts), 'Invalid cached sample ordinal')
            if not a <= ordinal < b:
                continue
            sample = samples.setdefault(ordinal, dict(ordinal=ordinal, exact_pts=str(pts[ordinal]),
                                      pixel_sha256=pixel, cache_references=[]))
            require(sample['pixel_sha256'] == pixel, 'Conflicting RGB pixel identity for one source ordinal')
            sample['cache_references'].append(dict(case_id=view['case_id'], array=view['array_ref'],
                      array_row_index=index, cache_present=view['cache_present']))
    rows = [samples[o] for o in sorted(samples)]
    present = [s['ordinal'] for s in rows if any(r['cache_present'] for r in s['cache_references'])]
    count = b-a
    status = eligibility_status(count, len(present))
    return dict(component_id=component_id(source_sha256, [a, b]), source_sha256=source_sha256,
        native_ordinal_range_half_open=[a, b], native_frames=count,
        native_cell_span_exact=[str(pts[a]), str(pts[b] if b < len(pts) else physical_end)],
        first_last_native_pts_exact=[str(pts[a]), str(pts[b-1])],
        has_at_least64_distinct_native_frames=(count >= NATIVE_FRAMES), eligibility_status=status,
        RGB_sample_coverage=dict(recorded_distinct_native_samples=len(rows),
             present_cache_referenced_distinct_native_samples=len(present),
             missing_cached_native_frames=count-len(present), samples=rows,
             availability_basis='Path.is_file only; recorded array/pixel SHAs inherited, bytes not reverified',
             full_component_RGB_coverage=(len(present) == count)),
        current_input_admitted=False, new_observation_performed=False, semantic_truth='UNKNOWN')


def combine_component(first, second):
    """Deduplicate identical source/ordinal component across any event/group."""
    invariant = ('component_id', 'source_sha256', 'native_ordinal_range_half_open',
                 'native_frames', 'native_cell_span_exact', 'first_last_native_pts_exact')
    require(all(first[k] == second[k] for k in invariant), 'Conflicting source/component clock metadata')
    samples = {}
    for row in first['RGB_sample_coverage']['samples']+second['RGB_sample_coverage']['samples']:
        ordinal = row['ordinal']
        target = samples.setdefault(ordinal, dict(ordinal=ordinal, exact_pts=row['exact_pts'],
                                   pixel_sha256=row['pixel_sha256'], cache_references=[]))
        require(target['exact_pts'] == row['exact_pts'] and target['pixel_sha256'] == row['pixel_sha256'],
                'Conflicting same-source native RGB identity')
        for reference in row['cache_references']:
            if reference not in target['cache_references']:
                target['cache_references'].append(reference)
    result = dict(first)
    rows = [samples[o] for o in sorted(samples)]
    present = sum(any(r['cache_present'] for r in row['cache_references']) for row in rows)
    coverage = dict(first['RGB_sample_coverage'], samples=rows, recorded_distinct_native_samples=len(rows),
                    present_cache_referenced_distinct_native_samples=present,
                    missing_cached_native_frames=first['native_frames']-present,
                    full_component_RGB_coverage=(present == first['native_frames']))
    result.update(RGB_sample_coverage=coverage, eligibility_status=eligibility_status(first['native_frames'], present))
    result['event_aliases'] = first.get('event_aliases', [])+second.get('event_aliases', [])
    refs = first.get('native_clock_refs', [first['native_clock_ref']] if 'native_clock_ref' in first else [])
    for reference in second.get('native_clock_refs', [second['native_clock_ref']] if 'native_clock_ref' in second else []):
        if reference not in refs:
            refs = refs+[reference]
    if refs:
        result['native_clock_refs'] = refs
    return result


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


class Evidence:
    def __init__(self):
        self.files = {}

    def read(self, path, expected=None):
        path = Path(path).resolve()
        require(path.is_relative_to(WORK.resolve()) and path.is_file(), 'Missing/out-of-workspace JSON: '+str(path))
        digest = sha(path)
        require(expected is None or digest == expected, 'Frozen JSON SHA mismatch: '+str(path))
        require(str(path) not in self.files or self.files[str(path)] == digest, 'JSON changed during metadata audit')
        self.files[str(path)] = digest
        return json.loads(path.read_text(encoding='utf-8-sig'))


def unique(rows, key):
    result = {r[key]: r for r in rows}
    require(len(result) == len(rows), 'Repeated '+key)
    return result


def audit_group(prior, group, oracle, evidence):
    frozen = oracle['evidence_files']

    def old(path, digest=None):
        path = Path(path).resolve()
        require(str(path) in frozen and (digest is None or digest == frozen[str(path)]),
                'Metadata absent from existing frozen evidence: '+str(path))
        return evidence.read(path, frozen[str(path)])

    sources = unique(unique(oracle['groups'], 'group')[group]['sources'], 'video_id')
    require(len(sources) == 4, 'All four original sources required')
    cpu_path = prior/('cpu_acceptance_'+group+'.json')
    cpu = old(cpu_path)
    complete = old(prior/group/'B0/gpu_01/completion.json')
    replay = old(prior/group/'B0/replay_01/completion.json')
    export = old(prior/group/'VERIFY/verification_export.json')
    comparison_path = prior/group/'comparison_01/result.json'
    comparison = old(comparison_path)
    require(cpu['group'] == export['group'] == comparison['group'] == group
            and cpu['status'] == 'PASS_ALL_RECALL_REAL_CPU_INPUTS_NOT_GPU_ADMISSION'
            and cpu['CPU_only'] is True and cpu['CUDA_initialized'] is False
            and complete['status'] == 'PASS_ALL_RECALL_B0_CALLS_NOT_QUALITY'
            and replay['status'] == 'PASS_ALL_RECALL_B0_INDEPENDENT_REPLAYS_NOT_QUALITY'
            and replay['gpu_completion_sha256'] == frozen[str((prior/group/'B0/gpu_01/completion.json').resolve())]
            and export['status'] == 'PASS_RECALL_VERIFY_EXECUTION_AND_REPLAY_NOT_QUALITY',
            'Original complete source/input/B0/VERIFY metadata required')
    require(comparison['bindings']['cpu_acceptance_sha256'] == frozen[str(cpu_path.resolve())]
            and comparison['bindings']['verification_export_sha256'] == frozen[str((prior/group/'VERIFY/verification_export.json').resolve())],
            'Saved VERIFY baseline binding differs')
    done_rows, proof_rows = unique(complete['entries'], 'case_id'), unique(replay['proofs'], 'case_id')
    require(complete['calls'] == replay['calls'] == len(done_rows) == len(proof_rows)
            and set(done_rows) == set(proof_rows) == {r['case_id'] for r in cpu['entries']}, 'Complete B0 case denominator differs')
    inputs, outputs, views = {}, {}, {name: [] for name in sources}
    cache_inventory = {}
    for entry in cpu['entries']:
        case = entry['case_id']
        meta = old(entry['input_path'], entry['input_sha256'])
        proof = old(entry['proof_path'], entry['proof_sha256'])
        done = old(done_rows[case]['done_path'], done_rows[case]['done_sha256'])
        qa = old(proof_rows[case]['proof_path'], proof_rows[case]['proof_sha256'])
        name = meta['source_name']
        require(name in sources and case == meta['case_id'] == proof['case_id'] == done['case_id'] == qa['case_id']
                and proof['input_sha256'] == entry['input_sha256']
                and qa['done_sha256'] == done_rows[case]['done_sha256']
                and qa['segments'] == done['segments'] and qa['native_ranges'] == done['native_ranges']
                and meta['source_sha256'] == done['source_sha256'] == sources[name]['source_sha256']
                and meta['reference_available_to_inference'] is False and meta['audio_observed'] is False,
                'Original B0 source/input/first-QA identity differs')
        ordinals = meta['source_frame_ordinals']
        require(len(ordinals) == len(set(ordinals)) == len(meta['pixel_sha256']) == NATIVE_FRAMES
                and ordinals == sorted(ordinals)
                and [meta['all_source_exact_pts'][i] for i in ordinals] == meta['sample_exact_pts'], 'Original native64 samples differ')
        array = Path(meta['frame_array_path']).resolve()
        require(array.is_relative_to(WORK.resolve()), 'RGB metadata reference escaped work root')
        reference = dict(path=str(array), sha256=meta['frame_array_sha256'])
        view = dict(case_id=case, ordinals=ordinals, pixel_sha256=meta['pixel_sha256'],
                    array_ref=reference, cache_present=array.is_file())
        cache_inventory[case] = dict(array=reference, present=view['cache_present'], input_ref=dict(path=entry['input_path'], sha256=entry['input_sha256']))
        views[name].append(view); inputs[case] = meta; outputs[case] = done
    saved = unique(comparison['cases'], 'video_id')
    require(set(saved) == set(sources), 'Original baseline four-source denominator differs')
    events = unique(export['events'], 'event_id')
    expected = {(case, j) for case, done in outputs.items() for j in range(len(done['segments']))}
    require(len(expected) == len(events) and {(v['original_case_id'], v['original_segment_index']) for v in events.values()} == expected,
            'All original B0 events required; no score-based subset allowed')
    result_sources, components = [], {}
    for name, source in sources.items():
        clock_ref = source['native_clock_ref']; clock = old(clock_ref['path'], clock_ref['sha256'])
        pts, end = clock_points(clock['original_exact_pts'], clock['physical_end_exact'])
        for meta in inputs.values():
            if meta['source_name'] == name:
                require(meta['original_clock_path'] == clock_ref['path'] and meta['original_clock_sha256'] == clock_ref['sha256']
                        and tuple(map(exact, meta['all_source_exact_pts'])) == pts, 'Full original source clock differs')
        baseline = native_ranges(saved[name]['baseline_spans'], pts, end)
        event_rows = []; source_components = set(); decisions = Counter()
        for event in sorted(events.values(), key=lambda r: r['event_id']):
            if event['source_name'] != name:
                continue
            meta = inputs[event['original_case_id']]; si = event['original_segment_index']
            lo, hi = exact(meta['window_start']), exact(meta['window_end'])
            interval = event['original_interval_exact']; a, b = map(exact, interval)
            require(event['source_sha256'] == source['source_sha256'] and lo <= a < b <= hi
                    and [str(lo+F(str(v))) for v in outputs[event['original_case_id']]['segments'][si]] == interval,
                    'Original unpadded B0 event endpoint/source differs')
            decision = event['decision_result']['decision']
            require(decision in ('KEEP', 'UNKNOWN', 'DROP') and event['decision_result']['original_interval_exact'] == interval,
                    'Original VERIFY metadata state differs')
            decisions[decision] += 1
            roles = meta.get('view_roles', [meta['window_role']])
            require(roles and set(roles) <= {'baseline', 'overlap'}, 'Unknown original view roles')
            residual = subtract_ranges(native_ranges([interval], pts, end), baseline)
            ids = []
            for ordinal_range in residual:
                ident = component_id(source['source_sha256'], ordinal_range)
                if ident not in components:
                    components[ident] = describe_component(source['source_sha256'], ordinal_range, pts, end, views[name])
                    components[ident].update(native_clock_ref=clock_ref, event_aliases=[])
                components[ident]['event_aliases'].append(dict(group=group, source_name=name, event_id=event['event_id'],
                    original_case_id=event['original_case_id'], original_segment_index=si, view_roles=roles,
                    original_VERIFY_decision=decision))
                ids.append(ident); source_components.add(ident)
            event_rows.append(dict(event_id=event['event_id'], original_case_id=event['original_case_id'],
                original_interval_exact=interval, view_roles=roles, original_VERIFY_decision=decision,
                residual_component_ids=ids, residual_native_frames=sum(b-a for a, b in residual),
                status='HAS_NEW_NATIVE_COMPONENTS' if ids else 'NOT_APPLICABLE_NO_NEW_NATIVE_FRAME', semantic_truth='UNKNOWN'))
        selected = [components[i] for i in sorted(source_components)]
        result_sources.append(dict(video_id=name, source_sha256=source['source_sha256'], native_clock_ref=clock_ref,
            saved_VERIFY_baseline=dict(comparison_path=str(comparison_path), comparison_sha256=frozen[str(comparison_path.resolve())],
                field='cases[video_id].baseline_spans', native_ordinal_ranges_half_open=baseline, recomputed_metrics=False,
                name='Historical_VERIFY_baseline_with_original_source_empty_guard_NOT_complete40.47'),
            original_B0_events=len(event_rows), original_VERIFY_state_counts=dict(decisions),
            events_without_new_native_frames=sum(not r['residual_component_ids'] for r in event_rows), events=event_rows,
            distinct_components=len(selected), component_ids=sorted(source_components),
            native64_eligible_components=sum(c['has_at_least64_distinct_native_frames'] for c in selected),
            metadata_cache64_eligible_components=sum(c['eligibility_status'].startswith('METADATA_ELIGIBLE64') for c in selected)))
    return dict(group=group, source_count=4, original_B0_events=len(events), sources=result_sources,
        original_RGB_cache_inventory=cache_inventory,
        native64_eligible_source_count=sum(r['native64_eligible_components'] > 0 for r in result_sources),
        metadata_cache64_eligible_source_count=sum(r['metadata_cache64_eligible_components'] > 0 for r in result_sources)), components


def save(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def main(root, prior=PRIOR):
    require(sys.platform.startswith('linux') and os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'Linux CPU child must explicitly hide its own CUDA')
    root, prior = Path(root).resolve(), Path(prior).resolve()
    require(root.is_relative_to(WORK.resolve()) and prior.is_relative_to(WORK.resolve()) and root != prior
            and not root.is_relative_to(prior) and not prior.is_relative_to(root), 'Separate new diagnostic root required')
    out = root/'residual_view_audit_01'; out.mkdir(exist_ok=False)
    evidence = Evidence()
    try:
        oracle = evidence.read(root/'retained_candidate_oracle/result.json')
        require(oracle['status'] == 'COMPLETE_REFERENCE_ASSISTED_DIAGNOSTIC_NOT_PREDICTIONS'
                and Path(oracle['prior_root']).resolve() == prior, 'Existing frozen historical evidence root differs')
        groups, components = [], {}
        for group in ('dev', 'confirm'):
            result, found = audit_group(prior, group, oracle, evidence); groups.append(result)
            for ident, row in found.items():
                if ident in components:
                    components[ident] = combine_component(components[ident], row)
                else:
                    components[ident] = row
        require(sum(g['original_B0_events'] for g in groups) == 85, 'Exact original85 B0 events required')
        for group in groups:
            ids = {i for s in group['sources'] for i in s['component_ids']}
            group['distinct_components'] = len(ids)
            group['component_eligibility_counts'] = status_counts(components[i] for i in ids)
            group['native64_eligible_components'] = sum(components[i]['has_at_least64_distinct_native_frames'] for i in ids)
            group['metadata_cache64_eligible_components'] = sum(components[i]['eligibility_status'] == ELIGIBILITY_STATES[2] for i in ids)
            group['events_without_new_native_frames'] = sum(s['events_without_new_native_frames'] for s in group['sources'])
            for source in group['sources']:
                source['metadata_cache64_eligible_components'] = sum(components[i]['eligibility_status'] == ELIGIBILITY_STATES[2] for i in source['component_ids'])
            group['metadata_cache64_eligible_source_count'] = sum(s['metadata_cache64_eligible_components'] > 0 for s in group['sources'])
        payload = dict(schema='RESIDUAL_NATIVE64_METADATA_ELIGIBILITY_V1',
            status='COMPLETE_METADATA_ONLY_ELIGIBILITY_NOT_INPUT_OR_MODEL_ADMISSION', prior_root=str(prior),
            groups=groups, distinct_source_component_count=len(components), component_eligibility_counts=status_counts(components.values()),
            distinct_source_count=len({s['source_sha256'] for g in groups for s in g['sources']}),
            components=[components[i] for i in sorted(components)], evidence_files=evidence.files,
            source_code=dict(path=str(Path(__file__).resolve()), sha256=sha(__file__)),
            candidate_policy='All85 unpadded original B0 events minus saved VERIFY baseline native set; maximal consecutive native ordinal components, deduplicated by sourceSHA/start/end; no human score selection',
            physical_input_contract=dict(required_distinct_native_frames=64, padding_or_repetition_permitted=False,
                metadata_cache_eligibility_is_not_current_byte_identity_or_first_input_QA=True),
            human_reference_files_read=0, human_metrics_computed=0, old_comparisons_or_oracles_repeated=0,
            human_metric_fields_used_for_component_selection=False,
            new_RGB_payloads_read=0, new_decode_or_processor_calls=0, new_model_calls=0, new_training_updates=0,
            missing_or_short_components_not_empty_success=True, unselected_or_UNKNOWN_is_not_ordinary=True,
            historical_exposure=True, new_blind_sources=0, input_or_model_or_production_admitted=False)
        save(out/'result.json', payload)
        print(json.dumps(dict(status=payload['status'], components=len(components), groups=[
            {k: g[k] for k in ('group', 'native64_eligible_source_count', 'metadata_cache64_eligible_source_count')} for g in groups])))
        return payload
    except BaseException as error:
        save(out/'failure.json', dict(error=repr(error), traceback=traceback.format_exc(), evidence_files=evidence.files,
             old_files_modified=False, short_or_missing_inputs_not_replaced=True, implicit_retry=False))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', required=True, type=Path)
    parser.add_argument('--prior', default=PRIOR, type=Path)
    args = parser.parse_args(); main(args.root, args.prior)
