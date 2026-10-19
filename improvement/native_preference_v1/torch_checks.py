"""Synthetic CPU acceptance checks; never loads Qwen or allocates CUDA.

Run ``python -m improvement.native_preference_v1.torch_checks`` on Linux before
admitting the GPU pilot.  Missing Torch exits 77 and explicitly does not pass
the Torch gate.  ``--pure`` runs the standard-library checks in this mirror.
"""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import math
from pathlib import Path
import tempfile
import unittest

from .runtime import (build_training_tokens, canonical_frozen_hash, dpo_loss_and_coefficient,
                      dpo_tensor_loss, freeze_except, sequence_log_probability, tokenize_answer,
                      _pair_payload)
from .contracts import reference, save_new


class _Tokenizer:
    """A deterministic tokenizer with a real prompt-boundary merge counterexample."""
    eos_token_id = 999

    def convert_tokens_to_ids(self, text):
        return self.eos_token_id if text == "<|im_end|>" else None

    def encode(self, text, *, add_special_tokens=False):
        assert add_special_tokens is False
        result = []
        while text:
            if text.startswith("<|im_end|>"):
                result.append(self.eos_token_id)
                text = text[len("<|im_end|>"):]
            elif text.startswith("ab"):
                result.append(1000)
                text = text[2:]
            else:
                result.append(ord(text[0]))
                text = text[1:]
        return result

    def decode(self, ids, *, skip_special_tokens=False, clean_up_tokenization_spaces=False):
        assert skip_special_tokens is False and clean_up_tokenization_spaces is False
        return "".join("<|im_end|>" if value == self.eos_token_id else "ab" if value == 1000 else chr(value)
                       for value in ids)


class PureChecks(unittest.TestCase):
    def test_actual_full_text_suffix_and_eos(self):
        tokenizer = _Tokenizer()
        answer = '{"segments":[]}'
        actual = tokenize_answer(tokenizer, {"input_ids": [[80, 58]]}, answer, request_text="P:")
        self.assertEqual(actual, [ord(char) for char in answer] + [999])

    def test_prompt_boundary_merge_is_rejected(self):
        tokenizer = _Tokenizer()
        # encode(answer) alone would accept [98,999]; the full prefix changes.
        with self.assertRaisesRegex(ValueError, "changed the visual/prompt prefix"):
            tokenize_answer(tokenizer, {"input_ids": [[97]]}, "b")

    def test_wrong_expanded_text_and_special_token_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "actual cached prefix"):
            tokenize_answer(_Tokenizer(), {"input_ids": [[80]]}, "x", request_text="Q")
        with self.assertRaisesRegex(ValueError, "special-token"):
            tokenize_answer(_Tokenizer(), {"input_ids": [[80]]}, "<|im_end|>")

    def test_whole_suffix_cannot_be_truncated(self):
        with self.assertRaisesRegex(ValueError, "token budget"):
            tokenize_answer(_Tokenizer(), {"input_ids": [[80]]}, "z" * 512)

    def test_dpo_scalar_and_coefficient_independent_finite_difference(self):
        args = (-5.1, -7.4, -6.0, -7.0, 0.1)
        loss, coefficient, margin = dpo_loss_and_coefficient(*args)
        self.assertAlmostEqual(margin, 1.3)
        self.assertAlmostEqual(loss, -math.log(1 / (1 + math.exp(-0.13))))
        epsilon = 1e-5
        plus = dpo_loss_and_coefficient(args[0] + epsilon, *args[1:])[0]
        minus = dpo_loss_and_coefficient(args[0] - epsilon, *args[1:])[0]
        self.assertAlmostEqual(coefficient, (plus - minus) / (2 * epsilon), places=9)
        zero = dpo_loss_and_coefficient(-100, -150, -100, -150, 0.1)
        self.assertAlmostEqual(zero[0], math.log(2))
        self.assertAlmostEqual(zero[1], -0.05)
        for pc, pr in ((-1e10, -1), (-1, -1e10)):
            self.assertTrue(all(math.isfinite(value) for value in dpo_loss_and_coefficient(pc, pr, -1, -2, 0.1)))

    def test_pairs_require_exact_equal_suffix_lengths(self):
        pair = dict(pair_id="source:0", input_key="source/window", chosen_ids=[1, 2, 9], rejected_ids=[2, 1, 9])
        self.assertEqual(_pair_payload(pair), pair)
        for bad in ([2, 9], [1, 2, 9], [True, 1, 9]):
            with self.assertRaises(ValueError):
                _pair_payload(dict(pair, rejected_ids=bad))


def torch_suite(torch):
    """Construct actual CPU-Torch tests only after its availability is known."""
    def tiny_model():
        class TinyCausal(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.embedding = torch.nn.Embedding(8, 4)
                self.backbone = torch.nn.Linear(4, 4, bias=False)
                self.lora_A = torch.nn.Linear(4, 2, bias=False)
                self.lora_B = torch.nn.Linear(2, 4, bias=False)
                self.lm_head = torch.nn.Linear(4, 8, bias=False)

            def forward(self, ids):
                value = self.embedding(ids)
                denominator = torch.arange(1, ids.shape[1] + 1, dtype=value.dtype)[None, :, None]
                # Every output sees only current/past tokens, never future targets.
                value = torch.tanh(self.backbone(value.cumsum(1) / denominator))
                return self.lm_head(value + self.lora_B(self.lora_A(value)))

        torch.manual_seed(613)
        model = TinyCausal()
        with torch.no_grad():
            model.embedding.weight.copy_(torch.tensor([
                [0., 0., 0., 0.], [1., .4, .1, .2], [1., .3, .2, .1],
                [.8, .2, .3, .1], [.7, .3, .2, .1], [.4, .5, .1, .2],
                [.5, .1, .4, .2], [.2, .4, .3, .1]], dtype=torch.float32))
            model.backbone.weight.copy_(torch.eye(4))
            model.lora_A.weight.copy_(torch.tensor([[1., 0., 0., 0.], [0., 1., 0., 0.]]))
            model.lora_B.weight.zero_()
            model.lm_head.weight.mul_(.1)
            model.lm_head.weight[3].copy_(torch.tensor([1., 0., 0., 0.]))
            model.lm_head.weight[4].copy_(torch.tensor([-1., 0., 0., 0.]))
        freeze_except(model, {"lora_A.weight", "lora_B.weight"})
        return model

    def logprob(model, suffix):
        tokens = build_training_tokens(torch, torch.tensor([[1, 2]], dtype=torch.int64), suffix)
        logits = model(tokens["input_ids"]).index_select(1, tokens["positions"])
        return sequence_log_probability(torch, logits, tokens["targets"])

    class TorchChecks(unittest.TestCase):
        def test_mask_matches_independent_conventional_causal_ce_and_eos(self):
            torch.manual_seed(137)
            prefix = torch.tensor([[1, 4, 2]], dtype=torch.int64)
            suffix = [3, 5]
            tokens = build_training_tokens(torch, {"input_ids": prefix, "attention_mask": torch.ones_like(prefix)}, suffix)
            logits = torch.randn(1, 5, 6, dtype=torch.float32, requires_grad=True)
            actual = sequence_log_probability(torch, logits.index_select(1, tokens["positions"]), tokens["targets"])
            # Conventional next-token labels constructed without the tested mask.
            expected_labels = torch.tensor([[-100, -100, -100, 3, 5]], dtype=torch.int64)
            expected = -torch.nn.functional.cross_entropy(logits[:, :-1].reshape(-1, 6),
                                                          expected_labels[:, 1:].reshape(-1),
                                                          ignore_index=-100, reduction="sum")
            self.assertTrue(torch.allclose(actual, expected, atol=1e-7, rtol=0))
            self.assertEqual(tokens["labels"].tolist(), expected_labels.tolist())
            self.assertEqual(tokens["positions"].tolist(), [2, 3])
            actual.backward()
            self.assertTrue(torch.equal(logits.grad[:, :2], torch.zeros_like(logits.grad[:, :2])))
            self.assertTrue(torch.equal(logits.grad[:, 4:], torch.zeros_like(logits.grad[:, 4:])))
            self.assertGreater(float(logits.grad[0, 3, 5]), 0, "Terminal EOS must have a nonzero causal target gradient")

        def test_repeating_tokens_doubles_sum_loss_and_not_mean(self):
            one = torch.tensor([[[1., -1., .5]]], dtype=torch.float32)
            target = torch.tensor([[2]], dtype=torch.int64)
            single = sequence_log_probability(torch, one, target)
            double = sequence_log_probability(torch, one.repeat(1, 2, 1), target.repeat(1, 2))
            self.assertTrue(torch.allclose(double, single * 2, atol=1e-7, rtol=0))
            self.assertNotEqual(float(double), float(single))

        def test_exact_recompute_matches_full_graph_dpo_gradient(self):
            policy, reference_model = tiny_model(), tiny_model()
            freeze_except(reference_model, ())
            with torch.no_grad():
                rc, rr = logprob(reference_model, [3, 7]), logprob(reference_model, [4, 7])
                policy.lora_B.weight.add_(.03)
            recompute = copy.deepcopy(policy)
            full_loss = dpo_tensor_loss(torch, logprob(policy, [3, 7]), logprob(policy, [4, 7]), rc, rr, .1)
            (full_loss / 2).backward()
            with torch.no_grad():
                pc, pr = float(logprob(recompute, [3, 7])), float(logprob(recompute, [4, 7]))
            loss, coefficient, _ = dpo_loss_and_coefficient(pc, pr, float(rc), float(rr), .1)
            self.assertAlmostEqual(float(full_loss), loss, places=6)
            (logprob(recompute, [3, 7]) * (coefficient / 2)).backward()
            (logprob(recompute, [4, 7]) * (-coefficient / 2)).backward()
            expected = dict(policy.named_parameters())
            for name, parameter in recompute.named_parameters():
                if "lora_" in name:
                    self.assertIsNotNone(parameter.grad)
                    self.assertTrue(torch.allclose(parameter.grad, expected[name].grad, atol=1e-7, rtol=1e-5), name)
                else:
                    self.assertIsNone(parameter.grad)
                    self.assertIsNone(expected[name].grad)
            self.assertTrue(all(parameter.grad is None for parameter in reference_model.parameters()))

        def test_fp32_destination_must_be_upcast_before_original_copy(self):
            source = torch.tensor([[1.000123, .345678, -.0000123456]], dtype=torch.float32)
            rounded = torch.zeros_like(source, dtype=torch.bfloat16)
            rounded.copy_(source)
            self.assertFalse(torch.equal(source.view(torch.uint8), rounded.float().view(torch.uint8)))
            exact = torch.zeros_like(source, dtype=torch.bfloat16).float()
            exact.copy_(source)
            self.assertTrue(torch.equal(source.view(torch.uint8), exact.view(torch.uint8)))

        def test_actual_adapter_gradient_frozen_base_and_save_reload(self):
            policy = tiny_model()
            before = canonical_frozen_hash(policy, torch)
            base_snapshot = {name: parameter.detach().clone() for name, parameter in policy.named_parameters() if "lora_" not in name}
            initial_adapter = {name: parameter.detach().clone() for name, parameter in policy.named_parameters() if "lora_" in name}
            with torch.no_grad():
                rc, rr = float(logprob(policy, [3, 7])), float(logprob(policy, [4, 7]))
            parameters = [parameter for parameter in policy.parameters() if parameter.requires_grad]
            # The toy optimizer is chosen for an observable CPU gradient check;
            # it is not the Qwen pilot recipe or a proxy-quality experiment.
            optimizer = torch.optim.AdamW(parameters, lr=.01, weight_decay=0)
            for step in range(8):
                optimizer.zero_grad(set_to_none=True)
                with torch.no_grad():
                    pc, pr = float(logprob(policy, [3, 7])), float(logprob(policy, [4, 7]))
                loss, coefficient, margin = dpo_loss_and_coefficient(pc, pr, rc, rr, .1)
                if step == 0:
                    self.assertAlmostEqual(loss, math.log(2), places=7)
                    self.assertAlmostEqual(margin, 0)
                (logprob(policy, [3, 7]) * coefficient).backward()
                (logprob(policy, [4, 7]) * -coefficient).backward()
                self.assertTrue(all(parameter.grad is not None and bool(torch.isfinite(parameter.grad).all()) for parameter in parameters))
                self.assertGreater(sum(float(parameter.grad.square().sum()) for parameter in parameters), 0)
                self.assertTrue(all(parameter.grad is None for name, parameter in policy.named_parameters() if "lora_" not in name))
                optimizer.step()
            with torch.no_grad():
                final_chosen, final_rejected = float(logprob(policy, [3, 7])), float(logprob(policy, [4, 7]))
            self.assertGreater((final_chosen - final_rejected) - (rc - rr), 1e-4)
            self.assertEqual(before, canonical_frozen_hash(policy, torch))
            for name, parameter in policy.named_parameters():
                if name in base_snapshot:
                    self.assertTrue(torch.equal(parameter, base_snapshot[name]), name)
            self.assertTrue(any(not torch.equal(parameter, initial_adapter[name]) for name, parameter in policy.named_parameters() if name in initial_adapter))
            state = {name: parameter.detach().clone() for name, parameter in policy.named_parameters() if "lora_" in name}
            with tempfile.TemporaryDirectory(prefix="aic_native_preference_cpu_") as directory:
                checkpoint = Path(directory) / "adapter.pt"
                torch.save(state, checkpoint)
                reloaded = tiny_model()
                result = reloaded.load_state_dict(torch.load(checkpoint, map_location="cpu", weights_only=True), strict=False)
                self.assertEqual(set(result.missing_keys), set(base_snapshot))
                self.assertEqual(result.unexpected_keys, [])
                freeze_except(reloaded, ())
                with torch.no_grad():
                    self.assertEqual(float(logprob(reloaded, [3, 7])), final_chosen)
                    self.assertEqual(float(logprob(reloaded, [4, 7])), final_rejected)
                self.assertEqual(before, canonical_frozen_hash(reloaded, torch))
                for name, parameter in reloaded.named_parameters():
                    if name in state:
                        self.assertTrue(torch.equal(parameter.view(torch.uint8), state[name].view(torch.uint8)), name)

    return unittest.defaultTestLoader.loadTestsFromTestCase(TorchChecks)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pure", action="store_true", help="Run only standard-library checks; does not pass Torch admission")
    parser.add_argument("--output", type=Path, help="Write a new explicit code-bound CPU gate JSON, including NOT_RUN/failure")
    args = parser.parse_args(argv)
    def emit_report(status, pure_result, actual_result=None, **extra):
        report = dict(schema="AIC_NATIVE_PREFERENCE_TORCH_CPU_CHECKS_V1", status=status,
                      checks=pure_result.testsRun + (actual_result.testsRun if actual_result else 0),
                      pure_checks=pure_result.testsRun, torch_checks=actual_result.testsRun if actual_result else 0,
                      pure_passed=pure_result.wasSuccessful(),
                      torch_passed=actual_result.wasSuccessful() if actual_result else False,
                      device="cpu", model_downloads=0, qwen_forwards=0,
                      code_refs=dict(runtime=reference(Path(__file__).with_name("runtime.py")),
                                     torch_checks=reference(Path(__file__))), **extra)
        if args.output is not None:
            save_new(args.output, report)
        print(json.dumps(report, allow_nan=False))
    pure = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(PureChecks))
    if not pure.wasSuccessful():
        emit_report("FAIL", pure, reason="STANDARD_LIBRARY_CHECK_FAILED")
        return 1
    if args.pure:
        emit_report("NOT_RUN", pure, reason="PURE_ONLY_TORCH_GATE_NOT_RUN")
        return 0
    if importlib.util.find_spec("torch") is None:
        emit_report("NOT_RUN", pure, reason="TORCH_UNAVAILABLE", required_linux_torch_gate="NOT_PASSED")
        return 77
    import torch
    torch.set_num_threads(1)
    actual = unittest.TextTestRunner(verbosity=2).run(torch_suite(torch))
    emit_report("PASS" if actual.wasSuccessful() else "FAIL", pure, actual, torch_version=torch.__version__)
    return 0 if actual.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
