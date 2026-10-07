"""Synthetic offline contract tests; fixture bytes are not production evidence."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from resource_contract import (MAC_WORKSPACE_ROOT, TOTAL_BUDGET_BYTES,
                               ResourceAdmissionError, admit_capacity, seal_plan)


GIB = 2**30


class ResourceContractTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        # Deliberately old but bounded evidence: there is no 300s heartbeat gate.
        self.evidence = {
            "observed_at": "2020-01-01T08:00:00+08:00", "timezone": "Asia/Taipei",
            "mac": {
                "workspace_root": MAC_WORKSPACE_ROOT, "known_work_bytes": 20 * GIB,
                "occupancy_reserve_bytes": 21 * GIB,
                "registered_remaining_write_bytes": 0, "new_write_limit_bytes": GIB,
                "reservation_bytes": 22 * GIB, "training_completed": True,
                "remaining_write_bound_reliable": True, "active_new_tasks": [],
            },
            "shared_temporary_limit_bytes": GIB, "linux_limit_bytes": 57 * GIB,
        }
        self.plan = {
            "schema_version": 1, "plan_id": "SYNTHETIC_TEST_ONLY",
            "frozen_at": "2020-01-01T08:01:00+08:00", "timezone": "Asia/Taipei",
            "total_budget_bytes": TOTAL_BUDGET_BYTES,
            "mac": deepcopy(self.evidence["mac"]),
            "shared_temporary_limit_bytes": GIB, "linux_limit_bytes": 57 * GIB,
            "proofs": {},
        }
        role_claims = {
            "mac_capacity": {"workspace_root": "/mac/workspace_root", "known_work_bytes": "/mac/known_work_bytes"},
            "mac_training_completed": {"completed": "/mac/training_completed"},
            "mac_write_bound": {name: "/mac/" + name for name in ("registered_remaining_write_bytes", "new_write_limit_bytes", "remaining_write_bound_reliable", "active_new_tasks")},
            "quota_registration": {
                "occupancy_reserve_bytes": "/mac/occupancy_reserve_bytes",
                "reservation_bytes": "/mac/reservation_bytes",
                "shared_temporary_limit_bytes": "/shared_temporary_limit_bytes",
                "linux_limit_bytes": "/linux_limit_bytes",
            },
        }
        for role, selectors in role_claims.items():
            self.plan["proofs"][role] = {
                "path": "quota_evidence.json", "sha256": "",
                "observed_at": self.evidence["observed_at"], "timezone": self.evidence["timezone"],
                "assertions": dict(selectors, observed_at="/observed_at", timezone="/timezone"),
            }
        self._save_evidence()
        self.plan = seal_plan(self.plan, base_dir=self.directory)

    def _save_evidence(self):
        raw = (json.dumps(self.evidence, sort_keys=True) + "\n").encode("utf-8")
        (self.directory / "quota_evidence.json").write_bytes(raw)
        for proof in self.plan["proofs"].values():
            proof["sha256"] = hashlib.sha256(raw).hexdigest()

    def admit(self, plan=None, **kwargs):
        values = dict(linux_work_bytes=40 * GIB, linux_free_bytes=100 * GIB,
                      planned_output_bytes=2 * GIB, registered_mac_remaining_bytes=0)
        values.update(kwargs)
        return admit_capacity(self.plan if plan is None else plan, base_dir=self.directory, **values)

    def test_offline_bounded_mac_allows_linux_without_heartbeat(self):
        result = self.admit()
        self.assertEqual(result["status"], "ADMITTED_QUOTA")
        self.assertFalse(result["mac_heartbeat_required"])
        self.assertEqual(result["combined_peak_bytes"], 65 * GIB)

    def test_offline_mac_keeps_full_reservation(self):
        result = self.admit(registered_mac_remaining_bytes=0)
        self.assertEqual(result["mac_reservation_bytes"], 22 * GIB)
        with self.assertRaisesRegex(ResourceAdmissionError, "exceeds frozen quota"):
            self.admit(linux_work_bytes=58 * GIB, planned_output_bytes=0)

    def test_unknown_mac_writes_stop(self):
        for value in (False, None):
            with self.subTest(value=value):
                changed = deepcopy(self.plan)
                changed["mac"]["remaining_write_bound_reliable"] = value
                with self.assertRaisesRegex(ResourceAdmissionError, "unknown Mac"):
                    self.admit(changed)

    def test_linux_occupancy_and_outputs_must_fit(self):
        with self.assertRaisesRegex(ResourceAdmissionError, "exceeds frozen quota"):
            self.admit(linux_work_bytes=56 * GIB, planned_output_bytes=2 * GIB)

    def test_disk_space_includes_shared_scratch(self):
        with self.assertRaisesRegex(ResourceAdmissionError, "free disk"):
            self.admit(linux_free_bytes=2 * GIB)
        result = self.admit(linux_free_bytes=3 * GIB)
        self.assertEqual(result["required_linux_free_bytes"], 3 * GIB)

    def test_exact_linux_quota_boundary_admits(self):
        result = self.admit(linux_work_bytes=55 * GIB, planned_output_bytes=2 * GIB)
        self.assertEqual(result["combined_peak_bytes"], TOTAL_BUDGET_BYTES)

    def test_runtime_remaining_writes_cannot_grow(self):
        with self.assertRaisesRegex(ResourceAdmissionError, "writes grew"):
            self.admit(registered_mac_remaining_bytes=1)

    def test_registered_remaining_allowance_is_not_released_by_zero(self):
        self.evidence["mac"]["registered_remaining_write_bytes"] = GIB
        self.evidence["mac"]["reservation_bytes"] += GIB
        self.evidence["linux_limit_bytes"] -= GIB
        self.plan["mac"] = deepcopy(self.evidence["mac"])
        self.plan["linux_limit_bytes"] = self.evidence["linux_limit_bytes"]
        self._save_evidence()
        self.plan = seal_plan(self.plan, base_dir=self.directory)
        result = self.admit(registered_mac_remaining_bytes=0)
        self.assertEqual(result["mac_reservation_bytes"], 23 * GIB)
        self.admit(registered_mac_remaining_bytes=GIB)
        with self.assertRaisesRegex(ResourceAdmissionError, "writes grew"):
            self.admit(registered_mac_remaining_bytes=GIB + 1)

    def test_negative_bool_fraction_arguments_rejected(self):
        for name in ("linux_work_bytes", "linux_free_bytes", "planned_output_bytes", "registered_mac_remaining_bytes"):
            for value in (-1, True, False, 0.5, 1.0, None):
                with self.subTest(name=name, value=value):
                    with self.assertRaisesRegex(ResourceAdmissionError, "nonnegative integer"):
                        self.admit(**{name: value})

    def test_negative_bool_fraction_plan_bytes_rejected(self):
        for name in ("known_work_bytes", "occupancy_reserve_bytes", "registered_remaining_write_bytes", "new_write_limit_bytes", "reservation_bytes"):
            for value in (-1, True, 1.5):
                with self.subTest(name=name, value=value):
                    changed = deepcopy(self.plan)
                    changed["mac"][name] = value
                    with self.assertRaisesRegex(ResourceAdmissionError, "nonnegative integer"):
                        self.admit(changed)

    def test_missing_proof_stops(self):
        for role in self.plan["proofs"]:
            with self.subTest(role=role):
                changed = deepcopy(self.plan)
                del changed["proofs"][role]
                with self.assertRaisesRegex(ResourceAdmissionError, "missing proof"):
                    self.admit(changed)

    def test_changed_evidence_stops(self):
        (self.directory / "quota_evidence.json").write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(ResourceAdmissionError, "proof bytes changed"):
            self.admit()

    def test_missing_evidence_file_stops(self):
        (self.directory / "quota_evidence.json").unlink()
        with self.assertRaisesRegex(ResourceAdmissionError, "cannot be read"):
            self.admit()

    def test_proof_assertion_mismatch_stops(self):
        self.evidence["mac"]["training_completed"] = False
        self._save_evidence()
        with self.assertRaisesRegex(ResourceAdmissionError, "does not establish completed"):
            seal_plan(self.plan, base_dir=self.directory)

    def test_missing_bound_assertion_stops(self):
        del self.plan["proofs"]["mac_write_bound"]["assertions"]["new_write_limit_bytes"]
        with self.assertRaisesRegex(ResourceAdmissionError, "JSON pointer"):
            self.admit()

    def test_reserve_increase_without_new_proof_stops(self):
        changed = deepcopy(self.plan)
        changed["mac"]["occupancy_reserve_bytes"] += GIB
        changed["mac"]["reservation_bytes"] += GIB
        changed["linux_limit_bytes"] -= GIB
        with self.assertRaisesRegex(ResourceAdmissionError, "does not establish"):
            self.admit(changed)

    def test_evidenced_change_still_requires_new_plan_seal(self):
        self.evidence["mac"]["occupancy_reserve_bytes"] += GIB
        self.evidence["mac"]["reservation_bytes"] += GIB
        self.evidence["linux_limit_bytes"] -= GIB
        self.plan["mac"] = deepcopy(self.evidence["mac"])
        self.plan["linux_limit_bytes"] = self.evidence["linux_limit_bytes"]
        self._save_evidence()
        with self.assertRaisesRegex(ResourceAdmissionError, "frozen plan changed"):
            self.admit()
        self.plan = seal_plan(self.plan, base_dir=self.directory)
        self.admit()

    def test_quota_cannot_overallocate(self):
        changed = deepcopy(self.plan)
        changed["linux_limit_bytes"] += 1
        with self.assertRaisesRegex(ResourceAdmissionError, "Linux quota must"):
            self.admit(changed)

    def test_total_budget_cannot_change(self):
        changed = deepcopy(self.plan)
        changed["total_budget_bytes"] += 1
        with self.assertRaisesRegex(ResourceAdmissionError, "exactly 80 GiB"):
            self.admit(changed)

    def test_mac_reserve_must_cover_known_work(self):
        changed = deepcopy(self.plan)
        changed["mac"]["known_work_bytes"] += 2 * GIB
        with self.assertRaisesRegex(ResourceAdmissionError, "below known occupancy"):
            self.admit(changed)

    def test_new_active_mac_task_stops(self):
        changed = deepcopy(self.plan)
        changed["mac"]["active_new_tasks"] = ["unregistered_download"]
        with self.assertRaisesRegex(ResourceAdmissionError, "active new Mac tasks"):
            self.admit(changed)

    def test_unaware_timestamp_stops(self):
        changed = deepcopy(self.plan)
        changed["frozen_at"] = "2020-01-01T08:01:00"
        with self.assertRaisesRegex(ResourceAdmissionError, "timezone-aware"):
            self.admit(changed)

    def test_timezone_offset_disagreement_stops(self):
        changed = deepcopy(self.plan)
        changed["frozen_at"] = "2020-01-01T08:01:00+00:00"
        with self.assertRaisesRegex(ResourceAdmissionError, "offset disagrees"):
            self.admit(changed)

    def test_unproved_timestamp_stops(self):
        changed = deepcopy(self.plan)
        changed["proofs"]["mac_capacity"]["observed_at"] = "2019-01-01T08:00:00+08:00"
        with self.assertRaisesRegex(ResourceAdmissionError, "does not establish observed_at"):
            self.admit(changed)

    def test_proof_cannot_postdate_plan(self):
        changed = deepcopy(self.plan)
        changed["proofs"]["mac_capacity"]["observed_at"] = "2021-01-01T08:00:00+08:00"
        with self.assertRaisesRegex(ResourceAdmissionError, "postdates"):
            self.admit(changed)

    def test_unsealed_plan_stops(self):
        changed = deepcopy(self.plan)
        del changed["frozen_plan_sha256"]
        with self.assertRaisesRegex(ResourceAdmissionError, "frozen plan changed"):
            self.admit(changed)

    def test_template_is_not_a_production_pass(self):
        template = json.loads(Path(__file__).with_name("quota_plan_template.json").read_text(encoding="utf-8"))
        with self.assertRaises(ResourceAdmissionError):
            self.admit(template)

    def test_sealing_does_not_mutate_input(self):
        original = deepcopy(self.plan)
        original.pop("frozen_plan_sha256")
        result = seal_plan(original, base_dir=self.directory)
        self.assertNotIn("frozen_plan_sha256", original)
        self.assertEqual(result["frozen_plan_sha256"], self.plan["frozen_plan_sha256"])


if __name__ == "__main__":
    unittest.main()
