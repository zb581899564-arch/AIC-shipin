#!/usr/bin/env python3
"""Meaningful fail-closed and safe metadata/extraction tests; synthetic only."""
from __future__ import annotations

import argparse
import copy
import io
import json
import zipfile
from pathlib import Path

from a_contract import compose, keyset, read_rows, select_frames, validate_manifest, validate_predictions, write_json
from inspect_first_jsonl import inspect_keys
from prepare_rematch_m0 import paired_members, read_approved_metadata


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", type=Path, required=True)
    ap.add_argument("--fixtures", type=Path, required=True)
    ap.add_argument("--report", type=Path, required=True)
    args = ap.parse_args()
    m = json.loads(args.manifest.read_text(encoding="utf-8"))
    temporal = read_rows(args.fixtures/"temporal.jsonl")
    selected = select_frames(m, temporal)
    shots, requests, outputs = [read_rows(args.fixtures/name) for name in
                                ("shots.jsonl", "anchor_requests.jsonl", "anchor_output.jsonl")]
    rows, prov = compose(m, selected, shots, requests, outputs)
    results = []
    def reject(name, operation):
        try:
            operation()
        except (ValueError, KeyError):
            results.append({"test": name, "pass": True})
        else:
            raise AssertionError(name+" failed open")
    unknown = copy.deepcopy(m); unknown["input_contract"]["status"] = "UNKNOWN"
    reject("unknown_input_role", lambda: validate_manifest(unknown))
    labels = copy.deepcopy(m); labels["records"][0]["segments"] = [[0, 1]]
    reject("label_field_in_clean_manifest", lambda: validate_manifest(labels))
    duplicate = copy.deepcopy(m); duplicate["records"][1]["video_id"] = duplicate["records"][0]["video_id"]
    reject("duplicate_video_input", lambda: validate_manifest(duplicate))
    bad = copy.deepcopy(temporal); bad[0]["windows"][0]["status"] = "PARSE_FAILURE"
    reject("parse_failure_is_not_empty", lambda: select_frames(m, bad))
    empty = copy.deepcopy(temporal); empty[0]["windows"][0]["parsed_segments"] = []
    reject("legacy_empty_unsupported", lambda: select_frames(m, empty))
    reject("missing_video_output", lambda: select_frames(m, temporal[:-1]))
    reject("duplicate_anchor_output", lambda: compose(m, selected, shots, requests, outputs+[outputs[0]]))
    pixel = copy.deepcopy(outputs); pixel[0]["decoded_pixel_sha256"] = "0"*64
    reject("anchor_pixel_identity_changed", lambda: compose(m, selected, shots, requests, pixel))
    float_box = copy.deepcopy(outputs); float_box[0]["box_xyw"][0] = 1.5
    reject("non_integer_anchor_box", lambda: compose(m, selected, shots, requests, float_box))
    reject("missing_shot_frame", lambda: compose(m, selected, shots[:-1], requests, outputs))
    bad_pred = copy.deepcopy(rows); bad_pred[0]["predictions"].append(bad_pred[0]["predictions"][0])
    reject("duplicate_final_frame", lambda: validate_predictions(m, bad_pred, keyset(selected), prov))
    raw = b'{"targetRatioWH":[9,16],"predictions":["SECRET_LABEL_VALUE"]}'
    gate = inspect_keys(io.BytesIO(raw))
    assert gate["status"] == "BLOCK_SUSPECTED_LABEL_KEY" and gate["bytes_consumed"] == raw.index(b'["SECRET')
    assert "SECRET" not in json.dumps(gate)
    results.append({"test": "stop_before_suspect_value_and_no_values_reported", "pass": True})
    buffer = io.BytesIO()
    samples = {"0.jsonl": b'{"targetRatioWH":[9,16]}\n', "1.jsonl": b'{"targetRatioWH":[16,9],"video_id":"1"}\n',
               "2.jsonl": b'{"targetRatioWH":[9,16],"segments":["SECRET"]}\n',
               "3.jsonl": b'{"targetRatioWH":[9,16]}\n{"cropRois":["SECRET"]}\n',
               "4.jsonl": b'{"targetRatioWH":[9,16],"video_id":"004"}\n',
               "5.jsonl": b'{"targetRatioWH":[18,32]}\n', "6.jsonl": b'{"targetRatioWH":[true,16]}\n',
               "7.jsonl": b'{"targetRatioWH":[9,16],"targetRatioWH":[16,9]}\n'}
    with zipfile.ZipFile(buffer, "w") as z:
        for name, data in samples.items():
            z.writestr(name, data)
    buffer.seek(0)
    with zipfile.ZipFile(buffer) as z:
        for stem in ("0", "1"):
            data, g = read_approved_metadata(z, z.getinfo(stem+".jsonl"), stem)
            assert data is not None and g["values_reported"] == 0
            results.append({"test": "approved_metadata_"+stem, "pass": True})
        for stem in ("2", "3", "4", "5", "6", "7"):
            data, g = read_approved_metadata(z, z.getinfo(stem+".jsonl"), stem)
            assert data is None and "SECRET" not in json.dumps(g)
            results.append({"test": "block_bad_metadata_"+stem, "pass": True})
    def infos(names):
        return [zipfile.ZipInfo(x) for x in names]
    reject("path_traversal_archive", lambda: paired_members(infos(["../../0.mp4", "0.jsonl"]), 1))
    reject("duplicate_archive_stem", lambda: paired_members(infos(["v/0.mp4", "other/0.mp4", "j/0.jsonl"]), 1))
    reject("unpaired_archive_stem", lambda: paired_members(infos(["v/0.mp4", "j/1.jsonl"]), 1))
    v, j = paired_members(infos(["v/000.mp4", "j/000.jsonl", "__MACOSX/._000.mp4", ".DS_Store"]), 1)
    assert set(v) == set(j) == {"000"}
    results.append({"test": "leading_zero_id_preserved_apple_metadata_ignored", "pass": True})
    report = {"status": "PASS_CPU_CONTRACT_AND_METADATA_SAFETY", "tests": len(results), "results": results,
              "cached_non_test_selected_frames": len(selected), "cached_non_test_anchors": len(outputs),
              "cached_non_test_videos": len(rows), "models_run": False, "contest_member_content_read": False}
    write_json(args.report, report)
    print(json.dumps(report, ensure_ascii=False))


if __name__ == "__main__":
    main()
