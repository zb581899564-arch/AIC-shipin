"""Metadata only. Never downloads media or alters original annotations."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "reports/scoring_spatial_audit_20261013_v1/fcdb_native_ratio_06"
REV = "546a02124e137be508d52104c667cab05e3aae48"
FILES = {
    "cropping_training_set.json": (306948, "651fde21a3e38adafd7565eafde150d6efb7dd9e"),
    "cropping_testing_set.json": (77377, "3e1e6c12482c3229593edc75ec90f46ff902cc36"),
}


def main():
    if OUT.exists():
        raise RuntimeError("Output exists; do not repeat successful metadata work")
    OUT.mkdir()
    receipt = {"utc": datetime.now(timezone.utc).isoformat(), "revision": REV,
               "scope": "ORIGINAL_ANNOTATION_GEOMETRY_COUNTS_ONLY_NO_MEDIA_OR_MODEL",
               "files": [], "media_downloads": 0, "model_calls": 0}
    try:
        rows = []
        groups = {}
        for name, (size, blob) in FILES.items():
            url = f"https://raw.githubusercontent.com/yiling-chen/flickr-cropping-dataset/{REV}/{name}"
            with urlopen(Request(url, headers={"User-Agent": "AIC-reference-metadata-audit"}), timeout=40) as response:
                raw = response.read(size + 1)
                final_url = response.url
            if len(raw) != size:
                raise ValueError(f"Unexpected size for {name}")
            actual_blob = hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest()
            if actual_blob != blob:
                raise ValueError(f"Pinned Git blob mismatch for {name}")
            (OUT / name).write_bytes(raw)
            group = json.loads(raw)
            if not isinstance(group, list):
                raise ValueError(f"Annotation root is not a list: {name}")
            receipt["files"].append({"name": name, "url": url, "final_url": final_url,
                                     "bytes": len(raw), "git_blob": actual_blob,
                                     "sha256": hashlib.sha256(raw).hexdigest()})
            groups[name] = len(group)
            rows.extend(group)
        ids = []
        invalid = 0
        ratios = {"9:16": {"exact_ids": [], "within_one_pixel_count": 0},
                  "16:9": {"exact_ids": [], "within_one_pixel_count": 0}}
        for row in rows:
            crop = row.get("crop")
            photo_id = row.get("flickr_photo_id")
            url = row.get("url", "")
            valid = (type(photo_id) is int and isinstance(crop, list) and len(crop) == 4
                     and all(type(v) is int for v in crop) and min(crop[:2]) >= 0
                     and min(crop[2:]) > 0 and isinstance(url, str)
                     and "staticflickr.com/" in url)
            if not valid:
                invalid += 1
                continue
            ids.append(photo_id)
            w, h = crop[2:]
            for label, tw, th in (("9:16", 9, 16), ("16:9", 16, 9)):
                error = abs(w * th - h * tw)
                if error == 0:
                    ratios[label]["exact_ids"].append(photo_id)
                if error <= tw:
                    ratios[label]["within_one_pixel_count"] += 1
        for value in ratios.values():
            value["exact_count"] = len(value["exact_ids"])
            value["exact_ids"].sort()
        result = {"scope": receipt["scope"], "rows": len(rows), "groups": groups,
                  "invalid_schema_rows": invalid, "duplicate_source_ids": len(ids) - len(set(ids)),
                  "coordinate_contract": "original x,y,width,height; no conversion or alteration",
                  "ratios": ratios,
                  "near_ratio_not_admitted_as_exact_truth": True,
                  "algorithm_quality_evaluated": False, "independent_cohort_registered": False,
                  "media_or_model_admitted": False,
                  "gate_decision": "METADATA_ONLY_NO_EXECUTION_ADMISSION"}
        (OUT / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        receipt["status"] = "COMPLETED"
        (OUT / "receipt.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"rows": result["rows"], "schema_errors": invalid,
                          "duplicate_ids": result["duplicate_source_ids"],
                          "ratios": {key: {k: v for k, v in value.items() if k != "exact_ids"}
                                     for key, value in ratios.items()}}, ensure_ascii=False))
    except Exception as exc:
        receipt["status"] = "FAILED"
        receipt["error"] = f"{type(exc).__name__}: {exc}"
        (OUT / "failure.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        raise


if __name__ == "__main__":
    main()
