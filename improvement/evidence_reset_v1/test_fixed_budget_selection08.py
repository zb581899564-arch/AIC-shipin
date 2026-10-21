import importlib.util
from pathlib import Path
import unittest

s=importlib.util.spec_from_file_location('select08',Path(__file__).with_name('fixed_budget_selection08.py'))
api=importlib.util.module_from_spec(s);s.loader.exec_module(api)


class SelectionTests(unittest.TestCase):
    def test_changes_content_without_changing_count_or_tail(self):
        result,info=api.select_fixed_budget(12,[0,1,2,10],
            [dict(start_ordinal=0,stop_ordinal=4,score=-1),dict(start_ordinal=4,stop_ordinal=8,score=2)])
        self.assertEqual(result,[4,5,6,10]);self.assertEqual(info['added'],3);self.assertEqual(info['removed'],3)

    def test_tied_scores_preserve_baseline(self):
        result,_=api.select_fixed_budget(8,[1,4,6],[dict(start_ordinal=0,stop_ordinal=8,score=0)])
        self.assertEqual(result,[1,4,6])

    def test_missing_availability_does_not_delete_original_or_create_box(self):
        result,info=api.select_fixed_budget(8,[0,1,7],
            [dict(start_ordinal=0,stop_ordinal=4,score=-1),dict(start_ordinal=4,stop_ordinal=8,score=1)],
            available_ordinals=[1,2,3,4,5,6])
        self.assertEqual(result,[0,4,7]);self.assertEqual(info['fixed_inside_budget'],1)

    def test_overlap_nan_and_out_of_bounds_rejected(self):
        with self.assertRaises(ValueError):api.select_fixed_budget(8,[1],[dict(start_ordinal=0,stop_ordinal=4,score=float('nan'))])
        with self.assertRaises(ValueError):api.select_fixed_budget(8,[1],[dict(start_ordinal=0,stop_ordinal=9,score=1)])
        with self.assertRaises(ValueError):api.select_fixed_budget(8,[1],[dict(start_ordinal=0,stop_ordinal=4,score=1),dict(start_ordinal=3,stop_ordinal=6,score=2)])

    def test_all_empty_and_full_are_successful_fixed_budgets(self):
        blocks=[dict(start_ordinal=0,stop_ordinal=8,score=3)]
        self.assertEqual(api.select_fixed_budget(8,[],blocks)[0],[])
        self.assertEqual(api.select_fixed_budget(8,list(range(8)),blocks)[0],list(range(8)))


if __name__=='__main__':unittest.main(verbosity=2)
