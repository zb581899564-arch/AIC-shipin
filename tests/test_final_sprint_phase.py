"""Synthetic CPU contract checks only; not model or video-quality validation."""
from fractions import Fraction
import itertools
import unittest
from unittest import mock

from improvement.final_sprint_v1.observation import plan_clips
from improvement.final_sprint_v1.qwen_runtime import (
    PHASES, TRANSITIONS, ORIGINAL_BASE_CANONICAL_SHA256, ORIGINAL_BASE_PARAMETERS, QwenRuntime,
    _commit_phase_cache, _original_base_identity,
)
from improvement.final_sprint_v1.temporal import assemble_events, select_event_budget, select_source


def source(points=None, end="4"):
    points = [str(Fraction(index, 4)) for index in range(16)] if points is None else points
    return dict(video_id="synthetic_source", media=dict(path="/synthetic/not-read.mp4", bytes=1, sha256="a" * 64),
                width=320, height=240, n_frames=len(points), normalized_exact_pts=points,
                physical_end_exact=end, targetRatioWH=[9, 16])


def results(item, selections):
    output = []
    for clip, states in zip(plan_clips(item), selections):
        rows = []
        for group, (cell, chosen) in enumerate(zip(clip["cells"], states)):
            alternatives = []
            for index, phase in enumerate(PHASES):
                score = -0.1 if phase == chosen else -1.0
                alternatives.append(dict(phase=phase, token_ids=[index, 8],
                    token_log_probabilities=[score, score], log_probability_sum=2 * score,
                    mean_log_probability=score))
            rows.append(dict(group=group, cell=cell, phase=chosen, alternatives=alternatives,
                             selected_minus_ordinary=0.0 if chosen == "ordinary" else 0.9))
        output.append(dict(clip=clip, phases=rows, status="MODEL_OK", no_global_source_prefix=True,
                           training_updates=0, input_proof=dict(physical_source_sha256=item["media"]["sha256"])))
    return output


class NativePhaseContracts(unittest.TestCase):
    def test_vfr_plan_partitions_every_native_frame_and_exact_duration(self):
        item = source(["0", "1/20", "1/5", "7/20", "1/2", "3/4", "4/5", "1", "21/20", "3/2"], "17/10")
        clips = plan_clips(item)
        cells = [cell for clip in clips for cell in clip["cells"]]
        self.assertEqual([frame for cell in cells for frame in range(cell["first"], cell["stop"])], list(range(10)))
        total = sum((Fraction(cell["end_exact"]) - Fraction(cell["start_exact"]) for cell in cells), Fraction(0))
        self.assertEqual(total, Fraction("17/10"))
        self.assertTrue(all(len(clip["sample_ordinals"]) == len(set(clip["sample_ordinals"])) for clip in clips))

    def test_action_completion_ablation_changes_only_selected_event_support(self):
        item = source()
        evidence = results(item, [["setup", "apex"], ["ordinary", "ordinary"],
                                  ["ordinary", "ordinary"], ["ordinary", "ordinary"]])
        complete = select_source(item, evidence, policy="event")
        apex = select_source(item, evidence, policy="apex")
        self.assertEqual(complete["selected_event_ids"], apex["selected_event_ids"])
        self.assertEqual(complete["frames"], [0, 1, 2, 3])
        self.assertEqual(apex["frames"], [2, 3])
        self.assertEqual(complete["budget"]["actual_event_duration_exact"], "1")

    def test_all_ordinary_is_legal_empty_not_inference_failure(self):
        item = source()
        evidence = results(item, [["ordinary", "ordinary"]] * 4)
        result = select_source(item, evidence)
        self.assertEqual(result["status"], "LEGAL_EMPTY")
        self.assertEqual(result["frames"], [])

    def test_failed_or_missing_clip_cannot_be_converted_to_empty(self):
        item = source()
        evidence = results(item, [["ordinary", "ordinary"]] * 4)
        with self.assertRaisesRegex(ValueError, "Every physical"):
            select_source(item, evidence[:-1])
        evidence[0]["status"] = "INFERENCE_FAILURE"
        with self.assertRaisesRegex(ValueError, "Missing, failed"):
            select_source(item, evidence)

    def test_unfinished_setup_is_not_invented_apex(self):
        item = source()
        evidence = results(item, [["setup", "ordinary"], ["ordinary", "ordinary"],
                                  ["ordinary", "ordinary"], ["ordinary", "ordinary"]])
        actual = select_source(item, evidence)
        self.assertEqual(actual["frames"], [])
        self.assertEqual(actual["rejected_partial_arcs"][0]["reason"], "SETUP_WITHOUT_OBSERVED_APEX")

    def test_cyclic_phase_or_tampered_margin_fails(self):
        item = source()
        evidence = results(item, [["resolution", "apex"], ["ordinary", "ordinary"],
                                  ["ordinary", "ordinary"], ["ordinary", "ordinary"]])
        with self.assertRaisesRegex(ValueError, "Invalid/cyclic"):
            assemble_events(item, evidence)
        evidence = results(item, [["setup", "apex"], ["ordinary", "ordinary"],
                                  ["ordinary", "ordinary"], ["ordinary", "ordinary"]])
        evidence[0]["phases"][0]["selected_minus_ordinary"] = 40
        with self.assertRaisesRegex(ValueError, "margin"):
            assemble_events(item, evidence)

    def test_duration_dp_agrees_with_exhaustive_feasible_subsets(self):
        events = [dict(event_id=str(index), start_exact="0", end_exact=str(Fraction(cost, 1000)),
                       evidence_mean_margin=utility)
                  for index, (cost, utility) in enumerate([(11, .8), (13, .9), (21, 1.4), (23, 1.0), (40, 1.5)])]
        actual, receipt = select_event_budget(events, Fraction(1, 5), segment_penalty=.15)
        feasible = []
        for bits in itertools.product((0, 1), repeat=len(events)):
            chosen = tuple(i for i, flag in enumerate(bits) if flag)
            cost = sum(Fraction(events[i]["end_exact"]) for i in chosen)
            score = sum(events[i]["evidence_mean_margin"] - .15 for i in chosen)
            if cost <= Fraction(1, 20):
                feasible.append((score, cost, chosen))
        best = min(feasible, key=lambda row: (-row[0], row[1], len(row[2]), row[2]))
        self.assertEqual(actual, list(best[2]))
        self.assertAlmostEqual(receipt["objective"], best[0])

    def test_single_frame_is_explicit_unique_observation_with_processor_padding(self):
        clips = plan_clips(source(["0"], "1/30"))
        self.assertEqual(clips[0]["sample_ordinals"], [0])
        self.assertEqual(clips[0]["implicit_last_frame_padding"], 1)
        self.assertEqual(clips[0]["cells"][0]["stop"], 1)

    def test_committed_branch_removes_all_right_padding(self):
        class Cache:
            def __init__(self):
                self.length, self.selected = 19, None
            def get_seq_length(self):
                return self.length
            def batch_select_indices(self, indices):
                self.selected = indices
            def crop(self, length):
                self.length = min(self.length, length)
        cache = Cache()
        actual = _commit_phase_cache(cache, [2], prefix_length=15, suffix_length=2)
        self.assertIs(actual, cache)
        self.assertEqual(cache.selected, [2])
        self.assertEqual(cache.get_seq_length(), 17)
        with self.assertRaisesRegex(ValueError, "shorter"):
            _commit_phase_cache(cache, [0], prefix_length=17, suffix_length=1)

    def test_base_identity_reuses_exact_historical_hash_and_freezes_first(self):
        class Parameter:
            requires_grad = True
            def requires_grad_(self, enabled):
                self.requires_grad = enabled
        parameter = Parameter()
        model = mock.Mock()
        model.parameters.return_value = [parameter]
        def canonical(base, torch):
            self.assertIs(base, model)
            self.assertFalse(parameter.requires_grad)
            return {"sha256": ORIGINAL_BASE_CANONICAL_SHA256, "parameters": ORIGINAL_BASE_PARAMETERS,
                    "method": "sorted canonical names and all unique frozen parameter bytes"}
        with mock.patch("improvement.native_preference_v1.runtime.canonical_frozen_hash", side_effect=canonical) as hasher:
            identity = _original_base_identity(model, object())
        hasher.assert_called_once()
        self.assertTrue(identity["verified_before_adapter"])
        self.assertEqual(identity["hash_calls_this_load"], 1)
        self.assertEqual(len(identity["hash_function_file"]["sha256"]), 64)

    def test_parameter_receipt_proof_is_identical_across_load_durations(self):
        runtime = QwenRuntime({"revision": "exact-revision"})
        runtime.original_base_identity = {
            "sha256": ORIGINAL_BASE_CANONICAL_SHA256, "parameters": ORIGINAL_BASE_PARAMETERS,
            "method": "sorted canonical names and all unique frozen parameter bytes",
            "expected_sha256": ORIGINAL_BASE_CANONICAL_SHA256, "verified_before_adapter": True,
            "hash_calls_this_load": 1,
            "hash_function": "improvement.native_preference_v1.runtime.canonical_frozen_hash",
            "hash_function_file": {"path": "/exact/runtime.py", "bytes": 100, "sha256": "a" * 64},
            "wall_seconds": 7.3,
        }
        first = runtime._parameter_loading_proof()
        runtime.original_base_identity["wall_seconds"] = 91.5
        runtime.counts["physical_model_forwards"] = 17000
        second = runtime._parameter_loading_proof()
        self.assertEqual(first, second)
        self.assertNotIn("wall_seconds", second["original_base_identity"])
        self.assertNotIn("counts", second)

    def test_correct_parameter_count_does_not_authorize_wrong_base_identity(self):
        model = mock.Mock()
        model.parameters.return_value = []
        with mock.patch("improvement.native_preference_v1.runtime.canonical_frozen_hash",
                        return_value={"sha256": "0" * 64, "parameters": ORIGINAL_BASE_PARAMETERS}):
            with self.assertRaisesRegex(ValueError, "canonical frozen"):
                _original_base_identity(model, object())


if __name__ == "__main__":
    unittest.main()
