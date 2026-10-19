"""Pure range/PTS/cache-metadata tests; no historical evidence or media."""
from fractions import Fraction as F
import unittest

from residual_view_audit import (clock_points, combine_component, component_id, describe_component,
                                 exact, merge_ranges, native_ranges, subtract_ranges)

SHA = 'a'*64


def view(ordinals=range(64), present=True, case='v'):
    values = list(ordinals)
    return dict(case_id=case, ordinals=values, pixel_sha256=[str(i) for i in values],
                array_ref=dict(path='/stored/'+case+'.npz', sha256='b'*64), cache_present=present)


class ResidualViewAuditTests(unittest.TestCase):
    def test_half_open_vfr_uses_native_pts_not_duration_or_fps(self):
        pts, end = clock_points(['0', '1/10', '3/5', '7/10'], '1')
        self.assertEqual(native_ranges([['1/10', '7/10']], pts, end), [[1, 3]])
        self.assertEqual(native_ranges([['11/100', '59/100']], pts, end), [])

    def test_difference_splits_only_at_baseline_native_members(self):
        self.assertEqual(subtract_ranges([[0, 12]], [[2, 4], [7, 9]]), [[0, 2], [4, 7], [9, 12]])
        self.assertEqual(subtract_ranges([[2, 4]], [[0, 9]]), [])

    def test_adjacent_components_are_native_contiguous_even_across_vfr_gap(self):
        pts, end = clock_points(['0', '1/10', '10', '11'], '12')
        self.assertEqual(native_ranges([['0', '1/10'], ['1/10', '11']], pts, end), [[0, 3]])
        self.assertEqual(subtract_ranges([[0, 2], [2, 4]], []), [[0, 4]])

    def test_multiple_candidates_and_overlapping_baseline_are_normalized(self):
        self.assertEqual(subtract_ranges([[8, 12], [0, 5], [4, 9]], [[2, 4], [3, 7]]), [[0, 2], [7, 12]])
        self.assertEqual(merge_ranges([[1, 3], [3, 5], [2, 4]]), [[1, 5]])

    def test_native_aliases_deduplicate_by_source_and_component(self):
        pts, end = clock_points(['0', '1/10', '1/5', '3/10'], '2/5')
        a = native_ranges([['1/100', '3/10']], pts, end)[0]
        b = native_ranges([['1/10', '21/100']], pts, end)[0]
        self.assertEqual(a, b)
        self.assertEqual(component_id(SHA, a), component_id(SHA, b))
        self.assertNotEqual(component_id(SHA, a), component_id('c'*64, b))

    def test_63_frames_are_inapplicable_without_filling(self):
        pts, end = clock_points(list(range(70)), 70)
        result = describe_component(SHA, [0, 63], pts, end, [view()])
        self.assertEqual(result['native_frames'], 63)
        self.assertTrue(result['eligibility_status'].startswith('NOT_APPLICABLE'))
        self.assertFalse(result['current_input_admitted'])
        self.assertEqual(result['semantic_truth'], 'UNKNOWN')

    def test_exactly64_present_samples_are_only_metadata_eligible(self):
        pts, end = clock_points(list(range(70)), 70)
        result = describe_component(SHA, [0, 64], pts, end, [view()])
        self.assertTrue(result['has_at_least64_distinct_native_frames'])
        self.assertTrue(result['eligibility_status'].startswith('METADATA_ELIGIBLE64'))
        self.assertEqual(result['RGB_sample_coverage']['present_cache_referenced_distinct_native_samples'], 64)
        self.assertEqual(result['native_cell_span_exact'], ['0', '64'])
        self.assertFalse(result['new_observation_performed'])

    def test_missing_cache_is_unknown_and_duplicate_views_do_not_add_samples(self):
        pts, end = clock_points(list(range(100)), 100)
        result = describe_component(SHA, [0, 80], pts, end, [view(present=False), view(present=False, case='alias')])
        self.assertTrue(result['eligibility_status'].startswith('UNKNOWN'))
        self.assertEqual(result['RGB_sample_coverage']['recorded_distinct_native_samples'], 64)
        self.assertEqual(result['RGB_sample_coverage']['present_cache_referenced_distinct_native_samples'], 0)

    def test_union_cache_coverage_maps_exact_array_rows_and_pts(self):
        pts, end = clock_points([str(F(i, 3)) for i in range(100)], '100/3')
        result = describe_component(SHA, [30, 100], pts, end, [view(), view(range(36, 100), case='other')])
        coverage = result['RGB_sample_coverage']
        self.assertEqual(coverage['present_cache_referenced_distinct_native_samples'], 70)
        sample = next(s for s in coverage['samples'] if s['ordinal'] == 99)
        self.assertEqual(sample['exact_pts'], '33')
        self.assertEqual(sample['cache_references'][0]['array_row_index'], 63)
        self.assertEqual(result['native_cell_span_exact'][1], '100/3')

    def test_invalid_clocks_ranges_float_pts_and_duplicate_samples_fail(self):
        for values, end in [(['0', '0'], '1'), (['1', '2'], '3'), (['0', '1'], '1')]:
            with self.assertRaises(ValueError): clock_points(values, end)
        with self.assertRaises(ValueError): exact(.1)
        with self.assertRaises(ValueError): merge_ranges([[True, 3]])
        pts, end = clock_points(list(range(70)), 70)
        with self.assertRaises(ValueError): native_ranges([['0', '71']], pts, end)
        bad = view(); bad['ordinals'][-1] = 0
        with self.assertRaises(ValueError): describe_component(SHA, [0, 64], pts, end, [bad])

    def test_cross_group_component_dedup_combines_metadata_not_source_counts(self):
        pts, end = clock_points(list(range(100)), 100)
        a = describe_component(SHA, [0, 80], pts, end, [view(present=False)])
        b = describe_component(SHA, [0, 80], pts, end, [view(range(16, 80), case='other')])
        a['event_aliases'] = [dict(group='dev', event_id='e1')]
        b['event_aliases'] = [dict(group='confirm', event_id='e2')]
        result = combine_component(a, b)
        self.assertEqual(result['component_id'], a['component_id'])
        self.assertEqual(len(result['event_aliases']), 2)
        self.assertEqual(result['RGB_sample_coverage']['recorded_distinct_native_samples'], 80)
        self.assertEqual(result['RGB_sample_coverage']['present_cache_referenced_distinct_native_samples'], 64)
        self.assertTrue(result['eligibility_status'].startswith('METADATA_ELIGIBLE64'))
        self.assertTrue(a['eligibility_status'].startswith('UNKNOWN'))

    def test_inconsistent_pixel_identity_is_not_silently_replaced(self):
        pts, end = clock_points(list(range(100)), 100)
        a = describe_component(SHA, [0, 80], pts, end, [view()])
        b = describe_component(SHA, [0, 80], pts, end, [view(case='other')])
        b['RGB_sample_coverage']['samples'][0]['pixel_sha256'] = 'wrong'
        with self.assertRaises(ValueError): combine_component(a, b)


if __name__ == '__main__':
    unittest.main()
