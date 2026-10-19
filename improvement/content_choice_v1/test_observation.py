"""Synthetic CPU observation tests; real Torch tests fail closed when required.

Run the deployment gate with:
  python -m improvement.content_choice_v1.test_observation --require-torch -v
No model, real media, label dataset, decoder, network or GPU is used.
"""
from copy import deepcopy
from fractions import Fraction
import importlib.util
import json
from pathlib import Path
import re
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np

from . import observation as obs
from ..native_preference_v1.assets import path_ref


HAS_TORCH = importlib.util.find_spec("torch") is not None


def patches_from_spatial_rgb(spatial):
    """Independent explicit merge-block/channel/temporal/patch fixture layout."""
    height, width, _ = spatial.shape
    pixels = np.empty((height * width, 1536), dtype=np.float32)
    row = 0
    for by in range(0, height, 2):
        for bx in range(0, width, 2):
            for dy in range(2):
                for dx in range(2):
                    for channel in range(3):
                        pixels[row, channel * 512:(channel + 1) * 512] = spatial[by + dy, bx + dx, channel]
                    row += 1
    return pixels


class PureObservationTests(unittest.TestCase):
    def test_same_even_budget_endpoints_without_padding(self):
        for count in (2, 3, 7, 64, 65, 128, 211):
            indices = list(range(count))
            chosen, qa = obs.select_cells(indices, list(map(str, indices)), np.zeros((count, 12), dtype=np.float64))
            self.assertEqual(chosen, obs.uniform_cells(indices))
            self.assertEqual(len(chosen), min(64, count - count % 2))
            self.assertEqual((chosen[0], chosen[-1]), (0, count - 1))
            self.assertEqual(qa["padding"], 0)

    def test_exact_midpoint_is_assigned_to_earlier_nonempty_stratum(self):
        indices = list(range(65))
        uniform, strata, boundaries = obs.fixed_time_strata(indices, list(map(str, indices)))
        self.assertEqual(strata[-2:], [[62, 63], [64]])
        self.assertEqual(boundaries[-1], Fraction(63))
        self.assertTrue(all(centre in members for centre, members in zip(uniform, strata)))

    def test_vfr_strata_are_native_time_based_and_complete(self):
        points = ["0", "1/10", "1/5", "1", "100", "101", "1000"]
        uniform, strata, boundaries = obs.fixed_time_strata(list(range(7)), points)
        self.assertEqual(boundaries[-1], Fraction(550))
        self.assertEqual(strata[-2:], [[4, 5], [6]])
        self.assertEqual([i for values in strata for i in values], list(range(7)))
        self.assertEqual(len(uniform), 6)

    def test_change_inside_stratum_can_expose_a_missed_real_observation(self):
        values = np.zeros((128, 12), dtype=np.float64); values[3] = 10
        selected, qa = obs.select_cells(list(range(128)), list(map(str, range(128))), values)
        self.assertNotIn(3, qa["uniform_cells"])
        self.assertIn(3, selected)
        self.assertEqual(len(selected), 64)
        self.assertGreater(qa["changed_observations"], 0)

    def test_equal_local_change_ties_prefer_original_uniform(self):
        values = np.repeat(np.arange(128, dtype=np.float64)[:, None], 12, axis=1)
        selected, qa = obs.select_cells(list(range(128)), list(map(str, range(128))), values)
        self.assertEqual(selected, qa["uniform_cells"])

    def test_excerpt_score_never_uses_outside_neighbours(self):
        values = np.zeros((128, 12), dtype=np.float64)
        values[9] = 10000; values[100] = -10000
        indices = list(range(10, 100))
        selected, qa = obs.select_cells(indices, list(map(str, range(128))), values)
        self.assertEqual(selected, qa["uniform_cells"])
        self.assertEqual(qa["selected_change_scores"], [0.0] * 64)

    def test_fixed_endpoints_are_not_replaced_by_high_change_neighbour(self):
        values = np.zeros((128, 12), dtype=np.float64); values[1] = 999; values[-2] = 999
        selected, _ = obs.select_cells(list(range(128)), list(map(str, range(128))), values)
        self.assertEqual((selected[0], selected[-1]), (0, 127))

    def test_invalid_input_or_nan_cannot_turn_into_a_selection(self):
        for indices in ([0], [0, 0], [True, 1], [1, 0]):
            with self.assertRaises(ValueError):
                obs.select_cells(indices, ["0", "1"], np.zeros((2, 12)))
        for points in (["0", "0"], ["0", "NaN"]):
            with self.assertRaises(ValueError):
                obs.fixed_time_strata([0, 1], points)
        for bad in (np.full((2, 12), np.nan), np.zeros((2, 11)), np.zeros((2, 12), dtype=bool)):
            with self.assertRaises(ValueError):
                obs.select_cells([0, 1], ["0", "1"], bad)

    def test_patch_layout_matches_independent_native_grid_quadrants(self):
        spatial = np.arange(4 * 8 * 3, dtype=np.float32).reshape(4, 8, 3)
        pixels = patches_from_spatial_rgb(spatial)
        actual = obs.patch_descriptor_array(pixels, [4, 8])
        expected = np.concatenate([spatial[y:y + 2, x:x + 4].mean(axis=(0, 1), dtype=np.float64)
                                   for y in (0, 2) for x in (0, 4)])
        np.testing.assert_array_equal(actual, expected)
        self.assertEqual(actual.dtype, np.float64)

    def test_temporal_copy_corruption_and_nonfinite_pixels_are_rejected(self):
        original = patches_from_spatial_rgb(np.ones((2, 2, 3), dtype=np.float32))
        corrupt = original.copy(); corrupt[0, 256] = 2
        with self.assertRaisesRegex(ValueError, "temporal copies"):
            obs.patch_descriptor_array(corrupt, [2, 2])
        bad = original.copy(); bad[0, 0] = np.inf
        with self.assertRaisesRegex(ValueError, "Finite"):
            obs.patch_descriptor_array(bad, [2, 2])
        with self.assertRaises(ValueError):
            obs.patch_descriptor_array(original.astype(np.float64), [2, 2])

    def test_source_descriptor_cache_once_then_detects_mutation(self):
        class ArrayFrame:
            device = SimpleNamespace(type="cpu")
            requires_grad = False
            def detach(self): return self
            def numpy(self): return patches_from_spatial_rgb(np.ones((2, 2, 3), dtype=np.float32))
        store = SimpleNamespace(sources={"s": dict(source_sha256="a" * 64,
            clock_ref={"path": "/synthetic/clock", "sha256": "b" * 64}, patches=[])})
        cache = {}
        first, computed, key = obs._descriptors(store, "s", [ArrayFrame(), ArrayFrame()], [2, 2], [0, 1], cache)
        self.assertTrue(computed)
        second, computed, again = obs._descriptors(store, "s", [ArrayFrame(), ArrayFrame()], [2, 2], [0, 1], cache)
        self.assertFalse(computed); self.assertIs(first, second); self.assertEqual(key, again)
        cache["descriptors"][0, 0] = 7
        with self.assertRaisesRegex(ValueError, "cache changed"):
            obs._descriptors(store, "s", [ArrayFrame(), ArrayFrame()], [2, 2], [0, 1], cache)


class SyntheticProcessor:
    """A deterministic text-only processor test double, never a pretrained model."""
    vision_start_token, video_token, vision_end_token = "<vs>", "<v>", "<ve>"
    def __init__(self):
        self.video_processor = SimpleNamespace(merge_size=2, model_input_names=[])
        self.tokenizer = self

    def convert_tokens_to_ids(self, token):
        return {"<vs>": 1, "<v>": 2, "<ve>": 3}[token]

    def apply_chat_template(self, messages, **kwargs):
        return "USER:" + "".join(item["text"] if item["type"] == "text" else "<vs><v><ve>"
                                 for item in messages[0]["content"]) + "ASSISTANT:"

    def _calculate_timestamps(self, *args):
        raise AssertionError("Independent processor stub must supply the actual native times")

    def __call__(self, text=None, videos=None, **kwargs):
        import torch
        if isinstance(text, str):
            parts = re.findall(r"<vs>|<v>|<ve>|[\s\S]", text)
            ids = [self.convert_tokens_to_ids(part) if part in ("<vs>", "<v>", "<ve>") else ord(part) + 10 for part in parts]
            return dict(input_ids=torch.tensor([ids], dtype=torch.int64), attention_mask=torch.ones((1, len(ids)), dtype=torch.int64))
        adopted = self.video_processor(videos)
        parts = text[0].split("<vs><v><ve>"); expanded = parts[0]
        for index, (_, height, width) in enumerate(adopted["video_grid_thw"].tolist()):
            times = self._calculate_timestamps(adopted["video_metadata"][index])
            expanded += "".join(("<%.1f seconds>" % value) + "<vs>" + "<v>" * (height * width // 4) + "<ve>" for value in times)
            expanded += parts[index + 1]
        return {**self(expanded), **{key: adopted[key] for key in ("pixel_values_videos", "video_grid_thw")}}


@unittest.skipUnless(HAS_TORCH, "Actual Torch is absent; deployment must run --require-torch")
class TorchObservationTests(unittest.TestCase):
    def setUp(self):
        import torch
        from ..bottleneck_24h_v1 import summary_contract
        self.torch, self.contract = torch, summary_contract
        self.processor = SyntheticProcessor()
        self.temp = tempfile.TemporaryDirectory(prefix="aic_observation_cpu_")
        self.addCleanup(self.temp.cleanup)

    def frames(self, pulse=True):
        result = []
        for index in range(128):
            pixels = patches_from_spatial_rgb(np.full((2, 2, 3), 1.0 if pulse and index == 3 else 0.0, dtype=np.float32))
            result.append(self.torch.from_numpy(pixels))
        return result

    def store(self, frames):
        clock = dict(normalized_exact_pts=[str(Fraction(i * i, 100)) for i in range(128)],
                     physical_end_exact="200", source_sha256="a" * 64)
        pixels, plan = self.contract.build_pixels(frames, [2, 2], list(range(128)), clock["normalized_exact_pts"], "0", "200",
                                                  dict(source_id="s", source_sha256="a" * 64))
        prefix, metadata = self.contract.build_text(self.processor, plan, pixels["video_grid_thw"], "200")
        values = {**pixels, **prefix}
        request = dict(uid="w", sid="s", source_sha256="a" * 64, plan=plan, text=metadata,
                       prefix_ref={"path": "/synthetic/original-prefix", "sha256": "c" * 64},
                       input_signature=self.contract.signature(values))
        path = Path(self.temp.name) / "request.json"; path.write_text(json.dumps(request))
        store = SimpleNamespace(workspace=Path(self.temp.name), request_refs={"w": path_ref(path)},
            sources={"s": dict(source_sha256="a" * 64, clock_ref={"sha256": "b" * 64}, patches=[])},
            case=lambda uid: (request, values, clock), _source_pixels=lambda sid: (frames, [2, 2], list(range(128))),
            _helpers=lambda: self.contract)
        return store, request, values, clock

    def test_real_tensor_pixel_layout_native_times_and_same_budget(self):
        store, old, before, clock = self.store(self.frames())
        request, values, _, qa = obs.build_observation_case(store, "w", self.processor)
        self.assertTrue(qa["changed_pixel_bytes"])
        self.assertEqual(qa["old_visual_tokens"], qa["new_visual_tokens"])
        self.assertNotIn("prefix_ref", request)
        self.assertIn("old_prefix_ref", request)
        self.assertEqual(request["text"]["prompt"], old["text"]["prompt"])
        self.assertNotEqual(request["input_signature"], old["input_signature"])
        self.contract.independent_pixels(store._source_pixels("s")[0], [2, 2], values, request["plan"], list(range(128)), clock["normalized_exact_pts"])
        for video in request["plan"]["videos"]:
            times = list(map(Fraction, video["exact_pts"]))
            self.assertEqual(video["group_timestamps_exact"], [str((a + b) / 2) for a, b in zip(times[::2], times[1::2])])

    def test_no_effect_returns_exact_original_four_tensors_and_plan(self):
        store, old, before, _ = self.store(self.frames(pulse=False))
        request, values, _, qa = obs.build_observation_case(store, "w", object())
        self.assertEqual(qa["status"], "NO_EFFECT")
        self.assertIs(values, before)
        self.assertEqual(request["plan"], old["plan"])
        self.assertEqual(request["prefix_ref"], old["prefix_ref"])
        self.assertTrue(qa["old_success_can_be_adopted"])

    def test_pixel_identical_changed_pts_proposal_is_wholly_discarded(self):
        store, old, before, _ = self.store(self.frames(pulse=False))
        def propose(indices, sample_pts, descriptors):
            chosen = obs.uniform_cells(indices); chosen[1] = 3
            return chosen, dict(changed_observations=1)
        with patch.object(obs, "select_cells", side_effect=propose):
            request, values, _, qa = obs.build_observation_case(store, "w", object())
        self.assertEqual(qa["status"], "NO_EFFECT")
        self.assertTrue(qa["proposed_plan_discarded"])
        self.assertFalse(qa["actual_plan_changed"])
        self.assertEqual(request["input_signature"], old["input_signature"])
        self.assertEqual(request["plan"], old["plan"])
        self.assertIs(values, before)

    def test_tensor_temporal_copy_or_excerpt_scope_failure_is_rejected(self):
        frames = self.frames(); frames[0][0, 256] = 2
        with self.assertRaisesRegex(ValueError, "temporal copies"):
            obs.pack_selected_pixels(frames, [2, 2], list(range(128)), list(map(str, range(128))), "0", "128", {}, [[0, 1], [0, 1]])
        with self.assertRaisesRegex(ValueError, "escaped"):
            obs.pack_selected_pixels(self.frames(), [2, 2], list(range(128)), list(map(str, range(128))), "10", "20", {}, [[0, 1], [1, 2]])


if __name__ == "__main__":
    if "--require-torch" in sys.argv:
        sys.argv.remove("--require-torch")
        if not HAS_TORCH:
            raise SystemExit("STOP_MISSING_TORCH: actual CPU tensor/processor-layout tests are required before model admission")
    unittest.main()
