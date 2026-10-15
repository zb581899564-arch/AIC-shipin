"""Independent CPU duration evaluation of new base-only12 output.

No model, tokenizer, tensor encoding, replay or media decoding is performed.
The parent pilot owns token/parser/native output replay. This evaluator binds
its completion and evaluates exact rational interval/native membership only.
"""
import argparse
import datetime
import hashlib
import json
import os
from bisect import bisect_left
from fractions import Fraction as F
from pathlib import Path

BASE = Path('/home/inspur/aic_video_work')
PILOT = BASE/'twenty_hour_five_20261014_v1/base_only_pilot'
OUT = BASE/'twenty_hour_five_20261014_v1/temporal_diagnosis/base_only_eval_01'
OLD = BASE/'videoxum_reference_iteration_20261013_v1'
SCHEMA = 'INDEPENDENT_BASE_ONLY12_SUMMARY_DEVELOPMENT_EVALUATION_01'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, body):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(body, stream, ensure_ascii=False, indent=2, allow_nan=False)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def merge(spans):
    result = []
    for a, b in sorted(spans):
        if a >= b:
            continue
        if result and a <= result[-1][1]:
            result[-1] = (result[-1][0], max(result[-1][1], b))
        else:
            result.append((a, b))
    return result


def measure(spans):
    return sum((b-a for a, b in merge(spans)), F(0))


def intersect(a, b):
    return merge((max(x, p), min(y, q)) for x, y in a for p, q in b if max(x, p) < min(y, q))


def interval_spans(windows, d8):
    result = []
    for w in windows:
        origin, limit = F(w['start_exact']), F(w['end_exact'])
        for a, b in w['segments']:
            a, b = F(str(a)), F(str(b))
            require(0 <= a < b <= limit-origin, 'coarse interval outside frozen window')
            # Calculate once from this arm's own coarse endpoints, never from
            # already padded endpoints. D8 is identical for old and new arms.
            pre = F(3, 4) if d8 else F(0)
            post = F(1, 2)+(F(1, 4) if b-a >= 8 else 0) if d8 else F(0)
            result.append((max(origin, origin+a-pre), min(limit, origin+b+post)))
    return merge(result)


def paired_metrics(pred, ref):
    selected, reference, hit = measure(pred), measure(ref), measure(intersect(pred, ref))
    return dict(precision=hit/selected if selected else F(0), recall=hit/reference if reference else F(0), f1=2*hit/(selected+reference) if selected+reference else F(0), selected_duration=selected, reference_duration=reference, intersection_duration=hit)


def average_metrics(pred, refs):
    values = [paired_metrics(pred, ref) for ref in refs]
    return {k: sum((x[k] for x in values), F(0))/len(values) for k in values[0]}, values


def encoded(value):
    if isinstance(value, F):
        return dict(exact=str(value), value=float(value))
    if isinstance(value, dict):
        return {k: encoded(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [encoded(v) for v in value]
    return value


def native_frames(points, spans):
    result = set()
    for a, b in spans:
        result.update(range(bisect_left(points, a), bisect_left(points, b)))
    return result


def fixed_inputs(root):
    registration_path = root/'registration_input_01.json'
    reg = read(registration_path)
    require(len(reg['rows']) == 12 and len({x['case_id'] for x in reg['rows']}) == 12, 'fixed twelve distinct cases')
    require(all(x['original_group'] == 'screen' and x['already_exposed'] and x['case_id'].endswith('_W000') for x in reg['rows']), 'only original exposed screen W000')
    export_path = OLD/'developer_prediction_export.json'
    accepted = read(OLD/'developer_export_acceptance.json')
    require(accepted['developer_prediction_export_sha256'] == sha(export_path), 'old successful export changed')
    sources = {x['source_name']: x for x in read(export_path)['rows']}
    bindings = {str(registration_path): sha(registration_path), str(export_path): sha(export_path), str(root/'old_trained_B_proxy_baseline_01.json'): sha(root/'old_trained_B_proxy_baseline_01.json')}
    for e in reg['rows']:
        for path_key, sha_key in [('original_done_path', 'original_done_sha256'), ('source_clock_path', 'source_clock_sha256'), ('author_reference_path', 'author_reference_sha256'), ('old_independent_replay_path', 'old_independent_replay_sha256'), ('input_path', 'input_sha256')]:
            require(sha(e[path_key]) == e[sha_key], 'frozen metadata/reference changed: '+path_key)
            bindings[e[path_key]] = e[sha_key]
        require(sha(e['entry']['proof_path']) == e['entry']['proof_sha256'], 'old independent CPU tensor proof changed')
        bindings[e['entry']['proof_path']] = e['entry']['proof_sha256']
        require(e['source_name'] in sources, 'registered source not in old full-source export')
        old = sources[e['source_name']]
        require(old['windows'][0]['segments'] == read(e['original_done_path'])['segments'], 'export vs frozen original W000 answer')
    return reg, sources, bindings


def register(root, out):
    out.mkdir(parents=True, exist_ok=True)
    require(not (out/'policy_01.json').exists(), 'policy already registered; do not repeat')
    reg, sources, bindings = fixed_inputs(root)
    policy = dict(schema=SCHEMA, registered_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), status='FROZEN_BEFORE_NEW_EVALUATION', sources=12, annotators_per_source=10, selection='Existing frozen accepted source order, every screen source W000; no labels/prediction severity used.', scope='Already exposed external VideoXum summary development proxy; not blind confirmation, dense highlight truth, spatial evaluation or official score.', root=str(root), evaluator_path=str(Path(__file__).resolve()), evaluator_sha256=sha(Path(__file__).resolve()), input_bindings=bindings, gates=dict(full_source_D8_macro_paired_F1_delta_min_exact='0', source_mean_D8_F1_loss_max_exact='1/20', invalid_outputs_max=0, native_changed_sources_min=3), padding='Each arm starts with its own coarse endpoints; pre3/4,post1/2 plus1/4 iff coarse duration>=8; apply once and clip to original inference window.', original_failure_and_quality_gates_unchanged=True, whole_source='Replace W000 only; all original windows1..end remain byte-for-byte content identical.', window_reference='Intersect each of all10 manual interval references with exact W000 native time domain; full-source metrics retain original unmodified reference intervals.', empty_policy='LEGAL_EMPTY is valid and zero selected duration; rate is descriptive and never a success condition.', CPU_tensor_policy='Reference accepted old CPU proof and independent replay metadata; never encode old inputs again. Parent pilot independently replays new token/parser/native output.', no_test_input=True, new_model_calls=0, new_CPU_encoding=0, new_CPU_replay=0)
    save(out/'policy_01.json', policy)
    print(json.dumps(dict(status=policy['status'], path=str(out/'policy_01.json'), sha256=sha(out/'policy_01.json'))))


def evaluate(root, out):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU evaluation must hide CUDA')
    require(not (out/'result_01.json').exists(), 'completed evaluation must not repeat')
    policy = read(out/'policy_01.json')
    require(policy['evaluator_sha256'] == sha(Path(__file__).resolve()), 'pre-registered evaluator changed')
    reg, sources, bindings = fixed_inputs(root)
    require(bindings == policy['input_bindings'], 'pre-registered evaluation input bindings changed')
    terminal_path = root/'gpu_01/completion.json'
    replay_path = root/'replay_01/completion.json'
    gpu, replay = read(terminal_path), read(replay_path)
    require(gpu['status'] == 'PASS_12_NEW_BASE_ONLY_CALLS_NOT_QUALITY' and gpu['calls'] == 12 and len(gpu['entries']) == 12, 'new complete twelve calls required')
    require(replay['status'] == 'PASS_ALL12_NEW_OUTPUT_REPLAYS' and replay['new_CPU_encoding'] == 0 and replay['prior_independent_input_proofs_reused'] == 12 and len(replay['proofs']) == 12, 'parent twelve independent new-output replays required')
    require(replay['gpu_completion_sha256'] == sha(terminal_path), 'new replay binding differs')
    accepted = {x['case_id']: x for x in gpu['entries']}
    proofs = {x['case_id']: x for x in replay['proofs']}
    require(set(accepted) == set(proofs) == {e['case_id'] for e in reg['rows']}, 'new source denominator changed')
    rows, invalid, old_empty, new_empty = [], [], 0, 0
    metric_names = ['old_raw_window', 'new_raw_window', 'old_D8_window', 'new_D8_window', 'old_raw_full', 'new_raw_full', 'old_D8_full', 'new_D8_full']
    for e in reg['rows']:
        case = e['case_id']
        done_path = Path(accepted[case]['done_path'])
        require(done_path.resolve().is_relative_to((root/'gpu_01').resolve()), 'new done outside pilot output')
        require(sha(done_path) == accepted[case]['done_sha256'], 'new done changed')
        require(sha(proofs[case]['path']) == proofs[case]['sha256'], 'new independent replay proof changed')
        done, replay_proof = read(done_path), read(proofs[case]['path'])
        require(replay_proof['status'] == 'PASS_NEW_CPU_TOKEN_GRAMMAR_PARSER_NATIVE_WITH_PRIOR_INDEPENDENT_TENSOR_PROOF' and replay_proof['done_sha256'] == sha(done_path) and replay_proof['new_CPU_encoding'] == 0, 'new output replay proof differs')
        require(done['case_id'] == case and done['source_name'] == e['source_name'], 'new output source identity')
        old = sources[e['source_name']]
        clock = read(e['source_clock_path'])
        meta = read(e['input_path'])
        points = list(map(F, clock['original_exact_pts']))
        require(clock['source_sha256'] == e['source_sha256'] and clock['original_exact_pts'] == meta['all_source_exact_pts'] and len(points) == clock['native_frames'], 'existing full native clock differs')
        require(points[0] == 0 and all(a < b for a, b in zip(points, points[1:])), 'native clock invalid')
        domain = [(F(e['window_start_exact']), F(e['window_end_exact']))]
        old_window = old['windows'][0]
        require(F(old_window['start_exact']) == domain[0][0] and F(old_window['end_exact']) == domain[0][1], 'W000 frozen window differs')
        refs = [[(F(a), F(b)) for a, b in ref] for ref in read(e['author_reference_path'])[0]['annotator_intervals_exact_seconds']]
        require(len(refs) == 10 and all(0 <= a < b <= F(clock['physical_end_exact']) for ref in refs for a, b in ref), 'unmodified all-ten native reference domain')
        window_refs = [intersect(ref, domain) for ref in refs]
        old_empty += not old_window['segments']
        if done['status'] != ('MODEL_OK' if done['segments'] else 'LEGAL_EMPTY'):
            invalid.append(dict(case_id=case, reason='new status contradicts segments'))
            continue
        new_empty += not done['segments']
        new_window = {**old_window, 'segments': done['segments'], 'original_status': done['status']}
        new_full = [new_window, *old['windows'][1:]]
        require(new_full[1:] == old['windows'][1:], 'other successful original windows changed')
        try:
            old_raw_window, new_raw_window = interval_spans([old_window], False), interval_spans([new_window], False)
            old_d8_window, new_d8_window = interval_spans([old_window], True), interval_spans([new_window], True)
            old_raw_full, new_raw_full = interval_spans(old['windows'], False), interval_spans(new_full, False)
            old_d8_full, new_d8_full = interval_spans(old['windows'], True), interval_spans(new_full, True)
        except ValueError as err:
            invalid.append(dict(case_id=case, reason=str(err)))
            continue
        for a, b in new_raw_window:
            if bisect_left(points, a) >= bisect_left(points, b):
                invalid.append(dict(case_id=case, reason='coarse interval has zero native frame'))
                break
        if any(x['case_id'] == case for x in invalid):
            continue
        span_values = [old_raw_window, new_raw_window, old_d8_window, new_d8_window, old_raw_full, new_raw_full, old_d8_full, new_d8_full]
        metrics, per_annotator = {}, {}
        for name, predicted in zip(metric_names, span_values):
            metrics[name], per_annotator[name] = average_metrics(predicted, window_refs if name.endswith('_window') else refs)
        before, after = native_frames(points, old_d8_full), native_frames(points, new_d8_full)
        window_duration, source_duration = domain[0][1]-domain[0][0], F(clock['physical_end_exact'])
        coverage = {name: measure(predicted)/(window_duration if name.endswith('_window') else source_duration) for name, predicted in zip(metric_names, span_values)}
        delta = metrics['new_D8_full']['f1']-metrics['old_D8_full']['f1']
        rows.append(dict(case_id=case, source_name=e['source_name'], already_exposed=True, metrics=metrics, annotator_metrics=per_annotator, selected_time_fraction=coverage, old_legal_empty=not old_window['segments'], new_legal_empty=not new_window['segments'], actual_native_frames_changed=before != after, added_native_frames=len(after-before), removed_native_frames=len(before-after), full_source_D8_mean_F1_delta=delta, source_loss_gate=delta >= -F(1, 20), source_end_exact=clock['physical_end_exact'], window_start_exact=e['window_start_exact'], window_end_exact=e['window_end_exact'], other_old_windows_preserved=True, new_done_sha256=sha(done_path)))
    require(len(rows)+len(invalid) == 12, 'evaluation denominator changed')
    complete = len(rows) == 12 and not invalid
    macro = {name: {key: sum((r['metrics'][name][key] for r in rows), F(0))/12 for key in ['f1', 'precision', 'recall']} for name in metric_names} if complete else None
    delta = macro['new_D8_full']['f1']-macro['old_D8_full']['f1'] if complete else None
    changed = sum(r['actual_native_frames_changed'] for r in rows)
    if complete:
        frozen_baseline = read(root/'old_trained_B_proxy_baseline_01.json')
        require(abs(float(macro['old_D8_full']['f1'])-frozen_baseline['macro_full_source_D8_f1']) < 1e-12 and abs(float(macro['old_D8_window']['f1'])-frozen_baseline['macro_window_D8_f1']) < 1e-12, 'independent evaluator does not reproduce frozen old baseline')
    gates = dict(full_source_macro_paired_F1_not_lower=bool(complete and delta >= 0), each_source_mean_F1_loss_at_most_005=complete and all(r['source_loss_gate'] for r in rows), invalid_zero=not invalid, at_least_three_actual_native_changed_sources=changed >= 3)
    passed = complete and all(gates.values())
    value = dict(schema=SCHEMA, status='PASS_SUMMARY_DEVELOPMENT_PROXY_GATE_NOT_HIGHLIGHT_CONFIRM' if passed else 'REJECT_SUMMARY_DEVELOPMENT_PROXY_GATE', utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), sources=12, evaluated_sources=len(rows), annotators_per_source=10, all_sources_already_exposed=True, scientific_scope=policy['scope'], policy_sha256=sha(out/'policy_01.json'), registration_input_sha256=sha(root/'registration_input_01.json'), evaluator_sha256=sha(Path(__file__).resolve()), gpu_completion_sha256=sha(terminal_path), replay_completion_sha256=sha(replay_path), macro=macro, paired_full_source_D8_macro_F1_delta=delta, gate_checks=gates, development_proxy_gate_pass=passed, actual_native_changed_sources=changed, invalid_count=len(invalid), invalid_outputs=invalid, old_valid_empty_windows=old_empty, new_valid_empty_windows=new_empty, empty_rate_is_not_a_success_condition=True, mean_selected_time_fraction={name: sum((r['selected_time_fraction'][name] for r in rows), F(0))/12 for name in metric_names} if complete else None, padding_applied_once_from_each_arms_coarse=True, all_other_old_windows_preserved=True, old_scientific_gates_changed=False, production_or_blind_confirmation_admitted=False, new_model_calls=0, new_CPU_encoding=0, new_CPU_replay=0, media_reads=0, rows=rows)
    save(out/'result_01.json', encoded(value))
    print(json.dumps(dict(status=value['status'], path=str(out/'result_01.json'), development_proxy_gate_pass=passed, macro_delta=float(delta) if delta is not None else None, changed_sources=changed, invalid_count=len(invalid), new_valid_empty_windows=new_empty)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=['register', 'evaluate'])
    parser.add_argument('--root', type=Path, default=PILOT)
    parser.add_argument('--out', type=Path, default=OUT)
    args = parser.parse_args()
    globals()[args.stage](args.root, args.out)
