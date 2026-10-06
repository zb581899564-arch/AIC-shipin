from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path


def digest(key: str, value: object) -> str:
    return hashlib.sha256(f"{key}:{value}".encode("utf-8")).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--registry", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    path = args.registry.resolve()
    registry = json.loads(path.read_text(encoding="utf-8"))
    components = set()
    weak_path = root / "reports/round6_score_alignment/training_alignment_20260917/weak_split_manifest.jsonl"
    for line in weak_path.read_text(encoding="utf-8").splitlines():
        row = json.loads(line)
        if row.get("split") != "holdout":
            continue
        for key in ("row_index", "video_id", "source_vid", "youtube_id"):
            components.add(digest(key, row[key]))
    gnmc_path = root / "reports/round6_score_alignment/p2r_reference_gate/round6_p2r_20260919T154701Z/sealed_holdout_manifest.jsonl"
    pattern = re.compile(r'"item_id"\s*:\s*("(?:[^"\\]|\\.)*")')
    for line in gnmc_path.read_text(encoding="utf-8").splitlines():
        match = pattern.search(line)
        if match is None:
            raise RuntimeError("missing item_id")
        item_id = json.loads(match.group(1))
        components.add(digest("item_id", item_id))
        components.add(digest("source_group", item_id))
    registry["blocked_component_sha256"] = sorted(components)
    registry["counts"]["blocked_component_digests"] = len(components)
    registry["component_guard_added_utc"] = datetime.now(timezone.utc).isoformat()
    registry["component_guard_note"] = "individual row/id/source fields are denied even if a caller changes the composite item_id"
    path.write_text(json.dumps(registry, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PASS", "blocked_component_digests": len(components)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
