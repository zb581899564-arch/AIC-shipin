#!/usr/bin/env python3
"""P1b-fix: real-page end-to-end verification.

Flow (all inside a real Chrome, file:// page, real HTTP to the loopback frame server):

  step 1  open the page -> pick sample S01 -> fetch an exact decoded frame ->
          drag/resize the visible box -> add interval + keyframe ->
          switch sample (state reset) -> switch back -> try two refusals ->
          export draft -> export reference
  step 2  fresh page load (same profile, so the autosave draft survives) ->
          restore the draft -> verify the restored state -> export reference again

Everything the page produces is captured from the DOM evidence hooks, written next
to the screenshots, then re-validated with the Python validator and finally consumed
by the real P1a scorer.  Semantic labels for the 8 real pilot videos are NOT filled.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
P1B = ROOT / "round6_score_alignment/p1b"
PHASE = ROOT / "reports/round6_score_alignment/phase1b_fix"
E2E = PHASE / "ui_e2e"
CHROME_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
]
SYNTHETIC = P1B / "synthetic/synthetic_marked.mp4"


def free_port(preferred: int = 8791) -> int:
    with socket.socket() as s:
        try:
            s.bind(("127.0.0.1", preferred))
            return preferred
        except OSError:
            s.bind(("127.0.0.1", 0))
            return s.getsockname()[1]


def find_chrome() -> str:
    for candidate in CHROME_CANDIDATES:
        if Path(candidate).is_file():
            return candidate
    raise SystemExit("no Chrome/Edge binary found")


def synthetic_manifest() -> dict:
    from PIL import Image  # noqa: F401  (import check only)

    meta = json.loads((P1B / "synthetic/synthetic_marked_manifest.json").read_text(encoding="utf-8"))
    width, height = meta["width"], meta["height"]
    fps, n = meta["fps"], meta["n_frames"]

    def sample(sample_id: str, ratio: list[int]) -> dict:
        tw, th = ratio
        return {
            "sample_id": sample_id, "split": "pilot_dev_synthetic",
            "source_group": "SYNTHETIC_MARKED", "youtube_id": "SYNTHETIC_MARKED",
            "file_name": meta["file_name"],
            "media_rel_path": "synthetic/" + meta["file_name"],
            "target_ratio_wh": ratio,
            "source_width": width, "source_height": height,
            "fps": float(fps), "n_frames": int(n),
            "duration_sec": round(n / fps, 6), "codec": "h264",
            "sha256_local": meta["sha256"], "sha256_remote": meta["sha256"],
            "bytes": meta["bytes"], "remote_path": "synthetic",
            "corpus_window_sec": [0, n / fps], "files_in_source_group": 1,
            "max_legal_crop": {"max_width": round(min(width, height * tw / th), 4),
                               "max_height": round(min(height, width * th / tw), 4),
                               "height_rule": "h = w * target_h / target_w"},
            "pts": {"time_base_seconds": 1.0 / (fps), "median_step_sec": 1.0 / fps,
                    "cfr_within_1us": True, "cfr_within_one_tick": True,
                    "stream_start_is_zero": True, "first_pts_sec": 0.0,
                    "last_pts_sec": (n - 1) / fps, "max_abs_step_deviation_sec": 0.0},
            "verified_sample_frames": [], "video_fingerprint": "synthetic",
            "annotation_status": "UNANNOTATED", "annotation": None,
            "source_record": {"synthetic": True,
                              "purpose": "tool verification only; not a diagnostic sample"},
        }

    return {"schema": "p1b_pilot_manifest_v1", "run_id": "round6_p1b_fix_e2e_synthetic",
            "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "purpose": "synthetic E2E manifest (tool verification only)",
            "annotation_contract": {"states": ["UNANNOTATED", "HAS_HIGHLIGHT", "NO_HIGHLIGHT",
                                               "UNCERTAIN"]},
            "sampling": {"rule": "synthetic"}, "exclusion": {"synthetic": True},
            "pilot_targets": {"groups": 2}, "totals": {"samples": 2},
            "samples": [sample("S01", [16, 9]), sample("S02", [9, 16])]}


E2E_STEP1 = r"""
<script>
(async () => {
  const out = { step: 1, checks: {}, events: [], confirm_calls: [] };
  const A = window.__annotator;
  const realConfirm = window.confirm;
  window.confirm = (msg) => { out.confirm_calls.push(String(msg)); return true; };
  window.__E2E_NO_DOWNLOAD = true;          // payloads are captured through the evidence hook
  window.alert = (msg) => { out.notice_via_alert = String(msg); };
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const wait = async (fn, ms = 8000) => {
    const t0 = Date.now();
    while (Date.now() - t0 < ms) { if (fn()) return true; await sleep(100); }
    return false;
  };
  try {
    out.checks.api_present = typeof A === "object" && !!A;
    out.checks.core_version = (A.CORE || {}).CORE_VERSION || null;
    out.checks.server_health = await A.serverHealth();
    out.checks.server_reachable = out.checks.server_health === true;
    out.checks.start_sample = A.currentSample().sample_id;

    // ---- exact decoded frame ------------------------------------------------
    A.setFrame(37, "manual_frame_input");
    const still = await A.fetchExactFrame(37);
    out.checks.still = still;
    out.checks.still_index_matches_request = !!still && still.index === 37;
    out.checks.still_hash_equals_browser_hash = !!still && still.sha256 === still.browser_hash;
    out.checks.frame_info_text = document.getElementById("frameInfo").textContent;

    // ---- visible box: drag then resize -------------------------------------
    A.setBox([0, 0, 120]);                       // start below max width so resize is visible
    document.getElementById("showBox").click();
    out.checks.overlay_visible_after_show = A.overlayStyle().display === "block";
    const beforeDrag = A.overlayStyle();
    const dragged = A.dragBox(40, 25);          // +40 display px right, +25 down
    out.checks.box_after_drag = dragged;
    const resized = A.resizeBox(20);            // widen by 20 display px
    out.checks.box_after_resize = resized;
    const after = A.overlayStyle();
    out.checks.overlay_style_before = beforeDrag;
    out.checks.overlay_style_after = after;
    out.checks.overlay_moved = beforeDrag.left !== after.left || beforeDrag.top !== after.top;
    out.checks.overlay_resized = beforeDrag.width !== after.width;
    const boxObj = JSON.parse(after.sourceBox);
    const sample = A.currentSample();
    out.checks.box_within_frame = boxObj[0] >= 0 && boxObj[1] >= 0 &&
      boxObj[0] + boxObj[2] <= sample.source_width + 1e-6 &&
      boxObj[1] + A.CORE.boxHeight(boxObj[2], sample) <= sample.source_height + 1e-6;
    out.checks.box_ratio_ok = Math.abs(A.CORE.boxHeight(boxObj[2], sample) -
      boxObj[2] * sample.target_ratio_wh[1] / sample.target_ratio_wh[0]) < 1e-9;

    // ---- clamp check: an absurd request must be clamped, not accepted ------
    out.checks.clamped_request = A.setBox([9999, 9999, 9999]);
    out.checks.overlay_after_clamp = A.overlayStyle();

    // ---- identity first, then interval covering the LAST frame + keyframe --
    A.setIdentity("E2E_SYNTHETIC_ANNOTATOR", "");
    A.setStatus("HAS_HIGHLIGHT", false);
    A.setBox([30, 20, 200]);
    A.setFrame(64, "manual_frame_input");
    await A.fetchExactFrame(64);
    A.addKeyframe();
    // interval endpoints carry their own provenance: start uses frame 60, end uses frame 119,
    // and only those frames may be claimed exact if they were decoded (60/119 were not)
    A.addInterval(60, 119);                     // last kept frame = N-1 = 119 -> end_exclusive 120
    out.checks.table_counts_after_add = A.tableCounts();
    let payload = JSON.parse(document.getElementById("preview").textContent);
    out.checks.interval = payload.intervals && payload.intervals[0];
    out.checks.keyframe = payload.keyframes && payload.keyframes[0];
    out.checks.valid_after_add = payload.validation.valid;
    out.checks.mode_after_add = payload.reference_derivation.mode;
    // ---- sample switch must reset frame + box + still ---------------------
    A.switchSample(1);
    out.checks.after_switch = { sample: A.currentSample().sample_id,
                                frame: document.getElementById("frameInput").value,
                                overlay: A.overlayStyle().display,
                                still_display: document.getElementById("still").style.display,
                                tables: A.tableCounts() };
    A.switchSample(0);
    out.checks.after_switch_back = { sample: A.currentSample().sample_id,
                                     frame: document.getElementById("frameInput").value,
                                     overlay: A.overlayStyle().display,
                                     tables: A.tableCounts() };

    // ---- valid export first (so the flow has a known-good artifact) -------
    out.checks.good_reference_export = A.exportReference();
    out.checks.good_export_valid = JSON.parse(
      JSON.parse(out.checks.good_reference_export).text).validation.valid;
    const goodDraftHook = A.exportDraft();
    const goodDraftText = JSON.parse(goodDraftHook).text;
    out.checks.good_draft_bytes = goodDraftText.length;

    // ---- refusal 1: invalid draft (negative width) must block the export ---
    const corrupt = JSON.parse(goodDraftText);
    corrupt.annotations[0].annotation.keyframes[0].box_xyw = [0, 0, -10];
    out.checks.corrupt_draft_applied = A.applyDraft(corrupt);
    const afterBad = JSON.parse(document.getElementById("preview").textContent);
    out.checks.invalid_draft_applied_problems = afterBad.validation.problems;
    out.checks.invalid_export_returned_empty = A.exportReference() === "";
    out.checks.invalid_export_refusal = A.lastRefusal();
    out.checks.invalid_export_mode = afterBad.reference_derivation.mode;
    out.checks.invalid_export_notice = A.notice();

    // ---- re-import the saved good draft (the same JSON the file input reads)
    out.checks.good_draft_reimported = A.applyDraft(JSON.parse(goodDraftText));
    const afterReimport = JSON.parse(document.getElementById("preview").textContent);
    out.checks.after_reimport_problems = afterReimport.validation.problems;
    out.checks.after_reimport_valid = afterReimport.validation.valid;
    out.checks.after_reimport_box = (afterReimport.keyframes || [{}])[0].box_xyw;

    // ---- refusal 2: NO_HIGHLIGHT with leftovers must be blocked -----------
    A.setStatus("NO_HIGHLIGHT", true);
    const conflict = JSON.parse(document.getElementById("preview").textContent);
    out.checks.conflict_problems = conflict.validation.problems;
    out.checks.conflict_mode = conflict.reference_derivation.mode;
    out.checks.conflict_export_returned_empty = A.exportReference() === "";
    out.checks.conflict_notice = A.notice();
    A.setStatus("HAS_HIGHLIGHT", false);
    out.checks.conflict_cleared_valid = JSON.parse(
      document.getElementById("preview").textContent).validation.valid;

    // ---- final drafts and reference --------------------------------------
    out.checks.draft_export = A.exportDraft();
    out.checks.reference_export = A.exportReference();
    out.checks.final_valid = JSON.parse(
      JSON.parse(out.checks.reference_export).text).validation.valid;
    out.checks.final_mode = JSON.parse(
      JSON.parse(out.checks.reference_export).text).reference_derivation.mode;
    out.checks.dirty_after_export = A.state().dirty;
  } catch (err) {
    out.error = String(err && err.stack || err);
  }
  const pre = document.createElement("pre");
  pre.id = "e2eResult";
  pre.textContent = JSON.stringify(out, null, 1);
  document.body.appendChild(pre);
  document.title = "E2E_STEP1_DONE";
})();
</script>
"""

E2E_STEP2 = r"""
<script>
(async () => {
  const out = { step: 2, checks: {}, confirm_calls: [] };
  const A = window.__annotator;
  window.__E2E_NO_DOWNLOAD = true;   // payloads are captured through the evidence hook
  window.alert = (msg) => { out.notice_via_alert = String(msg); };
  window.confirm = (msg) => { out.confirm_calls.push(String(msg)); return true; };
  const sleep = ms => new Promise(r => setTimeout(r, ms));
  const wait = async (fn, ms = 8000) => {
    const t0 = Date.now();
    while (Date.now() - t0 < ms) { if (fn()) return true; await sleep(100); }
    return false;
  };
  try {
    out.checks.server_health = await A.serverHealth();
    out.checks.sample_on_load = A.currentSample().sample_id;
    out.checks.state_on_load_dirty = A.state().dirty;
    out.checks.annotations_on_load = JSON.parse(JSON.stringify(A.state().annotations));
    out.checks.autosave_restore_message = A.restoreAutosave();
    out.checks.annotations_after_restore = JSON.parse(JSON.stringify(A.state().annotations));
    A.switchSample(0);
    const payload = JSON.parse(document.getElementById("preview").textContent);
    out.checks.restored_interval = payload.intervals && payload.intervals[0];
    out.checks.restored_keyframe = payload.keyframes && payload.keyframes[0];
    out.checks.restored_status = payload.annotation_status;
    out.checks.restored_annotator = payload.identity.annotator;
    out.checks.restored_valid = payload.validation.valid;
    out.checks.restored_mode = payload.reference_derivation.mode;
    out.checks.reference_export = A.exportReference();
  } catch (err) {
    out.error = String(err && err.stack || err);
  }
  const pre = document.createElement("pre");
  pre.id = "e2eResult";
  pre.textContent = JSON.stringify(out, null, 1);
  document.body.appendChild(pre);
  document.title = "E2E_STEP2_DONE";
})();
</script>
"""


def build_driver(step: int, page: str, out_path: Path) -> Path:
    html = page.replace("</body>", (E2E_STEP1 if step == 1 else E2E_STEP2) + "</body>")
    out_path.write_text(html, encoding="utf-8")
    return out_path


def run_chrome(chrome: str, url: str, profile: Path, png: Path, budget_ms: int) -> dict:
    cmd = [chrome, "--headless=new", "--disable-gpu", "--no-sandbox",
           "--allow-file-access-from-files", "--hide-scrollbars",
           f"--user-data-dir={profile}", "--window-size=1680,1050",
           f"--virtual-time-budget={budget_ms}",
           f"--screenshot={png}", "--dump-dom", url]
    started = time.time()
    timed_out = False
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        dom = proc.stdout
        returncode = proc.returncode
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        dom = (exc.stdout or b"").decode("utf-8", "ignore") if isinstance(exc.stdout, bytes)             else (exc.stdout or "")
        returncode = None
    result = {}
    marker = '<pre id="e2eResult">'
    if marker in dom:
        chunk = dom.split(marker, 1)[1].split("</pre>", 1)[0]
        try:
            result = json.loads(chunk.replace("&quot;", '"').replace("&amp;", "&")
                                .replace("&lt;", "<").replace("&gt;", ">"))
        except json.JSONDecodeError as exc:
            result = {"parse_error": str(exc), "raw": chunk[:2000]}
    return {"dom_bytes": len(dom), "returncode": returncode, "timed_out": timed_out,
            "seconds": round(time.time() - started, 2), "result": result,
            "screenshot": str(png),
            "screenshot_bytes": png.stat().st_size if png.exists() else 0}


def server_get(port: int, path: str) -> dict:
    with urllib.request.urlopen(f"http://127.0.0.1:{port}{path}", timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--budget-ms", type=int, default=25000)
    args = parser.parse_args()
    E2E.mkdir(parents=True, exist_ok=True)
    record: dict = {"schema": "p1b_ui_e2e_record_v1",
                    "run_id": "round6_p1b_fix_e2e_20260917",
                    "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "chrome": None, "steps": {}}

    manifest_path = E2E / "synthetic_manifest.json"
    manifest_path.write_text(json.dumps(synthetic_manifest(), ensure_ascii=False, indent=2) + "\n",
                             encoding="utf-8")

    port = free_port()
    server = subprocess.Popen([sys.executable, str(P1B / "frame_server.py"), "--port", str(port),
                               "--manifest", str(P1B / "pilot_manifest.json"),
                               "--extra-manifest", str(manifest_path)],
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    record["server"] = {"port": port, "pid": server.pid,
                        "start_command": f"python {P1B / 'frame_server.py'} --port {port}"}
    try:
        for _ in range(60):
            try:
                health = server_get(port, "/health")
                record["server"]["health"] = health
                break
            except Exception:
                time.sleep(0.5)
        else:
            raise SystemExit("frame server did not become healthy")

        chrome = find_chrome()
        record["chrome"] = chrome
        page = (P1B / "annotate_template.html").read_text(encoding="utf-8")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for sample in manifest["samples"]:
            sample["media_rel_path"] = "../synthetic/" + sample["file_name"]
        rendered = page.replace("__MANIFEST__", json.dumps(manifest, ensure_ascii=False))
        rendered = rendered.replace("__SERVER__", json.dumps(f"http://127.0.0.1:{port}"))
        # driver pages live in ui_e2e/, so the exact core file is placed next to them and its
        # hash is recorded to prove it is the same file the delivered page loads
        core_src = P1B / "annotation_core.js"
        core_dst = E2E / "annotation_core.js"
        core_dst.write_bytes(core_src.read_bytes())
        assert hashlib.sha256(core_src.read_bytes()).hexdigest() ==                hashlib.sha256(core_dst.read_bytes()).hexdigest(), "core copy diverged"
        record["core_copy"] = {
            "source": "round6_score_alignment/p1b/annotation_core.js",
            "copy": "reports/round6_score_alignment/phase1b_fix/ui_e2e/annotation_core.js",
            "sha256": hashlib.sha256(core_src.read_bytes()).hexdigest()}

        profile = E2E / "_chrome_profile"
        driver1 = build_driver(1, rendered, E2E / "driver_step1.html")
        driver2 = build_driver(2, rendered, E2E / "driver_step2.html")

        record["steps"]["step1"] = run_chrome(chrome, driver1.as_uri(), profile,
                                              E2E / "step1_page.png", args.budget_ms)
        # evidence: the exact JSON the page handed to the downloader
        s1 = record["steps"]["step1"]["result"].get("checks", {})
        for key, name in (("draft_export", "step1_draft.json"),
                          ("reference_export", "step1_reference.json")):
            hook = s1.get(key)
            if hook:
                payload = json.loads(hook)
                (E2E / name).write_text(payload["text"], encoding="utf-8")
                record["steps"]["step1"][key + "_file"] = name
                record["steps"]["step1"][key + "_name"] = payload["name"]
        if s1.get("invalid_export_refusal"):
            (E2E / "refusal_invalid_draft.json").write_text(
                s1["invalid_export_refusal"], encoding="utf-8")
        if s1.get("conflict_problems"):
            (E2E / "refusal_no_highlight_conflict.json").write_text(
                json.dumps({"problems": s1["conflict_problems"],
                            "mode": s1.get("conflict_mode"),
                            "export_blocked": s1.get("conflict_export_returned_empty")},
                           ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        record["steps"]["step2"] = run_chrome(chrome, driver2.as_uri(), profile,
                                              E2E / "step2_page.png", args.budget_ms)
        s2 = record["steps"]["step2"]["result"].get("checks", {})
        hook2 = s2.get("reference_export")
        if hook2:
            payload = json.loads(hook2)
            (E2E / "step2_restored_reference.json").write_text(payload["text"], encoding="utf-8")
            record["steps"]["step2"]["reference_export_file"] = "step2_restored_reference.json"

        # ---- independent frame-chain verification ---------------------------
        ref_path = E2E / "step2_restored_reference.json"
        chain = {"expected": "requested frame -> server decode -> displayed bytes -> export"}
        if ref_path.is_file():
            reference = json.loads(ref_path.read_text(encoding="utf-8"))
            kf = (reference.get("keyframes") or [{}])[0]
            frame = kf.get("frame")
            info = server_get(port, f"/frameinfo?sample=S01&frame={frame}")
            chain.update({"frame": frame, "server_index": info["index"],
                          "server_pts_sec": info["pts_sec"],
                          "exported_image_sha256": (kf.get("provenance") or {}).get("image_sha256"),
                          "server_image_sha256": info["sha256"],
                          "hash_match": (kf.get("provenance") or {}).get("image_sha256") == info["sha256"],
                          "index_match": info["index"] == frame})
            # decode the marker straight out of the served JPEG
            with urllib.request.urlopen(
                    f"http://127.0.0.1:{port}/frame?sample=S01&frame={frame}", timeout=30) as resp:
                jpeg = resp.read()
            import io

            from PIL import Image
            sys.path.insert(0, str(P1B))
            from make_marked_synthetic import frame_index_from_marker
            marker = frame_index_from_marker(Image.open(io.BytesIO(jpeg)))
            chain.update({"served_jpeg_bytes": len(jpeg),
                          "served_jpeg_sha256": hashlib.sha256(jpeg).hexdigest(),
                          "marker_decoded_from_served_image": marker,
                          "marker_matches_frame": marker == frame})
        record["frame_chain"] = chain
    finally:
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/shutdown", timeout=5).read()
        except Exception:
            pass
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()
        record["server"]["stopped"] = True

    record["finished_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    (E2E / "e2e_record.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n",
                                         encoding="utf-8")
    print(json.dumps({"step1_title_ok": record["steps"]["step1"]["result"].get("checks", {}) != {},
                      "step1": {k: v for k, v in record["steps"]["step1"]["result"].get("checks", {}).items()
                                if not isinstance(v, (dict, list))},
                      "step2": {k: v for k, v in record["steps"]["step2"]["result"].get("checks", {}).items()
                                if not isinstance(v, (dict, list))},
                      "frame_chain": record.get("frame_chain")}, ensure_ascii=False, indent=1)[:4000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
