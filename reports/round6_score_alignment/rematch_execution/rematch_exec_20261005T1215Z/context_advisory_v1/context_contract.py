"""Registered descriptive overview contract; no label or prediction repair.

Frame numbers refer to the actual sampled overview frames, never boundaries.
An empty event table is legal. It certifies neither absence of highlights nor
complete visual observation of the unsampled source.
"""
import hashlib
import json
import math
from bisect import bisect_left

DESCRIPTION_CHARS = frozenset("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 .,;:!?/'()-")
MAX_EVENTS = 8
MAX_DESCRIPTION = 80
OPEN = '{"events":['


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
        allow_nan=False, separators=(",", ":")).encode()).hexdigest()


class OverviewGrammar:
    """Canonical prefix grammar with physically bounded, ordered endpoints.

No event is inserted or sorted after generation. Events need not be ordered:
different visible activities may overlap. Each one names a nonempty range of
real sampled frames (including a single frame).
"""
    def __init__(self, frame_count):
        require(type(frame_count) is int and 1 <= frame_count <= 64, "invalid overview frame denominator")
        self.frame_count = frame_count
        self.prepared = None
        self.initial = ("literal", OPEN, 0, "first_or_close", 0, "", None, 0, False)

    def step(self, snapshot, c):
        state, literal, pos, after_literal, events, number, first, size, nonspace = snapshot
        if state == "literal":
            if pos >= len(literal) or literal[pos] != c:
                return None
            pos += 1
            if pos == len(literal):
                state = after_literal
        elif state in ("first_or_close", "event_open"):
            if state == "first_or_close" and c == "]":
                state, literal, pos, after_literal = "literal", "}", 0, "complete"
            elif c == "{" and events < MAX_EVENTS:
                state, literal, pos, after_literal = "literal", '"first":', 0, "first"
                number = ""
            else:
                return None
        elif state in ("first", "last"):
            lo = 0 if state == "first" else first
            allowed = [str(i) for i in range(lo, self.frame_count)]
            if c.isdigit():
                number += c
                if not any(n.startswith(number) for n in allowed):
                    return None
            elif c == "," and number in allowed:
                if state == "first":
                    first = int(number)
                    state, literal, pos, after_literal = "literal", '"last":', 0, "last"
                    number = ""
                else:
                    state, literal, pos, after_literal = "literal", '"description":"', 0, "description"
                    size, nonspace = 0, False
            else:
                return None
        elif state == "description":
            if c == '"' and nonspace:
                state, literal, pos, after_literal = "literal", "}", 0, "after_event"
            elif c in DESCRIPTION_CHARS and size < MAX_DESCRIPTION:
                size += 1
                nonspace = nonspace or bool(c.strip())
                if size == MAX_DESCRIPTION and not nonspace:
                    return None
            else:
                return None
        elif state == "after_event":
            events += 1
            if c == "]":
                state, literal, pos, after_literal = "literal", "}", 0, "complete"
            elif c == "," and events < MAX_EVENTS:
                state = "event_open"
            else:
                return None
        else:
            return None
        return state, literal, pos, after_literal, events, number, first, size, nonspace

    def walk(self, text, snapshot):
        if not isinstance(text, str) or not text.isascii() or snapshot is None:
            return None
        for c in text:
            snapshot = self.step(snapshot, c)
            if snapshot is None:
                break
        return snapshot

    def scan(self, text):
        snapshot = self.walk(text, self.initial)
        return snapshot is not None, snapshot is not None and snapshot[0] == "complete"

    def prepare(self, text):
        self.prepared = self.walk(text, self.initial)
        require(self.prepared is not None, "invalid actual decoded overview prefix")

    def can_extend(self, piece):
        return self.walk(piece, self.prepared) is not None

    def valid_prefix(self, text):
        return self.scan(text)[0]

    def complete(self, text):
        return all(self.scan(text))


def validate_overview(raw, actual_pts):
    require(OverviewGrammar(len(actual_pts)).complete(raw), "invalid/truncated overview JSON")
    value = json.loads(raw)
    require(list(value) == ["events"] and isinstance(value["events"], list), "overview schema changed")
    require(all(math.isfinite(x) for x in actual_pts) and
        all(b > a for a, b in zip(actual_pts, actual_pts[1:])), "overview PTS identity invalid")
    for e in value["events"]:
        require(set(e) == {"first", "last", "description"}, "event schema changed")
        require(type(e["first"]) is int and type(e["last"]) is int and
            0 <= e["first"] <= e["last"] < len(actual_pts), "event references no actual frame")
        require(isinstance(e["description"], str) and e["description"].strip(), "empty event description")
    return value


def overview_plan(path, sha, points, endpoint, window_id, **identity):
    require(points and all(math.isfinite(x) for x in points) and
        all(b > a for a, b in zip(points, points[1:])), "full source PTS required")
    require(math.isfinite(endpoint) and endpoint > points[-1], "physical source endpoint missing")
    n = len(points)
    ids = list(range(n)) if n <= 64 else [i * (n - 1) // 63 for i in range(64)]
    return dict(identity, source_path=str(path), source_sha256=sha, window_id=window_id,
        window_pts_start_sec=points[0], window_pts_end_exclusive_sec=endpoint,
        window_duration_sec=endpoint - points[0], planned_source_frame_ordinals=ids,
        planned_actual_pts_sec=[points[i] for i in ids], eligible_source_frame_count=n,
        source_total_frames=n, overview_is_sparse_not_complete_observation=True)


def render_event_table(value, actual_pts, local_start, local_end):
    """Exact program mapping. Missing events are never certified negative."""
    validate_overview(json.dumps(value, separators=(",", ":")), actual_pts)
    return json.dumps({"source_events": [{"source_first_pts": actual_pts[e["first"]],
        "source_last_pts": actual_pts[e["last"]], "description": e["description"]}
        for e in value["events"]], "current_window_source_start": local_start,
        "current_window_source_end_exclusive": local_end,
        "sparse_overview_may_miss_local_events": True}, ensure_ascii=False, separators=(",", ":"))


def deterministic_derangement(source_keys, durations):
    """Adjacent duration ranks, cyclic shift: no source can describe itself."""
    require(len(set(source_keys)) == len(source_keys) >= 2, "shuffle needs distinct sources")
    ordered = sorted(source_keys, key=lambda k: (durations[k], k))
    return {k: ordered[(i + 1) % len(ordered)] for i, k in enumerate(ordered)}


def interval_union(values):
    ordered = sorted(values)
    out = []
    for a, b in ordered:
        require(math.isfinite(a) and math.isfinite(b) and a < b, "invalid analysis interval")
        if out and a <= out[-1][1]:
            out[-1][1] = max(b, out[-1][1])
        else:
            out.append([a, b])
    return out


def overlap_seconds(a, b):
    return sum(max(0, min(y, v) - max(x, u)) for x, y in interval_union(a) for u, v in interval_union(b))


def seconds(values):
    return sum(b - a for a, b in interval_union(values))


def interval_jaccard(a, b):
    intersection = overlap_seconds(a, b)
    union = seconds(a) + seconds(b) - intersection
    return 1.0 if union == 0 else intersection / union


def weak_metrics(pred, reference):
    ps, rs, inter = seconds(pred), seconds(reference), overlap_seconds(pred, reference)
    precision = inter / ps if ps else (1.0 if not rs else 0.0)
    recall = inter / rs if rs else (1.0 if not ps else 0.0)
    return {"precision": precision, "recall": recall,
        "f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0,
        "pred_seconds": ps, "reference_seconds": rs, "intersection_seconds": inter}
