"""CPU-only, reference-assisted COMMON candidate-subset diagnostic.

This creates a new diagnostic, never reruns the historical recall comparison.
All ten original summaries evaluate ONE shared output per source. No oracle
output is a prediction, ordinary label, joint-IoU score or production admission.
"""
from __future__ import annotations

import argparse
from bisect import bisect_left
from collections import Counter
from fractions import Fraction as F
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import traceback

HOME = Path('/home/inspur/aic_video_work')
EXACT_LIMIT = 20
PRIOR_COMPARISON_SHA = {
    'dev': '63cf596d4ab28af4987a13b4da1e394c293f3e1570699a8e3eab34fd38e919f1',
    'confirm': 'ab6021698689cf1682d0953ed524d5f0d0b752b2bc6ecb0702ba6edc4a317bb8',
}


def require(value, message):
    if not value:
        raise ValueError(message)


def exact(value):
    require(not isinstance(value, (bool, float)), 'Exact seconds must be int/string, not float/bool')
    return F(value)


def merged(spans):
    result = []
    for a, b in sorted((exact(a), exact(b)) for a, b in spans):
        require(0 <= a < b, 'Invalid exact half-open interval')
        if result and a <= result[-1][1]:
            result[-1][1] = max(result[-1][1], b)
        else:
            result.append([a, b])
    return result


def number(value):
    return dict(exact=str(value), value=float(value))


def serialize(spans):
    return [[str(a), str(b)] for a, b in merged(spans)]


class UnionMetric:
    """Exact-duration atoms depend on candidates, never on reviewer answers."""
    def __init__(self, candidates, references):
        require(len(references) == 10, 'Exactly all ten original reviewers required')
        self.references = [merged(r) for r in references]
        self.candidates = [merged(c) for c in candidates]
        cuts = sorted({x for c in self.candidates for pair in c for x in pair})
        self.atoms = list(zip(cuts, cuts[1:]))
        weights = [b-a for a, b in self.atoms]
        intersections = [[sum((max(F(0), min(b, d)-max(a, c)) for c, d in r), F(0))
                          for a, b in self.atoms] for r in self.references]
        totals = [sum((b-a for a, b in r), F(0)) for r in self.references]
        denominator = 1
        for q in weights + totals + [v for row in intersections for v in row]:
            denominator = math.lcm(denominator, q.denominator)
        self.totals = [int(q*denominator) for q in totals]
        self.unit = denominator
        # Eight-atom tables keep exact scoring bounded without huge frame arrays.
        values = [[int(q*denominator) for q in weights]] + [
            [int(q*denominator) for q in row] for row in intersections]
        self.tables = []
        for first in range(0, len(weights), 8):
            width = min(8, len(weights)-first)
            table = [(0,)*11]
            for mask in range(1, 1 << width):
                bit = mask & -mask
                j = first+bit.bit_length()-1
                table.append(tuple(a+row[j] for a, row in zip(table[mask ^ bit], values)))
            self.tables.append(table)
        self.masks = []
        for candidate in self.candidates:
            mask = 0
            for j, (a, b) in enumerate(self.atoms):
                if any(c <= a and b <= d for c, d in candidate):
                    mask |= 1 << j
            self.masks.append(mask)

    def components(self, mask):
        result = [0]*11
        for table in self.tables:
            row = table[mask & 255]
            for j in range(11):
                result[j] += row[j]
            mask >>= 8
        require(mask == 0, 'Union mask escaped candidate atoms')
        return result

    def score(self, mask):
        p, *intersections = self.components(mask)
        # Match original duration proxy's zero denominator convention (zero).
        return sum((F(2*i, p+g) if p+g else F(0)
                    for i, g in zip(intersections, self.totals)), F(0))/10

    def describe(self, mask):
        p, *intersections = self.components(mask)
        return dict(mean_paired_duration_f1=number(self.score(mask)),
                    selected_duration=number(F(p, self.unit)),
                    per_rater_recall=[number(F(i, g) if g else F(0))
                                      for i, g in zip(intersections, self.totals)],
                    mean_rater_recall=number(sum((F(i, g) if g else F(0)
                                                  for i, g in zip(intersections, self.totals)), F(0))/10),
                    intervals_exact=serialize([self.atoms[j] for j in range(len(self.atoms)) if mask >> j & 1]))


def common_subset_oracle(candidates, references, exact_limit=EXACT_LIMIT, mandatory_spans=()):
    """Exact <=20; otherwise a deterministic FEASIBLE LOWER BOUND only."""
    require(0 <= exact_limit <= EXACT_LIMIT, 'Cannot expand registered exact enumeration limit')
    metric = UnionMetric(list(candidates)+[list(mandatory_spans)], references)
    candidate_masks, mandatory = metric.masks[:-1], metric.masks[-1]
    require(all(mask > 0 for mask in candidate_masks), 'Candidate with no positive duration')
    # Actions covered by the fixed baseline contribute nothing new. Deduplicate
    # the actual optional contributions, retaining the complete fixed mask.
    unique = sorted({mask & ~mandatory for mask in candidate_masks if mask & ~mandatory})
    n = len(unique)
    best_mask, best_subset, best_score = mandatory, 0, metric.score(mandatory)
    seen = set()
    evaluated = 0

    def visit(mask, subset):
        nonlocal evaluated, best_mask, best_subset, best_score
        if mask in seen:
            return
        seen.add(mask); evaluated += 1
        score = metric.score(mask)
        if score > best_score or (score == best_score and
                (metric.components(mask)[0], subset) < (metric.components(best_mask)[0], best_subset)):
            best_mask, best_subset, best_score = mask, subset, score

    if n <= exact_limit:
        unions = [mandatory]
        visit(mandatory, 0)
        for subset in range(1, 1 << n):
            bit = subset & -subset
            mask = unions[subset ^ bit] | unique[bit.bit_length()-1]
            unions.append(mask); visit(mask, subset)
        method = 'EXACT_COMMON_SUBSET_MAXIMUM_WITHIN_DECLARED_EVENT_POOL'
        enumerated = 1 << n
    else:
        visit(mandatory, 0)
        for i in range(n):
            visit(mandatory | unique[i], 1 << i)
            for j in range(i):
                visit(mandatory | unique[i] | unique[j], (1 << i) | (1 << j))
        # A single deterministic forward path, at most n rounds and n options.
        current, subset = best_mask, best_subset
        for _ in range(n):
            options = [(metric.score(current | mask), i, current | mask)
                       for i, mask in enumerate(unique) if not subset >> i & 1]
            if not options:
                break
            score, i, mask = max(options, key=lambda row: (row[0], -row[1]))
            if score <= metric.score(current):
                break
            subset |= 1 << i; current = mask; visit(current, subset)
        method = 'BOUNDED_FEASIBLE_GREEDY_LOWER_BOUND_NOT_AN_UPPER_BOUND'
        enumerated = None
    union = mandatory
    for mask in unique:
        union |= mask
    require(best_mask & mandatory == mandatory and union & mandatory == mandatory,
            'A feasible oracle result removed mandatory baseline atoms')
    return dict(method=method, exact_optimum=(n <= exact_limit),
                exact_enumeration_limit=exact_limit, input_candidates=len(candidates),
                deduplicated_candidate_masks=n, enumerated_subsets=enumerated,
                evaluated_distinct_unions=evaluated,
                null_choice_allowed=(mandatory == 0), optional_empty_subset_allowed=True,
                mandatory_intervals_exact=serialize(mandatory_spans), mandatory_mask_never_removed=True,
                candidates_already_fully_covered_by_mandatory=sum(not(mask & ~mandatory) for mask in candidate_masks),
                common_output_for_all_ten_raters=True,
                best=metric.describe(best_mask), all_candidate_union=metric.describe(union),
                selected_candidate_mask_indices=[i for i in range(n) if best_subset >> i & 1],
                deduplicated_candidate_intervals=[metric.describe(mask)['intervals_exact'] for mask in unique],
                interpretation='Reference-assisted temporal-summary diagnostic only; never a model prediction or official joint score')


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b''):
            digest.update(chunk)
    return digest.hexdigest()


class Evidence:
    def __init__(self):
        self.files = {}

    def read(self, path, expected=None):
        path = Path(path).resolve()
        require(path.is_relative_to(HOME.resolve()) and path.is_file(), 'Missing/out-of-workspace JSON evidence: '+str(path))
        digest = sha(path)
        require(expected is None or digest == expected, 'Evidence SHA mismatch: '+str(path))
        require(str(path) not in self.files or self.files[str(path)] == digest, 'Evidence changed during diagnosis')
        self.files[str(path)] = digest
        return json.loads(path.read_text(encoding='utf-8-sig'))

    def row(self, row, prefix):
        return self.read(row[prefix+'_path'], row[prefix+'_sha256'])


def index(completion, key):
    rows = completion[key]
    result = {row['case_id']: row for row in rows}
    require(completion['calls'] == len(rows) == len(result), 'Old complete call/proof denominator mismatch')
    return result


def native_projection(spans, pts):
    ranges = []
    for a, b in merged(spans):
        lo, hi = bisect_left(pts, a), bisect_left(pts, b)
        if lo < hi:
            if ranges and lo <= ranges[-1][1]:
                ranges[-1][1] = max(ranges[-1][1], hi)
            else:
                ranges.append([lo, hi])
    return dict(native_ordinal_ranges_half_open=ranges, native_selected_frames=sum(b-a for a, b in ranges))


def diagnose_group(prior, group, evidence):
    cpu_path = prior/('cpu_acceptance_'+group+'.json')
    cpu = evidence.read(cpu_path)
    require(cpu['status'] == 'PASS_ALL_RECALL_REAL_CPU_INPUTS_NOT_GPU_ADMISSION' and cpu['group'] == group
            and cpu['CPU_only'] is True and cpu['CUDA_initialized'] is False, 'Original CPU admission missing')
    completions, proofs = {}, {}
    for stage in ('B0', 'VERIFY'):
        cp = prior/group/stage/'gpu_01/completion.json'
        complete = evidence.read(cp); replay = evidence.read(prior/group/stage/'replay_01/completion.json')
        require(complete['status'] == 'PASS_ALL_RECALL_'+stage+'_CALLS_NOT_QUALITY'
                and replay['status'] == 'PASS_ALL_RECALL_'+stage+'_INDEPENDENT_REPLAYS_NOT_QUALITY'
                and replay['gpu_completion_sha256'] == evidence.files[str(cp.resolve())]
                and complete['calls'] == replay['calls'] and replay['CPU_only'] is True
                and replay['CUDA_initialized'] is False, 'Complete original model/first-QA bindings differ')
        completions[stage], proofs[stage] = index(complete, 'entries'), index(replay, 'proofs')
    export_path = prior/group/'VERIFY/verification_export.json'
    export = evidence.read(export_path)
    require(export['status'] == 'PASS_RECALL_VERIFY_EXECUTION_AND_REPLAY_NOT_QUALITY'
            and export['independent_replay_completion_sha256'] == evidence.files[str((prior/group/'VERIFY/replay_01/completion.json').resolve())]
            and len(export['events']) == len(completions['VERIFY']), 'Original VERIFY export binding differs')
    inputs, old_segments, source_identity = {}, {}, {}
    require([row['case_id'] for row in cpu['entries']] == list(completions['B0']) == list(proofs['B0']), 'Original CPU/B0 order differs')
    for row in cpu['entries']:
        case = row['case_id']; meta = evidence.row(row, 'input'); proof = evidence.row(row, 'proof')
        done = evidence.row(completions['B0'][case], 'done'); qa = evidence.row(proofs['B0'][case], 'proof')
        require(case == meta['case_id'] == proof['case_id'] == done['case_id'] == qa['case_id']
                and proof['input_sha256'] == row['input_sha256'] and qa['done_sha256'] == completions['B0'][case]['done_sha256']
                and qa['segments'] == done['segments'] and qa['native_ranges'] == done['native_ranges']
                and done['source_sha256'] == meta['source_sha256'] and proof['input_evidence'] == done['input_evidence'], 'B0 candidate input/output/QA binding differs')
        require(len(meta['source_frame_ordinals']) == len(set(meta['source_frame_ordinals'])) == 64
                and meta['source_frame_ordinals'] == sorted(meta['source_frame_ordinals'])
                and [meta['all_source_exact_pts'][i] for i in meta['source_frame_ordinals']] == meta['sample_exact_pts']
                and meta['reference_available_to_inference'] is False and meta['audio_observed'] is False, 'Original native64 input contract differs')
        identity = (meta['video_id'], meta['source_sha256'], meta['original_clock_path'], meta['original_clock_sha256'])
        name = meta['source_name']
        require(name not in source_identity or source_identity[name] == identity, 'Crossed source/clock identity')
        source_identity[name] = identity; inputs[case] = meta; old_segments[case] = done['segments']
    pointer = evidence.read(prior/('reference_completion_'+group+'.json'))
    reference_receipt = evidence.read(pointer['path'], pointer['sha256'])
    media = reference_receipt['accepted']
    require(len(media) == len({r['video_id'] for r in media}) == 4 and set(source_identity) == {r['video_id'] for r in media}, 'Complete four-source original reference denominator differs')
    comparison_path = prior/group/'comparison_01/result.json'
    comparison = evidence.read(comparison_path, PRIOR_COMPARISON_SHA[group])
    require(comparison['group'] == group and comparison['bindings']['cpu_acceptance_sha256'] == evidence.files[str(cpu_path.resolve())]
            and comparison['bindings']['verification_export_sha256'] == evidence.files[str(export_path.resolve())]
            and comparison['bindings']['protocol_sha256'] == evidence.files[str((prior/'protocol.json').resolve())], 'Historical baseline comparison binding differs')
    baseline_rows = {r['video_id']: r for r in comparison['cases']}
    require(set(baseline_rows) == set(source_identity), 'Historical baseline source denominator differs')
    pools = {name: [] for name in source_identity}; states = {name: Counter() for name in source_identity}
    retained = {name: [] for name in source_identity}; baseline_all = {name: [] for name in source_identity}
    overlap_pool = {name: [] for name in source_identity}
    baseline_kept = {name: [] for name in source_identity}; seen = set(); requests = set()
    for event in export['events']:
        case, si = event['original_case_id'], event['original_segment_index']; key = (case, si)
        require(key not in seen and case in inputs and 0 <= si < len(old_segments[case]), 'Repeated/foreign candidate')
        seen.add(key); meta = inputs[case]; name = meta['source_name']
        a, b = map(exact, event['original_interval_exact']); lo, hi = exact(meta['window_start']), exact(meta['window_end'])
        require([str(lo+F(str(x))) for x in old_segments[case][si]] == event['original_interval_exact'] and lo <= a < b <= hi
                and event['source_name'] == name and event['source_sha256'] == meta['source_sha256'], 'Original candidate exact endpoint/source differs')
        decision = event['decision_result']; request = decision['request_id']
        require(request not in requests and request in completions['VERIFY'], 'Foreign/repeated VERIFY request')
        requests.add(request)
        vd = evidence.row(completions['VERIFY'][request], 'done'); vq = evidence.row(proofs['VERIFY'][request], 'proof')
        require(vd['decision_result'] == vq['decision_result'] == decision and vq['done_sha256'] == completions['VERIFY'][request]['done_sha256']
                and event['event_id'] == decision['event_id'] and decision['successful_model_call_required'] is True
                and decision['decision'] in ('KEEP', 'UNKNOWN', 'DROP') and decision['original_interval_exact'] == event['original_interval_exact'], 'Original successful VERIFY decision binding differs')
        state = decision['decision']; states[name][state] += 1
        roles = meta.get('view_roles', [meta['window_role']])
        require(roles and set(roles) <= {'baseline', 'overlap'}, 'Unrecognized original window role')
        if 'baseline' in roles:
            span = [[max(lo, a-F(3, 4)), min(hi, b+F(1, 2)+(F(1, 4) if b-a >= 8 else F(0)))]]
            pools[name].append(span); baseline_all[name].append(span)
            if state != 'DROP':
                baseline_kept[name].append(span)
        if 'overlap' in roles:
            span = [[a, b]]; pools[name].append(span)
            overlap_pool[name].append(span)
            if state == 'KEEP':
                retained[name].append(span)
    require(seen == {(case, i) for case, segments in old_segments.items() for i in range(len(segments))}
            and requests == set(completions['VERIFY']), 'Complete candidate/VERIFY denominator differs')
    rows = []
    for source in media:
        name = source['video_id']; identity = source_identity[name]
        require(source['media']['sha256'] == identity[1] and source['clock_path'] == identity[2] and source['clock_sha256'] == identity[3], 'Reference/media/clock identity differs')
        clock = evidence.read(source['clock_path'], source['clock_sha256'])
        reference = evidence.read(source['reference_path'], source['reference_sha256'])
        pts = list(map(exact, clock['original_exact_pts'])); end = exact(clock['physical_end_exact'])
        require(pts and pts[0] == 0 and all(b > a for a, b in zip(pts, pts[1:])) and end > pts[-1], 'Complete original zero-origin native PTS required')
        refs = reference['annotator_intervals_exact_seconds']
        require(reference['annotator_count'] == len(refs) == 10 and all(0 <= exact(a) < exact(b) <= end for r in refs for a, b in r), 'All ten unaltered references must lie in native source domain')
        require(all(0 <= a < b <= end for c in pools[name] for a, b in c), 'Candidate escaped physical source')
        for meta in inputs.values():
            if meta['source_name'] == name:
                require(list(map(exact, meta['all_source_exact_pts'])) == pts, 'Candidate full native clock differs')
        result = common_subset_oracle(pools[name], refs)
        # The fixed spans come directly from the old successful comparison;
        # the old comparison is not rerun. New scoring here is solely the
        # required additive-action optimization, with deletion impossible.
        mandatory = baseline_rows[name]['baseline_spans']
        require(all(0 <= exact(a) < exact(b) <= end for a, b in mandatory), 'Historical mandatory baseline escaped native source domain')
        additive = common_subset_oracle(overlap_pool[name], refs, mandatory_spans=mandatory)
        for key in ('best', 'all_candidate_union'):
            result[key].update(native_projection(result[key]['intervals_exact'], pts))
            additive[key].update(native_projection(additive[key]['intervals_exact'], pts))
        # This new union readout is necessary to distinguish generated coverage
        # from VERIFY retention; no historical F1 comparison is recomputed.
        restored = not baseline_kept[name] and bool(baseline_all[name])
        retained[name] += baseline_all[name] if restored else baseline_kept[name]
        rm = UnionMetric(retained[name], refs); union = 0
        for mask in rm.masks: union |= mask
        row = dict(video_id=name, source_sha256=identity[1], native_clock_ref=dict(path=source['clock_path'], sha256=source['clock_sha256']),
                   reference_ref=dict(path=source['reference_path'], sha256=source['reference_sha256']), historical_exposure=True,
                   original_successful_VERIFY_states={state: states[name][state] for state in ('KEEP', 'UNKNOWN', 'DROP')}, UNKNOWN_is_not_ordinary=True,
                   baseline_reference=dict(name='Historical_B0_D8_PADDING_VERIFY_WITH_SOURCE_EMPTY_GUARD_NOT_40_47',
                       comparison_path=str(comparison_path), comparison_sha256=evidence.files[str(comparison_path.resolve())],
                       previously_computed=baseline_rows[name]['baseline'], recomputed=False),
                   all_actual_B0_candidate_pool=result,
                   fixed_historical_VERIFY_baseline_plus_optional_overlap=additive,
                   additive_action_scope='All historical VERIFY baseline spans fixed; only actual overlap B0 proposal intervals may be added; no deletion; not complete40.47',
                   VERIFY_retained_union=rm.describe(union),
                   original_source_empty_guard_applied=restored)
        row['VERIFY_retained_union'].update(native_projection(row['VERIFY_retained_union']['intervals_exact'], pts))
        rows.append(row)
    return dict(group=group, sources=rows, historical_comparison_repeated=False,
                source_count=4, original_B0_calls=len(completions['B0']), original_VERIFY_calls=len(completions['VERIFY']))


def save(path, value):
    with Path(path).open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def main(root, prior):
    require(sys.platform.startswith('linux') and os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'Linux CPU child must explicitly mask its own CUDA')
    root, prior = root.resolve(), prior.resolve()
    require(root.is_relative_to(HOME.resolve()) and prior.is_relative_to(HOME.resolve()) and root != prior
            and not root.is_relative_to(prior) and not prior.is_relative_to(root), 'New and prior roots must be separate work-root descendants')
    output = root/'retained_candidate_oracle'; output.mkdir(parents=True, exist_ok=False)
    evidence = Evidence()
    try:
        evidence.read(prior/'protocol.json')
        prior_code = prior/'code/evaluate_pilot.py'
        require(prior_code.is_file(), 'Missing original comparison source; request schema evidence instead of guessing')
        code = dict(diagnostic=dict(path=str(Path(__file__).resolve()), sha256=sha(__file__)),
                    original_comparison_source=dict(path=str(prior_code), sha256=sha(prior_code)))
        results = [diagnose_group(prior, group, evidence) for group in ('dev', 'confirm')]
        save(output/'result.json', dict(schema='COMMON_RETAINED_CANDIDATE_ORACLE_DIAGNOSTIC_V1',
            status='COMPLETE_REFERENCE_ASSISTED_DIAGNOSTIC_NOT_PREDICTIONS', prior_root=str(prior), groups=results,
            candidate_policy='All actual B0 events: baseline uses frozen D8 window-clipped padding; overlap uses original unpadded interval; exact interval masks deduplicated. One common subset including null, all ten raters.',
            scope='Historically exposed event-text-guided human summary temporal proxy; unselected is not ORDINARY; no spatial IoU; no complete40.47 external reconstruction',
            original_protocol_sha256=evidence.files[str((prior/'protocol.json').resolve())], source_code=code,
            evidence_files=evidence.files, new_model_calls=0, new_optimizer_updates=0,
            new_decode_or_processor_calls=0, old_comparisons_repeated=0, CPU_only=True,
            publication_or_training_admitted=False))
        print(json.dumps(dict(status='COMPLETE_NEW_CPU_DIAGNOSTIC_ONLY', output=str(output/'result.json'), sources=8)))
    except BaseException as error:
        save(output/'failure.json', dict(error=repr(error), traceback=traceback.format_exc(), evidence_files=evidence.files,
             old_files_modified=False, fallback_or_empty_substitution=False))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--prior', type=Path, required=True)
    args = parser.parse_args()
    main(args.root, args.prior)
