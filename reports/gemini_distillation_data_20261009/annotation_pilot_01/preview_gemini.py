"""Render raw Gemini crop suggestions without changing any coordinates."""
from pathlib import Path
import json
from PIL import Image, ImageDraw, ImageFont

root = Path(__file__).resolve().parent
raw = root.parent.parent / "antigravity_label_probe_20261009/output/real_tvsum_v1"
rows = []
for index in range(8):
    rows.extend(json.loads((raw / f"batch_{index:02d}.json").read_text(encoding="utf-8-sig"))["frames"])
by_index = {r["local_index"]: r for r in rows}
selected = [0, 8, 24, 32, 47]
preview = Image.new("RGB", (460, 1070), "#f5f7f9")
draw = ImageDraw.Draw(preview)
font = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 13)
for row_index, index in enumerate(selected):
    row = by_index[index]
    original = Image.open(root / "input" / f"f{index:03d}.png").convert("RGB")
    crop = next(c for c in row["crops"] if c["targetRatioWH"] == [9, 16])
    top = row_index * 214
    draw.text((8, top + 4), f"f{index:03d} / 源帧 {row['frame_index']} / {row['pts_seconds']:.4f}s", fill="#16202c", font=font)
    annotated = original.copy()
    if crop["state"] == "CROP":
        x, y, width = crop["box_xyw"]
        height = width * 16 / 9
        outline = ImageDraw.Draw(annotated)
        outline.rectangle((x, y, x + width - 1, y + height - 1), outline="#00ffff", width=3)
        portrait = original.transform((101, 180), Image.Transform.EXTENT,
            (x, y, x + width, y + height), Image.Resampling.BICUBIC)
        preview.paste(portrait, (342, top + 28))
    else:
        draw.text((342, top + 100), "UNKNOWN", fill="#16202c", font=font)
    preview.paste(annotated.resize((320, 180), Image.Resampling.LANCZOS), (8, top + 28))
    draw.text((235, top + 4), "Gemini原始框       9:16结果", fill="#16202c", font=font)
preview.save(root / "gemini_crop_preview.png")
with (root / "gemini_labels.jsonl").open("x", encoding="utf-8") as handle:
    for row in rows:
        handle.write(json.dumps({"annotator": "ANTIGRAVITY_GEMINI_3_8_FLASH_HIGH_UI", **row}, ensure_ascii=False) + "\n")
print(json.dumps({"frames": len(rows), "preview": str(root / "gemini_crop_preview.png")}, ensure_ascii=False))
