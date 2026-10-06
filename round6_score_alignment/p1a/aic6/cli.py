"""Public call boundary for P1a with explicit, non-zero failure exits.

Exit codes
----------
``score``
    0  a joint score was produced (status OK)
    2  the input or the reference is invalid (`INVALID_INPUT` / `INVALID_REFERENCE`)
    3  no score is computable (`NOT_COMPUTABLE` / `SPARSE_DIAGNOSTIC`)
    1  unexpected internal error

``compose``
    0  succeeded and deliverable (`OK_DELIVERABLE`), or legacy replay completed
    2  failure (`FAILED_INVALID_WINDOWS`)
    4  parsed but undeliverable (`NOT_DELIVERABLE_NEEDS_SPATIAL_INFERENCE`)
    1  unexpected internal error

Every path writes its result JSON before exiting, so a caller always has the
diagnostic even on failure.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import scoring
from .compose import (
    COMPOSITION_EXIT_CODES,
    CompositionMode,
    ShotMap,
    compose,
    load_spatial_source,
    load_windows,
)
from .segments import SegmentConstraint


def _write(path: str, payload: dict) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _score_command(args: argparse.Namespace) -> int:
    index = scoring.load_index(args.index)
    try:
        predictions = scoring.load_predictions(args.predictions, index)
    except Exception as exc:                      # validation is fail-closed
        _write(args.out, {"status": "INVALID_INPUT", "score": None, "official_status":
                          "INTERNAL_SPEC_REIMPLEMENTATION",
                          "error": f"{type(exc).__name__}: {exc}"})
        print(f"score failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    reference = None
    if args.reference:
        try:
            reference = scoring.load_reference(args.reference, index)
        except (scoring.ReferenceError, json.JSONDecodeError, OSError) as exc:
            _write(args.out, {"status": "INVALID_REFERENCE", "score": None,
                              "official_status": "INTERNAL_SPEC_REIMPLEMENTATION",
                              "error": f"{type(exc).__name__}: {exc}"})
            print(f"reference rejected: {exc}", file=sys.stderr)
            return 2

    result = scoring.score_joint(predictions=predictions, reference=reference, index=index)
    _write(args.out, result)
    status = result.get("status")
    if status == scoring.ScoreStatus.OK.value:
        print(json.dumps({k: result[k] for k in ("status", "score", "video_count")}, indent=2))
        return 0
    if status == scoring.ScoreStatus.INVALID_INPUT.value:
        print(f"invalid input: {result.get('issue_codes')}", file=sys.stderr)
        return 2
    print(f"no score computable: {status}", file=sys.stderr)
    return 3


def _compose_command(args: argparse.Namespace) -> int:
    requests, fps_by_video, n_frames_by_video = load_windows(args.temporal)
    spatial = load_spatial_source(args.spatial) if args.spatial else {}
    shot_map = None
    if args.shots:
        payload = json.loads(Path(args.shots).read_text(encoding="utf-8"))
        shot_map = ShotMap(shots_by_video={str(k): tuple(tuple(s) for s in v)
                                           for k, v in payload.items()})
    constraint = SegmentConstraint(args.min_segments, args.max_segments)
    report = compose(requests=requests, spatial_source=spatial, fps_by_video=fps_by_video,
                     n_frames_by_video=n_frames_by_video, constraint=constraint,
                     mode=CompositionMode(args.mode), shot_map=shot_map,
                     max_shot_nearest_gap_frames=args.max_shot_nearest_gap_frames)
    _write(args.out, report)
    print(json.dumps({"status": report["status"], "deliverable": report["deliverable"],
                      "totals": report["totals"]}, ensure_ascii=False, indent=2))
    return COMPOSITION_EXIT_CODES[report["status"]]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="aic6.cli", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    score = sub.add_parser("score", help="internal joint scorer (not the official evaluator)")
    score.add_argument("--predictions", required=True)
    score.add_argument("--reference", default=None)
    score.add_argument("--index", required=True)
    score.add_argument("--out", required=True)
    score.set_defaults(func=_score_command)

    comp = sub.add_parser("compose", help="traceable composition report (never a submission)")
    comp.add_argument("--temporal", required=True)
    comp.add_argument("--spatial", default=None)
    comp.add_argument("--shots", default=None)
    comp.add_argument("--out", required=True)
    comp.add_argument("--mode", choices=[m.value for m in CompositionMode], default="traceable")
    comp.add_argument("--min-segments", type=int, default=0)
    comp.add_argument("--max-segments", type=int, default=5)
    comp.add_argument("--max-shot-nearest-gap-frames", type=int, default=None)
    comp.set_defaults(func=_compose_command)
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return int(args.func(args))
    except Exception as exc:                       # last-resort boundary
        print(f"aic6.cli failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        if getattr(args, "out", None):
            _write(args.out, {"status": "ERROR", "score": None,
                              "error": f"{type(exc).__name__}: {exc}"})
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
