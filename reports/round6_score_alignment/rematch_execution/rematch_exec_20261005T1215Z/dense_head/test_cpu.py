#!/usr/bin/env python3
"""CPU logic regressions with toy modules; never claimed as real Qwen validation."""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

import torch
from torch import nn
from torch.nn import functional as F
from torch.utils.checkpoint import checkpoint

from dense_time import (DenseTimeHead, DenseTimeModel, EXPECTED_HEAD, UpdateCounters,
                        accumulation_update, fingerprint_parameters, masked_bce_sum,
                        parameter_inventory, query_markers, resolve_queries, unique_parameters)
from grid_targets import grid_targets_from_source_frames
from probe_8b import compare_gradients, verify_receipt


class CharacterTokenizer:
    def __len__(self):
        return 2048

    def encode(self, text, add_special_tokens=False):
        assert not add_special_tokens
        return [ord(c) for c in text]


class ToyLoRA(nn.Module):
    def __init__(self, width):
        super().__init__()
        self.base_layer = nn.Linear(width, width, bias=False)
        self.base_layer.weight.requires_grad_(False)
        self.lora_A = nn.Linear(width, 2, bias=False)
        self.lora_B = nn.Linear(2, width, bias=False)
        nn.init.zeros_(self.lora_B.weight)
        self.disabled = False
        self.merged = False

    def forward(self, x):
        return self.base_layer(x) + (0 if self.disabled else self.lora_B(self.lora_A(x)))


class ToyCore(nn.Module):
    def __init__(self, width=8):
        super().__init__()
        self.embed_tokens = nn.Embedding(32, width)
        self.visual = nn.Linear(3, width, bias=False)
        self.projections = nn.ModuleList([ToyLoRA(width) for _ in range(4)])
        for p in self.embed_tokens.parameters():
            p.requires_grad_(False)
        for p in self.visual.parameters():
            p.requires_grad_(False)
        self.rope_deltas = None

    def forward(self, input_ids, attention_mask, pixel_values_videos, use_cache,
                output_hidden_states, output_attentions, return_dict):
        assert not use_cache and not output_hidden_states and not output_attentions and return_dict
        frozen_input = self.embed_tokens(input_ids)
        frozen_input = frozen_input + self.visual(pixel_values_videos).unsqueeze(1)
        def block(x):
            return torch.tanh(sum(layer(x) for layer in self.projections)).cumsum(1)
        states = checkpoint(block, frozen_input, use_reentrant=False) if self.training else block(frozen_input)
        self.rope_deltas = torch.tensor([123])
        return SimpleNamespace(last_hidden_state=states, past_key_values=None, hidden_states=None)


class ToyBase(nn.Module):
    def __init__(self):
        super().__init__()
        self.model = ToyCore()
        self.lm_head = nn.Linear(8, 32, bias=False)
        # Shared embedding/head tensor must be counted once.
        self.lm_head.weight = self.model.embed_tokens.weight

    def forward(self, *args, **kwargs):
        raise RuntimeError("dense path must bypass LM forward/logits")


class ToyPeft(nn.Module):
    def __init__(self):
        super().__init__()
        self.base = ToyBase()

    def get_base_model(self):
        return self.base

    @contextmanager
    def disable_adapter(self):
        layers = self.base.model.projections
        for layer in layers:
            layer.disabled = True
        try:
            yield
        finally:
            for layer in layers:
                layer.disabled = False


class CpuTests(unittest.TestCase):
    def setUp(self):
        torch.manual_seed(20261005)

    def make_model(self):
        model = DenseTimeModel(ToyPeft(), hidden_size=8)
        encoded = {"input_ids": torch.tensor([[1, 2, 3, 4, 5, 6]]),
                   "attention_mask": torch.ones(1, 6, dtype=torch.long),
                   "pixel_values_videos": torch.tensor([[0.2, 0.4, 0.7]])}
        positions = torch.tensor([[3, 4, 5]])
        return model, encoded, positions

    def test_head_count(self):
        self.assertEqual(sum(p.numel() for p in DenseTimeHead().parameters()), EXPECTED_HEAD)

    def test_exact_gradient_diagnostic_and_math_backend_api(self):
        from torch.nn.attention import SDPBackend, sdpa_kernel
        original = {"a": torch.tensor([1.0, 2.0]), "b": torch.zeros(2)}
        self.assertTrue(compare_gradients(original, original, torch)["all_exact_equal"])
        altered = {"a": original["a"] + 0.01, "b": original["b"]}
        comparison = compare_gradients(original, altered, torch)
        self.assertFalse(comparison["all_exact_equal"])
        self.assertEqual(comparison["different_tensor_count"], 1)
        self.assertGreater(comparison["max_abs_diff"], 0)
        self.assertFalse(compare_gradients({"a": None}, {"a": None}, torch)["all_exact_equal"])
        values = torch.randn(1, 2, 3, 4, requires_grad=True)
        with sdpa_kernel(backends=[SDPBackend.MATH]):
            result = F.scaled_dot_product_attention(values, values, values)
            result.sum().backward()
        self.assertTrue(torch.isfinite(values.grad).all())

    def test_downloading_metadata_receipt_and_full_load_fail_closed(self):
        from dense_time import MODEL_ID, REVISION
        with tempfile.TemporaryDirectory(prefix="receipt_test_", dir=Path(__file__).parent) as task_dir:
            root = Path(task_dir)
            model_dir = root / "model"
            model_dir.mkdir()
            completed = []
            for name in ("config.json", "tokenizer.json", "tokenizer_config.json",
                         "preprocessor_config.json", "video_preprocessor_config.json"):
                data = b"{}\n"
                (model_dir / name).write_bytes(data)
                completed.append({"name": name, "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
                                  "official_content_hash": hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest(),
                                  "verification": "git_blob_sha1"})
            receipt = {"status": "DOWNLOADING", "repo": MODEL_ID, "revision": REVISION, "completed": completed}
            receipt_path = root / "receipt.json"
            receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
            self.assertTrue(verify_receipt(model_dir, receipt_path, metadata_only=True)["metadata_only"])
            with self.assertRaises(RuntimeError):
                verify_receipt(model_dir, receipt_path)
            receipt["status"] = "COMPLETE_HASH_VERIFIED"
            receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
            with self.assertRaises(RuntimeError):
                verify_receipt(model_dir, receipt_path)
            receipt["model_path"] = str(root / "other")
            receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
            with self.assertRaises(RuntimeError):
                verify_receipt(model_dir, receipt_path, metadata_only=True)
            receipt["model_path"] = str(model_dir)
            receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
            (model_dir / "config.json").write_bytes(b"bad")
            with self.assertRaises(RuntimeError):
                verify_receipt(model_dir, receipt_path, metadata_only=True)

    def test_processor_expansion_indices_and_fail_closed(self):
        tokenizer = CharacterTokenizer()
        suffix = tokenizer.encode("\n" + "".join(query_markers(3)))
        contracts = []
        for expanded_length in (10, 31):
            ids = [1000] * expanded_length + suffix + [1001]
            encoded = {"input_ids": torch.tensor([ids]), "attention_mask": torch.ones(1, len(ids), dtype=torch.long)}
            contracts.append(resolve_queries(encoded, tokenizer, 3, 1000))
        self.assertEqual([b - a for a, b in zip(contracts[0].positions, contracts[1].positions)], [21] * 3)
        self.assertTrue(all(p > contracts[1].last_video_position for p in contracts[1].positions))
        variants = [suffix + [1000], [1000] + suffix[:-5], [1000] + suffix + suffix]
        for ids in variants:
            encoded = {"input_ids": torch.tensor([ids]), "attention_mask": torch.ones(1, len(ids), dtype=torch.long)}
            with self.assertRaises(ValueError):
                resolve_queries(encoded, tokenizer, 3, 1000)
        encoded = {"input_ids": torch.tensor([[1000] + suffix]),
                   "attention_mask": torch.tensor([[1] + [0] * len(suffix)])}
        with self.assertRaises(ValueError):
            resolve_queries(encoded, tokenizer, 3, 1000)

    def test_grid_source_replay_coverage_edges_unknown_padding(self):
        result = grid_targets_from_source_frames(list(range(8)), [i / 2 for i in range(8)],
                                                 [(i + 1) / 2 for i in range(8)],
                                                 [1, 1, -1, -1, 0, 1, 0, 0],
                                                 [(i, i + 1) for i in range(5)], [(0.25, 3.0)])
        self.assertEqual(result["known_mask"].tolist(), [[False, False, True, False, False]])
        self.assertEqual(result["targets"][0, 2].item(), 0.5)
        self.assertEqual(result["replay"][2]["source_frame_ids"], [4, 5])
        with self.assertRaises(ValueError):
            grid_targets_from_source_frames([0, 2], [0, 1], [1, 2], [1, 1], [(0, 2)], [(0, 2)])

    def test_unknown_labels_never_enter_bce_or_gradient(self):
        logits = torch.tensor([[0.3, -0.7, 0.8]], requires_grad=True)
        mask = torch.tensor([[True, False, True]])
        losses, gradients = [], []
        for unknown in (float("nan"), -999.0, 999.0):
            logits.grad = None
            loss, count = masked_bce_sum(logits, torch.tensor([[1.0, unknown, 0.25]]), mask)
            self.assertEqual(count, 2)
            loss.backward()
            losses.append(loss.detach().clone())
            gradients.append(logits.grad.clone())
        self.assertTrue(all(torch.equal(losses[0], x) for x in losses))
        self.assertTrue(all(torch.equal(gradients[0], x) for x in gradients))
        self.assertEqual(gradients[0][0, 1].item(), 0.0)

    def test_accumulation_denominator_and_unknown_skip(self):
        model = nn.Linear(1, 1, bias=False)
        optimizer = torch.optim.AdamW(model.parameters(), lr=0.01)
        scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lambda _: 1.0)
        counter = UpdateCounters()
        a = {"x": torch.tensor([[0.2], [0.4]]), "targets": torch.tensor([[1.0], [float("nan")]]),
             "known_mask": torch.tensor([[True], [False]])}
        b = {"x": torch.tensor([[0.6], [0.8], [1.0]]), "targets": torch.tensor([[0.0], [0.5], [1.0]]),
             "known_mask": torch.ones(3, 1, dtype=torch.bool)}
        all_x = torch.cat((a["x"][:1], b["x"]))
        all_targets = torch.cat((a["targets"][:1], b["targets"]))
        F.binary_cross_entropy_with_logits(model(all_x), all_targets).backward()
        reference = model.weight.grad.clone()
        captured = []
        accumulation_update(model, [a, b], optimizer, scheduler, counter, lambda batch: model(batch["x"]),
                            before_step=lambda: captured.append(model.weight.grad.clone()), clip_norm=100)
        self.assertTrue(torch.allclose(captured[0], reference, atol=1e-7, rtol=1e-6))
        step, epoch, weight = float(optimizer.state[model.weight]["step"]), scheduler.last_epoch, model.weight.detach().clone()
        unknown = {"targets": torch.full((2, 1), float("nan")), "known_mask": torch.zeros(2, 1, dtype=torch.bool)}
        result = accumulation_update(model, [unknown, unknown], optimizer, scheduler, counter,
                                     lambda _: self.fail("UNKNOWN accumulation called forward"))
        self.assertEqual(result["status"], "SKIP_ALL_UNKNOWN")
        self.assertEqual(float(optimizer.state[model.weight]["step"]), step)
        self.assertEqual(scheduler.last_epoch, epoch)
        self.assertTrue(torch.equal(model.weight, weight))
        self.assertEqual(counter.optimizer_steps, 1)
        self.assertEqual(counter.known_cells_seen, 4)

    def test_lora_checkpoint_updates_frozen_base_and_restore(self):
        model, encoded, positions = self.make_model()
        model.eval()
        with model.spatial_base() as base:
            self.assertFalse(model.head_enabled)
            reference = base.model(**encoded, use_cache=False, output_hidden_states=False,
                                   output_attentions=False, return_dict=True).last_hidden_state.detach().clone()
        frozen = fingerprint_parameters(model.backbone, lambda n, p: "lora_" not in n)
        before = {n: p.detach().clone() for n, p in unique_parameters(model) if p.requires_grad}
        optimizer = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=0.01, weight_decay=0)
        batch = {"targets": torch.tensor([[1.0, float("nan"), 0.0]]),
                 "known_mask": torch.tensor([[True, False, True]])}
        counters, evidence = UpdateCounters(), []
        model.train()
        def capture():
            record = {n: int(torch.count_nonzero(p.grad)) for n, p in unique_parameters(model) if p.requires_grad}
            evidence.append(record)
        for _ in range(3):
            accumulation_update(model, [batch], optimizer, None, counters,
                                lambda b: model(encoded, positions), before_step=capture)
        self.assertTrue(all(v == 0 for n, v in evidence[0].items() if "lora_A" in n))
        self.assertTrue(any(v > 0 for n, v in evidence[0].items() if "lora_B" in n))
        self.assertTrue(any(v > 0 for n, v in evidence[1].items() if "lora_A" in n))
        for kind in ("head.", "lora_A", "lora_B"):
            self.assertTrue(any(kind in n and not torch.equal(before[n], p) for n, p in unique_parameters(model) if p.requires_grad))
        self.assertEqual(frozen, fingerprint_parameters(model.backbone, lambda n, p: "lora_" not in n))
        model.external_caches["bad_prior_window"] = object()
        with model.spatial_base() as base:
            restored = base.model(**encoded, use_cache=False, output_hidden_states=False,
                                  output_attentions=False, return_dict=True).last_hidden_state.detach()
            self.assertTrue(torch.equal(reference, restored))
            self.assertEqual(model.external_caches, {})
            with self.assertRaises(RuntimeError):
                model(encoded, positions)
        self.assertIsNone(model.backbone.base.model.rope_deltas)
        self.assertTrue(model.head_enabled)

    def test_model_masked_gradient_invariance_and_visual_sensitivity(self):
        model, encoded, positions = self.make_model()
        model.eval()
        results = []
        for value in (float("nan"), -999.0):
            model.zero_grad(set_to_none=True)
            labels = torch.tensor([[1.0, value, 0.0]])
            loss, _ = masked_bce_sum(model(encoded, positions), labels, torch.tensor([[True, False, True]]))
            loss.backward()
            results.append((float(loss), {n: p.grad.detach().clone() for n, p in unique_parameters(model) if p.requires_grad}))
        self.assertEqual(results[0][0], results[1][0])
        self.assertTrue(all(torch.equal(results[0][1][n], results[1][1][n]) for n in results[0][1]))
        mismatch = dict(encoded)
        mismatch["pixel_values_videos"] = torch.tensor([[0.7, 0.1, -0.4]])
        with torch.no_grad():
            self.assertGreater(float((model(encoded, positions) - model(mismatch, positions)).abs().max()), 0)

    def test_shared_inventory_and_no_merge(self):
        model, encoded, positions = self.make_model()
        inventory = parameter_inventory(model.backbone, model.head, enforce_expected=False)
        self.assertTrue(inventory["shared_parameter_aliases"])
        self.assertEqual(inventory["total"], sum(p.numel() for p in model.parameters()))
        model.backbone.base.model.projections[0].merged = True
        with self.assertRaises(RuntimeError):
            with model.spatial_base():
                pass


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(CpuTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = {"status": "PASS_CPU_LOGIC_ONLY" if result.wasSuccessful() else "FAIL_CPU_LOGIC_ONLY",
              "tests_run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
              "torch": torch.__version__, "scope": "toy modules; no real processor/model, CUDA, downloads, media decode or official quality"}
    (Path(__file__).parent / "cpu_test_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    raise SystemExit(0 if result.wasSuccessful() else 1)
