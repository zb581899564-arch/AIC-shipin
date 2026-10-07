"""Frozen two-host disk quota for new Linux jobs, without a live Mac heartbeat.

All bytes are nonnegative integers. Mac reservations include its measured work,
registered remaining writes and a bounded allowance for new writes; an offline
Mac never releases that reservation. Increasing any bound requires a new plan
and matching, hashed evidence. This module does not authorize a transfer, launch
a GPU job, change the shared GPU lock/ledger, or check GPU/CPU utilization.

Proof paths are resolved against ``base_dir`` (the plan's directory is advised),
or the current directory. Proof JSON files must travel with the frozen plan.
"""

from copy import deepcopy
from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


TOTAL_BUDGET_BYTES = 80 * 2**30
MAC_WORKSPACE_ROOT = "/Users/choubk/codex-workspace"


class ResourceAdmissionError(ValueError):
    """Fail-closed refusal of an incomplete, changed or overcommitted quota."""


def _require(condition, message):
    if not condition:
        raise ResourceAdmissionError(message)


def _bytes(value, name):
    _require(type(value) is int and value >= 0, name + " must be a nonnegative integer")
    return value


def _time(value, timezone, name):
    _require(isinstance(value, str) and isinstance(timezone, str), name + " needs a timestamp and IANA timezone")
    try:
        stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
        zone = ZoneInfo(timezone)
    except (ValueError, ZoneInfoNotFoundError) as exc:
        raise ResourceAdmissionError(name + " has an invalid timestamp/timezone") from exc
    _require(stamp.tzinfo is not None and stamp.utcoffset() is not None, name + " must be timezone-aware")
    _require(stamp.astimezone(zone).utcoffset() == stamp.utcoffset(), name + " offset disagrees with its timezone")
    return stamp


def _digest(plan):
    body = {key: value for key, value in plan.items() if key != "frozen_plan_sha256"}
    try:
        raw = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ResourceAdmissionError("plan must contain only finite JSON values") from exc
    return hashlib.sha256(raw).hexdigest()


def _pointer(document, pointer):
    _require(isinstance(pointer, str) and pointer.startswith("/"), "proof assertion needs a JSON pointer")
    result = document
    try:
        for item in pointer[1:].split("/"):
            item = item.replace("~1", "/").replace("~0", "~")
            result = result[int(item)] if isinstance(result, list) else result[item]
    except (KeyError, IndexError, ValueError, TypeError) as exc:
        raise ResourceAdmissionError("proof assertion pointer is missing: " + pointer) from exc
    return result


def _proof(role, proof, expected, frozen_at, base_dir):
    _require(isinstance(proof, dict), "missing proof: " + role)
    path, sha = proof.get("path"), proof.get("sha256")
    _require(isinstance(path, str) and bool(path.strip()), role + " proof path is missing")
    _require(isinstance(sha, str) and re.fullmatch(r"[0-9a-f]{64}", sha) is not None, role + " proof SHA256 is invalid")
    observed = _time(proof.get("observed_at"), proof.get("timezone"), role)
    _require(observed <= frozen_at, role + " proof postdates the frozen plan")
    proof_path = Path(path)
    if not proof_path.is_absolute():
        proof_path = Path(base_dir) / proof_path
    try:
        raw = proof_path.read_bytes()
        document = json.loads(raw)
    except (OSError, ValueError) as exc:
        raise ResourceAdmissionError(role + " proof cannot be read as JSON") from exc
    _require(hashlib.sha256(raw).hexdigest() == sha, role + " proof bytes changed")
    assertions = proof.get("assertions")
    _require(isinstance(assertions, dict), role + " proof assertions are missing")
    # Metadata must be present in the hashed evidence, not merely in the plan.
    expected = dict(expected, observed_at=proof["observed_at"], timezone=proof["timezone"])
    for name, wanted in expected.items():
        actual = _pointer(document, assertions.get(name))
        _require(type(actual) is type(wanted) and actual == wanted, role + " proof does not establish " + name)
    return sha


def _validate_plan(plan, base_dir, check_seal):
    _require(isinstance(plan, dict), "plan must be a JSON object")
    _require(type(plan.get("schema_version")) is int and plan["schema_version"] == 1, "unsupported quota schema")
    _require(isinstance(plan.get("plan_id"), str) and bool(plan["plan_id"].strip()), "plan_id is missing")
    frozen_at = _time(plan.get("frozen_at"), plan.get("timezone"), "plan")
    total = _bytes(plan.get("total_budget_bytes"), "total_budget_bytes")
    _require(total == TOTAL_BUDGET_BYTES, "the approved total is exactly 80 GiB")
    mac = plan.get("mac")
    _require(isinstance(mac, dict), "Mac reservation is missing; offline is not zero")
    _require(mac.get("workspace_root") == MAC_WORKSPACE_ROOT, "unexpected Mac workspace root")
    for name in ("known_work_bytes", "occupancy_reserve_bytes", "registered_remaining_write_bytes", "new_write_limit_bytes", "reservation_bytes"):
        _bytes(mac.get(name), "mac." + name)
    _require(mac["occupancy_reserve_bytes"] >= mac["known_work_bytes"], "Mac occupancy reserve is below known occupancy")
    _require(mac.get("training_completed") is True, "Mac training completion is unproved")
    _require(mac.get("remaining_write_bound_reliable") is True, "unknown Mac remaining writes: STOP")
    _require(type(mac.get("active_new_tasks")) is list and mac["active_new_tasks"] == [], "active new Mac tasks require a new reservation")
    expected_mac = mac["occupancy_reserve_bytes"] + mac["registered_remaining_write_bytes"] + mac["new_write_limit_bytes"]
    _require(mac["reservation_bytes"] == expected_mac, "Mac reservation must cover occupancy and all write allowances")
    shared = _bytes(plan.get("shared_temporary_limit_bytes"), "shared_temporary_limit_bytes")
    linux_limit = _bytes(plan.get("linux_limit_bytes"), "linux_limit_bytes")
    _require(expected_mac + shared <= total, "Mac/shared reservations overcommit 80 GiB")
    _require(linux_limit == total - expected_mac - shared, "Linux quota must be 80 GiB minus Mac and shared reservations")
    proofs = plan.get("proofs")
    _require(isinstance(proofs, dict), "hashed quota proofs are missing")
    roles = {
        "mac_capacity": {"workspace_root": MAC_WORKSPACE_ROOT, "known_work_bytes": mac["known_work_bytes"]},
        "mac_training_completed": {"completed": True},
        "mac_write_bound": {key: mac[key] for key in ("registered_remaining_write_bytes", "new_write_limit_bytes", "remaining_write_bound_reliable", "active_new_tasks")},
        "quota_registration": {"occupancy_reserve_bytes": mac["occupancy_reserve_bytes"], "reservation_bytes": expected_mac, "shared_temporary_limit_bytes": shared, "linux_limit_bytes": linux_limit},
    }
    checked = {role: _proof(role, proofs.get(role), claims, frozen_at, base_dir) for role, claims in roles.items()}
    if check_seal:
        _require(plan.get("frozen_plan_sha256") == _digest(plan), "frozen plan changed; register a new evidenced quota")
    return checked


def seal_plan(plan, *, base_dir=None):
    """Validate evidence and return a copied plan with its canonical SHA256."""
    result = deepcopy(plan)
    _validate_plan(result, Path.cwd() if base_dir is None else base_dir, check_seal=False)
    result["frozen_plan_sha256"] = _digest(result)
    return result


def admit_capacity(plan, linux_work_bytes, linux_free_bytes, planned_output_bytes,
                   registered_mac_remaining_bytes=0, *, base_dir=None):
    """Admit only a Linux job that fits the existing frozen, evidenced quota.

    ``planned_output_bytes`` covers the job's remaining durable output/downloads.
    Shared scratch is conservatively reserved separately and must also fit Linux
    free disk. ``registered_mac_remaining_bytes`` cannot grow the frozen reserve.
    Use current Linux readings at every admission/monitor check; no live Mac
    reading or age threshold is required. Mac writes must stay within the plan.
    """
    values = {
        "linux_work_bytes": linux_work_bytes, "linux_free_bytes": linux_free_bytes,
        "planned_output_bytes": planned_output_bytes,
        "registered_mac_remaining_bytes": registered_mac_remaining_bytes,
    }
    for name, value in values.items():
        _bytes(value, name)
    checked = _validate_plan(plan, Path.cwd() if base_dir is None else base_dir, check_seal=True)
    mac = plan["mac"]
    _require(registered_mac_remaining_bytes <= mac["registered_remaining_write_bytes"], "Mac remaining writes grew: register a new evidenced quota")
    linux_peak = linux_work_bytes + planned_output_bytes
    _require(linux_peak <= plan["linux_limit_bytes"], "Linux occupancy plus planned outputs exceeds frozen quota")
    required_free = planned_output_bytes + plan["shared_temporary_limit_bytes"]
    _require(linux_free_bytes >= required_free, "Linux free disk cannot cover planned outputs and shared scratch")
    return {
        "status": "ADMITTED_QUOTA", "plan_id": plan["plan_id"],
        "frozen_plan_sha256": plan["frozen_plan_sha256"],
        **values, "linux_limit_bytes": plan["linux_limit_bytes"],
        "linux_peak_bytes": linux_peak, "mac_reservation_bytes": mac["reservation_bytes"],
        "shared_temporary_limit_bytes": plan["shared_temporary_limit_bytes"],
        "combined_peak_bytes": linux_peak + mac["reservation_bytes"] + plan["shared_temporary_limit_bytes"],
        "required_linux_free_bytes": required_free, "verified_proof_sha256": checked,
        "mac_heartbeat_required": False,
        "transfer_policy": "Mac jump required; verify live Mac status before any transfer",
    }
