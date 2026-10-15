"""No decoder, processor, torch, GPU, or model imports. Mathematical oracles."""
import itertools
import math
from fractions import Fraction as F
from pathlib import Path
import unittest
from common import load
from objective import assistant_mask, classify, finite_decimal, target
from scientific_gate import summarize, compare, gate, reference_coverage
from native_runtime import native_ranges, validate_plan

ROOT = Path(__file__).resolve().parents[2]/'slot6_silver24_v1'
q = load(ROOT/'quality_contract.py', 'quality_contract')
e = load(ROOT/'event_metrics.py', 'silver_test_event_metrics')


class ObjectiveTests(unittest.TestCase):
    def test_reference_coverage_pre_gpu_negative_controls(self):
        jobs = {}; refs = {}
        for i in range(12):
            key = str(i); group = 'D'+str(i//2) if i < 4 else 'L'+str((i-4)//2)
            jobs[key] = dict(role='process_dev' if i < 4 else 'locked_evaluation', source_group=group)
            start = 10*(i%2)
            refs[key] = dict(keep_global_exact=[[start,start+1]] if group != 'L3' else [],
                no_global_exact=[[start+1,start+10]] if group != 'L3' else [[start,start+10]], unknown_global_exact=[], consequential_unknowns=[])
        self.assertEqual(reference_coverage(jobs,refs,q)['status'], 'PASS_FIXED_EVALUATION_REFERENCE_COVERAGE')
        # Complete denominator is insufficient if two groups have no known positive.
        for k in ('8','9'):
            refs[k]['keep_global_exact'] = []
        result = reference_coverage(jobs,refs,q)
        self.assertFalse(result['checks']['positive_locked_sources_min'])
        self.assertEqual(result['status'], 'STOP_INSUFFICIENT_FIXED_EVALUATION_REFERENCES_NO_GPU')
        with self.assertRaisesRegex(ValueError, 'complete evaluation references pending'):
            reference_coverage(jobs,{k:v for k,v in refs.items() if k != '11'},q)

    def test_native_floor64_and_half_open_fraction_oracle(self):
        # For 128 eligible frames, independent ordinal identity is every even
        # ordinal below 126 plus the physical terminal ordinal 127.
        ids = list(range(0, 126, 2))+[127]
        w = dict(planned_source_frame_ordinals=ids, planned_exact_pts=[str(F(i, 10)) for i in ids],
            planned_actual_pts_sec=[i/10 for i in ids], eligible_exact_pts=[str(F(i, 10)) for i in range(128)],
            domain_start_exact='0', domain_end_exact='64/5', window_pts_start_sec=0.,
            window_pts_end_exclusive_sec=12.8, eligible_source_frame_count=128, source_total_frames=200)
        a, b, points = validate_plan(w)
        self.assertEqual((a, b), (0, F(64, 5)))
        self.assertEqual(native_ranges([[F(1, 10), F(2, 10)]], w), [[1, 2]])
        self.assertEqual(native_ranges([], w), [])
        with self.assertRaisesRegex(ValueError, 'no native source frame'):
            native_ranges([[F(101, 1000), F(199, 1000)]], w)
        w['planned_exact_pts'][1] = '1/10'
        with self.assertRaises(ValueError):
            validate_plan(w)

    def test_assistant_causal_mask_and_termination(self):
        # Prompt and video sentinels 7,8,9; assistant JSON 1,2 and EOS 3.
        full = [0, 7, 8, 9, 1, 2, 3, 0]; attention = [0, 1, 1, 1, 1, 1, 1, 0]
        labels = assistant_mask(full, attention, [7, 8, 9], [1, 1, 1], [1, 2, 3], 3)
        self.assertEqual(labels, [-100, -100, -100, -100, 1, 2, 3, -100])
        # Independently assign probability 1/2,1/4,1/8 to the causal labels.
        # Their mean CE is log(4); EOS must contribute log(8).
        probs = [None, None, None, F(1, 2), F(1, 4), F(1, 8), None]
        pairs = [(i-1, label) for i, label in enumerate(labels) if label != -100]
        self.assertEqual(pairs, [(3, 1), (4, 2), (5, 3)])
        loss = sum(-math.log(float(probs[pos])) for pos, label in pairs)/len(pairs)
        self.assertAlmostEqual(loss, math.log(4))
        first = 4; keep = len(labels)-first+1
        tail = labels[-keep:]
        self.assertEqual([(i+len(labels)-keep-1, label) for i, label in enumerate(tail) if label != -100], pairs)
        with self.assertRaises(ValueError):
            assistant_mask(full, attention, [7, 8, 9], [1, 1, 1], [1, 2], 3)
        with self.assertRaises(ValueError):
            assistant_mask(full, attention, [7, 8], [1, 1], [1, 2, 3], 3)

    def test_source_balanced_objective_gradient_oracle(self):
        # Sourcewise average derivative is the oracle; coefficients are
        # checked against a different grouped sum, for every allowed N.
        for n in range(8, 13):
            groups = ['A', 'A', 'A', 'B', 'C', 'D', 'D', 'D']+['A']*(n-8)
            s = q.schedule(groups)
            deriv = [F((i+1)**2, 11) for i in range(n)]
            oracle = sum(sum(deriv[i] for i, x in enumerate(groups) if x == g)/groups.count(g)
                         for g in set(groups))/4
            for epoch in (0, 1):
                batches = [b for b in s['batches'] if b['epoch'] == epoch]
                actual = sum(q.batch_loss_mean_ce(s, b['indices'], deriv) for b in batches)/len(batches)
                self.assertEqual(actual, oracle)
                self.assertEqual(sorted(i for b in batches for i in b['indices']), list(range(n)))
                wrongly_divided = sum(q.batch_loss_mean_ce(s, b['indices'], deriv)/len(b['indices']) for b in batches)/len(batches)
                self.assertNotEqual(wrongly_divided, oracle)
            self.assertEqual(s['updates'], 4 if n == 8 else 6)

    def test_empty_unknown_errors_are_distinct(self):
        self.assertEqual(classify('{"segments":[]}', 30)['status'], 'LEGAL_EMPTY')
        for raw in ('', 'UNKNOWN', '{"segments":null}', '{"segments":[],"segments":[]}',
                    '{"segments":[[true,1]]}', '{"segments":[[2,1]]}', '{"segments":[[0,31]]}'):
            r = classify(raw, 30)
            self.assertEqual(r['status'], 'PARSE_FAILURE'); self.assertIsNone(r['parsed_segments'])
        self.assertEqual(classify('{"segments":[]}', 30, 'decoder failed')['status'], 'INFERENCE_FAILURE')
        ref = dict(training_admitted=False, unknown_global_exact=[['0', '1']], keep_global_exact=[], explicit_no_highlight=False)
        with self.assertRaises(ValueError):
            target(ref, dict(domain_start_exact='0', domain_end_exact='1'))

    def test_fraction_serialization_sidecar_keeps_native_membership(self):
        self.assertEqual(finite_decimal(F(1, 8)), '0.125')
        with self.assertRaises(ValueError):
            finite_decimal(F(1, 3))
        w = dict(window_id='w', domain_start_exact='0', domain_end_exact='1',
            planned_exact_pts=['0', '1/4', '1/2', '3/4'], eligible_exact_pts=['0', '1/4', '1/2', '3/4'])
        ref = dict(training_admitted=True, unknown_global_exact=[], keep_global_exact=[['0', '1/3']], explicit_no_highlight=False)
        side = dict(reference_sha256='abc', window_id='w', reviewed=True, not_measured_cut=True,
            exact_target_local=[['0', '1/3']], serialized_decimal_as_str=[['0', '0.3333333333333333']],
            reviewed_boundary_ranges_local_exact=[[['0', '0'], ['3/10', '2/5']]])
        text, exact = target(ref, w, side, 'abc')
        self.assertEqual(text, '{"segments":[[0,0.3333333333333333]]}')
        self.assertEqual(exact, [[F(0), F(1, 3)]])
        side['serialized_decimal_as_str'][0][1] = '0.6'
        side['reviewed_boundary_ranges_local_exact'][0][1] = ['0', '1']
        with self.assertRaisesRegex(ValueError, 'native source selection'):
            target(ref, w, side, 'abc')


def fixture():
    jobs = {}; refs = {}; old = {}; new = {}
    for role, sources in (('process_dev', range(2)), ('locked_evaluation', range(4))):
        for s in sources:
            for ix in range(2):
                key = '%s:%s:%s'%(role, s, ix); a = 10*ix; positive = s < 3
                jobs[key] = dict(role=role, source_group=role+str(s), window=dict(domain_start_exact=str(a), domain_end_exact=str(a+10)))
                refs[key] = dict(keep_global_exact=[[a, a+5]] if positive else [],
                    no_global_exact=[[a+5, a+10]] if positive else [[a, a+10]], unknown_global_exact=[],
                    events=[dict(local=['0', '5'])] if positive else [])
                old[key] = dict(status='MODEL_OK' if positive else 'LEGAL_EMPTY', parsed_segments=[[0, F(5, 2)]] if positive else [])
                new[key] = dict(status='MODEL_OK' if positive else 'LEGAL_EMPTY', parsed_segments=[[0, 3]] if positive else [])
    return jobs, refs, old, new


def summaries(jobs, refs, predictions):
    return {role: summarize(jobs, refs, {k: v for k, v in predictions.items() if jobs[k]['role'] == role}, q, e, role)
        for role in ('process_dev', 'locked_evaluation')}


class ScientificTests(unittest.TestCase):
    def test_exact_time_set_unknown_bounds_exhaustive_oracle(self):
        # Enumerate independent one-second true labels in UNKNOWN cells;
        # compare actual min/max F1, never reuse the bound formula as oracle.
        cells = [(F(i), F(i+1)) for i in range(5)]
        for selected in itertools.product((0, 1), repeat=5):
            p = [c for c, bit in zip(cells, selected) if bit]
            m = q.metrics([(0, 5)], cells[:1], cells[1:2], cells[2:], p)
            fs = []
            for truth in itertools.product((0, 1), repeat=3):
                tp = selected[0]+sum(s*t for s, t in zip(selected[2:], truth))
                fs.append(F(2*tp, sum(selected)+1+sum(truth)))
            self.assertEqual(m['f1_lower'], min(fs)); self.assertEqual(m['f1_upper'], max(fs))

    def test_fixed_quality_gate_pass_and_nonretuning_fail(self):
        jobs, refs, old, new = fixture(); b = summaries(jobs, refs, old); n = summaries(jobs, refs, new)
        g = gate(b['process_dev'], n['process_dev'], b['locked_evaluation'], n['locked_evaluation'], q)
        self.assertEqual(g['status'], 'PASS_FIXED_SILVER_QUALITY_GATE')
        self.assertEqual(g['locked']['positive_macro_gain'], F(1, 12))
        self.assertFalse(g['recipe_retuning_allowed'])
        # Removing a confirmed positive whole window cannot be hidden by
        # improving another window enough to keep aggregate recall constant.
        new['locked_evaluation:0:0'] = dict(status='LEGAL_EMPTY', parsed_segments=[])
        new['locked_evaluation:0:1'] = dict(status='MODEL_OK', parsed_segments=[[0, 5]])
        n = summaries(jobs, refs, new)
        g = gate(b['process_dev'], n['process_dev'], b['locked_evaluation'], n['locked_evaluation'], q)
        self.assertFalse(g['checks']['positive_empty_nonincrease'])
        self.assertTrue(g['status'].startswith('STOP_'))

    def test_equal_fp_duration_does_not_hide_new_spill(self):
        jobs, refs, old, new = fixture()
        key = 'locked_evaluation:3:0'
        old[key] = dict(status='MODEL_OK', parsed_segments=[[1, 2]])
        new[key] = dict(status='MODEL_OK', parsed_segments=[[2, 3]])
        b = summaries(jobs, refs, old)['locked_evaluation']; n = summaries(jobs, refs, new)['locked_evaluation']
        r = compare(b, n, q)['sources']['locked_evaluation3']
        self.assertTrue(r['no_fp_nonincrease']); self.assertFalse(r['no_new_unrelated_spill'])
        self.assertEqual(r['new_confirmed_no_spill_seconds'], 1)

    def test_event_matching_reassignment_not_greedy(self):
        # Independent feasible two-pair assignment exists; naive greedy uses
        # the shared broad prediction and loses the second event.
        r = e.match_events([[(0, 2)], [(1, 3)]], [[(0, 3)], [(0, 2)]])
        self.assertEqual(r['matched_events'], 2); self.assertEqual(r['event_recall'], 1)

    def test_engineering_error_not_empty_scientific_row(self):
        jobs, refs, old, new = fixture()
        new['process_dev:0:0'] = dict(status='PARSE_FAILURE', parsed_segments=None)
        with self.assertRaisesRegex(ValueError, 'failure cannot enter'):
            summaries(jobs, refs, new)

    def test_unknown_negative_source_cannot_invent_positive_denominator(self):
        jobs, refs, old, new = fixture(); key = 'locked_evaluation:3:0'
        refs[key]['no_global_exact'] = [[10-5, 10]]
        refs[key]['unknown_global_exact'] = [[0, 5]]
        new[key] = dict(status='MODEL_OK', parsed_segments=[[0, 1]])
        b = summaries(jobs, refs, old)['locked_evaluation']; n = summaries(jobs, refs, new)['locked_evaluation']
        r = compare(b, n, q)['sources']['locked_evaluation3']
        self.assertIsNone(r['conservative_gain']); self.assertFalse(r['unknown_conservative_nonnegative'])


if __name__ == '__main__':
    unittest.main()
