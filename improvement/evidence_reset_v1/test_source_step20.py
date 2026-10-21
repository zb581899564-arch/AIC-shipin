"""Linux Torch required: chain rule, global normalization, storage/reload."""
import itertools
from pathlib import Path
import tempfile
import unittest
import numpy as np
import torch
from safetensors.torch import load_file, save_file
from source_risk19 import action_gradient, normalize
from source_step20_math import combine_jacobians, fixed_step


class Checks(unittest.TestCase):
    def test_full_source_chain_rule_equals_direct_autograd(self):
        # Different numbers of actions, unequal native lengths, two raters.
        lengths = [[0, 2], [1, 3, 0]]
        tp = [[np.array([0, 0]), np.array([1, 2])],
              [np.array([1, 0]), np.array([2, 1]), np.array([0, 0])]]
        gt = np.array([4, 3])
        theta = torch.tensor([.2, -.1, .05], dtype=torch.float64, requires_grad=True)
        X = [torch.tensor([[1., 0, .2], [-.3, 1, .4]], dtype=torch.float64),
             torch.tensor([[.2, .3, .8], [.4, -.5, .6], [-.8, .2, .3]], dtype=torch.float64)]
        logits = [x @ theta for x in X]
        q = [l.softmax(0) for l in logits]
        direct = theta.sum() * 0
        for actions in itertools.product(range(2), range(3)):
            count = sum(lengths[w][j] for w, j in enumerate(actions))
            overlap = sum((tp[w][j] for w, j in enumerate(actions)))
            u = float(np.mean(2 * overlap / (count + gt)))
            direct = direct + q[0][actions[0]] * q[1][actions[1]] * u
        exact = torch.autograd.grad(direct, theta)[0].numpy()
        l = [v.detach().numpy() for v in logits]
        value, _, g, _ = action_gradient(np, lengths, tp, [normalize(np, a) for a in l], gt)
        branches = [{'theta': row.numpy().astype(np.float32)} for x in X for row in x]
        combined = combine_jacobians(np, branches, np.concatenate(g))['theta']
        self.assertAlmostEqual(value, float(direct.detach()), places=13)
        np.testing.assert_allclose(combined, exact, atol=2e-9, rtol=1e-7)

    def test_source_equal_is_not_gradient_normalized_per_source(self):
        rows = [{'a': np.array([100., 0.], np.float32)}, {'a': np.array([0., 1.], np.float32)}]
        np.testing.assert_array_equal(combine_jacobians(np, rows, [.5, .5])['a'], [50, .5])

    def test_one_step_rounding_and_safetensors_exact_reload(self):
        initial = {'a': np.array([1., -2., .001], np.float32)}
        grad = {'a': np.array([.1, .2, -.3], np.float64)}
        final, stats = fixed_step(np, initial, grad)
        independently = (initial['a'].astype(np.float64) + stats['effective_learning_rate'] * grad['a']).astype(np.float32)
        np.testing.assert_array_equal(final['a'], independently)
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / 'one.safetensors'; save_file({k: torch.from_numpy(v) for k, v in final.items()}, str(p))
            np.testing.assert_array_equal(load_file(str(p))['a'].numpy().view(np.uint8), final['a'].view(np.uint8))

    def test_reject_missing_branch_or_nonfinite_and_zero_gradient(self):
        with self.assertRaises(ValueError): combine_jacobians(np, [], [])
        with self.assertRaises(ValueError): combine_jacobians(np, [{'a': np.array([np.nan])}], [1])
        with self.assertRaises(ValueError): fixed_step(np, {'a': np.ones(1)}, {'a': np.zeros(1)})


if __name__ == '__main__': unittest.main()
