"""CPU/NumPy protocol checks and explicitly synthetic generation call checks.

No Torch, Qwen, tokenizer download or private input is needed.  These tests
cannot pass the separate real-Torch CPU admission gate.
"""
from __future__ import annotations

from contextlib import nullcontext
import hashlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np

from . import runtime


class _ArrayCarrier:
    """A transport-only stand-in; this is not advertised as a Torch tensor."""

    def __init__(self, values):
        self.array = np.asarray(values)

    @property
    def shape(self):
        return self.array.shape

    @property
    def ndim(self):
        return self.array.ndim

    def __getitem__(self, key):
        return _ArrayCarrier(self.array[key])

    def to(self, device):
        assert device == "cuda:0"
        return self

    def detach(self):
        return self

    def cpu(self):
        return self

    def tolist(self):
        return self.array.tolist()


class _Tokenizer:
    eos = 999

    def decode(self, ids, *, skip_special_tokens=False, clean_up_tokenization_spaces=False):
        assert skip_special_tokens is False and clean_up_tokenization_spaces is False
        return "".join("<|im_end|>" if value == self.eos else chr(value) for value in ids)


class _Constraint:
    def __init__(self, prompt_length, events):
        self.prompt_length = prompt_length
        self.eos_token_ids = frozenset({_Tokenizer.eos})
        self.grammar = SimpleNamespace(allow_empty=True, max_segments=6)
        self.stats = {"synthetic": True}
        self.events = events

    def __call__(self, *args):
        return [_Tokenizer.eos]

    def assert_complete(self, ids):
        self.events.append(("constraint_validated", {}))
        return json.loads(_Tokenizer().decode(ids[:-1]))


def numpy_values(grid=((4, 2, 2), (3, 2, 4))):
    grid = np.asarray(grid, dtype=np.int64)
    count = int(np.prod(grid, axis=1).sum())
    pixels = np.arange(count * 1536, dtype=np.float32).reshape(count, 1536) / np.float32(1024)
    return dict(input_ids=np.array([[7, 8]], dtype=np.int64),
                attention_mask=np.ones((1, 2), dtype=np.int64),
                pixel_values_videos=pixels, video_grid_thw=grid)


class PureRuntimeChecks(unittest.TestCase):
    def test_projection_matches_independent_scalar_bucket_sum(self):
        value = np.sin(np.arange(4096, dtype=np.float32) / np.float32(17))
        actual = runtime.project_numpy(value)
        expected = []
        for bucket in range(128):
            subtotal = np.float32(0)
            for index in range(bucket, 4096, 128):
                raw = hashlib.sha256(f"AIC_CONTENT_CHOICE_PROJECTION_V1:20261019:{index}".encode()).digest()
                signed = value[index] if raw[0] & 1 else -value[index]
                subtotal = np.float32(subtotal + signed)
            expected.append(np.float32(subtotal / np.float32(np.sqrt(32))))
        np.testing.assert_array_equal(actual, np.asarray(expected, dtype=np.float32))
        self.assertEqual(actual.shape, (128,))
        self.assertEqual(actual.dtype, np.float32)

    def test_projection_is_fixed_linear_and_bucket_normalized(self):
        signs = np.asarray(runtime.projection_signs(), dtype=np.float32)
        # Every signed contribution is +1, with exactly 32 entries per bucket.
        np.testing.assert_array_equal(runtime.project_numpy(signs),
                                      np.full(128, np.float32(32) / np.float32(np.sqrt(32)), dtype=np.float32))
        unit = np.zeros(4096, dtype=np.float32)
        unit[139] = signs[139]
        projected = runtime.project_numpy(unit)
        self.assertEqual(np.flatnonzero(projected).tolist(), [11])
        self.assertEqual(projected[11], np.float32(1) / np.float32(np.sqrt(32)))
        np.testing.assert_array_equal(runtime.project_numpy(-unit), -projected)
        self.assertEqual(runtime.projection_spec()["learned_parameters"], 0)

    def test_projection_rejects_wrong_dimension_dtype_and_nonfinite(self):
        for value in (np.zeros(4095, dtype=np.float32), np.zeros((1, 4096), dtype=np.float32),
                      np.zeros(4096, dtype=np.int64), [0.0] * 4096):
            with self.assertRaises(ValueError):
                runtime.project_numpy(value)
        for bad in (np.nan, np.inf, -np.inf):
            value = np.zeros(4096, dtype=np.float32)
            value[17] = bad
            with self.assertRaisesRegex(ValueError, "finite"):
                runtime.project_numpy(value)

    def test_projection_does_not_depend_on_numpy_rng_or_modify_input(self):
        rng = np.random.RandomState(77)
        values = rng.normal(size=4096).astype(np.float32)
        before = values.copy()
        state = np.random.get_state()
        first = runtime.project_numpy(values)
        np.testing.assert_array_equal(values, before)
        after = np.random.get_state()
        self.assertEqual(state[0], after[0])
        np.testing.assert_array_equal(state[1], after[1])
        self.assertEqual(state[2:], after[2:])
        np.random.seed(212)
        np.testing.assert_array_equal(first, runtime.project_numpy(values))
        np.random.set_state(state)

    def test_temporal_permutation_keeps_two_views_and_whole_patch_vectors(self):
        values = numpy_values()
        before = {key: value.copy() for key, value in values.items()}
        actual = runtime.permute_visual(values)
        expected_rows = list(range(8, 16)) + list(range(8)) + list(range(32, 40)) + list(range(16, 32))
        np.testing.assert_array_equal(actual["pixel_values_videos"], before["pixel_values_videos"][expected_rows])
        self.assertFalse(np.shares_memory(actual["pixel_values_videos"], values["pixel_values_videos"]))
        for name in values:
            np.testing.assert_array_equal(values[name], before[name])
            self.assertEqual(values[name].shape, actual[name].shape)
            if name != "pixel_values_videos":
                self.assertIs(actual[name], values[name], name)
        self.assertEqual(sorted(expected_rows), list(range(40)))

    def test_single_group_view_is_identity_other_view_still_rotates(self):
        values = numpy_values(((1, 2, 2), (2, 2, 2)))
        actual = runtime.permute_visual(values)["pixel_values_videos"]
        expected = values["pixel_values_videos"][[0, 1, 2, 3, 8, 9, 10, 11, 4, 5, 6, 7]]
        np.testing.assert_array_equal(actual, expected)
        self.assertEqual([row["shift_groups"] for row in runtime.permutation_plan(values["video_grid_thw"])], [0, 1])

    def test_permutation_rejects_partial_groups_wrong_fields_and_nonfinite(self):
        values = numpy_values()
        for grid in ([[0, 2, 2], [3, 2, 4]], [[4, 3, 2], [3, 2, 4]],
                     [[4, 2, 2]], [[True, 2, 2], [3, 2, 4]], [[4.0, 2, 2], [3, 2, 4]]):
            with self.assertRaises(ValueError):
                runtime.permutation_plan(grid)
        with self.assertRaisesRegex(ValueError, "four native"):
            runtime.permute_visual(dict(values, extra="not a native field"))
        with self.assertRaisesRegex(ValueError, "exactly match"):
            runtime.permute_visual(dict(values, pixel_values_videos=values["pixel_values_videos"][:-1]))
        wrong = values["pixel_values_videos"].copy()
        wrong[0, 0] = np.nan
        with self.assertRaisesRegex(ValueError, "Finite"):
            runtime.permute_visual(dict(values, pixel_values_videos=wrong))

    def test_eos_state_is_before_eos_and_after_all_answer_content(self):
        self.assertEqual(runtime.eos_feature_position(7, 3), 8)
        self.assertEqual(runtime.eos_feature_position(7, 1), 6)
        for prefix, suffix in ((0, 3), (7, 0), (True, 3), (7, 3.0)):
            with self.assertRaises(ValueError):
                runtime.eos_feature_position(prefix, suffix)

    def _synthetic_runtime(self, directory, sequence, events, *, error=None):
        spec = dict(model_dir=directory, revision="synthetic-no-model", base_sha256="1" * 64,
                    adapter_weights={"path": directory + "/adapter_model.safetensors", "sha256": "2" * 64},
                    adapter_config={"path": directory + "/adapter_config.json", "sha256": "3" * 64})
        obj = runtime.QwenChoiceRuntime(spec, on_event=lambda kind, payload: events.append((kind, payload)))
        calls = []

        def generate(**kwargs):
            calls.append(kwargs)
            if error is not None:
                raise error
            return SimpleNamespace(sequences=_ArrayCarrier([sequence]))

        obj.model = SimpleNamespace(generate=generate, parameters=lambda: (), training=False)
        obj.torch = SimpleNamespace(inference_mode=nullcontext)
        obj.tokenizer, obj.eos, obj.mode = _Tokenizer(), 999, "original_TIME"
        obj._values = lambda values: values
        obj._inference_mode = lambda: None
        values = {"input_ids": _ArrayCarrier([[80, 58]])}
        values.update({key: _ArrayCarrier([[1]]) for key in
                       ("attention_mask", "pixel_values_videos", "video_grid_thw")})
        return obj, values, calls

    def test_single_sample_records_raw_before_validation_and_passes_fixed_options(self):
        answer = '{"segments":[]}'
        suffix = list(map(ord, answer)) + [999]
        events, rng_seeds = [], []
        with tempfile.TemporaryDirectory() as directory:
            obj, values, calls = self._synthetic_runtime(directory, [80, 58] + suffix, events)
            constraint = _Constraint(2, events)
            with patch.object(runtime, "sampled_rng", side_effect=lambda _torch, seed: (rng_seeds.append(seed), nullcontext())[1]), \
                 patch.object(runtime, "tensor_signature", return_value={"synthetic": "four-tensor-binding"}):
                result = obj.generate_sample(values, constraint, 131)
        self.assertEqual(rng_seeds, [131])
        self.assertEqual(len(calls), 1)
        for key, value in dict(do_sample=True, temperature=.8, top_p=.9, top_k=0, typical_p=1.,
                               repetition_penalty=1., num_beams=1, num_return_sequences=1,
                               max_new_tokens=512, use_cache=True, eos_token_id=999).items():
            self.assertEqual(calls[0][key], value, key)
        self.assertIs(calls[0]["prefix_allowed_tokens_fn"], constraint)
        self.assertEqual([event[0] for event in events], ["generation_raw", "constraint_validated"])
        self.assertEqual(events[0][1]["raw_text"], answer + "<|im_end|>")
        self.assertEqual(result["text"], answer)
        self.assertTrue(result["eos"])
        self.assertEqual(result["ids"], suffix)
        self.assertEqual(result["counts"]["samples_completed"], 1)
        self.assertEqual(result["counts"]["optimizer_steps"], 0)

    def test_truncated_json_with_no_actual_eos_fails_after_raw_and_never_becomes_empty(self):
        suffix = list(map(ord, '{"segments":[]}'))
        events = []
        with tempfile.TemporaryDirectory() as directory:
            obj, values, calls = self._synthetic_runtime(directory, [80, 58] + suffix, events)
            with patch.object(runtime, "sampled_rng", return_value=nullcontext()), \
                 patch.object(runtime, "tensor_signature", return_value={}):
                with self.assertRaisesRegex(ValueError, "exactly one actual EOS"):
                    obj.generate_sample(values, _Constraint(2, events), 8)
        self.assertEqual(len(calls), 1)
        self.assertEqual([event[0] for event in events], ["generation_raw"])
        self.assertEqual(events[0][1]["ids"], suffix)
        self.assertEqual(obj.counts["sample_generation_calls"], 1)
        self.assertEqual(obj.counts["samples_completed"], 0)

    def test_generation_exception_is_recorded_once_without_retry(self):
        events = []
        with tempfile.TemporaryDirectory() as directory:
            obj, values, calls = self._synthetic_runtime(directory, [], events, error=RuntimeError("synthetic model failure"))
            with patch.object(runtime, "sampled_rng", return_value=nullcontext()):
                with self.assertRaisesRegex(RuntimeError, "synthetic model failure"):
                    obj.generate_sample(values, _Constraint(2, events), 8)
        self.assertEqual(len(calls), 1)
        self.assertEqual([event[0] for event in events], ["generation_exception"])
        self.assertEqual(obj.counts["generations_completed"], 0)

    def test_rng_setup_failure_is_not_counted_as_a_model_call(self):
        events = []
        with tempfile.TemporaryDirectory() as directory:
            obj, values, calls = self._synthetic_runtime(directory, [], events)
            with patch.object(runtime, "sampled_rng", side_effect=RuntimeError("synthetic RNG setup failure")):
                with self.assertRaisesRegex(RuntimeError, "RNG setup failure"):
                    obj.generate_sample(values, _Constraint(2, events), 8)
        self.assertEqual(calls, [])
        self.assertEqual(obj.counts["generation_calls"], 0)
        self.assertEqual([event[0] for event in events], ["generation_exception"])
        self.assertIs(events[0][1]["actual_model_call"], False)

    def test_duplicate_eos_and_changed_prefix_both_preserve_raw_then_fail(self):
        suffix = list(map(ord, '{"segments":[]}')) + [999]
        for sequence, message in (([80, 58] + suffix + [999], "exactly one actual EOS"),
                                  ([81, 58] + suffix, "changed the actual input prefix")):
            events = []
            with tempfile.TemporaryDirectory() as directory:
                obj, values, calls = self._synthetic_runtime(directory, sequence, events)
                with patch.object(runtime, "sampled_rng", return_value=nullcontext()), \
                     patch.object(runtime, "tensor_signature", return_value={}):
                    with self.assertRaisesRegex(ValueError, message):
                        obj.generate_sample(values, _Constraint(2, events), 8)
            self.assertEqual(len(calls), 1)
            self.assertEqual([event[0] for event in events], ["generation_raw"])
            self.assertEqual(obj.counts["samples_completed"], 0)

    def test_invalid_seed_or_constraint_fails_before_any_generation(self):
        with tempfile.TemporaryDirectory() as directory:
            obj, values, calls = self._synthetic_runtime(directory, [], [])
            constraint = _Constraint(2, [])
            for seed in (True, -1, 1 << 63, 1.5):
                with self.assertRaisesRegex(ValueError, "Sampling seed"):
                    obj.generate_sample(values, constraint, seed)
            constraint.grammar.allow_empty = False
            with self.assertRaisesRegex(ValueError, "allow-empty"):
                obj.generate_sample(values, constraint, 1)
            self.assertEqual(calls, [])
            self.assertEqual(obj.counts["generation_calls"], 0)

    def test_no_training_checkpoint_or_reference_cache_entry_point(self):
        obj = object.__new__(runtime.QwenChoiceRuntime)
        for method in (obj.train_pairs, obj.cache_reference, obj.save_policy, obj.load_policy):
            with self.assertRaises(ValueError):
                method()

    def test_frozen_guard_rejects_pending_training_or_any_update(self):
        with tempfile.TemporaryDirectory() as directory:
            obj, _, _ = self._synthetic_runtime(directory, [], [])
            obj._assert_frozen_state()
            for name in ("backward_calls", "backwards_completed", "optimizer_steps"):
                obj.counts[name] = 1
                with self.assertRaisesRegex(ValueError, "zero backward/updates"):
                    obj._assert_frozen_state()
                obj.counts[name] = 0
            obj.trained = True
            with self.assertRaises(ValueError):
                obj._assert_frozen_state()

    def test_identity_counts_original_time_once_and_binds_both_runtime_files(self):
        with tempfile.TemporaryDirectory() as directory:
            obj, _, _ = self._synthetic_runtime(directory, [], [])
            obj.versions, obj.video_token = {"scope": "SYNTHETIC_IDENTITY_CHECK"}, 17
            identity = obj.identity()
        self.assertEqual(identity["conservative_full_pipeline_parameters"], 8_782_557_449)
        self.assertEqual(identity["optimizer_updates"], 0)
        self.assertEqual(identity["active_weights"], "ORIGINAL_TIME_UNCHANGED")
        self.assertEqual(identity["runtime_source_sha256"], hashlib.sha256(Path(runtime.__file__).read_bytes()).hexdigest())
        self.assertEqual(identity["inherited_runtime"]["sha256"], hashlib.sha256(Path(runtime.inherited.__file__).read_bytes()).hexdigest())

    def test_gate_rejects_missing_torch_even_with_all_pure_checks_passed(self):
        from . import torch_checks
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic_not_run.json"
            path.write_text(json.dumps(dict(schema=torch_checks.SCHEMA, status="NOT_RUN",
                pure_passed=True, torch_passed=False, reason="TORCH_UNAVAILABLE")), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "CPU Torch checks must PASS"):
                torch_checks.validate_report(path)

    def test_gate_rejects_stale_observation_dependency_bytes(self):
        from . import torch_checks
        names = torch_checks.pure_test_names()
        synthetic = dict(schema=torch_checks.SCHEMA, status="PASS", pure_passed=True, torch_passed=True,
            device="cpu", qwen_forwards=0, model_downloads=0, pure_test_names=names,
            torch_test_names=torch_checks.TORCH_TEST_NAMES, pure_checks=len(names),
            torch_checks=len(torch_checks.TORCH_TEST_NAMES), checks=len(names) + len(torch_checks.TORCH_TEST_NAMES),
            skipped_checks=0, failed_checks=0, code_refs=torch_checks.code_refs())
        synthetic["code_refs"]["inherited_summary_contract"]["sha256"] = "0" * 64
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "synthetic_stale_gate.json"
            path.write_text(json.dumps(synthetic), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Reference bytes changed"):
                torch_checks.validate_report(path)


if __name__ == "__main__":
    unittest.main()
