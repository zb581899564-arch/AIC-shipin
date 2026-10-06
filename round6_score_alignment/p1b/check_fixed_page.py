#!/usr/bin/env python3
"""P1b-fix: post-fix checks on the DELIVERED page plus the pre/post comparison.

Static checks are the same ones the pre-fix harness recorded, so the two runs can be
diffed directly.  Nothing here fills in semantic labels.

Usage: python p1b/check_fixed_page.py --out reports/.../post_fix_reproduction.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
P1B = Path(__file__).resolve().parent
PHASE = ROOT / "reports/round6_score_alignment/phase1b_fix"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def static_checks(html: str) -> dict:
    return {
        "has_showBox_handler": bool(re.search(r'getElementById\(["\']showBox["\']\)\s*\.onclick', html)),
        "drag_listener_count": len(re.findall(r'addEventListener\(["\'](?:mousedown|mousemove|mouseup)["\']',
                                              html)),
        "has_draft_api": bool(re.search(r'\b(exportDraft|importDraftFile|restoreAutosave)\b', html)),
        "has_localstorage_draft": "localStorage" in html,
        "mentions_end_exclusive": "end_frame_exclusive" in html,
        "has_export_validation_call": bool(re.search(r'payload\.validation\.valid', html)),
        "hardcodes_error_zero": bool(re.search(r'estimated_error_frames\s*:\s*0', html)),
        "uses_shared_core": 'src="annotation_core.js"' in html,
        "has_beforeunload_guard": "beforeunload" in html,
        "has_nonblocking_notice": bool(re.search(r'function notice\(', html)),
        "blocking_alert_calls": len(re.findall(r'\balert\(', html)),
        "keyframes_go_to_kf_table": bool(re.search(r'kt\.appendChild\(tr\)', html)),
        "intervals_go_to_interval_table": bool(re.search(r'it\.appendChild\(tr\)', html)),
        "per_endpoint_provenance": bool(re.search(r'start_provenance', html)) and
                                   bool(re.search(r'end_provenance', html)),
        "provenance_for_endpoint_frame": "provenanceForFrame(start)" in html and
                                         "provenanceForFrame(last" in html,
        "serves_exact_frame_mode": "fetchExactFrame" in html and "/frameinfo" in html,
        "template_placeholders_left": len(re.findall(r'__MANIFEST__|__SERVER__', html)),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(PHASE / "post_fix_reproduction.json"))
    args = parser.parse_args()

    delivered = P1B / "annotate.html"
    template = P1B / "annotate_template.html"
    html = delivered.read_text(encoding="utf-8")
    checks = static_checks(html)

    # the shared-core boundary cases through the SAME file the page loads
    js_cases = PHASE / "cases_js.json"
    subprocess.run([ "node", str(P1B / "run_boundary_cases.js"),
                     str(P1B / "pilot_manifest.json"), str(P1B / "boundary_cases.json"),
                     str(js_cases)], cwd=str(P1B), check=False)
    js_summary = json.loads(js_cases.read_text(encoding="utf-8")) if js_cases.is_file() else {}

    # the Python validator on the same cases
    py_cases = PHASE / "cases_python.json"
    subprocess.run([sys.executable, str(P1B / "validate_exports.py"), "cases",
                    "--out", str(py_cases)], cwd=str(ROOT), check=False)
    py_summary = json.loads(py_cases.read_text(encoding="utf-8")) if py_cases.is_file() else {}

    # the exact pre-fix reproduction of the NaN defect, re-run against the fixed validator
    prefix_raw = PHASE / "_prefix_js_raw.json"
    prefix = json.loads(prefix_raw.read_text(encoding="utf-8")) if prefix_raw.is_file() else {}

    out = {
        "schema": "p1b_post_fix_reproduction_v1",
        "delivered_page": {"path": "round6_score_alignment/p1b/annotate.html",
                           "sha256": sha256(delivered), "bytes": delivered.stat().st_size},
        "template": {"path": "round6_score_alignment/p1b/annotate_template.html",
                     "sha256": sha256(template)},
        "core": {"path": "round6_score_alignment/p1b/annotation_core.js",
                 "sha256": sha256(P1B / "annotation_core.js"),
                 "version": (js_summary.get("core_version") if js_summary else None)},
        "static_checks_after": checks,
        "static_checks_before": prefix.get("static", {}),
        "js_core_cases": {"cases": js_summary.get("cases"), "passed": js_summary.get("passed"),
                          "failed": js_summary.get("failed")},
        "python_cases": {"cases": py_summary.get("cases"), "passed": py_summary.get("passed"),
                         "failed": py_summary.get("failed")},
        "js_behaviour_before": {k: v for k, v in (prefix.get("checks") or {}).items()},
    }
    PHASE.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"out": args.out, "checks": checks,
                      "js_cases": out["js_core_cases"], "python_cases": out["python_cases"]},
                     ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
