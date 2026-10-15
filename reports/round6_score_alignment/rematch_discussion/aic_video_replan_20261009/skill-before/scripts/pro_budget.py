"""Local append-only Pro reservations. Never controls a browser or calls a model."""

import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import sys
from datetime import datetime, timezone
import uuid


LIMIT = 3
SCHEMA = "ai-yiguodun.pro-budget/1"


def now():
    return datetime.now(timezone.utc).isoformat()


def write_exclusive(path, value):
    # O_EXCL makes concurrent reservation of the same slot fail closed.
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def initialize(root, task_id, already_used):
    root = Path(root).resolve()
    if not task_id.strip() or type(already_used) is not int or not 0 <= already_used <= LIMIT:
        raise ValueError("Confirm a nonempty task ID and already-used count between 0 and 3")
    if root.exists() and any(root.iterdir()):
        raise ValueError("Ledger is not empty; resume it instead of resetting the budget")
    root.mkdir(parents=True, exist_ok=True)
    value = {"schema": SCHEMA, "task_id": task_id, "limit": LIMIT,
             "already_used_confirmed": already_used, "created_at": now()}
    write_exclusive(root / "run.json", value)
    return value


def read_ledger(root):
    root = Path(root).resolve()
    value = json.loads((root / "run.json").read_text(encoding="utf-8"))
    used = value.get("already_used_confirmed")
    if (value.get("schema") != SCHEMA or value.get("limit") != LIMIT
            or type(used) is not int or not 0 <= used <= LIMIT
            or not isinstance(value.get("task_id"), str) or not value["task_id"].strip()):
        raise ValueError("Invalid ledger; do not infer zero or reset it")
    reservations = []
    for path in sorted(root.glob("pro-*-reservation.json")):
        item = json.loads(path.read_text(encoding="utf-8"))
        slot = item.get("slot")
        if (type(slot) is not int or not used < slot <= LIMIT
                or path.name != f"pro-{slot:02d}-reservation.json"
                or item.get("task_id") != value["task_id"]
                or not isinstance(item.get("packets"), list) or not item["packets"]):
            raise ValueError("Invalid reservation; preserve it and diagnose")
        reservations.append(item)
    return root, value, reservations


@contextmanager
def reservation_lock(root):
    root = Path(root).resolve()
    # The ledger must exist; never silently initialize a budget on recovery.
    if not (root / "run.json").is_file():
        raise ValueError("Ledger does not exist; confirm historical use before initialization")
    lock = root / "reservation.lock"
    token = uuid.uuid4().hex
    try:
        write_exclusive(lock, {"token": token, "created_at": now()})
    except FileExistsError:
        raise ValueError("BUDGET_LOCKED: another reservation or interrupted operation; inspect before retry")
    try:
        yield
    finally:
        # Only remove the exact temporary lock this operation created.
        if json.loads(lock.read_text(encoding="utf-8")).get("token") != token:
            raise ValueError("Lock ownership changed; preserve the lock and diagnose")
        lock.unlink()


def reserve(root, packet_paths):
    with reservation_lock(root):
        return reserve_locked(root, packet_paths)


def reserve_locked(root, packet_paths):
    root, run, existing = read_ledger(root)
    packets = []
    for filename in packet_paths:
        path = Path(filename).resolve(strict=True)
        if not path.is_file() or path.suffix.lower() != ".md":
            raise ValueError("Every packet must be an actual Markdown file")
        data = path.read_bytes()
        if not data.decode("utf-8-sig").strip():
            raise ValueError("Empty packet; finish the full context file first")
        packets.append({"path": str(path), "bytes": len(data),
                        "sha256": hashlib.sha256(data).hexdigest()})
    if not packets:
        raise ValueError("At least one complete Markdown packet is required")
    identity = sorted(p["sha256"] for p in packets)
    if len(set(identity)) != len(identity):
        raise ValueError("Duplicate packet in the same request")
    if any(sorted(p["sha256"] for p in old["packets"]) == identity for old in existing):
        raise ValueError("This packet is already reserved; inspect send state, do not resend")
    for slot in range(run["already_used_confirmed"] + 1, LIMIT + 1):
        value = {"task_id": run["task_id"], "slot": slot, "reserved_at": now(),
                 "packets": packets, "required_browser": "Google Chrome",
                 "required_mode": "Pro", "send_status": "NOT_YET_OBSERVED"}
        try:
            write_exclusive(root / f"pro-{slot:02d}-reservation.json", value)
            return value
        except FileExistsError:
            continue
    raise ValueError("PRO_LIMIT_REACHED: all three calls are used or reserved")


def outcome(root, slot, status, note):
    root, run, reservations = read_ledger(root)
    if status not in {"completed", "uncertain", "not-sent"}:
        raise ValueError("Invalid outcome status")
    if not any(item["slot"] == slot for item in reservations):
        raise ValueError("No reservation exists for this slot")
    value = {"task_id": run["task_id"], "slot": slot, "observed_at": now(),
             "status": status, "note": note, "refund": False}
    write_exclusive(root / f"pro-{slot:02d}-outcome-{uuid.uuid4().hex}.json", value)
    return value


def status(root):
    root, run, reservations = read_ledger(root)
    count = run["already_used_confirmed"] + len(reservations)
    outcomes = [json.loads(p.read_text(encoding="utf-8"))
                for p in sorted(root.glob("pro-*-outcome-*.json"))]
    return {"task_id": run["task_id"], "limit": LIMIT,
            "used_or_reserved": count, "remaining": LIMIT - count,
            "reservations": reservations,
            "outcomes": sorted(outcomes, key=lambda item: item["observed_at"]),
            "ui_execution_verified_by_this_script": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for command in ("init", "status", "reserve", "outcome"):
        sub = commands.add_parser(command)
        sub.add_argument("--ledger", required=True, type=Path)
        if command == "init":
            sub.add_argument("--task-id", required=True)
            sub.add_argument("--already-used", required=True, type=int)
        elif command == "reserve":
            sub.add_argument("--packet", required=True, nargs="+", type=Path)
        elif command == "outcome":
            sub.add_argument("--slot", required=True, type=int)
            sub.add_argument("--status", required=True,
                             choices=["completed", "uncertain", "not-sent"])
            sub.add_argument("--note", required=True)
    args = parser.parse_args()
    try:
        if args.command == "init":
            result = initialize(args.ledger, args.task_id, args.already_used)
        elif args.command == "reserve":
            result = reserve(args.ledger, args.packet)
        elif args.command == "outcome":
            result = outcome(args.ledger, args.slot, args.status, args.note)
        else:
            result = status(args.ledger)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({"status": "BLOCKED", "error": str(error)}, ensure_ascii=False),
              file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
