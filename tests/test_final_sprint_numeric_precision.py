"""Small frozen CPU tensors only; no real-model or CUDA numeric acceptance."""
import copy
import unittest
from unittest import mock

try:
    import torch
except ImportError:
    torch = None

from improvement.final_sprint_v1 import numeric_precision as precision
from improvement.final_sprint_v1.qwen_runtime import QwenRuntime
from improvement.native_preference_v1.runtime import canonical_frozen_hash


@unittest.skipIf(torch is None, "CPU PyTorch unavailable")
class LosslessPrecisionTests(unittest.TestCase):
    def setUp(self):
        self.previous_precision = torch.get_float32_matmul_precision()
        self.previous_matmul_tf32 = torch.backends.cuda.matmul.allow_tf32
        self.previous_cudnn_tf32 = torch.backends.cudnn.allow_tf32
        self.previous_autocast = torch.is_autocast_enabled()

    def tearDown(self):
        torch.set_float32_matmul_precision(self.previous_precision)
        torch.backends.cuda.matmul.allow_tf32 = self.previous_matmul_tf32
        torch.backends.cudnn.allow_tf32 = self.previous_cudnn_tf32
        torch.set_autocast_enabled(self.previous_autocast)

    def model(self):
        model = torch.nn.Module()
        model.weight = torch.nn.Parameter(torch.tensor([[1.25, -2.5], [0., .125]], dtype=torch.bfloat16),
                                          requires_grad=False)
        model.tied_weight = model.weight
        model.register_buffer("scale", torch.tensor([.5, 2.], dtype=torch.bfloat16))
        model.register_buffer("tied_scale", model.scale)
        model.register_buffer("frequencies", torch.tensor([.1, .2], dtype=torch.float32))
        model.register_buffer("positions", torch.tensor([0, 1], dtype=torch.int64))
        return model

    def identity(self, model):
        identity = canonical_frozen_hash(model, torch)
        return dict(identity, expected_sha256=identity["sha256"], verified_before_adapter=True)

    def test_conversion_preserves_exact_values_aliases_freeze_count_and_canonical_bytes(self):
        model = self.model()
        original = self.identity(model)
        before = {name: (id(value), value.clone()) for name, value in model.named_parameters(remove_duplicate=False)}
        old_buffers = {name: (id(value), value.clone()) for name, value in model.named_buffers(remove_duplicate=False)}
        proof = precision.lossless_fp32_conversion(model, torch, original)
        self.assertEqual(proof["roundtrip_BASE_identity"]["sha256"], original["sha256"])
        self.assertEqual(proof["roundtrip_BASE_identity"]["parameters"], 4)
        self.assertEqual(proof["unique_parameter_tensors"], 1)
        self.assertEqual(proof["unique_buffers"], 3)
        for name, value in model.named_parameters(remove_duplicate=False):
            old_id, old_value = before[name]
            self.assertEqual(id(value), old_id)
            self.assertEqual(value.dtype, torch.float32)
            self.assertTrue(torch.equal(value, old_value.float()))
            self.assertFalse(value.requires_grad)
            self.assertIsNone(value.grad)
        for name, value in model.named_buffers(remove_duplicate=False):
            old_id, old_value = old_buffers[name]
            self.assertEqual(id(value), old_id)
            self.assertTrue(torch.equal(value, old_value.to(dtype=value.dtype)))
        self.assertIs(model.weight, model.tied_weight)
        self.assertIs(model.scale, model.tied_scale)
        self.assertEqual(model.positions.dtype, torch.int64)
        self.assertEqual(proof["backend"], dict(float32_matmul_precision="highest",
                         cuda_matmul_allow_tf32=False, cudnn_allow_tf32=False, cuda_autocast_enabled=False))

    def test_unverified_identity_is_rejected_before_any_conversion(self):
        model = self.model()
        identity = self.identity(model)
        identity["verified_before_adapter"] = False
        with self.assertRaisesRegex(ValueError, "before FP32"):
            precision.lossless_fp32_conversion(model, torch, identity)
        self.assertEqual(model.weight.dtype, torch.bfloat16)

    def test_preconversion_weight_or_name_corruption_fails_original_canonical_match(self):
        for change in ("value", "name"):
            with self.subTest(change=change):
                model = self.model()
                identity = self.identity(model)
                if change == "value":
                    model.weight.data[0, 0] = 4
                else:
                    model.renamed = model.weight
                    del model.weight
                    del model.tied_weight
                with self.assertRaisesRegex(ValueError, "canonical BASE identity"):
                    precision.lossless_fp32_conversion(model, torch, identity)

    def test_fp32_corruption_smaller_than_bf16_rounding_is_still_rejected(self):
        model = self.model()
        precision.lossless_fp32_conversion(model, torch, self.identity(model))
        model.weight.data[0, 0] += 2 ** -18
        with self.assertRaisesRegex(ValueError, "exact expansion"):
            precision.bf16_roundtrip_identity(model, torch)

    def test_buffer_corruption_during_conversion_is_rejected(self):
        model = self.model()
        identity = self.identity(model)
        cast = precision._cast_owned_tensors

        def corrupt(rows, actual_torch):
            cast(rows, actual_torch)
            model.frequencies[0] += .1

        with mock.patch.object(precision, "_cast_owned_tensors", side_effect=corrupt):
            with self.assertRaisesRegex(ValueError, "buffer bytes"):
                precision.lossless_fp32_conversion(model, torch, identity)

    def test_alias_replacement_during_conversion_is_rejected(self):
        model = self.model()
        identity = self.identity(model)
        cast = precision._cast_owned_tensors

        def replace_alias(rows, actual_torch):
            cast(rows, actual_torch)
            model.tied_weight = torch.nn.Parameter(model.weight.clone(), requires_grad=False)

        with mock.patch.object(precision, "_cast_owned_tensors", side_effect=replace_alias):
            with self.assertRaisesRegex(ValueError, "objects, aliases, shapes or counts"):
                precision.lossless_fp32_conversion(model, torch, identity)

    def test_unfrozen_gradients_wrong_count_and_storage_views_are_rejected(self):
        for corruption in ("trainable", "gradient", "count", "view"):
            with self.subTest(corruption=corruption):
                model = self.model()
                identity = self.identity(model)
                if corruption == "trainable":
                    model.weight.requires_grad_(True)
                elif corruption == "gradient":
                    model.weight.grad = torch.ones_like(model.weight)
                elif corruption == "count":
                    identity["parameters"] += 1
                else:
                    model.distinct_view = torch.nn.Parameter(model.weight.detach().view(-1), requires_grad=False)
                with self.assertRaises(ValueError):
                    precision.lossless_fp32_conversion(model, torch, identity)
                self.assertEqual(model.weight.dtype, torch.bfloat16)

    def test_lossless_profile_refuses_adapter_and_unknown_profile_while_default_stays_opt_out(self):
        default = QwenRuntime({"revision": "synthetic"})
        self.assertIsNone(default.arithmetic_profile)
        self.assertIsNone(default.arithmetic_conversion)
        with default._arithmetic_context() as context:
            self.assertIsNone(context)
        with self.assertRaisesRegex(ValueError, "TIME adapter"):
            QwenRuntime({"arithmetic_profile": precision.LOSSLESS_FP32_PROFILE, "adapter_dir": "synthetic"})
        with self.assertRaisesRegex(ValueError, "Unknown"):
            QwenRuntime({"arithmetic_profile": "unregistered"})

    def test_fp32_inference_disables_autocast_and_rejects_backend_drift(self):
        runtime = QwenRuntime({"arithmetic_profile": precision.LOSSLESS_FP32_PROFILE})
        runtime.torch = torch
        torch.set_autocast_enabled(True)
        backend = precision.configure_fp32_backend(torch)
        self.assertFalse(torch.is_autocast_enabled())
        self.assertFalse(backend["cuda_autocast_enabled"])
        with mock.patch.object(torch, "autocast", return_value=mock.MagicMock()) as autocast:
            runtime._arithmetic_context()
        autocast.assert_called_once_with(device_type="cuda", enabled=False)
        torch.backends.cuda.matmul.allow_tf32 = True
        with self.assertRaisesRegex(ValueError, "backend was changed"):
            runtime._arithmetic_context()

    def test_receipt_explicitly_declares_conversion_and_preserves_original_weight_identity(self):
        model = self.model()
        identity = self.identity(model)
        runtime = QwenRuntime({"revision": "synthetic", "arithmetic_profile": precision.LOSSLESS_FP32_PROFILE})
        runtime.original_base_identity = dict(identity, hash_calls_this_load=1,
            hash_function="synthetic_historical_canonical", hash_function_file={"sha256": "a" * 64})
        runtime.arithmetic_conversion = precision.lossless_fp32_conversion(model, torch, identity)
        proof = runtime._parameter_loading_proof()
        self.assertEqual(proof["original_base_identity"]["sha256"], identity["sha256"])
        self.assertEqual(proof["arithmetic_conversion"]["source_parameter_dtype"], "torch.bfloat16")
        self.assertEqual(proof["arithmetic_conversion"]["materialized_parameter_dtype"], "torch.float32")
        self.assertFalse(proof["optional_TIME_loaded"])
        self.assertEqual(proof, copy.deepcopy(runtime._parameter_loading_proof()))


if __name__ == "__main__":
    unittest.main()
