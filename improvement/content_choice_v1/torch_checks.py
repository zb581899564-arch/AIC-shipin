"""Code-bound real CPU-Torch gate for frozen content choice.

This loads only tiny synthetic CPU tensors, never Qwen or a CUDA model.  Run
``python -m improvement.content_choice_v1.torch_checks --output /abs/gate.json``.
Missing Torch produces NOT_RUN and exit 77.  NumPy/synthetic call checks alone
do not pass admission for any GPU stage.
"""
from __future__ import annotations

import argparse
import importlib.metadata
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

import numpy as np

from improvement.native_preference_v1 import contracts as inherited_contracts
from improvement.native_preference_v1.contracts import checked, reference, require, save_new, strict_load

from . import contracts, observation, runtime
from .test_observation import PureObservationTests, TorchObservationTests
from .test_runtime import PureRuntimeChecks, numpy_values


SCHEMA = "AIC_CONTENT_CHOICE_TORCH_CPU_CHECKS_V1"
RUNTIME_TORCH_TEST_NAMES = sorted((
    "test_projection_cpu_matches_numpy_including_bfloat16_input",
    "test_permutation_real_cpu_tensors_preserves_all_original_bytes",
    "test_single_forward_full_suffix_sum_and_actual_eos_predicting_state",
    "test_feature_cannot_see_terminal_eos_but_sees_last_answer_token",
    "test_seeded_cpu_sampling_is_repeatable_and_rng_is_restored_on_error",
    "test_every_real_parameter_requires_frozen_state_and_absent_gradient",
    "test_fp32_adapter_byte_guard_and_cpu_checkpoint_reload",
    "test_wrong_actual_hidden_dimension_fails_before_vocabulary_head",
    "test_saved_changed_observation_reloads_and_rejects_prefix_damage_or_loss",
))
OBSERVATION_TORCH_TEST_NAMES = sorted((
    "test_real_tensor_pixel_layout_native_times_and_same_budget",
    "test_no_effect_returns_exact_original_four_tensors_and_plan",
    "test_pixel_identical_changed_pts_proposal_is_wholly_discarded",
    "test_tensor_temporal_copy_or_excerpt_scope_failure_is_rejected",
))
TORCH_TEST_NAMES = sorted(["runtime." + name for name in RUNTIME_TORCH_TEST_NAMES]
                          + ["observation." + name for name in OBSERVATION_TORCH_TEST_NAMES])


def code_refs():
    here = Path(__file__).resolve().parent
    improvement = here.parent
    return dict(runtime=reference(here / "runtime.py"),
                test_runtime=reference(here / "test_runtime.py"),
                torch_checks=reference(here / "torch_checks.py"),
                contracts=reference(Path(contracts.__file__)),
                verification=reference(here / "verification.py"),
                observation=reference(Path(observation.__file__)),
                test_observation=reference(here / "test_observation.py"),
                inherited_runtime=reference(Path(runtime.inherited.__file__)),
                inherited_contracts=reference(Path(inherited_contracts.__file__)),
                inherited_assets=reference(improvement / "native_preference_v1" / "assets.py"),
                inherited_inputs=reference(improvement / "native_preference_v1" / "inputs.py"),
                inherited_summary_contract=reference(improvement / "bottleneck_24h_v1" / "summary_contract.py"),
                inherited_summary_grammar=reference(improvement / "bottleneck_24h_v1" / "summary_grammar6.py"))


def pure_test_names():
    return sorted(["runtime." + name for name in unittest.defaultTestLoader.getTestCaseNames(PureRuntimeChecks)]
                  + ["observation." + name for name in unittest.defaultTestLoader.getTestCaseNames(PureObservationTests)])


def validate_report(path, workspace=None):
    """Require a complete genuine-Torch PASS for these exact current code bytes."""
    report = strict_load(path)
    pure_names = pure_test_names()
    require(report.get("schema") == SCHEMA and report.get("status") == "PASS"
            and report.get("pure_passed") is True and report.get("torch_passed") is True
            and report.get("device") == "cpu" and report.get("qwen_forwards") == 0
            and report.get("model_downloads") == 0
            and report.get("pure_test_names") == pure_names
            and report.get("torch_test_names") == TORCH_TEST_NAMES
            and type(report.get("pure_checks")) is int and report["pure_checks"] == len(pure_names)
            and type(report.get("torch_checks")) is int and report["torch_checks"] == len(TORCH_TEST_NAMES)
            and type(report.get("checks")) is int and report["checks"] == len(pure_names) + len(TORCH_TEST_NAMES)
            and report.get("skipped_checks") == 0 and report.get("failed_checks") == 0,
            "Actual current content-choice CPU Torch checks must PASS without skipped checks")
    expected = code_refs()
    require(isinstance(report.get("code_refs"), dict) and set(report["code_refs"]) == set(expected),
            "Torch gate must bind the complete runtime and test code dependency set")
    for key, value in expected.items():
        actual = report["code_refs"][key]
        checked(actual, workspace)
        require(actual == value, "Torch CPU gate belongs to another code version or path: " + key)
    try:
        installed = importlib.metadata.version("torch")
    except importlib.metadata.PackageNotFoundError as error:
        raise ValueError("Torch distribution is unavailable in this execution environment") from error
    require(report.get("torch_distribution_version") == installed,
            "Torch CPU gate belongs to a different installed Torch version")
    return reference(path)


def torch_suite(torch):
    """Construct runtime checks using actual CPU Torch operations, never mocks of Torch."""

    def tiny_native(width=runtime.HIDDEN_SIZE):
        class Core(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.embedding = torch.nn.Embedding(32, width)
                self.calls = 0
                self.last = None
                self.options = None

            def forward(self, *, input_ids, attention_mask, pixel_values_videos,
                        video_grid_thw, use_cache, return_dict):
                self.calls += 1
                self.options = dict(use_cache=use_cache, return_dict=return_dict)
                value = self.embedding(input_ids)
                denominator = torch.arange(1, value.shape[1] + 1, dtype=torch.float32)[None, :, None]
                # Causal states include each currently consumed token only.
                hidden = value.cumsum(1) / denominator
                self.last = hidden
                return SimpleNamespace(last_hidden_state=hidden)

        class Head(torch.nn.Linear):
            def __init__(self):
                super().__init__(width, 32, bias=False)
                self.calls = 0

            def forward(self, hidden):
                self.calls += 1
                return super().forward(hidden)

        with runtime.sampled_rng(torch, 783, device="cpu"):
            core, head = Core(), Head()
        runtime.inherited.freeze_except(core, ())
        runtime.inherited.freeze_except(head, ())
        core.eval()
        head.eval()
        return SimpleNamespace(model=core, lm_head=head)

    def values_for_score():
        values = numpy_values(((1, 2, 2), (1, 2, 2)))
        values["input_ids"] = np.asarray([[1, 2]], dtype=np.int64)
        return {key: torch.from_numpy(value.copy()) for key, value in values.items()}

    class TorchChecks(unittest.TestCase):
        def test_projection_cpu_matches_numpy_including_bfloat16_input(self):
            value = np.random.RandomState(133).normal(size=4096).astype(np.float32)
            for dtype in (torch.float32, torch.bfloat16):
                hidden = torch.tensor(value, dtype=dtype, requires_grad=True)
                expected = runtime.project_numpy(hidden.detach().float().numpy())
                actual = runtime.project_torch(torch, hidden)
                self.assertEqual(actual.dtype, torch.float32)
                self.assertEqual(tuple(actual.shape), (128,))
                self.assertFalse(actual.requires_grad)
                # Different CPU vector division kernels may differ by one ULP.
                np.testing.assert_allclose(actual.numpy(), expected, atol=5e-7, rtol=2e-7)

        def test_permutation_real_cpu_tensors_preserves_all_original_bytes(self):
            arrays = numpy_values()
            values = {key: torch.from_numpy(value.copy()) for key, value in arrays.items()}
            originals = {key: value.clone() for key, value in values.items()}
            actual = runtime.permute_visual(values)
            expected = runtime.permute_visual(arrays)
            for name in values:
                self.assertTrue(torch.equal(values[name].view(torch.uint8), originals[name].view(torch.uint8)), name)
                np.testing.assert_array_equal(actual[name].numpy(), expected[name])
                if name != "pixel_values_videos":
                    self.assertIs(actual[name], values[name])
            self.assertNotEqual(actual["pixel_values_videos"].data_ptr(), values["pixel_values_videos"].data_ptr())
            self.assertFalse(actual["pixel_values_videos"].requires_grad)

        def test_single_forward_full_suffix_sum_and_actual_eos_predicting_state(self):
            native, values, suffix = tiny_native(), values_for_score(), [3, 4, 31]
            result = runtime.teacher_forced_features(torch, native, values, suffix, device="cpu")
            self.assertEqual(native.model.calls, 1)
            self.assertEqual(native.lm_head.calls, 1)
            self.assertEqual(native.model.options, dict(use_cache=False, return_dict=True))
            hidden = native.model.last
            # Independent indexing: prefix length 2, targets at positions 1,2,3.
            logits = hidden[0, [1, 2, 3]].float() @ native.lm_head.weight.detach().float().T
            target_logp = torch.log_softmax(logits, dim=-1)[torch.arange(3), torch.tensor(suffix)]
            expected = float(target_logp.sum())
            self.assertAlmostEqual(result["logprob"], expected, places=5)
            self.assertNotAlmostEqual(result["logprob"], float(target_logp.mean()), places=3)
            self.assertEqual(result["suffix_tokens"], 3)
            self.assertEqual(result["feature_position"], 3)
            np.testing.assert_allclose(result["feature"], runtime.project_numpy(hidden[0, 3].float().numpy()), atol=5e-7, rtol=2e-7)
            self.assertGreater(float(np.max(np.abs(np.asarray(result["feature"]) -
                                                   runtime.project_numpy(hidden[0, 4].float().numpy())))), .01)
            self.assertTrue(all(parameter.grad is None and not parameter.requires_grad
                                for module in (native.model, native.lm_head) for parameter in module.parameters()))

        def test_feature_cannot_see_terminal_eos_but_sees_last_answer_token(self):
            native, values = tiny_native(), values_for_score()
            first = runtime.teacher_forced_features(torch, native, values, [3, 4, 31], device="cpu")
            last_state = native.model.last[0, -1].clone()
            with torch.no_grad():
                native.model.embedding.weight[31].add_(7.0)
            # Changing the consumed EOS embedding changes only the future state;
            # the EOS-predicting feature and every supervised causal logp stay equal.
            second = runtime.teacher_forced_features(torch, native, values, [3, 4, 31], device="cpu")
            self.assertEqual(first["feature"], second["feature"])
            self.assertEqual(first["logprob"], second["logprob"])
            self.assertFalse(torch.equal(last_state, native.model.last[0, -1]))
            third = runtime.teacher_forced_features(torch, native, values, [3, 5, 31], device="cpu")
            self.assertGreater(float(np.max(np.abs(np.asarray(first["feature"]) - np.asarray(third["feature"])))), .01)

        def test_seeded_cpu_sampling_is_repeatable_and_rng_is_restored_on_error(self):
            before = torch.get_rng_state().clone()
            with runtime.sampled_rng(torch, 739, device="cpu"):
                first = torch.multinomial(torch.tensor([.1, .2, .3, .4]), 100, replacement=True)
            self.assertTrue(torch.equal(torch.get_rng_state(), before))
            with runtime.sampled_rng(torch, 739, device="cpu"):
                second = torch.multinomial(torch.tensor([.1, .2, .3, .4]), 100, replacement=True)
            self.assertTrue(torch.equal(first, second))
            with runtime.sampled_rng(torch, 740, device="cpu"):
                third = torch.multinomial(torch.tensor([.1, .2, .3, .4]), 100, replacement=True)
            self.assertFalse(torch.equal(first, third))
            with self.assertRaisesRegex(RuntimeError, "intentional CPU exception"):
                with runtime.sampled_rng(torch, 741, device="cpu"):
                    torch.rand(100)
                    raise RuntimeError("intentional CPU exception")
            self.assertTrue(torch.equal(torch.get_rng_state(), before))

        def test_every_real_parameter_requires_frozen_state_and_absent_gradient(self):
            model = tiny_native().model
            obj = object.__new__(runtime.QwenChoiceRuntime)
            obj.model, obj.torch = model, torch
            obj.training = obj.trained = False
            obj._saved_identity = None
            obj.counts = dict(backward_calls=0, backwards_completed=0, optimizer_steps=0)
            obj._assert_frozen_state()
            parameter = next(model.parameters())
            parameter.requires_grad_(True)
            with self.assertRaisesRegex(ValueError, "Every base and TIME parameter"):
                obj._assert_frozen_state()
            parameter.requires_grad_(False)
            parameter.grad = torch.zeros_like(parameter)
            with self.assertRaisesRegex(ValueError, "Every base and TIME parameter"):
                obj._assert_frozen_state()
            self.assertIsNotNone(parameter.grad, "The guard must reject, not silently erase a pending gradient")

        def test_fp32_adapter_byte_guard_and_cpu_checkpoint_reload(self):
            source = {f"layer.{index}.lora_A.weight": torch.tensor([[.012345678 + index / 1000]], dtype=torch.float32)
                      for index in range(288)}
            state = {name: value.clone() for name, value in source.items()}
            self.assertEqual(runtime.assert_original_adapter_unchanged(torch, state, source), 0)
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "tiny_original.pt"
                torch.save(state, path)
                reloaded = torch.load(path, map_location="cpu", weights_only=True)
            self.assertEqual(runtime.assert_original_adapter_unchanged(torch, reloaded, source), 0)
            first = next(iter(state))
            reloaded[first].view(torch.uint8)[0, 0] ^= 1
            with self.assertRaisesRegex(ValueError, "bytes changed"):
                runtime.assert_original_adapter_unchanged(torch, reloaded, source)
            state[first] = source[first].to(torch.bfloat16).float()
            with self.assertRaisesRegex(ValueError, "bytes changed"):
                runtime.assert_original_adapter_unchanged(torch, state, source)
            state.pop(first)
            with self.assertRaisesRegex(ValueError, "inventory differs"):
                runtime.assert_original_adapter_unchanged(torch, state, source)

        def test_wrong_actual_hidden_dimension_fails_before_vocabulary_head(self):
            native = tiny_native(width=4095)
            with self.assertRaisesRegex(ValueError, "4096 hidden"):
                runtime.teacher_forced_features(torch, native, values_for_score(), [3, 31], device="cpu")
            self.assertEqual(native.model.calls, 1)
            self.assertEqual(native.lm_head.calls, 0)

        def test_saved_changed_observation_reloads_and_rejects_prefix_damage_or_loss(self):
            from .verification import verify_saved_observation

            # Reuse the real CPU patch/text fixture, adding the on-disk refs
            # present in actual NativeInputStore requests. No media/model is read.
            fixture = TorchObservationTests(methodName="test_real_tensor_pixel_layout_native_times_and_same_budget")
            self.addCleanup(fixture.doCleanups)
            fixture.setUp()
            store, original, before, clock = fixture.store(fixture.frames())
            directory = Path(fixture.temp.name)
            original_prefix = directory / "original_prefix.pt"
            torch.save({key: before[key] for key in ("input_ids", "attention_mask")}, original_prefix)
            clock_path = directory / "clock.json"
            clock_path.write_text(json.dumps(clock), encoding="utf-8")
            store.sources["s"]["clock_ref"] = reference(clock_path)
            original.update(prefix_ref=reference(original_prefix), grid_hw=[2, 2],
                            source_clock_ref=reference(clock_path))
            original_path = directory / "request.json"
            original_path.write_text(json.dumps(original), encoding="utf-8")
            store.request_refs["w"] = reference(original_path)
            store.requests, store.clocks = {"w": original}, {"s": clock}

            request, values, _, qa = observation.build_observation_case(store, "w", fixture.processor)
            self.assertEqual(qa["status"], "PASS_FIRST_CHANGED_OBSERVATION_CPU_QA")
            prefix = directory / "changed_prefix.pt"
            torch.save({key: values[key] for key in ("input_ids", "attention_mask")}, prefix)
            request["prefix_ref"] = reference(prefix)
            saved_request = directory / "changed_request.json"
            saved_request.write_text(json.dumps(request), encoding="utf-8")
            saved = strict_load(saved_request)
            actual = verify_saved_observation(store, "w", saved, processor=fixture.processor)
            for key in values:
                self.assertTrue(torch.equal(actual[key].view(torch.uint8), values[key].view(torch.uint8)), key)

            changed = {key: values[key].clone() for key in ("input_ids", "attention_mask")}
            changed["input_ids"][0, 0] += 1
            torch.save(changed, prefix)
            with self.assertRaisesRegex(ValueError, "Reference bytes changed"):
                verify_saved_observation(store, "w", saved)
            # A mistakenly rebound but well-hashed wrong prefix is caught by
            # the independent actual four-tensor byte signature as well.
            rebound = dict(saved, prefix_ref=reference(prefix))
            with self.assertRaisesRegex(ValueError, "four-tensor bytes differ"):
                verify_saved_observation(store, "w", rebound)
            prefix.unlink()
            with self.assertRaises(FileNotFoundError):
                verify_saved_observation(store, "w", saved)

    actual_names = unittest.defaultTestLoader.getTestCaseNames(TorchChecks)
    require(actual_names == RUNTIME_TORCH_TEST_NAMES, "Registered real CPU Torch check inventory changed")
    require(unittest.defaultTestLoader.getTestCaseNames(TorchObservationTests) == OBSERVATION_TORCH_TEST_NAMES,
            "Registered real CPU observation check inventory changed")
    return unittest.TestSuite((unittest.defaultTestLoader.loadTestsFromTestCase(TorchChecks),
                               unittest.defaultTestLoader.loadTestsFromTestCase(TorchObservationTests)))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pure", action="store_true", help="Run NumPy/protocol checks only; never passes Torch admission")
    parser.add_argument("--output", type=Path, help="Write a new code-bound PASS/FAIL/NOT_RUN JSON")
    args = parser.parse_args(argv)
    pure_suite = unittest.TestSuite((unittest.defaultTestLoader.loadTestsFromTestCase(PureRuntimeChecks),
                                     unittest.defaultTestLoader.loadTestsFromTestCase(PureObservationTests)))
    pure = unittest.TextTestRunner(verbosity=2).run(pure_suite)

    def emit(status, actual=None, **extra):
        results = [pure] + ([actual] if actual is not None else [])
        skipped = sum(len(result.skipped) for result in results)
        failed = sum(len(result.failures) + len(result.errors) for result in results)
        report = dict(schema=SCHEMA, status=status, device="cpu", model_downloads=0, qwen_forwards=0,
                      scope="REAL_TINY_CPU_TORCH_PLUS_NUMPY_AND_EXPLICITLY_SYNTHETIC_GENERATION_TRANSPORT",
                      checks=sum(result.testsRun for result in results), pure_checks=pure.testsRun,
                      torch_checks=actual.testsRun if actual is not None else 0,
                      pure_test_names=pure_test_names(), torch_test_names=TORCH_TEST_NAMES if actual is not None else [],
                      pure_passed=pure.wasSuccessful() and not pure.skipped,
                      torch_passed=actual.wasSuccessful() and not actual.skipped if actual is not None else False,
                      skipped_checks=skipped, failed_checks=failed, code_refs=code_refs(), **extra)
        if args.output is not None:
            save_new(args.output, report)
        print(json.dumps(report, allow_nan=False))

    if not pure.wasSuccessful() or pure.skipped:
        emit("FAIL", reason="NUMPY_OR_SYNTHETIC_PROTOCOL_CHECK_FAILED")
        return 1
    if args.pure:
        emit("NOT_RUN", reason="PURE_ONLY_TORCH_GATE_NOT_RUN")
        return 0
    if importlib.util.find_spec("torch") is None:
        emit("NOT_RUN", reason="TORCH_UNAVAILABLE", required_linux_torch_gate="NOT_PASSED")
        return 77
    try:
        import torch
    except Exception as error:
        emit("NOT_RUN", reason="TORCH_IMPORT_FAILED", error=str(error), required_linux_torch_gate="NOT_PASSED")
        return 77
    torch.set_num_threads(1)
    actual = unittest.TextTestRunner(verbosity=2).run(torch_suite(torch))
    success = actual.wasSuccessful() and not actual.skipped
    emit("PASS" if success else "FAIL", actual, torch_version=str(torch.__version__),
         torch_distribution_version=importlib.metadata.version("torch"))
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
