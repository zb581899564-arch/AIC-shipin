from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

from PIL import Image, ImageDraw

from reference_loader import sha256_file, validate_manifest

SEED = "round6-p2r-gnmc-v1"


def stable_select(rows: list[dict], split: str, n: int) -> list[dict]:
    eligible = [r for r in rows if "16:9" in r.get("crop_bboxes", {})]
    return sorted(
        eligible,
        key=lambda r: hashlib.sha256(f"{SEED}|{split}|{r['filename']}".encode()).hexdigest(),
    )[:n]


def convert_record(record: dict, split: str, image_path: Path, media_rel: str) -> tuple[dict, dict]:
    with Image.open(image_path) as im:
        width, height = im.size
    x1n, y1n, x2n, y2n = map(float, record["crop_bboxes"]["16:9"])
    original = [x1n, y1n, x2n, y2n]
    box = [x1n * width, y1n * height, (x2n - x1n) * width, (y2n - y1n) * height]
    item_id = f"gnmc:{split}:{record['filename']}"
    item = {
        "schema": "p2r_reference_item_v1",
        "dataset": "GNMC-0.0.1",
        "item_id": item_id,
        "source_group": item_id,
        "source_group_basis": "publisher split plus filename; no per-image origin URL is present",
        "source_group_independence": "UNKNOWN_BEYOND_FILE_IDENTITY",
        "split": "dev" if split == "validation" else "sealed_holdout",
        "target_ratio_wh": [16, 9],
        "media_rel_path": media_rel.replace("\\", "/"),
        "media_sha256": sha256_file(image_path),
        "source_width": width,
        "source_height": height,
        "reference_boxes": [box],
        "annotation_semantics": "single crop made by an experienced editor for the declared aspect ratio",
        "annotation_source": "GNMC publisher release; one editor per image/aspect ratio; no independent second review recorded",
        "coverage": "single_image",
        "evidence_tier": "TIER_B_PUBLIC_ANNOTATION_LIMITED",
        "license": "PolyForm-Noncommercial-1.0.0",
        "usage_scope": "local noncommercial diagnostic only; no redistribution, training, submission, or commercial use approved",
        "original_split": split,
        "original_filename": record["filename"],
    }
    conversion = {
        "item_id": item_id,
        "original_format": "normalized [x1,y1,x2,y2]",
        "original_bbox": original,
        "source_dimensions": [width, height],
        "canonical_format": "source-pixel float [x,y,w,h]",
        "canonical_bbox": box,
        "target_ratio_wh": [16, 9],
        "no_rounding_applied": True,
    }
    return item, conversion


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")


def contact_sheet(items: list[dict], media_root: Path, out: Path) -> None:
    panels = []
    for item in items:
        with Image.open(media_root / item["media_rel_path"]) as src:
            image = src.convert("RGB")
        scale = min(480 / image.width, 320 / image.height, 1.0)
        resized = image.resize((round(image.width * scale), round(image.height * scale)))
        draw = ImageDraw.Draw(resized)
        x, y, w, h = item["reference_boxes"][0]
        draw.rectangle((x * scale, y * scale, (x + w) * scale, (y + h) * scale), outline=(255, 0, 0), width=3)
        canvas = Image.new("RGB", (500, 360), "white")
        canvas.paste(resized, ((500 - resized.width) // 2, 20))
        ImageDraw.Draw(canvas).text((10, 340), item["item_id"], fill="black")
        panels.append(canvas)
    sheet = Image.new("RGB", (1000, 720), (235, 235, 235))
    for i, panel in enumerate(panels[:4]):
        sheet.paste(panel, ((i % 2) * 500, (i // 2) * 360))
    sheet.save(out, quality=94)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--zip", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    media_root = args.out
    with zipfile.ZipFile(args.zip) as z:
        validation = json.loads(z.read("GNMC/json/validation.json"))
        test = json.loads(z.read("GNMC/json/test.json"))
        selected = [("validation", r) for r in stable_select(validation, "validation", 4)]
        selected += [("test", r) for r in stable_select(test, "test", 4)]
        for name in ["GNMC/LICENSE.txt", "GNMC/README.md", "GNMC/json/validation.json", "GNMC/json/test.json"]:
            target = args.out / "raw_metadata" / Path(name).name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(z.read(name))
        manifests, conversions = [], []
        for split, record in selected:
            member = f"GNMC/{split}/{record['filename']}"
            rel = f"media/{split}/{record['filename']}"
            target = args.out / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(z.read(member))
            item, conversion = convert_record(record, split, target, rel)
            manifests.append(item)
            conversions.append(conversion)
    dev = [r for r in manifests if r["split"] == "dev"]
    holdout = [r for r in manifests if r["split"] == "sealed_holdout"]
    write_jsonl(args.out / "pilot_manifest.jsonl", manifests)
    write_jsonl(args.out / "dev_manifest.jsonl", dev)
    write_jsonl(args.out / "sealed_holdout_manifest.jsonl", holdout)
    write_jsonl(args.out / "conversion_records.jsonl", conversions)
    result = validate_manifest(manifests, media_root)
    (args.out / "manifest_validation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    contact_sheet(dev, media_root, args.out / "dev_visual_contact.jpg")
    print(json.dumps({"selected": len(manifests), "dev": len(dev), "sealed_holdout": len(holdout), "validation": result}, ensure_ascii=False))
    return 0 if result["status"] == "OK" else 2


if __name__ == "__main__":
    raise SystemExit(main())
