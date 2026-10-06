#!/usr/bin/env python3
"""Tests for the round-2 verification entry (orarl_verify.py).

Covers the six defects the round-2 brief lists:
  D1 four-state separation (tracking with missing keys is NOT protocol-complete)
  D2 any failing case -> non-zero exit, per-case status reported
  D3 run_id isolation, refusal to overwrite an existing run directory
  D4 NaN / Infinity / boolean-as-number / duplicate keys / multi-answer /
     temporal "first two numbers" all rejected
  D5 expected tracking key set comes from the case, not a hard-coded 1..32
  D6 this file

Runs end-to-end with --fake-generator (no GPU, no model).
Run:  python3 test_orarl_verify.py
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import orarl_verify as ov  # noqa: E402

PY = sys.executable
RESULTS = {"passed": [], "failed": []}


def check(name, cond, detail=""):
    (RESULTS["passed"] if cond else RESULTS["failed"]).append(name)
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f"   {detail}" if detail else ""))


def states(raw, task, expected, exec_error=None):
    return ov.evaluate_states(raw, task, expected, exec_error)


# ---------------------------------------------------------------------------
def t_d1_four_states():
    print("\n--- D1 four-state separation ---")
    exp32 = {"expected_seconds": list(range(1, 33))}
    # 32/32 keys present -> all three states true
    full = '<answer>{"boxes": {' + ", ".join(
        f'"{i}": [100,200,300,400]' for i in range(1, 33)) + '}}</answer>'
    r = states(full, "tracking", exp32)
    check("D1 complete tracking: parseable&protocol&success",
          r["output_parseable"] and r["protocol_complete"] and r["task_success"])
    # 2/32 keys -> parseable but NOT protocol_complete, NOT success
    part = '<answer>{"boxes": {"1": [100,200,300,400], "2": [1,2,3,4]}}</answer>'
    r = states(part, "tracking", exp32)
    check("D1 partial tracking: parseable TRUE", r["output_parseable"])
    check("D1 partial tracking: protocol_complete FALSE", not r["protocol_complete"])
    check("D1 partial tracking: task_success FALSE", not r["task_success"])
    check("D1 partial tracking: missing keys listed",
          len(r["parsed"]["missing_expected_seconds"]) == 30)
    # quality must never be silently promoted to a number
    check("D1 quality is NOT_COMPUTABLE without trusted GT",
          r["quality"]["status"] == "NOT_COMPUTABLE")
    # an execution error is success=False but is a different state
    r = states("", "tracking", exp32, exec_error="RuntimeError: boom")
    check("D1 exec error: all three FALSE",
          not r["output_parseable"] and not r["protocol_complete"] and not r["task_success"])
    check("D1 exec error preserved", r["execution_error"] == "RuntimeError: boom")


def t_d4_strict_json():
    print("\n--- D4 strict decoding ---")
    exp32 = {"expected_seconds": [1]}
    cases = [
        ("empty string", "", "no <answer>"),
        ("NaN rejected",
         '<answer>{"boxes": {"1": [NaN, 1, 2, 3]}}</answer>', "non-finite"),
        ("Infinity rejected",
         '<answer>{"boxes": {"1": [Infinity, 1, 2, 3]}}</answer>', "non-finite"),
        ("-Infinity rejected",
         '<answer>{"boxes": {"1": [-Infinity, 1, 2, 3]}}</answer>', "non-finite"),
        ("bool as number rejected",
         '<answer>{"boxes": {"1": [true, 1, 2, 3]}}</answer>', "boolean"),
        ("string as number rejected",
         '<answer>{"boxes": {"1": ["1", 1, 2, 3]}}</answer>', "non-numeric"),
        ("duplicate JSON keys rejected",
         '<answer>{"boxes": {"1": [1,2,3,4]}, "boxes": {"1": [5,6,7,8]}}</answer>',
         "duplicate"),
        ("two <answer> blocks rejected",
         '<answer>{"boxes": {"1": [1,2,3,4]}}</answer><answer>{"boxes": {"1": [9,9,9,9]}}'
         '</answer>', "ambiguous"),
        ("null box rejected",
         '<answer>{"boxes": {"1": null}}</answer>', "list of 4 numbers"),
        ("float second key rejected",
         '<answer>{"boxes": {"1.5": [1,2,3,4]}}</answer>', "integer second"),
    ]
    for name, raw, want in cases:
        r = states(raw, "tracking", exp32)
        ok = (not r["output_parseable"]) and any(want.lower() in e.lower()
                                                 for e in r["parse_errors"])
        check(f"D4 {name}", ok, f"errors={r['parse_errors'][:1]}")

    print("\n--- D4 temporal must not ignore trailing content ---")
    expt = {"clip_duration_sec": 32.0}
    bad = [
        ("three numbers", "<answer>12 to 18 to 25</answer>"),
        ("two spans", "<answer>12 to 18 and 20 to 25</answer>"),
        ("trailing text with numbers", "<answer>12 to 18, maybe 22</answer>"),
        ("leading prose", "<answer>the event is 12 to 18</answer>"),
    ]
    for name, raw in bad:
        r = states(raw, "temporal_grounding", expt)
        check(f"D4 temporal rejects {name}", not r["output_parseable"],
              f"errors={r['parse_errors'][:1]}")
    # round-1 behaviour would have accepted these; confirm the good case still works
    r = states("<answer> 12 to 18 </answer>", "temporal_grounding", expt)
    check("D4 temporal accepts clean span", r["task_success"])
    r = states("<answer>12.5 to 18.25</answer>", "temporal_grounding", expt)
    check("D4 temporal accepts decimals", r["task_success"])
    r = states("<answer>5 to 99</answer>", "temporal_grounding", expt)
    check("D4 temporal rejects span beyond clip", not r["task_success"])


def t_d5_expected_keys():
    print("\n--- D5 expected key set from case, not a global 1..32 ---")
    check("D5 explicit expected_seconds honoured",
          ov.resolve_expected_seconds({"expected_seconds": [1, 2, 3]}) == [1, 2, 3])
    d = ov.resolve_expected_seconds({"sampling": {"fps": 1, "max_frames": 32},
                                     "clip_duration_sec": 10.0})
    check("D5 10 s clip -> 1..10 (not 1..32)", d == list(range(1, 11)), str(d))
    d = ov.resolve_expected_seconds({"sampling": {"fps": 1, "max_frames": 32},
                                     "clip_duration_sec": 32.2})
    check("D5 32.2 s clip -> capped at 1..32", d == list(range(1, 33)))
    d = ov.resolve_expected_seconds({"sampling": {"fps": 2, "max_frames": 64},
                                     "clip_duration_sec": 5.0})
    check("D5 fps=2 5 s clip -> 1..10", d == list(range(1, 11)), str(d))
    # consequence: a video whose protocol needs only 10 keys must NOT be
    # failed for missing 11..32
    exp10 = {"expected_seconds": ov.resolve_expected_seconds(
        {"sampling": {"fps": 1, "max_frames": 32}, "clip_duration_sec": 10.0})}
    raw = '<answer>{"boxes": {' + ", ".join(
        f'"{i}": [10,20,30,40]' for i in range(1, 11)) + '}}</answer>'
    r = states(raw, "tracking", exp10)
    check("D5 10-key answer is protocol_complete for a 10 s clip", r["task_success"])
    # same answer against a 32-key protocol must fail
    r = states(raw, "tracking", {"expected_seconds": list(range(1, 33))})
    check("D5 same answer fails a 32-key protocol", not r["task_success"])
    # a case with no declared expectation must not silently pass
    r = states(raw, "tracking", {})
    check("D5 undeclared expected_seconds -> not protocol_complete",
          not r["protocol_complete"])
    # malformed case: neither explicit keys nor duration
    try:
        ov.resolve_expected_seconds({"sampling": {"fps": 1}})
        check("D5 missing config raises", False)
    except ValueError:
        check("D5 missing config raises", True)


def t_d3_run_isolation():
    print("\n--- D3 run_id isolation / refuse overwrite ---")
    tmp = Path(tempfile.mkdtemp(prefix="ov_test_"))
    try:
        cases = tmp / "cases.jsonl"
        # a real tiny media file so resolve_cases can probe it
        img = tmp / "frame.png"
        _make_png(img)
        cases.write_text(json.dumps({
            "case_id": "c1", "task": "spatial_grounding", "expression": "a thing",
            "image": str(img), "sampling": {"min_pixels": 4096, "max_pixels": 262144},
        }) + "\n")
        out = tmp / "out"
        r1 = subprocess.run([PY, str(HERE / "orarl_verify.py"), "--cases", str(cases),
                             "--out-root", str(out), "--run-id", "runA", "--dry-run"],
                            capture_output=True, text=True)
        check("D3 first dry-run succeeds", r1.returncode == 0, r1.stderr[-200:])
        check("D3 run dir created", (out / "runA").is_dir())
        r2 = subprocess.run([PY, str(HERE / "orarl_verify.py"), "--cases", str(cases),
                             "--out-root", str(out), "--run-id", "runA", "--dry-run"],
                            capture_output=True, text=True)
        check("D3 second run with same run_id refused (exit 3)", r2.returncode == 3,
              f"rc={r2.returncode}")
        check("D3 refusal message mentions overwrite",
              "refusing to overwrite" in (r2.stderr + r2.stdout))
        r3 = subprocess.run([PY, str(HERE / "orarl_verify.py"), "--cases", str(cases),
                             "--out-root", str(out), "--run-id", "runB", "--dry-run"],
                            capture_output=True, text=True)
        check("D3 different run_id allowed", r3.returncode == 0)
        check("D3 both run dirs exist",
              (out / "runA").is_dir() and (out / "runB").is_dir())
        r4 = subprocess.run([PY, str(HERE / "orarl_verify.py"), "--cases", str(cases),
                             "--out-root", str(out), "--run-id", "bad/../id", "--dry-run"],
                            capture_output=True, text=True)
        check("D3 path-traversal run_id rejected (exit 2)", r4.returncode == 2)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def t_d2_exit_code_and_status():
    print("\n--- D2 non-zero exit on any failing case + per-case status ---")
    tmp = Path(tempfile.mkdtemp(prefix="ov_test_"))
    try:
        img = tmp / "frame.png"
        _make_png(img)
        vid = tmp / "clip.mkv"
        _make_video(vid)
        cases = tmp / "cases.jsonl"
        cases.write_text("\n".join([
            json.dumps({"case_id": "ok_sg", "task": "spatial_grounding",
                        "expression": "a thing", "image": str(img),
                        "sampling": {"min_pixels": 4096, "max_pixels": 262144}}),
            json.dumps({"case_id": "ok_tr", "task": "tracking", "video": str(vid),
                        "question": "Track [1,2,3,4].", "sampling": {"fps": 1, "max_frames": 8},
                        "clip_duration_sec": 8.0}),
            json.dumps({"case_id": "bad_tr", "task": "tracking", "video": str(vid),
                        "question": "Track [1,2,3,4].", "sampling": {"fps": 1, "max_frames": 8},
                        "clip_duration_sec": 8.0}),
        ]) + "\n")
        canned = tmp / "canned.jsonl"
        good8 = '<answer>{"boxes": {' + ", ".join(
            f'"{i}": [10,20,30,40]' for i in range(1, 9)) + '}}</answer>'
        canned.write_text("\n".join([
            json.dumps({"case_id": "ok_sg",
                        "raw_output": '<answer>[{"bbox_2d": [10, 20, 30, 40]}]</answer>'}),
            json.dumps({"case_id": "ok_tr", "raw_output": good8}),
            json.dumps({"case_id": "bad_tr",
                        "raw_output": '<answer>{"boxes": {"1": [10,20,30,40]}}</answer>'}),
        ]) + "\n")
        out = tmp / "out"
        r = subprocess.run([PY, str(HERE / "orarl_verify.py"), "--cases", str(cases),
                            "--out-root", str(out), "--run-id", "mixed",
                            "--fake-generator", str(canned)],
                           capture_output=True, text=True)
        check("D2 non-zero exit when one case fails (exit 5)", r.returncode == 5,
              f"rc={r.returncode}")
        check("D2 per-case table printed",
              "PER-CASE STATUS" in r.stdout and "ok_sg" in r.stdout
              and "bad_tr" in r.stdout)
        check("D2 failing case shown as success=False", "success=False" in r.stdout)
        status = json.loads((out / "mixed" / "run_status.json").read_text())
        by = {c["case_id"]: c for c in status["cases"]}
        check("D2 status json records n_failed=1", status["run"]["n_failed"] == 1)
        check("D2 status json records exit_code=5", status["run"]["exit_code"] == 5)
        check("D2 ok_sg task_success", by["ok_sg"]["task_success"])
        check("D2 ok_tr task_success", by["ok_tr"]["task_success"])
        check("D2 bad_tr parseable but not success",
              by["bad_tr"]["output_parseable"] and not by["bad_tr"]["task_success"])
        check("D2 raw outputs saved per case",
              (out / "mixed" / "raw" / "bad_tr.raw.txt").exists())
        # all-pass case must exit 0
        canned2 = tmp / "canned2.jsonl"
        canned2.write_text("\n".join([
            json.dumps({"case_id": "ok_sg",
                        "raw_output": '<answer>[{"bbox_2d": [10, 20, 30, 40]}]</answer>'}),
            json.dumps({"case_id": "ok_tr", "raw_output": good8}),
            json.dumps({"case_id": "bad_tr", "raw_output": good8}),
        ]) + "\n")
        r2 = subprocess.run([PY, str(HERE / "orarl_verify.py"), "--cases", str(cases),
                             "--out-root", str(out), "--run-id", "allpass",
                             "--fake-generator", str(canned2)],
                            capture_output=True, text=True)
        check("D2 all-pass exits 0", r2.returncode == 0, f"rc={r2.returncode}")
        # an exception in one case must not abort the run, but must fail it
        canned3 = tmp / "canned3.jsonl"
        canned3.write_text("\n".join([
            json.dumps({"case_id": "ok_sg",
                        "raw_output": '<answer>[{"bbox_2d": [10, 20, 30, 40]}]</answer>'}),
            json.dumps({"case_id": "ok_tr", "raw_output": good8}),
            json.dumps({"case_id": "bad_tr", "raw_output": "", "raise": "boom"}),
        ]) + "\n")
        r3 = subprocess.run([PY, str(HERE / "orarl_verify.py"), "--cases", str(cases),
                             "--out-root", str(out), "--run-id", "exception",
                             "--fake-generator", str(canned3)],
                            capture_output=True, text=True)
        check("D2 exception in a case -> non-zero exit", r3.returncode == 5)
        st3 = json.loads((out / "exception" / "run_status.json").read_text())
        by3 = {c["case_id"]: c for c in st3["cases"]}
        check("D2 exception recorded as execution_error",
              "boom" in (by3["bad_tr"]["execution_error"] or ""))
        check("D2 other cases still evaluated",
              by3["ok_sg"]["task_success"] and by3["ok_tr"]["task_success"])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _make_png(p: Path):
    from PIL import Image
    Image.new("RGB", (64, 48), (30, 60, 90)).save(p)


def _make_video(p: Path):
    """2-second, 10 fps tiny video via ffmpeg already on the box."""
    import subprocess as sp
    tmp = p.parent / "vidbuild"
    tmp.mkdir(exist_ok=True)
    from PIL import Image
    for i in range(20):
        Image.new("RGB", (64, 48), (i * 10 % 255, 40, 80)).save(tmp / f"v_{i:04d}.png")
    sp.run(["/usr/local/bin/ffmpeg", "-nostdin", "-y", "-v", "error",
            "-framerate", "10", "-i", str(tmp / "v_%04d.png"),
            "-c:v", "ffv1", "-pix_fmt", "rgb24", str(p)], check=True)
    shutil.rmtree(tmp, ignore_errors=True)


def t_d6_self():
    print("\n--- D6 test file itself ---")
    check("D6 test file is present and runnable", Path(__file__).exists())


def main():
    print("=" * 72)
    print("test_orarl_verify.py  (python", sys.version.split()[0], ")")
    print("=" * 72)
    t_d1_four_states()
    t_d4_strict_json()
    t_d5_expected_keys()
    t_d3_run_isolation()
    t_d2_exit_code_and_status()
    t_d6_self()
    n_ok, n_bad = len(RESULTS["passed"]), len(RESULTS["failed"])
    print("\n" + "=" * 72)
    print(f"RESULT: {n_ok} passed, {n_bad} failed")
    if n_bad:
        print("FAILED:", RESULTS["failed"])
    print("=" * 72)
    out = HERE.parent / "no_gpu_tests/test_results.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "test_file": str(Path(__file__).resolve()),
        "python": sys.version.split()[0],
        "n_passed": n_ok, "n_failed": n_bad,
        "passed": RESULTS["passed"], "failed": RESULTS["failed"],
        "result": "ALL PASS" if n_bad == 0 else "FAILURES",
    }, indent=2) + "\n")
    print("wrote", out)
    return 1 if n_bad else 0


if __name__ == "__main__":
    sys.exit(main())
