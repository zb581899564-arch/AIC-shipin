#!/usr/bin/env python3
"""Independent actual CPU marker-video test. No model/GPU/contest input.

All fixture media, raw pixels, logs, metadata and receipts stay under a new
explicit output root. Fixture clocks are constructed ONLY from actual
ffprobe native integer/packet metadata and full Decord timestamp agreement.
"""
from __future__ import annotations

import argparse
import copy
from fractions import Fraction
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
FRAME_COUNT, WIDTH, HEIGHT, INPUT_FPS = 80, 96, 64, 10


def require(ok, message):
    if not ok:
        raise AssertionError(message)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def pixel_sha(array):
    return hashlib.sha256(memoryview(array).cast("B")).hexdigest()


def write_json(path, value):
    with Path(path).open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")


def checkpoint(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def marker_rgb(index, np):
    y, x = np.indices((HEIGHT, WIDTH), dtype=np.int32)
    frame = np.stack(((3 * index + 2 * x + 5 * y) % 256,
                      (7 * index + x + 3 * y) % 256,
                      (11 * index + x + 2 * y) % 256), axis=-1).astype(np.uint8)
    frame[:8, :, :] = [index, 255 - index, index ^ 0x5A]
    return np.ascontiguousarray(frame)


def run_command(argv, root, name):
    process = subprocess.run(argv, cwd=root, stdin=subprocess.DEVNULL, capture_output=True,
                             text=True, timeout=180, check=False)
    (root / (name + ".stdout.txt")).write_text(process.stdout, encoding="utf-8")
    (root / (name + ".stderr.txt")).write_text(process.stderr, encoding="utf-8")
    write_json(root / (name + ".command.json"), {"argv": argv, "returncode": process.returncode})
    require(process.returncode == 0, name + " failed; retained argv/stdout/stderr")
    return process.stdout


def verify_lock():
    lock_path = HERE / "source_lock.json"
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    require(lock.get("schema") == "aic_a_native_pts_source_lock_v1", "production source lock schema changed")
    files = {r["path"]: r["sha256"] for r in lock.get("files", [])}
    require({"native_frames.py", "pts_contract.py", "detect_shots_pts.py", "infer_anchors_pts.py"} <= set(files),
            "production source lock incomplete")
    for name, digest in files.items():
        require(sha(HERE / name) == digest, "production source lock mismatch: " + name)
    vendor = HERE / "vendor/detect_shots_sequential.py"
    vendor_lock = json.loads((HERE / "vendor_lock.json").read_text(encoding="utf-8"))
    entries = vendor_lock.get("files", [])
    matches = [r for r in entries if r.get("path") in ("detect_shots_sequential.py", "vendor/detect_shots_sequential.py")]
    require(len(matches) == 1 and matches[0].get("sha256") == sha(vendor), "frozen shot descriptor vendor hash mismatch")
    return {"source_lock_sha256": sha(lock_path), "source_lock_revision": lock.get("revision"),
            "production_files": files, "frozen_descriptor_sha256": sha(vendor), "test_sha256": sha(__file__)}


def make_source(root, ffmpeg, name, nonzero_gap, np):
    case_root = root / name
    case_root.mkdir()
    raw = case_root / "source_rgb24.raw"
    expected = []
    with raw.open("xb") as handle:
        for index in range(FRAME_COUNT):
            rgb = marker_rgb(index, np)
            handle.write(memoryview(rgb).cast("B"))
            expected.append({"source_frame": index, "marker_rgb": [index, 255 - index, index ^ 0x5A],
                "rgb_sha256": pixel_sha(rgb), "bgr_sha256": pixel_sha(rgb[:, :, ::-1].copy())})
    require(len({r["rgb_sha256"] for r in expected}) == FRAME_COUNT, "synthetic frames are not individually distinguishable")
    write_json(case_root / "expected_markers.json", {"shape": [HEIGHT, WIDTH, 3], "frames": expected})
    source = case_root / "marker_lossless_rgb.mp4"
    expression = "PTS+gte(N\\,40)*0.6/TB+2/TB" if nonzero_gap else "PTS"
    argv = [ffmpeg, "-nostdin", "-hide_banner", "-loglevel", "error", "-n", "-f", "rawvideo",
        "-pixel_format", "rgb24", "-video_size", f"{WIDTH}x{HEIGHT}", "-framerate", str(INPUT_FPS),
        "-i", str(raw), "-vf", "setpts=" + expression, "-vsync", "0", "-an", "-c:v", "libx264rgb",
        "-crf", "0", "-preset", "ultrafast", "-bf", "0", "-pix_fmt", "rgb24", str(source)]
    run_command(argv, case_root, "ffmpeg_generate")
    return case_root, source, expected


def construct_actual_clock(case_root, source, ffprobe, np, decord):
    argv = [ffprobe, "-v", "error", "-select_streams", "v:0", "-show_streams", "-show_frames", "-show_entries",
        "stream=width,height,avg_frame_rate,r_frame_rate,time_base,start_pts,start_time,duration_ts,duration,nb_frames:"
        "frame=best_effort_timestamp,best_effort_timestamp_time,pkt_duration,pkt_duration_time", "-of", "json", str(source)]
    text = run_command(argv, case_root, "ffprobe_native")
    (case_root / "raw_ffprobe.json").write_text(text, encoding="utf-8")
    data = json.loads(text)
    require(len(data.get("streams", [])) == 1 and len(data.get("frames", [])) == FRAME_COUNT,
            "actual generated stream/frame count changed")
    stream, frames = data["streams"][0], data["frames"]
    tick, fps = Fraction(stream["time_base"]), Fraction(stream["avg_frame_rate"])
    require(tick > 0 and fps > 0 and (stream["width"], stream["height"]) == (WIDTH, HEIGHT), "actual generated geometry/timebase changed")
    ticks, ends, durations = [], [], []
    for frame in frames:
        p, duration = frame.get("best_effort_timestamp"), frame.get("pkt_duration")
        require(type(p) is int and type(duration) is int and duration > 0, "actual native integer PTS/packet duration missing")
        require(abs(float(Fraction(frame["best_effort_timestamp_time"]) - p * tick)) <= 1e-6 + 1e-12,
                "actual native integer/textual PTS differs")
        ticks.append(p); durations.append(duration); ends.append(p + duration)
    require(all(b > a for a, b in zip(ticks, ticks[1:])) and all(b > a for a, b in zip(ends, ends[1:])),
            "actual native starts/ends not strictly monotonic")
    require(type(stream.get("start_pts")) is int and stream["start_pts"] == ticks[0]
            and abs(float(Fraction(stream["start_time"]) - ticks[0] * tick)) <= 1e-6 + 1e-12,
            "actual stream start does not bind first native frame")
    numeric_reader = decord.VideoReader(str(source), ctx=decord.cpu(0))
    require(len(numeric_reader) == FRAME_COUNT, "actual decoder frame count differs")
    timestamps = numeric_reader.get_frame_timestamp(list(range(FRAME_COUNT)))
    timestamps = np.asarray(timestamps.asnumpy() if hasattr(timestamps, "asnumpy") else timestamps)
    require(timestamps.shape == (FRAME_COUNT, 2) and timestamps.dtype == np.float32 and np.isfinite(timestamps).all(),
            "actual decoder timestamps are not known float32")
    candidates = {}
    for mode, shift in (("RAW_CONTAINER_PTS", 0), ("SOURCE_RELATIVE_PTS", ticks[0])):
        exact = [(Fraction(p - shift) * tick, Fraction(e - shift) * tick) for p, e in zip(ticks, ends)]
        represented = np.asarray([[float(a), float(b)] for a, b in exact], dtype=np.float32)
        if np.array_equal(timestamps, represented):
            for column in (0, 1):
                minimum_gap = min(b[column] - a[column] for a, b in zip(exact, exact[1:]))
                require(np.all(represented[1:, column] > represented[:-1, column]), "neighboring generated frame timestamps alias in float32")
                require(all(abs(Fraction.from_float(float(timestamps[i, column])) - pair[column]) < minimum_gap / 2
                            for i, pair in enumerate(exact)), "actual float32 error does not resolve half-frame identity")
            candidates[mode] = represented.tolist()
    require(candidates, "actual native integers/packet ends do not bind all decoder timestamps")
    require(len(candidates) == 1 or ticks[0] == 0, "generated nonzero origin is ambiguous")
    mode = "RAW_AND_RELATIVE_EQUIVALENT_ZERO_ORIGIN" if len(candidates) == 2 else next(iter(candidates))
    require(abs(float(numeric_reader.get_avg_fps()) - float(fps)) <= max(1e-6, float(fps) * 1e-6), "actual decoder average-FPS metadata differs")
    source_digest = sha(source)
    relative = [(p - ticks[0]) * tick for p in ticks]
    terminal = (ends[-1] - ticks[0]) * tick
    arrays = {"schema": "aic_source_clock_arrays_v1", "video_id": case_root.name, "source_sha256": source_digest,
        "n_frames": FRAME_COUNT, "raw_time_base": str(tick), "raw_first_pts_ticks": ticks[0], "native_pts_ticks": ticks,
        "native_frame_end_pts_ticks": ends, "source_relative_pts": [float(p) for p in relative],
        "source_relative_pts_rational": [str(p) for p in relative], "native_packet_duration_ticks": durations,
        "integer_evidence_kind": "ACTUAL_SYNTHETIC_FFPROBE_NATIVE_INTEGERS"}
    array_path = case_root / "actual_clock_arrays.json"
    write_json(array_path, arrays)
    write_json(case_root / "actual_decoder_numeric.json", {"decord_timestamps": timestamps.tolist(), "dtype": str(timestamps.dtype),
        "decord_frame_count": len(numeric_reader), "decord_average_fps": float(numeric_reader.get_avg_fps()),
        "mode": mode, "all_native_starts_and_packet_ends_exact_float32": True})
    row = {"video_id": case_root.name, "source_path": str(source), "source_sha256": source_digest,
        "n_frames": FRAME_COUNT, "fps_num": fps.numerator, "fps_den": fps.denominator, "width": WIDTH, "height": HEIGHT,
        "targetRatioWH": [16, 9], "scope_start_sec": 0.0, "scope_end_sec": float(terminal)}
    clock = {"branch": "NATIVE_PTS", "arrays": arrays, "pts": relative, "duration": terminal,
        "decord_clock_mode": mode, "clock_record_sha256": sha(array_path),
        "fixture_role": "direct native decoder API test; not a production registry or inference admission"}
    tolerance = 1 / float(fps) + 1e-6
    cfr_error = max(abs(float(p) - i / float(fps)) for i, p in enumerate(relative))
    evidence = {"source_sha256": source_digest, "raw_ffprobe_sha256": sha(case_root / "raw_ffprobe.json"),
        "clock_arrays_sha256": sha(array_path), "raw_first_pts_ticks": ticks[0], "raw_time_base": str(tick),
        "packet_terminal_rational": str(terminal), "decord_clock_mode": mode,
        "source_relative_pts_rational": [str(p) for p in relative], "max_legacy_cfr_error_sec": cfr_error,
        "unchanged_one_frame_tolerance_sec": tolerance, "cfr_eligible_for_diagnostic": cfr_error <= tolerance}
    write_json(case_root / "actual_clock_construction.json", evidence)
    return row, clock, evidence


def rejected(call, name):
    try:
        call()
    except (ValueError, AssertionError) as exc:
        return {"case": name, "status": "EXPECTED_STOP", "failure": str(exc)}
    raise AssertionError(name + " unexpectedly accepted")


def check_pixels(case_root, source, row, clock, expected, np, frozen_descriptor):
    from native_frames import VerifiedNativeReader, build_native_clip
    from pts_contract import native_clip_plan, validate_frame_request
    from detect_shots_pts import descriptors
    def check(frame, index):
        truth_rgb = marker_rgb(index, np)
        truth_bgr = truth_rgb[:, :, ::-1].copy()
        require(np.array_equal(frame, truth_bgr), f"decoded BGR differs from known RGB marker/ramp at source ordinal {index}")
        require(pixel_sha(frame) == expected[index]["bgr_sha256"], "shot BGR SHA differs")
        require(frame[0, 0, ::-1].tolist() == expected[index]["marker_rgb"], "RGB marker ordinal differs")
        hist, gray = descriptors(frame)
        reference_hist, reference_gray = frozen_descriptor(truth_bgr)
        require(np.array_equal(hist, reference_hist) and np.array_equal(gray, reference_gray), "production/frozen shot descriptor differs")
        return {"source_frame": index, "decoded_pixel_sha256": pixel_sha(frame),
                "marker_rgb": frame[0, 0, ::-1].tolist(), "descriptor_hist_sha256": pixel_sha(hist),
                "descriptor_gray_sha256": pixel_sha(gray)}
    reader = VerifiedNativeReader(source, row, clock)
    frame_records = []
    for index in range(FRAME_COUNT):
        frame_records.append(check(reader.read(index), index))
        if index in (0, 17, FRAME_COUNT - 1):
            require(np.array_equal(reader.read(index), marker_rgb(index, np)[:, :, ::-1]), "same-frame cached read changed")
    spatial = VerifiedNativeReader(source, row, clock)
    for index in (0, 3, 17, 40, FRAME_COUNT - 1):
        frame = spatial.read(index)
        require(pixel_sha(frame) == frame_records[index]["decoded_pixel_sha256"], "independent spatial reopen differs from shot-stage pixel SHA")
    plan = native_clip_plan(clock, 0.0, float(clock["duration"]), max_frames=64)
    require(len(plan["source_frame_ids"]) == 64 and plan["source_frame_ids"][0] == 0
            and plan["source_frame_ids"][-1] == FRAME_COUNT - 1, "native max64 ordinal sampling contract changed")
    clip, metadata = build_native_clip(source, row, clock, plan)
    for physical, index in enumerate(plan["source_frame_ids"]):
        require(np.array_equal(clip[physical], marker_rgb(index, np)), "native temporal sampled pixels use wrong source frame")
    require(metadata["frames_indices"] == plan["source_frame_ids"], "temporal metadata ordinals changed")
    last_plan = native_clip_plan(clock, float(clock["pts"][-1]), float(clock["duration"]))
    last_clip, last_metadata = build_native_clip(source, row, clock, last_plan)
    require(last_plan["source_frame_ids"] == [FRAME_COUNT - 1] and last_clip.shape[0] == 2
            and np.array_equal(last_clip[0], last_clip[1])
            and np.array_equal(last_clip[0], marker_rgb(FRAME_COUNT - 1, np))
            and last_metadata["frames_indices"] == [FRAME_COUNT - 1, FRAME_COUNT - 1], "single last physical frame padding changed identity")
    faults = []
    for bad_index in (-1, FRAME_COUNT, 0.5, True):
        faults.append(rejected(lambda value=bad_index: spatial.read(value), "invalid_frame_index_" + str(bad_index)))
    faults.append(rejected(lambda: spatial.read(1), "backward_source_ordinal"))
    wrong_row = {**row, "source_sha256": "0" * 64}
    faults.append(rejected(lambda: VerifiedNativeReader(source, wrong_row, clock), "source_sha_corruption"))
    wrong_clock = copy.deepcopy(clock); wrong_clock["arrays"]["native_pts_ticks"][17] += 1
    faults.append(rejected(lambda: VerifiedNativeReader(source, row, wrong_clock), "native_start_clock_corruption"))
    wrong_end = copy.deepcopy(clock); wrong_end["arrays"]["native_frame_end_pts_ticks"][-1] += 1
    faults.append(rejected(lambda: VerifiedNativeReader(source, row, wrong_end), "native_last_packet_end_corruption"))
    request = {"video_id": row["video_id"], "source_path": str(source), "source_frame": FRAME_COUNT,
        "source_width": WIDTH, "source_height": HEIGHT, "source_n_frames": FRAME_COUNT,
        "fps": row["fps_num"] / row["fps_den"], "target_ratio_wh": [16, 9]}
    faults.append(rejected(lambda: validate_frame_request(request, {row["video_id"]: row}), "shot_spatial_request_out_of_range"))
    require(sha(source) == row["source_sha256"], "fixture source changed during decoder tests")
    write_json(case_root / "shot_descriptor_and_pixel_identity.json", {"frames": frame_records,
        "independent_spatial_reopen_indices": [0, 3, 17, 40, FRAME_COUNT - 1], "all_equal": True})
    write_json(case_root / "temporal_native_sample_identity.json", {"plan": plan, "metadata": metadata,
        "sampled_rgb_sha256": [pixel_sha(frame) for frame in clip], "single_last_physical_frame_ids": last_plan["source_frame_ids"],
        "single_last_processor_input_ids": last_metadata["frames_indices"], "all_match_source_markers": True})
    write_json(case_root / "expected_stops.json", faults)
    return {"source_sha256": row["source_sha256"], "source_frames_checked": FRAME_COUNT, "unique_marker_frames": FRAME_COUNT,
        "shot_descriptor_matches_frozen": True, "independent_spatial_reopen_pixel_sha_matches": True,
        "temporal_sampled_frames_checked": 64, "single_last_physical_frame_padding_checked": True,
        "expected_stop_cases": len(faults)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ffmpeg", type=Path, required=True)
    parser.add_argument("--ffprobe", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    report = {"status": "CHECKING_INDEPENDENT_SYNTHETIC_DECODER", "fixture_only": True, "GPU_used": False,
        "models_run": False, "contest_media_read": False, "labels_read": False, "inference_admission_granted": False}
    output = None
    started = time.monotonic()
    try:
        target = args.output_root.resolve()
        require(args.output_root.is_absolute() and not args.output_root.exists() and ".." not in args.output_root.parts,
                "new absolute explicit output root required")
        if sys.platform.startswith("linux"):
            require(Path("/home/inspur/aic_video_work") in target.parents, "synthetic outputs outside approved Linux project root")
        require(args.ffmpeg.is_absolute() and args.ffprobe.is_absolute()
                and args.ffmpeg.is_file() and args.ffprobe.is_file(), "explicit existing absolute ffmpeg/ffprobe required")
        target.mkdir(parents=True, exist_ok=False); output = target
        for name in ("tmp", "cache"):
            (output / name).mkdir()
        os.environ.update(TMPDIR=str(output / "tmp"), TMP=str(output / "tmp"), TEMP=str(output / "tmp"),
            XDG_CACHE_HOME=str(output / "cache"), PYTHONDONTWRITEBYTECODE="1", AV_LOG_FORCE_NOCOLOR="1")
        os.chdir(output)
        report["runtime_identity"] = verify_lock()
        report["ffmpeg"] = {"path": str(args.ffmpeg.resolve()), "sha256": sha(args.ffmpeg)}
        report["ffprobe"] = {"path": str(args.ffprobe.resolve()), "sha256": sha(args.ffprobe)}
        checkpoint(output / "decoder_test_receipt.json", report)
        import numpy as np
        import decord
        import cv2
        report["environment"] = {"python": sys.version, "executable": sys.executable,
            "numpy": np.__version__, "decord": decord.__version__, "opencv": cv2.__version__}
        descriptor_path = HERE / "vendor/detect_shots_sequential.py"
        spec = importlib.util.spec_from_file_location("independent_frozen_shot_descriptor", descriptor_path)
        frozen = importlib.util.module_from_spec(spec); spec.loader.exec_module(frozen)
        report["cases"] = []
        for name, nonzero_gap in (("cfr_zero_origin", False), ("vfr_gap_nonzero_origin", True)):
            case_root, source, expected = make_source(output, str(args.ffmpeg.resolve()), name, nonzero_gap, np)
            row, clock, clock_evidence = construct_actual_clock(case_root, source, str(args.ffprobe.resolve()), np, decord)
            if nonzero_gap:
                require(clock["arrays"]["raw_first_pts_ticks"] != 0, "nonzero-origin fixture was silently normalized by muxer")
                require(not clock_evidence["cfr_eligible_for_diagnostic"], "gap fixture did not establish non-CFR behavior")
                intervals = [b - a for a, b in zip(clock["pts"], clock["pts"][1:])]
                require(max(intervals) > min(intervals) * 2, "VFR gap fixture lost intended gap")
            else:
                require(clock_evidence["cfr_eligible_for_diagnostic"], "CFR fixture is not actually CFR")
            result = check_pixels(case_root, source, row, clock, expected, np, frozen.descriptors)
            report["cases"].append({"case": name, **result, "clock_evidence": clock_evidence})
            checkpoint(output / "decoder_test_receipt.json", report)
        require(verify_lock() == report["runtime_identity"], "production/test/frozen descriptor bytes changed during test")
        report["status"] = "PASS_REAL_CPU_SYNTHETIC_NATIVE_DECODER_IDENTITY"
        report["spatial_model_entry_called"] = False
        report["shot_cli_full_manifest_admission_tested"] = False
    except Exception as exc:
        report["status"] = "FAIL_REAL_CPU_SYNTHETIC_NATIVE_DECODER_IDENTITY"
        report["failure"] = {"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()}
    report["wall_seconds"] = time.monotonic() - started
    if output is not None:
        checkpoint(output / "decoder_test_receipt.json", report)
    print(json.dumps({"status": report["status"], "receipt": str(output / "decoder_test_receipt.json") if output else None,
        "cases_passed": len(report.get("cases", [])), "source_sha256": [r["source_sha256"] for r in report.get("cases", [])],
        "failure": report.get("failure", {}).get("message"), "GPU_used": False, "models_run": False}), flush=True)
    return 0 if report["status"].startswith("PASS_") else 1


if __name__ == "__main__":
    raise SystemExit(main())
