#!/usr/bin/env python3
"""CPU prediction-contract tests plus the frozen nonempty grammar regression."""
from __future__ import annotations

import argparse
import ast
from fractions import Fraction
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re
import sys
import unittest

try:
    from . import constrained_json as grammar_module
    from . import contracts
except ImportError:
    import constrained_json as grammar_module
    import contracts

HERE = Path(__file__).resolve().parent
OLD_TESTS = HERE.parent / "baseline_a_format_recovery_v1" / "test_constrained_json.py"


def legacy_tests_module():
    spec = importlib.util.spec_from_file_location("_next_round_frozen_nonempty_tests", OLD_TESTS)
    module = importlib.util.module_from_spec(spec)
    previous = sys.modules.get("constrained_json")
    sys.modules["constrained_json"] = grammar_module
    try:
        spec.loader.exec_module(module)
    finally:
        if previous is None:
            sys.modules.pop("constrained_json", None)
        else:
            sys.modules["constrained_json"] = previous
    # The old tests intentionally reject []. Run them against the new code
    # with the explicit old nonempty protocol, without editing frozen files.
    module.BoundedSegmentsGrammar = lambda duration, max_segments=5: grammar_module.BoundedSegmentsGrammar(
        duration, max_segments, allow_empty=False)

    def old_make(*args, **kwargs):
        return grammar_module.make_prefix_constraint(*args, **kwargs, allow_empty=False)

    module.make_prefix_constraint = old_make
    return module


LEGACY = legacy_tests_module()
FixtureTokenizer = LEGACY.FixtureTokenizer


class SpatialContractTests(unittest.TestCase):
    def test_old_coordinate_unit_bug_is_reproduced_from_old_source(self):
        source = HERE.parents[4] / ".github-publication" / "AIC-shipin" / "inference" / "baseline_qwen3vl.py"
        if not source.exists():
            source = Path('/home/inspur/aic_video_work/inference/baseline_qwen3vl.py')
        nodes = ast.parse(source.read_text(encoding="utf-8-sig")).body
        function = next(node for node in nodes if isinstance(node, ast.FunctionDef) and node.name == "parse_focus_norm")
        module = ast.Module(body=[ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0),
                                  function], type_ignores=[])
        namespace = {"json": json, "re": re, "_NUM": re.compile(r"-?\d+\.?\d*")}
        exec(compile(ast.fix_missing_locations(module), str(source), "exec"), namespace)
        raw = '{"center":[1,500]}'
        self.assertEqual(namespace["parse_focus_norm"](raw, 1080, 1920), [1.0, 0.5])
        self.assertEqual(contracts.parse_focus_norm(raw, 1080, 1920), [0.001, 0.5])

    def test_one_unit_contract_is_independent_of_image_dimensions(self):
        for center in ([0, 0], [1, 500], [500, 1], [1000, 1000]):
            raw = json.dumps({"center": center})
            expected = [value / 1000 for value in center]
            for dimensions in ((None, None), (10, 10), (1080, 1920), (3840, 2160)):
                self.assertEqual(contracts.parse_focus_norm(raw, *dimensions), expected)

    def test_invalid_type_shape_and_range_are_rejected(self):
        for center in ([True, 500], [1, False], [1.0, 500], ["1", 500], [None, 500],
                       [-1, 500], [1001, 500], [1, 1001], [1], [1, 500, 900], [],
                       [0.001, 0.5], {"x": 1, "y": 500}, None):
            with self.subTest(center=center):
                self.assertIsNone(contracts.parse_focus_norm(json.dumps({"center": center})))

    def test_non_json_nonfinite_duplicate_or_extra_fields_are_rejected(self):
        for raw in (None, "", "1 500", "center=(1,500)", '[1,500]',
                    '```json\n{"center":[1,500]}\n```', 'answer: {"center":[1,500]}',
                    '{"center":[1,500]} after', '{"center":[1,500]}{}',
                    '{"center":[1,500],"other":0}', '{"focus":[1,500]}',
                    '{"center":[1,500],"center":[2,500]}', '{"center":[NaN,500]}',
                    '{"center":[Infinity,500]}', '{"center":[1,500],}'):
            with self.subTest(raw=raw):
                self.assertIsNone(contracts.parse_focus_norm(raw))


class TemporalContractTests(unittest.TestCase):
    def test_empty_is_legal_and_not_a_parse_failure(self):
        self.assertEqual(contracts.parse_segments('{"segments":[]}', 2), ([], [], []))
        self.assertEqual(contracts.answer_string([], 2), '{"segments":[]}')
        self.assertEqual(contracts.validate_segments([], 2), [])
        self.assertEqual(contracts.classify_temporal_result('{"segments":[]}', 2)["status"], contracts.LEGAL_EMPTY)
        segments, errors, warnings = contracts.parse_segments('{"segments":[]}', 2, allow_empty=False)
        self.assertIsNone(segments)
        self.assertTrue(errors)
        self.assertEqual(warnings, [])

    def test_geometry_preserves_order_values_and_object(self):
        target = [[0.123456, 1.234567], [1.234567, 2]]
        self.assertIs(contracts.validate_segments(target, 2), target)
        self.assertEqual(contracts.parse_segments(json.dumps({"segments": target}), 2), (target, [], []))
        self.assertEqual(contracts.parse_segments('{"segments":[[0,1],[1,2]]}', Fraction(2)),
                         ([[0, 1], [1, 2]], [], []))

    def test_answer_matches_four_decimal_grammar_without_rounding(self):
        for target in ([], [[0, 2]], [[0.0001, 1.2345], [1.2345, 2]], [[0, 100000000000000000000]]):
            duration = 100000000000000000000 if target and target[-1][-1] > 2 else 2
            text = contracts.answer_string(target, duration)
            self.assertTrue(grammar_module.BoundedSegmentsGrammar(duration).complete(text), text)
            self.assertEqual(json.loads(text)["segments"], target)
        with self.assertRaisesRegex(ValueError, "four-decimal"):
            contracts.answer_string([[0, 0.00001]], 2)
        with self.assertRaises(ValueError):
            contracts.answer_string([], 2, allow_empty=False)

    def test_whole_prediction_fails_instead_of_repairing_any_segment(self):
        invalid = ([[0, 1], [2, 2.0001]], [[1, 2], [0, 1]], [[0, 1.5], [1, 2]],
                   [[1, 1]], [[2, 1]], [[-0.0001, 1]], [[0, 2.0000001]],
                   [[0, 1], [None, 2]], [[False, 1]], [[0, "2"]], [[0]],
                   [[0, 1, 2]], [[0, 1]] * 6)
        for target in invalid:
            with self.subTest(target=target):
                result, errors, warnings = contracts.parse_segments(json.dumps({"segments": target}), 2)
                self.assertIsNone(result)
                self.assertTrue(errors)
                self.assertEqual(warnings, [])

    def test_strict_single_json_object_no_fences_prose_or_nonfinite(self):
        for raw in (None, "", "[]", "null", "{}", '{"segments":null}',
                    '```json\n{"segments":[]}\n```', 'answer {"segments":[]}',
                    '{"segments":[]} trailing', '{"segments":[]}{}',
                    '{"segments":[],"other":0}', '{"segments":[],"segments":[[0,1]]}',
                    '{"segments":[[0,NaN]]}', '{"segments":[[0,Infinity]]}',
                    '{"segments":[[0,1e999]]}', '{"segments":[[0,1]],}',
                    '{"segments":[[0,1],]}', '{"segments":[[0,2.00000000000000001]]}'):
            with self.subTest(raw=raw):
                result, errors, warnings = contracts.parse_segments(raw, 2)
                self.assertIsNone(result)
                self.assertTrue(errors)
                self.assertEqual(warnings, [])

    def test_invalid_duration_and_protocol_options_fail_closed(self):
        for duration in (True, 0, -1, float("nan"), float("inf"), "2", None):
            self.assertIsNone(contracts.parse_segments('{"segments":[]}', duration)[0])
        for options in ({"max_segments": 0}, {"max_segments": 6}, {"max_segments": True},
                        {"max_segments": 1.0}, {"allow_empty": 1}):
            self.assertIsNone(contracts.parse_segments('{"segments":[]}', 2, **options)[0])

    def test_prediction_and_execution_states_are_distinct(self):
        self.assertEqual(contracts.classify_temporal_result('{"segments":[[0,1]]}', 2)["status"], contracts.MODEL_OK)
        self.assertEqual(contracts.classify_temporal_result("broken", 2)["status"], contracts.PARSE_FAILURE)
        self.assertEqual(contracts.classify_temporal_result(None, 2)["status"], contracts.PARSE_FAILURE)
        failure = contracts.classify_temporal_result('{"segments":[]}', 2, inference_error="CUDA failure")
        self.assertEqual(failure["status"], contracts.INFERENCE_FAILURE)
        self.assertIsNone(failure["parsed_segments"])
        self.assertFalse(failure["output_valid"])
        all_empty = [contracts.classify_temporal_result('{"segments":[]}', 2) for _ in range(8)]
        self.assertTrue(all(row["status"] == contracts.LEGAL_EMPTY and row["parsed_segments"] == [] for row in all_empty))

    def test_empty_prompt_does_not_define_unknown_as_empty(self):
        self.assertIn("between 0 and 5 intervals", contracts.EMPTY_PROMPT)
        self.assertIn('return {"segments": []}', contracts.EMPTY_PROMPT)
        self.assertIn("do not use an empty list to represent uncertainty", contracts.EMPTY_PROMPT)


class EmptyGrammarTests(unittest.TestCase):
    def test_every_prefix_and_complete_empty_or_nonempty(self):
        grammar = grammar_module.BoundedSegmentsGrammar(2)
        for text in ('{"segments":[]}', '{"segments":[[0,1]]}', '{"segments":[[0,1],[1,2]]}'):
            for length in range(len(text) + 1):
                self.assertTrue(grammar.valid_prefix(text[:length]), text[:length])
            self.assertTrue(grammar.complete(text), text)
            self.assertFalse(grammar.complete(text[:-1]))

    def test_empty_is_enabled_only_at_the_initial_list_position(self):
        grammar = grammar_module.BoundedSegmentsGrammar(2)
        for text in ('{"segments":[,', '{"segments":[[0,1],]}', '{"segments":[[0,1],]',
                     '{"segments":[[]]}', '{"segments":[[0,1]],}', '{"segments":[]]}',
                     '{"segments":[[0,1],[,', '{"segments":[],"other":0}'):
            self.assertFalse(grammar.valid_prefix(text), text)
        self.assertFalse(grammar_module.BoundedSegmentsGrammar(2, allow_empty=False).valid_prefix('{"segments":]'))
        self.assertFalse(grammar_module.BoundedSegmentsGrammar(2, allow_empty=False).complete('{"segments":[]}'))

    def test_tiny_positive_duration_has_only_empty_continuation(self):
        grammar = grammar_module.BoundedSegmentsGrammar(Fraction(1, 100001))
        self.assertTrue(grammar.complete('{"segments":[]}'))
        self.assertFalse(grammar.valid_prefix('{"segments":[['))
        with self.assertRaises(ValueError):
            grammar_module.BoundedSegmentsGrammar(Fraction(1, 100001), allow_empty=False)
        with self.assertRaises(ValueError):
            grammar_module.BoundedSegmentsGrammar(2, allow_empty=1)

    def test_count_duration_and_nonempty_geometry_still_reject_overflow(self):
        grammar = grammar_module.BoundedSegmentsGrammar(2)
        for target in ([[0, 2.0001]], [[0, 1]] * 6, [[1, 1]], [[0, 1.1], [1, 2]], [[1, 2], [0, 1]]):
            self.assertFalse(grammar.valid_prefix(json.dumps({"segments": target}, separators=(",", ":"))))

    def test_token_adapter_empty_eos_truncation_and_old_policy(self):
        tokenizer = FixtureTokenizer()
        constraint = grammar_module.make_prefix_constraint(tokenizer, 2, 2)
        prompt = [999, 998]
        opening = '{"segments":['
        self.assertIn(tokenizer.chars["]"], constraint(0, prompt + tokenizer.ids(opening)))
        self.assertNotIn(tokenizer.eos_token_id, constraint(0, prompt + tokenizer.ids(opening)))
        complete = '{"segments":[]}'
        self.assertEqual(constraint(0, prompt + tokenizer.ids(complete)), [tokenizer.eos_token_id])
        self.assertEqual(constraint.assert_complete(tokenizer.ids(complete) + [0]), {"segments": []})
        with self.assertRaises(grammar_module.IncompleteConstrainedOutput):
            constraint.assert_complete(tokenizer.ids('{"segments":[]'))
        with self.assertRaises(grammar_module.IncompleteConstrainedOutput):
            constraint.assert_complete(tokenizer.ids(opening) + [0] + tokenizer.ids("]}"))
        old = grammar_module.make_prefix_constraint(tokenizer, 2, 2, allow_empty=False)
        self.assertNotIn(tokenizer.chars["]"], old(0, prompt + tokenizer.ids(opening)))
        with self.assertRaises(grammar_module.ConstraintDeadEnd):
            old(0, prompt + tokenizer.ids(complete))

    def test_adapter_rejects_trailing_comma_and_invalid_token_identity(self):
        tokenizer = FixtureTokenizer()
        constraint = grammar_module.make_prefix_constraint(tokenizer, 2, 2)
        with self.assertRaises(grammar_module.ConstraintDeadEnd):
            constraint(0, [999, 998] + tokenizer.ids('{"segments":[[0,1],]}'))
        for ids in ([True], [-1], [1.0]):
            with self.assertRaises(grammar_module.IncompleteConstrainedOutput):
                constraint.assert_complete(ids)


def load_tests(loader, tests, pattern):
    del pattern
    tests.addTests(loader.loadTestsFromTestCase(LEGACY.GrammarTests))
    tests.addTests(loader.loadTestsFromTestCase(LEGACY.TokenAdapterTests))
    return tests


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.output is not None and args.output.exists():
        raise FileExistsError("preserve CPU contract evidence")
    stream = io.StringIO()
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    receipt = {"schema": "aic_next_round_contract_cpu_v1", "status": "PASS" if result.wasSuccessful() else "FAIL",
               "tests_run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
               "old_nonempty_regression_tests": 19, "output": stream.getvalue(),
               "source_sha256": {name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
                                  for name in ("contracts.py", "constrained_json.py", "test_contracts.py")},
               "model_run": False, "GPU_used": False, "contest_media_read": False,
               "semantic_labels_read": False, "quality_claim": False}
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as target:
            json.dump(receipt, target, ensure_ascii=False, indent=2)
            target.write("\n")
    print(stream.getvalue())
    print(json.dumps({key: value for key, value in receipt.items() if key != "output"}, ensure_ascii=False))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
