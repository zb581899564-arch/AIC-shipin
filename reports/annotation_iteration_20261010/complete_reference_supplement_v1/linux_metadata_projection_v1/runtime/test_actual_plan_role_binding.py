"""Regression using the actual frozen roster, without treating fixtures as labels."""
from collections import Counter
from fractions import Fraction as F
import json
from pathlib import Path
import sys
import unittest

from common import evaluation_keys, sha
from scientific_gate import reference_coverage

OLD = Path(__file__).resolve().parents[2]/'slot6_silver24_v1'
sys.path.insert(0, str(OLD))
import quality_contract as quality


class ActualFrozenPlanRoles(unittest.TestCase):
    def setUp(self):
        p = OLD/'source_window_plan.json'
        self.assertEqual(sha(p), '09ecb28971932bd3bf8ac275c30d0a6fd534345442f2d2ec3529fa3f8e1e4b22')
        plan = json.loads(p.read_text(encoding='utf-8-sig'))
        self.jobs = {j['window']['window_id']: j for j in plan['jobs']}

    def test_runtime_accepts_actual_roles_and_keeps_roster(self):
        self.assertEqual(Counter(j['role'] for j in self.jobs.values()),
                         {'train': 12, 'process_dev': 4, 'locked_evaluation': 8})
        dev, locked = evaluation_keys(self.jobs)
        self.assertEqual((len(dev), len(locked)), (4, 8))
        self.assertEqual(len({self.jobs[k]['source_group'] for k in dev}), 2)
        self.assertEqual(len({self.jobs[k]['source_group'] for k in locked}), 4)

    def test_scientific_coverage_recognizes_actual_locked_jobs(self):
        # Synthetic positive/NO intervals exercise role selection only. They
        # never become saved training/evaluation annotation or quality evidence.
        dev, locked = evaluation_keys(self.jobs); refs = {}
        for k in dev+locked:
            w = self.jobs[k]['window']; a, b = F(w['domain_start_exact']), F(w['domain_end_exact'])
            refs[k] = dict(keep_global_exact=[[str(a+1), str(a+2)]],
                no_global_exact=[[str(a), str(a+1)], [str(a+2), str(b)]],
                unknown_global_exact=[], consequential_unknowns=[])
        result = reference_coverage(self.jobs, refs, quality)
        self.assertEqual(result['status'], 'PASS_FIXED_EVALUATION_REFERENCE_COVERAGE')
        self.assertTrue(all(result['checks'].values()))


if __name__ == '__main__':
    unittest.main()
