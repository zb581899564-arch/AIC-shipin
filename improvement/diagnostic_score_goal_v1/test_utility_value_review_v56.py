import copy
import hashlib
import json
import random
from pathlib import Path
import unittest
from unittest import mock

import numpy as np
import torch

import crop_policy_v33 as policy
import utility_value_review_v56 as qa


def ref(name):
    return dict(path='/synthetic/'+name, sha256=hashlib.sha256(name.encode()).hexdigest())


def value_state():
    w = torch.zeros((1, 4096)); w[0, 0] = 1.
    return dict(weight=w, geometry_beta=torch.zeros(11))


def progress():
    weights = {}
    for layer in range(36):
        for projection in ('q_proj', 'k_proj', 'v_proj', 'o_proj'):
            for kind, shape in (('A', (8, 4096)), ('B', ((4096 if projection in ('q_proj', 'o_proj') else 1024), 8))):
                name = f'base_model.model.model.language_model.layers.{layer}.self_attn.{projection}.lora_{kind}.weight'
                weights[name] = torch.zeros(shape)
    head, beta = torch.ones((1, 4096))*.001, torch.zeros(11)
    all_weights = list(weights.values())+[head, beta]
    moments = {i:dict(step=torch.tensor(4.), exp_avg=torch.zeros_like(v), exp_avg_sq=torch.zeros_like(v))
               for i, v in enumerate(all_weights)}
    names = [list(weights), ['head.weight'], ['geometry_beta']]
    nrng = np.random.RandomState(0).get_state()
    return dict(schema='UTILITY_R8_COMPLETE_UPDATE_PROGRESS_V55', step=4, micro=16, logical_training_forwards=32,
        schedule_sha256='schedule', train_schedule_reference=ref('prepared'), recipe=qa.RECIPE, train_target_RMS=.2,
        adapter_state_dict=weights, head_state_dict=dict(weight=head), geometry_beta=beta,
        optimizer_parameter_names_by_group=names,
        optimizer_parameter_names_sha256=hashlib.sha256(json.dumps(names, sort_keys=True, separators=(',', ':')).encode()).hexdigest(),
        optimizer_state_dict=dict(state=moments, param_groups=[dict(params=list(range(288)), lr=5e-5, weight_decay=0.),
            dict(params=[288], lr=.001, weight_decay=0.), dict(params=[289], lr=.001, weight_decay=0.)]),
        torch_rng_state=torch.Generator().get_state(), torch_cuda_rng_state_all=[torch.zeros(16, dtype=torch.uint8)],
        numpy_rng_state=dict(name=nrng[0], keys=torch.tensor(nrng[1].astype(np.int64)), position=nrng[2],
            has_gauss=nrng[3], cached_gaussian=nrng[4]), python_rng_state=random.Random(0).getstate(),
        original_TIME_loaded=False, old_PAIR_loaded=False, old_CROP_loaded=False, no_base_tensors_saved=True)


def gradients(first=1, last=4):
    result = []
    for step in range(first, last+1):
        groups = {name:dict(tensors=count, nonzero_tensors=count, finite=True, preclip_norm=.1)
                  for name, count in dict(LoRA_A=144, LoRA_B=144, VALUE_HEAD=1, GEOMETRY_BETA=1).items()}
        if step == 1:
            groups['LoRA_A'].update(nonzero_tensors=0, preclip_norm=0.)
        result.append(dict(step=step, micro=step*4, grad_groups=groups, combined_preclip_gradient_norm=.4,
                           progress=ref('p'+str(step))))
    return result


def evaluation_fixture():
    sources, pairs, lookup, targets = [], [], {}, {}
    for i in range(20):
        sid = 'source'+str(i); digest = f'{i:064x}'
        sources.append(dict(source_id=sid, source_sha256=digest, role='screen', width=20, height=20,
            pool=[[0, 0, 16], [2, 2, 8]]))
        own, first, reverse = sid+'self', sid+'f', sid+'r'
        for identifier, number in ((own, 0.), (first, 2.), (reverse, 0.)):
            h = np.zeros(4096); h[0] = number
            lookup[identifier] = dict(source_id=sid, source_sha256=digest, hidden4096=h)
        pairs.extend([dict(source_id=sid, candidate_index=0, first_id=own, reverse_id=own, same_crop=True),
                      dict(source_id=sid, candidate_index=1, first_id=first, reverse_id=reverse, same_crop=False)])
        targets[sid] = [.4, .8]
    old = dict(RMS=np.ones(14), GEOM11_beta=np.zeros(11))
    return sources, pairs, lookup, targets, value_state(), old, np.zeros(13), policy


class UtilityReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(2)

    def test_actual_raw_value_float64_replay_and_gpu_tolerance(self):
        raw = torch.arange(4096, dtype=torch.float32)/100
        state = value_state(); receipt = dict(head_value=0.000005)
        result = qa.validate_raw(raw, receipt, state)
        self.assertEqual(result['CPU_value'], 0.)
        np.testing.assert_array_equal(result['hidden4096'], raw.double().numpy())
        with self.assertRaises(ValueError): qa.validate_raw(raw, dict(head_value=.1), state)
        for bad in (raw.double(), raw.reshape(1, -1), raw*float('nan')):
            with self.assertRaises(ValueError): qa.validate_raw(bad, receipt, state)
        with self.assertRaises(ValueError): qa.validate_value(dict(state, bias=torch.zeros(1)))

    def test_alias_requires_exact_owner_role_signature_and_both_weights(self):
        receipt = dict(model_role=qa.ROLE, source_id='s', source_sha256='a'*64, class_token_ids=[15, 16, 17],
            input_signature={'same':'input'}, adapter_weights=ref('adapter'), value_weights=ref('value'),
            raw_hidden=ref('hidden'), actual_new_forward=True, alias_of=None)
        first, second = ref('firstreceipt'), ref('aliasreceipt')
        key = qa.validate_alias(receipt, first, {}, set())
        previous = {first['path']:dict(reference=first, receipt=receipt)}
        alias = dict(receipt, actual_new_forward=False, alias_of=first)
        self.assertEqual(qa.validate_alias(alias, second, previous, {key}), key)
        for change in (dict(source_id='other'), dict(model_role='old_CROP'), dict(value_weights=ref('wrongvalue')),
                       dict(raw_hidden=ref('wrongraw')), dict(class_token_ids=[0, 1, 2])):
            with self.assertRaises(ValueError): qa.validate_alias(dict(alias, **change), second, previous, {key})
        with self.assertRaises(ValueError): qa.validate_alias(receipt, second, previous, {key})

    def test_complete290_adam_rng_and_external_head_beta_required(self):
        state = progress()
        result = qa.validate_progress(state, 4, 'schedule', ref('prepared'), qa.RECIPE, .2)
        self.assertEqual(result['adam_states'], 290)
        self.assertEqual(result['logical_training_forwards'], 32)
        for change in ('stale', 'head', 'names', 'rng'):
            with self.subTest(change=change):
                bad = copy.deepcopy(state)
                if change == 'stale': bad['optimizer_state_dict']['state'][289]['step'] = torch.tensor(3.)
                if change == 'head': del bad['head_state_dict']['weight']
                if change == 'names': bad['optimizer_parameter_names_by_group'][0][0] = 'wrong_parameter'
                if change == 'rng': bad['torch_rng_state'] = torch.zeros(10)
                with self.assertRaises((ValueError, KeyError)):
                    qa.validate_progress(bad, 4, 'schedule', ref('prepared'), qa.RECIPE, .2)

    def test_gradient_groups_cannot_be_substituted_by_total_norm(self):
        rows = gradients()
        result = qa.validate_gradient_updates(rows, 1, 4, ref('p4'))
        self.assertTrue(result['initial_zero_LoRA_A_allowed'])
        bad = copy.deepcopy(rows); bad[1]['grad_groups']['LoRA_A'].update(nonzero_tensors=0, preclip_norm=0.)
        with self.assertRaises(ValueError): qa.validate_gradient_updates(bad, 1, 4, ref('p4'))
        bad = copy.deepcopy(rows); bad[2]['grad_groups']['VALUE_HEAD']['finite'] = False
        with self.assertRaises(ValueError): qa.validate_gradient_updates(bad, 1, 4, ref('p4'))
        later = gradients(5, 5); later[0]['grad_groups']['LoRA_A'].update(nonzero_tensors=0, preclip_norm=0.)
        qa.validate_gradient_updates(later, 5, 5, ref('p5'))  # No invented late convergence gate.
        immutable = dict(path='/synthetic/immutable_pilot.pt', sha256=ref('p4')['sha256'])
        qa.validate_gradient_updates(rows, 1, 4, immutable)

    def test_first240_hidden_receipt_alias_grid_and_raw_first_journal_contract(self):
        def r(path):
            return dict(path=str(path), sha256=hashlib.sha256(str(path).encode()).hexdigest())
        directory = Path('/synthetic/TRAINED_screen'); completion_ref = r(directory/'completion.json')
        attempts = r(directory/'attempts.jsonl'); registration = r('/synthetic/reg')
        adapter, value = r('/synthetic/adapter'), r('/synthetic/value')
        docs, raws, entries, expected, receipts, events = {}, {}, [], [], [], []
        grid = [[1, 2, 2]]*3
        grid_sha = hashlib.sha256(np.array(grid, np.int64).tobytes()).hexdigest()
        for i in range(240):
            cid = 'case'+str(i); owner = 'source'+str(i//12); digest = f'{i//12:064x}'
            inp, rec = r(directory/(cid+'.input')), r(directory/(cid+'.receipt'))
            sig = {k:dict(sha256='a'*64, shape=[1]) for k in qa.INPUT_KEYS}
            sig['input_ids']['sha256'] = f'{0 if i == 1 else i:064x}'
            sig['image_grid_thw'] = dict(sha256=grid_sha, shape=[3, 3], dtype='torch.int64')
            request = dict(id=cid, source_id=owner, source_sha256=digest, input_signature=sig,
                class_token_ids=[15, 16, 17], image_grid_thw=grid, reference_or_target_in_prompt=False)
            rawref = r(directory/('case0.hidden' if i == 1 else cid+'.hidden'))
            raw = torch.zeros(4096); raw[0] = 0 if i == 1 else i; raws[rawref['path']] = raw
            receipt = dict(request, input=inp, model_role=qa.ROLE, raw_hidden=rawref, head_value=float(raw[0]),
                raw_dtype='torch.float32', dimension=4096, adapter_weights=adapter, value_weights=value,
                actual_new_forward=i != 1, alias_of=r(directory/'case0.receipt') if i == 1 else None,
                screen_reference_read=False, no_full_vocabulary_logits=True,
                original_TIME_loaded=False, old_PAIR_loaded=False, old_CROP_loaded=False)
            docs[inp['path']], docs[rec['path']] = request, receipt
            entry = dict(id=cid, source_id=owner, source_sha256=digest, input=inp, receipt=rec)
            entries.append(entry); expected.append(dict(id=cid, source_id=owner, input=inp)); receipts.append(receipt)
            if i != 1:
                events.extend([dict(event='BEGIN_NEW_ROLE_FORWARD', id=cid, input=inp, model_role=qa.ROLE),
                    dict(event='FIRST_RAW_PERSISTED', id=cid, raw_hidden=rawref, model_role=qa.ROLE)])
            events.append(dict(event='ACCEPTED_NEW_ROLE_RESULT', id=cid, receipt=rec, alias=i == 1, model_role=qa.ROLE))
        docs[completion_ref['path']] = dict(status='COMPLETE_UTILITY_ORDERED_HIDDEN_VALUES_NOT_QUALITY',
            model_role=qa.ROLE, expected_inputs=240, actual_forward_calls=239, aliases=1, entries=entries,
            adapter_weights=adapter, value_weights=value, GPU_registration=registration, attempts=attempts,
            screen_reference_read=False, original_TIME_loaded=False, old_PAIR_loaded=False, old_CROP_loaded=False)
        with mock.patch.object(qa, 'bound', side_effect=lambda v:Path(v['path'])), \
             mock.patch.object(qa, 'read', side_effect=lambda p:docs[str(p)]), \
             mock.patch.object(qa, 'ref', side_effect=r), mock.patch.object(qa, 'lines', return_value=events), \
             mock.patch.object(torch, 'load', side_effect=lambda p, **kw:raws[str(p)]) as loads:
            lookup, predictions, report = qa.review_screen(completion_ref, expected, [15, 16, 17], adapter, value,
                value_state(), registration_ref=registration)
            self.assertEqual(len(lookup), 240); self.assertEqual(len(predictions), 240)
            self.assertEqual(report['actual_new_forwards'], 239); self.assertEqual(report['aliases'], 1)
            self.assertEqual(loads.call_count, 239)
        bad = copy.deepcopy(events); bad[0], bad[1] = bad[1], bad[0]
        with self.assertRaises(ValueError): qa.validate_raw_journal(bad, receipts, entries)
        bad = copy.deepcopy(events); bad[2]['alias'] = True
        with self.assertRaises(ValueError): qa.validate_raw_journal(bad, receipts, entries)

    def test_weighted_rms_loss_signed_order_and_dual_forward_count(self):
        schedule, events = [], []
        for i in range(16):
            row = dict(id='T'+str(i), source_id='s', target=-.2, draw_weight=1.25,
                forward=dict(id='f'+str(i)), reverse=dict(id='r'+str(i)))
            schedule.append(row); common = dict(step=i//4+1, micro=i, id=row['id'])
            owners = dict(source_id='s', forward_id=row['forward']['id'], reverse_id=row['reverse']['id'])
            events.extend([dict(common, **owners, event='BEGIN_TRAIN_MICRO'),
                dict(common, **owners, event='TRAIN_RAW_LOSS', target=-.2, draw_weight=1.25, target_RMS=.5,
                     prediction=.3, loss=1.25), dict(common, event='TRAIN_BACKWARD_COMPLETE')])
        result = qa.validate_micro_logs(events, schedule, 1, 4, .5)
        self.assertEqual(result['actual_dual_training_forwards'], 32)
        for change in (dict(target=.2), dict(reverse_id='wrong'), dict(loss=.1), dict(target_RMS=1.)):
            bad = copy.deepcopy(events); bad[1].update(change)
            with self.assertRaises(ValueError): qa.validate_micro_logs(bad, schedule, 1, 4, .5)

    def test_full20_utility_gain_exact_selfzero_and_all_fixed_controls(self):
        args = evaluation_fixture(); result = qa.evaluate_scope(*args)
        self.assertTrue(result['quality']['admitted'])
        self.assertEqual(result['self_gain_exact_zero'], 20)
        self.assertEqual(result['summaries']['UTILITY']['changed'], 20)
        for name in ('UTILITY_BETA_GEOMETRY', 'OLD47_GEOM11', 'OLD33_GEOM13'):
            self.assertEqual(result['summaries'][name]['changed'], 0)
        self.assertEqual(qa.choose([0., 0., -1.]), 0)
        self.assertEqual(qa.choose([0., .1, .1]), 1)

    def test_geometry_alone_or_allzero_cannot_admit_visual_mechanism(self):
        args = list(evaluation_fixture())
        for row in args[2].values(): row['hidden4096'].fill(0.)
        result = qa.evaluate_scope(*args)
        self.assertFalse(result['quality']['admitted'])
        self.assertEqual(result['summaries']['UTILITY']['changed'], 0)
        args[4]['geometry_beta'][0] = 1.
        result = qa.evaluate_scope(*args)
        self.assertEqual(result['summaries']['UTILITY']['changed'], 20)
        self.assertFalse(result['quality']['checks']['beats_UTILITY_BETA_GEOMETRY'])
        self.assertFalse(result['quality']['admitted'])

    def test_missing_pair_wrong_owner_and_invalid_reference_cannot_be_empty(self):
        args = list(evaluation_fixture())
        with self.assertRaises(ValueError): qa.evaluate_scope(args[0], args[1][:-1], *args[2:])
        args[2]['source0f']['source_sha256'] = 'wrong'
        with self.assertRaises(ValueError): qa.evaluate_scope(*args)
        args = list(evaluation_fixture()); args[3]['source0'][0] = float('nan')
        with self.assertRaises(ValueError): qa.evaluate_scope(*args)


if __name__ == '__main__':
    unittest.main()
