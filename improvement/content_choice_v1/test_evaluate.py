"""Synthetic all-rater evaluation and independent mechanism admission checks.

Reported fixture numbers are hand-constructible temporal F1, never official
scores. Gate tests vary actual selected candidates rather than a fake oracle.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import unittest

from .evaluate import (
    admission_reasons, bootstrap_mean_interval, compare_selections,
    evaluate_pool, pair_accuracy,
)


def pool_fixture(count=2):
    sources, humans = {}, {}
    actions = [[0], [0, 1], [2], []]
    for index in range(count):
        sid = "check" + str(index)
        sha = hashlib.sha256(sid.encode("ascii")).hexdigest()
        candidates = [dict(slot=slot, selected_ordinals=list(action), feature=[0.0] * 131,
            permuted_feature=[0.0] * 131, suffix_tokens=5,
            mean_logprob=-1.0, logprob_sum=-5.0, contrast=0.0)
            for slot, action in enumerate(actions)]
        sources[sid] = dict(status="ACCEPTED", source_id=sid, source_sha256=sha,
                            native_count=4, candidates=candidates)
        humans[sid] = dict(source_sha256=sha, clock=dict(normalized_exact_pts=["0", "1", "2", "3"]),
            raters=[{0, 1}, {0, 1, 2}], known_masks=[[True] * 4, [True] * 4], baseline={0})
    return sources, humans


def score_map(sources, **roles):
    return {role: {sid: list(scores) for sid in sources} for role, scores in roles.items()}


GOOD = [2, 3, 1, 0]  # Utility order: slot1 > slot0 > slot2 > empty.
GREEDY = [3, 2, 1, 0]


class SourceMetricChecks(unittest.TestCase):
    def test_fixed_pool_oracle_regret_and_actual_selection_are_separate(self):
        sources, humans = pool_fixture()
        report, selected = evaluate_pool(sources, humans, score_map(sources, contrast=GOOD, raw=GREEDY))
        self.assertAlmostEqual(report["macro"]["greedy"]["f1"], 7 / 12)
        self.assertAlmostEqual(report["macro"]["contrast"]["f1"], 0.9)
        self.assertAlmostEqual(report["oracle_macro"], 0.9)
        self.assertEqual(report["mean_regret"]["contrast"], 0.0)
        self.assertAlmostEqual(report["mean_regret"]["raw"], 0.9 - 7 / 12)
        self.assertEqual(selected["contrast"], {sid: {0, 1} for sid in sources})
        self.assertEqual(report["rankings"]["contrast"]["source_macro"], 1.0)
        self.assertAlmostEqual(report["rankings"]["raw"]["source_macro"], 5 / 6)
        self.assertTrue(report["oracle_is_reference_assisted_bound_not_a_predictor"])
        self.assertTrue(report["historical_exposure"])
        self.assertEqual(report["official_score"], "NOT_MEASURED")
        self.assertEqual(report["spatial_joint_utility"], "UNKNOWN_NO_BOUND_VIDEO_SPATIAL_REFERENCE")

    def test_video_macro_does_not_weight_long_sources_or_extra_raters_more(self):
        human = {}
        for sid, n, raters in (("short", 4, [{0}]), ("long", 100, [set(range(50))] * 3)):
            human[sid] = dict(source_sha256=hashlib.sha256(sid.encode()).hexdigest(),
                clock=dict(normalized_exact_pts=[str(i) for i in range(n)]), raters=raters,
                known_masks=[[True] * n for _ in raters], baseline={n - 1})
        greedy = {"short": {3}, "long": {99}}
        report = compare_selections(human, greedy, {"observation": {"short": {0}, "long": {99}}})
        self.assertEqual(report["macro"]["observation"]["f1"], 0.5)
        self.assertNotEqual(report["macro"]["observation"]["f1"], 0.25)  # Reviewer-count weighted.
        self.assertEqual(report["effects"]["observation"]["source_wins"], 1)

    def test_identity_and_native_length_mismatch_and_duplicate_media_are_rejected(self):
        sources, humans = pool_fixture()
        for mode in ("different_sha", "different_native_length", "duplicate_media"):
            a, b = deepcopy(sources), deepcopy(humans)
            if mode == "different_sha":
                b["check0"]["source_sha256"] = "f" * 64
            elif mode == "different_native_length":
                a["check0"]["native_count"] = 5
            else:
                a["check1"]["source_sha256"] = a["check0"]["source_sha256"]
                b["check1"]["source_sha256"] = b["check0"]["source_sha256"]
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                evaluate_pool(a, b, score_map(a, contrast=GOOD))

    def test_empty_remains_a_prediction_while_missing_failed_and_unknown_are_errors(self):
        sources, humans = pool_fixture()
        human = deepcopy(humans)
        human["check0"]["raters"] = [set(), set()]
        report, selected = evaluate_pool(sources, human, score_map(sources, observation=[0, 0, 0, 1]))
        self.assertEqual(selected["observation"], {"check0": set(), "check1": set()})
        self.assertEqual(report["macro"]["observation"]["f1"], 0.5)
        self.assertEqual(report["effects"]["observation"]["false_empty_sources"], ["check1"])
        for mode in ("missing_source", "missing_score", "failed_source", "unknown"):
            a, b = deepcopy(sources), deepcopy(humans)
            scores = score_map(a, observation=GOOD)
            if mode == "missing_source":
                del a["check1"]
            elif mode == "missing_score":
                del scores["observation"]["check1"]
            elif mode == "failed_source":
                a["check1"]["status"] = "FAILED"
            else:
                b["check1"]["known_masks"][0][2] = False
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                evaluate_pool(a, b, scores)

    def test_empty_protected_proxy_does_not_hide_a_new_false_empty_against_original_time(self):
        sources, humans = pool_fixture(1)
        humans["check0"]["baseline"] = set()
        report, _ = evaluate_pool(sources, humans, score_map(sources, observation=[0, 0, 0, 1]))
        self.assertEqual(report["per_source"][0]["frames"]["protected_proxy"], 0)
        self.assertGreater(report["per_source"][0]["frames"]["greedy"], 0)
        self.assertEqual(report["effects"]["observation"]["false_empty_sources"], ["check0"])
        self.assertIn("NEW_FALSE_EMPTY_COMPLETE_SOURCE", admission_reasons("observation", report,
                      observation_evidence=dict(changed_input_windows=1)))

    def test_action_duplicates_utility_ties_and_score_ties_have_distinct_denominators(self):
        sources, humans = pool_fixture(1)
        source, human = sources["check0"], humans["check0"]
        for candidate, action in zip(source["candidates"], [[0], [0], [1], []]):
            candidate["selected_ordinals"] = action
        human["raters"] = [{0, 1}, {0, 1}]
        correct = pair_accuracy(source, [1, 999, 1, 0], human)
        self.assertEqual(correct, dict(accuracy=1.0, non_tied_pairs=2, utility_ties_ignored=1))
        tied = pair_accuracy(source, [0, 999, 0, 0], human)
        self.assertEqual(tied["accuracy"], 0.5)
        for candidate in source["candidates"]:
            candidate["selected_ordinals"] = []
        undefined = pair_accuracy(source, [1, 1, 1, 1], human)
        self.assertIsNone(undefined["accuracy"])
        self.assertEqual(undefined["non_tied_pairs"], 0)

    def test_bootstrap_is_reproducible_source_level_diagnostic_not_a_gate(self):
        first = bootstrap_mean_interval([0.2, -0.1, 0.0], draws=128)
        self.assertEqual(first, bootstrap_mean_interval([0.2, -0.1, 0.0], draws=128))
        self.assertFalse(first["admission_test"])
        self.assertEqual(first["unit"], "complete_source")
        self.assertLessEqual(first["low"], first["high"])


class IndependentMechanismGateChecks(unittest.TestCase):
    def test_critic_positive_path_requires_both_content_controls_and_loso(self):
        sources, humans = pool_fixture()
        good, _ = evaluate_pool(sources, humans, score_map(sources, critic=GOOD, shape=GREEDY, permuted=GREEDY))
        self.assertEqual(admission_reasons("critic", good, oof=good), [])
        for comparator in ("shape", "permuted"):
            roles = dict(critic=GOOD, shape=GREEDY, permuted=GREEDY)
            roles[comparator] = GOOD
            tied, _ = evaluate_pool(sources, humans, score_map(sources, **roles))
            stops = admission_reasons("critic", tied, oof=good)
            self.assertIn("CROSS_F1_DID_NOT_BEAT_" + comparator.upper() + "_CONTROL", stops)
            self.assertIn("CROSS_UTILITY_ORDERING_DID_NOT_BEAT_" + comparator.upper() + "_CONTROL", stops)
        failed_oof, _ = evaluate_pool(sources, humans, score_map(sources, critic=GREEDY, shape=GOOD, permuted=GREEDY))
        stops = admission_reasons("critic", good, oof=failed_oof)
        self.assertIn("LOSO_F1_DID_NOT_BEAT_ORIGINAL_TIME", stops)
        self.assertIn("LOSO_UTILITY_ORDERING_DID_NOT_BEAT_SHAPE_ONLY_CONTROL", stops)
        with self.assertRaisesRegex(ValueError, "LOSO"):
            admission_reasons("critic", good)

    def test_oracle_and_old_dpo_metrics_cannot_admit_an_unchanged_critic(self):
        sources, humans = pool_fixture()
        failed, _ = evaluate_pool(sources, humans,
            score_map(sources, critic=GREEDY, shape=GOOD, permuted=GOOD))
        self.assertGreater(failed["oracle_macro"], failed["macro"]["critic"]["f1"])
        # Deliberately tempting but unrelated fields must be inert to this gate.
        failed["old_dpo_metrics"] = dict(f1=1.0, raw_accuracy=1.0, optimizer_updates=16)
        failed["oracle_macro"] = 1.0
        stops = admission_reasons("critic", failed, oof=failed)
        self.assertIn("NO_CHANGE_IN_ACTUAL_COMPLETE_SOURCE_SELECTION", stops)
        self.assertIn("CROSS_SOURCE_F1_DID_NOT_BEAT_ORIGINAL_TIME", stops)
        self.assertIn("CROSS_F1_DID_NOT_BEAT_SHAPE_CONTROL", stops)
        self.assertIn("CROSS_F1_DID_NOT_BEAT_PERMUTED_CONTROL", stops)

    def test_contrast_needs_raw_control_and_better_ordering_not_only_better_top_choice(self):
        sources, humans = pool_fixture()
        good, _ = evaluate_pool(sources, humans, score_map(sources, contrast=GOOD, raw=GREEDY))
        self.assertEqual(admission_reasons("contrast", good), [])
        same, _ = evaluate_pool(sources, humans, score_map(sources, contrast=GOOD, raw=GOOD))
        self.assertIn("CONDITIONAL_SCORE_DID_NOT_BEAT_SAME_POOL_RAW_MEAN_LOGP",
                      admission_reasons("contrast", same))
        # Top choice is ideal, but all three lower candidates are misordered.
        weak_order, _ = evaluate_pool(sources, humans,
            score_map(sources, contrast=[0, 3, 1, 2], raw=GREEDY))
        self.assertGreater(weak_order["macro"]["contrast"]["f1"], weak_order["macro"]["raw"]["f1"])
        self.assertIn("CONDITIONAL_SCORE_DID_NOT_IMPROVE_FULL_SOURCE_UTILITY_ORDERING",
                      admission_reasons("contrast", weak_order))

    def test_uninformative_source_cannot_disappear_from_ordering_coverage_gate(self):
        sources, humans = pool_fixture()
        for candidate in sources["check1"]["candidates"]:
            candidate["selected_ordinals"] = []
        report, _ = evaluate_pool(sources, humans, score_map(sources, contrast=GOOD, raw=GREEDY))
        self.assertEqual(report["rankings"]["contrast"]["source_coverage"], 1)
        self.assertEqual(report["rankings"]["contrast"]["total_sources"], 2)
        self.assertIn("CONDITIONAL_SCORE_DID_NOT_IMPROVE_FULL_SOURCE_UTILITY_ORDERING",
                      admission_reasons("contrast", report))

    def test_observation_needs_actual_changed_input_and_false_empty_can_stop_macro_gain(self):
        sources, humans = pool_fixture()
        good, _ = evaluate_pool(sources, humans, score_map(sources, observation=GOOD))
        self.assertEqual(admission_reasons("observation", good,
                         observation_evidence=dict(changed_input_windows=1)), [])
        self.assertIn("NO_NEW_ACTUAL_VISUAL_OBSERVATION", admission_reasons("observation", good,
                      observation_evidence=dict(changed_input_windows=0)))
        refs, greedy, current = {}, {}, {}
        for sid in ("improved_a", "improved_b", "false_empty"):
            refs[sid] = dict(source_sha256=hashlib.sha256(sid.encode()).hexdigest(),
                clock=dict(normalized_exact_pts=["0", "1", "2"]),
                raters=[{0, 1}], known_masks=[[True] * 3], baseline={0, 1} if sid == "false_empty" else {2})
            greedy[sid] = {0, 1} if sid == "false_empty" else {2}
            current[sid] = set() if sid == "false_empty" else {0, 1}
        report = compare_selections(refs, greedy, dict(observation=current))
        self.assertGreater(report["macro"]["observation"]["f1"], report["macro"]["greedy"]["f1"])
        self.assertIn("NEW_FALSE_EMPTY_COMPLETE_SOURCE", admission_reasons("observation", report,
                      observation_evidence=dict(changed_input_windows=3)))


if __name__ == "__main__":
    unittest.main()
