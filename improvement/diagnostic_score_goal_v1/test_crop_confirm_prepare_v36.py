import copy
import hashlib
import unittest

import crop_confirm_prepare_v36 as confirm
import crop_geometry_v31 as geometry


def ref(name):
    return dict(path='/synthetic/'+name, sha256=hashlib.sha256(name.encode()).hexdigest())


class ConfirmTests(unittest.TestCase):
    def fixture(self):
        refs, rows, bases, proofs = [], [], [], {}
        for index in range(20):
            sid = confirm.EXCLUDED_SOURCE if index == 0 else 'gnmc:test:%06d.jpeg'%index
            digest = hashlib.sha256(sid.encode()).hexdigest(); entry = ref('C%02d.json'%index)
            refs.append(entry)
            row = dict(item_id=sid, source_sha256=digest, role='confirm', width=500, height=333,
                RGB=ref(sid+'.npy'), original_proof=ref(sid+'.proof'), new_vision=ref(sid+'.pt'),
                new_vision_signature={'pixel_values': {'sha256': digest}}, reference_available_to_inference=False)
            rows.append(row); proofs[sid] = dict(source_sha256=digest, RGB_sha256=digest)
            if index:
                bases.append(dict(reference=ref(sid+'.base.json'), value=dict(item_id=sid, source_sha256=digest,
                    source=entry, original_BASE_box=[5, 6, 400], original_BASE_raw=ref(sid+'.base_raw.json'))))
        excluded = dict(item_id=confirm.EXCLUDED_SOURCE, input=refs[0])
        return refs, rows, bases, proofs, excluded

    def catalog(self):
        return confirm.build_confirm_catalog(*self.fixture(), geometry)

    def admission(self):
        reg = dict(native_remaining_registration=ref('remaining33'), adapter_weights=ref('final500'),
            adapter_directory='/synthetic/adapter/crop', model_config=ref('config'), geometry_code=ref('geometry'), input_code=ref('image'))
        remaining = dict(original_pilot_registration=ref('pilot32'))
        pilot = dict(_reference=ref('pilot32'), model_config=reg['model_config'], CPU_registration=ref('CPU31'))
        cpu = dict(_reference=ref('CPU31'), geometry_code=reg['geometry_code'], input_code=reg['input_code'])
        screen = dict(status='PASS_NATIVE_CROP_SCREEN_ONLY', confirm_admitted=True, primary='TRAINED', fixed_final_checkpoint=True,
            registration=reg['native_remaining_registration'], adapter_weights=reg['adapter_weights'])
        training = dict(status='COMPLETE_FIXED_FINAL500_CROP_COMPARISON_NOT_QUALITY', completed_updates=500,
            successful_micro=2000, adapter_reload_all288_exact=True, adapter_weights=reg['adapter_weights'],
            adapter_directory=reg['adapter_directory'], remaining_admission=reg['native_remaining_registration'])
        return reg, screen, remaining, training, pilot, cpu

    def test_native_pass_and_exact_final500_are_mandatory(self):
        confirm.validate_native_admission(*self.admission())
        for section, key, wrong in [(1, 'confirm_admitted', False), (1, 'primary', 'BASE'),
                (1, 'status', 'STOP_NATIVE_CROP_SCREEN'), (3, 'completed_updates', 4),
                (3, 'adapter_reload_all288_exact', False), (3, 'adapter_weights', ref('other')),
                (4, 'model_config', ref('other-config'))]:
            values = copy.deepcopy(self.admission()); values[section][key] = wrong
            with self.subTest(key=key), self.assertRaises(ValueError):
                confirm.validate_native_admission(*values)

    def test_exact_remaining19_and_baseline_first(self):
        records = self.catalog()
        self.assertEqual(len(records), 19)
        self.assertEqual([r['original_index'] for r in records], list(range(1, 20)))
        self.assertTrue(all(r['source_id'] != confirm.EXCLUDED_SOURCE and r['pool'][0] == [5, 6, 400] for r in records))
        self.assertFalse(any('reference_xywh' in r or 'candidate_ious' in r for r in records))

    def test_excluded_or_reordered_or_wrong_source_rejected(self):
        for mode in ('first', 'order', 'sha', 'role', 'baseline', 'proof', 'duplicate'):
            args = copy.deepcopy(self.fixture())
            if mode == 'first': args[4]['input'] = args[0][1]
            elif mode == 'order': args[2][0], args[2][1] = args[2][1], args[2][0]
            elif mode == 'sha': args[2][0]['value']['source_sha256'] = '0'*64
            elif mode == 'role': args[1][1]['role'] = 'screen'
            elif mode == 'baseline': args[2][0]['value']['original_BASE_box'] = [200, 0, 400]
            elif mode == 'proof': args[3][args[1][1]['item_id']]['source_sha256'] = '0'*64
            elif mode == 'duplicate': args[1][2]['item_id'] = args[1][1]['item_id']
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                confirm.build_confirm_catalog(*args, geometry)

    def test_complete_dual_order_self_controls_and_no_train(self):
        records = self.catalog(); plan = confirm.build_confirm_cases(records)
        self.assertEqual(len(plan['cases']), 247)
        cases = {r['id']: r for r in plan['cases']}
        self.assertEqual(len(cases), len(plan['confirm_ids']))
        self.assertEqual(sum(p['same_crop'] for p in plan['pair_index']), 19)
        for pair in plan['pair_index']:
            a, b = cases[pair['first_id']], cases[pair['reverse_id']]
            self.assertEqual((a['a'], a['b']), (b['b'], b['a']))
            self.assertEqual(a['source_id'], pair['source_id'])
            self.assertEqual(pair['same_crop'], a['a'] == a['b'])
        self.assertFalse(plan['GT_used_for_input_or_pair_choice'])
        self.assertFalse(plan['original20_complete'])

    def test_plan_cannot_observe_labels_and_rejects_unknown_scope(self):
        records = self.catalog(); expected = confirm.build_confirm_cases(records)
        for index, row in enumerate(records):
            row['human_reference_not_read'] = [index, 0, 1, 1]
        self.assertEqual(expected, confirm.build_confirm_cases(records))
        for wrong in (records[:-1], records+[records[0]]):
            with self.assertRaises(ValueError): confirm.build_confirm_cases(wrong)
        records[0]['source_id'] = confirm.EXCLUDED_SOURCE
        with self.assertRaises(ValueError): confirm.build_confirm_cases(records)

    def test_cpu_targets_only_original_confirm_reference_and_iou(self):
        records = self.catalog()
        labels = [dict(item_id=r['source_id'], source_sha256=r['source_sha256'], role='confirm',
            reference_xywh=[10., 10., 300., 200.]) for r in records]
        targets = confirm.build_cpu_targets(records, labels, geometry)
        self.assertEqual(len(targets), 19)
        self.assertEqual(targets[0]['candidate_ious'], [geometry.crop_iou(b, labels[0]['reference_xywh']) for b in records[0]['pool']])
        self.assertFalse(targets[0]['reference_modified'])
        for key, wrong in [('source_sha256', '0'*64), ('role', 'screen'), ('reference_xywh', [0, 0, 501, 1])]:
            changed = copy.deepcopy(labels); changed[0][key] = wrong
            with self.subTest(key=key), self.assertRaises(ValueError): confirm.build_cpu_targets(records, changed, geometry)
        with self.assertRaises(ValueError): confirm.build_cpu_targets(records, labels+[labels[0]], geometry)


if __name__ == '__main__':
    unittest.main()
