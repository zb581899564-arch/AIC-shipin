"""Public CPU checks for specialist time/selection contracts, not model quality."""
from fractions import Fraction
from pathlib import Path
import tempfile
import unittest

from .contracts import canonical_bytes, ref
from .specialist import (SpecialistConfig, SpecialistRuntime, normalize_features, plan_cells,
                         pack_float32, plan_windows, preprocess_clip_image, select_native,
                         unpack_float32, validate_clip_tokens, clip_query_layout)


def source(points, end):
    return {"video_id": "synthetic", "normalized_exact_pts": [str(value) for value in points],
            "physical_end_exact": str(end), "n_frames": len(points),
            "width": 320, "height": 240, "media": {"sha256": "a" * 64}}


def outputs(cells, *, probability=.9, score=None, span=(.5, 1.)):
    rows = []
    for window in plan_windows(cells):
        count = window["stop_cell"] - window["first_cell"]
        scores = [float(index) for index in range(window["first_cell"], window["stop_cell"])] if score is None else [float(score)] * count
        rows.append(dict(window, saliency=scores, spans_cxw=[list(span)], foreground_probability=[probability]))
    return rows


class NativeTimeTests(unittest.TestCase):
    def test_vfr_cells_cover_native_ordinals_and_nearest_actual_center(self):
        spec = source([Fraction(0), Fraction(1, 3), Fraction(7, 4), Fraction(9, 4), Fraction(19, 4)], 5)
        cells = plan_cells(spec)
        self.assertEqual([cell["sample_frame"] for cell in cells], [1, 3, 4])
        expanded = [frame for cell in cells for frame in range(cell["first"], cell["stop"])]
        self.assertEqual(expanded, list(range(5)))
        self.assertEqual(cells[-1]["end_exact"], "5")

    def test_long_source_has_fixed_overlap_and_no_75_cell_rejection(self):
        spec = source([Fraction(i) for i in range(364)], 364)
        cells = plan_cells(spec)
        windows = plan_windows(cells)
        self.assertEqual([(r["first_cell"], r["stop_cell"]) for r in windows], [(0, 75), (60, 135), (120, 182)])
        self.assertTrue(all(r["stop_cell"] - r["first_cell"] <= 75 for r in windows))
        result = select_native(spec, cells, outputs(cells))
        self.assertLessEqual(Fraction(result["selected_duration_exact"]), 91)
        self.assertEqual(len(result["selected_frames"]), 91)
        self.assertEqual(result["cell_saliency"], [float(i) for i in range(182)])

    def test_foreground_absence_is_legal_empty_not_forced_quota(self):
        spec = source([Fraction(i, 4) for i in range(32)], 8)
        cells = plan_cells(spec)
        result = select_native(spec, cells, outputs(cells, probability=.49, score=100))
        self.assertEqual(result["selected_frames"], [])
        self.assertTrue(result["empty_is_model_policy"])

    def test_model_failure_not_converted_to_empty(self):
        spec = source([Fraction(i, 4) for i in range(32)], 8)
        cells = plan_cells(spec)
        for bad in ([], [dict(outputs(cells)[0], saliency=[float("nan")] * 4)],
                    [dict(outputs(cells)[0], spans_cxw=[[1.1, .4]])]):
            with self.assertRaises(ValueError):
                select_native(spec, cells, bad)

    def test_native_duration_cap_does_not_count_frames_as_constant_fps(self):
        spec = source([Fraction(0), Fraction(1, 10), Fraction(2, 10), Fraction(9, 10), Fraction(19, 10),
                       Fraction(3), Fraction(4), Fraction(6)], 8)
        cells = plan_cells(spec)
        result = select_native(spec, cells, outputs(cells))
        points = [Fraction(point) for point in spec["normalized_exact_pts"]]
        durations = [((points[index + 1] if index + 1 < len(points) else Fraction(8)) - points[index])
                     for index in result["selected_frames"]]
        self.assertEqual(sum(durations, Fraction(0)), Fraction(result["selected_duration_exact"]))
        self.assertLessEqual(sum(durations, Fraction(0)), 2)

    def test_short_source_can_select_without_forcing_a_whole_two_second_cell(self):
        spec = source([Fraction(i, 30) for i in range(30)], 1)
        cells = plan_cells(spec)
        result = select_native(spec, cells, outputs(cells))
        self.assertEqual(len(result["selected_frames"]), 7)
        self.assertLessEqual(Fraction(result["selected_duration_exact"]), Fraction(1, 4))
        self.assertEqual(result["selected_frames"], list(range(12, 19)))

    def test_foreign_cell_clock_is_rejected_before_selection(self):
        spec = source([Fraction(i, 4) for i in range(32)], 8)
        cells = plan_cells(spec)
        wrong = [dict(row) for row in cells]
        wrong[0]["end_exact"] = "1999/1000"
        with self.assertRaisesRegex(ValueError, "exact native clock"):
            select_native(spec, wrong, outputs(wrong))


class CLIPProfileTests(unittest.TestCase):
    def test_literal_zero_token_before_eot_is_content_not_padding(self):
        tokens = [[49406, 320, 0, 49407] + [0] * 73]
        layout = clip_query_layout(tokens, 32)
        self.assertEqual(layout["attention_mask"], [[1., 1., 1., 1.] + [0.] * 73])
        self.assertEqual(layout["retained_feature_tokens"], 4)
        self.assertFalse(layout["trained_prefix_truncated"])

    def test_frozen_training_prefix_is_explicit_and_preserves_full_clip_tokens(self):
        tokens = [[49406] + [320] * 40 + [49407] + [0] * 35]
        layout = clip_query_layout(tokens, 32)
        self.assertEqual(layout["actual_query_tokens_with_sot_eot"], 42)
        self.assertEqual(layout["retained_token_indices"], list(range(32)))
        self.assertTrue(layout["trained_prefix_truncated"])
        self.assertEqual(sum(layout["attention_mask"][0]), 42)
        self.assertEqual(tokens[0][41], 49407)
        for invalid in [None, True, 0, 78]:
            with self.assertRaises(ValueError):
                clip_query_layout(tokens, invalid)

    def test_compact_float32_round_trip_is_bit_exact(self):
        import numpy as np
        values = np.random.default_rng(19).standard_normal((16, 512)).astype(np.float32)
        values[0, 0] = np.float32(-0.0)
        packed = pack_float32(values)
        restored = unpack_float32(packed, values.shape)
        self.assertEqual(restored.dtype, np.dtype("<f4"))
        self.assertEqual(restored.tobytes(), values.tobytes())
        self.assertLess(len(canonical_bytes(packed)), values.size * 6 + 512)
        self.assertTrue(restored.flags.writeable)

    def test_compact_tensor_rejects_wrong_shape_dtype_checksum_and_nan(self):
        import base64
        import hashlib
        import numpy as np
        values = np.ones((1, 77, 512), dtype=np.float32)
        packed = pack_float32(values)
        for bad in (dict(packed, shape=[77, 512]), dict(packed, dtype="<f2"),
                    dict(packed, bytes=packed["bytes"] - 4), dict(packed, sha256="0" * 64),
                    dict(packed, data=packed["data"][:-1])):
            with self.assertRaises((ValueError, TypeError)):
                unpack_float32(bad, (1, 77, 512))
        values[0, 0, 0] = np.nan
        with self.assertRaises(ValueError):
            pack_float32(values)
        raw = values.tobytes()
        bad = dict(packed, data=base64.b64encode(raw).decode("ascii"), sha256=hashlib.sha256(raw).hexdigest())
        with self.assertRaisesRegex(ValueError, "Nonfinite"):
            unpack_float32(bad, (1, 77, 512))

    def test_actual_openai_token_contract_and_padding(self):
        tokens = [[49406, 320, 0, 49407] + [0] * 73]
        self.assertEqual(validate_clip_tokens(tokens), tokens)
        for invalid in ([[0] * 77], [[49406, 49407, 5] + [0] * 74],
                        [[49406, 49407, 49407] + [0] * 74],
                        [[49406, 49407] + [0] * 74]):
            with self.subTest(invalid=invalid[0][:4]), self.assertRaises(ValueError):
                validate_clip_tokens(invalid)

    def test_center_crop_profile_and_training_normalization(self):
        import numpy as np
        image = np.zeros((240, 480, 3), dtype=np.uint8)
        image[:, 120:360] = 255
        result = preprocess_clip_image(image)
        self.assertEqual(result.shape, (3, 224, 224))
        self.assertEqual(result.dtype, np.float32)
        self.assertTrue(np.isfinite(result).all())
        x = np.zeros((2, 512), np.float32)
        x[:, 0] = [3., 4.]
        normalized = normalize_features(x)
        self.assertAlmostEqual(float(normalized[0, 0]), 3 / (3 + 1e-5), places=7)
        self.assertLess(float(normalized[0, 0]), 1.)

    def test_bad_features_and_unregistered_config_rejected(self):
        import numpy as np
        with self.assertRaises(ValueError):
            normalize_features(np.zeros((2, 768)))
        with self.assertRaises(ValueError):
            SpecialistConfig(maximum_duration_fraction="1/3").validate()


class _Parameter:
    def __init__(self, shape):
        self.shape = shape


class _Module:
    def __init__(self):
        self.value = _Parameter((2, 3))

    def named_parameters(self, remove_duplicate=False):
        return [("weight", self.value)]


class RuntimeReceiptTests(unittest.TestCase):
    def test_source_return_contract_consumes_complete_native_iterator(self):
        import hashlib
        import numpy as np
        spec = source([Fraction(i, 4) for i in range(32)], 8)
        spec.update(width=6, height=4)
        runtime = SpecialistRuntime({"weights": "fixture"})
        calls, exhausted = [], []
        def encode(images):
            calls.append(len(images))
            return normalize_features(np.ones((len(images), 512), dtype=np.float32))
        runtime.encode_images = encode  # Public API fixture; no actual model call.
        def observed():
            for cell in plan_cells(spec):
                rgb = np.zeros((4, 6, 3), dtype=np.uint8)
                yield {"frame": cell["sample_frame"], "pts": cell["sample_pts_exact"], "rgb": rgb,
                       "source_id": spec["video_id"], "pixel_sha256": hashlib.sha256(rgb.tobytes()).hexdigest()}
            exhausted.append(True)
        result = runtime.encode_source(spec, observed())
        self.assertEqual(exhausted, [True])
        self.assertEqual(calls, [4])
        self.assertEqual(set(result), {"rows", "features"})
        self.assertEqual(len(result["rows"]), 4)
        self.assertEqual(unpack_float32(result["features"], (4, 512)).shape, (4, 512))
        self.assertTrue(all(row["source_sha256"] == spec["media"]["sha256"] for row in result["rows"]))
        canonical_bytes({"features": result})  # Runner's exact outer cache shape.

    def test_parameter_receipts_are_deterministic_across_runtime_objects(self):
        # A small contract fixture, not an actual-loaded production receipt.
        with tempfile.TemporaryDirectory() as directory:
            checkpoint = Path(directory) / "fixture.bin"
            checkpoint.write_bytes(b"public-engineering-fixture")
            identity = ref(checkpoint)
            spec = {"checkpoint": identity, "clip_checkpoint": identity,
                    "source": {"path": directory, "commit": "fixed", "tree_sha": "fixed"}}
            receipts = []
            for _ in range(2):
                runtime = SpecialistRuntime(spec)
                runtime.model, runtime.clip_model = _Module(), _Module()
                runtime.runtime_identity = {"torch": "synthetic-fixture", "clip_package_files": {}}
                receipts.append(runtime.parameter_receipts())
            self.assertEqual(canonical_bytes(receipts[0]), canonical_bytes(receipts[1]))
            self.assertEqual([row["total_elements"] for row in receipts[0]], [6, 6])
            self.assertNotIn("created_at", canonical_bytes(receipts[0]).decode())

    def test_cache_key_includes_exact_runtime_implementation(self):
        seen = {}
        physical = []
        def cache(kind, key, payload, compute):
            if key not in seen:
                seen[key] = compute()
            return seen[key]
        runtime = SpecialistRuntime({"weights": "fixed"}, call_cache=cache)
        def compute():
            physical.append(True)
            return {"physical_model_forwards": 1}
        runtime.runtime_identity = {"clip_code_sha256": "a" * 64}
        runtime._cached("clip_images", {"pixels": "fixed"}, compute)
        runtime._cached("clip_images", {"pixels": "fixed"}, compute)
        runtime.runtime_identity = {"clip_code_sha256": "b" * 64}
        runtime._cached("clip_images", {"pixels": "fixed"}, compute)
        self.assertEqual(len(physical), 2)


if __name__ == "__main__":
    unittest.main()
