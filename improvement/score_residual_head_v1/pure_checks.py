"""Targeted synthetic CPU checks; no media/model/cache/official data access."""
import unittest
from fractions import Fraction
import torch
from torch.nn import functional as F

try:
    from .contracts import build_contract, native_interval_ordinals
    from .head import ResidualHead, TrainingVideo, native_prediction, train_head, unit_logits
    from .metrics import hard_temporal_metrics, macro_objective, video_losses
except ImportError:
    from contracts import build_contract, native_interval_ordinals
    from head import ResidualHead, TrainingVideo, native_prediction, train_head, unit_logits
    from metrics import hard_temporal_metrics, macro_objective, video_losses


class ContractChecks(unittest.TestCase):
    def test_vfr_half_open_exact(self):
        pts = ["0", "1/100", "1/10", "7/10", "9/10"]
        self.assertEqual(native_interval_ordinals(pts, "1/10", "9/10"), (2, 4))
        with self.assertRaises(ValueError):
            native_interval_ordinals([0.0, 0.1], "0", "1")
        with self.assertRaises(ValueError):
            native_interval_ordinals(["0", "0"], "0", "1")

    def test_cross_boundary_and_zero_native_identity(self):
        base = [False, True, False, False, True]
        contract = build_contract([0, 0, 0, 1, 1], base, [None]*5, 2)
        self.assertEqual(contract.n, (1, 1, 1, 1, 1))
        self.assertEqual(contract.feature_index, (0, 0, 0, 1, 1))
        model = ResidualHead(3, 4)
        residual = model(torch.randn(2, 3))
        self.assertTrue(torch.equal(residual, torch.zeros(2)))
        self.assertEqual(native_prediction(residual, contract), tuple(base))
        # A nonzero group correction applies to native frames without merging
        # baseline boundaries, and a threshold tie retains the native prior.
        self.assertEqual(native_prediction(torch.tensor([1., -1.]), contract), (False, True, False, False, True))
        self.assertEqual(native_prediction(torch.tensor([2., -2.]), contract), (True, True, True, False, False))

    def test_counts_soft_labels_and_unknown_mask(self):
        contract = build_contract([0, 0, 0, 1, 1], [False]*5, [1., .5, None, 0., None], 2)
        logits = torch.tensor([.3, -.6], dtype=torch.float64, requires_grad=True)
        result = video_losses(logits, contract)
        expected_bce = F.binary_cross_entropy_with_logits(logits[[0, 0, 1]], torch.tensor([1., .5, 0.], dtype=torch.float64))
        torch.testing.assert_close(result.bce, expected_bce)
        p = logits.sigmoid()
        torch.testing.assert_close(result.soft_f1, 2*(1.5*p[0])/(2*p[0]+p[1]+1.5))
        unknown = build_contract([0, 1], [True, False], [None, 1.], 2)
        z = torch.tensor([10., 0.], requires_grad=True)
        loss = video_losses(z, unknown)
        macro_objective([loss], "SCORE").backward()
        self.assertEqual(float(z.grad[0]), 0.)
        self.assertEqual(result.scope, "MASKED")

    def test_empty_unknown_and_invalid_input(self):
        empty = build_contract([0, 0], [True, True], [0., 0.], 1)
        result = video_losses(torch.tensor([0.]), empty)
        self.assertIsNone(result.soft_f1)
        self.assertEqual(result.reference_kind, "COMPLETE_EMPTY")
        self.assertEqual(float(result.score_loss), .5)
        unknown = build_contract([0], [False], [None], 1)
        with self.assertRaises(ValueError):
            macro_objective([video_losses(torch.tensor([0.]), unknown)], "BCE")
        self.assertIsNone(hard_temporal_metrics([False], [0.])["temporal_f1"])
        self.assertTrue(hard_temporal_metrics([False], [0.])["empty_match"])
        with self.assertRaises(ValueError):
            build_contract([0], [False], [float("nan")], 1)
        with self.assertRaises(ValueError):
            ResidualHead(100000, 64)

    def test_video_macro_and_single_update(self):
        a = build_contract([0], [False], [1.], 1)
        b = build_contract([0]*3, [False]*3, [0.]*3, 1)
        first = video_losses(torch.tensor([0.]), a)
        second = video_losses(torch.tensor([2.]), b)
        torch.testing.assert_close(macro_objective([first, second], "BCE"), (first.bce+second.bce)/2)
        sample = TrainingVideo("synthetic-only", torch.tensor([[1., 2.]]), a)
        model, receipt = train_head([sample], "SCORE", 7, updates=1, hidden_dim=4)
        self.assertEqual(receipt["updates"], 1)
        self.assertLessEqual(model.parameter_count, 2_000_000)
        self.assertEqual(receipt["resident_parameters"], 8_782_459_120+model.parameter_count)
        self.assertNotEqual(float(model(sample.features)[0]), 0.)


if __name__ == "__main__":
    unittest.main()
