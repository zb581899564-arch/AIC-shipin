from pathlib import Path
from datetime import datetime, timezone
from collections import Counter
import hashlib
import json
import math
import av
from PIL import Image, ImageDraw, ImageFont

root = Path(__file__).resolve().parent
project = root.parent / "antigravity_label_probe_20261009"
input_dir = project / "input/native_video_tvsum_v1"
output_dir = project / "output/native_video_tvsum_v1"
manifest = json.loads((input_dir / "manifest.json").read_text(encoding="utf-8"))
label_path = output_dir / "highlights.json"
labels = json.loads(label_path.read_text(encoding="utf-8-sig"))
video = input_dir / manifest["file"]
duration = manifest["duration_seconds_metadata"]
issues = []
if labels.get("source_id") != manifest["source_id"]:
    issues.append("SOURCE_ID_MISMATCH")
if labels.get("native_video_accepted") is not True or labels.get("actual_tool_name") != "view_file":
    issues.append("NATIVE_INPUT_NOT_DECLARED_ACCEPTED")
events = labels.get("events", [])
for index, event in enumerate(events):
    start, end = event.get("start_seconds"), event.get("end_seconds_exclusive")
    if (not isinstance(start, (int, float)) or not isinstance(end, (int, float)) or
        not math.isfinite(start) or not math.isfinite(end) or not 0 <= start < end <= duration):
        issues.append({"event_index": index, "issue": "INVALID_TIME_INTERVAL", "start": start, "end": end})
    if event.get("state") not in ("KEEP", "UNKNOWN"):
        issues.append({"event_index": index, "issue": "INVALID_STATE"})
    if not event.get("event_type") or not event.get("visible_evidence"):
        issues.append({"event_index": index, "issue": "MISSING_EVENT_TEXT"})
    uncertainty = event.get("boundary_uncertainty_seconds")
    if uncertainty is not None and (not isinstance(uncertainty, (int, float)) or not math.isfinite(uncertainty) or uncertainty < 0):
        issues.append({"event_index": index, "issue": "INVALID_BOUNDARY_UNCERTAINTY"})
times = labels.get("observed_timestamps_seconds", [])
if any(not isinstance(t, (int, float)) or not math.isfinite(t) or t < 0 or t > duration for t in times):
    issues.append("INVALID_REPORTED_OBSERVATION_TIMESTAMP")
video_sha = hashlib.sha256(video.read_bytes()).hexdigest()
if video_sha != manifest["media_sha256"]:
    issues.append("SOURCE_SHA_CHANGED")
intervals = sorted((e["start_seconds"], e["end_seconds_exclusive"]) for e in events)
union = []
for start, end in intervals:
    if union and start <= union[-1][1]:
        union[-1][1] = max(end, union[-1][1])
    else:
        union.append([start, end])
receipt = {"status": "PASS_NATIVE_MP4_RAW_SCHEMA_TIME_BOUNDS_AND_SOURCE_IDENTITY" if not issues else "NATIVE_LABEL_ISSUES",
           "utc": datetime.now(timezone.utc).isoformat(), "input_mode": "Direct native MP4 from folder",
           "model_ui": "Gemini 3.8 Flash High", "source_id": manifest["source_id"],
           "source_duration_seconds_metadata": duration, "source_bytes": video.stat().st_size,
           "source_sha256": video_sha, "native_mp4_read_entry_observed_in_ui": True,
           "native_tool_name_declared": labels.get("actual_tool_name"),
           "event_count": len(events), "event_states": dict(Counter(e["state"] for e in events)),
           "union_selected_seconds": sum(end - start for start, end in union),
           "reported_observation_timestamps_count": len(times),
           "reported_observation_scope": labels.get("observation_scope"),
           "full_decode_and_continuous_model_observation_independently_verified": False,
           "event_boundary_accuracy": "NOT_MEASURED_COARSE_MODEL_RECOMMENDATIONS",
           "issues": issues,
           "raw_files": [{"path": str(p), "bytes": p.stat().st_size,
                          "sha256": hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(output_dir.iterdir()) if p.is_file()]}
(root / "native_video_acceptance.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
if issues:
    print(json.dumps(receipt, ensure_ascii=False))
    raise SystemExit(1)

# Three fixed event positions, each with start/middle/end native source observations.
selected_indices = [0, len(events) // 2, len(events) - 1]
targets = []
for index in selected_indices:
    event = events[index]
    start, end = event["start_seconds"], event["end_seconds_exclusive"]
    for position, stamp in (("start", start + 0.2), ("mid", (start + end) / 2), ("end", end - 0.2)):
        targets.append({"event_index": index, "position": position, "requested_seconds": stamp,
                        "event_type": event["event_type"]})
targets.sort(key=lambda t: t["requested_seconds"])
review = root / "native_visual_review"
review.mkdir(exist_ok=False)
remaining = iter(targets)
target = next(remaining, None)
records = []
with av.open(str(video)) as container:
    stream = container.streams.video[0]
    for ordinal, frame in enumerate(container.decode(stream)):
        stamp = float(frame.pts * frame.time_base)
        while target is not None and stamp >= target["requested_seconds"]:
            rgb = frame.to_ndarray(format="rgb24")
            image = Image.fromarray(rgb)
            name = f"event_{target['event_index']:02d}_{target['position']}.png"
            image.save(review / name)
            records.append({**target, "file": name, "source_frame_index": ordinal,
                            "pts": frame.pts, "time_base": [frame.time_base.numerator, frame.time_base.denominator],
                            "actual_pts_seconds": stamp, "rgb24_sha256": hashlib.sha256(rgb.tobytes()).hexdigest()})
            target = next(remaining, None)
        if target is None:
            break
assert len(records) == 9
(review / "manifest.json").write_text(json.dumps({"purpose": "Representative diagnostic review, not independent ground truth",
    "selection_policy": "First, middle and last event; first native PTS at or after start+0.2, midpoint, end-0.2",
    "frames": records}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
preview = Image.new("RGB", (990, 675), "#f5f7f9")
draw = ImageDraw.Draw(preview)
font = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 12)
for index, record in enumerate(records):
    x, y = (index % 3) * 330, (index // 3) * 225
    draw.text((x + 5, y + 2), f"事件{record['event_index']+1} {record['position']}  PTS {record['actual_pts_seconds']:.3f}s", fill="#16202c", font=font)
    image = Image.open(review / record["file"]).convert("RGB")
    preview.paste(image.resize((320, 180), Image.Resampling.LANCZOS), (x + 5, y + 24))
    draw.text((x + 5, y + 206), record["event_type"], fill="#16202c", font=font)
preview.save(root / "native_highlight_review.png")
print(json.dumps({k: v for k, v in receipt.items() if k not in ("raw_files", "reported_observation_scope")}, ensure_ascii=False))
