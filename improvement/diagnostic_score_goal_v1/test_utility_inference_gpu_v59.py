import copy
import hashlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

import torch

import utility_inference_gpu_v59 as gpu


def reference(name):
    return dict(path='/synthetic/'+name, sha256=hashlib.sha256(name.encode()).hexdigest())


def admissions(scope='resized20'):
    reg = dict(schema=gpu.SCHEMA, scope=scope, model_role='UTILITY_'+scope, expected_inputs=240,
        expected_sources={'resized20':20, 'resized19':19, 'production':6563}[scope], profile='RESIZED_OBSERVATION_PLANE',
        adapter_weights=reference('adapter'), value_weights=reference('value'), training_completion=reference('training'),
        frozen_GPU55_registration=reference('reg55'), confirm_quality_admission=reference('confirm'))
    if scope == 'production': reg.update(official_source_count=426, affected_video_count=303)
    training = dict(status='COMPLETE_FIXED_FINAL500_UTILITY_VALUES_NOT_QUALITY', completed_updates=500,
        successful_micro=2000, actual_training_forwards=4000, adapter_reload_all288_exact=True,
        head_reload_exact=True, beta_reload_exact=True, adapter_weights=reg['adapter_weights'],
        value_weights=reg['value_weights'], GPU_registration=reg['frozen_GPU55_registration'])
    native = dict(status='PASS_UTILITY_SCREEN20_ONLY', evaluation=dict(quality=dict(admitted=True)),
        confirm_admitted=True, fixed_final_checkpoint=True, adapter_weights=reg['adapter_weights'],
        value_weights=reg['value_weights'], training_completion=reg['training_completion'])
    profile = dict(status='PASS_UTILITY_RESIZED20_PROFILE_ONLY', quality=dict(admitted=True),
        adapter_weights=reg['adapter_weights'], value_weights=reg['value_weights'])
    confirm = dict(profile, status='PASS_UTILITY_RESIZED19_CONFIRM_ONLY')
    production = dict(status='ADMIT_UTILITY_EXACT_NATIVE_PTS_SPATIAL_ONLY', production_admitted=True,
        confirm_quality_admission=reg['confirm_quality_admission'], adapter_weights=reg['adapter_weights'], value_weights=reg['value_weights'])
    if scope == 'production': production.update(expected_sources=6563, observations=6563, official_source_count=426,
        affected_video_count=303, whole426_preserved=True)
    return reg, training, native, profile, confirm, production


def stage_fixture(directory):
    values = dict(input_ids=torch.tensor([[1, 2]]), attention_mask=torch.ones((1, 2), dtype=torch.int64),
        pixel_values=torch.zeros((12, 1536)), image_grid_thw=torch.tensor([[1, 2, 2]]*3))
    other = {k:v.clone() for k, v in values.items()}; other['input_ids'][0, 1] = 3
    reg = dict(model_role='UTILITY_resized20', scope='resized20', profile='RESIZED_OBSERVATION_PLANE',
        adapter_weights=reference('adapter'), value_weights=reference('value'), expected_inputs=3,
        _registration_ref=reference('reg59'))
    entries, requests = [], {}
    for i in range(3):
        path = directory/('input%d.json'%i); value = other if i == 2 else values
        request = dict(id='case%d'%i, source_id='s', source_sha256='a'*64,
            class_token_ids=[15, 16, 17], input_signature=gpu.signature(value), image_grid_thw=value['image_grid_thw'].tolist(),
            adapter_weights=reg['adapter_weights'], value_weights=reg['value_weights'], scope=reg['scope'], profile=reg['profile'],
            native_RGB_recovered=False, reference_or_target_in_prompt=False)
        gpu.save(path, request); r = gpu.ref(path)
        entries.append(dict(id=request['id'], source_id='s', source_sha256='a'*64, role='screen', input=r))
        requests[str(path.resolve())] = (value, request)
    gets = []
    def get(r):
        gets.append(r)
        if r == entries[2]['input']:
            raise AssertionError('An externally adopted input must never call58 reader.get')
        return requests[str(Path(r['path']).resolve())]
    inputs = SimpleNamespace(prepared=dict(class_token_ids=[15, 16, 17]), get=get)
    adopted = dict(input=reference('oldinput'), receipt=reference('oldreceipt'), raw_hidden=reference('oldraw'),
        acceptance=reference('oldQA'), model_role='UTILITY_TRAINED_screen', GPU_value=.25,
        adapter_weights=reg['adapter_weights'], value_weights=reg['value_weights'])
    external = {gpu.exact_key(requests[str((directory/'input2.json').resolve())][1],
                             reg['adapter_weights'], reg['value_weights']):adopted}
    return reg, entries, inputs, external, gets


class UtilityInferenceTests(unittest.TestCase):
    def test_conditional_scopes_need_actual_sequential_quality_and_exact_weights(self):
        for scope in gpu.SCOPES:
            reg, train, native, profile, confirm, production = admissions(scope)
            gpu.validate_admission(reg, scope, train, native, profile, confirm, production)
            bad = copy.deepcopy(native); bad['evaluation']['quality']['admitted'] = False
            with self.assertRaises(ValueError): gpu.validate_admission(reg, scope, train, bad, profile, confirm, production)
            bad = dict(train, value_weights=reference('wrong'))
            with self.assertRaises(ValueError): gpu.validate_admission(reg, scope, bad, native, profile, confirm, production)
        reg, train, native, profile, confirm, production = admissions('production')
        with self.assertRaises(ValueError): gpu.validate_admission(reg, 'production', train, native, profile, confirm,
                                                                  dict(production, production_admitted=False))
        with self.assertRaises(ValueError): gpu.validate_admission(reg, 'production', train, native, profile,
                                                                  dict(confirm, status='STOP'), production)
        for change in (dict(observations=426), dict(whole426_preserved=False), dict(official_source_count=303)):
            with self.assertRaises(ValueError): gpu.validate_admission(reg, 'production', train, native, profile, confirm,
                                                                      dict(production, **change))

    def test_prepared_exact_partition_counts_and_permanent_missing_source(self):
        reg = dict(scope='resized19', profile='RESIZED_OBSERVATION_PLANE', expected_inputs=2, expected_sources=19,
            CPU_registration=reference('cpu58'), prepared=reference('prepared'),
            adapter_weights=reference('adapter'), value_weights=reference('value'))
        entries = [dict(id=str(i), source_id='s'+str(i)) for i in range(2)]
        prepared = dict(scope='resized19', profile=reg['profile'], sources=19, adapter_weights=reg['adapter_weights'],
            value_weights=reg['value_weights'], inference_inputs=entries, execution_entries=[entries[0]],
            adopted_success={'1':{}}, original20_complete=False, native_RGB_recovered=False)
        gate = dict(status=gpu.CPU_GATE, registration=reg['CPU_registration'], prepared=reg['prepared'], scope='resized19',
            sources=19, inference_inputs=2, execution_inputs=1, adopted_successes=1,
            first_independent_crop_processor_QA=True, first_compressed_save_and_reader_roundtrip=True, native_RGB_recovered=False)
        self.assertEqual(gpu.validate_prepared(reg, gate, prepared), entries)
        for change in ('overlap', 'missing', 'source', 'nativeclaim', 'count'):
            p, g = copy.deepcopy(prepared), copy.deepcopy(gate)
            if change == 'overlap': p['execution_entries'] = entries
            if change == 'missing': p['adopted_success'] = {}
            if change == 'source': p['inference_inputs'][1]['source_id'] = 'gnmc:test:006575.jpeg'
            if change == 'nativeclaim': p['native_RGB_recovered'] = True
            if change == 'count': g['inference_inputs'] = 3
            with self.subTest(change=change), self.assertRaises(ValueError): gpu.validate_prepared(reg, g, p)

    def test_new_external_internal_counts_and_external_no_reader_or_raw_load(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); reg, entries, inputs, external, gets = stage_fixture(root)
            observed, order, successful = [], [], []
            def observe(values):
                observed.append(1)
                return torch.arange(4096, dtype=torch.float32), lambda:(order.append('value') or .5)
            def write(path, raw):
                with path.open('xb') as f: torch.save(raw, f)
                order.append('persist')
            with mock.patch.object(gpu, 'bound', side_effect=lambda r:Path(r['path'])), \
                 mock.patch.object(torch, 'load', side_effect=AssertionError('No previously QAd raw load allowed')):
                completed = gpu.ordered_stage(root, inputs, entries, reg, observe=observe, write_tensor=write,
                    external=external, successful_raw=successful)
            done = gpu.read(completed['path'])
            self.assertEqual((done['actual_forward_calls'], done['external_aliases'], done['aliases']), (1, 1, 1))
            self.assertEqual(len(gets), 1); self.assertEqual(len(observed), 1); self.assertEqual(len(successful), 1)
            self.assertEqual(order, ['persist', 'value'])
            receipts = [gpu.read(row['receipt']['path']) for row in done['entries']]
            self.assertTrue(receipts[0]['actual_new_forward'])
            self.assertTrue(receipts[1]['internal_alias']); self.assertFalse(receipts[1]['external_alias'])
            self.assertTrue(receipts[2]['external_alias']); self.assertFalse(receipts[2]['actual_new_forward'])
            self.assertEqual(receipts[2]['adopted_model_role'], 'UTILITY_TRAINED_screen')
            self.assertEqual(receipts[2]['adopted_from_acceptance'], reference('oldQA'))

    def test_returned_raw_survives_head_failure_and_nonfinite_output_no_empty(self):
        for mode in ('head', 'nonfinite'):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary); reg, entries, inputs, external, gets = stage_fixture(root)
                reg['expected_inputs'] = 1; successful = []
                def observe(values):
                    raw = torch.zeros(4096)
                    if mode == 'nonfinite': raw[0] = float('nan')
                    def head(): raise RuntimeError('synthetic head failure')
                    return raw, head
                def write(path, raw):
                    with path.open('xb') as f: torch.save(raw, f)
                with mock.patch.object(gpu, 'bound', side_effect=lambda r:Path(r['path'])):
                    with self.assertRaises((ValueError, RuntimeError)):
                        gpu.ordered_stage(root, inputs, entries[:1], reg, observe=observe, write_tensor=write,
                            external={}, successful_raw=successful)
                self.assertEqual(len(successful), 1)
                self.assertTrue(Path(successful[0]['raw_hidden']['path']).is_file())
                events = [json.loads(line) for line in (root/'ordered/attempts.jsonl').read_text().splitlines()]
                self.assertEqual([e['event'] for e in events], ['BEGIN_NEW_ROLE_FORWARD', 'FIRST_RAW_PERSISTED'])
                self.assertFalse((root/'ordered/completion.json').exists())

    def test_exact_key_owner_class_signature_and_two_weight_refs(self):
        request = dict(source_id='s', source_sha256='a'*64, class_token_ids=[15, 16, 17],
                       input_signature={k:dict(sha256='b'*64) for k in gpu.INPUT_KEYS})
        key = gpu.exact_key(request, reference('adapter'), reference('value'))
        for change in (dict(source_id='other'), dict(source_sha256='c'*64), dict(class_token_ids=[0, 1, 2])):
            self.assertNotEqual(gpu.exact_key(dict(request, **change), reference('adapter'), reference('value')), key)
        self.assertNotEqual(gpu.exact_key(request, reference('adapter'), reference('otherhead')), key)
        with self.assertRaises(ValueError): gpu.exact_key(dict(request, input_signature={}), reference('adapter'), reference('value'))

    def test_adopted_index_uses_accepted_metadata_and_artifact_binding_without_tensor_qa(self):
        adapter, value, training = reference('adapter'), reference('value'), reference('training')
        request = dict(id='old', source_id='s', source_sha256='a'*64, class_token_ids=[15, 16, 17],
                       input_signature={k:dict(sha256='b'*64) for k in gpu.INPUT_KEYS})
        inp, rec, raw, accepted = reference('oldinput'), reference('oldreceipt'), reference('oldraw'), reference('oldQA')
        receipt = dict(request, input=inp, model_role='UTILITY_TRAINED_screen', raw_hidden=raw, head_value=.2,
                       adapter_weights=adapter, value_weights=value)
        prediction = dict(id='old', source_id='s', source_sha256='a'*64, input=inp, receipt=rec,
                          raw_hidden=raw, CPU_value=.20000001)
        docs = {inp['path']:request, rec['path']:receipt, accepted['path']:dict(
            status='PASS_UTILITY_FINAL500_SCREEN_FIRST_RAW_QA', adapter_weights=adapter, value_weights=value,
            training_completion=training, predictions=[prediction])}
        with mock.patch.object(gpu, 'bound', side_effect=lambda r:Path(r['path'])) as bindings, \
             mock.patch.object(gpu, 'read', side_effect=lambda p:docs[Path(p).as_posix()]), \
             mock.patch.object(torch, 'load', side_effect=AssertionError('Old QA tensor must not be loaded')):
            index = gpu.adopted_index([accepted], adapter, value, training)
            item = index[gpu.exact_key(request, adapter, value)]
            self.assertEqual(item['raw_hidden'], raw)
            self.assertEqual(item['CPU_value'], prediction['CPU_value'])
            self.assertIn(mock.call(raw), bindings.call_args_list)
            bad = docs[accepted['path']]['adapter_weights']; docs[accepted['path']]['adapter_weights'] = reference('wrong')
            with self.assertRaises(ValueError): gpu.adopted_index([accepted], adapter, value, training)
            docs[accepted['path']]['adapter_weights'] = bad

    def test_count_failure_before_any_model_observation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); reg, entries, inputs, external, gets = stage_fixture(root)
            reg['expected_inputs'] = 4
            with self.assertRaises(ValueError):
                gpu.ordered_stage(root, inputs, entries, reg,
                    observe=lambda values:self.fail('Count mismatch must precede any model call'),
                    write_tensor=None, external=external, successful_raw=[])
            self.assertFalse((root/'ordered').exists())


if __name__ == '__main__':
    unittest.main()
