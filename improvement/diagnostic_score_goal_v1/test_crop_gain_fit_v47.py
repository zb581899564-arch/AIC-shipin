"""Synthetic47 joins/target sign/state writer/scope and one mocked-artifact CLI."""
import copy
import datetime as dt
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

import crop_gain_fit_v47 as fit47
import crop_gain_math_v45 as math45
import crop_policy_v33 as policy33


def identity(value):
    return hashlib.sha256(value.encode()).hexdigest()


def train_fixture():
    sources, targets, pairs, predictions = [], {}, [], {}
    for i in range(602):
        sid = 'train%03d'%i; digest = identity(sid); pool = [[0, 0, 160], [0, 0, 128], [16, 0, 128]]
        sources.append(dict(source_id=sid, source_sha256=digest, role='train', width=160, height=90, pool=pool))
        targets[sid] = np.array([.4, .3, .2], dtype=np.float64)
        for a, b in ((0, 1), (1, 2)):
            first, reverse = sid+'_%d%d'%(a, b), sid+'_%d%d'%(b, a)
            pairs.append(dict(source_id=sid, source_sha256=digest, a=a, b=b, first_id=first, reverse_id=reverse))
            for cid, logits in ((first, [0., 1., 0.]), (reverse, [1., 0., 0.])):
                predictions[cid] = dict(id=cid, source_id=sid, source_sha256=digest, class_logits3=logits)
    return sources, targets, pairs, predictions


def scope_fixture(role='screen', count=20):
    sources, targets, pairs, predictions = [], {}, [], {}
    pool = [[0, 0, 160], [0, 0, 128], [16, 0, 128], [32, 0, 128], [0, 9, 128], [16, 9, 128], [32, 9, 128]]
    for i in range(count):
        sid = role+str(i); digest = identity(sid); boxes = copy.deepcopy(pool[:6] if i < 10 else pool)
        sources.append(dict(source_id=sid, source_sha256=digest, role=role, width=160, height=90, pool=boxes, baseline_box=boxes[0]))
        targets[sid] = np.full(len(boxes), .4, dtype=np.float64)
        for index in range(len(boxes)):
            first, reverse = sid+'_%dF'%index, sid+'_%dR'%index
            if index == 0:
                reverse = first
            pairs.append(dict(source_id=sid, candidate_index=index, first_id=first, reverse_id=reverse, same_crop=index == 0))
            for cid, logits in ((first, [0., 1., 0.]), (reverse, [1., 0., 0.])):
                predictions[cid] = dict(id=cid, source_id=sid, source_sha256=digest, class_logits3=logits)
    return sources, targets, pairs, predictions


class GainFitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.train, cls.targets, cls.pairs, cls.raw = train_fixture()
        cls.rows, cls.mapping, cls.design = fit47.build_training_rows(cls.train, cls.targets, cls.pairs, cls.raw, math45, policy33)
        cls.state, cls.report = math45.fit(cls.rows)

    def test_exact602_two_unordered_target_sign_and_complete2408(self):
        self.assertEqual(len(self.rows), 602); self.assertEqual(len(self.mapping), 1204)
        self.assertEqual(self.rows[0]['pairs'][0]['target'], .3-.4)
        self.assertEqual(self.rows[0]['pairs'][1]['target'], .2-.3)
        self.assertEqual(self.report['sources'], 602); self.assertEqual(self.report['solves'], 3)
        missing = dict(self.raw); missing.pop(next(iter(missing)))
        with self.assertRaises((KeyError, ValueError)):
            fit47.build_training_rows(self.train, self.targets, self.pairs, missing, math45, policy33)
        with self.assertRaises(ValueError):
            fit47.build_training_rows(self.train[:-1], self.targets, self.pairs, self.raw, math45, policy33)
        wrong = copy.deepcopy(self.pairs); wrong[0]['a'], wrong[0]['b'] = wrong[0]['b'], wrong[0]['a']
        with self.assertRaises(ValueError):
            fit47.build_training_rows(self.train, self.targets, wrong, self.raw, math45, policy33)

    def test_original_targets_join_without_reference_recomputation_or_mutation(self):
        source = self.train[0]
        target = dict(source_id=source['source_id'], source_sha256=source['source_sha256'], role='train',
            reference_modified=False, baseline_index=0, candidate_ious=[.4, .3, .2],
            original_reference_xywh='NOT_CONSUMED_BY_THIS_JOIN')
        before = copy.deepcopy(target)
        result = fit47.joined_targets([source], [target])
        np.testing.assert_array_equal(result[source['source_id']], [.4, .3, .2]); self.assertEqual(target, before)
        for change in ({'reference_modified':True}, {'candidate_ious':[.4, None, .2]}, {'source_sha256':'f'*64}):
            with self.assertRaises(ValueError): fit47.joined_targets([source], [dict(target, **change)])

    def test_npz_scalar_array_bits_prediction_reload_and_no_success_overwrite(self):
        screen, _, pairs, raw = scope_fixture()
        design = fit47.build_scope_design(screen, pairs, raw, math45, policy33, phase='screen20')
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'critic.npz'
            loaded = fit47.save_reload_state(path, self.state, math45, [self.design]+[row['design'] for row in design])
            self.assertEqual(set(loaded), math45.STATE_KEYS)
            for key in self.state:
                self.assertEqual(np.asarray(self.state[key]).tobytes(), loaded[key].tobytes())
            with self.assertRaises(FileExistsError): fit47.save_reload_state(path, self.state, math45, [self.design])

    def test_complete_scope_self_zero_and_old_geometry_mean_is_independent_gate(self):
        for role, count, phase in (('screen', 20, 'screen20'), ('confirm', 19, 'confirm19')):
            sources, targets, pairs, raw = scope_fixture(role, count)
            result = fit47.evaluate_scope(sources, pairs, raw, targets, self.state, math45, policy33,
                                          phase=phase, original_geometry_mean=float(np.mean([.4]*count)))
            self.assertEqual(result['phase'], phase)
            self.assertEqual(result['self_gain_exact_zero'], dict(JOINT14=count, GEOM11=count, MARGIN1=count))
            self.assertEqual(result['summaries']['JOINT14']['sources'], count)
            self.assertFalse(result['quality']['admitted'])
            self.assertFalse(result['quality']['checks']['beats_original33_geometry'])
            bad = copy.deepcopy(pairs); bad[0]['reverse_id'] = pairs[1]['reverse_id']
            with self.assertRaises(ValueError): fit47.build_scope_design(sources, bad, raw, math45, policy33, phase=phase)

    def test_bound_artifact_sha_rejects_changed_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'artifact.json'; path.write_text('{}', encoding='utf-8')
            reference = fit47.ref(path); self.assertEqual(fit47.bound(reference), path)
            path.write_text('{"changed":true}', encoding='utf-8')
            with self.assertRaises(ValueError): fit47.bound(reference)

    def test_one_mocked_artifact_run_writer_contract_stop_and_exclusive_directory(self):
        # All input objects below are synthetic. Bound/read/module are stubbed;
        # real output JSON/NPZ bytes and their SHA references are exercised.
        with tempfile.TemporaryDirectory() as directory, patch.dict('os.environ', {'CUDA_VISIBLE_DEVICES':''}):
            root = Path(directory); objects = {}
            def fake_ref(name):
                return dict(path=str(root/'virtual'/name), sha256=identity(name))
            reg = dict(schema=fit47.SCHEMA, deadline_utc=(dt.datetime.now(dt.timezone.utc)+dt.timedelta(days=1)).isoformat())
            reg.update({name:fake_ref(name) for name in fit47.REF_FIELDS})
            reg['fit_code'] = fit47.ref(fit47.__file__)
            def put(key, value):
                objects[reg[key]['path']] = value
            train, train_targets, train_pairs, raw_train = copy.deepcopy((self.train, self.targets, self.pairs, self.raw))
            screen, screen_targets, screen_pairs, raw_screen = scope_fixture()
            catalog = train+screen; all_targets = {**train_targets, **screen_targets}
            put('original_screen_catalog', dict(sources=catalog)); put('gain_catalog', dict(sources=train))
            put('CPU_targets', dict(sources=[dict(source_id=s['source_id'], source_sha256=s['source_sha256'], role=s['role'],
                baseline_index=0, reference_modified=False, candidate_ious=all_targets[s['source_id']].tolist()) for s in catalog]))
            def entries(raw):
                return [dict(id=cid, source_id=p['source_id'], source_sha256=p['source_sha256'], input=fake_ref(cid+'_request')) for cid, p in raw.items()]
            train_entries = entries(raw_train); screen_entries = entries(raw_screen)
            first32 = {s['source_id'] for s in sorted(train, key=lambda s:(s['source_sha256'], s['source_id']))[:32]}
            pilot = [e for e in train_entries if e['source_id'] in first32]; remaining = [e for e in train_entries if e['source_id'] not in first32]
            original_bindings = {key:reg[value] for key, value in (('old_prepared','original_screen_prepared'),
                ('old_catalog','original_screen_catalog'), ('old_case_plan','original_screen_case_plan'), ('old_input_gate','original_screen_input_acceptance'))}
            put('gain_prepared', dict(source_catalog=reg['gain_catalog'], CPU_targets=reg['CPU_targets'], adapter_weights=reg['adapter_weights'],
                pair_index=train_pairs, original_bindings=original_bindings, class_token_ids=[71,72,73],
                train_inputs=train_entries, pilot_inputs=pilot, remaining_inputs=remaining))
            put('gain_plan', dict(pair_index=train_pairs))
            put('gain_CPU_registration', dict(CPU_targets=reg['CPU_targets'], gain_protocol=reg['gain_protocol'],
                fixed_training_completion=reg['fixed_training_completion'], adapter_weights=reg['adapter_weights'], old_STOP=reg['original_comparison']))
            put('gain_input_acceptance', dict(status='PASS_ALL_GAIN44_2408_ADOPT2000_NEW408_COMBINATIONS_FIRST_CPU_QA',
                registration=reg['gain_CPU_registration'], prepared=reg['gain_prepared'], adopted_inputs=2000,
                first_new_combinations=408, new_image_processor_calls=0, new_original_decodes=0))
            put('original_screen_prepared', dict(source_catalog=reg['original_screen_catalog'], case_plan=reg['original_screen_case_plan'],
                class_token_ids=[71,72,73], screen_inputs=screen_entries))
            put('original_screen_case_plan', dict(pair_index=screen_pairs, GT_used_for_input_or_pair_choice=False))
            put('original_screen_input_acceptance', dict(status='PASS_ALL_CROP31_TRIPLET_FIRST_CPU_QA', prepared=reg['original_screen_prepared']))
            put('fixed_training_completion', dict(status='COMPLETE_FIXED_FINAL500_CROP_COMPARISON_NOT_QUALITY',
                completed_updates=500, successful_micro=2000, adapter_reload_all288_exact=True, adapter_weights=reg['adapter_weights']))
            put('gain_GPU_registration', dict(CPU_registration=reg['gain_CPU_registration'], input_acceptance=reg['gain_input_acceptance'],
                adapter_weights=reg['adapter_weights'], fixed_training_completion=reg['fixed_training_completion']))
            put('gain_remaining_admission', dict(original_GPU_registration=reg['gain_GPU_registration'],
                pilot_output_acceptance=reg['pilot_output_acceptance'], input_acceptance=reg['gain_input_acceptance']))
            for key, stage_entries, status, gpu_ref in (
                ('pilot_output_acceptance', pilot, 'PASS_GAIN_PILOT128_FIRST_RAW_QA', reg['gain_GPU_registration']),
                ('remaining_output_acceptance', remaining, 'PASS_GAIN_REMAINING2280_FIRST_RAW_QA', reg['gain_remaining_admission'])):
                put(key, dict(status=status, GPU_registration=gpu_ref, original_GPU_registration=reg['gain_GPU_registration'],
                    adapter_weights=reg['adapter_weights'], no_utility_targets_read=True,
                    predictions=[dict(raw_train[e['id']], input=e['input'], receipt=fake_ref(e['id']+'_receipt'),
                                      adapter_weights=reg['adapter_weights']) for e in stage_entries]))
            comparison_registration = fake_ref('old33_registration'); geometry_receipt = fake_ref('old_geometry_receipt')
            objects[geometry_receipt['path']] = dict(coefficients=fake_ref('old_geometry_coefficients'), parameters=13,
                                                    training_sources=602, eval_target_fitted=False)
            put('original_comparison', dict(status='STOP_NATIVE_CROP_SCREEN', primary='TRAINED', fixed_final_checkpoint=True,
                adapter_weights=reg['adapter_weights'], TRAINED_acceptance=reg['screen_output_acceptance'], CPU_targets=reg['CPU_targets'],
                policy_code=reg['policy_code'], registration=comparison_registration,
                reports=dict(TRAINED=dict(summary=dict(mean_geometry_iou=float(np.mean([.4]*20))))), geometry_control=geometry_receipt,
                selected=dict(TRAINED=[dict(source_id=s['source_id'], source_sha256=s['source_sha256'], geometry_index=0, geometry_iou=.4) for s in screen])))
            screen_predictions = []
            for entry in screen_entries:
                p = raw_screen[entry['id']]; receipt_ref = fake_ref(entry['id']+'_screen_receipt')
                objects[receipt_ref['path']] = dict(id=entry['id'], source_id=p['source_id'], source_sha256=p['source_sha256'],
                    input=entry['input'], model_role='TRAINED_screen', class_token_ids=[71,72,73], class_logits=p['class_logits3'])
                screen_predictions.append(dict(id=entry['id'], source_id=p['source_id'], source_sha256=p['source_sha256'], input=entry['input'], receipt=receipt_ref))
            put('screen_output_acceptance', dict(status='PASS_CROP_TRAINED_SCREEN_FINAL500_FIRST_QA',
                training_completion=reg['fixed_training_completion'], registration=comparison_registration, predictions=screen_predictions))
            fit47.save(root/'crop_gain_fit_registration_47.json', reg)
            real_read = fit47.read
            def read_stub(path):
                return objects[str(path)] if str(path) in objects else real_read(path)
            with patch.object(fit47, 'bound', side_effect=lambda value:Path(value['path'])), \
                    patch.object(fit47, 'read', side_effect=read_stub), \
                    patch.object(fit47, 'module', side_effect=lambda value,name:math45 if 'math45' in name else policy33), \
                    patch('builtins.print'):
                result = fit47.run(root)
                with self.assertRaises(FileExistsError): fit47.run(root)
            self.assertEqual(result['status'], 'STOP_GAIN_CRITIC_SCREEN20_REJECTED')
            self.assertEqual(result['primary'], 'JOINT14'); self.assertTrue(result['fixed_final_checkpoint'])
            self.assertFalse(result['confirm_admitted']); self.assertFalse(result['production_admitted'])
            self.assertEqual(result['geometry_control'], geometry_receipt)
            self.assertEqual(result['reports']['JOINT14']['summary']['sources'], 20)
            self.assertEqual(result['old_native_CE_quality'], 'STOP')
            self.assertEqual(result['critic_weights'], fit47.ref(root/fit47.OUTPUT/'critic_state.npz'))


if __name__ == '__main__':
    unittest.main()
