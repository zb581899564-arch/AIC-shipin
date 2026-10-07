"""Local, evidence-bound 32B annotation and second weak semantic review.

No downloads, transfers, contest media, or teacher fallback. GPU ownership belongs
to the calling shared-resource wrapper. A child llama-server inherits its PGID.
"""
from __future__ import annotations

import argparse
import base64
import copy
from fractions import Fraction
from collections import Counter
import datetime as dt
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = Path(__file__).resolve().parent
TEACHER_ID = "Qwen/Qwen3-VL-32B-Instruct-GGUF"
BASE_ID = "Qwen/Qwen3-VL-32B-Instruct"
TEACHER_REVISION = "e3e1fe0c76de7ee58ea65db420c643adfe2e457c"
RUNTIME_REVISION = "5ad1c5da0ad7f6176256b823925aad19134f0263"
MEDIA_ROOT = Path("/home/inspur/aic_video_data/videos")
STUDENT_CONTRACT = {
    "sampling": "SELECTED_WINDOW_INTEGER_FLOOR_ENDPOINTS",
    "source_clock": "SOURCE_PRESENTATION_PTS_NOT_FPS_RECONSTRUCTION",
    "max_frames": 64, "video_size": {"shortest_edge": 4096, "longest_edge": 25165824},
    "max_sequence_length": 16384, "pixel_identity": "PYAV_RGB24_C_CONTIGUOUS_BYTES",
    "no_truncation": True, "no_resampling": True,
}
REVIEW_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["window_id", "observation_scope", "semantics_consistent", "uncertain", "reason", "issues"],
    "properties": {
        "window_id": {"type": "string"},
        "observation_scope": {"type": "object", "additionalProperties": False,
            "required": ["window_pts_start_sec", "window_pts_end_exclusive_sec", "sampled_pts_sec", "all_provided_frames_reviewed"],
            "properties": {"window_pts_start_sec": {"type": "number"}, "window_pts_end_exclusive_sec": {"type": "number"},
                "sampled_pts_sec": {"type": "array", "items": {"type": "number"}}, "all_provided_frames_reviewed": {"type": "boolean"}}},
        "semantics_consistent": {"type": "boolean"}, "uncertain": {"type": "boolean"},
        "reason": {"type": "string", "minLength": 1}, "issues": {"type": "array", "items": {"type": "string", "minLength": 1}},
    },
}


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def canonical_sha(value):
    # Matches the frozen validator's eligible teacher_record_sha256 projection.
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def text_sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def rows(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8-sig").splitlines() if line.strip()]


def save(path, value, *, fresh=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    if fresh:
        with path.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
    else:
        tmp = path.with_name(path.name + ".tmp")
        tmp.write_text(text, encoding="utf-8")
        tmp.replace(path)


def save_rows(path, values):
    with Path(path).open("x", encoding="utf-8", newline="\n") as stream:
        for value in values:
            stream.write(json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False) + "\n")


def validator_for(run_dir):
    supervision = Path(run_dir) / "next_round_v1/supervision"
    sys.path.insert(0, str(supervision))
    spec = importlib.util.spec_from_file_location("aic_frozen_teacher_validator", supervision / "validate_teacher.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    require(sha(HERE / "teacher_prompt.txt") == sha(supervision / "teacher_prompt.txt"), "new teacher prompt differs from frozen validator prompt")
    return module


def local_url(url):
    value = urllib.parse.urlsplit(url)
    require(value.scheme == "http" and value.hostname in ("127.0.0.1", "::1") and value.port
            and not value.username and not value.password and not value.query and not value.fragment
            and value.path in ("", "/", "/v1", "/v1/"), "only an explicit local loopback HTTP llama-server is allowed")
    return urllib.parse.urlunsplit((value.scheme, value.netloc, "", "", ""))


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError("local inference redirect refused: " + str(code))


def http_json(url, payload, receipt_dir, *, timeout=3600, method="POST"):
    """Persist HTTP bytes even for errors. No retry and no environment proxy."""
    receipt_dir = Path(receipt_dir)
    receipt_dir.mkdir(parents=True, exist_ok=False)
    encoded = json.dumps(payload, ensure_ascii=False, allow_nan=False).encode() if payload is not None else None
    if encoded is not None:
        (receipt_dir / "request.json").write_bytes(encoded)
    request = urllib.request.Request(url, data=encoded, method=method, headers={"Content-Type": "application/json"})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    started = utc()
    try:
        with opener.open(request, timeout=timeout) as response:
            raw, status = response.read(), response.status
    except urllib.error.HTTPError as exc:
        raw, status = exc.read(), exc.code
    except Exception as exc:
        save(receipt_dir / "http_receipt.json", {"status": "STOP_TRANSPORT_ERROR", "started_utc": started,
            "finished_utc": utc(), "url": url, "error": f"{type(exc).__name__}: {exc}", "retry_performed": False}, fresh=True)
        raise
    (receipt_dir / "response.bin").write_bytes(raw)
    save(receipt_dir / "http_receipt.json", {"status": "PASS_HTTP" if status == 200 else "STOP_HTTP_ERROR", "http_status": status,
        "started_utc": started, "finished_utc": utc(), "url": url, "request_sha256": hashlib.sha256(encoded).hexdigest() if encoded else None,
        "response_sha256": hashlib.sha256(raw).hexdigest(), "retry_performed": False}, fresh=True)
    require(status == 200, "HTTP inference failed: " + str(status))
    return json.loads(raw.decode("utf-8"))


def parse_processor_log(log_text, n_frames):
    """Read actual tensor copy dimensions. Qwen still-image temporal copies are not new source frames."""
    found = re.findall(r"copying image (\d+)/(\d+) to input buffer \(nx=(\d+), ny=(\d+)\)", log_text)
    groups, current = [], []
    for a, n, w, h in found:
        a, n, w, h = map(int, (a, n, w, h))
        require(n in (1, 2) and w > 0 and h > 0, "unexpected independent-image processor batch")
        if a == 1:
            require(not current, "incomplete preceding image tensor-copy group")
        require(a == len(current) + 1, "image tensor-copy log order changed")
        current.append([w, h])
        if a == n:
            require(len(current) == n and all(size == current[0] for size in current), "Qwen duplicated image spatial grids differ")
            groups.append({"width": w, "height": h, "tensor_copies": n, "pixels": w * h})
            current = []
    require(not current and len(groups) == n_frames, "actual processor log lacks exactly one measured grid per provided physical frame")
    require(all(g["width"] % 32 == 0 and g["height"] % 32 == 0 for g in groups), "Qwen3VL patch16/merge2 grid not evidenced")
    return groups


def verify_decoded_pts(ordinals, decoded_pts, window):
    require(ordinals == window["planned_source_frame_ordinals"], "decoded ordinal identity differs")
    require(len(decoded_pts) == len(window["planned_actual_pts_sec"]) and all(math.isfinite(x) for x in decoded_pts)
        and all(abs(x - y) <= 1e-6 for x, y in zip(decoded_pts, window["planned_actual_pts_sec"])), "decoded actual PTS differ from frozen selection")


def decode_window(window, out, validator, *, ffprobe="ffprobe"):
    """Full sequential source decode with PyAV RGB24, never seeking or FPS-derived PTS."""
    import av
    import numpy as np
    from PIL import Image
    validator.validate_window(window)
    source = Path(window["source_path"]).resolve(strict=True)
    require(MEDIA_ROOT.resolve(strict=True) in source.parents and source.is_file(), "resolved source escapes approved non-test media root")
    before = source.stat()
    require(sha(source) == window["source_sha256"], "selected source SHA differs before observation")
    probe = subprocess.run([ffprobe, "-v", "error", "-select_streams", "v:0", "-show_frames", "-show_entries",
        "frame=best_effort_timestamp_time,pkt_duration_time,duration_time", "-of", "json", str(source)],
        capture_output=True, text=True, check=True, timeout=600)
    clock_frames = json.loads(probe.stdout)["frames"]
    clock_pts, clock = validator.parse_clock_frames(clock_frames) if hasattr(validator, "parse_clock_frames") else (None, None)
    if clock_pts is None:
        from select_windows import parse_clock_frames
        clock_pts, clock = parse_clock_frames(clock_frames)
    require(clock["pts_sequence_sha256"] == window["clock_sequence_sha256"], "full-source clock sequence differs from selection")
    frame_dir = Path(out) / "frames"
    frame_dir.mkdir(exist_ok=False)
    wanted = set(window["planned_source_frame_ordinals"])
    pts, ordinals, pixels, frame_files = [], [], [], []
    with av.open(str(source), "r") as container:
        stream = container.streams.video[0]
        rate = stream.average_rate
        require(rate is not None and rate > 0, "real stream average_rate missing")
        metadata = {"fps_num": int(rate.numerator), "fps_den": int(rate.denominator),
                    "width": int(stream.codec_context.width), "height": int(stream.codec_context.height)}
        count = 0
        for ordinal, frame in enumerate(container.decode(stream)):
            require(frame.pts is not None and frame.time_base is not None, "source frame has no native PTS")
            actual = float(frame.pts * frame.time_base)
            require(ordinal < len(clock_pts) and math.isfinite(actual) and abs(actual - clock_pts[ordinal]) <= 1e-6,
                    "PyAV/ffprobe source ordinal and native PTS disagree")
            count = ordinal + 1
            if ordinal in wanted:
                image = np.ascontiguousarray(frame.to_ndarray(format="rgb24"))
                require(image.shape == (metadata["height"], metadata["width"], 3), "actual decoded RGB geometry changed")
                pixel_hash = hashlib.sha256(image.tobytes(order="C")).hexdigest()
                file = frame_dir / (str(ordinal).zfill(9) + ".png")
                Image.fromarray(image, mode="RGB").save(file, format="PNG")
                reopened = np.ascontiguousarray(np.asarray(Image.open(file).convert("RGB")))
                require(hashlib.sha256(reopened.tobytes(order="C")).hexdigest() == pixel_hash, "lossless PNG roundtrip changed source RGB")
                ordinals.append(ordinal); pts.append(actual); pixels.append(pixel_hash)
                frame_files.append({"path": str(file), "sha256": sha(file), "source_frame_ordinal": ordinal, "pixel_sha256": pixel_hash})
    require(count == len(clock_pts), "PyAV did not decode the full frozen source frame sequence")
    verify_decoded_pts(ordinals, pts, window)
    after = source.stat()
    require((before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns) and sha(source) == window["source_sha256"],
            "source changed during complete sequential decode")
    observation = {**{key: window[key] for key in ("window_id", "source_path", "source_sha256", "clock_sequence_sha256", "window_pts_start_sec", "window_pts_end_exclusive_sec", "window_duration_sec")},
        "decode_status": "PASS_REAL_SEQUENTIAL_DECODE", "pixel_identity_status": "PASS", "all_planned_frames_delivered": True,
        "source_frame_ordinals": ordinals, "actual_pts_sec": pts, "frame_pixel_sha256": pixels,
        "source_total_frames": count, **metadata, "rgb_byte_order": "RGB24_C_CONTIGUOUS", "source_full_decode_performed": True,
        "ffprobe_clock_sequence_sha256": clock["pts_sequence_sha256"], "max_frames": 64,
        "student_input_contract": STUDENT_CONTRACT, "teacher_student_same_source_range_frame_rgb": True,
        "teacher_student_embedding_tensors_equal": False,
        "teacher_modality": "ORDERED_LOSSLESS_INDEPENDENT_IMAGES_WITH_EXPLICIT_NATIVE_PTS",
        "frame_files": frame_files, "unobserved_sampling_gaps_proven_negative": False}
    save(Path(out) / "decode_receipt.json", observation, fresh=True)
    return observation


def window_local_points(observation):
    origin = Fraction(str(observation['window_pts_start_sec']))
    duration = observation['window_duration_sec']
    require(type(duration) in (int, float) and math.isfinite(duration) and duration > 0, 'actual window duration missing')
    values = [float(Fraction(str(point)) - origin) for point in observation['actual_pts_sec']]
    require(values and all(0 <= point < duration for point in values), 'provided native PTS outside local window')
    return values


def request_schema(schema, observation):
    result = copy.deepcopy(schema)
    properties = result['properties']
    properties['window_id'] = {'const': observation['window_id']}
    scope = properties['observation_scope']['properties']
    scope['window_pts_start_sec'] = {'const': observation['window_pts_start_sec']}
    scope['window_pts_end_exclusive_sec'] = {'const': observation['window_pts_end_exclusive_sec']}
    scope['sampled_pts_sec'] = {'const': observation['actual_pts_sec']}
    # all_provided_frames_reviewed and all semantic decisions remain model choices.
    if 'retained_segments' in properties:
        boundaries = sorted(set([0.0, float(observation['window_duration_sec']), *window_local_points(observation)]))
        segments = properties['retained_segments']['items']['properties']
        for key in ('start_sec', 'end_sec'):
            segments[key] = {'type': 'number', 'enum': boundaries}
    return result


def frame_content(observation):
    from PIL import Image
    import numpy as np
    content = []
    require(len(observation["frame_files"]) == len(observation["actual_pts_sec"]), "frame bundle missing")
    local_points = window_local_points(observation)
    for file, point, local_point in zip(observation["frame_files"], observation["actual_pts_sec"], local_points):
        path = Path(file["path"])
        require(sha(path) == file["sha256"], "provided lossless PNG bytes changed")
        image = np.ascontiguousarray(np.asarray(Image.open(path).convert("RGB")))
        require(hashlib.sha256(image.tobytes(order="C")).hexdigest() == file["pixel_sha256"], "provided PNG no longer matches observed RGB")
        content.extend([{"type": "text", "text": f"frame_ordinal={file['source_frame_ordinal']}; HIGHLIGHT_OUTPUT_WINDOW_LOCAL_SECONDS={local_point!r}; source_PTS_sec={point!r} (source clock is observation metadata only; retained_segments must use window-local seconds in [0,{observation['window_duration_sec']!r}])"},
            {"type": "image_url", "image_url": {"url": "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode()}}])
    return content


def inference(server_url, prompt, observation, schema, admission, out, timeout):
    log = Path(admission["server_log"])
    require(log.is_file() and admission.get("server_parallel") == 1 and admission.get("server_log_verbosity", 0) >= 5,
            "exclusive sequential server and actual DEBUG processor log required")
    offset = log.stat().st_size
    save(Path(out) / "generation_schema.json", request_schema(schema, observation), fresh=True)
    payload = {"model": TEACHER_ID, "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}, *frame_content(observation)]}],
        "temperature": 0, "seed": 20261007, "top_k": 1, "max_tokens": admission.get("max_new_tokens", 8192),
        "stream": False, "cache_prompt": False, "n_cache_reuse": 0, "timings_per_token": True,
        "chat_template_kwargs": {"enable_thinking": False}, "response_format": {"type": "json_schema", "schema": request_schema(schema, observation)}}
    result = http_json(local_url(server_url) + "/v1/chat/completions", payload, Path(out) / "http", timeout=timeout)
    save(Path(out) / "server_response.json", result, fresh=True)
    choices = result.get("choices")
    answer = choices[0].get("message", {}).get("content") if isinstance(choices, list) and len(choices) == 1 else None
    if isinstance(answer, str):
        (Path(out) / "raw_answer.txt").write_text(answer, encoding="utf-8")
    # Read only the newly appended actual encode evidence for this single request.
    require(log.stat().st_size >= offset, "server log rotated during teacher request")
    with log.open("rb") as stream:
        stream.seek(offset); log_bytes = stream.read()
    (Path(out) / "processor.log").write_bytes(log_bytes)
    grids = parse_processor_log(log_bytes.decode("utf-8", errors="replace"), len(observation["actual_pts_sec"]))
    usage = result.get("usage", {})
    tokens = usage.get("prompt_tokens")
    require(type(tokens) is int and 0 < tokens <= admission["max_sequence_length"], "actual expanded teacher token count unavailable or over contract")
    require(all(g["pixels"] <= admission["max_pixels_per_frame"] for g in grids), "actual teacher processor exceeds admitted per-frame pixels")
    require(result.get("truncated", False) is False, "teacher response truncated context")
    require(isinstance(choices, list) and len(choices) == 1 and choices[0].get("finish_reason") == "stop", "teacher generation did not finish normally; do not salvage truncated JSON")
    require(isinstance(answer, str) and answer.strip(), "teacher returned no real response text")
    contract = {"schema": "aic_real_teacher_student_observation_contract_v1", "student": STUDENT_CONTRACT,
        "teacher": {"runtime_revision": RUNTIME_REVISION, "modality": observation["teacher_modality"], "image_max_tokens": admission["image_max_tokens"],
            "image_min_tokens": admission["image_min_tokens"], "max_sequence_length": admission["max_sequence_length"],
            "max_pixels_per_frame": admission["max_pixels_per_frame"], "patch_size": 16, "merge_size": 2,
            "real_processor_grids": grids, "expanded_prompt_tokens": tokens},
        "same_source_window_ordinals_native_pts_rgb": True, "same_embedding_tensors": False, "server_request_sha256": sha(Path(out) / "http/request.json")}
    save(Path(out) / "input_contract.json", contract, fresh=True)
    measured = {"actual_processed_pixels_per_frame": [g["pixels"] for g in grids], "actual_teacher_processor_grids": grids,
        "max_pixels_per_frame": admission["max_pixels_per_frame"], "max_sequence_length": admission["max_sequence_length"],
        "input_sequence_length": tokens, "input_contract_sha256": sha(Path(out) / "input_contract.json"),
        "processor_log_sha256": sha(Path(out) / "processor.log"), "server_response_sha256": sha(Path(out) / "server_response.json")}
    return answer, measured


def teacher_receipt(admission, prompt, out):
    return {"base_model_id": BASE_ID, "model_id": TEACHER_ID, "model_revision": TEACHER_REVISION,
        "inference_status": "PASS_REAL_TEACHER_GENERATION", "production_test_access": False, "capacity_admission_pass": True,
        "job_source_lock_sha256": admission["job_source_lock_sha256"], "weight_files": admission["weight_files"],
        "runtime_revision": RUNTIME_REVISION, "generated_utc": utc(), "prompt_sha256": text_sha(prompt),
        "real_generation_response_sha256": sha(Path(out) / "server_response.json"), "real_input_contract_sha256": sha(Path(out) / "input_contract.json"),
        "teacher_admission_identity_sha256": canonical_sha(admission.get("physical_admission", admission["weight_files"]))}


def annotate(window, out, validator, admission, server_url, timeout, ffprobe):
    out = Path(out)
    done = out / "done.json"
    if done.is_file():
        receipt = read(done)
        require(receipt["window_sha256"] == canonical_sha(window) and all(sha(out / file) == digest for file, digest in receipt["files"].items()),
                "complete cached annotation identity changed")
        annotation = read(out / "annotation.json")
        require(sha(window["source_path"]) == window["source_sha256"], "source changed since the accepted cached observation")
        record = validator.make_record(window, annotation["observation"], annotation["teacher"], annotation["raw_answer"])
        # created_utc is validator-local; do not replace the original accepted record on resume.
        require(record["status"] == read(out / "validated_record.json")["status"] and record["status"] != "INVALID_TEACHER_OR_INPUT_RECEIPT",
                "cached annotation no longer passes the frozen validator")
        frame_content(annotation["observation"])
        return annotation
    require(not out.exists(), "incomplete/failed annotation exists; retain it and STOP without relabelling")
    out.mkdir(parents=True)
    started_wall = time.monotonic()
    try:
        observation = decode_window(window, out, validator, ffprobe=ffprobe)
        prompt = validator.prompt_for(window, observation)
        (out / "prompt.txt").write_text(prompt, encoding="utf-8")
        schema = read(Path(validator.HERE) / "teacher_response.schema.json")
        answer, measured = inference(server_url, prompt, observation, schema, admission, out, timeout)
        observation.update(measured)
        teacher = teacher_receipt(admission, prompt, out)
        annotation = {"window_id": window["window_id"], "observation": observation, "teacher": teacher, "raw_answer": answer}
        save(out / "annotation.json", annotation, fresh=True)
        record = validator.make_record(window, observation, teacher, answer)
        save(out / "validated_record.json", record, fresh=True)
        require(record["status"] != "INVALID_TEACHER_OR_INPUT_RECEIPT", "real annotation rejected: " + "; ".join(record["validation_errors"]))
        files = {name: sha(out / name) for name in ("annotation.json", "validated_record.json", "decode_receipt.json", "prompt.txt", "raw_answer.txt",
            "server_response.json", "input_contract.json", "processor.log", "http/request.json", "http/response.bin", "http/http_receipt.json")}
        save(done, {"status": "PASS_COMPLETE_ANNOTATION_RECEIPT", "window_sha256": canonical_sha(window), "label_status": record["status"],
            "completed_utc": utc(), "wall_sec": time.monotonic() - started_wall, "files": files}, fresh=True)
        return annotation
    except Exception as exc:
        save(out / "failure.json", {"status": "STOP_ANNOTATION_FAILURE", "window_id": window["window_id"], "failed_utc": utc(),
            "error": f"{type(exc).__name__}: {exc}", "failed_or_uncertain_never_empty": True, "automatic_retry": False}, fresh=True)
        raise


def independent_validation(run_dir, selected_train, selected_dev, selection_receipt, annotations, output):
    """Execute the unmodified validator in a new process; adapt only its output-directory guard."""
    output = Path(output)
    if output.exists():
        receipt = read(output / "validation_receipt.json")
        require(receipt["annotation_receipts_sha256"] == sha(annotations) and receipt["selection_receipt_sha256"] == sha(selection_receipt)
            and receipt["selected_train_sha256"] == sha(selected_train) and receipt["selected_dev_sha256"] == sha(selected_dev)
            and all(sha(output / name) == digest for name, digest in receipt["files"].items()), "existing independent validation differs/incomplete")
        return receipt
    validator_path = Path(run_dir) / "next_round_v1/supervision/validate_teacher.py"
    bootstrap = """import pathlib,runpy,sys
source=pathlib.Path(sys.argv[1]); expected=pathlib.Path(sys.argv[2]).resolve()
sys.path.insert(0,str(source.parent)); values=runpy.run_path(str(source))
def output_directory(path):
    resolved=pathlib.Path(path).resolve()
    if resolved!=expected or resolved.exists(): raise ValueError('fresh exact owned validation output required')
    resolved.mkdir(parents=True); return resolved
values['main'].__globals__['output_directory']=output_directory
sys.argv=[str(source)]+sys.argv[3:]
values['main']()
"""
    process = subprocess.run([sys.executable, "-c", bootstrap, str(validator_path), str(output),
        "--selected-train", str(selected_train), "--selected-dev", str(selected_dev), "--selection-receipt", str(selection_receipt),
        "--annotation-receipts", str(annotations), "--out-dir", str(output)], capture_output=True, text=True, timeout=300)
    (output.parent / "independent_validator.stdout.txt").write_text(process.stdout, encoding="utf-8")
    (output.parent / "independent_validator.stderr.txt").write_text(process.stderr, encoding="utf-8")
    require(process.returncode == 0, "independent frozen validator failed: " + process.stderr[-1500:])
    save(output.parent / "independent_validator_execution.json", {"status": "PASS_INDEPENDENT_FROZEN_VALIDATOR", "returncode": 0,
        "validator_sha256": sha(validator_path), "select_windows_sha256": sha(validator_path.parent / "select_windows.py"),
        "output_guard_adapter_sha256": text_sha(bootstrap), "adaptation": "ONLY_FRESH_EXACT_OUTPUT_DIRECTORY_GUARD_FOR_NEW_OWNED_OUTPUT",
        "response_or_observation_validation_modified": False, "completed_utc": utc()}, fresh=True)
    return read(output / "validation_receipt.json")


def review_prompt(record):
    window, observation = record["window"], record["actual_observation"]
    contract = {key: window[key] for key in ("window_id", "window_pts_start_sec", "window_pts_end_exclusive_sec", "window_duration_sec")}
    contract["sampled_pts_sec"] = observation["actual_pts_sec"]
    return ("你再次检查同一完整自然窗口的全部实际采样画面，审核下面弱教师判断是否有可解释的画面依据。"
        "这不是人工真值或独立模型共识。请重新看所有提供帧，核对事件解释、起止边界、多段遗漏、全选偏置和显式无高光的依据。"
        "采样间隙无法观察，不能证明为负。若无法支持完整列表，请uncertain=true或semantics_consistent=false，不为了让训练继续而通过。"
        "空判断必须确实有普通背景/等待等可解释依据；有事件却缺段、边界错位或全选缺解释应拒绝。不要修改原标签。"
        "只输出严格JSON，字段恰好window_id,observation_scope,semantics_consistent,uncertain,reason,issues。"
        "observation_scope字段恰好window_pts_start_sec,window_pts_end_exclusive_sec,sampled_pts_sec,all_provided_frames_reviewed。"
        "reason必须说明此次实际审核依据，issues保存发现的问题。\n合同：" + json.dumps(contract, ensure_ascii=False, allow_nan=False)
        + "\n待审核完整原始响应：" + record["raw_answer"])


def review_response(answer, record, validator):
    value = validator.strict_json(answer)
    validator.exact_keys(value, {"window_id", "observation_scope", "semantics_consistent", "uncertain", "reason", "issues"}, "review schema mismatch")
    require(value["window_id"] == record["window_id"], "review window identity differs")
    scope = value["observation_scope"]
    validator.exact_keys(scope, validator.SCOPE_KEYS, "review observation scope mismatch")
    validator.same_numbers([scope["window_pts_start_sec"], scope["window_pts_end_exclusive_sec"]],
        [record["window"]["window_pts_start_sec"], record["window"]["window_pts_end_exclusive_sec"]], "review observed a different window")
    validator.same_numbers(scope["sampled_pts_sec"], record["actual_observation"]["actual_pts_sec"], "review sampled PTS changed")
    require(scope["all_provided_frames_reviewed"] is True and type(value["semantics_consistent"]) is bool and type(value["uncertain"]) is bool,
            "review did not verify all actually delivered samples")
    require(validator.nonempty_text(value["reason"]) and isinstance(value["issues"], list)
        and all(validator.nonempty_text(issue) for issue in value["issues"]), "review explanations unavailable")
    require(value["semantics_consistent"] is True and value["uncertain"] is False and not value["issues"], "real weak reviewer cannot support this complete-window label")
    return value


def review_one(record, out, validator, admission, server_url, timeout):
    out = Path(out)
    require(sha(record["window"]["source_path"]) == record["window"]["source_sha256"], "review source differs from accepted original observation")
    if (out / "done.json").is_file():
        done = read(out / "done.json")
        require(done["teacher_record_sha256"] == canonical_sha(record) and all(sha(out / name) == digest for name, digest in done["files"].items()),
                "complete cached review changed")
        review = read(out / "review_receipt.json")
        review_response(review["raw_response"], record, validator)
        frame_content(record["actual_observation"])
        return review
    require(not out.exists(), "incomplete/failed review exists; retain and STOP without random rereview")
    out.mkdir(parents=True)
    try:
        prompt = review_prompt(record)
        (out / "prompt.txt").write_text(prompt, encoding="utf-8")
        answer, measured = inference(server_url, prompt, record["actual_observation"], REVIEW_SCHEMA, admission, out, timeout)
        value = review_response(answer, record, validator)
        review = {"schema": "aic_real_weak_teacher_second_review_record_v1", "window_id": record["window_id"],
            "teacher_record_sha256": canonical_sha(record), "review_status": "PASS_EXPLAINABLE_SAMPLED_WINDOW_REVIEW",
            "all_provided_frames_reviewed": True, "uncertain": False, "semantics_consistent": True, "reason": value["reason"],
            "reviewer_model_id": BASE_ID, "reviewer_model_revision": TEACHER_REVISION, "reviewer_runtime_revision": RUNTIME_REVISION,
            "raw_response": answer, "raw_response_sha256": text_sha(answer), "parsed_response": value,
            "review_prompt_sha256": text_sha(prompt), "review_prompt_path": str(out / "prompt.txt"),
            "same_teacher_not_independent_truth": True, "manual_ground_truth": False, "actual_observation": measured,
            "teacher": teacher_receipt(admission, prompt, out),
            "source_frame_pixel_sha256": record["actual_observation"]["frame_pixel_sha256"],
            "source_frame_ordinals": record["actual_observation"]["source_frame_ordinals"], "actual_pts_sec": record["actual_observation"]["actual_pts_sec"],
            "server_response_sha256": sha(out / "server_response.json"), "completed_utc": utc()}
        save(out / "review_receipt.json", review, fresh=True)
        save(out / "done.json", {"teacher_record_sha256": canonical_sha(record), "files": {name: sha(out / name)
            for name in ("review_receipt.json", "raw_answer.txt", "prompt.txt", "server_response.json", "input_contract.json", "processor.log", "http/response.bin")}}, fresh=True)
        return review
    except Exception as exc:
        save(out / "failure.json", {"status": "STOP_SEMANTIC_REVIEW_FAILURE", "window_id": record["window_id"], "error": f"{type(exc).__name__}: {exc}",
            "original_label_not_changed_or_removed": True, "automatic_retry": False, "failed_utc": utc()}, fresh=True)
        raise


def semantic_audit(records, validation):
    eligible = [record for record in records if record["sft_eligible"]]
    reasons = []
    for split in ("train", "dev"):
        if validation["positive_by_split"][split] < 1:
            reasons.append(split + " lacks explainable validated positive windows; new independently selected expansion required")
        if validation["explicit_empty_by_split"][split] < 1:
            reasons.append(split + " lacks real justified explicit-empty windows; never force an empty quota")
        split_records = [record for record in eligible if record["split"] == split]
        if split_records and all(record.get("explicit_no_highlight") for record in split_records):
            reasons.append(split + " is systematically all-empty")
        if split_records and all(len(record["retained_segments"]) == 1 and record["retained_segments"][0]["start_sec"] == 0
            and record["retained_segments"][0]["end_sec"] == record["window"]["window_duration_sec"] for record in split_records):
            reasons.append(split + " is systematically whole-window selected")
    if math.ceil(validation["eligible_by_split"]["train"] / 16) * 3 < 20:
        reasons.append("eligible train count cannot yield the 20-update prefix within three epochs; independent 512/64 selection needs new registration")
    representatives = {}
    conditions = {"positive": lambda r: bool(r["retained_segments"]), "explicit_empty": lambda r: r["explicit_no_highlight"],
        "multisegment": lambda r: len(r["retained_segments"]) > 1,
        "boundary": lambda r: bool(r["parsed_answer"]["boundary_notes"]) or r["window"].get("structural_stratum") in ("source_beginning", "source_end")}
    for name, condition in conditions.items():
        candidates = sorted((record for record in eligible if condition(record)), key=lambda r: r["window_id"])
        representatives[name] = [{"window_id": r["window_id"], "split": r["split"], "teacher_record_sha256": canonical_sha(r),
            "source_group": r["source_group"], "actual_pts_coverage_sec": r["actual_pts_coverage_sec"],
            "window_duration_sec": r["window"]["window_duration_sec"], "decision_reason": r["parsed_answer"]["decision_reason"],
            "retained_segments": r["retained_segments"], "boundary_notes": r["parsed_answer"]["boundary_notes"]} for r in candidates[:4]]
    return reasons, {"representative_selection": "STABLE_WINDOW_ID_FIRST_FOUR_PER_OBSERVED_CLASS_NO_FABRICATION", "representatives": representatives,
        "missing_observed_classes": [name for name, examples in representatives.items() if not examples],
        "source_groups_by_split": {split: len({r["source_group"] for r in eligible if r["split"] == split}) for split in ("train", "dev")},
        "retained_duration_fraction_by_window": [{"window_id": r["window_id"], "split": r["split"],
            "retained_duration_fraction": sum(s["end_sec"] - s["start_sec"] for s in r["retained_segments"]) / r["window"]["window_duration_sec"]} for r in eligible],
        "no_observed_class_manufactured": True, "weak_teacher_only": True}


def semantic_review(out, validator, admission, server_url, timeout):
    validated = Path(out) / "validated"
    records, validation = rows(validated / "validated_records.jsonl"), read(validated / "validation_receipt.json")
    reasons, audit = semantic_audit(records, validation)
    eligible = [r for r in records if r["sft_eligible"]]
    review_rows = []
    try:
        # Counts and bias shortages stop before consuming a second full inference pass.
        require(not reasons, "; ".join(reasons))
        for record in sorted(eligible, key=lambda r: r["window_id"]):
            review_rows.append(review_one(record, Path(out) / "reviews" / record["window_id"], validator, admission, server_url, timeout))
        raw_path = Path(out) / "raw_semantic_review_receipts.jsonl"
        if raw_path.exists():
            require(rows(raw_path) == review_rows, "aggregate semantic review bytes differ")
        else:
            save_rows(raw_path, review_rows)
        receipt = {"schema": "aic_automated_weak_semantic_review_v1", "status": "PASS_AUTOMATED_WEAK_SEMANTIC_REVIEW",
            "mode": "AUTOMATED_WEAK_TEACHER_REVIEW_NOT_HUMAN_GROUND_TRUTH", "manual_ground_truth": False,
            "confirm_opened": False, "contest_assets_opened": False, "validation_receipt_sha256": sha(validated / "validation_receipt.json"),
            "files": {name: sha(validated / name) for name in ("eligible_train.jsonl", "eligible_dev.jsonl", "validated_records.jsonl")},
            "reviewed_teacher_record_sha256": [canonical_sha(r) for r in eligible], "positive_reviewed": True, "explicit_empty_reviewed": True,
            "multisegment_and_boundary_reviewed_without_fabrication": True, "raw_review_receipts": {"path": str(raw_path), "sha256": sha(raw_path)},
            "input_coverage_and_event_explanations_reviewed": True, "source_group_isolation_pass": True,
            "no_unknown_or_unobserved_gaps_certified_negative": True, "no_forced_empty_quota": True,
            "teacher_long_interval_and_all_positive_bias_reviewed": True, "boundary_and_multisegment_behavior_reviewed": True,
            "second_review_same_teacher_not_independent_evidence": True, "semantic_training_admitted": False, "completed_utc": utc(), **audit}
    except Exception as exc:
        receipt = {"schema": "aic_automated_weak_semantic_review_v1", "status": "STOP_AUTOMATED_WEAK_SEMANTIC_REVIEW",
            "mode": "AUTOMATED_WEAK_TEACHER_REVIEW_NOT_HUMAN_GROUND_TRUTH", "manual_ground_truth": False,
            "confirm_opened": False, "contest_assets_opened": False, "reasons": reasons + [f"{type(exc).__name__}: {exc}"],
            "completed_review_count": len(review_rows), "labels_removed_to_make_gate_pass": False, "semantic_training_admitted": False,
            "validation_receipt_sha256": sha(validated / "validation_receipt.json"), "checked_utc": utc(), **audit}
    save(Path(out) / "semantic_review.json", receipt)
    return receipt


def load_selection(args, validator):
    selection = read(args.selection_receipt)
    require(selection.get("status") == "PASS_CPU_SELECTION_UNLABELLED" and selection.get("confirm_opened") is False
            and selection.get("contest_assets_opened") is False, "actual successful isolated unlabelled selection receipt required")
    require(selection["files"]["selected_train.jsonl"] == sha(args.selected_train) and selection["files"]["selected_dev.jsonl"] == sha(args.selected_dev),
            "selection receipt byte identities differ")
    train, dev = rows(args.selected_train), rows(args.selected_dev)
    require(len(train) == 128 and len(dev) == 32 and all(w["split"] == "train" for w in train) and all(w["split"] == "dev" for w in dev),
            "this job requires the frozen first 128train/32dev selection")
    validator.validate_isolation(train, dev)
    require(len({w["window_id"] for w in train + dev}) == 160, "duplicate selected window identity")
    for window in train + dev:
        validator.validate_window(window)
    return train, dev


def validate_admission(admission, validator):
    require(admission.get("status") in ("ADMITTED_PENDING_REAL_TEACHER_PROBE", "PASS_REAL_STRONGER_TEACHER_ADMISSION"), "teacher job has not been admitted for real probe")
    require(admission.get("model_id") == TEACHER_ID and admission.get("model_revision") == TEACHER_REVISION
        and admission.get("base_model_id") == BASE_ID and admission.get("runtime_revision") == RUNTIME_REVISION,
        "pinned teacher/runtime identity mismatch")
    require(admission.get("production_test_access") is False and validator.is_sha(admission.get("job_source_lock_sha256")), "teacher isolation/source lock missing")
    for name in ("max_sequence_length", "max_pixels_per_frame", "image_min_tokens", "image_max_tokens"):
        require(type(admission.get(name)) is int and admission[name] > 0, "explicit admitted teacher input limit required: " + name)
    for weight in admission["weight_files"]:
        path = Path(weight["path"])
        require(path.is_absolute() and path.is_file() and path.stat().st_size == weight["bytes"] and sha(path) == weight["sha256"], "actual pinned teacher weight bytes differ")
    # Frozen validator verifies the exact official two-file SHA recipe.
    probe_teacher = {**admission, "inference_status": "PASS_REAL_TEACHER_GENERATION", "capacity_admission_pass": True,
        "prompt_sha256": text_sha("WEIGHT_IDENTITY_CHECK_ONLY"), "generated_utc": utc()}
    validator.validate_teacher(probe_teacher, "WEIGHT_IDENTITY_CHECK_ONLY")


def start_server(admission, out):
    command = admission.get("server_command")
    require(isinstance(command, list) and command and all(isinstance(part, str) for part in command), "explicit frozen local server command required")
    def option(key):
        require(key in command and command.index(key) + 1 < len(command), "server command lacks " + key)
        return command[command.index(key) + 1]
    require(option("--host") == "127.0.0.1" and option("--parallel") == "1" and "--no-context-shift" in command,
            "server must use loopback/exclusive slot/no context shift")
    require(int(option("--ctx-size")) == admission["max_sequence_length"] and int(option("--image-max-tokens")) == admission["image_max_tokens"]
        and int(option("--image-min-tokens")) == admission["image_min_tokens"] and int(option("--log-verbosity")) >= 5,
        "actual server options differ from teacher observation contract")
    model_path = option("--model") if "--model" in command else option("-m")
    actual_weight_paths = {str(Path(weight["path"]).resolve()) for weight in admission["weight_files"]}
    require({str(Path(model_path).resolve()), str(Path(option("--mmproj")).resolve())} == actual_weight_paths,
            "actual local server model/projector paths differ from the SHA-verified recipe")
    if admission.get("server_binary_sha256"):
        require(sha(command[0]) == admission["server_binary_sha256"], "pinned server executable bytes changed")
    log = Path(out) / "server.log"
    handle = log.open("ab", buffering=0)
    process = subprocess.Popen(command, cwd=str(HERE), stdout=handle, stderr=subprocess.STDOUT)  # inherit caller's shared GPU PGID
    handle.close()
    admission.update(server_pid=process.pid, server_log=str(log), server_parallel=1, server_log_verbosity=int(option("--log-verbosity")),
        server_port=int(option("--port")), server_url="http://127.0.0.1:" + option("--port"))
    save(Path(out) / "server_start_receipt.json", {"pid": process.pid, "parent_pgid": os.getpgrp(), "inherited_process_group": True,
        "command": command, "server_log": str(log), "started_utc": utc()})
    deadline = time.monotonic() + 600
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    try:
        while time.monotonic() < deadline:
            require(process.poll() is None, "owned local server exited during load")
            try:
                with opener.open(admission["server_url"] + "/health", timeout=5) as response:
                    if response.status == 200:
                        return process, admission
            except (urllib.error.URLError, TimeoutError):
                pass
            time.sleep(2)
        raise ValueError("teacher server did not become healthy within bounded load wait")
    except Exception:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=30)
            except subprocess.TimeoutExpired:
                process.kill(); process.wait(timeout=30)
        raise


def choose_probe_windows(train, dev, out, ffprobe):
    """Label-independent metadata rank: most frames, then greatest native RGB footprint."""
    path = Path(out) / "probe_selection.json"
    selected = {w["window_id"]: w for w in train + dev}
    if path.exists():
        evidence = read(path)
        require(evidence["selected_windows_sha256"] == canonical_sha(train + dev), "probe selection input changed")
        return [selected[identity] for identity in evidence["window_ids"]]
    candidates = []
    for window in train + dev:
        probe = subprocess.run([ffprobe, "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
            "-of", "json", window["source_path"]], check=True, capture_output=True, text=True, timeout=60)
        meta = json.loads(probe.stdout)["streams"][0]
        require(type(meta["width"]) is int and type(meta["height"]) is int and meta["width"] > 0 and meta["height"] > 0,
                "real non-test source geometry missing for probe admission")
        candidates.append({"window_id": window["window_id"], "split": window["split"], "actual_native_width": meta["width"],
            "actual_native_height": meta["height"], "sampled_frames": len(window["planned_actual_pts_sec"]),
            "uncompressed_provided_rgb_bytes": len(window["planned_actual_pts_sec"]) * meta["width"] * meta["height"] * 3})
    chosen = [min((c for c in candidates if c["split"] == split), key=lambda c:
        (-c["sampled_frames"], -c["uncompressed_provided_rgb_bytes"], c["window_id"]))["window_id"] for split in ("train", "dev")]
    save(path, {"schema": "aic_teacher_real_nontest_probe_selection_v1", "selected_windows_sha256": canonical_sha(train + dev),
        "window_ids": chosen, "rank_rule": "MOST_ACTUAL_SELECTED_FRAMES_THEN_LARGEST_SOURCE_RGB_FOOTPRINT_THEN_STABLE_WINDOW_ID",
        "label_or_quality_values_read": False, "contest_or_confirm_opened": False,
        "not_a_claim_of_unmeasured_worst_teacher_token_count": True, "candidates": candidates}, fresh=True)
    return [selected[identity] for identity in chosen]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("run-dir", "out-dir", "selected-train", "selected-dev", "selection-receipt"):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--server-url", default="http://127.0.0.1:8080")
    parser.add_argument("--teacher-admission", type=Path)
    parser.add_argument("--start-server", action="store_true")
    parser.add_argument("--phase", choices=("all", "probe", "labels", "review"), default="all")
    parser.add_argument("--request-timeout", type=int, default=3600)
    parser.add_argument("--ffprobe", default="ffprobe")
    args = parser.parse_args()
    require(socket.gethostname() == "inspur-NP5570M5", "real teacher inference is restricted to the registered Linux host")
    args.run_dir = args.run_dir.resolve(strict=True); args.out_dir = args.out_dir.resolve()
    require(args.run_dir == HERE.parent and HERE in args.out_dir.parents, "run/output must stay in this independent owned job")
    local_url(args.server_url)
    admission_path = args.teacher_admission or (HERE / "teacher_admission.json")
    validator = validator_for(args.run_dir)
    train, dev = load_selection(args, validator)
    admission = read(admission_path)
    validate_admission(admission, validator)
    binding = {"schema": "aic_teacher_annotation_binding_v1", "selection_receipt_sha256": sha(args.selection_receipt),
        "selected_train_sha256": sha(args.selected_train), "selected_dev_sha256": sha(args.selected_dev),
        "source_sha256": sha(__file__), "prompt_template_sha256": sha(HERE / "teacher_prompt.txt"), "admission_input_sha256": sha(admission_path),
        "sampling": STUDENT_CONTRACT, "model_id": TEACHER_ID, "teacher_revision": TEACHER_REVISION, "runtime_revision": RUNTIME_REVISION}
    args.out_dir.mkdir(parents=True, exist_ok=True)
    registration = args.out_dir / "job_registration.json"
    if registration.exists():
        require(read(registration)["binding"] == binding, "registered teacher job inputs/code changed; fresh independent version required")
    else:
        save(registration, {"binding": binding, "registered_utc": utc(), "pid": os.getpid(), "confirm_opened": False,
            "contest_assets_opened": False, "automatic_retry_of_failed_windows": False}, fresh=True)
    server = None
    phase_started = time.monotonic()
    try:
        if args.start_server:
            server, admission = start_server(admission, args.out_dir)
        else:
            require(admission.get("status") == "PASS_REAL_STRONGER_TEACHER_ADMISSION", "external server requires already real admitted receipt")
        server_url = admission["server_url"] if args.start_server else local_url(args.server_url)
        schema_probe = http_json(local_url(server_url) + "/v1/models", None, args.out_dir / ("models_check_" + str(os.getpid())), timeout=30, method="GET")
        save(args.out_dir / "server_models.json", schema_probe)
        models = schema_probe.get("data", [])
        require(len(models) == 1 and "image" in models[0].get("architecture", {}).get("input_modalities", [])
            and models[0].get("meta", {}).get("n_ctx") == admission["max_sequence_length"],
            "loaded real server lacks image support or its actual slot context differs from admission")
        # Genuine non-test heavy probes are selected on frozen sampling and real metadata only.
        annotations = []
        if args.phase != "review":
            probe_windows = choose_probe_windows(train, dev, args.out_dir, args.ffprobe)
            for window in probe_windows:
                annotate(window, args.out_dir / "windows" / window["window_id"], validator, admission, server_url, args.request_timeout, args.ffprobe)
            final_admission = {**admission, "status": "PASS_REAL_STRONGER_TEACHER_ADMISSION", "capacity": {"status": "PASS_REAL_STRONGER_TEACHER_ADMISSION"},
                "capacity_admission_pass": True, "real_non_test_probe_windows": [w["window_id"] for w in probe_windows], "probe_completed_utc": utc()}
            save(args.out_dir / "teacher_admission.json", final_admission)
            save(args.out_dir / "teacher_probe_completion.json", {"status": "PASS_REAL_NONTEST_TEACHER_PROBE", "window_ids": [w["window_id"] for w in probe_windows],
                "admission_sha256": sha(args.out_dir / "teacher_admission.json"), "actual_processor_grids_and_tokens_measured": True,
                "not_a_supervision_or_training_admission": True, "completed_utc": utc(), "wall_sec": time.monotonic() - phase_started,
                "per_window_wall_sec": [read(args.out_dir / "windows" / w["window_id"] / "done.json")["wall_sec"] for w in probe_windows],
                "max_actual_prompt_tokens": max(read(args.out_dir / "windows" / w["window_id"] / "annotation.json")["observation"]["input_sequence_length"] for w in probe_windows)})
            if args.phase == "probe":
                return
            for index, window in enumerate(train + dev):
                annotations.append(annotate(window, args.out_dir / "windows" / window["window_id"], validator, admission, server_url, args.request_timeout, args.ffprobe))
                save(args.out_dir / "progress.json", {"status": "REAL_TEACHER_LABELS_RUNNING", "completed_windows": index + 1, "selected_windows": 160,
                    "last_window_id": window["window_id"], "updated_utc": utc()})
            aggregate = args.out_dir / "annotation_receipts.jsonl"
            if aggregate.exists():
                require(rows(aggregate) == annotations, "complete aggregate annotations changed")
            else:
                save_rows(aggregate, annotations)
            validation = independent_validation(args.run_dir, args.selected_train, args.selected_dev, args.selection_receipt, aggregate, args.out_dir / "validated")
            require(validation["record_count"] == 160 and validation["unlabelled_window_count"] == 0
                and validation["status_counts"].get("INVALID_TEACHER_OR_INPUT_RECEIPT", 0) == 0, "independent validation incomplete/invalid")
            save(args.out_dir / "teacher_completion.json", {"schema": "aic_real_teacher_label_completion_v1", "status": "PASS_VALIDATED_WEAK_TEACHER_LABELS",
                "validation_receipt": {"path": str(args.out_dir / "validated/validation_receipt.json"), "sha256": sha(args.out_dir / "validated/validation_receipt.json")},
                "files": validation["files"], "eligible_by_split": validation["eligible_by_split"], "label_status": "WEAK_TEACHER_NOT_MANUAL_GROUND_TRUTH",
                "semantic_training_admitted": False, "confirm_opened": False, "contest_assets_opened": False, "completed_utc": utc()})
        if args.phase in ("all", "review"):
            require(read(args.out_dir / "teacher_completion.json").get("status") == "PASS_VALIDATED_WEAK_TEACHER_LABELS",
                    "semantic review requires completed real labels, not a manually assembled validation directory")
            validation = independent_validation(args.run_dir, args.selected_train, args.selected_dev, args.selection_receipt,
                args.out_dir / "annotation_receipts.jsonl", args.out_dir / "validated")
            require(validation["record_count"] == 160 and validation["unlabelled_window_count"] == 0
                and validation["status_counts"].get("INVALID_TEACHER_OR_INPUT_RECEIPT", 0) == 0,
                "semantic review annotation/selection/independent validation chain incomplete")
            review = semantic_review(args.out_dir, validator, admission, server_url, args.request_timeout)
            require(review["status"] == "PASS_AUTOMATED_WEAK_SEMANTIC_REVIEW", "semantic review STOP; see semantic_review.json")
    except Exception as exc:
        save(args.out_dir / "teacher_stop.json", {"status": "STOP_REAL_TEACHER_PIPELINE", "error": f"{type(exc).__name__}: {exc}", "stopped_utc": utc(),
            "previous_success_and_raw_failures_preserved": True, "semantic_training_admitted": False})
        raise
    finally:
        if server is not None and server.poll() is None:
            server.terminate()
            try:
                server.wait(timeout=30)
            except subprocess.TimeoutExpired:
                server.kill(); server.wait(timeout=30)
            save(args.out_dir / "server_stop_receipt.json", {"owned_server_pid": server.pid, "returncode": server.returncode,
                "stopped_utc": utc(), "external_processes_signalled": False})


if __name__ == "__main__":
    main()
