"""Review the twelve preserved v5 pilot labels; never produce training labels.

A negative review is retained as a negative review, never converted to an empty
target. This diagnostic runs despite the already failed distribution gate so
that the reason for the gate failure can be investigated with real evidence.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import socket
import sys
import time

HERE = Path(__file__).resolve().parent
RUN = HERE.parent
V5 = RUN / "teacher_student_autopilot_v5"
sys.path.insert(0, str(V5))
import autopilot_common as c
import teacher_label as t


def require(value, message):
    if not value:
        raise ValueError(message)


def verify():
    lock = c.read(HERE / "source_lock.json")
    for path, digest in lock["files"].items():
        require(c.sha(path) == digest, "diagnostic bound source changed: " + path)
    manifest = c.read(HERE / "manifest.json")
    require(manifest["student_training_admitted"] is False, "diagnostic cannot admit training")
    require(c.sha(V5 / "source_lock.json") == manifest["v5_source_lock_sha256"], "v5 source lock changed")
    require(c.sha(V5 / "pilot_01/validated/validated_records.jsonl") == manifest["validated_records_sha256"], "pilot records changed")
    require(c.sha(V5 / "pilot_01/validated/validation_receipt.json") == manifest["validation_receipt_sha256"], "pilot validation changed")
    records = c.rows(V5 / "pilot_01/validated/validated_records.jsonl")
    require(len(records) == 12 and sorted(r["window_id"] for r in records) == manifest["window_ids"], "diagnostic population differs")
    validator = t.validator_for(RUN)
    for record in records:
        out = V5 / "teacher_01/windows" / record["window_id"]
        done = c.read(out / "done.json")
        require(c.sha(out / "done.json") == manifest["done_sha256"][record["window_id"]], "original done changed")
        require(done["window_sha256"] == t.canonical_sha(record["window"]), "original source window differs")
        require(all(c.sha(out / name) == digest for name, digest in done["files"].items()), "original accepted bytes changed")
        annotation = c.read(out / "annotation.json")
        require(c.sha(record["window"]["source_path"]) == record["window"]["source_sha256"], "original source changed")
        rebuilt = validator.make_record(record["window"], annotation["observation"], annotation["teacher"], annotation["raw_answer"])
        require({k:v for k,v in rebuilt.items() if k != "created_utc"} ==
                {k:v for k,v in record.items() if k != "created_utc"}, "original validator record differs")
        t.frame_content(record["actual_observation"])
    return manifest, records, validator


def supported(value):
    return (value["observation_scope"]["all_provided_frames_reviewed"] is True
            and value["semantics_consistent"] is True and value["uncertain"] is False and not value["issues"])


def run():
    require(socket.gethostname() == "inspur-NP5570M5", "diagnostic restricted to registered Linux")
    manifest, records, validator = verify()
    require(not (HERE / "registration.json").exists(), "diagnostic already registered; never duplicate")
    c.write(HERE / "registration.json", {"pid":os.getpid(), "utc":c.utc(),
        "source_lock_sha256":c.sha(HERE / "source_lock.json"), "manifest_sha256":c.sha(HERE / "manifest.json")}, fresh=True)
    admission = c.read(V5 / "teacher_admission.json")
    admission["job_source_lock_sha256"] = c.sha(HERE / "source_lock.json")
    with socket.socket() as port:
        port.bind(("127.0.0.1", 0)); number = port.getsockname()[1]
    admission["server_command"][admission["server_command"].index("--port") + 1] = str(number)
    admission["server_url"] = "http://127.0.0.1:" + str(number)
    t.validate_admission(admission, validator)
    out = HERE / "review_01"; out.mkdir(exist_ok=False)
    server = None; reviews = []; started = time.monotonic()
    try:
        server, admission = t.start_server(admission, out)
        c.write(out / "teacher_admission.json", admission, fresh=True)
        models = t.http_json(admission["server_url"] + "/v1/models", None, out / "models_http", method="GET", timeout=60)
        c.write(out / "server_models.json", models, fresh=True)
        for record in sorted(records, key=lambda r:r["window_id"]):
            window_out = out / "windows" / record["window_id"]; window_out.mkdir(parents=True, exist_ok=False)
            prompt = t.review_prompt(record)
            (window_out / "prompt.txt").write_text(prompt, encoding="utf-8")
            answer, measured = t.inference(admission["server_url"], prompt, record["actual_observation"],
                t.REVIEW_SCHEMA, admission, window_out, 3600)
            value = t.review_response(answer, record, validator, require_supported=False)
            review = {"status":"SUPPORTED_BY_SAME_TEACHER_WEAK_REVIEW" if supported(value) else "REJECTED_OR_UNCERTAIN_WEAK_REVIEW",
                "window_id":record["window_id"], "original_teacher_record_sha256":t.canonical_sha(record),
                "raw_response":answer, "parsed_response":value, "actual_observation":measured,
                "original_label_changed":False, "negative_review_converted_to_empty":False,
                "student_training_admitted":False, "same_teacher_not_independent_truth":True, "utc":c.utc()}
            c.write(window_out / "diagnostic_review_receipt.json", review, fresh=True)
            c.write(window_out / "done.json", {"original_teacher_record_sha256":t.canonical_sha(record),
                "files":{name:c.sha(window_out/name) for name in ("diagnostic_review_receipt.json", "prompt.txt", "raw_answer.txt",
                    "generation_schema.json", "runtime_grammar_validation.json", "server_response.json", "input_contract.json",
                    "processor.log", "http/request.json", "http/response.bin", "http/http_receipt.json")}}, fresh=True)
            reviews.append(review)
            c.write(HERE / "progress.json", {"stage":"RUNNING_REAL_WEAK_DIAGNOSTIC", "completed_reviews":len(reviews),
                "total_reviews":12, "supported":sum(r["status"].startswith("SUPPORTED_") for r in reviews),
                "rejected_or_uncertain":sum(not r["status"].startswith("SUPPORTED_") for r in reviews),
                "optimizer_steps":0, "utc":c.utc()})
        t.save_rows(out / "diagnostic_reviews.jsonl", reviews)
        result = {"status":"PASS_REAL_WEAK_DIAGNOSTIC_COMPLETE", "review_count":12,
            "supported":sum(r["status"].startswith("SUPPORTED_") for r in reviews),
            "rejected_or_uncertain":sum(not r["status"].startswith("SUPPORTED_") for r in reviews),
            "raw_reviews_sha256":c.sha(out / "diagnostic_reviews.jsonl"), "source_lock_sha256":c.sha(HERE / "source_lock.json"),
            "student_training_admitted":False, "optimizer_steps":0, "original_labels_preserved":True,
            "no_empty_targets_created":True, "same_teacher_not_independent_truth":True,
            "wall_sec":time.monotonic()-started, "utc":c.utc()}
        c.write(HERE / "completion.json", result, fresh=True)
        c.write(HERE / "progress.json", {"stage":result["status"], **result})
    except BaseException as error:
        c.write(HERE / "completion.json", {"status":"STOP_REAL_DIAGNOSTIC_PRESERVED", "reason":str(error),
            "completed_reviews":len(reviews), "optimizer_steps":0, "student_training_admitted":False, "utc":c.utc()}, fresh=True)
        raise
    finally:
        if server is not None:
            if server.poll() is None:
                server.terminate()
                try: server.wait(timeout=30)
                except __import__("subprocess").TimeoutExpired: server.kill(); server.wait(timeout=30)
            c.write(out / "server_stop_receipt.json", {"owned_server_pid":server.pid, "returncode":server.returncode,
                "external_processes_signalled":False, "utc":c.utc()}, fresh=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args()
    if args.preflight:
        manifest, records, _ = verify()
        print(json.dumps({"status":"PASS_DIAGNOSTIC_SOURCE_AND_ORIGINAL_LABEL_PREFLIGHT", "records":len(records), "GPU_started":False}))
    else:
        run()
