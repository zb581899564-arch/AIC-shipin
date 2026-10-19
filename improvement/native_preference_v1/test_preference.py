"""Synthetic CPU tests for risks introduced by the native preference contract."""

from fractions import Fraction as F
import itertools
import json
import math
import unittest

from improvement.native_preference_v1.preference import (
    CandidateRepresentationError,
    PreferenceContractError,
    UnknownSupervisionError,
    causal_positions,
    contiguous_runs,
    dpo_loss,
    make_preference_pairs,
    mean_source_utility,
    native_selection,
    parse_answer,
    reflect_selection,
    selection_answer,
    window_bounds,
)


class AnswerContractTests(unittest.TestCase):
    def test_empty_and_exact_decimal_json(self):
        self.assertEqual(parse_answer('{"segments":[]}', "1"), [])
        self.assertEqual(parse_answer('{"segments":[[1e-1,0.3],[0.3,1]]}', "1"),
                         [(F(1, 10), F(3, 10)), (F(3, 10), F(1))])

    def test_malformed_never_becomes_empty(self):
        invalid = [
            "", "null", "[]", '{"segments":null}', '{"segments":{},"x":0}',
            '{"segments":[],"segments":[]}', '{"segments":[],"x":0}',
            '{"segments":[[true,1]]}', '{"segments":[["0",1]]}',
            '{"segments":[[0,NaN]]}', '{"segments":[[0,Infinity]]}',
            '{"segments":[[0,-Infinity]]}', '{"segments":[[0,1e999999]]}',
            '{"segments":[[0,1,2]]}', '{"segments":[[0,0]]}',
            '{"segments":[[-0.1,0.5]]}', '{"segments":[[0,1.1]]}',
            '{"segments":[[0.5,0.8],[0.2,0.3]]}',
            '{"segments":[[0,0.6],[0.5,1]]}', '{"segments":[]} trailing',
        ]
        for text in invalid:
            with self.subTest(text=text), self.assertRaises(PreferenceContractError):
                parse_answer(text, "1")

    def test_fixed_segment_limit(self):
        text = json.dumps({"segments": [[2 * i, 2 * i + 1] for i in range(7)]})
        with self.assertRaises(PreferenceContractError):
            parse_answer(text, "14")
        self.assertEqual(len(parse_answer(text, "14", max_segments=7)), 7)

    def test_fraction_boundaries_and_union(self):
        clock = ["0", "1/10", "1/5", "3/10", "2/5"]
        intervals = [(F(0), F(1, 5)), (F(1, 10), F(3, 10)),
                     (F(1, 10), F(3, 10))]
        self.assertEqual(native_selection(intervals, clock, "1/10", "2/5"), {1, 2, 3})
        self.assertEqual(native_selection([(F(0), F(1, 5))], clock, "1/10", "2/5"), {1, 2})
        self.assertEqual(window_bounds(clock, "1/10", "3/10"), (1, 3))

    def test_do_not_substitute_binary_float_or_bad_clock(self):
        with self.assertRaises(PreferenceContractError):
            native_selection([(0, 1)], [0.0, 0.5], 0, 1)
        for clock in ([], ["0", "0"], ["1", "0"], ["-1", "0"]):
            with self.subTest(clock=clock), self.assertRaises(PreferenceContractError):
                native_selection([], clock, "0", "1")


class NativeCandidateTests(unittest.TestCase):
    def test_safe_decimal_roundtrip_all_vfr_selections(self):
        clock = [F(0), F(1, 10), F(1, 3), F(2, 3), F(1001, 1000), F(19, 11), F(2)]
        # Exhaust all finite selections, including disjoint, touching, empty,
        # first/last-frame and fractional-window cases, against the native clock.
        for start, end in [(F(0), F(5, 2)), (F(1, 7), F(13, 7))]:
            allowed = [i for i, t in enumerate(clock) if start <= t < end]
            for flags in itertools.product((False, True), repeat=len(allowed)):
                selected = {i for i, keep in zip(allowed, flags) if keep}
                answer = selection_answer(selected, clock, start, end)
                self.assertEqual(native_selection(parse_answer(answer, end-start), clock, start, end), selected)
                self.assertEqual(answer, selection_answer(selected, clock, start, end))
                self.assertTrue(all(type(v) in (int, float)
                                    for pair in json.loads(answer)["segments"] for v in pair))

    def test_tiny_gap_is_rejected_instead_of_widening_frozen_grammar(self):
        clock = [F(0), F(1, 10**30), F(2, 10**30), F(3, 10**30)]
        # Exact rational encoding could use 31 decimals, but the production
        # grammar cannot generate it.  Reject, never round or enlarge a gap.
        with self.assertRaises(CandidateRepresentationError):
            selection_answer({1, 2}, clock, F(0), F(4, 10**30))
        self.assertEqual(make_preference_pairs([{1}], [{1}], set(), clock,
                                              F(0), F(4, 10**30)), [])

    def test_canonical_answer_matches_actual_frozen_number_grammar(self):
        from improvement.bottleneck_24h_v1.summary_grammar6 import BoundedSegmentsGrammar
        clock = [F(i, 3) for i in range(10)]
        answer = selection_answer({1, 2, 5, 9}, clock, 0, F(10, 3))
        grammar = BoundedSegmentsGrammar(F(10, 3))
        self.assertTrue(grammar.complete(answer))
        self.assertTrue(all(grammar.valid_prefix(answer[:i]) for i in range(len(answer)+1)))

    def test_generation_grammar_uses_the_exact_physical_fraction_endpoint(self):
        from improvement.bottleneck_24h_v1 import summary_grammar6 as grammar
        from improvement.native_preference_v1.run import validate_token_path

        class CharacterTokenizer:
            def convert_tokens_to_ids(self, text):
                return 999 if text == "<|im_end|>" else None

            def decode(self, ids, **_):
                return "".join(chr(value) for value in ids)

        duration = F(5, 7)
        outside = '{"segments":[[0,0.7142857142857143]]}'
        inside = '{"segments":[[0,0.7142857142857142]]}'
        # Rounding duration UP through float would permit a grammar-complete
        # answer that the exact native output parser must subsequently reject.
        self.assertTrue(grammar.BoundedSegmentsGrammar(float(duration)).complete(outside))
        self.assertFalse(grammar.BoundedSegmentsGrammar(duration).complete(outside))
        tokenizer, candidates = CharacterTokenizer(), frozenset(range(128))
        with self.assertRaisesRegex(ValueError, "prefix-reachable"):
            validate_token_path(tokenizer, [ord(c) for c in outside] + [999],
                                outside, duration, grammar, candidates)
        validate_token_path(tokenizer, [ord(c) for c in inside] + [999],
                            inside, duration, grammar, candidates)

    def test_cannot_encode_outside_window_or_too_many_runs(self):
        with self.assertRaises(PreferenceContractError):
            selection_answer({0}, range(10), 2, 8)
        with self.assertRaises(CandidateRepresentationError):
            selection_answer({0, 2, 4, 6, 8, 10, 12}, range(14), 0, 14)
        self.assertEqual(selection_answer(set(), range(3), 0, 3), '{"segments":[]}')

    def test_reflection_budget_runs_and_involution(self):
        selected = {2, 3, 6}
        reflected = reflect_selection(selected, 1, 9)
        self.assertEqual(reflected, {3, 6, 7})
        self.assertEqual(len(reflected), len(selected))
        self.assertEqual(len(contiguous_runs(reflected)), len(contiguous_runs(selected)))
        self.assertEqual(reflect_selection(reflected, 1, 9), selected)
        self.assertEqual(reflect_selection(set(), 3, 3), set())
        with self.assertRaises(PreferenceContractError):
            reflect_selection({0}, 1, 9)


class SourceUtilityTests(unittest.TestCase):
    def test_all_references_and_complete_source_denominator(self):
        # Two relevant frames outside the local candidate still count as GT.
        self.assertEqual(mean_source_utility({2}, [{2, 10, 11}]), 0.5)
        self.assertAlmostEqual(mean_source_utility({2}, [{2, 10, 11}, {2}]), 0.75)

    def test_empty_summary_choices(self):
        self.assertEqual(mean_source_utility(set(), [set()]), 1.0)
        self.assertEqual(mean_source_utility(set(), [{1}]), 0.0)
        self.assertEqual(mean_source_utility({1}, [set()]), 0.0)
        self.assertEqual(mean_source_utility(set(), [set(), {1}]), 0.5)
        with self.assertRaises(PreferenceContractError):
            mean_source_utility(set(), [])

    def test_unknown_is_not_a_negative_even_outside_prediction(self):
        for mask in ([True, False, True], [True, None, True], [True, 1, True]):
            with self.subTest(mask=mask), self.assertRaises(UnknownSupervisionError):
                mean_source_utility({0}, [{0}], known_masks=[mask])
        self.assertEqual(mean_source_utility({0}, [{0}], [[True] * 3]), 1.0)
        with self.assertRaises(PreferenceContractError):
            mean_source_utility({3}, [{0}], [[True] * 3])
        with self.assertRaises(PreferenceContractError):
            mean_source_utility({0}, [{0}, {1}], [[True] * 3])

    def test_boolean_mask_cannot_silently_become_ordinal_set(self):
        with self.assertRaises(PreferenceContractError):
            mean_source_utility([True, False], [{0}])

    def test_pair_uses_outside_baseline_and_all_source_references(self):
        raters = [{0, 2, 9}, {0, 2, 3, 9}]
        pairs = make_preference_pairs([raters[0]], raters, {0, 4, 9},
                                      range(10), 2, 6, known_masks=[[True] * 10] * 2)
        self.assertEqual(len(pairs), 1)
        pair = pairs[0]
        self.assertEqual(pair["chosen_selected"], [2])
        self.assertEqual(pair["rejected_selected"], [5])
        self.assertEqual(pair["chosen_utility_exact"], "13/14")
        self.assertEqual(pair["rejected_utility_exact"], "13/21")
        self.assertEqual(pair["outside_baseline_frames"], 2)
        self.assertEqual(pair["budget"], 1)
        self.assertEqual(pair["segments"], 1)
        self.assertFalse(pair["token_length_equality_checked"])
        for side in ("chosen", "rejected"):
            mapped = native_selection(parse_answer(pair[side + "_answer"], 4), range(10), 2, 6)
            self.assertEqual(mapped, set(pair[side + "_selected"]))

    def test_reflection_can_win_original_seed_is_not_assumed_positive(self):
        pairs = make_preference_pairs([{1}], [{4}, {4}, {1}], set(), range(6), 0, 6)
        self.assertEqual(len(pairs), 1)
        self.assertEqual(pairs[0]["chosen_selected"], [4])
        self.assertFalse(pairs[0]["chosen_is_seed"])

    def test_identical_tied_and_duplicate_pairs_are_not_training_data(self):
        self.assertEqual(make_preference_pairs([set(), {1, 4}], [{1}], set(), range(6), 0, 6), [])
        self.assertEqual(make_preference_pairs([{1}], [{1}, {4}], set(), range(6), 0, 6), [])
        pairs = make_preference_pairs([{1}, {4}, {1}], [{1}], set(), range(6), 0, 6)
        self.assertEqual(len(pairs), 1)
        self.assertEqual(pairs[0]["seed_index"], 0)

    def test_missing_reference_contract_is_checked_even_without_pairs(self):
        with self.assertRaises(UnknownSupervisionError):
            make_preference_pairs([set()], [{1}], set(), range(3), 0, 3,
                                  known_masks=[[True, True, False]])
        with self.assertRaises(PreferenceContractError):
            make_preference_pairs([{0}], [{0}], {3}, range(3), 0, 3)
        with self.assertRaises(PreferenceContractError):
            make_preference_pairs([{0}], [{0}], set(), range(3), 0, 3,
                                  known_masks=[[True] * 2])


class DpoReferenceTests(unittest.TestCase):
    def test_reference_policy_initialization_and_preference_sign(self):
        self.assertAlmostEqual(dpo_loss(-4, -9, -4, -9, 0.2), math.log(2))
        original = dpo_loss(-4, -9, -4, -9, 0.2)
        self.assertLess(dpo_loss(-3, -9, -4, -9, 0.2), original)
        self.assertLess(dpo_loss(-4, -10, -4, -9, 0.2), original)
        self.assertGreater(dpo_loss(-5, -9, -4, -9, 0.2), original)

    def test_finite_difference_matches_policy_gradient(self):
        chosen, rejected, ref_chosen, ref_rejected, beta = -4.3, -5.2, -4.6, -4.7, 0.3
        margin = beta * ((chosen-ref_chosen)-(rejected-ref_rejected))
        derivative = -beta / (1 + math.exp(margin))
        step = 1e-5
        chosen_fd = (dpo_loss(chosen+step, rejected, ref_chosen, ref_rejected, beta)
                     - dpo_loss(chosen-step, rejected, ref_chosen, ref_rejected, beta)) / (2*step)
        rejected_fd = (dpo_loss(chosen, rejected+step, ref_chosen, ref_rejected, beta)
                       - dpo_loss(chosen, rejected-step, ref_chosen, ref_rejected, beta)) / (2*step)
        self.assertAlmostEqual(chosen_fd, derivative, places=9)
        self.assertAlmostEqual(rejected_fd, -derivative, places=9)

    def test_stable_extremes_and_reject_nonfinite(self):
        self.assertTrue(math.isfinite(dpo_loss(-1, -10001, -1, -1, 1)))
        self.assertEqual(dpo_loss(-10001, -1, -1, -1, 1), 10000)
        for bad in (float("nan"), float("inf"), -float("inf"), True):
            with self.subTest(bad=bad), self.assertRaises(PreferenceContractError):
                dpo_loss(bad, -1, -1, -1, 0.1)
        with self.assertRaises(PreferenceContractError):
            dpo_loss(-1, -1, -1, -1, 0)

    def test_causal_suffix_positions_include_eos_predecessor(self):
        self.assertEqual(causal_positions(8, 3), [4, 5, 6])
        tokens = [10, 11, 12, 13, 14, 20, 21, 99]
        self.assertEqual([tokens[index+1] for index in causal_positions(8, 3)], [20, 21, 99])
        self.assertEqual(causal_positions(2, 1), [0])
        for length, count in ((3, 0), (3, 3), (3, 4), (0, 0), (True, 1), (3, 1.0)):
            with self.subTest(length=length, count=count), self.assertRaises(PreferenceContractError):
                causal_positions(length, count)


if __name__ == "__main__":
    unittest.main()
