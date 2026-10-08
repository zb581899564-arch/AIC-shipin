"""CPU-only native source planning, before prediction-dependent selection.

The developer clip domains are the original permitted 104 records. Full-source
overview uses only their same SHA-bound source files. No teacher answer or
contest prediction determines the 24-source subset.
"""
import argparse
from collections import defaultdict
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import time
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import context_contract as cc
import runtime as rt


def source_clock(row, allowed_roots=None):
    import av
    path = Path(row["source_path"]).resolve(strict=True)
    roots = [Path(p).resolve(strict=True) for p in (allowed_roots or ["/home/inspur/aic_video_data/videos"])]
    cc.require(any(root in path.parents for root in roots), "unapproved source path")
    before = path.stat()
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            h.update(block)
    cc.require(h.hexdigest() == row["source_sha256"], "developer source bytes changed")
    pts, durations = [], []
    begun = time.monotonic()
    with av.open(str(path)) as container:
        cc.require(len(container.streams.video) == 1, "multiple video streams")
        stream = container.streams.video[0]
        cc.require(stream.average_rate is not None, "source rate missing")
        rate = stream.average_rate
        for frame in container.decode(stream):
            cc.require(frame.pts is not None and frame.time_base is not None, "decoded native PTS missing")
            pts.append(Fraction(frame.pts) * frame.time_base)
            durations.append(Fraction(frame.duration) * frame.time_base if frame.duration else None)
        width, height = stream.width, stream.height
    after = path.stat()
    cc.require(pts and all(b > a for a, b in zip(pts, pts[1:])), "nonmonotonic native PTS")
    cc.require(durations[-1] is not None and durations[-1] > 0, "physical last packet duration missing")
    endpoint = pts[-1] + durations[-1]
    cc.require((before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns), "source changed during scan")
    cc.require(len(pts) == row.get("decoded_source_frames", row.get("n_frames")), "full source frame count changed")
    cc.require((width, height) == (row["width"], row["height"]), "source geometry changed")
    value = dict(source_path=str(path), source_sha256=row["source_sha256"],
        pts=[float(x) for x in pts], pts_rational=[str(x) for x in pts],
        raw_origin_sec=float(pts[0]), raw_end_exclusive_sec=float(endpoint),
        physical_endpoint_rational=str(endpoint), duration_sec=float(endpoint - pts[0]),
        n_frames=len(pts), width=width, height=height, fps_num=rate.numerator, fps_den=rate.denominator,
        endpoint_kind="ACTUAL_LAST_DECODED_FRAME_PACKET_DURATION", sequential_scan_seconds=time.monotonic() - begun)
    return value


def stratified_subset(sources, grouped):
    # A source group can own several different SHA-bound 150s source files.
    # Group stratification uses the median file duration, not arbitrary union.
    import statistics
    ordered = sorted(grouped, key=lambda g: (statistics.median(
        sources[r["source_sha256"]]["duration_sec"] for r in grouped[g]), g))
    cc.require(len(ordered) == 96, "open source denominator changed")
    groups = [ordered[i * 24:(i + 1) * 24] for i in range(4)]
    selected = []
    for group in groups:
        selected += sorted(group, key=lambda k: hashlib.sha256(k.encode()).hexdigest())[:6]
    return selected


def prepare():
    student, old, frame_contract, production = rt.bind_helpers()
    out = HERE / "input_01"
    cc.require(not (out / "developer_plan.json").exists(),
        "developer planning already exists; do not reselect")
    out.mkdir(exist_ok=True)
    old_config = old.read(rt.RUN / "next_round_v1/config.json")
    developer = old.read(old_config["open_dev_contract"])
    records = developer["records"]
    cc.require(len(records) == 104 and len({r["youtube_id"] for r in records}) == 96, "developer104/96 denominator changed")
    cc.require(all(r["label_status"] == "WEAK_TEACHER" and
        r["annotation_source"] == "api_doubao_doubao-seed-2-1-pro-260628" for r in records), "weak reference authority changed")
    sources, grouped = {}, defaultdict(list)
    for r in records:
        key = r["source_sha256"]
        grouped[r["youtube_id"]].append(r)
        if key not in sources:
            cache = out / (key + ".clock.json")
            if cache.exists():
                # Exact CPU scan reuse after the recorded endpoint admission
                # failure. No source scan or model call is claimed anew.
                value = old.read(cache)
                cc.require(old.sha(r["source_path"]) == key and value["source_sha256"] == key and
                    value["source_path"] == r["source_path"] and value["n_frames"] == r["decoded_source_frames"] and
                    (value["width"], value["height"]) == (r["width"], r["height"]) and
                    len(value["pts"]) == len(value["pts_rational"]) == value["n_frames"] and
                    value["pts"] == [float(Fraction(p)) for p in value["pts_rational"]] and
                    value["endpoint_kind"] == "ACTUAL_LAST_DECODED_FRAME_PACKET_DURATION",
                    "original CPU source-clock receipt changed")
                sources[key] = value
            else:
                sources[key] = source_clock(r)
                rt.raw_write(cache, sources[key])
            print(json.dumps(dict(stage="NATIVE_DEVELOPER_SOURCE_SCAN", sources=len(sources), total=104)), flush=True)
    cc.require(len(sources) == 104 and len(grouped) == 96, "source file/group denominator changed")
    subset_groups = stratified_subset(sources, grouped)
    chosen = [min(grouped[g], key=lambda r: hashlib.sha256(r["video_id"].encode()).hexdigest()) for g in subset_groups]
    subset = [r["source_sha256"] for r in chosen]
    pilot_ids = [r["video_id"] for r in chosen]
    durations = {k: v["duration_sec"] for k, v in sources.items()}
    # The other 80 files belong to 72 untouched groups plus eight extra files.
    # Map each extra file to the SAME frozen donor group as its group's first
    # chosen file. Never feed another clip from the recipient's own group.
    group_duration = {g: min(durations[r["source_sha256"]] for r in grouped[g]) for g in grouped}
    other = sorted(set(grouped) - set(subset_groups))
    donor_groups = {**cc.deterministic_derangement(subset_groups, group_duration),
        **cc.deterministic_derangement(other, group_duration)}
    donor_file = {g: min(grouped[g], key=lambda r: hashlib.sha256(r["video_id"].encode()).hexdigest())["source_sha256"] for g in grouped}
    shuffle = {r["source_sha256"]: donor_file[donor_groups[r["youtube_id"]]] for r in records}
    jobs = []
    for r in records:
        clock = sources[r["source_sha256"]]
        start, end = float(r["clip_start_sec"]), float(r["clip_end_sec"])
        cc.require(0 <= start < end and start < clock["duration_sec"], "original clip has no physical source domain")
        nominal_endpoint = end > clock["duration_sec"]
        if nominal_endpoint:
            # This is the unchanged three-decimal annotation endpoint, not a
            # physical frame endpoint. Admit only this exact original record
            # and SHA; preserve 150.017 and never manufacture a tail frame.
            from decimal import Decimal, ROUND_HALF_UP
            cc.require(r["video_id"] == "qvh_000443_9x16" and
                r["source_sha256"] == "2dfa2f8d7edfe8bac502d7f5f2947ae12aca71844cdde4ffda4481d412fb09dd" and
                start == 137.017 and end == 150.017 and
                Decimal(str(clock["duration_sec"])).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP) == Decimal("150.017"),
                "unregistered annotation endpoint outside physical source clock")
        windows = []
        cursor = start
        while cursor < end:
            stop = min(cursor + 30.0, end)
            origin = clock["raw_origin_sec"]
            w = student.window_from_pts(clock["source_path"], clock["source_sha256"], clock["pts"],
                origin + cursor, origin + stop, r["video_id"] + ":CAD:" + str(len(windows)),
                width=clock["width"], height=clock["height"])
            w["window_duration_sec"] = stop - cursor
            windows.append({"start_sec": cursor, "end_sec": stop, "window": w})
            cursor = stop
        jobs.append(dict(video_id=r["video_id"], source_key=r["source_sha256"], source_group=r["youtube_id"],
            clip_start_sec=start, clip_end_sec=end, windows=windows, weak_reference=r["segments_clip_local"],
            annotation_endpoint_rounding_record=nominal_endpoint,
            physical_source_endpoint_sec=clock["duration_sec"],
            reference_role="FIXED_EXTERNAL_DOUBAO_WEAK_REFERENCE_NOT_HUMAN_TRUTH"))
    # Source exposure is reported, never used to silently remove hard cases.
    prior = old.rows(rt.RUN / "teacher_student_autopilot_v14/teacher_01/validated/validated_records.jsonl")
    cc.require(len(prior) == 160, "prior source exposure denominator missing")
    prior_sha = {x["window"]["source_sha256"] for x in prior}
    plan = dict(schema="aic_c_advisory_input_v1", developer_jobs=jobs,
        source_clocks={k: str(out / (k + ".clock.json")) for k in sources},
        source_files=104, source_groups=96, records=104, pilot_sources=subset, pilot_source_groups=subset_groups,
        pilot_video_ids=pilot_ids, full_source_observation_authority="USER_AUTHORIZED_OPEN_NONTEST_FILES_EXACT_SOURCE_SHA",
        overview_sharing_between_distinct_files=False,
        pilot_rule="SOURCE_DURATION_RANK_QUARTILES_6_SHA_ORDERED_EACH_ONE_ORIGINAL_CLIP_PER_SOURCE",
        original_clip_domain_not_full_video_metric=True, shuffle_source_mapping=shuffle,
        prior_teacher_source_intersection=sorted(set(sources) & prior_sha),
        source_exposure_check_available=bool(prior), developer_contract_sha256=old.sha(old_config["open_dev_contract"]),
        confirm_read=False, test_predictions_read=False, selector_model_calls=0)
    rt.raw_write(out / "developer_plan.json", plan)
    rt.raw_write(out / "prepared.json", dict(status="PASS_NATIVE_SOURCE_PLANNING_NO_MODEL_CALLS",
        source_files=104, source_groups=96, records=104, pilot_sources=24, plan_sha256=old.sha(out / "developer_plan.json")))


if __name__ == "__main__":
    prepare()
