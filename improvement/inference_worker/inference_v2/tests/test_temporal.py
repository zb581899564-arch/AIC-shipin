from __future__ import annotations

import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from inference_v2 import qwen_io
from inference_v2.baseline_v2 import load_index
from inference_v2.temporal import (
    build_temporal_prompt,
    canonicalize_segments,
    merge_overlapping_frame_segments,
    parse_segments_response,
    plan_windows,
    seconds_to_frame_segments,
    temporal_json_regex,
    temporal_json_schema,
)


class TemporalParserTests(unittest.TestCase):
    def test_zero_one_four_segments(self):
        empty = parse_segments_response('{"segments": []}', "multi")
        self.assertEqual((empty.status, empty.segments), ("valid_empty", ()))
        one = parse_segments_response('{"segments": [[1, 2.5]]}', "single")
        self.assertEqual((one.status, one.segments), ("valid", ((1.0, 2.5),)))
        four = parse_segments_response(
            '{"segments": [[0,1],[2,3],[4,5],[6,7]]}', "multi"
        )
        self.assertEqual(four.status, "valid")
        self.assertEqual(len(four.segments), 4)

    def test_cardinality_and_invalid_json(self):
        too_many = parse_segments_response(
            '{"segments": [[0,1],[2,3],[4,5],[6,7],[8,9]]}', "multi"
        )
        self.assertEqual(too_many.reason, "too_many_segments")
        self.assertEqual(parse_segments_response("not json").reason, "invalid_json")
        self.assertEqual(
            parse_segments_response('{"segments": [], "extra": 1}').reason,
            "invalid_root_structure",
        )

    def test_rejects_nan_bool_reversed_and_overlap(self):
        self.assertEqual(
            parse_segments_response('{"segments": [[NaN, 2]]}').reason,
            "segment_nonfinite",
        )
        self.assertEqual(
            parse_segments_response('{"segments": [[true, 2]]}').reason,
            "segment_not_numeric",
        )
        self.assertEqual(
            parse_segments_response('{"segments": [[3, 2]]}').reason,
            "segment_not_forward",
        )
        self.assertEqual(
            parse_segments_response('{"segments": [[1, 3], [2, 4]]}').reason,
            "segments_unordered_or_overlapping",
        )

    def test_single_prompt_is_frozen_baseline_prompt(self):
        self.assertIn("single most highlight-worthy clip", build_temporal_prompt(None, "single"))
        prompt = build_temporal_prompt("person opens door", "multi", 150.0)
        self.assertIn("zero to four", prompt)
        self.assertIn('{"segments":[[12.5,27.0]]}', prompt)
        self.assertIn('{"segments":[]}', prompt)
        self.assertIn("never use a string, timestamp text, or mm:ss", prompt.lower())
        self.assertIn("end_sec <= 150.000000", prompt)
        self.assertNotIn("...", prompt)

    def test_short_window_uses_legal_numeric_example(self):
        prompt = build_temporal_prompt("action", "windowed", 6.0)
        self.assertIn("end_sec <= 6.000000", prompt)
        self.assertIn('{"segments":[[2.4,4.8]]}', prompt)


class TimelineTests(unittest.TestCase):
    def test_non_integer_fps_half_open_membership(self):
        frames = seconds_to_frame_segments([(0.05, 1.0)], 29.97, 100)
        self.assertEqual(frames, [(2, 30)])
        start, end = frames[0]
        self.assertGreaterEqual(start / 29.97, 0.05)
        self.assertLess((end - 1) / 29.97, 1.0)

    def test_window_plan_and_last_partial(self):
        self.assertEqual(plan_windows(0.0), [])
        self.assertEqual(plan_windows(20.0), [(0.0, 20.0)])
        self.assertEqual(
            plan_windows(56.0),
            [(0.0, 30.0), (25.0, 55.0), (50.0, 56.0)],
        )
        self.assertEqual(
            plan_windows(150.024875)[-1], (125.0, 150.024875)
        )
        self.assertNotIn((150.0, 150.024875), plan_windows(150.024875))
        self.assertEqual(plan_windows(30.01), [(0.0, 30.0), (25.0, 30.01)])
        for duration in (30.01, 56.0, 150.024875):
            windows = plan_windows(duration)
            self.assertEqual(windows[0][0], 0.0)
            self.assertEqual(windows[-1][1], duration)
            for previous, current in zip(windows, windows[1:]):
                self.assertGreater(current[1], previous[1])

    def test_overlap_dedupe_does_not_merge_adjacent_frames(self):
        merged = merge_overlapping_frame_segments(
            [(10, 20), (15, 25), (25, 30), (40, 41), (40, 41)], 100
        )
        self.assertEqual(merged, [(10, 25), (25, 30), (40, 41)])

    def test_bounds_and_canonical_consistency(self):
        seconds, frames = canonicalize_segments(
            [(-3.0, 0.1), (9.9, 12.0)], fps=10.0, n_frames=100, duration_sec=10.0
        )
        self.assertEqual(frames, [(0, 1), (99, 100)])
        self.assertEqual(seconds, [(0.0, 0.1), (9.9, 10.0)])


class WindowInferenceTests(unittest.TestCase):
    def test_window_offsets_once_and_dedupes_overlap(self):
        outputs = iter([
            qwen_io.GenerationResult('{"segments": [[26,29]]}', []),
            qwen_io.GenerationResult('{"segments": [[0,6]]}', []),
            qwen_io.GenerationResult('{"segments": []}', []),
        ])
        with mock.patch.object(qwen_io, "generate_temporal", side_effect=lambda *a, **k: next(outputs)):
            result = qwen_io.infer_temporal_policy(
                object(), object(), "unused.mp4", policy="windowed", query="action",
                duration_sec=56.0,
            )
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.segments_sec, [(25.0, 31.0)])
        self.assertEqual(
            [row["window_sec"] for row in result.raw_outputs],
            [[0.0, 30.0], [25.0, 55.0], [50.0, 56.0]],
        )


class ConstrainedJsonTests(unittest.TestCase):
    @staticmethod
    def _grammar_accepts(text, policy):
        try:
            from lmformatenforcer import RegexParser
        except ImportError:
            raise unittest.SkipTest("lm-format-enforcer is not installed")
        parser = RegexParser(temporal_json_regex(policy))
        for character in text:
            if character not in parser.get_allowed_characters():
                return False
            parser = parser.add_character(character)
        return parser.can_end()

    def test_schema_cardinality_and_exact_shape(self):
        single = temporal_json_schema("single")["properties"]["segments"]
        multi = temporal_json_schema("multi")["properties"]["segments"]
        self.assertEqual(single["maxItems"], 1)
        self.assertEqual(multi["maxItems"], 4)
        self.assertEqual((multi["items"]["minItems"], multi["items"]["maxItems"]), (2, 2))
        self.assertFalse(temporal_json_schema("multi")["additionalProperties"])

    def test_character_parser_accepts_valid_and_rejects_invalid_shapes(self):
        self.assertTrue(self._grammar_accepts('{"segments":[]}', "single"))
        self.assertTrue(self._grammar_accepts('{"segments":[[12.5,27.0]]}', "single"))
        self.assertTrue(self._grammar_accepts(
            '{"segments":[[0,1],[2,3],[4,5],[6,7]]}', "multi"
        ))
        self.assertFalse(self._grammar_accepts('{"segments":[0,1]}', "multi"))
        self.assertFalse(self._grammar_accepts(
            '{"segments":[[0,1],[2,3]]}', "single"
        ))
        self.assertFalse(self._grammar_accepts(
            '{"segments":[[0,1],[2,3],[4,5],[6,7],[8,9]]}', "multi"
        ))
        self.assertFalse(self._grammar_accepts('{"segments":[]', "multi"))

    def test_real_qwen_tokenizer_prefix_function_and_cache(self):
        model_path = Path("/home/inspur/aic_video_work/models/Qwen3-VL-4B-Instruct")
        if not model_path.exists():
            self.skipTest("real Qwen tokenizer exists only on the remote host")
        try:
            import torch
            from transformers import AutoTokenizer
        except ImportError as exc:
            self.skipTest(str(exc))
        tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True)
        before = qwen_io.tokenizer_data_cache_size()
        prefix_fn = qwen_io.build_temporal_prefix_allowed_tokens_fn(tokenizer, "single")
        after_first = qwen_io.tokenizer_data_cache_size()
        qwen_io.build_temporal_prefix_allowed_tokens_fn(tokenizer, "multi")
        after_second = qwen_io.tokenizer_data_cache_size()
        self.assertEqual(after_first, before + 1)
        self.assertEqual(after_second, after_first)

        prompt_ids = tokenizer.encode("arbitrary prompt", add_special_tokens=False)
        sent = torch.tensor(prompt_ids, dtype=torch.long)
        allowed = prefix_fn(0, sent)
        invalid_first = tokenizer.encode("plain text", add_special_tokens=False)[0]
        self.assertNotIn(invalid_first, allowed)
        for token in tokenizer.encode('{"segments":[]}', add_special_tokens=False):
            self.assertIn(token, allowed)
            sent = torch.cat([sent, torch.tensor([token], dtype=torch.long)])
            allowed = prefix_fn(0, sent)
        self.assertIn(tokenizer.eos_token_id, allowed)


class MetadataTests(unittest.TestCase):
    class DummyIds:
        def clone(self):
            return self

    class DummyInputs(dict):
        def __init__(self):
            super().__init__(input_ids=MetadataTests.DummyIds())
            self.input_ids = self["input_ids"]

        def to(self, device):
            return self

    class DummyProcessor:
        def __init__(self):
            self.kwargs = None

        def apply_chat_template(self, *args, **kwargs):
            return "rendered"

        def __call__(self, **kwargs):
            self.kwargs = kwargs
            return MetadataTests.DummyInputs()

    def test_metadata_is_required_and_decord_clip_is_local(self):
        messages = qwen_io.build_temporal_messages(
            "x.mp4", "prompt", clip_start_sec=25.0, clip_end_sec=55.0
        )
        self.assertLess(messages[0]["content"][0]["video_end"], 55.0)
        metadata = {
            "fps": 30.0,
            "frames_indices": [750, 900, 1649],
            "total_num_frames": 900,
            "video_backend": "decord",
        }
        fake_module = types.SimpleNamespace(
            process_vision_info=lambda *a, **k: (None, [(object(), metadata)], {"fps": [2.0]})
        )
        processor = self.DummyProcessor()
        with mock.patch.dict(sys.modules, {"qwen_vl_utils": fake_module}):
            encoded = qwen_io.encode_qwen3vl_messages(processor, messages)
        self.assertFalse(processor.kwargs["do_sample_frames"])
        passed = processor.kwargs["video_metadata"][0]
        self.assertEqual(passed["frames_indices"], [0, 150, 899])
        self.assertEqual(encoded.sampling[0]["first_source_frame"], 750)
        self.assertEqual(encoded.sampling[0]["first_timestamp_sec"], 0.0)
        self.assertAlmostEqual(encoded.sampling[0]["last_timestamp_sec"], 899 / 30.0)

    def test_missing_metadata_fails_closed(self):
        messages = qwen_io.build_temporal_messages("x.mp4", "prompt")
        fake_module = types.SimpleNamespace(
            process_vision_info=lambda *a, **k: (None, [object()], {})
        )
        with mock.patch.dict(sys.modules, {"qwen_vl_utils": fake_module}):
            with self.assertRaisesRegex(RuntimeError, "did not return video metadata"):
                qwen_io.encode_qwen3vl_messages(self.DummyProcessor(), messages)


class IndexAndSourceTests(unittest.TestCase):
    def test_query_and_source_group_are_preserved(self):
        rows = [{
            "video_id": "q1",
            "video_path": "/data/q1.mp4",
            "source_group": "source-A",
            "query": "person opens a door",
            "targetRatioWH": [9, 16],
        }]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "index.json"
            path.write_text(json.dumps(rows), encoding="utf-8")
            loaded = load_index(str(path))
        self.assertEqual(loaded[0]["query"], rows[0]["query"])
        self.assertEqual(loaded[0]["source_group"], "source-A")

    def test_jsonl_index_is_supported(self):
        rows = [
            {"video_id": "q1", "query": "one", "targetRatioWH": None},
            {"video_id": "q2", "query": "two"},
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "index.jsonl"
            path.write_text(
                "\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8"
            )
            loaded = load_index(str(path), allow_missing_target=True)
        self.assertEqual([row["query"] for row in loaded], ["one", "two"])
        self.assertEqual(loaded[0]["targetRatioWH"], [16.0, 9.0])

    def test_null_target_is_rejected_for_full_pipeline(self):
        rows = [{"video_id": "q1", "targetRatioWH": None}]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "index.json"
            path.write_text(json.dumps(rows), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "missing targetRatioWH"):
                load_index(str(path))

    def test_frozen_baseline_hash(self):
        baseline = ROOT / "inference" / "baseline_qwen3vl.py"
        if not baseline.exists():
            self.skipTest("frozen baseline exists only in remote deployment layout")
        import hashlib
        self.assertEqual(
            hashlib.sha256(baseline.read_bytes()).hexdigest(),
            "a522244712831e7fddc605bce73b083851b7353dac1ceb2a9e4f41b948733631",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
