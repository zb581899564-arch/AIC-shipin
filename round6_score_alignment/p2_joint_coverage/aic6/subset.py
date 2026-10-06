"""Reproduce the frozen P2 v2 inference subset from the full source-frame list.

The original draw used ``random.Random(20260918).sample`` on the ordered gap
rows, retained every control row, then restored the full manifest's row order.
The original JSONL line bytes (including CRLF) are preserved, so this can be
checked against the historical subset by SHA-256 without rewriting it.
"""
from __future__ import annotations

import json
import random


def regenerate_subset_bytes(full_manifest: bytes, *, seed: int,
                            n_gaps: int) -> bytes:
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError("seed must be an integer")
    if isinstance(n_gaps, bool) or not isinstance(n_gaps, int) or n_gaps < 0:
        raise ValueError("n_gaps must be a non-negative integer")

    lines = full_manifest.splitlines(keepends=True)
    gaps: list[int] = []
    controls: set[int] = set()
    keys: set[tuple[str, int]] = set()
    for position, line in enumerate(lines):
        row = json.loads(line)
        if not isinstance(row, dict) or not isinstance(row.get("video_id"), str):
            raise ValueError(f"invalid request at line {position + 1}")
        frame = row.get("source_frame")
        if isinstance(frame, bool) or not isinstance(frame, int) or frame < 0:
            raise ValueError(f"invalid source_frame at line {position + 1}")
        key = (row["video_id"], frame)
        if key in keys:
            raise ValueError(f"duplicate request key: {key}")
        keys.add(key)
        if row.get("kind") == "NEEDS_INFERENCE":
            gaps.append(position)
        elif row.get("kind") == "CONTROL_SAME_FRAME":
            controls.add(position)
        else:
            raise ValueError(f"unknown request kind at line {position + 1}")
    if n_gaps > len(gaps):
        raise ValueError("requested more gaps than available")

    sampled = set(random.Random(seed).sample(gaps, n_gaps))
    return b"".join(line for position, line in enumerate(lines)
                    if position in controls or position in sampled)
