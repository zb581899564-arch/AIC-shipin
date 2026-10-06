"""Regression cases for accidental comparison reuse and out-of-order delivery."""
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from candidate_gate import load_qualified_holdout


class CandidateGateTests(unittest.TestCase):
    def setUp(self):
        parent = Path(__file__).resolve().parent
        self.temp = tempfile.TemporaryDirectory(prefix='gate-regression-', dir=parent)
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.campaign = self.root / 'improvement_round1'
        self.campaign.mkdir()
        self.out = self.root / 'runs/holdout'
        self.out.mkdir(parents=True)
        reference = b'{"fixture":true}\n'
        (self.out / 'holdout_frozen.jsonl').write_bytes(reference)
        self.plan = {'output': str(self.out), 'candidate_order': ['multi', 'windowed'],
                     'holdout_sha256': hashlib.sha256(reference).hexdigest()}
        self.summary = {'status': 'completed', 'candidate_order': ['multi', 'windowed'],
                        'accepted_in_dev_order': ['multi', 'windowed'], 'selected': 'multi',
                        'results': {p: {'accepted_holdout': True} for p in ('multi', 'windowed')}}
        self.write(self.campaign / 'holdout_comparison_lock.json', self.plan)
        self.write(self.out / 'plan.json', self.plan)
        self.write(self.out / 'summary.json', self.summary)
        self.write(self.campaign / 'submission_policy.json', {'initial_score': 41.09})

    @staticmethod
    def write(path, value):
        path.write_text(json.dumps(value) + '\n')

    def scored(self, score, status='DONE'):
        self.write(self.campaign / 'submission_ledger.jsonl',
                   {'event': 'scored', 'status': status, 'policy': 'multi', 'official_score': score})

    def test_first_candidate_allowed(self):
        plan, result = load_qualified_holdout(self.out, 'multi', self.root)
        self.assertEqual(plan, self.plan)
        self.assertEqual(result['selected'], 'multi')

    def test_lower_ranked_candidate_cannot_go_first(self):
        with self.assertRaisesRegex(ValueError, 'higher-priority'):
            load_qualified_holdout(self.out, 'windowed', self.root)

    def test_pending_score_does_not_unlock_second(self):
        self.scored(40, status='PENDING')
        with self.assertRaisesRegex(ValueError, 'higher-priority'):
            load_qualified_holdout(self.out, 'windowed', self.root)

    def test_nonimproving_score_allows_next_in_frozen_order(self):
        self.scored(41.09)
        load_qualified_holdout(self.out, 'windowed', self.root)

    def test_improvement_stops_further_challengers(self):
        self.scored(41.10)
        with self.assertRaisesRegex(ValueError, 'already achieved'):
            load_qualified_holdout(self.out, 'windowed', self.root)

    def test_later_lower_score_cannot_erase_a_prior_improvement(self):
        events = [{'event': 'scored', 'status': 'DONE', 'policy': 'multi', 'official_score': s}
                  for s in (42.0, 40.0)]
        (self.campaign / 'submission_ledger.jsonl').write_text(''.join(json.dumps(e) + '\n' for e in events))
        with self.assertRaisesRegex(ValueError, 'already achieved'):
            load_qualified_holdout(self.out, 'windowed', self.root)

    def test_other_self_consistent_comparison_rejected(self):
        copied = self.root / 'runs/other'
        copied.mkdir()
        for path in self.out.iterdir():
            (copied / path.name).write_bytes(path.read_bytes())
        with self.assertRaisesRegex(ValueError, 'unique campaign'):
            load_qualified_holdout(copied, 'multi', self.root)

    def test_reference_drift_rejected(self):
        (self.out / 'holdout_frozen.jsonl').write_text('changed')
        with self.assertRaisesRegex(ValueError, 'reference identity'):
            load_qualified_holdout(self.out, 'multi', self.root)

    def test_summary_reordering_rejected(self):
        self.summary['accepted_in_dev_order'] = ['windowed', 'multi']
        self.summary['selected'] = 'windowed'
        self.write(self.out / 'summary.json', self.summary)
        with self.assertRaisesRegex(ValueError, 'frozen development order'):
            load_qualified_holdout(self.out, 'multi', self.root)

    def test_different_global_plan_rejected(self):
        self.write(self.campaign / 'holdout_comparison_lock.json', self.plan | {'candidate_order': ['multi']})
        with self.assertRaisesRegex(ValueError, 'unique campaign'):
            load_qualified_holdout(self.out, 'multi', self.root)


if __name__ == '__main__':
    unittest.main()
