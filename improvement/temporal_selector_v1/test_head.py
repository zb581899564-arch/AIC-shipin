"""Focused CPU contract tests; synthetic fixtures never claim model quality."""
import io
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import torch
from torch.nn import functional as F

try:
    from . import head
except ImportError:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import head


_OLD_THREADS = None


def setUpModule():
    global _OLD_THREADS
    _OLD_THREADS = torch.get_num_threads()
    torch.set_num_threads(1)


def tearDownModule():
    torch.set_num_threads(_OLD_THREADS)


def video(name="source", *, reference=None, known=None):
    return head.TrainingVideo(
        name, torch.tensor([[0.2, 0.8], [0.7, -0.2]], dtype=torch.float64),
        torch.tensor([0, 0, 0, 1]),
        torch.tensor([[True, False], [True, False], [False, True], [False, False]]) if reference is None else reference,
        known,
    )


class TemporalHeadTests(unittest.TestCase):
    def test_native_duration_weights_and_all_raters(self):
        sample = video()
        logits = torch.tensor([1.0, -0.7], dtype=torch.float64, requires_grad=True)
        losses = head.source_losses(logits, sample)
        native = logits[sample.native_group]
        expected = F.binary_cross_entropy_with_logits(native, sample.reference.double().mean(dim=1))
        torch.testing.assert_close(losses["bce"], expected)
        group_target = torch.tensor([0.5, 0.0], dtype=torch.float64)
        unweighted = F.binary_cross_entropy_with_logits(logits, group_target)
        self.assertNotAlmostEqual(float(losses["bce"]), float(unweighted))
        p = native.sigmoid()
        manual = torch.stack([1 - 2 * (p * sample.reference[:, r]).sum() / (p.sum() + sample.reference[:, r].sum()) for r in range(2)]).mean()
        torch.testing.assert_close(losses["set_loss"], manual)

    def test_unknown_references_do_not_change_loss_or_gradient(self):
        known = torch.tensor([[True, False], [False, False], [True, True], [False, True]])
        original = video(known=known)
        altered = video(reference=original.reference ^ ~known, known=known)
        for arm in ("BCE", "SET"):
            first = torch.tensor([0.4, -0.6], dtype=torch.float64, requires_grad=True)
            second = first.detach().clone().requires_grad_()
            a = head.source_loss(first, original, arm)
            b = head.source_loss(second, altered, arm)
            a.backward()
            b.backward()
            torch.testing.assert_close(a, b, rtol=0, atol=0)
            torch.testing.assert_close(first.grad, second.grad, rtol=0, atol=0)

    def test_unknown_frame_is_not_added_as_a_negative(self):
        reference = torch.tensor([[True], [True], [True], [False]])
        sample = video(reference=reference, known=torch.tensor([True, True, True, False]))
        logits = torch.tensor([0.2, 9.0], dtype=torch.float64, requires_grad=True)
        loss = head.source_loss(logits, sample, "BCE")
        expected = F.binary_cross_entropy_with_logits(logits[:1], torch.ones(1, dtype=torch.float64))
        torch.testing.assert_close(loss, expected)
        loss.backward()
        self.assertEqual(float(logits.grad[1]), 0.0)

    def test_negative_rater_has_nonzero_set_penalty_gradient(self):
        sample = video(reference=torch.zeros((4, 2), dtype=torch.bool))
        logits = torch.zeros(2, dtype=torch.float64, requires_grad=True)
        penalty = head.source_losses(logits, sample)["set_loss"]
        penalty.backward()
        self.assertEqual(float(penalty), 0.5)
        torch.testing.assert_close(logits.grad, torch.tensor([0.1875, 0.0625], dtype=torch.float64))

    def test_multiple_frame_owners_and_duplicate_sources_are_rejected(self):
        sample = video()
        overlap = head.TrainingVideo(sample.source_id, sample.features, torch.tensor([[0, 1]] * 4), sample.reference)
        with self.assertRaisesRegex(ValueError, "one owner"):
            overlap.validate()
        with self.assertRaisesRegex(ValueError, "duplicate source_id"):
            head.fit([sample, sample], "BCE", updates=1, hidden=3)

    def test_detached_finite_and_known_annotation_contracts(self):
        model = head.TemporalHead(2, hidden=3).double()
        with self.assertRaisesRegex(ValueError, "detached"):
            model(video().features.clone().requires_grad_())
        broken = video().features.clone()
        broken[0, 0] = float("nan")
        with self.assertRaisesRegex(ValueError, "finite"):
            model(broken)
        with self.assertRaisesRegex(ValueError, "no known annotations"):
            video(known=torch.zeros((4, 2), dtype=torch.bool)).validate()

    def test_two_arms_use_identical_initialization_and_preserve_rng(self):
        saved = torch.get_rng_state().clone()
        initialized = []
        actual = head.initialize_head

        def capture(*args, **kwargs):
            model = actual(*args, **kwargs)
            initialized.append({k: v.detach().clone() for k, v in model.state_dict().items()})
            return model

        with patch.object(head, "initialize_head", side_effect=capture):
            for arm in ("BCE", "SET"):
                head.fit([video()], arm, updates=1, hidden=3)
        self.assertTrue(torch.equal(saved, torch.get_rng_state()))
        for key in initialized[0]:
            torch.testing.assert_close(initialized[0][key], initialized[1][key], rtol=0, atol=0)

    def test_equal_source_weight_and_frozen_features(self):
        a = video("a")
        b = head.TrainingVideo("b", a.features.clone(), torch.tensor([0, 1]), torch.tensor([[False, False], [True, True]]))
        initial = head.initialize_head(2, 3, dtype=torch.float64)
        expected = (head.source_loss(initial(a.features), a, "SET") + head.source_loss(initial(b.features), b, "SET")) / 2
        before = [v.features.clone() for v in (a, b)]
        _, report = head.fit([a, b], "SET", updates=1, hidden=3)
        self.assertAlmostEqual(report["objective_history"][0], float(expected), places=12)
        for item, original in zip((a, b), before):
            torch.testing.assert_close(item.features, original, rtol=0, atol=0)
            self.assertIsNone(item.features.grad)
        self.assertEqual(report["backbone_updates"], 0)

    def test_final_checkpoint_roundtrip_and_predictions(self):
        model, report = head.fit([video()], "SET", updates=3, hidden=3)
        payload = io.BytesIO()
        torch.save(model.state_dict(), payload)
        payload.seek(0)
        restored = head.TemporalHead(2, hidden=3).double()
        restored.load_state_dict(torch.load(payload, weights_only=True))
        torch.testing.assert_close(head.predict(model, video().features), head.predict(restored, video().features), rtol=0, atol=0)
        probabilities = head.predict_native(model, video().features, video().native_group)
        self.assertEqual(tuple(probabilities.shape), (4,))
        self.assertFalse(probabilities.requires_grad)
        self.assertTrue(torch.equal(probabilities[:3], probabilities[0].expand(3)))
        self.assertEqual(report["checkpoint_selection"], "final_update_only")
        self.assertEqual(len(report["objective_history"]), 3)

    def test_actual_budget_at_expected_8192_feature_dimensions(self):
        model = head.TemporalHead(8192)
        expected = 8192 * 128 + 128 + 2 * (3 * 128 * 128 + 128) + 128 + 1
        self.assertEqual(model.parameter_count, expected)
        budget = head.parameter_budget(model)
        self.assertEqual(budget["head_parameters"], 1_147_393)
        self.assertLessEqual(budget["head_parameters"], 2_000_000)
        self.assertLessEqual(budget["resident_parameters"], 9_000_000_000)
        with self.assertRaisesRegex(ValueError, "budget"):
            head.parameter_budget(model, 9_000_000_000)
        with self.assertRaisesRegex(ValueError, "2M"):
            head.TemporalHead(20000)


if __name__ == "__main__":
    unittest.main(verbosity=2)
