import copy
import hashlib
import unittest

import crop_confirm_prepare_v36 as pure36
import crop_gain_confirm_prepare_v49 as gain49
import crop_geometry_v31 as geometry


def ref(name):
    return dict(path='/synthetic/'+name, sha256=hashlib.sha256(name.encode()).hexdigest())


def catalog():
    return dict(sources=[dict(source_id='train%03d'%i, source_sha256=hashlib.sha256(('train%d'%i).encode()).hexdigest(), role='train') for i in range(602)]+[
        dict(source_id='screen%02d'%i, source_sha256=hashlib.sha256(('screen%d'%i).encode()).hexdigest(), role='screen') for i in range(20)])


def records():
    return [dict(source_id='gnmc:test:%06d.jpeg'%i, source_sha256=hashlib.sha256(('confirm%d'%i).encode()).hexdigest(),
        role='confirm', original_index=i, baseline_box=[5, 6, 400], pool=geometry.candidate_pool(500, 333, [5, 6, 400])) for i in range(1, 20)]


class GainConfirmTests(unittest.TestCase):
    def admission(self):
        reg = {k:ref(k) for k in ('gain_fit_registration', 'critic_weights', 'adapter_weights', 'gain_source_catalog',
            'screen_output_acceptance', 'fixed_training_completion', 'math_code', 'policy_code')}
        reg['adapter_directory'] = '/synthetic/adapter/crop'
        fit = dict(schema='CROP_GAIN_FINAL500_FIT_SCREEN_V47', adapter_weights=reg['adapter_weights'],
            fixed_training_completion=reg['fixed_training_completion'], original_screen_catalog=reg['gain_source_catalog'],
            screen_output_acceptance=reg['screen_output_acceptance'], math_code=reg['math_code'], policy_code=reg['policy_code'])
        result = dict(status='PASS_GAIN_CRITIC_SCREEN20_ONLY', confirm_admitted=True, production_admitted=False,
            primary='JOINT14', fixed_final_checkpoint=True, reports={'JOINT14': {'quality': {'admitted': True}}},
            registration=reg['gain_fit_registration'], critic_weights=reg['critic_weights'], adapter_weights=reg['adapter_weights'],
            source_catalog=reg['gain_source_catalog'], screen_output_acceptance=reg['screen_output_acceptance'],
            input_bindings={k:reg[k] for k in ('math_code', 'policy_code')})
        training = dict(status='COMPLETE_FIXED_FINAL500_CROP_COMPARISON_NOT_QUALITY', completed_updates=500, successful_micro=2000,
            adapter_reload_all288_exact=True, adapter_weights=reg['adapter_weights'], adapter_directory=reg['adapter_directory'])
        accepted = dict(status='PASS_CROP_TRAINED_SCREEN_FINAL500_FIRST_QA', training_completion=reg['fixed_training_completion'])
        return reg, result, fit, training, accepted

    def test_only_new47_pass_not_old33_pass_or_unknown(self):
        gain49.validate_gain_admission(*self.admission())
        for key, value in [('status', 'PASS_NATIVE_CROP_SCREEN_ONLY'), ('status', 'STOP_GAIN_CRITIC_SCREEN20_REJECTED'),
                ('confirm_admitted', False), ('primary', 'GEOM11'), ('production_admitted', True), ('fixed_final_checkpoint', False)]:
            args = copy.deepcopy(self.admission()); args[1][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): gain49.validate_gain_admission(*args)

    def test_all_weights_rms_code_catalog_and_qa_bindings_match(self):
        for owner, key in [(1, 'critic_weights'), (1, 'source_catalog'), (1, 'screen_output_acceptance'),
                (1, 'registration'), (2, 'math_code'), (2, 'policy_code'), (3, 'adapter_weights'), (4, 'training_completion')]:
            args = copy.deepcopy(self.admission()); args[owner][key] = ref('different')
            with self.subTest(owner=owner, key=key), self.assertRaises(ValueError): gain49.validate_gain_admission(*args)
        args = copy.deepcopy(self.admission()); args[3]['completed_updates'] = 4
        with self.assertRaises(ValueError): gain49.validate_gain_admission(*args)

    def test_native19_exact_order_and_gainfit_screen_disjoint(self):
        gain49.validate_confirm_scope(records(), catalog())
        for mode in ('order', 'identity', 'bytes', 'exclude', 'role', 'count'):
            rows, old = records(), catalog()
            if mode == 'order': rows[0], rows[1] = rows[1], rows[0]
            elif mode == 'identity': rows[0]['source_id'] = old['sources'][0]['source_id']
            elif mode == 'bytes': rows[0]['source_sha256'] = old['sources'][-1]['source_sha256']
            elif mode == 'exclude': rows[0]['source_id'] = gain49.EXCLUDED_SOURCE
            elif mode == 'role': rows[0]['role'] = 'train'
            else: old['sources'].pop()
            with self.subTest(mode=mode), self.assertRaises(ValueError): gain49.validate_confirm_scope(rows, old)

    def test_pure36_algorithm_reused_with_fresh_purpose49_identity(self):
        rows = records(); original = pure36.build_confirm_cases(rows)
        plan = gain49.build_gain_confirm_plan(rows, pure36)
        self.assertEqual(len(plan['cases']), 247)
        self.assertFalse(set(original['confirm_ids']) & set(plan['confirm_ids']))
        self.assertEqual([(c['source_id'], c['a'], c['b']) for c in plan['cases']],
                         [(c['source_id'], c['a'], c['b']) for c in original['cases']])
        lookup = {c['id']: c for c in plan['cases']}
        for pair in plan['pair_index']:
            a, b = lookup[pair['first_id']], lookup[pair['reverse_id']]
            self.assertEqual((a['a'], a['b']), (b['b'], b['a']))
            self.assertEqual(pair['same_crop'], a['a'] == a['b'])
        self.assertEqual(sum(p['same_crop'] for p in plan['pair_index']), 19)
        self.assertFalse(plan['old_CE_admission_used']); self.assertFalse(plan['original20_complete'])

    def test_no_gt_can_change_the_registered_case_plan(self):
        rows = records(); expected = gain49.build_gain_confirm_plan(rows, pure36)
        for i, row in enumerate(rows): row['human_reference_not_read'] = [i, 0, 1, 1]
        self.assertEqual(expected, gain49.build_gain_confirm_plan(rows, pure36))
        self.assertFalse(expected['GT_used_for_input_or_pair_choice'])

    def test_joint_quality_true_and_original_qa_are_required(self):
        args = copy.deepcopy(self.admission()); args[1]['reports']['JOINT14']['quality']['admitted'] = False
        with self.assertRaises(ValueError): gain49.validate_gain_admission(*args)
        args = copy.deepcopy(self.admission()); args[4]['status'] = 'NOT_COMPLETED'
        with self.assertRaises(ValueError): gain49.validate_gain_admission(*args)
        self.assertEqual(gain49.DEADLINE.isoformat(), '2026-10-18T03:22:24+00:00')


if __name__ == '__main__':
    unittest.main()
