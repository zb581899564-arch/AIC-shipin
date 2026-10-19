"""Independent small outcome oracles; no Torch, models, media or real annotations."""
from copy import deepcopy
from fractions import Fraction
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest

from .contracts import reference, save_new
from .run import (assess_mechanism, case_output, mean_metrics, preference_accuracy,
                  read_generation, require_production_assets, torch_gate)


def selections(values):
    return {sid: dict(status="ACCEPTED", selected_ordinals=sorted(items))
            for sid, items in values.items()}


def pair_scores(source_ids, *, right):
    return [dict(source_id=sid, pair_id=sid + str(i),
                 chosen_logprob=-1.0 if right else -3.0, rejected_logprob=-2.0)
            for sid in source_ids for i in range(2)]


class OutcomeChecks(unittest.TestCase):
    def setUp(self):
        self.human = {"one": dict(baseline={0, 2}, raters=[{0, 1}, {0, 1}],
                                 known_masks=[[True] * 4] * 2)}
        self.before = selections({"one": {0, 2}})
        self.after = selections({"one": {0, 1}})
        self.bad, self.good = pair_scores(self.human, right=False), pair_scores(self.human, right=True)

    def assess(self, **changes):
        args = dict(supervision=self.human, reference_selections=self.before,
                    policy_selections=self.after, reference_pairs=self.bad, policy_pairs=self.good)
        args.update(changes)
        return assess_mechanism(**args)

    def test_true_content_gain_is_only_review_eligibility(self):
        result = self.assess()
        self.assertEqual(result["status"], "ELIGIBLE_FOR_EXECUTION_REVIEW")
        self.assertEqual(result["macro"]["policy"]["f1"], 1.0)
        self.assertEqual(result["macro"]["reference"]["f1"], .5)
        self.assertFalse(result["automatic_production"])
        self.assertNotIn("approved", result)
        self.assertEqual(result["official_score"], "NOT_MEASURED")

    def test_relative_dpo_improvement_can_still_rank_bad_answer_first(self):
        better_but_wrong = deepcopy(self.bad)
        for row in better_but_wrong:
            row["chosen_logprob"] = -2.5
        result = self.assess(policy_pairs=better_but_wrong)
        self.assertIn("RAW_HELDOUT_PAIR_ORDERING_DID_NOT_IMPROVE", result["stop_reasons"])
        self.assertEqual(result["pair_accuracy"]["policy"]["source_macro"], 0.0)

    def test_probability_only_improvement_does_not_pass(self):
        result = self.assess(policy_selections=self.before)
        self.assertIn("NO_CHANGE_IN_ACTUAL_GENERATED_SELECTION", result["stop_reasons"])
        self.assertEqual(result["status"], "STOP_MECHANISM")

    def test_must_beat_protected_proxy_as_well_as_original_time(self):
        self.human["one"]["baseline"] = {0, 1}
        result = self.assess()
        self.assertIn("FULL_SOURCE_GENERATION_DID_NOT_BEAT_EXPOSED_40_47_PROXY", result["stop_reasons"])

    def test_false_empty_source_stops_even_when_macro_f1_improves(self):
        human = {
            "large_gain": dict(baseline={3}, raters=[{0, 1, 2}], known_masks=[[True]*4]),
            "collapse": dict(baseline={0, 1, 2}, raters=[{0}], known_masks=[[True]*4])}
        result = self.assess(supervision=human,
            reference_selections=selections({"large_gain": {3}, "collapse": {0, 1, 2}}),
            policy_selections=selections({"large_gain": {0, 1, 2}, "collapse": set()}),
            reference_pairs=pair_scores(human, right=False), policy_pairs=pair_scores(human, right=True))
        self.assertGreater(result["macro"]["policy"]["f1"], result["macro"]["reference"]["f1"])
        self.assertIn("NEW_FALSE_EMPTY_COMPLETE_SOURCE", result["stop_reasons"])
        self.assertEqual(result["newly_false_empty_sources"], ["collapse"])

    def test_failed_source_is_never_an_empty_candidate(self):
        failed = {"one": dict(status="FAILED", selected_ordinals=[])}
        with self.assertRaises(ValueError):
            self.assess(policy_selections=failed)
        with self.assertRaises(ValueError):
            self.assess(policy_selections={})

    def test_unknown_rater_membership_cannot_supply_metric(self):
        self.human["one"]["known_masks"][0][2] = False
        with self.assertRaises(ValueError):
            self.assess()

    def test_full_source_f1_has_outside_reference_denominator(self):
        # Two selected true frames out of ten true frames: not window F1=1.
        self.assertAlmostEqual(mean_metrics({0, 1}, [set(range(10))])["f1"], 1/3)
        self.assertEqual(mean_metrics(set(), [set()])["f1"], 1)
        self.assertEqual(mean_metrics(set(), [{0}])["f1"], 0)

    def test_raw_pair_tie_and_complete_source_weighting(self):
        rows = pair_scores(["one", "two"], right=True)
        rows[0]["chosen_logprob"] = rows[0]["rejected_logprob"]
        rows[2]["chosen_logprob"] = -3
        rows[3]["chosen_logprob"] = -3
        self.assertEqual(preference_accuracy(rows, ["one", "two"])["source_macro"], .375)
        with self.assertRaises(ValueError):
            preference_accuracy(rows[:-1], ["one", "two"])


class ReceiptChecks(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.root = Path(self.temp.name)
        clock_path = self.root / "clock.json"
        self.clock = {"normalized_exact_pts": ["0", "1", "2", "3"], "physical_end_exact": "4"}
        save_new(clock_path, self.clock)
        self.clock_ref = reference(clock_path)
        requests, refs = {}, {}
        for number, (start, end) in enumerate((("0", "2"), ("2", "4"))):
            uid = "window" + str(number)
            request = dict(uid=uid, sid="source", input_signature={"native": number},
                           plan=dict(window_start_exact=start, window_end_exact=end))
            path = self.root / (uid + ".json")
            save_new(path, request)
            requests[uid], refs[uid] = request, reference(path)
        self.store = SimpleNamespace(workspace=self.root, case_ids=tuple(requests), source_ids=("source",),
            requests=requests, request_refs=refs, clocks={"source": self.clock},
            sources={"source": {"clock_ref": self.clock_ref}})

    def tearDown(self):
        self.temp.cleanup()

    def record(self, uid, *, text='{"segments":[]}', selected=None):
        request = self.store.requests[uid]
        return dict(status="ACCEPTED", actual_model_call=True, uid=uid, source_id="source",
            role="policy", input_signature=request["input_signature"], text=text,
            ids=[1, 2, 99], eos=True, eos_token_id=99,
            selected_ordinals=[] if selected is None else selected,
            legal_empty=not selected, request_ref=self.store.request_refs[uid], clock_ref=self.clock_ref)

    def refs(self, rows):
        result = []
        for index, row in enumerate(rows):
            result.append(save_new(self.root / ("result" + str(index) + ".json"), row))
        return result

    def test_empty_json_with_actual_eos_is_valid(self):
        row = self.record("window0")
        self.assertEqual(case_output(row, self.store.requests["window0"], self.clock, eos=99), set())

    def test_failed_and_truncated_json_are_rejected_separately(self):
        for changes in ({"status": "FAILED"}, {"eos": False}, {"ids": [1, 2]},
                        {"actual_model_call": False}, {"text": '{"segments":['}):
            with self.subTest(changes=changes):
                row = self.record("window0")
                row.update(changes)
                with self.assertRaises(ValueError):
                    case_output(row, self.store.requests["window0"], self.clock, eos=99)

    def test_frame_mapping_is_independently_reparsed(self):
        row = self.record("window0", text='{"segments":[[0,1.5]]}', selected=[0, 1])
        self.assertEqual(case_output(row, self.store.requests["window0"], self.clock, eos=99), {0, 1})
        row["selected_ordinals"] = [0]
        with self.assertRaises(ValueError):
            case_output(row, self.store.requests["window0"], self.clock, eos=99)

    def test_complete_window_union_keeps_legal_empty(self):
        rows = [self.record("window0", text='{"segments":[[0,1.5]]}', selected=[0, 1]),
                self.record("window1")]
        union, empty = read_generation(self.refs(rows), self.store, eos=99, role="policy")
        self.assertEqual(union["source"]["selected_ordinals"], [0, 1])
        self.assertEqual(empty, 1)

    def test_missing_window_is_not_synthesized_as_empty(self):
        with self.assertRaises(ValueError):
            read_generation(self.refs([self.record("window0")]), self.store, eos=99, role="policy")

    def test_duplicate_window_or_wrong_role_cannot_complete_source(self):
        rows = [self.record("window0"), self.record("window0")]
        with self.assertRaises(ValueError):
            read_generation(self.refs(rows), self.store, eos=99, role="policy")

    def test_not_run_torch_receipt_never_admits_gpu(self):
        path = self.root / "torch.json"
        save_new(path, dict(schema="AIC_NATIVE_PREFERENCE_TORCH_CPU_CHECKS_V1",
                            status="NOT_RUN", torch_passed=False, torch_checks=0))
        with self.assertRaises(ValueError):
            torch_gate(path, self.root)

    def test_formal_assets_cannot_replace_prior_training_or_model(self):
        original = {key: {"fixed": True} for key in ("model_spec", "model_files", "input_code",
            "code_refs", "protected_baseline_ref", "inherited_baseline_head_ref",
            "actual_pipeline_parameters", "rights_declaration_ref", "source_registration_ref")}
        original.update(workspace_root=str(self.root), scopes={"train": [1], "check": [2]})
        formal = deepcopy(original)
        formal["scopes"]["production"] = [3]
        formal["renderer"] = {"bound": True}
        require_production_assets(original, formal)
        formal["scopes"]["check"] = [4]
        with self.assertRaises(ValueError):
            require_production_assets(original, formal)


if __name__ == "__main__":
    unittest.main()
