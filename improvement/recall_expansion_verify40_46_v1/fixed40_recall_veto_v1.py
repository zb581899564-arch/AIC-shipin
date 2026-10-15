"""Consume future accepted execution evidence; only veto frozen observed facts.

No launch, download, decode, processor, tensor load, model, or replay is provided.
CLI execution is restricted to the existing Linux host. All refs are explicit
{path, sha256} JSON artifacts; original labels and source-export bytes are pinned.

Registration contract (FIXED40_RECALL_FACT_REGISTRATION_V1): status must be
REGISTERED_FIXED40_AFTER_DEV_CONFIRM_PASS; protocol_ref, dev_result_ref,
confirm_result_ref, reference_ref, source_export_ref and checker_ref are required.
The dev/confirm result statuses and their protocol hashes are checked first.

Evidence contract (FIXED40_RECALL_EVIDENCE_V1): registration_sha256;
geometry_scope=FULL_ORIGINAL_SOURCE_ZERO_ORIGIN_15_STRIDE7_5;
execution_receipt_ref; first_independent_qa_ref; and the nine frozen sources
with explicit ORDINARY points. registered_views must enumerate exactly the
complete-source grid windows capable of containing any of those 222 points;
the unrelated full-source windows need no calls for this limited veto.
Execution receipt status is PASS_FIXED40_ACTUAL_EXECUTION_NOT_FACT_QUALITY,
with all_registered_views_completed=true, failed_views=0, registered_view_count
equal to completed_view_count, and keep_event_ids_by_case enumerating *every*
actual KEEP from those views. QA status is PASS_FIXED40_FIRST_QA_NOT_FACT_QUALITY and binds the
execution receipt hash, has complete_view_and_decision_denominators=true,
CPU_only=true, CUDA_initialized=false. These are upstream acceptance receipts,
not receipts this module creates or a substitute for the runtime's own QA.

Each source supplies frozen case/video/source_group/source_key/clock_sha256,
clock_ref (the original complete clock with its previously measured physical
endpoint), and new_keep_events. A real baseline_verify_receipt_ref is optional.
The baseline receipt status is PASS_ACTUAL_VERIFY40_46_SELECTION_AND_FIRST_QA,
binds the same source/clock, baseline=TEMPORAL_VERIFY_USER40.46, intervals_exact,
actual_execution_receipt_ref and first_independent_qa_ref. It must certify
actual_calls_or_exact_identity_adoption=true and baseline_reconstructed_from_
real_VERIFY_decisions=true. This adapter must be produced from real accepted
baseline outputs; old D8 spans cannot be relabelled into this schema.

Every new_keep_event supplies event_id, view_id, start_exact, end_exact and bound
input_ref, request_ref, raw_ref, done_ref, replay_ref, resource_terminal_ref.
The real current VERIFY raw/done/first-replay schemas are checked, including
source/event/interval identity and raw/request/done hashes. A claimed interval
or baseline-retention flag alone never passes. A genuinely empty complete KEEP
denominator needs the upstream execution+QA receipts; a missing list rejects.

If the complete new KEEP set is disjoint from all explicit ORDINARY points,
then for any true baseline B, ((B union KEEP) minus B) intersects ORDINARY is
empty. This is a sufficient condition for the unchanged difference gate, not
a stricter replacement threshold. If KEEP touches ORDINARY and a real VERIFY
baseline is unavailable, return INCONCLUSIVE_NEEDS_REAL_VERIFY_BASELINE.
KEEP deletion additionally needs an actual baseline_retention_proof_ref:
PASS_ACTUAL_BASELINE_FRAMES_BOXES_RETENTION with source/count-complete=true,
all_original_frames_and_boxes_preserved=true, execution_receipt_sha256 bound,
new_selection_equals_baseline_union_explicit_KEEP=true, no UNKNOWN/DROP
additions, and a passed independent_qa_ref. Until then, sufficient ordinary protection
only returns SUFFICIENT_PASS_PENDING_BASELINE_RETENTION_PROOF, not final PASS.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import re
import socket


REFERENCE_SHA = "37a7c93876334b3a5d0c222e3a7f99727778d50f28f3a1172e860d19d3dc82b8"
EXPORT_SHA = "7feb4cbec6567612e99a98bca708deb5041e38cd0735500a1016263fb43cc8d6"
GEOMETRY = "FULL_ORIGINAL_SOURCE_ZERO_ORIGIN_15_STRIDE7_5"
EXPECTED_COVERAGE = dict(sources=40, keep_sources=6, ordinary_sources=9,
                         two_ended_dense_events=1, KEEP=184, ORDINARY=222, UNKNOWN=2675)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def unique_object(pairs):
    value = {}
    for key, item in pairs:
        require(key not in value, "Duplicate JSON key: " + key)
        value[key] = item
    return value


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"), object_pairs_hook=unique_object,
                      parse_constant=lambda value: (_ for _ in ()).throw(ValueError("Nonfinite JSON: " + value)))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def bound(ref):
    require(isinstance(ref, dict) and set(ref) == {"path", "sha256"}, "Explicit path/SHA JSON reference required")
    path = Path(ref["path"])
    require(path.is_absolute() and path.suffix == ".json" and path.is_file(), "Existing absolute JSON artifact required")
    require(isinstance(ref["sha256"], str) and re.fullmatch(r"[0-9a-f]{64}", ref["sha256"]), "Invalid SHA binding")
    require(sha(path) == ref["sha256"], "Frozen JSON artifact changed: " + str(path))
    return read(path)


def exact(value):
    require(type(value) in (str, int), "Exact seconds must be a string/non-bool integer")
    return F(value)


def merged(spans, end):
    require(isinstance(spans, list), "Complete explicit interval list required")
    result = []
    for interval in spans:
        require(isinstance(interval, list) and len(interval) == 2, "Exact [start,end] interval required")
        first, last = map(exact, interval)
        require(0 <= first < last <= end, "Interval outside the accepted complete source")
        result.append((first, last))
    out = []
    for first, last in sorted(result):
        if out and first <= out[-1][1]:
            out[-1] = (out[-1][0], max(last, out[-1][1]))
        else:
            out.append((first, last))
    return out


def includes(spans, point):
    return any(first <= point < last for first, last in spans)


def point_covering_windows(end, ordinary):
    """The original zero-origin source grid, filtered only for observed veto points."""
    if end <= 15:
        windows = {(F(0), end)}
    else:
        windows, cursor = set(), F(0)
        while cursor + 15 <= end:
            windows.add((cursor, cursor + 15))
            cursor += F(15, 2)
        windows.add((end - 15, end))
    return {window for window in windows if any(window[0] <= t < window[1] for t in ordinary)}


def identity(document, source):
    for key in ("case_id", "video_id", "source_group", "source_key", "clock_sha256"):
        require(document.get(key) == source[key], "Frozen source identity differs: " + key)


def first_qa(document, receipt_ref):
    require(document.get("CPU_only") is True and document.get("CUDA_initialized") is False,
            "Accepted independent CPU QA receipt required")
    require(document.get("actual_execution_receipt_sha256") == receipt_ref["sha256"],
            "Independent QA is not bound to the actual execution receipt")
    require(document.get("complete_view_and_decision_denominators") is True,
            "Incomplete view or semantic-decision denominator")


def baseline_spans(source, evidence, physical_end):
    document = bound(evidence["baseline_verify_receipt_ref"])
    require(document.get("status") == "PASS_ACTUAL_VERIFY40_46_SELECTION_AND_FIRST_QA",
            "Old B/D8 or proposed baseline cannot replace real VERIFY baseline acceptance")
    identity(document, source)
    require(document.get("baseline") == "TEMPORAL_VERIFY_USER40.46" and
            document.get("actual_calls_or_exact_identity_adoption") is True and
            document.get("baseline_reconstructed_from_real_VERIFY_decisions") is True,
            "Actual unchanged baseline VERIFY/identity adoption evidence is missing")
    execution_ref = document["actual_execution_receipt_ref"]
    execution = bound(execution_ref)
    require(execution.get("status") == "PASS_BASELINE_VERIFY_ACTUAL_EXECUTION_NOT_FACT_QUALITY" and
            execution.get("all_registered_views_completed") is True and execution.get("failed_views") == 0,
            "Complete actual baseline execution is required")
    qa = bound(document["first_independent_qa_ref"])
    require(qa.get("status") == "PASS_BASELINE_VERIFY_FIRST_QA_NOT_FACT_QUALITY", "Baseline first QA missing")
    first_qa(qa, execution_ref)
    return merged(document["intervals_exact"], physical_end)


def keep_span(source, event, physical_end, points, terminal_hashes, views):
    require(isinstance(event.get("event_id"), str) and event["event_id"], "Explicit unique KEEP event ID required")
    pair = [event["start_exact"], event["end_exact"]]
    span = merged([pair], physical_end)[0]
    view_id = event["view_id"]
    require(view_id in views and views[view_id][0] <= span[0] < span[1] <= views[view_id][1],
            "New KEEP must remain inside its actual accepted point-covering original-source view")
    meta, request, raw, done, replay, resource = [bound(event[name]) for name in
        ("input_ref", "request_ref", "raw_ref", "done_ref", "replay_ref", "resource_terminal_ref")]
    require(meta.get("source_name") == source["video_id"] and meta.get("source_sha256") == source["source_key"] and
            meta.get("event_id") == event["event_id"] and meta.get("reference_labels_read") is False and
            meta.get("original_case_id") == view_id,
            "Actual KEEP input source/event/reference isolation differs")
    require(request.get("input_path") == event["input_ref"]["path"] and
            request.get("input_sha256") == event["input_ref"]["sha256"] and
            request.get("event_id") == event["event_id"] and request.get("reference_labels_read") is False and
            request.get("original_case_id") == view_id,
            "Actual KEEP request/input binding differs")
    require(list(map(exact, meta["original_interval_exact"])) == list(span) and
            list(map(exact, request["original_interval_exact"])) == list(span),
            "New KEEP endpoints were modified after their real input/request")
    require("overlap" in meta.get("view_roles", []) and "overlap" in request.get("view_roles", []),
            "New contribution must originate in an accepted overlap view")
    require(raw.get("actual_model_call") is True and type(raw.get("output_tokens")) is int and raw["output_tokens"] > 0 and
            len(raw.get("output_token_ids", [])) == raw["output_tokens"], "Real untouched VERIFY model output missing")
    require(meta.get("input_evidence") and meta["input_evidence"] == request.get("input_evidence") ==
            raw.get("input_evidence") == done.get("input_evidence"), "Actual KEEP prompt/tensor evidence differs")
    require(done.get("status") == "PASS_RECALL_VERIFY_DECISION_NOT_QUALITY" and
            done.get("event_id") == event["event_id"] and done.get("raw_sha256") == event["raw_ref"]["sha256"] and
            done.get("request_sha256") == event["request_ref"]["sha256"], "Actual successful VERIFY done/raw binding missing")
    decision = done["decision_result"]
    require(decision.get("decision") == "KEEP" and decision.get("successful_model_call_required") is True and
            list(map(exact, decision["original_interval_exact"])) == list(span), "Explicit accepted unchanged KEEP required")
    require(replay.get("status") == "PASS_INDEPENDENT_RECALL_VERIFY_TOKEN_RAW_GRAMMAR_NATIVE_REPLAY" and
            replay.get("CPU_only") is True and replay.get("event_id") == event["event_id"] and
            replay.get("raw_sha256") == event["raw_ref"]["sha256"] and
            replay.get("done_sha256") == event["done_ref"]["sha256"] and replay.get("decision_result") == decision,
            "First independent actual KEEP raw/grammar/native replay is missing")
    members = [ordinal for ordinal, point in enumerate(points) if span[0] <= point < span[1]]
    require(members and replay.get("original_native_range") == [members[0], members[-1] + 1],
            "Exact original clock membership differs from first actual KEEP replay")
    require(event["resource_terminal_ref"]["sha256"] in terminal_hashes and
            resource.get("status") == "completed" and resource.get("exit_code") == 0,
            "Natural completed shared-model resource receipt required")
    return span


def evaluate(registration_path, evidence_path):
    registration, evidence = read(registration_path), read(evidence_path)
    require(registration.get("schema") == "FIXED40_RECALL_FACT_REGISTRATION_V1" and
            registration.get("status") == "REGISTERED_FIXED40_AFTER_DEV_CONFIRM_PASS", "New fixed40 registration missing")
    checker_ref = registration["checker_ref"]
    require(Path(checker_ref["path"]).resolve() == Path(__file__).resolve() and checker_ref["sha256"] == sha(__file__),
            "The actual independent veto implementation must be frozen before its evidence is evaluated")
    protocol = bound(registration["protocol_ref"])
    require(protocol.get("baseline") == "TEMPORAL_VERIFY_USER40.46", "Frozen VERIFY40.46 protocol required")
    require(protocol["quality_gates"]["fixed_40_KEEP_deletion"] == 0 and
            protocol["quality_gates"]["fixed_40_ORDINARY_addition"] == 0 and
            protocol["quality_gates"]["UNKNOWN_old_coverage_failed_unchanged"] is True, "Original fact gates changed")
    for group in ("dev", "confirm"):
        result = bound(registration[group + "_result_ref"])
        require(result.get("status") == "PASS_REGISTERED_PROXY_GROUP_PENDING_FIXED_FACT_GATE" and
                result.get("group") == group and result["bindings"]["protocol_sha256"] == registration["protocol_ref"]["sha256"] and
                result.get("conditions") and all(value is True for value in result["conditions"].values()),
                "Both complete frozen proxy groups must pass before fixed40 evaluation")
    require(registration["reference_ref"]["sha256"] == REFERENCE_SHA and
            registration["source_export_ref"]["sha256"] == EXPORT_SHA, "Original silver/source artifacts were replaced")
    reference, exported = bound(registration["reference_ref"]), bound(registration["source_export_ref"])
    require(reference.get("reference_level") == "AI_REVIEWED_SILVER_NOT_HUMAN_GOLD" and
            reference.get("coverage") == EXPECTED_COVERAGE and reference.get("coverage_pass") is False and
            reference.get("reference_quality_pass") is False, "Original failed silver reference gate must stay failed")
    require(evidence.get("schema") == "FIXED40_RECALL_EVIDENCE_V1" and
            evidence.get("registration_sha256") == sha(registration_path) and evidence.get("geometry_scope") == GEOMETRY,
            "Complete original-source geometry evidence required; clipped surrogate grid is not production geometry")
    execution_ref = evidence["execution_receipt_ref"]
    execution, qa = bound(execution_ref), bound(evidence["first_independent_qa_ref"])
    require(execution.get("status") == "PASS_FIXED40_ACTUAL_EXECUTION_NOT_FACT_QUALITY" and
            execution.get("registration_sha256") == sha(registration_path) and execution.get("geometry_scope") == GEOMETRY and
            execution.get("all_registered_views_completed") is True and type(execution.get("registered_view_count")) is int and
            execution["registered_view_count"] > 0 and execution.get("completed_view_count") == execution["registered_view_count"] and
            execution.get("failed_views") == 0, "Complete actual registered view execution is missing")
    require(execution.get("model_parameters") == protocol["model_parameters"] and
            execution.get("new_optimizer_updates") == 0, "Actual fixed40 model/optimizer identity differs")
    terminal_refs = execution["resource_terminal_refs"]
    require(isinstance(terminal_refs, list) and terminal_refs, "Actual completed resource terminal bindings required")
    terminal_hashes = set()
    for terminal_ref in terminal_refs:
        terminal = bound(terminal_ref)
        require(terminal.get("status") == "completed" and terminal.get("exit_code") == 0 and
                terminal_ref["sha256"] not in terminal_hashes, "Resource failure, duplicate or missing natural terminal")
        terminal_hashes.add(terminal_ref["sha256"])
    require(qa.get("status") == "PASS_FIXED40_FIRST_QA_NOT_FACT_QUALITY", "First independent full execution QA missing")
    first_qa(qa, execution_ref)
    expected = execution["keep_event_ids_by_case"]
    sources = evidence["sources"]
    fact_sources = [row for row in reference["rows"] if any(p["label"] == "ORDINARY" for p in row["points"])]
    require(isinstance(sources, list) and len(sources) == len(fact_sources) == 9,
            "All nine original explicit-ORDINARY sources required")
    by_case = {row["case_id"]: row for row in sources}
    require(len(by_case) == 9 and set(by_case) == set(expected) == {row["case_id"] for row in fact_sources},
            "Complete observed-ORDINARY source/KEEP execution denominator differs")
    registered_views = execution["registered_views"]
    require(isinstance(registered_views, list) and len(registered_views) == execution["registered_view_count"],
            "Actual registered point-covering view manifest missing")
    views_by_case, view_ids = {name: {} for name in by_case}, set()
    for view in registered_views:
        name, view_id = view["case_id"], view["view_id"]
        require(name in views_by_case and isinstance(view_id, str) and view_id and view_id not in view_ids,
                "Unexpected, duplicate or missing actual point-covering view identity")
        view_ids.add(view_id)
        views_by_case[name][view_id] = (exact(view["start_exact"]), exact(view["end_exact"]))
    entries = {row["video_id"]: row for row in exported["entries"]}
    checks, all_event_ids, all_ordinary_disjoint, needs_baseline, ordinary_added_count = [], set(), True, False, 0
    for source in fact_sources:
        current = by_case[source["case_id"]]
        identity(current, source)
        entry = entries[source["video_id"]]
        for key in ("source_group", "source_key", "clock_sha256"):
            require(entry[key] == source[key], "Frozen original source-export binding changed")
        require(current["clock_ref"]["sha256"] == source["clock_sha256"], "Original complete clock SHA differs")
        clock = bound(current["clock_ref"])
        points = list(map(exact, clock.get("exact_pts", clock.get("pts_rational", []))))
        require(points and points == list(map(exact, entry["native_clock"]["exact_pts"])) and
                all(a < b for a, b in zip(points, points[1:])), "Original complete native clock differs")
        require(clock.get("source_sha256") == source["source_key"] and
                clock.get("endpoint_kind") == "ACTUAL_LAST_DECODED_FRAME_PACKET_DURATION",
                "Previously measured original complete source end required; no new measure or guessed end")
        end = exact(clock["physical_endpoint_rational"])
        require(points[0] == 0 and end > points[-1], "Full zero-origin physical source domain required")
        ordinary_points = set()
        for point in source["points"]:
            label, ordinal, time = point["label"], point["ordinal"], exact(point["exact_pts"])
            require(label in ("KEEP", "ORDINARY", "UNKNOWN") and type(ordinal) is int and
                    0 <= ordinal < len(points) and points[ordinal] == time,
                    "Original observed label/ordinal/PTS differs")
            if label == "ORDINARY":
                ordinary_points.add(time)
        views = views_by_case[source["case_id"]]
        require(len(set(views.values())) == len(views) and set(views.values()) == point_covering_windows(end, ordinary_points),
                "An original-source grid view capable of touching an explicit ORDINARY point was omitted/changed")
        events = current["new_keep_events"]
        require(isinstance(events, list) and isinstance(expected[source["case_id"]], list), "Explicit complete KEEP event lists required")
        event_ids = [event["event_id"] for event in events]
        require(len(set(event_ids)) == len(event_ids) and len(set(expected[source["case_id"]])) == len(expected[source["case_id"]]) and
                set(event_ids) == set(expected[source["case_id"]]) and not all_event_ids.intersection(event_ids),
                "Missing, duplicate, or unexecuted new KEEP evidence")
        all_event_ids.update(event_ids)
        added = [keep_span(source, event, end, points, terminal_hashes, views) for event in events]
        touched = {time for time in ordinary_points if includes(added, time)}
        ordinary, mode = set(), "SUFFICIENT_NEW_KEEP_DISJOINT_FROM_ALL_EXPLICIT_ORDINARY"
        if touched:
            all_ordinary_disjoint = False
            if "baseline_verify_receipt_ref" in current:
                baseline = baseline_spans(source, current, end)
                ordinary = {time for time in touched if not includes(baseline, time)}
                ordinary_added_count += len(ordinary)
                mode = "REAL_VERIFY_BASELINE_OBSERVED_DIFFERENCE"
            else:
                needs_baseline = True
                ordinary, mode = None, "INCONCLUSIVE_NEEDS_REAL_VERIFY_BASELINE"
        checks.append(dict(case_id=source["case_id"], video_id=source["video_id"], source_group=source["source_group"],
                           actual_new_KEEP_events=len(events), observed_ordinary_points=len(ordinary_points),
                           new_KEEP_touches_ordinary=[str(time) for time in sorted(touched)],
                           ordinary_added=None if ordinary is None else [str(time) for time in sorted(ordinary)],
                           ordinary_proof_mode=mode, known_ordinary_protection=None if ordinary is None else not ordinary))
    retention_pass = False
    if "baseline_retention_proof_ref" in evidence:
        retention_ref = evidence["baseline_retention_proof_ref"]
        retention = bound(retention_ref)
        require(retention.get("status") == "PASS_ACTUAL_BASELINE_FRAMES_BOXES_RETENTION" and
                retention.get("execution_receipt_sha256") == execution_ref["sha256"] and
                retention.get("protocol_sha256") == registration["protocol_ref"]["sha256"] and
                retention.get("all_original_frames_and_boxes_preserved") is True and
                retention.get("source_and_frame_denominators_complete") is True and
                retention.get("new_selection_equals_baseline_union_explicit_KEEP") is True and
                retention.get("UNKNOWN_or_DROP_additions") == 0 and
                retention.get("all_added_frames_have_executed_KEEP_provenance") is True,
                "Actual complete baseline frame/box retention proof required; a KEEP-only flag is insufficient")
        retention_qa = bound(retention["independent_qa_ref"])
        require(retention_qa.get("status") == "PASS_INDEPENDENT_ACTUAL_BASELINE_RETENTION" and
                retention_qa.get("retention_receipt_sha256") == retention_ref["sha256"] and
                retention_qa.get("CPU_only") is True, "Independent actual baseline retention QA missing")
        retention_pass = True
    if ordinary_added_count:
        status = "REJECT_FIXED40_OBSERVED_FACT_VETO"
    elif needs_baseline:
        status = "INCONCLUSIVE_NEEDS_REAL_VERIFY_BASELINE"
    elif retention_pass:
        status = "PASS_FIXED40_OBSERVED_FACT_VETO_NOT_QUALITY"
    elif all_ordinary_disjoint:
        status = "SUFFICIENT_PASS_PENDING_BASELINE_RETENTION_PROOF"
    else:
        status = "FACT_VETO_PENDING_BASELINE_RETENTION_PROOF"
    passed = status == "PASS_FIXED40_OBSERVED_FACT_VETO_NOT_QUALITY"
    return dict(schema="FIXED40_RECALL_FACT_VETO_RESULT_V1",
                status=status,
                passed=passed, utc=datetime.now(timezone.utc).isoformat(), checks=checks,
                unchanged_original_source_denominator=40, point_covering_source_count=9,
                complete_point_covering_original_source_views=len(registered_views),
                ordinary_disjoint_sufficient_proof=all_ordinary_disjoint,
                baseline_frame_and_box_retention_proven=retention_pass,
                real_VERIFY_baseline_needed=needs_baseline,
                actual_new_KEEP_events=len(all_event_ids), complete_execution_with_zero_KEEP=not all_event_ids,
                old_reference_quality_failed_preserved=True, old_coverage_failed_preserved=True,
                reference_level="AI_REVIEWED_SILVER_NOT_HUMAN_GOLD", UNKNOWN_not_relabelled=True,
                original_ORDINARY_observation_points_checked=222, original_KEEP_observation_points_preserved_by_retention_proof=184 if retention_pass else None,
                new_model_calls=0, media_decodes=0, processor_calls=0, replay_calls=0,
                scientific_quality_pass=False, official_score="UNKNOWN", production_admitted=False,
                bindings=dict(registration_sha256=sha(registration_path), evidence_sha256=sha(evidence_path),
                              original_reference_sha256=REFERENCE_SHA, original_source_export_sha256=EXPORT_SHA,
                              checker_sha256=sha(__file__)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registration", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    require(socket.gethostname() == "inspur-NP5570M5" and Path("/home/inspur/aic_video_work").is_dir(),
            "Actual scientific evaluation stays on the existing Linux host")
    require(not args.output.exists(), "Never overwrite or rerun a successful fixed40 output")
    result = evaluate(args.registration, args.evidence)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps(dict(status=result["status"], sources=len(result["checks"]),
                         ordinary_added=sum(len(row["ordinary_added"] or []) for row in result["checks"]),
                         actual_new_KEEP_events=result["actual_new_KEEP_events"], new_model_calls=0)))
    return 0 if result["passed"] else 5


if __name__ == "__main__":
    raise SystemExit(main())
