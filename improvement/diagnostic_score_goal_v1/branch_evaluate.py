"""New CPU-only external temporal-proxy evaluation of fixed branch margins.

This never reruns an old comparison, fits a threshold, deletes baseline spans,
or grants confirmation/production admission. UNKNOWN is not ordinary truth.
"""
from __future__ import annotations

import argparse
from bisect import bisect_left
from fractions import Fraction as F
import hashlib
import json
import math
import os
from pathlib import Path
import traceback


WORK = Path('/home/inspur/aic_video_work')
PRIOR = WORK/'recall_expansion_verify40_46_20261014_v1'
BRANCHES = {'KEEP', 'UNKNOWN', 'DROP'}
RULE = 'PER_SOURCE_AT_MOST_ONE_POSITIVE_M_KEEP_MAXIMUM_WHOLE_OVERLAP_CANDIDATE'


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def exact(value):
    require(not isinstance(value, (float, bool)), 'Exact time/metric must not use float/bool')
    return F(value)


def number(value):
    return dict(exact=str(value), value=float(value))


def merge_spans(spans):
    result = []
    for a, b in sorted((exact(a), exact(b)) for a, b in spans):
        require(0 <= a < b, 'Invalid exact half-open span')
        if result and a <= result[-1][1]:
            result[-1][1] = max(result[-1][1], b)
        else:
            result.append([a, b])
    return result


def serial_spans(spans):
    return [[str(a), str(b)] for a, b in merge_spans(spans)]


def duration(spans):
    return sum((b-a for a, b in merge_spans(spans)), F(0))


def intersection_duration(first, second):
    a, b = merge_spans(first), merge_spans(second)
    i = j = 0
    total = F(0)
    while i < len(a) and j < len(b):
        total += max(F(0), min(a[i][1], b[j][1])-max(a[i][0], b[j][0]))
        if a[i][1] <= b[j][1]:
            i += 1
        else:
            j += 1
    return total


def native_frames(spans, pts):
    frames = set()
    for a, b in merge_spans(spans):
        frames.update(range(bisect_left(pts, a), bisect_left(pts, b)))
    return frozenset(frames)


def score_proposal(spans, references):
    """Score ONE new shared proposal against all ten full human summaries."""
    require(len(references) == 10, 'All ten original human summaries required')
    p = duration(spans)
    rows = []
    for ref in references:
        g, i = duration(ref), intersection_duration(spans, ref)
        rows.append(dict(f1=F(2)*i/(p+g) if p+g else F(0),
                         recall=i/g if g else F(0), precision=i/p if p else F(0)))
    means = {key: sum((row[key] for row in rows), F(0))/10 for key in rows[0]}
    return dict(**{key: number(value) for key, value in means.items()},
                per_rater=[{key: number(value) for key, value in row.items()} for row in rows],
                selected_duration=number(p), annotator_count=10,
                shared_output_for_all_raters=True)


def _finite_margin(value):
    require(isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value), 'Finite M_KEEP required')
    return float(value)


def deduplicate_candidates(candidates, baseline_spans, pts):
    """Aliases are fixed by earliest event ID BEFORE inspecting margins."""
    baseline = native_frames(baseline_spans, pts)
    seen, unique, aliases = {}, [], []
    ignored_roles = zero = 0
    require(len({c['event_id'] for c in candidates}) == len(candidates), 'Duplicate event ID')
    for candidate in sorted(candidates, key=lambda c: c['event_id']):
        roles = candidate['view_roles']
        require(roles and set(roles) <= {'baseline', 'overlap'}, 'Unrecognized original view roles')
        if 'overlap' not in roles:
            ignored_roles += 1
            continue
        contribution = native_frames([candidate['interval_exact']], pts)-baseline
        if not contribution:
            zero += 1
            continue
        signature = tuple(sorted(contribution))
        if signature in seen:
            aliases.append(dict(event_id=candidate['event_id'], canonical_event_id=seen[signature]))
            continue
        seen[signature] = candidate['event_id']
        unique.append(dict(candidate, M_KEEP=_finite_margin(candidate['M_KEEP']),
                           new_native_frames=len(contribution)))
    return unique, dict(input_candidates=len(candidates), non_overlap_candidates=ignored_roles,
                        zero_new_native_candidates=zero, native_aliases=aliases,
                        effective_distinct_native_contribution_candidates=len(unique),
                        alias_rule='Lexicographically earliest event_id, independent of score/reference')


def select_candidate(candidates):
    positive = [c for c in candidates if _finite_margin(c['M_KEEP']) > 0]
    return min(positive, key=lambda c: (-c['M_KEEP'], c['event_id'])) if positive else None


def pairwise_concordance(rows):
    """Source-local pairs; utility ties omitted, margin ties get half credit."""
    concordant = discordant = margin_ties = utility_ties = 0
    for i, first in enumerate(rows):
        for second in rows[i+1:]:
            utility_delta = exact(first['marginal_f1_exact'])-exact(second['marginal_f1_exact'])
            if not utility_delta:
                utility_ties += 1
                continue
            margin_delta = _finite_margin(first['M_KEEP'])-_finite_margin(second['M_KEEP'])
            if not margin_delta:
                margin_ties += 1
            elif (margin_delta > 0) == (utility_delta > 0):
                concordant += 1
            else:
                discordant += 1
    informative = concordant+discordant+margin_ties
    return dict(concordant_pairs=concordant, discordant_pairs=discordant,
                margin_tied_pairs=margin_ties, utility_tied_pairs=utility_ties,
                informative_pairs=informative,
                concordance=number(F(2*concordant+margin_ties, 2*informative)) if informative else None,
                diagnostic_only=True, cross_source_pairs=0)


def evaluate_source(saved, candidates, pts, references):
    """Old aggregate metrics are copied; only proposals get new scoring."""
    baseline_spans = saved['baseline_spans']
    baseline = native_frames(baseline_spans, pts)
    old_hard = native_frames(saved['augmented_spans'], pts)
    require(baseline <= old_hard, 'Saved old hard KEEP removed baseline')
    require(len(baseline) == saved['baseline_selected_frames']
            and len(old_hard) == saved['augmented_selected_frames'], 'Saved native frame counts disagree')
    unique, inventory = deduplicate_candidates(candidates, baseline_spans, pts)
    chosen = select_candidate(unique)
    spans = serial_spans(list(baseline_spans)+([chosen['interval_exact']] if chosen else []))
    proposed = native_frames(spans, pts)
    require(baseline <= proposed, 'New proposal removed a baseline frame')
    score = score_proposal(spans, references)
    base_f1, hard_f1 = exact(saved['baseline']['f1']['exact']), exact(saved['augmented']['f1']['exact'])
    utilities = []
    for candidate in unique:
        single = score_proposal(list(baseline_spans)+[candidate['interval_exact']], references)
        utilities.append(dict(event_id=candidate['event_id'], case_id=candidate['case_id'],
                              M_KEEP=candidate['M_KEEP'], new_native_frames=candidate['new_native_frames'],
                              marginal_f1_exact=str(exact(single['f1']['exact'])-base_f1)))
    return dict(video_id=saved['video_id'], selected_event_id=chosen['event_id'] if chosen else None,
                selected_case_id=chosen['case_id'] if chosen else None,
                selected_M_KEEP=chosen['M_KEEP'] if chosen else None,
                proposal_spans=spans, proposal=score,
                saved_baseline=saved['baseline'], saved_old_hard_KEEP=saved['augmented'],
                old_aggregate_metrics_recomputed=False,
                proposal_equals_baseline=proposed == baseline,
                baseline_native_frames=len(baseline), proposal_native_frames=len(proposed),
                old_hard_KEEP_native_frames=len(old_hard), new_native_frames=len(proposed-baseline),
                baseline_native_frames_preserved=True,
                versus_old_hard_KEEP=dict(added_native_frames=len(proposed-old_hard),
                                         removed_native_frames=len(old_hard-proposed),
                                         prediction_changed=proposed != old_hard),
                delta_f1_vs_saved_baseline=number(exact(score['f1']['exact'])-base_f1),
                delta_f1_vs_saved_old_hard_KEEP=number(exact(score['f1']['exact'])-hard_f1),
                candidate_inventory=dict(inventory, positive_margin_unique_candidates=sum(c['M_KEEP'] > 0 for c in unique)),
                single_candidate_utilities=utilities,
                source_local_margin_utility=pairwise_concordance(utilities))


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


class Evidence:
    def __init__(self):
        self.files = {}

    def check(self, path, expected=None):
        path = Path(path).resolve()
        require(path.is_relative_to(WORK.resolve()) and path.is_file(), 'Missing/out-of-root evidence: '+str(path))
        digest = sha(path)
        require(expected is None or digest == expected, 'Evidence SHA differs: '+str(path))
        require(str(path) not in self.files or self.files[str(path)] == digest, 'Evidence changed during evaluation')
        self.files[str(path)] = digest
        return path

    def read(self, path, expected=None):
        return json.loads(self.check(path, expected).read_text(encoding='utf-8-sig'))

    def bound(self, reference):
        return self.read(reference['path'], reference['sha256'])


def _unique(rows, key):
    result = {row[key]: row for row in rows}
    require(len(result) == len(rows), 'Duplicate '+key)
    return result


def validate_new_outputs(root, group, evidence):
    dst = root/('branch_'+group+'_03')
    qa = evidence.read(dst/'output_acceptance.json')
    require(qa['status'] == 'PASS_ALL_FIRST_INDEPENDENT_BRANCH_OUTPUT_QA_NOT_QUALITY'
            and qa['new_model_forwards'] == 0, 'First complete new output QA required')
    done = evidence.bound(qa['GPU_completion'])
    require(Path(qa['GPU_completion']['path']).resolve() == (dst/'GPU/completion.json').resolve()
            and done['status'] == 'PASS_ALL_FIRST_COMPLETE_BRANCH_LIKELIHOODS_NOT_QUALITY'
            and done['generation_calls'] == done['training_updates'] == 0
            and done['labels_read'] is False, 'New GPU completion identity differs')
    claim = evidence.read(dst/'GPU/claim.json')
    reg = evidence.bound(claim['registration'])
    require(reg['source_scope'] == 'EXTERNAL_NONTEST_ONLY' and reg['new_training_updates'] == 0
            and group in reg['permitted_groups'] and done['cases'] == reg['expected_cases'][group],
            'Registered new external-only group required')
    model = evidence.bound(done['model_identity'])
    require(model['identity']['logical_parameters'] == 8782459120
            and model['all_144_TIME_layers_enabled'] is True
            and model['original_adapter_disable_flags'] == [False]*144,
            'Actual original enabled TIME model identity required')
    input_qa = evidence.bound(claim['input_acceptance'])
    require(Path(claim['input_acceptance']['path']).resolve() == (dst/'input_acceptance.json').resolve()
            and input_qa['status'] == 'PASS_ALL_FIRST_NEW_FULL_BRANCH_INPUT_QA', 'First input QA binding differs')
    prepared = evidence.bound(input_qa['prepared'])
    case_rows = [evidence.bound(ref) for ref in prepared['entries']]
    case_index = _unique(case_rows, 'case_id')
    expected = {(case_id, branch) for case_id in case_index for branch in BRANCHES}
    require(set(map(tuple, input_qa['explicit_case_branches'])) == expected
            and len(input_qa['explicit_case_branches']) == len(expected)
            and done['cases'] == prepared['cases'] == len(case_index)
            and done['actual_new_forwards'] == claim['expected_forwards'] == len(done['entries']) == len(expected),
            'Complete first branch denominator differs')
    seen = set()
    for reference in done['entries']:
        row = evidence.bound(reference); key = (row['case_id'], row['branch'])
        require(key in expected and key not in seen and row['actual_new_forward'] is True
                and row['labels_read'] is False and row['full_vocab_unprocessed'] is True, 'Foreign/repeated branch output')
        seen.add(key)
        request = evidence.bound(row['request'])
        case = evidence.bound(request['case'])
        require(case == case_index[key[0]] and request['case_id'] == key[0]
                and request['branch'] == key[1], 'Branch request/case binding differs')
        evidence.check(row['raw_logits']['path'], row['raw_logits']['sha256'])
    require(seen == expected, 'Missing successful branch')
    scores = _unique(qa['cases'], 'case_id')
    require(set(scores) == set(case_index), 'Output-QA case denominator differs')
    for score in scores.values():
        _finite_margin(score['M_KEEP'])
        require(set(score['sequence_log_probs']) == set(score['probabilities']) == BRANCHES,
                'All three canonical branches required in QA result')
    return case_index, scores, qa


def evaluate(root, group):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'Only this CPU child must mask CUDA')
    root = Path(root).resolve()
    require(root.is_relative_to(WORK.resolve()) and root != PRIOR.resolve(), 'Separate new work root required')
    destination = root/('branch_'+group+'_03')/'evaluation'
    destination.mkdir(exist_ok=False)
    evidence = Evidence()
    try:
        cases, scores, _ = validate_new_outputs(root, group, evidence)
        oracle = evidence.read(root/'retained_candidate_oracle/result.json')
        require(oracle['status'] == 'COMPLETE_REFERENCE_ASSISTED_DIAGNOSTIC_NOT_PREDICTIONS'
                and Path(oracle['prior_root']).resolve() == PRIOR.resolve(), 'Existing candidate diagnostic identity differs')
        frozen = oracle['evidence_files']
        def old(path):
            p = Path(path).resolve()
            require(str(p) in frozen, 'Historical evidence missing from original diagnostic binding')
            return evidence.read(p, frozen[str(p)])
        groups = _unique(oracle['groups'], 'group')
        require(group in groups, 'Missing bound source group')
        source_rows = _unique(groups[group]['sources'], 'video_id')
        comparison = old(PRIOR/group/'comparison_01/result.json')
        cpu = old(PRIOR/('cpu_acceptance_'+group+'.json'))
        export = old(PRIOR/group/'VERIFY/verification_export.json')
        require(comparison['group'] == cpu['group'] == export['group'] == group
                and cpu['status'] == 'PASS_ALL_RECALL_REAL_CPU_INPUTS_NOT_GPU_ADMISSION'
                and export['status'] == 'PASS_RECALL_VERIFY_EXECUTION_AND_REPLAY_NOT_QUALITY', 'Historical group/status differs')
        saved = _unique(comparison['cases'], 'video_id')
        require(set(saved) == set(source_rows) and len(saved) == 4, 'Complete original four-source group required')
        inputs = {}
        for entry in cpu['entries']:
            meta = evidence.read(entry['input_path'], entry['input_sha256'])
            require(meta['case_id'] == entry['case_id'] and meta['reference_available_to_inference'] is False,
                    'Original source input identity differs')
            inputs[entry['case_id']] = meta
        events = _unique(export['events'], 'event_id')
        event_cases = {event['decision_result']['request_id']: event for event in events.values()}
        require(len(event_cases) == len(events) and set(event_cases) == set(cases), 'Complete original VERIFY/case set differs')
        pools = {name: [] for name in source_rows}
        for case_id, row in cases.items():
            event = event_cases[case_id]; meta = inputs[event['original_case_id']]
            source = source_rows[event['source_name']]
            require(row['event_id'] == event['event_id'] and row['source_name'] == event['source_name'] == meta['source_name']
                    and row['source_sha256'] == event['source_sha256'] == meta['source_sha256'] == source['source_sha256']
                    and row['original_interval_exact'] == event['original_interval_exact'], 'Branch source SHA/event/interval differs')
            original = evidence.bound(row['original_input'])
            require(original['request_id'] == case_id and original['source_sha256'] == row['source_sha256']
                    and original['original_interval_exact'] == row['original_interval_exact']
                    and original['reference_labels_read'] is False, 'Original branch input identity differs')
            roles = meta.get('view_roles', [meta['window_role']])
            require(event.get('view_roles', roles) == roles, 'Original source view aliases differ')
            pools[row['source_name']].append(dict(case_id=case_id, event_id=event['event_id'],
                interval_exact=event['original_interval_exact'], M_KEEP=scores[case_id]['M_KEEP'], view_roles=roles))
        results = []
        for name, source in source_rows.items():
            reference = evidence.bound(source['reference_ref']); clock = evidence.bound(source['native_clock_ref'])
            pts = list(map(exact, clock['original_exact_pts'])); end = exact(clock['physical_end_exact'])
            require(pts and pts[0] == 0 and all(b > a for a, b in zip(pts, pts[1:])) and end > pts[-1], 'Original exact native clock differs')
            refs = reference['annotator_intervals_exact_seconds']
            require(reference['annotator_count'] == len(refs) == 10, 'All ten original reviewers required')
            for spans in refs+[saved[name]['baseline_spans'], saved[name]['augmented_spans']]:
                require(all(0 <= a < b <= end for a, b in merge_spans(spans)), 'Reference/prediction escaped source domain')
            for candidate in pools[name]:
                a, b = map(exact, candidate['interval_exact'])
                require(0 <= a < b <= end, 'Candidate escaped source domain')
            for meta in inputs.values():
                if meta['source_name'] == name:
                    require(meta['original_clock_path'] == source['native_clock_ref']['path']
                            and meta['original_clock_sha256'] == source['native_clock_ref']['sha256']
                            and list(map(exact, meta['all_source_exact_pts'])) == pts,
                            'Actual candidate/native clock binding differs')
            result = evaluate_source(saved[name], pools[name], pts, refs)
            result.update(source_sha256=source['source_sha256'], reference_ref=source['reference_ref'],
                          native_clock_ref=source['native_clock_ref'], historical_exposure=True)
            results.append(result)
        macro = {}
        for metric in ('f1', 'recall', 'precision'):
            values = {arm: sum((exact(row[arm][metric]['exact']) for row in results), F(0))/len(results)
                      for arm in ('proposal', 'saved_baseline', 'saved_old_hard_KEEP')}
            macro[metric] = {arm: number(value) for arm, value in values.items()}
            macro[metric].update(delta_vs_baseline=number(values['proposal']-values['saved_baseline']),
                                 delta_vs_old_hard_KEEP=number(values['proposal']-values['saved_old_hard_KEEP']))
        f1 = macro['f1']
        flags = dict(at_least_two_sources_with_real_new_native_frames=sum(r['new_native_frames'] > 0 for r in results) >= 2,
                     any_source_with_positive_margin_utility_ordering=any(
                         r['source_local_margin_utility']['concordance'] is not None and
                         exact(r['source_local_margin_utility']['concordance']['exact']) > F(1, 2) for r in results),
                     macro_f1_not_below_saved_baseline=exact(f1['delta_vs_baseline']['exact']) >= 0,
                     macro_f1_not_below_saved_old_hard_KEEP=exact(f1['delta_vs_old_hard_KEEP']['exact']) >= 0,
                     all_baseline_native_frames_preserved=all(r['baseline_native_frames_preserved'] for r in results))
        payload = dict(schema='FIXED_BRANCH_MARGIN_CAPABILITY_EVALUATION_V1',
            runtime_sha256=sha(__file__),
            status='COMPLETE_NEW_EXTERNAL_TEMPORAL_PROXY_DIAGNOSTIC_NO_ADMISSION', group=group,
            rule=RULE, threshold=0, maximum_candidates_per_source=1, sources=results, macro=macro, known_flags=flags,
            flags_are_observations_not_automatic_gates=True, automatic_confirm=False, automatic_426=False,
            publication_admitted=False, new_model_calls=0, new_training_updates=0,
            old_comparisons_repeated=0, old_baseline_and_hard_KEEP_aggregate_metrics_recomputed=False,
            proposal_evaluation_including_possible_baseline_identical_proposal=True,
            candidate_counts={key: sum(row['candidate_inventory'][key] for row in results) for key in
                ('input_candidates', 'non_overlap_candidates', 'zero_new_native_candidates',
                 'effective_distinct_native_contribution_candidates', 'positive_margin_unique_candidates')},
            native_alias_candidates=sum(len(row['candidate_inventory']['native_aliases']) for row in results),
            prediction_difference_vs_old_hard_KEEP=dict(
                changed_sources=sum(row['versus_old_hard_KEEP']['prediction_changed'] for row in results),
                added_native_frames=sum(row['versus_old_hard_KEEP']['added_native_frames'] for row in results),
                removed_native_frames=sum(row['versus_old_hard_KEEP']['removed_native_frames'] for row in results)),
            scope='Historical exposed all-ten-human-summary temporal proxy only; unselected/UNKNOWN are not ORDINARY; no IoU; not full40.47 external reconstruction',
            evidence_files=evidence.files)
        save(destination/'result.json', payload)
        return payload
    except BaseException as error:
        save(destination/'failure.json', dict(error=repr(error), traceback=traceback.format_exc(),
             evidence_files=evidence.files, no_admission=True, old_files_modified=False))
        raise


def save(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--group', choices=['dev', 'confirm'], required=True)
    args = parser.parse_args()
    result = evaluate(args.root, args.group)
    print(json.dumps(dict(status=result['status'], group=args.group, known_flags=result['known_flags'])))
