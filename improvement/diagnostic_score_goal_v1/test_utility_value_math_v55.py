import copy
import hashlib
import io
import math
from types import SimpleNamespace
import unittest
from unittest import mock

import numpy as np
import torch

import utility_value_math_v55 as utility
import utility_value_gpu_v55 as gpu


def prepared_schedule():
    rows = []
    for cycle, length in ((0, 602), (1, 602), (2, 602), (3, 194)):
        for i in range(length):
            sid = 's%03d'%i; sha = hashlib.sha256(sid.encode()).hexdigest()
            pair = [0, 1+cycle//2]; a, b = pair if cycle%2 == 0 else pair[::-1]
            sign = 1. if a < b else -1.; target = sign*(.1 if pair[1] == 1 else .2)
            count = 2 if pair[1] == 1 or i < 194 else 1
            def entry(x, y):
                cid = '%s_%d_%d'%(sid, x, y)
                return dict(id=cid, source_id=sid, source_sha256=sha,
                            input=dict(path='/frozen/'+cid+'.json', sha256=hashlib.sha256(cid.encode()).hexdigest()))
            f, r = entry(a, b), entry(b, a)
            rows.append(dict(id='T%04d'%len(rows), source_id=sid, source_sha256=sha,
                a=a, b=b, unordered_pair=pair, forward=f, reverse=r, forward_id=f['id'], reverse_id=r['id'],
                geometry_delta11=(sign*np.arange(1., 12.)/100).tolist(), target=target,
                draw_weight=2000/(1204*count)))
    return dict(schema='UTILITY_CONTINUOUS_TRAIN_SCHEDULE_V55', train_schedule=rows,
                train_target_RMS=math.sqrt((.1**2+.2**2)/2), class_token_ids=[15, 16, 17])


class UtilityValueTests(unittest.TestCase):
    def test_original2000_draws_equal1204_pair_objective_without_double_counting_order(self):
        prepared = prepared_schedule(); rows, digest, report = utility.validate_schedule(prepared)
        weights = {}; loss_by_pair = {}
        for row in rows:
            key = row['source_id'], *row['unordered_pair']
            weights[key] = weights.get(key, 0.)+row['draw_weight']/2000
            loss_by_pair[key] = (row['target']/prepared['train_target_RMS'])**2
        self.assertEqual((len(weights), report['sources'], len(rows)), (1204, 602, 2000))
        np.testing.assert_allclose(list(weights.values()), np.full(1204, 1/1204), rtol=1e-15, atol=0.)
        objective = math.fsum(row['draw_weight']*(row['target']/prepared['train_target_RMS'])**2 for row in rows)/2000
        self.assertAlmostEqual(objective, math.fsum(loss_by_pair.values())/1204)
        self.assertEqual(digest, utility.digest(rows)); self.assertTrue(report['source_pair_equal_empirical_objective'])

    def test_schedule_identity_target_weight_rms_unknowns_fail_closed(self):
        for kind in ('count', 'weight', 'target', 'RMS', 'id', 'source', 'geometry', 'class'):
            p = prepared_schedule(); r = p['train_schedule'][0]
            if kind == 'count': p['train_schedule'].pop()
            elif kind == 'weight': r['draw_weight'] *= 2
            elif kind == 'target': r['target'] = .3
            elif kind == 'RMS': p['train_target_RMS'] *= 2
            elif kind == 'id': r['reverse_id'] = r['forward_id']
            elif kind == 'source': r['reverse']['source_sha256'] = '0'*64
            elif kind == 'geometry': r['geometry_delta11'][0] = np.inf
            else: p['class_token_ids'] = [True, 16, 17]
            with self.subTest(kind=kind), self.assertRaises(ValueError): utility.validate_schedule(p)

    def test_continuous_target_gradient_reaches_both_hidden_and_all_parameter_groups(self):
        torch.manual_seed(20261018)
        head = torch.nn.Linear(4096, 1, bias=False); torch.nn.init.normal_(head.weight, 0., .001)
        a = torch.nn.Parameter(torch.randn(2, 4)*.01); b = torch.nn.Parameter(torch.zeros(4096, 2))
        beta = torch.nn.Parameter(torch.zeros(11)); x = torch.tensor([1., 2., 3., 4.]); reverse = -x
        fixed_f, fixed_r = torch.randn(4096), torch.randn(4096)
        geom = torch.linspace(.01, .11, 11)
        params = [('toy.lora_A.utility.weight', a), ('toy.lora_B.utility.weight', b)]
        optimizer = torch.optim.AdamW([dict(params=[a, b], lr=5e-5), dict(params=[head.weight], lr=.001),
                                      dict(params=[beta], lr=.001)], weight_decay=0.)
        initial = [p.detach().clone() for p in (a, b, head.weight, beta)]
        for step in range(1, 5):
            optimizer.zero_grad(set_to_none=True)
            hf = fixed_f+b@(a@x); hr = fixed_r+b@(a@reverse)
            hf.retain_grad(); hr.retain_grad()
            gain = utility.prediction(head, hf, hr, beta, geom)
            actual = utility.loss(gain, .2, 1.7, .15)
            torch.testing.assert_close(actual, 1.7*((gain-.2)/.15)**2)
            actual.backward(); self.assertGreater(hf.grad.abs().sum().item(), 0.); self.assertGreater(hr.grad.abs().sum().item(), 0.)
            groups = gpu._grad_groups(params, head, beta, torch)
            if step == 1: self.assertEqual(groups['LoRA_A']['nonzero_tensors'], 0)
            else: self.assertTrue(all(g['nonzero_tensors'] and g['finite'] and g['preclip_norm'] > 0 for g in groups.values()))
            torch.nn.utils.clip_grad_norm_([a, b, head.weight, beta], 1.); optimizer.step()
        self.assertTrue(all(not torch.equal(p, old) for p, old in zip((a, b, head.weight, beta), initial)))

    def test_gain_swap_and_same_input_self_exact_zero(self):
        torch.manual_seed(2); head = torch.nn.Linear(4096, 1, bias=False)
        f, r, beta, geometry = torch.randn(4096), torch.randn(4096), torch.randn(11), torch.randn(11)
        forward = utility.prediction(head, f, r, beta, geometry)
        swapped = utility.prediction(head, r, f, beta, -geometry)
        self.assertEqual(forward.item(), -swapped.item())
        self.assertEqual(utility.prediction(head, f, f, beta, torch.zeros(11)).item(), 0.)
        for target, weight, rms in ((True, 1., .1), (.2, 0., .1), (.2, 1., 0.), (np.nan, 1., .1)):
            with self.assertRaises(ValueError): utility.loss(forward, target, weight, rms)

    def test_progress_preserves_three_adam_groups_names_rng_and_value_tensors(self):
        torch.manual_seed(7); head = torch.nn.Linear(4096, 1, bias=False); beta = torch.nn.Parameter(torch.zeros(11))
        adapter = torch.nn.Parameter(torch.ones(2, 2))
        optimizer = torch.optim.AdamW([dict(params=[adapter], lr=5e-5), dict(params=[head.weight], lr=.001),
                                      dict(params=[beta], lr=.001)], weight_decay=0.)
        (adapter.sum()+head.weight.sum()+beta.sum()).backward(); optimizer.step()
        names = [['toy.lora_A.weight'], ['head.weight'], ['geometry_beta']]
        def cpu_tree(v, torch):
            if isinstance(v, torch.Tensor): return v.detach().cpu().clone()
            if isinstance(v, dict): return {k:cpu_tree(x, torch) for k, x in v.items()}
            if isinstance(v, list): return [cpu_tree(x, torch) for x in v]
            return v
        fake = SimpleNamespace(_cpu_tree=cpu_tree)
        trainables = dict(adapter_state_dict={'toy.lora_A.weight':adapter.detach().clone()},
            head_state_dict={'weight':head.weight.detach().clone()}, geometry_beta=beta.detach().clone())
        with mock.patch.object(gpu, '_trainables', return_value=trainables), \
                mock.patch.object(torch.cuda, 'get_rng_state_all', return_value=[]):
            progress = gpu._progress(None, head, beta, optimizer, torch, np, fake, 4, 'a'*64,
                                     dict(path='/frozen/prepared.json', sha256='b'*64), .2, names)
        self.assertEqual((progress['step'], progress['micro'], progress['logical_training_forwards']), (4, 16, 32))
        self.assertEqual(progress['optimizer_parameter_names_by_group'], names)
        self.assertEqual(progress['optimizer_parameter_names_sha256'], utility.digest(names))
        self.assertEqual([g['lr'] for g in progress['optimizer_state_dict']['param_groups']], [5e-5, .001, .001])
        buffer = io.BytesIO(); torch.save(progress, buffer); buffer.seek(0)
        restored = torch.load(buffer, map_location='cpu', weights_only=True)
        self.assertTrue(gpu._tree_equal(progress, restored, torch))
        altered = copy.deepcopy(restored); altered['geometry_beta'][0] += 1
        self.assertFalse(gpu._tree_equal(progress, altered, torch))

    def test_only_explicit_remaining_starts5_no_repeated_pilot_or_checkpoint_search(self):
        pilot, rest = list(utility.phase_steps('pilot4')), list(utility.phase_steps('remaining496'))
        self.assertEqual(pilot, [1, 2, 3, 4]); self.assertEqual((rest[0], rest[-1], len(rest)), (5, 500, 496))
        self.assertFalse(set(pilot)&set(rest))
        with self.assertRaises(ValueError): utility.phase_steps('retry')


if __name__ == '__main__':
    unittest.main()
