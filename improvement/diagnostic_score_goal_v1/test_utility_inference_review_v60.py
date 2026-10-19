"""Synthetic artifact integration only: no real raw/input/model/processor."""
import copy
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

import numpy as np
import torch

import crop_policy_v33 as policy33
import utility_inference_gpu_v59 as gpu59
import utility_inference_review_v60 as review60
import utility_scope_math_v60 as math60
import utility_value_review_v56 as review56


def bounded(reference):
    path = Path(reference['path'])
    if not path.is_file() or gpu59.sha(path) != reference['sha256']:
        raise ValueError('Synthetic missing/changed bound artifact: '+str(path))
    return path


def put(path, value):
    gpu59.save(path, value)
    return gpu59.ref(path)


def rewrite(path, value):
    with path.open('w', encoding='utf-8') as stream:
        json.dump(value, stream, allow_nan=False)
    return gpu59.ref(path)


def tensor(path, value):
    with path.open('xb') as stream:
        torch.save(value, stream)
    return gpu59.ref(path)


def fixture(root):
    scope = 'production'; out = root/'utility_inference_59'/scope; out.mkdir(parents=True)
    roles = ('f1', 'r1', 'own', 'f2', 'r2')
    source_id, source_sha = 'video0@native00042', 'a'*64
    adapter = put(root/'adapter.metadata', {'synthetic':True})
    weight = torch.zeros((1, 4096)); weight[0, 0] = 1.
    value_ref = tensor(root/'value.pt', dict(weight=weight, geometry_beta=torch.zeros(11)))
    training = put(root/'training.json', {'only':'synthetic identity ref'})
    reg = dict(scope=scope, model_role='UTILITY_'+scope, profile='RESIZED_OBSERVATION_PLANE',
        expected_inputs=5, expected_sources=1, official_source_count=426, affected_video_count=1,
        input_acceptance_status='PASS_SYNTHETIC_PRODUCTION_INPUTS',
        adapter_weights=adapter, value_weights=value_ref, training_completion=training)
    requests, entries, actual_values = {}, [], {}
    input_classes = {'f1':11, 'r1':12, 'own':12, 'f2':13, 'r2':11}
    for name in roles:
        values = dict(input_ids=torch.tensor([[1, input_classes[name]]]), attention_mask=torch.ones((1, 2), dtype=torch.int64),
            pixel_values=torch.zeros((12, 1536)), image_grid_thw=torch.tensor([[1, 2, 2]]*3))
        request = dict(id=name, source_id=source_id, source_sha256=source_sha, class_token_ids=[15, 16, 17],
            input_signature=gpu59.signature(values), image_grid_thw=values['image_grid_thw'].tolist(),
            adapter_weights=adapter, value_weights=value_ref, scope=scope, profile=reg['profile'],
            native_RGB_recovered=False, reference_or_target_in_prompt=False)
        request_ref = put(root/(name+'.request.json'), request)
        entries.append(dict(id=name, source_id=source_id, source_sha256=source_sha, role='production', input=request_ref))
        requests[request_ref['path']] = request; actual_values[request_ref['path']] = values
    old_raw = tensor(root/'old_DO_NOT_TENSOR_LOAD.pt', torch.zeros(4096))
    old_input = put(root/'old.input.json', dict(requests[entries[1]['input']['path']], id='oldr'))
    old_receipt = put(root/'old.receipt.json', dict(requests[entries[1]['input']['path']], id='oldr', input=old_input,
        model_role='UTILITY_TRAINED_screen', raw_hidden=old_raw, head_value=0.))
    old_acceptance = put(root/'old.acceptance.json', dict(status='PASS_UTILITY_FINAL500_SCREEN_FIRST_RAW_QA',
        adapter_weights=adapter, value_weights=value_ref, training_completion=training,
        predictions=[dict(id='oldr', source_id=source_id, source_sha256=source_sha, input=old_input,
            receipt=old_receipt, raw_hidden=old_raw, CPU_value=0., GPU_value=0.)]))
    reg['adopted_output_acceptances'] = [old_acceptance]
    metadata = dict(input=old_input, receipt=old_receipt, raw_hidden=old_raw, acceptance=old_acceptance,
        model_role='UTILITY_TRAINED_screen', adapter_weights=adapter, value_weights=value_ref, CPU_value=0., GPU_value=0.)
    sources = put(root/'sources.json', dict(sources=[dict(source_id=source_id, source_sha256=source_sha, role='production',
        width=20, height=20, pool=[[0, 0, 16], [2, 2, 8], [1, 1, 10]], baseline_box=[0, 0, 16])]))
    pairs = [dict(source_id=source_id, candidate_index=0, first_id='own', reverse_id='own', same_crop=True),
        dict(source_id=source_id, candidate_index=1, first_id='f1', reverse_id='r1', same_crop=False),
        dict(source_id=source_id, candidate_index=2, first_id='f2', reverse_id='r2', same_crop=False)]
    plan = put(root/'plan.json', dict(GT_used_for_input_or_pair_choice=False, pair_index=pairs))
    prepared = dict(scope=scope, profile=reg['profile'], sources=1, official_source_count=426, affected_video_count=1,
        native_RGB_recovered=False, inference_inputs=entries,
        execution_entries=[e for e in entries if e['id'] not in ('r1', 'own')],
        adopted_success={'r1':copy.deepcopy(metadata), 'own':copy.deepcopy(metadata)},
        adapter_weights=adapter, value_weights=value_ref, class_token_ids=[15, 16, 17], source_catalog=sources, case_plan=plan)
    reg['prepared'] = put(root/'prepared.json', prepared)
    reg['CPU_registration'] = put(root/'cpu.registration.json', {'synthetic':True})
    reg['input_acceptance'] = put(root/'input_acceptance.json', dict(status=reg['input_acceptance_status'],
        registration=reg['CPU_registration'], prepared=reg['prepared'], scope=scope, sources=1,
        official_source_count=426, affected_video_count=1, inference_inputs=5, execution_inputs=3, adopted_successes=2,
        first_independent_crop_processor_QA=True, first_compressed_save_and_reader_roundtrip=True, native_RGB_recovered=False))
    reg['review_code'] = gpu59.ref(Path(review60.__file__))
    reg['GPU_code'] = gpu59.ref(Path(gpu59.__file__))
    reg['frozen_review56_code'] = gpu59.ref(Path(review56.__file__))
    reg['policy_math_code'] = gpu59.ref(Path(math60.__file__))
    reg['frozen_policy33_code'] = gpu59.ref(Path(policy33.__file__))
    reg['model_config'] = put(root/'config.json', {'only':'synthetic; inventory independently tested elsewhere'})
    with (root/'old_gain.npz').open('xb') as stream: np.savez(stream, RMS=np.ones(14), GEOM11_beta=np.zeros(11))
    with (root/'old_geometry.npz').open('xb') as stream: np.savez(stream, beta=np.zeros(13))
    reg['old_gain_state'] = gpu59.ref(root/'old_gain.npz')
    reg['old_geometry_control'] = put(root/'old_geometry.receipt.json', dict(coefficients=gpu59.ref(root/'old_geometry.npz')))
    registration_path = root/'registration59.json'; registration_ref = put(registration_path, reg)
    run_reg = dict(reg, _registration_ref=registration_ref)
    external = {gpu59.exact_key(requests[entries[1]['input']['path']], adapter, value_ref):metadata}
    def get(reference):
        request = requests[reference['path']]
        return actual_values[reference['path']], request
    def observe(values):
        h = torch.zeros(4096); h[0] = 2. if int(values['input_ids'][0, 1]) == 11 else 4.
        return h, lambda:float(h[0])
    def write_tensor(path, raw):
        with path.open('xb') as stream: torch.save(raw, stream)
    with mock.patch.object(gpu59, 'bound', side_effect=bounded):
        ordered_ref = gpu59.ordered_stage(out, SimpleNamespace(prepared=prepared, get=get), entries, run_reg,
            observe=observe, write_tensor=write_tensor, external=external, successful_raw=[])
    ordered = gpu59.read(ordered_ref['path'])
    # Exercise legal same-scope alias of an earlier *external* accepted entry.
    r_receipt = ordered['entries'][1]['receipt']
    self_record = ordered['entries'][2]; self_receipt = gpu59.read(self_record['receipt']['path'])
    self_receipt.update(external_alias=False, internal_alias=True, alias_of=r_receipt,
        adopted_from_acceptance=None, adopted_model_role=None, adopted_input=None)
    self_record['receipt'] = rewrite(Path(self_record['receipt']['path']), self_receipt)
    journal = Path(ordered['attempts']['path'])
    events = [json.loads(line) for line in journal.read_text().splitlines()]
    events = [event for event in events if not (event['id'] == 'own' and event['event'] == 'ADOPTED_PREVIOUSLY_QA_RAW')]
    for event in events:
        if event['id'] == 'own':
            event.update(receipt=self_record['receipt'], external_alias=False, internal_alias=True)
    journal.write_text(''.join(json.dumps(event)+'\n' for event in events), encoding='utf-8')
    ordered.update(attempts=gpu59.ref(journal), external_aliases=1, aliases=2)
    ordered_ref = rewrite(Path(ordered_ref['path']), ordered)
    top = dict(status='COMPLETE_UTILITY_V59_READONLY_SCOPE_NOT_QUALITY', GPU_registration=registration_ref,
        input_acceptance=reg['input_acceptance'], prepared=reg['prepared'], training_completion=training,
        labels_read=False, new_optimizer_updates=0, adapter_weights=adapter, value_weights=value_ref,
        inventory={}, base_fingerprint={}, completion=ordered_ref)
    put(out/'completion.json', top)
    put(root/'utility_production_resource_receipt_60.json', dict(unique_ledger_entries=1,
        record=dict(status='completed', exit_code=0)))
    return dict(root=root, registration_path=registration_path, ordered_ref=ordered_ref,
                old_raw=old_raw, top_path=out/'completion.json')


def corrupt(f, mode):
    ordered = gpu59.read(f['ordered_ref']['path'])
    record = ordered['entries'][0]
    receipt_path = Path(record['receipt']['path']); receipt = gpu59.read(receipt_path)
    if mode == 'head': receipt['head_value'] = 999.
    elif mode == 'alias': receipt['external_alias'] = True
    elif mode == 'missing_raw': Path(receipt['raw_hidden']['path']).unlink()
    elif mode == 'missing_persist':
        path = Path(ordered['attempts']['path'])
        events = [json.loads(line) for line in path.read_text().splitlines()]
        path.write_text(''.join(json.dumps(e)+'\n' for e in events if not (e['id'] == record['id']
            and e['event'] == 'FIRST_RAW_PERSISTED')), encoding='utf-8')
        ordered['attempts'] = gpu59.ref(path)
    if mode in ('head', 'alias'): record['receipt'] = rewrite(receipt_path, receipt)
    updated = rewrite(Path(f['ordered_ref']['path']), ordered)
    top = gpu59.read(f['top_path']); top['completion'] = updated; rewrite(f['top_path'], top)


class UtilityInferenceReviewIntegration(unittest.TestCase):
    def execute(self, f):
        original_load = torch.load; loaded = []
        def load(path, *args, **kwargs):
            path = Path(path).resolve()
            if path == Path(f['old_raw']['path']).resolve():
                raise AssertionError('External first-QAd raw must never be tensor-loaded again')
            loaded.append(path)
            return original_load(path, *args, **kwargs)
        frozen = SimpleNamespace(validate_inventory=lambda *args:None,
            validate_value=review56.validate_value, validate_raw=review56.validate_raw)
        modules = {str(Path(review56.__file__).resolve()):frozen, str(Path(gpu59.__file__).resolve()):gpu59,
            str(Path(math60.__file__).resolve()):math60, str(Path(policy33.__file__).resolve()):policy33}
        with mock.patch.dict(os.environ, {'CUDA_VISIBLE_DEVICES':''}), \
             mock.patch.object(review60, 'bound', side_effect=bounded), mock.patch.object(gpu59, 'bound', side_effect=bounded), \
             mock.patch.object(review60, 'module', side_effect=lambda r,n:modules[str(Path(r['path']).resolve())]), \
             mock.patch.object(torch, 'load', side_effect=load):
            review60.run(f['root'], 'production', f['registration_path'])
        return loaded

    def test_real_loop_dot_external_adoption_internal_after_external_and_native_policy(self):
        with tempfile.TemporaryDirectory() as temporary:
            f = fixture(Path(temporary)); loaded = self.execute(f)
            out = f['root']/'utility_review_60/production'
            accepted = gpu59.read(out/'output_acceptance.json')
            self.assertEqual(accepted['status'], gpu59.OUTPUT_QA_GATE)
            self.assertEqual((accepted['actual_new_forwards'], accepted['external_adopted'], accepted['internal_aliases']), (2, 1, 2))
            self.assertEqual(len(loaded), 3)  # value weights + two actual new raw tensors.
            values = {p['id']:p['CPU_value'] for p in accepted['predictions']}
            self.assertEqual(values, dict(f1=2., r1=0., own=0., f2=4., r2=2.))
            output = gpu59.read(out/'policy.json')
            self.assertEqual(output['predictions'][0]['choices']['UTILITY'], 1)
            self.assertEqual(output['proof']['selfzero'], 1)
            self.assertFalse(output['GT_read'])

    def test_wrong_head_alias_flags_missing_raw_or_persist_fail_without_empty_output(self):
        for mode in ('head', 'alias', 'missing_raw', 'missing_persist'):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temporary:
                f = fixture(Path(temporary)); corrupt(f, mode)
                with self.assertRaises(ValueError): self.execute(f)
                out = f['root']/'utility_review_60/production'
                self.assertTrue((out/'failure.json').is_file())
                self.assertFalse((out/'output_acceptance.json').exists())
                self.assertFalse((out/'policy.json').exists())


if __name__ == '__main__':
    unittest.main()
