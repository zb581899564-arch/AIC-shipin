import unittest

from vision_time66 import (derived_request, complete_unions, partition_parameters,
                           transfer_reasons, INPUT_KEYS, validate_pilot_scope, DIAGNOSTIC_PURPOSE)


class Transfer66Tests(unittest.TestCase):
    def test_failed_pilot_requires_explicit_diagnostic_and_stays_failed(self):
        failed = dict(status="STOP", stop_reasons=["REAL_ACCURACY_BELOW_POINT75"])
        with self.assertRaises(ValueError): validate_pilot_scope({}, failed)
        reg = dict(purpose=DIAGNOSTIC_PURPOSE, pilot_pair_gate="STOP", automatic426=False)
        validate_pilot_scope(reg, failed)
        self.assertEqual(failed["status"], "STOP")
        reg["automatic426"] = True
        with self.assertRaises(ValueError): validate_pilot_scope(reg, failed)

    def test_counterfactual_has_own_signature_without_mutating_original(self):
        old = {k: dict(sha256=k) for k in INPUT_KEYS}
        original = dict(uid="one", input_signature=old, plan={"native": "unchanged"})
        shifted = {k: dict(v) for k, v in old.items()}
        shifted["pixel_values_videos"] = dict(sha256="different")
        request = derived_request(original, "shift", shifted)
        self.assertFalse(request["truthful_native_observation"])
        self.assertEqual(request["original_input_signature"], old)
        self.assertNotEqual(request["input_signature"], original["input_signature"])
        self.assertEqual(request["plan"], original["plan"])
        with self.assertRaises(ValueError): derived_request(original, "real", shifted)

    def test_empty_success_is_distinct_from_missing_or_failed_window(self):
        def row(role, uid, chosen):
            return dict(role=role, uid=uid, source_id="V00", status="ACCEPTED",
                        selected_ordinals=chosen, legal_empty=not chosen)
        rows = {r: [row(r, "a", []), row(r, "b", [2, 3])] for r in ("real", "shift")}
        unions, empty = complete_unions(rows, ["a", "b"], ["V00"])
        self.assertEqual(unions["real"]["V00"], {2, 3})
        self.assertEqual(empty["real"], 1)
        rows["shift"].pop()
        with self.assertRaises(ValueError): complete_unions(rows, ["a", "b"], ["V00"])
        rows["shift"].append(row("shift", "b", [])); rows["shift"][-1]["status"] = "FAILED"
        with self.assertRaises(ValueError): complete_unions(rows, ["a", "b"], ["V00"])

    def test_adapters_partition_by_ownership_rejects_unknown_lora(self):
        class Parameter:
            requires_grad = False
            grad = None
            dtype = "torch.float32"
            def __init__(self, count): self.count = count
            def numel(self): return self.count
        base, time, vision, rogue = [Parameter(n) for n in [10, 3, 2, 1]]
        named = [("base.weight", base), ("language.lora_A.policy.weight", time), ("visual.lora_A", vision)]
        self.assertEqual(partition_parameters(named, [time], [vision]), dict(base=10, TIME=3, visual=2))
        with self.assertRaises(ValueError): partition_parameters(named + [("other.lora_B", rogue)], [time], [vision])

    def test_fit_or_single_source_success_cannot_admit_transfer(self):
        report = dict(macro={k: dict(f1=v) for k, v in dict(vision_real=.4, greedy=.3,
                         protected_proxy=.35, vision_shift=.39).items()}, effects={"vision_real": dict(source_wins=2)})
        greedy, real = {"a": {1}, "b": {2}}, {"a": {1, 3}, "b": {2}}
        self.assertEqual(transfer_reasons(report, greedy, real), [])
        report["effects"]["vision_real"]["source_wins"] = 1
        self.assertIn("FEWER_THAN_TWO_SOURCES_IMPROVED_VS_ORIGINAL_TIME", transfer_reasons(report, greedy, real))
        report["effects"]["vision_real"]["source_wins"] = 2
        real["b"] = set()
        self.assertIn("NEW_COMPLETE_SOURCE_EMPTY", transfer_reasons(report, greedy, real))
        report["macro"]["vision_real"]["f1"] = .3
        reasons = transfer_reasons(report, greedy, real)
        self.assertIn("REAL_NOT_BETTER_THAN_ORIGINAL_TIME", reasons)
        self.assertIn("REAL_NOT_BETTER_THAN_PROTECTED40_47_PROXY", reasons)
        self.assertIn("REAL_NOT_BETTER_THAN_FIXED_CONTENT_SHIFT", reasons)


if __name__ == "__main__": unittest.main()
