"""Actual NumPy ridge solves against synthetic, independently known objectives.

These fixtures exercise estimator mathematics and split isolation. They do not
stand in for frozen-Qwen features, media annotations or a scientific pass.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
from itertools import combinations
from pathlib import Path
import tempfile
import unittest

import numpy as np

from .contracts import save_new, strict_load
from .critic import FEATURE_KINDS, fit_pairwise, fit_with_loso, full_utility, score_source


def toy_source(sid, actions, coordinates, *, n=6):
    sha = hashlib.sha256(sid.encode("ascii")).hexdigest()
    candidates = []
    for slot, (selected, coords) in enumerate(zip(actions, coordinates)):
        feature = list(coords) + [0.0] * (131 - len(coords))
        shifted = [-feature[0], feature[1] + feature[0]] + feature[2:]
        candidates.append(dict(slot=slot, selected_ordinals=list(selected),
            feature=feature, permuted_feature=shifted, suffix_tokens=4,
            mean_logprob=-1.0, logprob_sum=-4.0, contrast=0.0))
    return dict(status="ACCEPTED", source_id=sid, source_sha256=sha,
                native_count=n, candidates=candidates)


def human_for(source, raters):
    n = source["native_count"]
    return dict(source_sha256=source["source_sha256"],
        clock=dict(normalized_exact_pts=[str(i) for i in range(n)], physical_end_exact=str(n)),
        raters=[set(row) for row in raters], known_masks=[[True] * n for _ in raters], baseline={0})


def small_problem(count=4):
    sources, humans = {}, {}
    actions = [[0], [0, 1], [3], []]
    for index in range(count):
        sid = "source" + str(index)
        coordinates = [[(index + 1) * (slot - 1.0), (-1.0) ** slot * (index + 2) / (slot + 1)]
                       for slot in range(4)]
        source = toy_source(sid, actions, coordinates)
        for slot, candidate in enumerate(source["candidates"]):
            # Keep genuine shape channels explicit and common to both views.
            shape = [len(actions[slot]) / 6, float(bool(actions[slot])) / 6, (4 + slot) / 512]
            candidate["feature"][-3:] = shape
            candidate["permuted_feature"][-3:] = shape
        sources[sid] = source
        humans[sid] = human_for(source, [{index % 4}, {0, (index + 1) % 4}])
    return sources, humans


def independent_augmented_least_squares(sources, humans, kind):
    """Independent augmented-design least squares, not the normal-equation path."""
    groups = {}
    for sid, source in sorted(sources.items()):
        seen, group = set(), []
        for candidate in source["candidates"]:
            action = tuple(candidate["selected_ordinals"])
            if action not in seen:
                seen.add(action)
                value = candidate["permuted_feature"] if kind == "permuted" else candidate["feature"]
                vector = np.asarray(value[-3:] if kind == "shape" else value, dtype=np.float64)
                # Deliberately spell out ALL-reviewer complete-source F1 here.
                scores = []
                for truth in humans[sid]["raters"]:
                    denominator = len(action) + len(truth)
                    scores.append(2 * len(set(action).intersection(truth)) / denominator if denominator else 1.0)
                group.append((vector, sum(scores) / len(scores)))
        groups[sid] = group
    scale = np.std(np.stack([vector for group in groups.values() for vector, _ in group]), axis=0)
    scale[scale <= 1e-8] = 1.0
    rows, targets = [], []
    for group in groups.values():
        pairs = list(combinations(group, 2))
        for (left, a), (right, b) in pairs:
            factor = np.sqrt(1 / (len(groups) * len(pairs)))
            rows.append(factor * (left - right) / scale)
            targets.append(factor * (a - b))
    size = len(scale)
    design = np.vstack((np.asarray(rows), np.sqrt(0.01) * np.eye(size)))
    target = np.r_[targets, np.zeros(size)]
    beta = np.linalg.lstsq(design, target, rcond=None)[0]
    return beta / scale


class FullSourceUtilityChecks(unittest.TestCase):
    def test_complete_source_denominator_and_all_raters_not_best_rater(self):
        source = toy_source("utility", [[0], [1], [2], []], [[0], [1], [2], [3]])
        human = human_for(source, [{0, 3}, {0, 1, 2, 3}])
        self.assertAlmostEqual(full_utility({0}, human), (2 / 3 + 2 / 5) / 2)
        self.assertNotEqual(full_utility({0}, human), 1.0)  # Cropping truth to the chosen window.
        self.assertNotEqual(full_utility({0}, human), 2 / 3)  # Picking the best reviewer.
        self.assertEqual(full_utility(set(), human), 0.0)
        empty_human = human_for(source, [set()])
        self.assertEqual(full_utility(set(), empty_human), 1.0)
        self.assertEqual(full_utility({0}, empty_human), 0.0)

    def test_unknown_and_out_of_domain_reference_membership_are_rejected(self):
        sources, humans = small_problem(1)
        original = humans["source0"]
        for value in (False, None, 0, 1):
            bad = deepcopy(original)
            bad["known_masks"][0][2] = value
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "UNKNOWN"):
                full_utility({0}, bad)
        bad = deepcopy(original)
        bad["raters"][0].add(6)
        with self.assertRaisesRegex(ValueError, "domain"):
            full_utility({0}, bad)
        with self.assertRaisesRegex(ValueError, "domain"):
            full_utility({True}, original)


class RidgeAndIsolationChecks(unittest.TestCase):
    def test_actual_closed_form_matches_augmented_least_squares_for_all_ablations(self):
        sources, humans = small_problem()
        for kind in FEATURE_KINDS:
            with self.subTest(kind=kind):
                actual = fit_pairwise(sources, humans, kind=kind)
                expected = independent_augmented_least_squares(sources, humans, kind)
                np.testing.assert_allclose(actual["weights"], expected, rtol=2e-9, atol=2e-10)
                self.assertEqual(actual["solves"], 1)
                self.assertEqual(actual["backbone_updates"], 0)
                self.assertLess(actual["linear_solve_residual"], 1e-8)

    def test_source_equal_weight_beats_pair_count_in_an_analytic_sign_counterexample(self):
        # Abstract one-coordinate design: six pairs from A, one from B. A
        # contributes three positive slopes; B contributes one negative slope.
        # Pooling pair rows would choose a positive slope. Equal SOURCE mass
        # gives gram=.75, rhs=-.25 before scaling, and scale^2=1/3.
        a = toy_source("many-actions", [[0], [1], [2], []], [[1], [0], [0], [0]])
        b = toy_source("few-actions", [[0], [0], [0], []], [[-1], [-1], [-1], [0]])
        sources = {a["source_id"]: a, b["source_id"]: b}
        humans = {sid: human_for(source, [{0}]) for sid, source in sources.items()}
        fitted = fit_pairwise(sources, humans)
        self.assertEqual(fitted["training_pairs"], 7)
        self.assertAlmostEqual(fitted["weights"][0], -75 / 226, places=12)
        self.assertTrue(all(value == 0 for value in fitted["weights"][1:]))
        self.assertLess(fitted["weights"][0], 0)
        wrong_pooled_slope = (2 / 7) / (4 / 7 + 0.01 / 3)
        self.assertGreater(wrong_pooled_slope, 0)

    def test_loso_weights_are_invariant_to_held_source_labels_and_extreme_features(self):
        sources, humans = small_problem()
        before = fit_with_loso(sources, humans)
        held = "source3"
        changed_sources, changed_humans = deepcopy(sources), deepcopy(humans)
        for candidate in changed_sources[held]["candidates"]:
            candidate["feature"][0] = 100000 * candidate["feature"][0] + 777
            candidate["permuted_feature"][1] = 90000 * candidate["permuted_feature"][1] - 555
            candidate["feature"][-3] *= 1000
            candidate["permuted_feature"][-3] *= 1000
        changed_humans[held]["raters"] = [{5}, {5}]
        after = fit_with_loso(changed_sources, changed_humans)
        self.assertEqual(before["actual_linear_solves"], 3 * (len(sources) + 1))
        self.assertEqual(len(before["folds"]), 3 * len(sources))
        for kind in FEATURE_KINDS:
            old_fold = next(row for row in before["folds"] if row["feature_kind"] == kind and row["held_source"] == held)
            new_fold = next(row for row in after["folds"] if row["feature_kind"] == kind and row["held_source"] == held)
            self.assertEqual(old_fold["weight_sha256"], new_fold["weight_sha256"])
            self.assertNotIn(held, old_fold["fit_sources"])
            self.assertNotIn(sources[held]["source_sha256"], old_fold["fit_source_sha256"].values())
            self.assertEqual(old_fold["scale_fit_source_ids"], sorted(set(sources) - {held}))
            train = {sid: source for sid, source in sources.items() if sid != held}
            refs = {sid: value for sid, value in humans.items() if sid != held}
            direct = fit_pairwise(train, refs, kind=kind)
            self.assertEqual(after["out_of_fold_scores"][kind][held], score_source(direct, changed_sources[held]))
        # Ensure the intervention is strong enough to matter when it IS fit.
        self.assertNotEqual(before["heads"]["content"]["weights"], after["heads"]["content"]["weights"])

    def test_shape_and_permuted_controls_do_not_secretly_read_real_hidden(self):
        sources, humans = small_problem(3)
        changed = deepcopy(sources)
        for source in changed.values():
            for candidate in source["candidates"]:
                candidate["feature"][0] *= 100
                candidate["feature"][1] += candidate["slot"] ** 2
        for kind in ("shape", "permuted"):
            left = fit_pairwise(sources, humans, kind=kind)
            right = fit_pairwise(changed, humans, kind=kind)
            self.assertEqual(left["weights"], right["weights"])
            self.assertEqual(score_source(left, sources["source0"]), score_source(right, changed["source0"]))
        self.assertNotEqual(fit_pairwise(sources, humans)["weights"], fit_pairwise(changed, humans)["weights"])

    def test_saved_reloaded_head_has_identical_scores_and_changed_weights_change_scores(self):
        sources, humans = small_problem(3)
        for kind in FEATURE_KINDS:
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as directory:
                head = fit_pairwise(sources, humans, kind=kind)
                expected = score_source(head, sources["source1"])
                path = Path(directory) / "critic.json"
                save_new(path, head)
                reloaded = strict_load(path)
                self.assertEqual(reloaded, head)
                self.assertEqual(score_source(reloaded, sources["source1"]), expected)
                changed = deepcopy(reloaded)
                changed["weights"][0] += 0.25
                other_path = Path(directory) / "changed.json"
                save_new(other_path, changed)
                alternate = score_source(strict_load(other_path), sources["source1"])
                self.assertNotEqual(alternate, expected)
                self.assertEqual(score_source(strict_load(path), sources["source1"]), expected)
                bad = deepcopy(reloaded)
                bad["scaling_folded_into_inference_weights"] = False
                with self.assertRaises(ValueError):
                    score_source(bad, sources["source1"])

    def test_fit_rejects_duplicate_media_unknown_supervision_and_unregistered_ridge(self):
        sources, humans = small_problem(3)
        duplicate, duplicate_humans = deepcopy(sources), deepcopy(humans)
        duplicate["source1"]["source_sha256"] = duplicate["source0"]["source_sha256"]
        duplicate_humans["source1"]["source_sha256"] = duplicate_humans["source0"]["source_sha256"]
        with self.assertRaisesRegex(ValueError, "duplicates"):
            fit_with_loso(duplicate, duplicate_humans)
        wrong = deepcopy(humans)
        wrong["source1"]["source_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "identities"):
            fit_pairwise(sources, wrong)
        unknown = deepcopy(humans)
        unknown["source1"]["known_masks"][0][0] = False
        with self.assertRaisesRegex(ValueError, "UNKNOWN"):
            fit_pairwise(sources, unknown)
        with self.assertRaisesRegex(ValueError, "Fixed ridge"):
            fit_pairwise(sources, humans, ridge=0.1)


if __name__ == "__main__":
    unittest.main()
