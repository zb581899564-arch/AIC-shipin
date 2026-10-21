import unittest
from copy import deepcopy

from vision_readout53 import excerpt_shape, independent_pool


class VisualReadoutContract(unittest.TestCase):
    def test_native_excerpt_split_and_reject_role_drift(self):
        plan = dict(videos=[dict(role='Overview', groups=2, padding=0, native_ordinals=[1, 2, 3, 4]),
                            dict(role='Excerpt', groups=3, padding=0, native_ordinals=[5, 6, 7, 8, 9, 10])])
        self.assertEqual(excerpt_shape([[2, 4, 6], [3, 4, 6]], plan), ([12, 18], 3, 6))
        bad = deepcopy(plan);bad['videos'][1]['role'] = 'Overview'
        with self.assertRaises(ValueError):excerpt_shape([[2, 4, 6], [3, 4, 6]], bad)
        bad = deepcopy(plan);bad['videos'][1]['native_ordinals'].pop()
        with self.assertRaises(ValueError):excerpt_shape([[2, 4, 6], [3, 4, 6]], bad)

    def test_real_torch_independent_group_pool(self):
        import torch
        gen = torch.Generator().manual_seed(5301)
        tokens = torch.randn(3, 6, 4096, generator=gen)
        actual = torch.nn.functional.layer_norm(tokens.flatten(0, 1).mean(0), (4096,), eps=1e-5)
        # The production independent path is CPU FP64 spatial means, saved FP32.
        independent_groups = tokens.double().mean(1).float()
        torch.testing.assert_close(actual, independent_pool(torch, independent_groups), atol=2e-5, rtol=1e-4)
        other = tokens.clone();other[2, :, 0] += 10
        changed = independent_pool(torch, other.double().mean(1).float())
        self.assertFalse(torch.allclose(actual, changed))

    def test_source_equal_metric_and_nonidentity_permutation(self):
        import numpy as np
        from vision_readout53 import metric
        rows = [dict(source_id='one', pair_id='a', preference_left=1.),
                dict(source_id='one', pair_id='b', preference_left=0.),
                dict(source_id='two', pair_id='c', preference_left=1.)]
        diff = np.array([[1.], [-1.], [-1.]])
        value = metric(np, rows, diff, np.array([1.]))
        self.assertEqual(value['source_macro_accuracy'], .5)
        self.assertFalse(np.array_equal(diff, np.roll(diff, 1, axis=0)))


if __name__ == '__main__':unittest.main()
