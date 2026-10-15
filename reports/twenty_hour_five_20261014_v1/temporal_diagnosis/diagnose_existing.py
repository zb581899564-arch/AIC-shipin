"""CPU-only descriptive audit of four completed external B cohorts.

Reads only existing JSON exports, successful raw/request JSON and VideoXum
manual-summary interval JSON. Never reads media, tensor arrays or test data.
"""
import datetime
import hashlib
import json
from fractions import Fraction as F
from pathlib import Path
from statistics import median

BASE = Path('/home/inspur/aic_video_work')
OUT = BASE / 'twenty_hour_five_20261014_v1/temporal_diagnosis'
COHORTS = [
    ('SumMe20', 'human_reference_iteration_20261013_v1', 'developer_prediction_export.json', 'developer_export_acceptance.json', 'human_gpu_01', None),
    ('VideoXum20', 'videoxum_reference_iteration_20261013_v1', 'developer_prediction_export.json', 'developer_export_acceptance.json', 'cohort_gpu_07', 'direct_cohort_06/completion.json'),
    ('SumMe5', 'duration_guard_iteration_20261013_v1', 'developer_prediction_export.json', 'developer_export_acceptance.json', 'new5_gpu_01', None),
    ('VideoXum8', 'sparse_context_iteration_20261013_v1', 'new_confirm_prediction_export.json', 'new_confirm_export_acceptance.json', 'new_confirm_gpu_04', 'new_confirm_CPU_02/completion.json'),
]


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def merged(spans):
    out = []
    for a, b in sorted(spans):
        if not a < b:
            continue
        if out and a <= out[-1][1]:
            out[-1] = (out[-1][0], max(out[-1][1], b))
        else:
            out.append((a, b))
    return out


def measure(spans):
    return sum((b-a for a, b in merged(spans)), F(0))


def intersection(a, b):
    return merged((max(x, p), min(y, q)) for x, y in a for p, q in b if max(x, p) < min(y, q))


def stats(values):
    s = sorted(map(float, values))
    if not s:
        return dict(n=0)
    return dict(n=len(s), minimum=s[0], median=median(s), mean=sum(s)/len(s), maximum=s[-1], p90=s[min(len(s)-1, int(len(s)*.9))])


def spans(windows, d8=False):
    result = []
    for w in windows:
        lo, hi = F(w['start_exact']), F(w['end_exact'])
        for a, b in w['segments']:
            a, b = F(str(a)), F(str(b))
            if not (0 <= a < b <= hi-lo):
                raise ValueError('Export interval outside frozen external window')
            pre, post = (F(3, 4), F(3, 4) if b-a >= 8 else F(1, 2)) if d8 else (0, 0)
            result.append((max(lo, lo+a-pre), min(hi, lo+b+post)))
    return merged(result)


def consensus_spans(references, minimum=5):
    # Descriptive >=5/10 summary support, not a new classifier or GT.
    changes = {}
    for ref in references:
        for a, b in merged(ref):
            changes[a] = changes.get(a, 0)+1
            changes[b] = changes.get(b, 0)-1
    items = sorted(changes.items())
    count = 0
    result = []
    for i, (point, delta) in enumerate(items[:-1]):
        count += delta
        if count >= minimum:
            result.append((point, items[i+1][0]))
    return merged(result)


def metric(pred, ref):
    p, r, hit = measure(pred), measure(ref), measure(intersection(pred, ref))
    precision = hit/p if p else F(0)
    recall = hit/r if r else F(0)
    f1 = 2*hit/(p+r) if p+r else F(0)
    return dict(precision=float(precision), recall=float(recall), f1=float(f1), intersection_seconds=float(hit), reference_seconds=float(r), predicted_seconds=float(p), predicted_outside_this_summary_seconds=float(p-hit), missed_summary_seconds=float(r-hit))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    cohorts, all_windows, source_rows, bindings = [], [], [], []
    for name, dirname, export_name, acceptance_name, gpu_name, ref_complete_name in COHORTS:
        root = BASE/dirname
        acceptance = read(root/acceptance_name)
        export_path = root/export_name
        if acceptance['status'] != 'PASS_COMPLETE_B_EXPORT_AND_INDEPENDENT_CPU_REPLAY' or acceptance['developer_prediction_export_sha256'] != sha(export_path):
            raise ValueError('Existing successful export acceptance changed')
        payload = read(export_path)
        if payload['status'] != 'PASS_NEW_B_NATIVE_INFERENCE_AND_INDEPENDENT_CPU_REPLAY' or payload['model_parameters'] != 8782459120 or payload['reference_labels_read'] or payload['new_optimizer_updates']:
            raise ValueError('Existing original B cohort identity changed')
        bindings.append(dict(cohort=name, export_path=str(export_path), export_sha256=sha(export_path), acceptance_path=str(root/acceptance_name), source_lock_sha256=payload['source_lock_sha256']))
        raws = {}
        for entry in read(root/gpu_name/'completion.json')['entries']:
            done_path = Path(entry['done_path'])
            done, raw, request = read(done_path), read(done_path.parent/'raw.json'), read(done_path.parent/'request.json')
            if sha(done_path) != entry['done_sha256'] or not raw['actual_model_call'] or request['reference_labels_read']:
                raise ValueError('Existing successful raw/request binding changed')
            key = (request['source_name'], F(request['source_start_exact']))
            if key in raws:
                raise ValueError('Duplicate successful external model window')
            raws[key] = (raw, request, done_path.parent)
        references = {}
        if ref_complete_name:
            for row in read(root/ref_complete_name)['accepted']:
                path = Path(row['reference_path'])
                if sha(path) != row['reference_sha256']:
                    raise ValueError('Frozen original manual summary reference changed')
                ref = read(path)[0]
                references[row['video_id']] = [[(F(a), F(b)) for a, b in x] for x in ref['annotator_intervals_exact_seconds']]
        cohort_windows = []
        for row in payload['rows']:
            windows = row['windows']
            end = F(row['native_clock']['physical_end_exact'])
            if F(windows[0]['start_exact']) != 0 or F(windows[-1]['end_exact']) != end or any(F(a['end_exact']) != F(b['start_exact']) for a, b in zip(windows, windows[1:])):
                raise ValueError('External source windows do not exactly partition full native time')
            for index, w in enumerate(windows):
                lo, hi = F(w['start_exact']), F(w['end_exact'])
                raw, request, folder = raws[(row['source_name'], lo)]
                if sha(folder/'raw.json') != w['original_raw_sha256']:
                    raise ValueError('Export points to another raw answer')
                ev = raw['input_evidence']
                pts = list(map(F, ev['sample_exact_pts']))
                ordinals = ev['source_frame_ordinals']
                if len(pts) != 64 or len(set(ordinals)) != 64 or ev['physical_frames'] != 64 or ev['truncation']:
                    raise ValueError('Existing successful native64 input differs')
                segs = [(F(str(a)), F(str(b))) for a, b in w['segments']]
                endpoints = [x for ab in segs for x in ab]
                ss = dict(cohort=name, source_name=row['source_name'], window_index=index, case_id=request['case_id'], window_start_exact=str(lo), window_end_exact=str(hi), duration_seconds=float(hi-lo), segments=len(segs), legal_empty=not segs, selected_fraction=float(measure(segs)/(hi-lo)), sample_step_seconds=[float(b-a) for a, b in zip(pts, pts[1:])], first_sample_offset_seconds=float(pts[0]-lo), unobserved_tail_seconds=float(hi-pts[-1]), endpoints=len(endpoints), half_second_grid_endpoints=sum((2*x).denominator == 1 for x in endpoints), endpoints_close_last_sample=sum(abs(x-(pts[-1]-lo)) <= F(1, 10000) for x in endpoints), start_zero=sum(a == 0 for a, b in segs), end_within_last_sample_step=sum(b >= pts[-2]-lo for a, b in segs), endpoint_distance_to_nearest_observed_seconds=[float(min(abs(lo+x-t) for t in pts)) for x in endpoints], raw_path=str(folder/'raw.json'), request_path=str(folder/'request.json'), generation_seconds=raw['generation_seconds'])
                # Last observed frame equality demonstrates censoring only; it is not event GT.
                cohort_windows.append(ss)
                all_windows.append(ss)
            pred, d8 = spans(windows), spans(windows, True)
            sr = dict(cohort=name, source_name=row['source_name'], original_group=row.get('group', 'already_exposed'), native_duration_seconds=float(end), windows=len(windows), original_B_selected_seconds=float(measure(pred)), D8_selected_seconds=float(measure(d8)), raw_selected_fraction=float(measure(pred)/end), D8_selected_fraction=float(measure(d8)/end), internal_window_boundaries=len(windows)-1)
            if references:
                refs = references[row['source_name']]
                if len(refs) != 10:
                    raise ValueError('Ten original summary annotators required')
                boundaries = [F(w['end_exact']) for w in windows[:-1]]
                majority = consensus_spans(refs)
                unit_rows = []
                for ai, ref in enumerate(refs):
                    for ri, interval in enumerate(ref):
                        hit = measure(intersection(pred, [interval]))
                        d8hit = measure(intersection(d8, [interval]))
                        unit_rows.append(dict(annotator_index=ai, interval_index=ri, start_exact=str(interval[0]), end_exact=str(interval[1]), duration_seconds=float(interval[1]-interval[0]), raw_overlap_seconds=float(hit), D8_overlap_seconds=float(d8hit), internal_window_boundaries_inside=sum(interval[0] < b < interval[1] for b in boundaries)))
                sr['summary_proxy'] = dict(annotators=10, original_B=[metric(pred, ref) for ref in refs], D8=[metric(d8, ref) for ref in refs], reference_interval_units=len(unit_rows), reference_interval_units_fully_missed_raw=sum(x['raw_overlap_seconds'] == 0 for x in unit_rows), reference_interval_units_fully_missed_D8=sum(x['D8_overlap_seconds'] == 0 for x in unit_rows), reference_interval_units_straddling_internal_window=sum(x['internal_window_boundaries_inside'] > 0 for x in unit_rows), majority_summary_reference=metric(pred, majority), D8_majority_summary_reference=metric(d8, majority), majority_summary_interval_units=len(majority), majority_summary_interval_units_fully_missed_raw=sum(not intersection(pred, [x]) for x in majority), majority_summary_interval_units_fully_missed_D8=sum(not intersection(d8, [x]) for x in majority), units=unit_rows)
            source_rows.append(sr)
        cohorts.append(dict(cohort=name, sources=len(payload['rows']), windows=len(cohort_windows), legal_empty_windows=sum(w['legal_empty'] for w in cohort_windows), model_calls_successfully_reused=len(cohort_windows), original_call_generation_seconds=sum(w['generation_seconds'] for w in cohort_windows)))
    proxy = [x for x in source_rows if 'summary_proxy' in x]
    summary = dict(status='COMPLETE_CPU_READ_ONLY_EXISTING_EXTERNAL_DIAGNOSIS', utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), new_model_calls=0, new_optimizer_updates=0, new_media_decode=0, new_CPU_processor_calls=0, new_CPU_replays=0, tested_media_or_GT_read=False, all_sources_already_exposed=True, no_old_quality_gate_changes=True, original_model_parameters=8782459120, cohorts=cohorts, sources=len(source_rows), windows=len(all_windows), full_time_partition_coverage_pass=True, sampled_frames_per_window=64, window_duration_seconds=stats([w['duration_seconds'] for w in all_windows]), sample_step_seconds=stats([x for w in all_windows for x in w['sample_step_seconds']]), nearest_observed_frame_to_output_endpoint_seconds=stats([x for w in all_windows for x in w['endpoint_distance_to_nearest_observed_seconds']]), endpoints=sum(w['endpoints'] for w in all_windows), half_second_grid_endpoints=sum(w['half_second_grid_endpoints'] for w in all_windows), endpoints_at_last_observed_frame_rounded4=sum(w['endpoints_close_last_sample'] for w in all_windows), segments=sum(w['segments'] for w in all_windows), segments_start_zero=sum(w['start_zero'] for w in all_windows), segments_end_in_last_observation_step=sum(w['end_within_last_sample_step'] for w in all_windows), legal_empty_windows=sum(w['legal_empty'] for w in all_windows), windows_selected_fraction_at_least_90_percent=sum(w['selected_fraction'] >= .9 for w in all_windows), source_raw_selected_fraction=stats([s['raw_selected_fraction'] for s in source_rows]), source_D8_selected_fraction=stats([s['D8_selected_fraction'] for s in source_rows]), summary_proxy_sources=len(proxy), summary_proxy_annotators=sum(s['summary_proxy']['annotators'] for s in proxy), summary_proxy_original_B_source_macro_f1=sum(sum(m['f1'] for m in s['summary_proxy']['original_B'])/10 for s in proxy)/len(proxy), summary_proxy_D8_source_macro_f1=sum(sum(m['f1'] for m in s['summary_proxy']['D8'])/10 for s in proxy)/len(proxy), summary_proxy_reference_interval_units=sum(s['summary_proxy']['reference_interval_units'] for s in proxy), summary_proxy_units_fully_missed_raw=sum(s['summary_proxy']['reference_interval_units_fully_missed_raw'] for s in proxy), summary_proxy_units_fully_missed_D8=sum(s['summary_proxy']['reference_interval_units_fully_missed_D8'] for s in proxy), summary_proxy_units_straddling_internal_window=sum(s['summary_proxy']['reference_interval_units_straddling_internal_window'] for s in proxy), majority_summary_interval_units=sum(s['summary_proxy']['majority_summary_interval_units'] for s in proxy), majority_summary_interval_units_fully_missed_raw=sum(s['summary_proxy']['majority_summary_interval_units_fully_missed_raw'] for s in proxy), majority_summary_interval_units_fully_missed_D8=sum(s['summary_proxy']['majority_summary_interval_units_fully_missed_D8'] for s in proxy), summary_proxy_warning='VideoXum manual ~15% summaries are preference selections; unselected is UNKNOWN. Repeated annotator interval units are not independent events. Descriptive disagreement is not official highlight error or crop GT.', binding=bindings)
    full = dict(summary=summary, source_rows=source_rows, window_rows=all_windows)
    with (OUT/'observations.json').open('x', encoding='utf-8') as f:
        json.dump(full, f, ensure_ascii=False, indent=2, allow_nan=False)
    summary['remote_full_observations_path'] = str(OUT/'observations.json')
    summary['remote_full_observations_bytes'] = (OUT/'observations.json').stat().st_size
    examples = sorted(proxy, key=lambda s: s['summary_proxy']['D8_majority_summary_reference']['recall'])[:5]
    summary['lowest_D8_majority_summary_overlap_examples'] = [dict(source_name=s['source_name'], cohort=s['cohort'], D8_majority_summary_reference=s['summary_proxy']['D8_majority_summary_reference'], majority_intervals_fully_missed=s['summary_proxy']['majority_summary_interval_units_fully_missed_D8']) for s in examples]
    with (OUT/'summary.json').open('x', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2, allow_nan=False)
    print(json.dumps(summary, ensure_ascii=False, allow_nan=False))


if __name__ == '__main__':
    main()
