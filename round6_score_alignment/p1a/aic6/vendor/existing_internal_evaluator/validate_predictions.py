"""CLI for validating AIC prediction JSONL against B's media metadata."""

from __future__ import annotations

import argparse
import json
from typing import Optional, Sequence

from .schema import load_jsonl_records, load_media_metadata, validate_submission_records


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Validate AIC highlight prediction JSONL")
    parser.add_argument("--metadata", required=True, help="fixed index/media metadata JSON")
    parser.add_argument("--predictions", required=True, help="prediction JSONL")
    parser.add_argument("--out", required=True, help="JSON validation report")
    parser.add_argument(
        "--allow-partial",
        action="store_true",
        help="diagnostic mode: do not require one output line for every indexed video",
    )
    args = parser.parse_args(argv)

    metadata = load_media_metadata(args.metadata)
    records, parse_issues = load_jsonl_records(args.predictions)
    report = validate_submission_records(
        records,
        metadata,
        require_complete=not args.allow_partial,
    )
    result = report.as_dict(include_predictions=True)
    result["parse_issues"] = parse_issues
    if parse_issues:
        result["ok"] = False
        result["error_count"] += len(parse_issues)
    result["metadata"] = {
        "video_count": len(metadata),
        "source": str(args.metadata),
        "is_ground_truth": False,
    }
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(json.dumps({"ok": bool(result["ok"]), "out": str(args.out), "valid_prediction_count": report.valid_prediction_count}))
    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
