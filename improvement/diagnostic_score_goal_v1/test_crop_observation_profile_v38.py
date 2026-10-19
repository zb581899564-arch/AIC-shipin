"""Six synthetic/fake-processor checks. No files, real data, model or GPU."""
import copy
import unittest

import numpy as np
from PIL import Image
import torch

import crop_image_input_v31 as image
import crop_observation_v34 as recovery
import crop_observation_profile_v38 as profile
from test_crop_image_input_v31 import FakeProcessor


def reference(name):
    import hashlib
    return dict(path='/synthetic/'+name, sha256=hashlib.sha256(name.encode()).hexdigest())


WEIGHTS = reference('final500_weights')


def native_results():
    screen = dict(status='PASS_NATIVE_CROP_SCREEN_ONLY', confirm_admitted=True, primary='TRAINED',
                  fixed_final_checkpoint=True, adapter_weights=WEIGHTS)
    confirm = dict(status='PASS_NATIVE_CROP_CONFIRM19_RESEARCH_ONLY', native_research_qualified=True,
        primary='TRAINED', adapter_weights=WEIGHTS, original20_complete=False, excluded_missing_source_repeated=False)
    return screen, confirm


def cohort(role, count):
    sources, cases, entries, pairs = [], [], [], []
    for i in range(count):
        sid = role+str(i); pool = [[0, 0, 160], [16, 9, 128]]
        source = dict(source_id=sid, source_sha256=reference(sid)['sha256'], role=role, width=160, height=90,
            pool=pool, baseline_box=pool[0], source_vision=reference(sid+'_source'), original_proof=reference(sid+'_proof'))
        sources.append(source)
        ids = []
        for a, b in ((0, 1), (1, 0), (0, 0)):
            cid = sid+'_'+str(a)+str(b); ids.append(cid)
            cases.append(dict(id=cid, source_id=sid, a=a, b=b))
            entries.append(dict(id=cid, source_id=sid, input=reference(cid+'_native_request')))
        pairs.extend([dict(source_id=sid, candidate_index=1, first_id=ids[0], reverse_id=ids[1], same_crop=False),
            dict(source_id=sid, candidate_index=0, first_id=ids[2], reverse_id=ids[2], same_crop=True)])
    prepared = dict(class_token_ids=[71, 72, 73], CPU_targets=reference(role+'_targets'),
                    **{('screen_inputs' if role == 'screen' else 'confirm_inputs'):entries})
    return dict(sources=sources), prepared, dict(cases=cases, pair_index=pairs, GT_used_for_input_or_pair_choice=False)


class NewCropEncoder:
    merge_size = 2
    model_input_names = ['pixel_values', 'image_grid_thw']

    def __init__(self, size):
        self.size, self.calls = size, 0

    def __call__(self, images, **kwargs):
        self.calls += 1
        rgb = np.array(images[0].resize(self.size, Image.Resampling.BICUBIC), dtype=np.uint8)
        pixels, grid = recovery.forward_pack_observation_rgb(rgb)
        return dict(pixel_values=pixels, image_grid_thw=grid)


def source_inputs(new_size=(64, 32)):
    source = cohort('screen', 1)[0]['sources'][0]
    y, x = np.indices((32, 64)); rgb = np.stack((x, y, (x+3*y)%256), axis=-1).astype(np.uint8)
    pixels, grid = recovery.forward_pack_observation_rgb(rgb)
    vision = dict(pixel_values=pixels, image_grid_thw=grid)
    processor = FakeProcessor(); encoder = NewCropEncoder(new_size); processor.image_processor = encoder
    native_grid = torch.cat((grid, grid, grid)); packed = image.pack_image_pixels([pixels]*3, native_grid)
    tokens, text = image.build_text_input(processor, native_grid)
    native, cases = {}, []
    for i, (a, b) in enumerate(((0, 1), (1, 0), (0, 0))):
        old = 'native%d'%i
        request = dict(id=old, source_id=source['source_id'], source_sha256=source['source_sha256'], role='screen',
            candidate_indices=[a, b], boxes=[source['pool'][a], source['pool'][b]],
            vision_inputs=[source['source_vision'], reference('oldcropA'), reference('oldcropB')],
            reference_or_target_in_prompt=False, tokens=reference(old+'_tokens'),
            input_signature=profile.signature(dict(**tokens, **packed)), image_grid_thw=native_grid.tolist(),
            class_token_ids=[71, 72, 73], text_evidence=text)
        native[old] = dict(request=request, tokens=tokens)
        cases.append(dict(id='profile%d'%i, native_case_id=old, native_input=reference(old+'_request'),
                          source_id=source['source_id'], role='screen', a=a, b=b))
    return source, vision, cases, native, processor, encoder


def prepare_fixture(new_size=(64, 32)):
    source, vision, cases, native, processor, encoder = source_inputs(new_size)
    screen, confirm = native_results()
    result = profile.prepare_source_profile(source, vision, cases, native, processor, recovery=recovery, image=image,
        screen_result=screen, confirm_result=confirm, adapter_weights=WEIGHTS)
    return source, vision, native, result, encoder


def success(request, name='native'):
    return dict(source_id=request['source_id'], source_sha256=request['source_sha256'], model_role='TRAINED_'+request['role'],
        first_output_QA_passed=True, class_token_ids=request['class_token_ids'], input_signature=request['input_signature'],
        native_request=reference(name+'_request'), receipt=reference(name+'_receipt'), probabilities3=[.1, .7, .2], adapter_weights=WEIGHTS)


class ObservationProfileTests(unittest.TestCase):
    def test_native_both_pass_and_exact_weights_required_before_any_new_encoding(self):
        screen, confirm = native_results()
        self.assertFalse(profile.validate_native_admission(screen, confirm, WEIGHTS)['production_admitted'])
        for which in ('screen', 'confirm', 'weights'):
            a, b = copy.deepcopy(screen), copy.deepcopy(confirm)
            if which == 'screen': a['status'] = 'STOP_NATIVE_CROP_SCREEN'
            elif which == 'confirm': b['status'] = 'STOP_NATIVE_CROP_CONFIRM19'
            else: b['adapter_weights'] = reference('different_checkpoint')
            with self.assertRaises(ValueError): profile.validate_native_admission(a, b, WEIGHTS)
        source, vision, cases, native, processor, encoder = source_inputs()
        screen['status'] = 'STOP_NATIVE_CROP_SCREEN'
        with self.assertRaises(ValueError):
            profile.prepare_source_profile(source, vision, cases, native, processor, recovery=recovery, image=image,
                screen_result=screen, confirm_result=confirm, adapter_weights=WEIGHTS)
        self.assertEqual(encoder.calls, 0)

    def test_plan_same39_pool_order_pair_order_and_cpu_target_refs_only(self):
        sc, sp, sl = cohort('screen', 20); cc, cp, cl = cohort('confirm', 19); a, b = native_results()
        original = copy.deepcopy((sc, sp, sl, cc, cp, cl))
        result = profile.build_profile_plan(sc, sp, sl, cc, cp, cl, screen_targets_ref=sp['CPU_targets'],
            confirm_targets_ref=cp['CPU_targets'], adapter_weights=WEIGHTS, screen_result=a, confirm_result=b)
        self.assertEqual(len(result['sources']), 39); self.assertEqual(len(result['cases']), 117)
        self.assertEqual(result['CPU_targets'], dict(screen=sp['CPU_targets'], confirm=cp['CPU_targets']))
        self.assertEqual([c['native_case_id'] for c in result['cases']], [c['id'] for c in sl['cases']+cl['cases']])
        self.assertEqual(result['sources'][0]['pool'], sc['sources'][0]['pool'])
        self.assertEqual(result['pair_index'][1]['first_id'], result['pair_index'][1]['reverse_id'])
        self.assertEqual((sc, sp, sl, cc, cp, cl), original)
        cp['CPU_targets'] = reference('wrong_targets')
        with self.assertRaises(ValueError):
            profile.build_profile_plan(sc, sp, sl, cc, cp, cl, screen_targets_ref=sp['CPU_targets'],
                confirm_targets_ref=reference('confirm_targets'), adapter_weights=WEIGHTS, screen_result=a, confirm_result=b)

    def test_exact_alias_partition_source_class_full_signature_weights_and_conflict(self):
        _, _, _, result, _ = prepare_fixture()
        request = copy.deepcopy(result['cases'][0]['request']); request['input'] = reference('profile_request')
        accepted = success(request)
        adopted = profile.find_native_alias(request, [accepted], WEIGHTS)
        self.assertEqual(set(adopted), {'native_request', 'receipt', 'probabilities3', 'adapter_weights'})
        changed = copy.deepcopy(request); changed['id'] = 'different'; changed['input'] = reference('different')
        changed['input_signature']['pixel_values']['sha256'] = 'f'*64
        divided = profile.partition_inputs([request, changed], [accepted], WEIGHTS)
        self.assertEqual(divided['actual_new_inputs'], 1); self.assertEqual(divided['adopted_native_successes'], 1)
        self.assertEqual(divided['execution_entries'][0]['id'], 'different')
        for field, value in (('source_sha256', 'f'*64), ('class_token_ids', [74, 75, 76])):
            wrong = copy.deepcopy(request); wrong[field] = value
            self.assertIsNone(profile.find_native_alias(wrong, [accepted], WEIGHTS))
        wrong = copy.deepcopy(accepted); wrong['adapter_weights'] = reference('wrong_weights')
        with self.assertRaises(ValueError): profile.find_native_alias(request, [wrong], WEIGHTS)
        wrong = copy.deepcopy(accepted); wrong['probabilities3'] = [.2, .6, .2]
        with self.assertRaises(ValueError): profile.find_native_alias(request, [accepted, wrong], WEIGHTS)

    def test_one_source_recovery_new_crops_only_and_adopt_exact_native_tokens(self):
        source, vision, native, result, encoder = prepare_fixture()
        self.assertFalse(result['native_RGB_recovered']); self.assertEqual(encoder.calls, 2*len(source['pool']))
        self.assertEqual(result['old_source_processor_repeated'], 0)
        self.assertEqual(result['observation_rgb'].shape, (32, 64, 3))
        self.assertTrue(result['recovery']['forward_roundtrip_bitidentical'])
        for output in result['cases']:
            self.assertTrue(output['request']['adopted_native_tokens'])
            self.assertEqual(set(output['values']), profile.FOUR_KEYS)
            self.assertTrue(torch.equal(output['values']['pixel_values'][:8], vision['pixel_values']))
            request = profile.materialize_request(output, {i:reference('new_observation_crop%d'%i) for i in result['crops']})
            self.assertEqual(request['vision_inputs'][0], source['source_vision'])
            self.assertEqual(request['tokens'], native[request['native_case_id']]['request']['tokens'])
            self.assertFalse(request['native_RGB_recovered'])
        with self.assertRaises(ValueError):
            profile.materialize_request(result['cases'][0], {0:reference('oldcropA'), 1:reference('oldcropB')})

    def test_changed_grid_requires_new_prefix_and_bad_source_normalization_never_falls_back(self):
        _, _, _, result, encoder = prepare_fixture((64, 64))
        self.assertEqual(encoder.calls, 4)
        self.assertTrue(all(not row['request']['adopted_native_tokens'] for row in result['cases']))
        output = result['cases'][0]
        with self.assertRaises(ValueError): profile.materialize_request(output, {0:reference('c0'), 1:reference('c1')})
        request = profile.materialize_request(output, {0:reference('c0'), 1:reference('c1')}, reference('new_prefix'))
        self.assertEqual(request['tokens'], reference('new_prefix'))
        source, vision, cases, native, processor, encoder = source_inputs()
        vision['pixel_values'] = torch.full_like(vision['pixel_values'], 1.01)
        a, b = native_results()
        with self.assertRaises(ValueError):
            profile.prepare_source_profile(source, vision, cases, native, processor, recovery=recovery, image=image,
                screen_result=a, confirm_result=b, adapter_weights=WEIGHTS)
        self.assertEqual(encoder.calls, 0)

    def test_execution_reader_fourkeys_no_target_reads_and_alias_ref_forbidden(self):
        source, vision, native, result, _ = prepare_fixture()
        crop_refs = {i:reference('newcrop%d'%i) for i in result['crops']}
        output = result['cases'][0]; request = profile.materialize_request(output, crop_refs)
        request_ref = reference('request'); reads = []
        objects = {source['source_vision']['path']:vision, request['tokens']['path']:output['tokens']}
        objects.update({crop_refs[i]['path']:crop['vision'] for i, crop in result['crops'].items()})
        def load_json(ref):
            reads.append(ref['path']); self.assertEqual(ref, request_ref); return request
        def load_tensor(ref):
            reads.append(ref['path']); return objects[ref['path']]
        prepared = dict(profile=profile.PROFILE, class_token_ids=[71, 72, 73], adapter_weights=WEIGHTS,
            execution_entries=[dict(id=request['id'], source_id=request['source_id'], role='screen', input=request_ref)],
            CPU_targets=dict(screen=reference('DO_NOT_READ_TARGETS'), confirm=reference('DO_NOT_READ_TARGETS2')))
        reader = profile.ProfileInputs(prepared, load_json=load_json, load_tensor=load_tensor, image=image)
        values, actual = reader.get(request_ref)
        self.assertEqual(set(values), profile.FOUR_KEYS); self.assertEqual(actual['id'], request['id'])
        self.assertFalse(any('TARGET' in path for path in reads))
        with self.assertRaises(ValueError): reader.get(reference('adopted_native_request'))
        request['input_signature']['pixel_values']['sha256'] = 'f'*64
        with self.assertRaises(ValueError): reader.get(request_ref)


if __name__ == '__main__':
    unittest.main()
