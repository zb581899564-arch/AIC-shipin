"""Actual Torch CPU checks, including independent finite-difference gradients."""
import unittest

import torch

from policy_contract import sampled_logps, source_policy_loss


class PolicyContractTests(unittest.TestCase):
    def test_forbidden_large_logits_cannot_enter_normalizer_or_gradient(self):
        logits = torch.tensor([[1.0, 2.0, 1000.0]], dtype=torch.float64, requires_grad=True)
        logp = sampled_logps(logits, [1], [[0, 1]], 1.0)
        self.assertAlmostEqual(float(logp.exp()), 0.7310585786300049)
        (-logp.sum()).backward()
        self.assertEqual(float(logits.grad[0, 2]), 0.0)
        self.assertLess(float(logits.grad[0, 1]), 0.0)

    def test_single_forced_EOS_has_no_policy_gradient(self):
        logits = torch.tensor([[9.0, 4.0]], dtype=torch.float64, requires_grad=True)
        logp = sampled_logps(logits, [1], [[1]], 0.7)
        self.assertEqual(float(logp), 0.0)
        logp.sum().backward()
        self.assertEqual(float(logits.grad.abs().sum()), 0.0)

    def test_exact_normalizer_temperature_and_token_order(self):
        logits = torch.tensor([[0.0, 2.0, 8.0]], dtype=torch.float64)
        value = sampled_logps(logits, [1], [[1, 0]], 2.0)
        self.assertAlmostEqual(float(value.exp()), 0.7310585786300049)
        with self.assertRaises(ValueError):
            sampled_logps(logits, [2], [[1, 0]], 1.0)

    def test_negative_advantage_changes_gradient_direction(self):
        base = torch.tensor([[1.0, 2.0]], dtype=torch.float64)
        gradients = []
        for advantage in [1.0, -1.0]:
            actor = base.clone().requires_grad_()
            loss, _ = source_policy_loss(actor, base, [1], [[0, 1]], 1.0, advantage, 0.0)
            loss.backward()
            gradients.append(actor.grad.clone())
        self.assertTrue(torch.allclose(gradients[0], -gradients[1], atol=1e-12, rtol=0))

    def test_categorical_KL_and_full_gradient(self):
        actor = torch.tensor([[0.2, 0.7, 9.0], [0.3, 0.4, 2.0]], dtype=torch.float64, requires_grad=True)
        reference = torch.tensor([[0.0, 0.2, 0.1], [0.1, 0.2, 0.4]], dtype=torch.float64)
        def objective(value):
            return source_policy_loss(value, reference, [1, 2], [[0, 1], [0, 2]], 0.7, 0.3, 0.02)[0]
        self.assertTrue(torch.autograd.gradcheck(objective, (actor,), eps=1e-6, atol=1e-6, rtol=1e-4))
        _, details = source_policy_loss(actor, reference, [1, 2], [[0, 1], [0, 2]], 0.7, 0.3, 0.02)
        p = torch.distributions.Categorical(logits=actor[0, [0, 1]] / 0.7)
        q = torch.distributions.Categorical(logits=reference[0, [0, 1]] / 0.7)
        self.assertGreaterEqual(float(details['mean_allowed_categorical_KL']), 0.0)
        self.assertGreater(float(torch.distributions.kl_divergence(p, q)), 0.0)

    def test_identical_reference_has_zero_KL(self):
        actor = torch.tensor([[0.2, 0.7]], dtype=torch.float64, requires_grad=True)
        _, details = source_policy_loss(actor, actor.detach(), [0], [[0, 1]], 1.0, 0.0, 0.02)
        self.assertEqual(float(details['mean_allowed_categorical_KL']), 0.0)


if __name__ == '__main__':
    unittest.main()
