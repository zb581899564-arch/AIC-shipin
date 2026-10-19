"""Read-only CPU decomposition of the frozen utility55 screen20 STOP.

Only JSON/JSONL metadata and the pinned pure31 geometry module are opened.
No tensor, pixel, model, processor, optimizer, fit or threshold scan is used.
The original55/56 result and admission decision remain immutable.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
import time

sys.dont_write_bytecode = True


def require(condition, message):
    if not condition:
        raise ValueError(message)


def number(value):
    require(type(value) in (int, float) and math.isfinite(value), 'Explicit finite number required')
    return float(value)


def mean(values):
    values = list(values)
    return math.fsum(values)/len(values) if values else None


def reference(path):
    path = Path(path).resolve()
    return dict(path=str(path), sha256=hashlib.sha256(path.read_bytes()).hexdigest())


class Metadata:
    def __init__(self):
        self.references = {}

    def bound(self, ref, suffixes=('.json', '.jsonl', '.py')):
        require(set(ref) == {'path', 'sha256'}, 'Exact metadata reference required')
        path = Path(ref['path'])
        require(path.is_absolute() and path.suffix in suffixes, 'Only explicit metadata/code files may be opened')
        require(path.stat().st_size <= 32*1024*1024, 'Bounded metadata size exceeded')
        actual = reference(path)
        require(actual['sha256'] == ref['sha256'], 'Metadata source SHA changed: '+str(path))
        self.references[str(path)] = actual
        return path

    def read(self, ref):
        return json.loads(self.bound(ref, ('.json',)).read_text(encoding='utf-8'))

    def lines(self, ref):
        return [json.loads(line) for line in self.bound(ref, ('.jsonl',)).read_text(encoding='utf-8').splitlines()]


def choose(gains):
    require(gains and number(gains[0]) == 0., 'Exact baseline zero required')
    values = list(map(number, gains))
    best = max(values)
    return values.index(best) if best > 0. else 0


def concordance(predicted, truth):
    """Within-source unequal-target pairs; predicted ties receive half credit."""
    good = bad = ties = 0
    for i in range(len(truth)):
        for j in range(i+1, len(truth)):
            difference = truth[i]-truth[j]
            if difference == 0.:
                continue
            ranked = predicted[i]-predicted[j]
            if ranked == 0.:
                ties += 1
            elif ranked*difference > 0.:
                good += 1
            else:
                bad += 1
    count = good+bad+ties
    return dict(concordant=good, discordant=bad, predicted_ties=ties, comparable_pairs=count,
                rate=(good+.5*ties)/count if count else None)


def descriptor(box, width, height):
    x, y, w = box
    maximum = min(width, 16*height//9)
    return [w/maximum, (x+w/2-width/2)/maximum,
            (y+9*w/32-height/2)/(9*maximum/16)]


def screen_decomposition(sources, predictions, geometry):
    require(len(sources) == len(predictions) == 20, 'Exact historical screen20 required')
    lookup = {row['source_id']: row for row in predictions}
    require(len(lookup) == 20 and set(lookup) == {s['source_id'] for s in sources}, 'Exact screen owner set required')
    rows = []; candidates = []; confusion = Counter()
    for source in sources:
        sid = source['source_id']; prediction = lookup[sid]
        require(source['role'] == 'screen' and source['source_sha256'] == prediction['source_sha256'], 'Screen owner/SHA mismatch')
        pool = source['pool']; truth = list(map(number, source['candidate_ious']))
        require(source['original_BASE_observed'] is True and source['reference_modified'] is False
                and source['baseline_index'] == 0 and source['baseline_box'] == pool[0], 'Adopt unchanged actual BASE and original reference')
        require(len(pool) == len(truth) and all(0. <= x <= 1. for x in truth), 'Complete saved native-pool IoUs required')
        scores = list(map(number, prediction['predicted_gains']['UTILITY']))
        require(len(scores) == len(pool), 'Missing candidate score cannot silently abstain')
        selected = choose(scores)
        require(selected == prediction['choices']['UTILITY'], 'Frozen strict-zero/earliest policy decision changed')
        gains = [v-truth[0] for v in truth]
        positive = [i for i in range(1, len(pool)) if gains[i] > 0.]
        predicted_positive = [i for i in range(1, len(pool)) if scores[i] > 0.]
        true_positive = [i for i in positive if scores[i] > 0.]
        oracle = gains.index(max(gains))
        top_nonbase = max(range(1, len(pool)), key=lambda i: scores[i])
        synthetic = geometry.candidate_pool(source['width'], source['height'])
        require(pool == geometry.candidate_pool(source['width'], source['height'], baseline_box=pool[0]), 'Saved pool differs from fixed31 GT-free geometry')
        ds = [descriptor(box, source['width'], source['height']) for box in synthetic]
        base_descriptor = descriptor(pool[0], source['width'], source['height'])
        outside = [j for j in range(3) if not min(d[j] for d in ds) <= base_descriptor[j] <= max(d[j] for d in ds)]
        if positive and gains[selected] <= 0.:
            error = 'NO_POSITIVE_TRUE_GAIN_ABOVE_ZERO' if not true_positive else 'WRONG_CANDIDATE_OUTRANKS_POSITIVE'
        elif positive:
            error = 'POSITIVE_SELECTED_SUBOPTIMAL' if gains[selected] < gains[oracle] else 'ORACLE_POSITIVE_SELECTED'
        else:
            error = 'BASE_IS_POOL_ORACLE'
        comparisons = concordance(scores, gains)
        nonbase_comparisons = concordance(scores[1:], gains[1:])
        rows.append(dict(source_id=sid, source_sha256=source['source_sha256'], baseline_iou=truth[0],
            selected_index=selected, selected_iou=truth[selected], selected_gain=gains[selected],
            oracle_index=oracle, oracle_iou=truth[oracle], oracle_gain=gains[oracle], regret=gains[oracle]-gains[selected],
            positive_candidates=len(positive), positive_candidates_predicted_positive=len(true_positive),
            predicted_positive_candidates=len(predicted_positive), selected_improves=gains[selected] > 0.,
            selected_harms=gains[selected] < 0., selected_changed=selected != 0,
            best_true_positive_score=max((scores[i] for i in positive), default=None),
            top_nonbase_index=top_nonbase, top_nonbase_predicted_gain=scores[top_nonbase],
            top_nonbase_actual_gain=gains[top_nonbase], error_class=error,
            source_candidate_MSE=mean((scores[i]-gains[i])**2 for i in range(1, len(pool))),
            source_zero_gain_MSE=mean(gains[i]**2 for i in range(1, len(pool))),
            concordance_with_baseline=comparisons, concordance_nonbase=nonbase_comparisons,
            baseline_in_synthetic_train_pool=pool[0] in synthetic,
            baseline_descriptor_width_center_xy=base_descriptor,
            synthetic_coordinate_min=[min(d[j] for d in ds) for j in range(3)],
            synthetic_coordinate_max=[max(d[j] for d in ds) for j in range(3)],
            outside_synthetic_coordinate_envelope_indices=outside,
            coordinate_envelope_is_not_convex_hull_or_visual_support=True))
        for i in range(1, len(pool)):
            actual = 'positive' if gains[i] > 0. else ('negative' if gains[i] < 0. else 'zero')
            called = 'positive' if scores[i] > 0. else ('negative' if scores[i] < 0. else 'zero')
            confusion[actual+'__pred_'+called] += 1
            candidates.append(dict(source_id=sid, candidate_index=i, actual_gain=gains[i], predicted_gain=scores[i],
                actual_sign=actual, predicted_sign=called, selected=i == selected,
                box=pool[i], baseline_box=pool[0]))
    positive_sources = [r for r in rows if r['oracle_gain'] > 0.]
    oracle_total = math.fsum(r['oracle_gain'] for r in rows)
    positive_gain = math.fsum(max(0., r['selected_gain']) for r in rows)
    negative_gain = math.fsum(min(0., r['selected_gain']) for r in rows)
    best = max(r['selected_gain'] for r in rows)
    def subset(values):
        return dict(sources=len(values), oracle_positive_sources=sum(r['oracle_gain'] > 0. for r in values),
            improved=sum(r['selected_gain'] > 0. for r in values), harmed=sum(r['selected_gain'] < 0. for r in values),
            selected_mean_gain=mean(r['selected_gain'] for r in values), oracle_mean_gain=mean(r['oracle_gain'] for r in values))
    statistics = dict(sources=20, nonbase_candidates=len(candidates),
        improvable_sources=len(positive_sources), baseline_already_pool_oracle_sources=20-len(positive_sources),
        selected_improved_sources=sum(r['selected_improves'] for r in rows),
        selected_harmed_sources=sum(r['selected_harms'] for r in rows), changed_sources=sum(r['selected_changed'] for r in rows),
        missed_improvable_sources=sum(not r['selected_improves'] for r in positive_sources),
        improvement_source_recall=sum(r['selected_improves'] for r in rows)/len(positive_sources) if positive_sources else None,
        positive_candidates=sum(r['positive_candidates'] for r in rows),
        positive_candidates_recalled=sum(r['positive_candidates_predicted_positive'] for r in rows),
        predicted_positive_candidates=sum(r['predicted_positive_candidates'] for r in rows),
        confusion=dict(confusion), error_classes=dict(Counter(r['error_class'] for r in rows)),
        source_equal_candidate_MSE=mean(r['source_candidate_MSE'] for r in rows),
        source_equal_zero_gain_MSE=mean(r['source_zero_gain_MSE'] for r in rows),
        source_equal_concordance_with_baseline=mean(r['concordance_with_baseline']['rate'] for r in rows if r['concordance_with_baseline']['rate'] is not None),
        source_equal_concordance_nonbase=mean(r['concordance_nonbase']['rate'] for r in rows if r['concordance_nonbase']['rate'] is not None),
        actual_mean_gain=(positive_gain+negative_gain)/20, oracle_mean_gain=oracle_total/20,
        positive_gain_sum=positive_gain, negative_gain_sum=negative_gain,
        largest_positive_gain=best, mean_gain_excluding_largest_positive=(positive_gain+negative_gain-best)/19,
        old_five_improvements_gate_feasible_with_same_pool=len(positive_sources) >= 5,
        baseline_in_synthetic_pool=sum(r['baseline_in_synthetic_train_pool'] for r in rows),
        baseline_outside_synthetic_coordinate_envelope=sum(bool(r['outside_synthetic_coordinate_envelope_indices']) for r in rows),
        support_strata={str(flag):subset([r for r in rows if bool(r['outside_synthetic_coordinate_envelope_indices']) == flag]) for flag in (False, True)})
    return dict(statistics=statistics, sources=rows, candidates=candidates)


def journal_decomposition(journals, schedule):
    byid = {r['id']:r for r in schedule}; events = []
    for journal in journals:
        events.extend(row for row in journal if row['event'] == 'TRAIN_RAW_LOSS')
    events.sort(key=lambda r:r['micro'])
    require(len(events) == 2000 and [r['micro'] for r in events] == list(range(2000)), 'Exact original2000 successful training loss rows required')
    for row in events:
        old = byid[row['id']]
        require(all(row[k] == old[k] for k in ('source_id', 'forward_id', 'reverse_id', 'target', 'draw_weight')), 'Original journal/schedule identity differs')
        number(row['prediction']); number(row['loss'])
    def summarize(values):
        weight = math.fsum(r['draw_weight'] for r in values)
        mse = math.fsum(r['draw_weight']*(r['prediction']-r['target'])**2 for r in values)/weight
        zero = math.fsum(r['draw_weight']*r['target']**2 for r in values)/weight
        informative = [r for r in values if r['target'] != 0.]
        return dict(rows=len(values), first_micro=values[0]['micro'], last_micro=values[-1]['micro'],
            distinct_sources=len({r['source_id'] for r in values}), weighted_MSE=mse, weighted_zero_MSE=zero,
            weighted_MSE_over_zero=mse/zero if zero else None, mean_logged_normalized_loss=mean(r['loss'] for r in values),
            nonzero_target_sign_accuracy=mean(float(r['prediction']*r['target'] > 0.) for r in informative))
    return dict(all=summarize(events), first200=summarize(events[:200]), last200=summarize(events[-200:]),
        scope='CHANGING_WEIGHTS_AND_EXAMPLES_NOT_FINAL_TRAIN_SET_METRICS',
        cannot_replace_fixed_final_checkpoint_train_readout=True,
        no_hyperparameter_or_checkpoint_selection=True)


def save(path, value):
    import os
    with Path(path).open('x', encoding='utf-8') as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write('\n'); handle.flush(); os.fsync(handle.fileno())


def run(root, output):
    root = Path(root).resolve(); output = Path(output).resolve()
    require(output == root/'utility_failure_diagnosis_66', 'One explicit fresh66 result directory required')
    output.mkdir(exist_ok=False)
    started = time.monotonic(); metadata = Metadata()
    try:
        result_ref = reference(root/'utility_value_comparison_56/result.json')
        result = metadata.read(result_ref)
        require(result['status'] == 'STOP_UTILITY_SCREEN20_REJECTED' and result['primary'] == 'UTILITY'
                and result['fixed_final_checkpoint'] is True and result['confirm_admitted'] is False
                and result['production_admitted'] is False, 'Adopt actual frozen55/56 STOP only')
        reg = metadata.read(result['registration']); targets = metadata.read(result['CPU_targets'])
        catalog = metadata.read(result['source_catalog']); plan = metadata.read(result['case_plan'])
        prepared = metadata.read(reg['prepared']); done = metadata.read(result['training_completion'])
        pilot = metadata.read(done['pilot_completion'])
        require(reg['schema'] == 'UTILITY_CONTINUOUS_IOU_GRADIENT_V55'
                and prepared['schema'] == 'UTILITY_CONTINUOUS_TRAIN_SCHEDULE_V55'
                and done['completed_updates'] == 500 and done['successful_micro'] == 2000
                and done['actual_training_forwards'] == 4000, 'Actual unique final500 completed training required')
        require(done['adapter_weights'] == result['adapter_weights'] and done['value_weights'] == result['value_weights']
                and done['train_schedule_reference'] == reg['prepared'], 'Frozen checkpoint/source schedule binding differs')
        require(targets['status'] == 'ORIGINAL_SCREEN20_CPU_REFERENCE_ONLY_V55'
                and targets['source_catalog'] == result['source_catalog'] and plan['GT_used_for_input_or_pair_choice'] is False,
                'Original CPU-only20 reference/GT-free case plan required')
        original = {r['source_id']:r for r in catalog['sources']}
        require(len(original) == 622 and len(targets['sources']) == 20, 'Original602train+20screen catalog only')
        for source in targets['sources']:
            adopted = original[source['source_id']]
            require(all(source[k] == adopted[k] for k in ('source_sha256', 'role', 'width', 'height', 'pool', 'baseline_box', 'original_BASE_observed')),
                    'Screen metadata is not original31 catalog')
            pairs = [p for p in plan['pair_index'] if p['source_id'] == source['source_id']]
            require(sorted(p['candidate_index'] for p in pairs) == list(range(len(source['pool']))), 'Missing original full screen pool pair')
        oldreg = metadata.read(reference(root/'crop_CPU_registration_31.json'))
        spec = importlib.util.spec_from_file_location('_pure_frozen_geometry31_for66', metadata.bound(oldreg['geometry_code'], ('.py',)))
        geometry = importlib.util.module_from_spec(spec); spec.loader.exec_module(geometry)
        analysis = screen_decomposition(targets['sources'], result['evaluation']['predictions'], geometry)
        require(math.isclose(analysis['statistics']['actual_mean_gain'], result['evaluation']['summaries']['UTILITY']['mean_gain'], rel_tol=0., abs_tol=1e-14), 'Saved quality arithmetic mismatch')
        training = [r for r in catalog['sources'] if r['role'] == 'train']
        require(len(training) == 602 and not {r['source_sha256'] for r in training}&{r['source_sha256'] for r in targets['sources']}, 'Original602/20 file-byte isolation differs')
        journals = journal_decomposition([metadata.lines(pilot['micro_journal']), metadata.lines(done['micro_journal'])], prepared['train_schedule'])
        report = dict(status='COMPLETE_FROZEN55_STOP_CPU_ERROR_DECOMPOSITION_NOT_NEW_ADMISSION',
            original_quality_status=result['status'], original_quality=result['evaluation']['quality'],
            screen=analysis, training_log_diagnostic=journals,
            training_support=dict(sources=602, actual_BASE_observed=sum(r['original_BASE_observed'] for r in training),
                train_target_RMS=prepared['train_target_RMS'], screen_sources=20,
                causal_explanation_proven=False, sparse_graph_coverage_owned_by_independent67=True,
                geometric_membership_is_not_learned_visual_support=True),
            bindings=dict(code=reference(__file__), metadata=list(metadata.references.values())),
            elapsed_seconds=time.monotonic()-started, new_model_calls=0, new_training_updates=0,
            new_processor_calls=0, pixel_or_tensor_reads=0, formal426_reads=0,
            no_threshold_scan=True, no_gate_change=True, no_new_mechanism_admitted=True)
        save(output/'result.json', report)
        short = dict(status=report['status'], result=reference(output/'result.json'),
            screen=analysis['statistics'], training_log=journals,
            training_support=report['training_support'], elapsed_seconds=report['elapsed_seconds'])
        save(output/'short_summary.json', short)
        print(json.dumps(short, ensure_ascii=False, allow_nan=False))
        return report
    except BaseException as error:
        save(output/'failure.json', dict(error=repr(error), no_failure_to_empty=True, automatic_retry=False,
            original55_56_unchanged=True, new_model_calls=0, opened_metadata=list(metadata.references.values())))
        raise


def self_test():
    import unittest
    class PureChecks(unittest.TestCase):
        def test_policy_and_pairwise(self):
            self.assertEqual(choose([0., .1, .1]), 1)
            self.assertEqual(choose([0., -.1]), 0)
            self.assertEqual(concordance([0., 1., 1.], [0., 1., 2.])['rate'], 5/6)
        def test_nonfinite_rejected(self):
            with self.assertRaises(ValueError): choose([0., float('nan')])
        def test_journal_is_not_final(self):
            rows = [dict(id=str(i), source_id=str(i%20), forward_id='f'+str(i), reverse_id='r'+str(i), target=.2, draw_weight=1.) for i in range(2000)]
            logged = [dict(r, event='TRAIN_RAW_LOSS', micro=i, prediction=.1, loss=.5) for i, r in enumerate(rows)]
            answer = journal_decomposition([logged[:16], logged[16:]], rows)
            self.assertAlmostEqual(answer['all']['weighted_MSE_over_zero'], .25)
            self.assertTrue(answer['cannot_replace_fixed_final_checkpoint_train_readout'])
            with self.assertRaises(ValueError): journal_decomposition([logged[:-1]], rows)
        def test_screen_separates_sign_ranking_and_suboptimal_choice(self):
            spec = importlib.util.spec_from_file_location('_pure_geometry31_synthetic66', Path(__file__).with_name('crop_geometry_v31.py'))
            geometry = importlib.util.module_from_spec(spec); spec.loader.exec_module(geometry)
            pool = geometry.candidate_pool(160, 100, baseline_box=[20, 16, 100])
            sources = []; predictions = []
            for i in range(20):
                sid = str(i); truth = [.9]+[.2]*(len(pool)-1); scores = [0.]+[-.5]*(len(pool)-1)
                if i < 3:
                    truth = [.5, .6, .8]+[.3]*(len(pool)-3)
                    scores = [0.]+[-.2]*(len(pool)-1)
                if i == 1:
                    scores[2], scores[3] = .1, .2
                if i == 2:
                    scores[1], scores[2] = .3, .1
                sources.append(dict(source_id=sid, source_sha256=str(i), role='screen', width=160, height=100,
                    pool=pool, baseline_box=pool[0], original_BASE_observed=True, reference_modified=False,
                    baseline_index=0, candidate_ious=truth))
                predictions.append(dict(source_id=sid, source_sha256=str(i), predicted_gains={'UTILITY':scores},
                    choices={'UTILITY':choose(scores)}))
            report = screen_decomposition(sources, predictions, geometry)
            self.assertEqual(report['statistics']['improvable_sources'], 3)
            self.assertEqual(report['statistics']['missed_improvable_sources'], 2)
            self.assertEqual([r['error_class'] for r in report['sources'][:3]],
                ['NO_POSITIVE_TRUE_GAIN_ABOVE_ZERO', 'WRONG_CANDIDATE_OUTRANKS_POSITIVE', 'POSITIVE_SELECTED_SUBOPTIMAL'])
            self.assertEqual(report['statistics']['baseline_in_synthetic_pool'], 0)
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(PureChecks)
    require(unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful(), 'Pure66 tests failed')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root'); parser.add_argument('--output'); parser.add_argument('--self-test', action='store_true')
    args = parser.parse_args()
    if args.self_test:
        self_test()
    else:
        require(args.root is not None and args.output is not None, 'Explicit root and fresh output required')
        run(args.root, args.output)
