"""Synthetic CPU checks of complete-source composition, never media quality.

Two unequal-duration windows deliberately have different locally best slots.
No model, tokenizer, Torch tensor, media or private reference is loaded here.
"""
from __future__ import annotations

from copy import deepcopy
import unittest

from .selection import (
    aggregate_source, choose, fixed_scores, unique_candidates,
    validate_source_candidates,
)


def two_window_fixture():
    sid, sha = "synthetic-source", "1" * 64
    clock = dict(normalized_exact_pts=[str(i) for i in range(8)], physical_end_exact="8")
    requests, windows = {}, {}
    # Insert the later window first to ensure dict order is not temporal order.
    specifications = (
        ("later", "2", "8", [[6], [2], [6], []], [21, 22, 23, 999], 10.0, -12.0, -10.0),
        ("earlier", "0", "2", [[0], [1], [0], []], [11, 999], 2.0, -2.0, -6.0),
    )
    for uid, left, right, selections, ids, hidden, lp, shifted_lp in specifications:
        requests[uid] = dict(sid=sid, source_sha256=sha,
            plan=dict(window_start_exact=left, window_end_exact=right))
        slots = []
        for slot, selected in enumerate(selections):
            feature = [hidden + slot] + [0.0] * 127
            shifted = [-hidden - slot] + [0.0] * 127
            slots.append(dict(slot=slot, status="ACCEPTED", selected_ordinals=selected,
                ids=list(ids), real=dict(feature=feature, logprob=lp, suffix_tokens=len(ids)),
                permuted=dict(feature=shifted, logprob=shifted_lp, suffix_tokens=len(ids))))
        windows[uid] = dict(status="ACCEPTED", uid=uid, source_id=sid, slots=slots)
    return sid, sha, clock, requests, windows


class CompleteSourceCompositionChecks(unittest.TestCase):
    def test_one_same_slot_source_cannot_become_a_window_oracle_hybrid(self):
        source = aggregate_source(*two_window_fixture())
        self.assertEqual(source["window_ids"], ["earlier", "later"])
        self.assertEqual([c["selected_ordinals"] for c in source["candidates"]],
                         [[0, 6], [1, 2], [0, 6], []])
        # An external reference {0,2} would prefer slot0 in the first window,
        # slot1 in the second. That perfect hybrid is not an available action.
        truth = {0, 2}
        utilities = [2 * len(set(c["selected_ordinals"]) & truth)
                     / (len(c["selected_ordinals"]) + len(truth))
                     for c in source["candidates"]]
        self.assertEqual(max(utilities), 0.5)
        self.assertNotIn([0, 2], [c["selected_ordinals"] for c in source["candidates"]])
        self.assertEqual(choose(source, [0.0, 5.0, 1.0, -1.0])["selected_ordinals"], [1, 2])
        self.assertFalse(source["labels_read"])

    def test_hidden_is_duration_weighted_but_complete_logp_is_token_weighted(self):
        source = aggregate_source(*two_window_fixture())
        first, second = source["candidates"][:2]
        self.assertEqual(source["window_weights"], {"earlier": 0.25, "later": 0.75})
        self.assertEqual(first["feature"][0], 8.0)  # .25*2 + .75*10, not a token mean.
        self.assertEqual(first["permuted_feature"][0], -8.0)
        self.assertEqual(first["suffix_tokens"], 6)  # Both supplied suffixes include their EOS.
        self.assertEqual(first["logprob_sum"], -14.0)
        self.assertAlmostEqual(first["mean_logprob"], -14 / 6)
        self.assertNotAlmostEqual(first["mean_logprob"], (-2 / 2 - 12 / 4) / 2)
        self.assertAlmostEqual(first["contrast"], (-14 - (-16)) / 6)
        self.assertEqual(first["feature"][-3], 2 / 8)
        self.assertEqual(first["feature"][-2], 2 / 12)
        # Frames1 and2 touch across a window boundary: one SOURCE run, not two.
        self.assertEqual(second["feature"][-2], 1 / 12)
        self.assertEqual(first["feature"][-1], 6 / 1024)
        self.assertEqual(fixed_scores(source, "raw"), [c["mean_logprob"] for c in source["candidates"]])
        self.assertEqual(fixed_scores(source, "contrast"), [c["contrast"] for c in source["candidates"]])

    def test_duplicate_native_actions_reuse_first_slot_but_keep_four_decisions(self):
        source = aggregate_source(*two_window_fixture())
        candidates = source["candidates"]
        self.assertEqual(candidates[0]["native_selection_sha256"], candidates[2]["native_selection_sha256"])
        self.assertNotEqual(candidates[0]["feature"], candidates[2]["feature"])
        self.assertEqual([c["slot"] for c in unique_candidates(source)], [0, 1, 3])
        self.assertEqual(len(source["candidates"]), 4)
        self.assertEqual(choose(source, [1, 1, 1, 1])["slot"], 0)
        # A differently worded duplicate may win scoring, but cannot add frames.
        self.assertEqual(choose(source, [0, 0, 9, 0])["selected_ordinals"], [0, 6])
        for bad in ([1, 2, 3], [0, float("nan"), 0, 0]):
            with self.assertRaises(ValueError):
                choose(source, bad)

    def test_legal_empty_is_preserved_but_missing_failed_windows_are_rejected(self):
        fixture = two_window_fixture()
        source = aggregate_source(*fixture)
        self.assertTrue(source["candidates"][3]["legal_empty"])
        self.assertEqual(choose(source, [0, 0, 0, 1])["selected_ordinals"], [])
        for mode in ("missing", "failed_window", "failed_candidate"):
            args = deepcopy(fixture)
            if mode == "missing":
                del args[4]["later"]
            elif mode == "failed_window":
                args[4]["later"]["status"] = "FAILED"
            else:
                args[4]["later"]["slots"][3]["status"] = "FAILED"
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                aggregate_source(*args)

    def test_missing_or_noncontiguous_physical_coverage_is_not_clipped_away(self):
        for mode in ("gap", "overlap", "truncated_end", "foreign_source"):
            args = deepcopy(two_window_fixture())
            if mode == "gap":
                args[3]["later"]["plan"]["window_start_exact"] = "3"
            elif mode == "overlap":
                args[3]["later"]["plan"]["window_start_exact"] = "1"
            elif mode == "truncated_end":
                args[2]["physical_end_exact"] = "9"
            else:
                args[3]["later"]["source_sha256"] = "2" * 64
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                aggregate_source(*args)

    def test_native_membership_must_match_its_window_not_only_the_source(self):
        # Valid source-native frame7 is outside the first window [0,2).
        args = deepcopy(two_window_fixture())
        args[4]["earlier"]["slots"][0]["selected_ordinals"] = [7]
        with self.assertRaises(ValueError):
            aggregate_source(*args)
        for selected in ([0, 0], [1, 0], [8], [True]):
            args = deepcopy(two_window_fixture())
            args[4]["earlier"]["slots"][0]["selected_ordinals"] = selected
            with self.subTest(selected=selected), self.assertRaises(ValueError):
                aggregate_source(*args)

    def test_window_membership_keeps_fraction_precision_at_the_half_open_endpoint(self):
        args = deepcopy(two_window_fixture())
        # This actual native PTS is below2, although binary float rounds it to2.
        numerator = 2 * 10 ** 40 - 1
        args[2]["normalized_exact_pts"][1] = str(numerator) + "/" + str(10 ** 40)
        source = aggregate_source(*args)
        self.assertEqual(source["candidates"][1]["selected_ordinals"], [1, 2])
        # Exact frame2 belongs only to [2,8), never to [0,2).
        args[4]["earlier"]["slots"][0]["selected_ordinals"] = [2]
        with self.assertRaises(ValueError):
            aggregate_source(*args)

    def test_scored_suffix_must_include_the_same_complete_tokens_and_eos(self):
        for mode in ("real_eos_omitted", "shifted_shorter", "nonfinite_hidden"):
            args = deepcopy(two_window_fixture())
            case = args[4]["earlier"]["slots"][0]
            if mode == "real_eos_omitted":
                case["real"]["suffix_tokens"] -= 1
            elif mode == "shifted_shorter":
                case["permuted"]["suffix_tokens"] -= 1
            else:
                case["real"]["feature"][7] = float("inf")
            with self.subTest(mode=mode), self.assertRaises(ValueError):
                aggregate_source(*args)

    def test_absent_counterfactual_stays_absent_instead_of_zero_score(self):
        args = deepcopy(two_window_fixture())
        del args[4]["later"]["slots"][0]["permuted"]
        source = aggregate_source(*args)
        self.assertIsNone(source["candidates"][0]["contrast"])
        self.assertIsNone(source["candidates"][0]["permuted_feature"])
        with self.assertRaises(ValueError):
            fixed_scores(source, "contrast")
        malformed = deepcopy(source)
        malformed["candidates"][3]["selected_ordinals"] = [0]
        with self.assertRaisesRegex(ValueError, "explicit"):
            validate_source_candidates(malformed)


if __name__ == "__main__":
    unittest.main()
