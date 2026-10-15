"""Serialize individually supplied visual judgments; no inference or interpolation."""
from pathlib import Path
from datetime import datetime, timezone
import json
import sys

root = Path(__file__).resolve().parent
manifest = json.loads((root / "input/manifest.json").read_text(encoding="utf-8"))
request = json.load(sys.stdin)
batch_index = request["batch_index"]
judgments = request["judgments"]
if [r["local_index"] for r in judgments] != list(range(batch_index * 6, batch_index * 6 + 6)):
    raise ValueError("Require exactly six explicit observations in original order")
frames = []
for judgment in judgments:
    source = manifest["frames"][judgment["local_index"]]
    crops = judgment.get("crops")
    if crops is None:
        crops = [{"targetRatioWH": [16, 9], "state": "CROP", "box_xyw": judgment["wide_box"],
                  "reason": judgment["wide_reason"]},
                 {"targetRatioWH": [9, 16], "state": "CROP", "box_xyw": judgment["portrait_box"],
                  "reason": judgment["portrait_reason"]}]
    frames.append({"local_index": source["local_index"], "frame_index": source["frame_index"],
                   "pts_seconds": source["pts_seconds"], "observed_file": source["file"],
                   "visible_content": judgment["visible_content"],
                   "highlight_state": judgment["highlight_state"],
                   "highlight_reason": judgment["highlight_reason"],
                   "crops": crops})
output = root / "codex_raw"
output.mkdir(exist_ok=True)
path = output / f"batch_{batch_index:02d}.json"
with path.open("x", encoding="utf-8") as handle:
    json.dump({"annotator": "CURRENT_CODEX_ASSISTANT_DIRECT_VISUAL",
               "gemini_generated": False, "utc": datetime.now(timezone.utc).isoformat(),
               "visual_observation": "Each named PNG actually returned by view_image before this batch was written",
               "frames": frames}, handle, ensure_ascii=False, indent=2)
    handle.write("\n")
print(json.dumps({"path": str(path), "frames": len(frames)}, ensure_ascii=False))
