"""Synthetic-only44 plans/patch swaps/reader tests; no real data or processor."""
import copy
import unittest

import torch

import crop_gain_prepare_v44 as gain
import crop_image_input_v31 as image
from test_crop_image_input_v31 import FakeProcessor, image_pixels


def reference(name):
    import hashlib
    return dict(path='/synthetic/'+name, sha256=hashlib.sha256(name.encode()).hexdigest())


def old_fixture():
    sources, requests, schedule, cases, micro = [], [], [], {}, []
    chosen = {}
    for i in range(602):
        sid = 's%03d'%i
        sources.append(dict(source_id=sid, source_sha256=reference(sid)['sha256'], role='train', width=32, height=18,
            pool=[[0, 0, 16], [8, 0, 16], [0, 0, 8]], source_vision=reference(sid+'_source'), original_proof=reference(sid+'_proof')))
        chosen[sid] = [[0, 1], [1, 2]]
    by_id = {source['source_id']:source for source in sources}
    for cycle in range(4):
        ordered = sorted(sources, key=lambda s:gain._key(s['source_sha256'], cycle, 'CROP31_SOURCE_ORDER'))
        for source in ordered:
            if len(schedule) == 2000:
                break
            sid = source['source_id']; a, b = chosen[sid][cycle//2]
            if cycle % 2:
                a, b = b, a
            cid = gain._key(source['source_sha256'], a, b, 'CROP31_TRIPLET')
            case = dict(id=cid, source_id=sid, a=a, b=b); cases[cid] = case
            request = dict(id=cid, source_id=sid, source_sha256=source['source_sha256'], role='train',
                candidate_indices=[a, b], boxes=[source['pool'][a], source['pool'][b]],
                vision_inputs=[source['source_vision'], reference(sid+'_crop'+str(a)), reference(sid+'_crop'+str(b))],
                class_token_ids=[71, 72, 73], reference_or_target_in_prompt=False)
            request_ref = reference(cid+'_request')
            requests.append(dict(reference=request_ref, request=request))
            iid = 'T%04d'%len(schedule)
            schedule.append(dict(id=iid, source_id=sid, input=request_ref, target='DO_NOT_USE_OLD_TARGET'))
            micro.append(dict(id=iid, source_id=sid, case_id=cid))
        if len(schedule) == 2000:
            break
    return dict(sources=sources), dict(class_token_ids=[71, 72, 73], train_schedule=schedule), \
        dict(chosen_train_pairs=chosen, cases=list(cases.values()), train_schedule=micro, GT_used_for_input_or_pair_choice=False), requests


def missing_fixture(different_grid=False):
    processor = FakeProcessor()
    grids = [[1, 2, 4], [1, 2, 2], [1, 2, 4] if different_grid else [1, 2, 2]]
    pixels = [image_pixels(row[1], row[2], i*100000) for i, row in enumerate(grids)]
    grid = torch.tensor(grids, dtype=torch.int64)
    packed = image.pack_image_pixels(pixels, grid)
    tokens, text = image.build_text_input(processor, grid)
    values = dict(**tokens, **packed)
    boxes = [[0, 0, 16], [8, 0, 16]]
    old = dict(id='forward', source_id='source', source_sha256=reference('source')['sha256'], role='train',
        candidate_indices=[0, 1], boxes=boxes, vision_inputs=[reference('source_pixels'), reference('cropA'), reference('cropB')],
        tokens=reference('old_tokens'), input_signature=gain.signature(values), image_grid_thw=grids,
        class_token_ids=[71, 72, 73], text_evidence=text, reference_or_target_in_prompt=False)
    case = dict(id='reverse', source_id='source', source_sha256=old['source_sha256'], role='train', a=1, b=0,
        boxes=list(reversed(boxes)), adopted_input=False, input=None,
        template_input=reference('forward_request'), template_case_id='forward')
    return case, old, values, processor, pixels


class GainPrepareTests(unittest.TestCase):
    def test_exact2408_adopt2000_new408_and_sha32_partition_without_targets(self):
        catalog, prepared, old_plan, requests = old_fixture()
        class ForbiddenTarget:
            def __deepcopy__(self, memo):
                raise AssertionError('Old target must never be copied')
        prepared['train_schedule'][0]['target'] = ForbiddenTarget()
        result = gain.build_gain_plan(catalog, prepared, old_plan, requests)
        self.assertEqual(len(result['cases']), 2408); self.assertEqual(len(result['pair_index']), 1204)
        self.assertEqual(sum(c['adopted_input'] for c in result['cases']), 2000)
        self.assertEqual(len(result['pilot_case_ids']), 128); self.assertEqual(len(result['remaining_case_ids']), 2280)
        expected = [s['source_id'] for s in sorted(catalog['sources'], key=lambda s:(s['source_sha256'], s['source_id']))[:32]]
        self.assertEqual(result['pilot_source_ids'], expected)
        self.assertFalse(set(result['pilot_case_ids']) & set(result['remaining_case_ids']))
        for pair in result['pair_index']:
            cases = {c['id']:c for c in result['cases'] if c['source_id'] == pair['source_id']}
            self.assertEqual([cases[pair['first_id']]['a'], cases[pair['first_id']]['b']], [pair['a'], pair['b']])
            self.assertEqual([cases[pair['reverse_id']]['a'], cases[pair['reverse_id']]['b']], [pair['b'], pair['a']])
        self.assertNotIn('target', result['cases'][0])

    def test_wrong_old_mapping_duplicate_source_and_noncanonical_pairs_fail(self):
        catalog, prepared, plan, requests = old_fixture()
        wrong = copy.deepcopy(requests); wrong[0]['request']['candidate_indices'].reverse()
        with self.assertRaises(ValueError): gain.build_gain_plan(catalog, prepared, plan, wrong)
        wrong = copy.deepcopy(catalog); wrong['sources'][1]['source_sha256'] = wrong['sources'][0]['source_sha256']
        with self.assertRaises(ValueError): gain.build_gain_plan(wrong, prepared, plan, requests)
        wrong = copy.deepcopy(plan); sid = catalog['sources'][0]['source_id']; wrong['chosen_train_pairs'][sid] = [[1, 0], [1, 2]]
        with self.assertRaises(ValueError): gain.build_gain_plan(catalog, prepared, wrong, requests)

    def test_missing_reverse_exact_blocks_refs_and_adopted_same_grid_tokens(self):
        case, old, values, processor, pixels = missing_fixture()
        actual, request, evidence = gain.build_missing_input(case, old, values, processor, image)
        self.assertTrue(torch.equal(actual['pixel_values'], torch.cat([pixels[0], pixels[2], pixels[1]])))
        self.assertEqual(request['vision_inputs'], [old['vision_inputs'][0], old['vision_inputs'][2], old['vision_inputs'][1]])
        self.assertEqual(request['tokens'], old['tokens']); self.assertEqual(request['candidate_indices'], [1, 0])
        self.assertEqual(evidence['new_image_processor_calls'], 0)
        self.assertEqual(gain.materialize_missing_input(request)['tokens'], old['tokens'])
        with self.assertRaises(ValueError): gain.materialize_missing_input(request, reference('unnecessary_new_tokens'))
        corrupted = dict(values); corrupted['pixel_values'] = values['pixel_values'].clone(); corrupted['pixel_values'][0, 0] += 1
        with self.assertRaises(ValueError): gain.build_missing_input(case, old, corrupted, processor, image)

    def test_different_crop_grid_only_rebuilds_text_never_encodes_pixels(self):
        case, old, values, processor, pixels = missing_fixture(True)
        actual, request, evidence = gain.build_missing_input(case, old, values, processor, image)
        self.assertIsNone(request['tokens']); self.assertFalse(request['adopted_native_tokens'])
        self.assertEqual(actual['image_grid_thw'].tolist(), [old['image_grid_thw'][i] for i in (0, 2, 1)])
        with self.assertRaises(ValueError): gain.materialize_missing_input(request)
        result = gain.materialize_missing_input(request, reference('first_new_prefix'))
        self.assertEqual(result['tokens'], reference('first_new_prefix'))
        self.assertEqual(evidence['new_original_decodes'], 0)

    def test_prepared_gate_whitelist_fourkeys_and_no_cpu_target_reads(self):
        catalog, prepared, old_plan, requests = old_fixture(); plan = gain.build_gain_plan(catalog, prepared, old_plan, requests)
        new_refs = {c['id']:reference(c['id']+'_first_new') for c in plan['cases'] if not c['adopted_input']}
        bindings = {key:reference(key) for key in ('old_prepared', 'old_catalog', 'old_case_plan', 'old_input_gate', 'source_catalog')}
        result = gain.finalize_prepared(plan, new_refs, CPU_targets_ref=reference('DO_NOT_READ_TARGETS'),
            adapter_weights=reference('final500'), bindings=bindings)
        self.assertFalse(result['GPU_admitted']); self.assertEqual(result['old_native_quality'], 'STOP')
        entry = next(e for e in result['train_inputs'] if e['id'] in {c['id'] for c in plan['cases'] if c['adopted_input']})
        _, old, values, _, pixels = missing_fixture()
        original = next(r['request'] for r in requests if r['request']['id'] == entry['id'])
        request = copy.deepcopy(old)
        for key in ('id', 'source_id', 'source_sha256', 'candidate_indices', 'boxes', 'vision_inputs'):
            request[key] = copy.deepcopy(original[key])
        objects = {request['tokens']['path']:{key:values[key] for key in ('input_ids', 'attention_mask')}}
        for ref, pixel, row in zip(request['vision_inputs'], pixels, old['image_grid_thw']):
            objects[ref['path']] = dict(pixel_values=pixel, image_grid_thw=torch.tensor([row], dtype=torch.int64))
        reads = []
        def load_json(ref):
            reads.append(ref['path']); self.assertEqual(ref, entry['input']); return request
        def load_tensor(ref):
            reads.append(ref['path']); return objects[ref['path']]
        prepared_ref, reg_ref = reference('new_prepared'), reference('reg44')
        gate = dict(status=gain.GATE, prepared=prepared_ref, registration=reg_ref, adopted_inputs=2000,
                    first_new_combinations=408, new_image_processor_calls=0, new_original_decodes=0)
        reader = gain.GainInputs(result, gate=gate, prepared_ref=prepared_ref, registration_ref=reg_ref,
            load_json=load_json, load_tensor=load_tensor, image=image)
        actual, returned = reader.get(entry['input'])
        self.assertEqual(set(actual), gain.FOUR_KEYS); self.assertEqual(returned['id'], entry['id'])
        self.assertFalse(any('TARGETS' in path for path in reads))
        with self.assertRaises(ValueError): reader.get(reference('unregistered_or_screen'))
        wrong = copy.deepcopy(result); wrong['remaining_inputs'][0] = wrong['pilot_inputs'][0]
        with self.assertRaises(ValueError):
            gain.GainInputs(wrong, gate=gate, prepared_ref=prepared_ref, registration_ref=reg_ref,
                load_json=load_json, load_tensor=load_tensor, image=image)

    def test_registration_preserves_stop_requires_actual_final500_and_old_gate(self):
        fields = ('preparation_code', 'input_code', 'image_code', 'geometry_code', 'helper_code', 'old_prepared',
            'old_catalog', 'old_case_plan', 'old_input_gate', 'CPU_targets', 'fixed_training_completion',
            'adapter_weights', 'old_STOP', 'gain_protocol')
        reg = {key:reference(key) for key in fields}
        reg.update(schema=gain.SCHEMA, purpose='FIXED_FINAL500_GAIN_CRITIC_INPUT_READOUT_ONLY',
                   deadline_utc='2026-10-18T03:22:24Z', new_image_processor_calls=0, new_original_decodes=0)
        training = dict(status='COMPLETE_FIXED_FINAL500_CROP_COMPARISON_NOT_QUALITY', completed_updates=500,
            successful_micro=2000, adapter_reload_all288_exact=True, adapter_weights=reg['adapter_weights'])
        stop = dict(status='STOP_NATIVE_CROP_SCREEN', adapter_weights=reg['adapter_weights'])
        old_gate = dict(status='PASS_ALL_CROP31_TRIPLET_FIRST_CPU_QA', prepared=reg['old_prepared'])
        result = gain.validate_cpu_registration(reg, training_completion=training, old_stop=stop, old_gate=old_gate)
        self.assertEqual(result['old_native_quality'], 'STOP'); self.assertFalse(result['GPU_admitted'])
        for field, value in (('completed_updates', 499), ('adapter_reload_all288_exact', False)):
            with self.assertRaises(ValueError):
                gain.validate_cpu_registration(reg, training_completion=dict(training, **{field:value}), old_stop=stop, old_gate=old_gate)
        with self.assertRaises(ValueError):
            gain.validate_cpu_registration(reg, training_completion=training, old_stop=dict(stop, status='PASS'), old_gate=old_gate)


if __name__ == '__main__':
    unittest.main()
