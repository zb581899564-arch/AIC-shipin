#!/usr/bin/env python3
"""P1b step 5: build the offline annotation package.

Produces, inside round6_score_alignment/p1b/:
  pilot_manifest.json   per-sample media + frame timetable + provenance record
  annotate.html         self-contained offline annotation page (data embedded)
  README_annotation.md  how to use it and what may be exported

The page never contacts a server, never writes anywhere except a local download,
and starts every highlight/composition field as UNANNOTATED.  Text inside
``<script>`` is embedded JSON produced by json.dumps, which cannot break out of
the tag for these data.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
P1B = ROOT / "round6_score_alignment/p1b"
MEDIA_VERIFICATION = ROOT / "reports/round6_score_alignment/phase1b/media_verification.json"
INVENTORY = P1B / "inventory_raw.json"
PROBE = P1B / "remote_probe_raw.json"
MANIFEST = P1B / "pilot_manifest.json"
HTML = P1B / "annotate.html"
README = P1B / "README_annotation.md"

RUN_ID = "round6_p1b_20260917T0615Z"

SOURCE_RECORD = {
    "origin": "competition-provided Baidu-netdisk share '/高光剪辑训练集/qvhighlights-videos/'",
    "evidence_files": [
        "remote:/home/inspur/aic_video_data/bddownload.log (share listing, 34 zip archives + train.jsonl)",
        "remote:/home/inspur/aic_video_data/unzip.log (UNZIP_ALL_DONE after extracting the archives)",
        "reports/标签来源复核_20260915.md (project record of the share and its open questions)",
    ],
    "video_provenance": ("derived 150-second windows of public YouTube videos, named "
                         "<youtube_id>_<start>_<end>.mp4; the YouTube id is the source group"),
    "terms_recorded": [
        {"what": "official task page", "url": "https://www.aicomp.cn/tracks/tracks-6/4267.html",
         "read_on": "2026-09-15 (recorded 2026-09-09 and 2026-09-15 in project evidence)",
         "states": "the organiser does not provide a training set; public/self-built training data "
                   "is allowed; samples, test data and a basic evaluation script are provided",
         "confidence": "page text recorded by the project; not re-fetched in P1b"},
        {"what": "competition-provided share", "url": "login-gated AIC submission form (not public)",
         "read_on": "recorded in reports/标签来源复核_20260915.md",
         "states": "shows the 高光剪辑训练集 and test-video download links",
         "confidence": "recorded, publisher identity not verifiable from the logs"},
    ],
    "permitted_use_registered": ["internal research use inside this project",
                                 "local offline analysis, annotation and diagnostics"],
    "limitations": [
        "no per-video licence is attached to the shared corpus",
        "the underlying videos are YouTube content with their own rights; the share terms do not "
        "transfer them",
        "'downloadable from a netdisk' is NOT treated as a licence grant",
        "videos must not be redistributed or published by this project",
        "no frame or video may be sent to any external service",
    ],
    "unconfirmed": [
        "whether the share terms permit redistribution (assumed NOT, so nothing is redistributed)",
        "the identity of the share publisher",
        "whether the corpus videos share sources with the official test set (see the pilot report's "
        "test-exclusion limitations)",
    ],
}

ANNOTATION_CONTRACT = {
    "states": ["UNANNOTATED", "HAS_HIGHLIGHT", "NO_HIGHLIGHT", "UNCERTAIN"],
    "rules": [
        "every highlight and composition field starts UNANNOTATED; the page never pre-fills semantics",
        "NO_HIGHLIGHT requires an explicit confirmation by the annotator and only then exports an "
        "empty ground-truth frame set",
        "UNANNOTATED and UNCERTAIN are never exported as a reference; they are exported as "
        "'not_exportable' with a reason",
        "UNANNOTATED is exported with intervals=null and keyframes=null, never as []",
        "composition keyframes are sparse and export as coverage='sparse'; the page never fabricates "
        "per-frame boxes",
        "reviewed_by stays null unless a human reviewer is recorded; no tool fills it automatically",
        "browser currentTime is an estimate: the frame field records how the number was obtained and "
        "the estimated error",
    ],
}


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def build_manifest() -> dict:
    verification = load(MEDIA_VERIFICATION)
    inventory = load(INVENTORY)
    probe = load(PROBE)
    probe_by_name = {item["file_name"]: item for item in probe["items"]}
    selection = {s["youtube_id"]: s for s in inventory["sampling"]["selected"]}

    samples = []
    for item in verification["items"]:
        name = item["file_name"]
        remote = probe_by_name[name]
        group = selection.get(item["youtube_id"], {})
        width = item["decode_probe"]["width"]
        height = item["decode_probe"]["height"]
        tw, th = item["target_ratio_wh"]
        max_w = min(width, height * tw / th)
        max_h = min(height, width * th / tw)
        samples.append({
            "sample_id": item["sample_id"],
            "split": "pilot_dev",
            "source_group": item["youtube_id"],
            "youtube_id": item["youtube_id"],
            "file_name": name,
            "media_rel_path": f"media/{name}",
            "media_abs_path": str((P1B / "media" / name).resolve()),
            "target_ratio_wh": item["target_ratio_wh"],
            "source_width": width,
            "source_height": height,
            "fps": item["decode_probe"]["average_rate"],
            "n_frames": item["decode_probe"]["frames"],
            "duration_sec": round(item["decode_probe"]["frames"]
                                  / item["decode_probe"]["average_rate"], 6),
            "codec": item["decode_probe"]["codec"],
            "sha256_local": item["local_sha256"],
            "sha256_remote": remote.get("sha256"),
            "bytes": item["local_bytes"],
            "remote_path": remote.get("remote_path"),
            "corpus_window_sec": group.get("window"),
            "files_in_source_group": group.get("files_in_group"),
            "max_legal_crop": {"max_width": round(max_w, 4), "max_height": round(max_h, 4),
                               "height_rule": "h = w * target_h / target_w"},
            "pts": {k: v for k, v in item["pts"].items()
                    if k in ("time_base_seconds", "median_step_sec", "cfr_within_1us",
                             "cfr_within_one_tick", "stream_start_is_zero", "first_pts_sec",
                             "last_pts_sec", "max_abs_step_deviation_sec")},
            "verified_sample_frames": item["fingerprint"]["frame_table"],
            "video_fingerprint": item["fingerprint"]["video_fingerprint"],
            "annotation_status": "UNANNOTATED",
            "annotation": None,
            "source_record": SOURCE_RECORD,
        })

    return {
        "schema": "p1b_pilot_manifest_v1",
        "run_id": RUN_ID,
        "created_utc": verification["generated_utc"],
        "purpose": ("8-source-group pilot media package for offline, human annotation; every "
                    "highlight/composition field is intentionally unannotated"),
        "annotation_contract": ANNOTATION_CONTRACT,
        "sampling": inventory["sampling"],
        "exclusion": inventory["exclusion"],
        "pilot_targets": {"groups": 8, "target_ratio_wh_distribution": {"[16,9]": 4, "[9,16]": 4},
                          "negative_examples": ("not guaranteed and not fabricated; a no-highlight "
                                                "case only counts if an annotator confirms it")},
        "totals": {"samples": len(samples),
                   "bytes": sum(s["bytes"] for s in samples),
                   "duration_sec": round(sum(s["duration_sec"] for s in samples), 3)},
        "samples": samples,
    }


def build_html(manifest: dict) -> str:
    data = json.dumps(manifest, ensure_ascii=False)
    return """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<title>AIC P1b pilot annotation (offline)</title>
<style>
 :root { --bg:#14161a; --panel:#1d2026; --line:#2c313a; --fg:#e8eaee; --muted:#9aa3b2;
         --accent:#4da3ff; --warn:#ffb020; --ok:#3ddc84; --bad:#ff5f56; }
 * { box-sizing:border-box; }
 body { margin:0; background:var(--bg); color:var(--fg);
        font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Noto Sans CJK SC",sans-serif; }
 header { padding:10px 14px; background:var(--panel); border-bottom:1px solid var(--line);
          display:flex; gap:12px; align-items:center; flex-wrap:wrap; }
 h1 { font-size:15px; margin:0 12px 0 0; font-weight:600; }
 .warn { color:var(--warn); font-size:12px; }
 main { display:grid; grid-template-columns: 300px 1fr 380px; gap:12px; padding:12px; }
 .panel { background:var(--panel); border:1px solid var(--line); border-radius:8px; padding:10px; }
 .panel h2 { font-size:13px; margin:0 0 8px; color:var(--muted); font-weight:600; text-transform:uppercase; letter-spacing:.04em;}
 .samplebtn { display:block; width:100%; text-align:left; margin:4px 0; padding:8px;
              background:#232830; color:var(--fg); border:1px solid var(--line); border-radius:6px; cursor:pointer; }
 .samplebtn.active { border-color:var(--accent); background:#1b2c42; }
 .samplebtn small { color:var(--muted); display:block; }
 video { width:100%; background:#000; border-radius:6px; }
 .stage { position:relative; display:inline-block; width:100%; }
 .overlay { position:absolute; border:2px solid var(--accent); background:rgba(77,163,255,.18);
            cursor:move; }
 .overlay .handle { position:absolute; right:-6px; bottom:-6px; width:12px; height:12px;
                    background:var(--accent); cursor:nwse-resize; }
 .row { display:flex; gap:8px; align-items:center; margin:6px 0; flex-wrap:wrap; }
 label { color:var(--muted); font-size:12px; }
 input[type=number], input[type=text], textarea, select {
   background:#12151a; color:var(--fg); border:1px solid var(--line); border-radius:4px; padding:4px 6px; }
 input[type=number] { width:80px; }
 textarea { width:100%; min-height:52px; }
 button { background:#2b313b; color:var(--fg); border:1px solid var(--line); border-radius:4px;
          padding:5px 9px; cursor:pointer; }
 button:hover { border-color:var(--accent); }
 button.primary { background:#1f4d7a; border-color:var(--accent); }
 button.danger { background:#4a2323; border-color:#7a2f2f; }
 table { width:100%; border-collapse:collapse; font-size:12.5px; }
 th, td { border-bottom:1px solid var(--line); padding:4px 5px; text-align:left; }
 .muted { color:var(--muted); }
 .pill { display:inline-block; padding:1px 7px; border-radius:10px; font-size:11.5px;
         border:1px solid var(--line); }
 .pill.UNANNOTATED { color:var(--muted); }
 .pill.HAS_HIGHLIGHT { color:var(--ok); border-color:#245c3d; }
 .pill.NO_HIGHLIGHT { color:var(--warn); border-color:#5c4a24; }
 .pill.UNCERTAIN { color:var(--bad); border-color:#5c2424; }
 .kv { font-size:12px; color:var(--muted); }
 .kv b { color:var(--fg); font-weight:600; }
 pre { background:#12151a; border:1px solid var(--line); border-radius:6px; padding:8px;
       max-height:260px; overflow:auto; font-size:11.5px; }
</style>
</head>
<body>
<header>
  <h1>AIC P1b 试点标注（离线）</h1>
  <span class="warn">所有高光/构图字段默认“未标注”。页面不联网、不上传、不写入任何服务器；导出靠浏览器下载。</span>
</header>

<main>
  <section class="panel" id="left">
    <h2>样本（8 来源组）</h2>
    <div id="sampleList"></div>
    <div class="kv" id="sampleMeta"></div>
  </section>

  <section class="panel">
    <h2>视频与定位</h2>
    <div class="stage">
      <video id="video" controls preload="metadata"></video>
      <div class="overlay" id="overlay" style="display:none"><div class="handle" id="handle"></div></div>
    </div>
    <div class="row">
      <span class="kv">当前时间 <b id="tNow">0.000</b> s ｜ 估算帧 <b id="fEst">0</b>
      （<span id="fErr">±1 帧</span>，浏览器时间不是精确帧号）</span>
    </div>
    <div class="row">
      <label>帧号（权威字段）</label><input type="number" id="frameInput" value="0" min="0">
      <button id="useEstimate">用当前时间估算帧号</button>
      <button id="stepBack10">-10 帧</button><button id="stepBack1">-1 帧</button>
      <button id="stepFwd1">+1 帧</button><button id="stepFwd10">+10 帧</button>
      <button id="alignPts">对齐到最近的已校验采样帧</button>
    </div>
    <div class="row" id="ptsRow"></div>
    <div class="row">
      <label>目标比例</label><span class="pill" id="ratioPill"></span>
      <span class="kv">最大合法裁剪 <b id="maxCrop"></b></span>
    </div>
  </section>

  <section class="panel">
    <h2>标注</h2>
    <div class="row">
      <label>状态</label>
      <select id="status">
        <option value="UNANNOTATED">未标注（默认）</option>
        <option value="HAS_HIGHLIGHT">有高光</option>
        <option value="NO_HIGHLIGHT">确认无高光</option>
        <option value="UNCERTAIN">不确定</option>
      </select>
      <label><input type="checkbox" id="confirmNoHighlight"> 我确认整段没有值得保留的高光</label>
    </div>

    <h2 style="margin-top:10px">时间区间（秒 = 帧 / fps）</h2>
    <div class="row">
      <label>起帧</label><input type="number" id="intStart" min="0">
      <label>止帧</label><input type="number" id="intEnd" min="0">
      <button id="setStartHere">起点=当前帧</button>
      <button id="setEndHere">终点=当前帧</button>
      <button id="addInterval">添加区间</button>
    </div>
    <table id="intervalTable"><thead><tr><th>#</th><th>起帧</th><th>止帧</th><th>起s</th><th>止s</th><th></th></tr></thead><tbody></tbody></table>

    <h2 style="margin-top:10px">稀疏构图关键帧 [x, y, w]</h2>
    <div class="row">
      <label>x</label><input type="number" id="bx" value="0">
      <label>y</label><input type="number" id="by" value="0">
      <label>w</label><input type="number" id="bw" value="100">
      <span class="kv">高度按比例推导 h = w·th/tw</span>
    </div>
    <div class="row">
      <button id="showBox">在画面上显示/编辑框</button>
      <button id="addKeyframe">以当前帧添加关键帧</button>
      <button id="clampBox">框约束到合法范围</button>
    </div>
    <table id="kfTable"><thead><tr><th>帧</th><th>x</th><th>y</th><th>w</th><th>h(推导)</th><th></th></tr></thead><tbody></tbody></table>

    <h2 style="margin-top:10px">身份与不确定性</h2>
    <div class="row"><label>标注者</label><input type="text" id="annotator" placeholder="必填，需为真实执行者"></div>
    <div class="row"><label>复核者</label><input type="text" id="reviewer" placeholder="未复核则留空"></div>
    <div class="row"><textarea id="notes" placeholder="不确定性/说明（例如：帧号由浏览器时间估算，误差约 1 帧）"></textarea></div>

    <div class="row">
      <button class="primary" id="exportOne">导出本样本 JSON</button>
      <button id="exportAll">导出全部已标注样本</button>
      <button id="copyJson">复制本样本 JSON</button>
      <button class="danger" id="resetOne">清空本样本标注</button>
    </div>
    <div class="kv" id="exportHint"></div>
    <pre id="preview"></pre>
  </section>
</main>

<script>
const MANIFEST = __MANIFEST__;
const state = { current: 0, annotations: {} };
const samples = MANIFEST.samples;

function blank() {
  return { status: "UNANNOTATED", confirm_no_highlight: false, intervals: null, keyframes: null,
           annotator: "", reviewer: null, notes: "", frame_source: null, estimated_error_frames: null };
}
function ann(sample) {
  if (!state.annotations[sample.sample_id]) state.annotations[sample.sample_id] = blank();
  return state.annotations[sample.sample_id];
}
function frameFromTime(t, sample) { return Math.max(0, Math.min(sample.n_frames - 1, Math.round(t * sample.fps))); }
function timeFromFrame(f, sample) { return f / sample.fps; }
function boxHeight(w, sample) { return w * sample.target_ratio_wh[1] / sample.target_ratio_wh[0]; }

function renderSampleList() {
  const el = document.getElementById("sampleList");
  el.innerHTML = "";
  samples.forEach((s, i) => {
    const b = document.createElement("button");
    b.className = "samplebtn" + (i === state.current ? " active" : "");
    b.innerHTML = `<b>${s.sample_id}</b> ${s.source_group}<small>` +
      `${s.source_width}x${s.source_height} · ${s.fps.toFixed(3)} fps · ${s.n_frames} 帧 · ` +
      `目标 ${s.target_ratio_wh[0]}:${s.target_ratio_wh[1]} · ` +
      `<span class="pill ${ann(s).status}">${ann(s).status}</span></small>`;
    b.onclick = () => { state.current = i; loadSample(); };
    el.appendChild(b);
  });
}

function loadSample() {
  const s = samples[state.current];
  const v = document.getElementById("video");
  v.src = s.media_rel_path;
  v.load();
  const a = ann(s);
  document.getElementById("status").value = a.status;
  document.getElementById("confirmNoHighlight").checked = !!a.confirm_no_highlight;
  document.getElementById("annotator").value = a.annotator || "";
  document.getElementById("reviewer").value = a.reviewer || "";
  document.getElementById("notes").value = a.notes || "";
  document.getElementById("ratioPill").textContent = s.target_ratio_wh[0] + ":" + s.target_ratio_wh[1];
  document.getElementById("maxCrop").textContent =
    `宽 ${s.max_legal_crop.max_width} × 高 ${s.max_legal_crop.max_height}（源 ${s.source_width}x${s.source_height}）`;
  const maxW = Math.floor(s.max_legal_crop.max_width);
  document.getElementById("bw").value = Math.min(maxW, Math.floor(s.source_width));
  document.getElementById("bw").max = maxW;
  document.getElementById("frameInput").max = s.n_frames - 1;
  document.getElementById("intEnd").max = s.n_frames - 1;
  const ptsRow = document.getElementById("ptsRow");
  ptsRow.innerHTML = "<label>已校验采样帧</label>";
  s.verified_sample_frames.forEach(f => {
    const b = document.createElement("button");
    b.textContent = f.index;
    b.title = `PTS ${f.pts_sec}s`;
    b.onclick = () => { v.currentTime = f.pts_sec; setFrameField(f.index, "pts_sample", 0); };
    ptsRow.appendChild(b);
  });
  renderTables();
  renderSampleList();
  updatePreview();
}

function setFrameField(frame, source, errorFrames) {
  document.getElementById("frameInput").value = frame;
  const a = ann(samples[state.current]);
  a.frame_source = source;
  a.estimated_error_frames = errorFrames;
}

function renderTables() {
  const s = samples[state.current];
  const a = ann(s);
  const it = document.querySelector("#intervalTable tbody");
  it.innerHTML = "";
  (a.intervals || []).forEach((iv, i) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>${i + 1}</td><td>${iv.start_frame}</td><td>${iv.end_frame}</td>` +
      `<td>${timeFromFrame(iv.start_frame, s).toFixed(3)}</td>` +
      `<td>${timeFromFrame(iv.end_frame, s).toFixed(3)}</td>`;
    const td = document.createElement("td");
    const del = document.createElement("button");
    del.textContent = "删除";
    del.onclick = () => { a.intervals.splice(i, 1); renderTables(); updatePreview(); };
    td.appendChild(del); tr.appendChild(td); it.appendChild(tr);
  });
  const kt = document.querySelector("#kfTable tbody");
  kt.innerHTML = "";
  (a.keyframes || []).forEach((kf, i) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>${kf.frame}</td><td>${kf.box[0]}</td><td>${kf.box[1]}</td><td>${kf.box[2]}</td>` +
      `<td>${boxHeight(kf.box[2], s).toFixed(2)}</td>`;
    const td = document.createElement("td");
    const del = document.createElement("button");
    del.textContent = "删除";
    del.onclick = () => { a.keyframes.splice(i, 1); renderTables(); updatePreview(); };
    td.appendChild(del); tr.appendChild(td); it.appendChild(tr);
  });
}

function currentFrame() { return parseInt(document.getElementById("frameInput").value || "0", 10); }

function updatePreview() {
  const s = samples[state.current];
  const a = ann(s);
  const payload = buildExport(s, a);
  document.getElementById("preview").textContent = JSON.stringify(payload, null, 2);
  document.getElementById("exportHint").textContent =
    "导出模式：" + payload.reference_derivation.mode + " — " + payload.reference_derivation.reason;
}

function buildExport(s, a) {
  const annotator = (a.annotator || "").trim();
  const intervals = a.intervals;
  const keyframes = a.keyframes;
  let mode, reason, reference = null;
  if (a.status === "UNANNOTATED") {
    mode = "NOT_EXPORTABLE";
    reason = "尚未标注；未标注不等于空参考，不能导出为 full/sparse 参考";
  } else if (a.status === "UNCERTAIN") {
    mode = "NOT_EXPORTABLE";
    reason = "标注者标记为不确定；不计入参考";
  } else if (a.status === "NO_HIGHLIGHT") {
    if (!a.confirm_no_highlight) {
      mode = "NOT_EXPORTABLE";
      reason = "无高光需标注者显式勾选确认后才可导出为空真值";
    } else {
      mode = "NO_HIGHLIGHT_EMPTY_GT";
      reason = "标注者确认整段无高光：导出为空帧集合（coverage=full, frames=[]）";
      reference = { coverage: "full", videos: [{ video_id: s.sample_id, coverage: "full", frames: [] }] };
    }
  } else {
    if (!intervals || intervals.length === 0) {
      mode = "NOT_EXPORTABLE";
      reason = "状态为有高光但没有时间区间";
    } else if (!keyframes || keyframes.length === 0) {
      mode = "TEMPORAL_ONLY";
      reason = "只有时间区间、没有构图关键帧：可用于时间诊断，不构成联合指标参考";
    } else {
      mode = "SPARSE_KEYFRAME_GT";
      reason = "稀疏构图关键帧：导出为 coverage=sparse（只有列出的帧被标注）";
      reference = { coverage: "sparse",
                    videos: [{ video_id: s.sample_id, coverage: "sparse",
                               frames: keyframes.map(kf => ({ frame: kf.frame, box_xyw: kf.box })) }] };
    }
  }
  return {
    schema: "p1b_annotation_export_v1",
    run_id: MANIFEST.run_id,
    sample_id: s.sample_id,
    source_group: s.source_group,
    split: "pilot_dev",
    media: { file_name: s.file_name, sha256: s.sha256_local, fps: s.fps, n_frames: s.n_frames,
             source_width: s.source_width, source_height: s.source_height,
             target_ratio_wh: s.target_ratio_wh },
    annotation_status: a.status,
    confirm_no_highlight: !!a.confirm_no_highlight,
    intervals: intervals ? intervals.map(iv => ({ start_frame: iv.start_frame, end_frame: iv.end_frame,
      start_sec: timeFromFrame(iv.start_frame, s), end_sec: timeFromFrame(iv.end_frame, s) })) : null,
    keyframes: keyframes ? keyframes.map(kf => ({ frame: kf.frame, box: kf.box,
      box_height_derived: boxHeight(kf.box[2], s) })) : null,
    frame_provenance: { frame_source: a.frame_source, estimated_error_frames: a.estimated_error_frames,
      global_note: "浏览器 currentTime 只是估算；权威字段是帧号，误差需记录" },
    identity: { annotator: annotator || null, reviewer: (a.reviewer || "").trim() || null },
    notes: a.notes || "",
    exportable_as_reference: reference !== null,
    reference_derivation: { mode: mode, reason: reason, reference: reference },
    not_human_reviewed_unless_recorded: true,
    label_status: "WEAK_HUMAN_SPARSE_PENDING_REVIEW",
  };
}

function download(name, text) {
  const blob = new Blob([text], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = name; a.click();
  URL.revokeObjectURL(url);
}

document.getElementById("useEstimate").onclick = () => {
  const s = samples[state.current], v = document.getElementById("video");
  const f = frameFromTime(v.currentTime, s);
  setFrameField(f, "browser_estimate", 1);
  updatePreview();
};
function step(d) {
  const s = samples[state.current], v = document.getElementById("video");
  const f = Math.max(0, Math.min(s.n_frames - 1, currentFrame() + d));
  v.currentTime = timeFromFrame(f, s);
  setFrameField(f, "frame_step", 0);
  updatePreview();
}
document.getElementById("stepBack10").onclick = () => step(-10);
document.getElementById("stepBack1").onclick = () => step(-1);
document.getElementById("stepFwd1").onclick = () => step(1);
document.getElementById("stepFwd10").onclick = () => step(10);
document.getElementById("alignPts").onclick = () => {
  const s = samples[state.current], v = document.getElementById("video");
  let best = s.verified_sample_frames[0];
  s.verified_sample_frames.forEach(f => {
    if (Math.abs(f.pts_sec - v.currentTime) < Math.abs(best.pts_sec - v.currentTime)) best = f;
  });
  v.currentTime = best.pts_sec;
  setFrameField(best.index, "pts_sample", 0);
  updatePreview();
};
document.getElementById("setStartHere").onclick = () => { document.getElementById("intStart").value = currentFrame(); };
document.getElementById("setEndHere").onclick = () => { document.getElementById("intEnd").value = currentFrame(); };
document.getElementById("addInterval").onclick = () => {
  const s = samples[state.current], a = ann(s);
  const start = parseInt(document.getElementById("intStart").value || "0", 10);
  const end = parseInt(document.getElementById("intEnd").value || "0", 10);
  if (!(end > start)) { alert("结束帧必须大于起始帧"); return; }
  if (start < 0 || end > s.n_frames - 1) { alert("帧号超出 0.." + (s.n_frames - 1)); return; }
  a.intervals = a.intervals || [];
  a.intervals.push({ start_frame: start, end_frame: end });
  renderTables(); updatePreview();
};
function readBox() {
  return [parseInt(document.getElementById("bx").value || "0", 10),
          parseInt(document.getElementById("by").value || "0", 10),
          parseFloat(document.getElementById("bw").value || "0")];
}
function clampBox(box, s) {
  const [tw, th] = s.target_ratio_wh;
  let [x, y, w] = box;
  w = Math.min(w, s.max_legal_crop.max_width, s.source_width);
  const h = w * th / tw;
  x = Math.max(0, Math.min(x, s.source_width - w));
  y = Math.max(0, Math.min(y, s.source_height - h));
  return [Math.round(x), Math.round(y), +w.toFixed(2)];
}
document.getElementById("clampBox").onclick = () => {
  const s = samples[state.current];
  const b = clampBox(readBox(), s);
  document.getElementById("bx").value = b[0]; document.getElementById("by").value = b[1];
  document.getElementById("bw").value = b[2];
};
document.getElementById("addKeyframe").onclick = () => {
  const s = samples[state.current], a = ann(s);
  const box = clampBox(readBox(), s);
  const h = boxHeight(box[2], s);
  if (box[0] + box[2] > s.source_width + 1e-6 || box[1] + h > s.source_height + 1e-6) {
    alert("框超出源帧范围"); return;
  }
  a.keyframes = a.keyframes || [];
  a.keyframes.push({ frame: currentFrame(), box: box });
  renderTables(); updatePreview();
};
document.getElementById("status").onchange = (e) => {
  const a = ann(samples[state.current]);
  a.status = e.target.value;
  if (a.status !== "NO_HIGHLIGHT") a.confirm_no_highlight = false;
  document.getElementById("confirmNoHighlight").checked = !!a.confirm_no_highlight;
  renderSampleList(); updatePreview();
};
document.getElementById("confirmNoHighlight").onchange = (e) => {
  ann(samples[state.current]).confirm_no_highlight = e.target.checked; updatePreview();
};
["annotator", "reviewer", "notes"].forEach(id => {
  document.getElementById(id).oninput = (e) => {
    const a = ann(samples[state.current]);
    if (id === "annotator") a.annotator = e.target.value;
    if (id === "reviewer") a.reviewer = e.target.value;
    if (id === "notes") a.notes = e.target.value;
    updatePreview();
  };
});
document.getElementById("exportOne").onclick = () => {
  const s = samples[state.current];
  const payload = buildExport(s, ann(s));
  if (!payload.identity.annotator) { alert("请先填写标注者（必须为真实执行者）"); return; }
  download(`${s.sample_id}_annotation.json`, JSON.stringify(payload, null, 2));
};
document.getElementById("exportAll").onclick = () => {
  const out = [];
  samples.forEach(s => {
    const a = ann(s);
    const payload = buildExport(s, a);
    if (payload.annotation_status !== "UNANNOTATED" && payload.identity.annotator) out.push(payload);
  });
  download("p1b_annotations_export.json", JSON.stringify(
    { schema: "p1b_annotation_bundle_v1", run_id: MANIFEST.run_id, exports: out }, null, 2));
};
document.getElementById("copyJson").onclick = () => {
  const s = samples[state.current];
  navigator.clipboard.writeText(JSON.stringify(buildExport(s, ann(s)), null, 2));
};
document.getElementById("resetOne").onclick = () => {
  const s = samples[state.current];
  if (confirm("清空 " + s.sample_id + " 的标注？")) { state.annotations[s.sample_id] = blank(); loadSample(); }
};
loadSample();
</script>
</body>
</html>
""".replace("__MANIFEST__", data)


def build_readme(manifest: dict) -> str:
    rows = "\n".join(
        f"| {s['sample_id']} | `{s['source_group']}` | {s['source_width']}x{s['source_height']} | "
        f"{s['fps']:.3f} | {s['n_frames']} | {s['target_ratio_wh'][0]}:{s['target_ratio_wh'][1]} | "
        f"{s['bytes']/1048576:.2f} MiB | {s['sha256_local'][:12]}… |"
        for s in manifest["samples"])
    return f"""# P1b 离线标注说明

run_id：`{RUN_ID}`；样本：8 个来源组（4 个目标 16:9、4 个目标 9:16），全部标记 `pilot_dev`。

## 打开方式

直接双击 `annotate.html`（纯 `file://`，不需要服务器、不联网）。若浏览器限制本地视频，
用 `python -m http.server` 起一个本地静态服务并从 `http://127.0.0.1:8000/annotate.html` 打开即可
（页面本身不发起任何外部请求）。

## 媒体清单

| 样本 | 来源组(YouTube) | 源分辨率 | fps | 帧数 | 目标比例 | 大小 | SHA-256 |
|---|---|---|---|---|---|---|---|
{rows}

（完整字段见 `pilot_manifest.json`；每个样本的远端哈希、PTS 统计、12 个已校验采样帧都在里面。）

## 标注状态机（重要）

| 状态 | 含义 | 能否导出为参考 |
|---|---|---|
| `UNANNOTATED`（默认） | 尚未标注 | **否**；导出 `NOT_EXPORTABLE`，且 `intervals/keyframes = null`（不是 `[]`） |
| `HAS_HIGHLIGHT` + 有时间区间 + 有关键帧 | 稀疏构图标注 | 导出 `coverage=sparse`（只有列出的帧被标注） |
| `HAS_HIGHLIGHT` + 只有时间区间 | 仅时间标注 | `TEMPORAL_ONLY`：只能做时间诊断，**不构成联合指标参考** |
| `NO_HIGHLIGHT` + 勾选确认 | 标注者主动确认整段无高光 | 导出空帧集合（`coverage=full, frames=[]`） |
| `UNCERTAIN` | 不确定 | **否**；不计入参考 |

- 未标注 ≠ 空。只有真实标注者勾选“确认无高光”才会产生空真值。
- 复核者字段默认留空；**没有人工复核就不要填写**，页面不会自动填。
- 页面导出的 `label_status` 固定为 `WEAK_HUMAN_SPARSE_PENDING_REVIEW`，人工复核前不得升格。

## 帧号与误差

浏览器 `currentTime` 不是精确帧号。页面做法：

1. 顶部按钮是**已用容器 PTS 校验过**的采样帧，点击可跳到精确位置；
2. `帧号` 输入框是权威字段，可用 “用当前时间估算帧号” 填入估算值（此时记录
   `frame_source=browser_estimate`、`estimated_error_frames=1`）；
3. `±1 / ±10 帧` 按钮按 `t = frame / fps` 跳转；
4. 目标比例约束：框高按 `h = w · th / tw` 推导，宽度不得超过 `max_legal_crop.max_width`。

## 导出

- `导出本样本 JSON`：单样本，含 `reference_derivation`（模式 + 理由 + 可直接喂给 P1a 的参考片段）。
- `导出全部已标注样本`：只导出**已标注且填了标注者**的样本，未标注样本不会进入导出。
- 导出文件请放在 `reports/round6_score_alignment/phase1b/annotations/` 下再用
  `round6_score_alignment/p1b/validate_exports.py` 校验（含未标注≠空、框界内/比例、身份、时间映射）。

## 禁止

- 不得把本页或任何帧/视频上传到外部服务；
- 不得用测试视频做标注；
- 不得由模型代替人工填写高光或构图语义；本页面初始状态即为“未标注”，这是有意为之。
"""


def main() -> int:
    manifest = build_manifest()
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    HTML.write_text(build_html(manifest), encoding="utf-8")
    README.write_text(build_readme(manifest), encoding="utf-8")
    print(json.dumps({"manifest": str(MANIFEST), "html": str(HTML), "readme": str(README),
                      "samples": len(manifest["samples"]),
                      "bytes": manifest["totals"]["bytes"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
