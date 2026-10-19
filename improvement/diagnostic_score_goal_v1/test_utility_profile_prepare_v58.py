import copy
import hashlib
from types import SimpleNamespace
import unittest

import numpy as np
import torch

import crop_geometry_v31 as geometry
import crop_image_input_v31 as image31
import crop_observation_v34 as recovery
import utility_profile_prepare_v58 as profile


def ref(name):
    return dict(path='/frozen/'+name, sha256=hashlib.sha256(name.encode()).hexdigest())


def quality():
    return dict(status='PASS_UTILITY_SCREEN20_ONLY', primary='UTILITY', confirm_admitted=True, fixed_final_checkpoint=True,
        evaluation=dict(quality=dict(admitted=True)), adapter_weights=ref('adapter'), value_weights=ref('value'),
        original_CROP_CE_and_old47_52_remain_STOP=True)


def inventory():
    sources, cases, pairs, entries = [], [], [], []
    for i in range(20):
        sid = 'validation%d'%i; base = [0, 33, 500] if i < 10 else geometry.candidate_pool(500, 333)[0]
        pool = geometry.candidate_pool(500, 333, base)
        sources.append(dict(source_id=sid, source_sha256=ref(sid)['sha256'], role='screen', width=500, height=333,
            pool=pool, baseline_box=base, original_BASE_observed=True, source_vision=ref(sid+'.pt'), original_proof=ref(sid+'.proof')))
        def add(a, b):
            cid = '%s_%d_%d'%(sid, a, b); cases.append(dict(id=cid, source_id=sid, a=a, b=b))
            entries.append(dict(id=cid, source_id=sid, input=ref(cid+'.json'))); return cid
        for j in range(1, len(pool)):
            f, r = add(0, j), add(j, 0)
            pairs.append(dict(source_id=sid, candidate_index=j, first_id=f, reverse_id=r, same_crop=False))
        own = add(0, 0); pairs.append(dict(source_id=sid, candidate_index=0, first_id=own, reverse_id=own, same_crop=True))
    reg = dict(schema=profile.SCHEMA, scope='resized20', expected_source_ids=[s['source_id'] for s in sources],
        CPU_targets=ref('targets'), adapter_weights=ref('adapter'), value_weights=ref('value'), profile_acceptanceRef=None)
    plan = dict(cases=cases, pair_index=pairs, GT_used_for_input_or_pair_choice=False)
    return reg, dict(sources=sources), plan, dict(screen_inputs=entries)


class FakeProcessor:
    def __init__(self): self.calls = 0
    def image_processor(self, *, images, return_tensors):
        self.calls += 1
        rgb = np.array(images[0].resize((64, 32)), dtype=np.uint8)
        pixels, grid = recovery.forward_pack_observation_rgb(rgb)
        return dict(pixel_values=pixels, image_grid_thw=grid)


def fake_image():
    def text(processor, grid):
        return dict(input_ids=torch.tensor([[10, 11, 12]]), attention_mask=torch.ones((1, 3), dtype=torch.int64)), \
            dict(question=image31.QUESTION, class_token_ids=[15, 16, 17])
    return SimpleNamespace(QUESTION=image31.QUESTION, pack_image_pixels=image31.pack_image_pixels,
        independent_pixel_check=image31.independent_pixel_check, build_text_input=text,
        independent_text_check=lambda p, packed, tokens, meta:dict(status='SYNTHETIC_TEXT_CHECK'),
        render_crop=image31.render_crop, independent_render_check=image31.independent_render_check)


def synthetic_source():
    rng = np.random.default_rng(58); rgb = rng.integers(0, 256, (64, 64, 3), dtype=np.uint8)
    pixels, grid = recovery.forward_pack_observation_rgb(rgb)
    source = dict(source_id='s', source_sha256=ref('s')['sha256'], role='screen', scope='resized20',
        width=64, height=64, pool=[[0, 0, 64], [16, 16, 32]], baseline_box=[0, 0, 64],
        source_vision=ref('source.pt'), original_proof=ref('source.proof'), profile=profile.PROFILE)
    cases = [dict(id='c%d'%i, native_case_id='n%d'%i, source_id='s', a=a, b=b) for i, (a, b) in enumerate([(0, 1), (1, 0), (0, 0)])]
    return source, cases, dict(pixel_values=pixels, image_grid_thw=grid), rgb


class ProfileTests(unittest.TestCase):
    def test_exact20_pool_order_self_pair_and_no_old33_gate(self):
        reg, catalog, cases, native = inventory(); old = copy.deepcopy(catalog)
        plan = profile.build_plan(reg, catalog, cases, native, quality())
        self.assertEqual((len(plan['sources']), len(plan['cases']), len(plan['pair_index'])), (20, 240, 130))
        self.assertEqual([s['pool'] for s in plan['sources']], [s['pool'] for s in old['sources']])
        self.assertEqual(catalog, old); self.assertFalse(plan['native_RGB_recovered'])
        with self.assertRaises(ValueError): profile.build_plan(reg, catalog, cases, native, dict(quality(), status='STOP_UTILITY_SCREEN20_REJECTED'))
        bad = copy.deepcopy(reg); bad['expected_source_ids'].reverse()
        with self.assertRaises(ValueError): profile.build_plan(bad, catalog, cases, native, quality())
        bad = copy.deepcopy(cases); bad['cases'].pop()
        with self.assertRaises(ValueError): profile.build_plan(reg, catalog, bad, native, quality())

    def test_remaining19_requires_new_profile_quality_and_excludes_lost_source(self):
        reg, _, _, _ = inventory(); reg.update(scope='resized19', profile_acceptanceRef=ref('resized20quality'))
        q = dict(status='PASS_UTILITY_RESIZED20_PROFILE_ONLY', primary='UTILITY', confirm_admitted=True,
            fixed_final_checkpoint=True, quality=dict(admitted=True), adapter_weights=ref('adapter'), value_weights=ref('value'))
        profile.validate_quality(reg, quality(), q)
        for wrong in (None, dict(q, status='PASS_NATIVE_CROP_SCREEN_ONLY'), dict(q, value_weights=ref('other'))):
            with self.assertRaises(ValueError): profile.validate_quality(reg, quality(), wrong)
        reg, cat, cases, native = inventory(); cat['sources'][0]['source_id'] = profile.EXCLUDED; reg['expected_source_ids'][0] = profile.EXCLUDED
        with self.assertRaises(ValueError): profile.build_plan(reg, cat, cases, native, quality())

    def test_affine_reference_preserved_and_nonuniform_height_not_redefined(self):
        reg, cat, cases, native = inventory(); plan = profile.build_plan(reg, cat, cases, native, quality())
        labels = dict(sources=[dict(source_id=s['source_id'], source_sha256=s['source_sha256'], role=s['role'],
            original_reference_xywh=[10., 20., 100., 56.25], candidate_ious=[.5]*len(s['pool']), baseline_index=0,
            reference_modified=False) for s in plan['sources']]); original = copy.deepcopy(labels)
        result = profile.cpu_targets(plan, labels, {s['source_id']:[256, 256] for s in plan['sources']})
        self.assertEqual(labels, original)
        row = result['sources'][0]
        from fractions import Fraction
        xywh = list(map(Fraction, row['observation_reference_xywh_exact']))
        self.assertNotEqual(xywh[3], xywh[2]*9/16)
        self.assertEqual(row['original_reference_xywh'], labels['sources'][0]['original_reference_xywh'])
        self.assertEqual(row['candidate_ious'], labels['sources'][0]['candidate_ious'])
        self.assertTrue(row['candidate_ious_adopted_without_recompute'])

    def test_first_source_recovery_render_compress_qa_without_source_processor(self):
        source, cases, vision, rgb = synthetic_source(); processor = FakeProcessor()
        actual = profile.prepare_source(source, cases, vision, processor, fake_image(), recovery)
        self.assertEqual(processor.calls, 4)  #2new unique crops plus their first independent replay.
        self.assertEqual(len(actual['cases']), 3); self.assertEqual(actual['observation_dimensions'], [64, 64])
        np.testing.assert_array_equal(actual['plane']['rgb'], rgb)
        for output in actual['cases']:
            self.assertFalse(output['request']['reference_or_target_in_prompt'])
            self.assertFalse(any(k in output['request'] for k in ('candidate_ious', 'target', 'original_reference_xywh')))
        for crop in actual['crops'].values():
            self.assertEqual(crop['codec']['codec'], profile.CODEC)
            self.assertTrue(crop['codec']['first_lossless_roundtrip_bitidentical'])
            self.assertGreater(crop['codec']['compressed_bytes'], 0)

    def test_cached_plane_requires_same_tensor_grid_formula_normalization(self):
        source, _, vision, rgb = synthetic_source(); recovered, proof = recovery.recover_observation_rgb(vision['pixel_values'], vision['image_grid_thw'])
        check = recovery.independent_recovery_check(vision['pixel_values'], vision['image_grid_thw'], recovered, proof)
        r = dict(status='PASS_RESIZED_OBSERVATION_LAYOUT_ONLY', entry=dict(source_id='s', source_sha256=source['source_sha256'],
            layout=dict(tensor_ref=source['source_vision'], row_start=0, row_end_exclusive=16, grid_thw=[1, 4, 4], normalization='FLOAT32(u-127.5)/127.5')),
            formula_code=ref('recovery34.py'), native_dimensions=[64, 64], native_RGB_recovered=False,
            recovery=proof, independent_recovery=check, resized_RGB=ref('plane.npy'))
        adopted = profile.cached_recovery(source, vision, [r], lambda x:rgb, ref('recovery34.py'))
        self.assertEqual(adopted['adopted'], ref('plane.npy'))
        for field, value in [('row_end_exclusive', 15), ('grid_thw', [1, 2, 8]), ('normalization', 'different')]:
            wrong = copy.deepcopy(r); wrong['entry']['layout'][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError): profile.cached_recovery(source, vision, [wrong], lambda x:rgb, ref('recovery34.py'))

    def test_compressed_reader_exact_whitelist_and_no_GT_callback(self):
        source, cases, vision, _ = synthetic_source(); image = fake_image()
        actual = profile.prepare_source(source, cases[:1], vision, FakeProcessor(), image, recovery); output = actual['cases'][0]
        q = output['request']; q.update(vision_inputs=[source['source_vision'], ref('a.pt.gz'), ref('b.pt.gz')], tokens=ref('tokens.pt'),
            vision_codecs=[dict(codec='TORCH_RAW', decoded_signature=profile.signature(vision)), actual['crops'][0]['codec'], actual['crops'][1]['codec']],
            adapter_weights=ref('adapter'), value_weights=ref('value'))
        entry = {k:q[k] for k in ('id', 'source_id', 'source_sha256', 'role')}; entry['input'] = ref('request.json')
        prepared = dict(schema='UTILITY_PROFILE_PREPARED_V58', scope='resized20', profile=profile.PROFILE,
            inference_inputs=[entry], execution_entries=[entry], adopted_success={}, class_token_ids=[15, 16, 17],
            adapter_weights=ref('adapter'), value_weights=ref('value'), CPU_targets=ref('NEVER_OPEN_GT'))
        data = {source['source_vision']['path']:vision, ref('tokens.pt')['path']:output['tokens']}
        blobs = {ref('a.pt.gz')['path']:actual['crops'][0]['compressed'], ref('b.pt.gz')['path']:actual['crops'][1]['compressed']}
        gate = dict(status=profile.GATE, prepared=ref('prepared'), registration=ref('reg'))
        reader = profile.ProfileInputs(prepared, gate=gate, prepared_ref=ref('prepared'), registration_ref=ref('reg'),
            load_json=lambda r:q, load_tensor=lambda r:data[r['path']], load_bytes=lambda r:blobs[r['path']], image=image)
        values, _ = reader.get(entry['input']); self.assertEqual(profile.signature(values), q['input_signature'])
        with self.assertRaises(ValueError): reader.get(ref('NEVER_OPEN_GT'))
        blobs[ref('a.pt.gz')['path']] = b'invalid'; reader.cache.clear()
        with self.assertRaises(Exception): reader.get(entry['input'])

    def test_exact_signature_owner_weights_alias_partition_never_calls_model(self):
        q = dict(id='new', source_id='s', source_sha256=ref('s')['sha256'], role='screen', input=ref('newinput'),
            class_token_ids=[15, 16, 17], input_signature=dict(dummy='fixed'))
        success = dict(source_id='s', source_sha256=q['source_sha256'], class_token_ids=q['class_token_ids'],
            input_signature=q['input_signature'], input=ref('oldinput'), receipt=ref('receipt'), raw_hidden=ref('hidden'),
            acceptance=ref('QA'), model_role='UTILITY_TRAINED_screen', adapter_weights=ref('adapter'), value_weights=ref('value'),
            CPU_value=.2, GPU_value=.20000001, first_output_QA_passed=True)
        adopted = profile.partition([q], [success], ref('adapter'), ref('value'))
        self.assertEqual(adopted['execution_entries'], []); self.assertEqual(set(adopted['adopted_success']), {'new'})
        changed = dict(q, source_id='other'); self.assertEqual(len(profile.partition([changed], [success], ref('adapter'), ref('value'))['execution_entries']), 1)
        with self.assertRaises(ValueError): profile.partition([q], [dict(success, value_weights=ref('wrong'))], ref('adapter'), ref('value'))


if __name__ == '__main__': unittest.main()
