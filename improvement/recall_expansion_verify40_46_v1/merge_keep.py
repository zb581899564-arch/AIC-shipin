"""Pure KEEP-only recall merge; baseline prediction JSON bytes remain intact.

Candidates use RECALL_VERIFIED_CANDIDATES_V1. Each item has candidate_id,
video_id, source_sha256, start_exact, end_exact, decision, execution_status
(``MODEL_OK``), independent_cpu_qa_status (``PASS``). The field callback is
called once per added frame and returns status=ACCEPTED_SOURCE_FIELD_FRAME,
video_id, source_sha256, frame, targetRatioWH and an accepted [x,y,w] bboxes.

CLI --accepted-field is JSONL of those callback objects. This is caller-supplied
accepted evidence, not a source-field validator or a model-quality gate.
"""
from __future__ import annotations

import argparse
from bisect import bisect_left
from dataclasses import dataclass
from decimal import Decimal
from fractions import Fraction
import json
import math
from pathlib import Path

from overlap_plan import (exact, read_json_document, reject_constant, require,
                          stable_id, unique_object, validate_sources, write_json_document)

CANDIDATE_SCHEMA = "RECALL_VERIFIED_CANDIDATES_V1"
DECISIONS = ("KEEP", "UNKNOWN", "DROP")
DECODER = json.JSONDecoder(object_pairs_hook=unique_object, parse_float=Decimal,
                           parse_constant=reject_constant)


def number(value):
    require(type(value) in (int, float, Decimal), "Box coordinates must be non-bool numeric values")
    require(not isinstance(value, float) or math.isfinite(value), "Nonfinite box coordinate")
    require(not isinstance(value, Decimal) or value.is_finite(), "Nonfinite box coordinate")
    return Fraction(str(value))


def validate_box(box, source):
    require(isinstance(box, list) and len(box) == 3, "bboxes must be a flat [x,y,w] triplet")
    x, y, width = map(number, box)
    ratio = source["targetRatioWH"]
    height = width * ratio[1] / ratio[0]
    tolerance = Fraction(1, 10**9)  # Same bounds tolerance as the existing official-shape loader.
    require(x >= 0 and y >= 0 and width > 0 and x + width <= source["width"] + tolerance
            and y + height <= source["height"] + tolerance, "Crop box is outside the registered source geometry")


def skip_space(text, position):
    while position < len(text) and text[position] in " \t\r\n":
        position += 1
    return position


def top_level_spans(text):
    """Find exact JSON value slices; decode strings rather than regex matching."""
    position = skip_space(text, 0)
    require(position < len(text) and text[position] == "{", "Baseline row must be a JSON object")
    position = skip_space(text, position + 1)
    spans = {}
    if position < len(text) and text[position] == "}":
        return spans
    while True:
        key, position = DECODER.raw_decode(text, position)
        require(isinstance(key, str) and key not in spans, "Invalid/duplicate baseline object key")
        position = skip_space(text, position)
        require(position < len(text) and text[position] == ":", "Missing JSON object colon")
        first = skip_space(text, position + 1)
        _, position = DECODER.raw_decode(text, first)
        spans[key] = (first, position)
        position = skip_space(text, position)
        require(position < len(text) and text[position] in ",}", "Invalid JSON object delimiter")
        if text[position] == "}":
            require(skip_space(text, position + 1) == len(text), "Trailing baseline JSON content")
            return spans
        position = skip_space(text, position + 1)


def prediction_slices(text, span):
    first, last = span
    require(text[first] == "[" and text[last - 1] == "]", "Baseline predictions must be an array")
    position = skip_space(text, first + 1)
    values = []
    while position < last - 1:
        start = position
        item, position = DECODER.raw_decode(text, position)
        values.append((item, text[start:position].encode("utf-8")))
        position = skip_space(text, position)
        if position == last - 1:
            break
        require(text[position] == ",", "Invalid prediction array delimiter")
        position = skip_space(text, position + 1)
    return values


def baseline_records(baseline_bytes, sources):
    require(isinstance(baseline_bytes, bytes) and bool(baseline_bytes), "Baseline must be nonempty UTF-8 JSONL bytes")
    records, seen = [], set()
    for line in baseline_bytes.splitlines(keepends=True):
        ending = b"\r\n" if line.endswith(b"\r\n") else b"\n" if line.endswith(b"\n") else b""
        body = line[:-len(ending)] if ending else line
        text = body.decode("utf-8")
        require(bool(text.strip()), "Blank baseline records are not accepted")
        row = DECODER.decode(text)
        require(isinstance(row, dict) and set(row) == {"video_id", "targetRatioWH", "predictions", "model_params_b"},
                "Baseline row requires video_id, targetRatioWH, predictions and the actual model_params_b")
        require(number(row["model_params_b"]) == Fraction(8782459120, 10**9),
                "Protected baseline must declare the actual unchanged 8.78245912B model")
        video_id = stable_id(row["video_id"])
        require(video_id in sources and video_id not in seen, "Unknown or duplicate baseline source")
        source = sources[video_id]["source"]
        ratio = row["targetRatioWH"]
        require(isinstance(ratio, list) and all(type(v) is int for v in ratio)
                and ratio == source["targetRatioWH"], "Baseline target ratio differs from registered source")
        require(isinstance(row["predictions"], list), "Baseline predictions must be an explicit list")
        spans = top_level_spans(text)
        items = prediction_slices(text, spans["predictions"])
        require(len(items) == len(row["predictions"]), "Baseline prediction slice denominator differs")
        raw_by_frame, previous = {}, -1
        for item, raw in items:
            require(isinstance(item, dict) and set(item) == {"frame", "bboxes"}, "Invalid baseline prediction fields")
            frame = item["frame"]
            require(type(frame) is int and previous < frame < source["n_frames"],
                    "Baseline frames must be unique sorted non-bool in-domain integers")
            validate_box(item["bboxes"], source)
            raw_by_frame[frame], previous = raw, frame
        ratio_span = spans["targetRatioWH"]
        records.append(dict(video_id=video_id, text=text, ending=ending, original_line=line,
            prediction_span=spans["predictions"], raw_by_frame=raw_by_frame,
            ratio_bytes=text[ratio_span[0]:ratio_span[1]].encode("utf-8"),
            model_params_bytes=text[spans["model_params_b"][0]:spans["model_params_b"][1]].encode("utf-8")))
        seen.add(video_id)
    require(seen == set(sources), "Baseline source set must exactly match the registered source collection")
    return records


def render_new_prediction(frame, box):
    def numeric_text(value):
        if type(value) is Decimal:
            return str(value)
        return json.dumps(value, allow_nan=False, separators=(",", ":"))
    return ("{\"frame\":" + str(frame) + ",\"bboxes\":[" + ",".join(map(numeric_text, box)) + "]}").encode("utf-8")


@dataclass(frozen=True)
class MergeResult:
    predictions_jsonl: bytes
    differences: dict
    gate: dict


def merge_verified_candidates(sources_document, baseline_jsonl_bytes, candidates_document, accepted_field_callback):
    sources = validate_sources(sources_document)
    baseline = baseline_records(baseline_jsonl_bytes, sources)
    require(isinstance(candidates_document, dict) and candidates_document.get("schema") == CANDIDATE_SCHEMA,
            "RECALL_VERIFIED_CANDIDATES_V1 is required")
    candidates = candidates_document.get("candidates")
    require(isinstance(candidates, list), "Candidate collection must be an explicit list")
    require(callable(accepted_field_callback), "An accepted source-field callback is required")
    kept_frames = {video_id: {} for video_id in sources}
    candidate_ids, diagnostics = set(), []
    for candidate in candidates:
        require(isinstance(candidate, dict), "Every candidate must be an object")
        candidate_id = stable_id(candidate.get("candidate_id"))
        require(candidate_id not in candidate_ids, "Duplicate candidate identity")
        candidate_ids.add(candidate_id)
        video_id = stable_id(candidate.get("video_id"))
        require(video_id in sources, "Candidate refers to an unregistered source")
        value, decision = sources[video_id], candidate.get("decision")
        require(candidate.get("source_sha256") == value["source"]["source_sha256"], "Candidate source SHA256 differs")
        require(candidate.get("execution_status") == "MODEL_OK"
                and candidate.get("independent_cpu_qa_status") == "PASS",
                "Engineering/model/QA failure blocks merge; it cannot become UNKNOWN")
        require(decision in DECISIONS, "Missing or invalid explicit KEEP/UNKNOWN/DROP decision")
        start, end = exact(candidate.get("start_exact")), exact(candidate.get("end_exact"))
        require(0 <= start < end <= value["end"], "Zero-length or out-of-domain candidate interval")
        first, limit = bisect_left(value["points"], start), bisect_left(value["points"], end)
        require(first < limit, "Candidate interval has no native source frame")
        if decision == "KEEP":
            for frame in range(first, limit):
                kept_frames[video_id].setdefault(frame, []).append(candidate_id)
        diagnostics.append(dict(candidate_id=candidate_id, video_id=video_id, decision=decision,
            start_exact=str(start), end_exact=str(end), native_first=first, native_stop=limit,
            new_contribution_allowed=decision == "KEEP"))
    output, added, before_count = [], [], 0
    for record in baseline:
        video_id = record["video_id"]
        source, old = sources[video_id]["source"], record["raw_by_frame"]
        before_count += len(old)
        new_frames = sorted(set(kept_frames[video_id]) - set(old))
        merged = dict(old)
        for frame in new_frames:
            field = accepted_field_callback(video_id, frame)
            require(isinstance(field, dict) and field.get("status") == "ACCEPTED_SOURCE_FIELD_FRAME",
                    "New frame requires an explicitly accepted source-field result")
            require(field.get("video_id") == video_id and type(field.get("frame")) is int and field["frame"] == frame
                    and field.get("source_sha256") == source["source_sha256"]
                    and isinstance(field.get("targetRatioWH"), list)
                    and all(type(v) is int for v in field["targetRatioWH"])
                    and field["targetRatioWH"] == source["targetRatioWH"], "Accepted source field identity/ratio differs")
            box = field.get("bboxes")
            validate_box(box, source)
            merged[frame] = render_new_prediction(frame, box)
            added.append(dict(video_id=video_id, frame=frame, supporting_KEEP_candidate_ids=kept_frames[video_id][frame]))
        if not new_frames:
            output.append(record["original_line"])
        else:
            first, last = record["prediction_span"]
            content = b",".join(merged[frame] for frame in sorted(merged))
            output.append(record["text"][:first + 1].encode("utf-8") + content
                          + record["text"][last - 1:].encode("utf-8") + record["ending"])
    prediction_bytes = b"".join(output)
    after = baseline_records(prediction_bytes, sources)
    for old_record, new_record in zip(baseline, after):
        require(old_record["video_id"] == new_record["video_id"]
                and old_record["ratio_bytes"] == new_record["ratio_bytes"]
                and old_record["model_params_bytes"] == new_record["model_params_bytes"],
                "Original source/ratio/actual parameter JSON bytes changed")
        require(all(new_record["raw_by_frame"].get(frame) == raw
                    for frame, raw in old_record["raw_by_frame"].items()), "Original baseline frame/box JSON bytes changed")
    nonzero = bool(added)
    gate = dict(schema="RECALL_KEEP_MERGE_GATE_V1",
        status="PASS_MERGE_ENGINEERING_NONZERO_NOT_QUALITY" if nonzero else "FAIL_ZERO_PREDICTION_DIFFERENCE",
        source_set_exact=True, source_count=len(sources), candidate_count=len(candidates),
        baseline_frames=before_count, added_frames=len(added), merged_frames=before_count + len(added),
        nonzero_prediction_difference=nonzero, candidate_ready_for_quality_gate=nonzero,
        baseline_prediction_objects_byte_equal=True, baseline_ratio_json_byte_equal=True,
        baseline_model_params_json_byte_equal=True, actual_model_parameters=8782459120,
        frames_unique_and_sorted=True, UNKNOWN_or_DROP_new_frames=0, engineering_failure_to_UNKNOWN=False,
        source_field_callback_calls=len(added), scientific_quality_pass=False, GPU_admitted=False,
        submission_package_created=False, deliverable_claimed=False, model_calls=0, media_decodes=0)
    differences = dict(schema="RECALL_KEEP_DIFFERENCES_V1", added=added, removed=[], changed_baseline_boxes=[],
        candidate_diagnostics=diagnostics, baseline_frames=before_count, added_frames=len(added))
    return MergeResult(prediction_bytes, differences, gate)


def accepted_field_index(path, sources):
    rows = {}
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        require(bool(line.strip()), "Blank accepted source-field row")
        row = DECODER.decode(line)
        require(isinstance(row, dict) and row.get("status") == "ACCEPTED_SOURCE_FIELD_FRAME",
                "Every source-field row must be explicitly accepted")
        video_id, frame = stable_id(row.get("video_id")), row.get("frame")
        require(video_id in sources and type(frame) is int and 0 <= frame < sources[video_id]["source"]["n_frames"],
                "Unregistered source-field frame")
        key = video_id, frame
        require(key not in rows, "Duplicate accepted source-field frame")
        rows[key] = row
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("sources", "baseline", "candidates", "accepted-field", "predictions-output", "diff-output", "gate-output"):
        parser.add_argument("--" + name, required=True, type=Path)
    args = parser.parse_args()
    paths = (args.predictions_output, args.diff_output, args.gate_output)
    require(len({path.resolve() for path in paths}) == 3 and not any(path.exists() for path in paths),
            "Three distinct new output paths are required; no successful output may be overwritten")
    document = read_json_document(args.sources)
    field = accepted_field_index(args.accepted_field, validate_sources(document))
    def callback(video_id, frame):
        require((video_id, frame) in field, "Required new frame has no accepted source-field row")
        return field[video_id, frame]
    result = merge_verified_candidates(document, args.baseline.read_bytes(), read_json_document(args.candidates), callback)
    args.predictions_output.parent.mkdir(parents=True, exist_ok=True)
    with args.predictions_output.open("xb") as stream:
        stream.write(result.predictions_jsonl)
    write_json_document(args.diff_output, result.differences)
    write_json_document(args.gate_output, result.gate)
    print(json.dumps(result.gate, ensure_ascii=False))
    return 0 if result.gate["nonzero_prediction_difference"] else 5


if __name__ == "__main__":
    raise SystemExit(main())
