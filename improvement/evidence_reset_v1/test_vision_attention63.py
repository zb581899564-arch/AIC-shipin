"""Targeted real CPU Torch checks; no Qwen weights, media or CUDA execution."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

import numpy as np
import torch
from torch import nn

import vision_attention63 as v63


class Checks(unittest.TestCase):
    def test_zero_bits_first_B_gradient_then_A_gradient_with_frozen_BF16_base(self):
        torch.manual_seed(63)
        base = nn.Linear(5, 7, bias=True).to(dtype=torch.bfloat16)
        original = {k: t.detach().clone() for k, t in base.state_dict().items()}
        layer = v63.VisualLoRALinear(base)
        x = torch.randn(8, 5, dtype=torch.bfloat16)
        expected = base(x).detach()
        actual = layer(x)
        self.assertTrue(torch.equal(expected.view(torch.uint8), actual.detach().view(torch.uint8)))
        optimizer = torch.optim.AdamW([layer.lora_A, layer.lora_B], lr=.01, weight_decay=0)
        actual.float().square().mean().backward()
        self.assertEqual(int(layer.lora_A.grad.count_nonzero()), 0)
        self.assertGreater(float(layer.lora_B.grad.abs().sum()), 0)
        self.assertEqual(layer.lora_A.grad.dtype, torch.float32)
        optimizer.step(); optimizer.zero_grad(set_to_none=True)
        layer(x).float().square().mean().backward()
        self.assertGreater(float(layer.lora_A.grad.abs().sum()), 0)
        self.assertTrue(all(p.grad is None and not p.requires_grad for p in base.parameters()))
        self.assertTrue(all(torch.equal(original[k].view(torch.uint8), t.view(torch.uint8)) for k, t in base.state_dict().items()))
        self.assertEqual(layer.base_layer.weight.dtype, torch.bfloat16)
        self.assertEqual(layer.lora_A.dtype, torch.float32)
        self.assertEqual(layer.lora_B.dtype, torch.float32)

    def test_full_FP32_saved_reset_and_reload_with_dtype_rejection(self):
        model = nn.Sequential(v63.VisualLoRALinear(nn.Linear(5, 7).to(dtype=torch.bfloat16)))
        initial = v63.lora_state(model)
        with torch.no_grad():
            model[0].lora_A.add_(.013)
            model[0].lora_B.normal_(mean=.01, std=.02)
        final = v63.lora_state(model)
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'adapter.pt'
            torch.save(dict(adapter_state_dict=final), path)
            durable = torch.load(path, map_location='cpu', weights_only=True)['adapter_state_dict']
            v63.load_lora_state(model, initial)
            self.assertEqual(v63.tensor_signature(v63.lora_state(model)), v63.tensor_signature(initial))
            self.assertNotEqual(v63.tensor_signature(initial), v63.tensor_signature(final))
            v63.load_lora_state(model, durable)
            self.assertEqual(v63.tensor_signature(v63.lora_state(model)), v63.tensor_signature(final))
            wrong = {k: value.to(torch.bfloat16) for k, value in durable.items()}
            with self.assertRaises(ValueError):
                v63.load_lora_state(model, wrong)

    def test_actual_pool_FP64_margin_gradient_and_heldout_target_exclusion(self):
        torch.manual_seed(64)
        grid = torch.tensor([[1, 2, 2], [2, 2, 2]], dtype=torch.int64)
        plan = dict(videos=[dict(role='Overview', groups=1, native_ordinals=[0, 4], padding=0),
                            dict(role='Excerpt', groups=2, native_ordinals=[8, 12, 16, 20], padding=0)])
        left = torch.randn(2, 4096, requires_grad=True)
        right = torch.randn(2, 4096, requires_grad=True)
        fleft, audit = v63.pool_feature([torch.randn(1, 4096), left], grid, plan)
        fright, _ = v63.pool_feature([torch.randn(1, 4096), right], grid, plan)
        self.assertEqual(tuple(audit.shape), (2, 4096))
        self.assertFalse(audit.requires_grad)
        head = torch.linspace(-.3, .5, 4096, dtype=torch.float64)
        loss, margin = v63.soft_pair_loss(fleft, fright, head, .7)
        expected = ((fleft.detach().double().numpy() - fright.detach().double().numpy()) / 64) @ head.numpy()
        self.assertAlmostEqual(float(margin.detach()), float(expected), places=12)
        loss.backward()
        self.assertGreater(float(left.grad.abs().sum()), 0)
        self.assertGreater(float(right.grad.abs().sum()), 0)
        self.assertIsNone(head.grad)
        self.assertEqual(margin.dtype, torch.float64)
        wrong_grid = grid.clone(); wrong_grid[1, 0] = 3
        with self.assertRaises(ValueError):
            v63.pool_feature([torch.randn(1, 4096), left], wrong_grid, plan)
        rows, cases, train_uids = [], {}, set()
        for source in range(18):
            sid = f'D{source:02d}'
            for pair in range(2):
                a, b = f'{sid}_{pair}_A', f'{sid}_{pair}_B'
                cases[a] = cases[b] = dict(sid=sid)
                train_uids.update([a, b])
                rows.append(dict(pair_id=f'{sid}_{pair}', source_id=sid, source_pair_count=2,
                                 left=a, right=b, preference_left=.7))
        self.assertEqual(len(v63.validate_training_pairs(rows, cases, train_uids)), 18)
        cases['heldout_case'] = dict(sid='D00')
        poisoned = deepcopy(rows); poisoned[0]['left'] = 'heldout_case'
        with self.assertRaises(ValueError):
            v63.validate_training_pairs(poisoned, cases, train_uids)
        with self.assertRaises(ValueError):
            v63.soft_pair_loss(fleft, fright, head, 1.1)


if __name__ == '__main__':
    unittest.main()
