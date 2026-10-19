import collections
import hashlib
import unittest
from crop_prepare_v31 import planned_cases
from crop_geometry_v31 import candidate_pool


class ScheduleTests(unittest.TestCase):
    def records(self):
        return [dict(source_id='train%03d'%i,source_sha256=hashlib.sha256(('source%d'%i).encode()).hexdigest(),
            role='train',pool=candidate_pool(500,333)) for i in range(602)]+[
            dict(source_id='screen%02d'%i,source_sha256=hashlib.sha256(('eval%d'%i).encode()).hexdigest(),
                 role='screen',pool=candidate_pool(500,333,[0,33,500])) for i in range(20)]
    def test_exact_budget_source_balance_and_mirrors(self):
        plan=planned_cases(self.records());schedule=plan['train_schedule'];cases={c['id']:c for c in plan['cases']}
        self.assertEqual(len(schedule),2000);self.assertEqual(len({s['id'] for s in schedule}),2000)
        visits=collections.defaultdict(list)
        for row in schedule:visits[row['source_id']].append(cases[row['case_id']])
        self.assertEqual(len(visits),602);self.assertEqual({len(v) for v in visits.values()},{3,4})
        for rows in visits.values():
            self.assertEqual((rows[0]['a'],rows[0]['b']),(rows[1]['b'],rows[1]['a']))
            if len(rows)==4:self.assertEqual((rows[2]['a'],rows[2]['b']),(rows[3]['b'],rows[3]['a']))
    def test_pair_and_source_choice_cannot_observe_labels(self):
        records=self.records();before=planned_cases(records)
        for i,row in enumerate(records):row['human_reference_not_read']=[i,0,1,1]
        self.assertEqual(before,planned_cases(records));self.assertFalse(before['GT_used_for_input_or_pair_choice'])
    def test_eval_has_both_orders_and_self_but_no_training_source(self):
        p=planned_cases(self.records());cases={c['id']:c for c in p['cases']}
        self.assertEqual(len(p['screen_ids']),260)
        self.assertTrue(all(cases[c]['source_id'].startswith('screen') for c in p['screen_ids']))
        for row in p['pair_index']:
            a,b=cases[row['first_id']],cases[row['reverse_id']]
            self.assertEqual((a['a'],a['b']),(b['b'],b['a']))
            self.assertEqual(row['same_crop'],a['a']==a['b'])


if __name__=='__main__':unittest.main()
