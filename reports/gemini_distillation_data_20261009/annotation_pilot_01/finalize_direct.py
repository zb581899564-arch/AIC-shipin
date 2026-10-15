from pathlib import Path
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from PIL import Image, ImageDraw, ImageFont

root = Path(__file__).resolve().parent
raw = root / "codex_raw"
manifest = json.loads((root / "input/manifest.json").read_text(encoding="utf-8"))
rows = []
for index in range(8):
    rows.extend(json.loads((raw / f"batch_{index:02d}.json").read_text(encoding="utf-8"))["frames"])
assert [r["local_index"] for r in rows] == list(range(48))
summary = {"source_id": manifest["source_id"], "source_frame_range": [300, 348],
           "frame_range_end_exclusive": True, "observed_files": [r["observed_file"] for r in rows],
           "observed_count": 48, "output_frame_count": 48, "crops_count": 96,
           "highlight_state_counts": dict(Counter(r["highlight_state"] for r in rows)),
           "crop_unknown_count": 0, "annotator": "CURRENT_CODEX_ASSISTANT_DIRECT_VISUAL",
           "gemini_generated": False, "audio_provided": False,
           "clip_events": [{"start_frame": 300, "end_frame_exclusive": 348,
                            "description": "户外树下聚集的人群；蓝衣前景逐渐移开，后方人物和轻微手势露出。仅覆盖已观察48帧。",
                            "highlight_state": "NO_HIGHLIGHT"}],
           "limitations": ["没有音频；只观察约1.60秒短片段，不判断整部视频。",
                           "源画面自身有截头、遮挡和模糊，无法恢复画面外内容。",
                           "竖幅主体在可见人群变化时切换，逐帧建议没有进行轨迹平滑。",
                           "没有独立人工构图参考，未测准确率或美学优劣。"],
           "utc": datetime.now(timezone.utc).isoformat()}
with (raw / "summary.json").open("x", encoding="utf-8") as handle:
    json.dump(summary, handle, ensure_ascii=False, indent=2)
    handle.write("\n")
with (root / "direct_labels.jsonl").open("x", encoding="utf-8") as handle:
    for row in rows:
        handle.write(json.dumps({"annotator": summary["annotator"], "gemini_generated": False, **row}, ensure_ascii=False) + "\n")
receipt = {"status": "48_ACTUAL_ORIGINAL_PNG_VISUAL_OBSERVATIONS_AND_RAW_BATCHES_SAVED",
           "utc": summary["utc"], "batch_size": 6, "batches": 8, "actual_view_image_files": summary["observed_files"],
           "observation_evidence": "This Codex tool transcript contains eight batches of six view_image returns, individually labelled f000 through f047",
           "gemini_output_files": 0, "direct_annotator": summary["annotator"],
           "raw_sha256": {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(raw.glob("*.json"))}}
(root / "direct_observation_receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
selected = [0, 8, 24, 32, 47]
preview = Image.new("RGB", (460, 1070), "#f5f7f9")
draw = ImageDraw.Draw(preview)
font = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 13)
for row_index, index in enumerate(selected):
    row = rows[index]
    original = Image.open(root / "input" / row["observed_file"]).convert("RGB")
    x, y, width = row["crops"][1]["box_xyw"]
    height = width * 16 / 9
    annotated = original.copy()
    outline = ImageDraw.Draw(annotated)
    outline.rectangle((x, y, x + width - 1, y + height - 1), outline="#00ffff", width=3)
    top = row_index * 214
    draw.text((8, top + 4), f"f{index:03d} / 源帧 {row['frame_index']} / {row['pts_seconds']:.4f}s", fill="#16202c", font=font)
    preview.paste(annotated.resize((320, 180), Image.Resampling.LANCZOS), (8, top + 28))
    portrait = original.transform((101, 180), Image.Transform.EXTENT, (x, y, x + width, y + height), Image.Resampling.BICUBIC)
    preview.paste(portrait, (342, top + 28))
    draw.text((235, top + 4), "原图+竖幅框       9:16结果", fill="#16202c", font=font)
preview.save(root / "direct_crop_preview.png")
print(json.dumps({"frames": 48, "crops": 96, "summary": str(raw / "summary.json"), "preview": str(root / "direct_crop_preview.png")}, ensure_ascii=False))
