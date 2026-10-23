"""Synthetic frozen-field asset/domain tests; no model or media decoding."""
from contextlib import contextmanager
import copy
from fractions import Fraction
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import zipfile

from improvement.final_sprint_v1 import frozen_field as field
from improvement.final_sprint_v1.contracts import ref, save_new


class FrozenFieldTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name).resolve()
        self.run = self.root / "original"
        self.original = self.run / "b_score_aligned_package_v4"
        self.pts_dir = self.run / "baseline_a_pts_v1"
        for directory, names in (
            (self.original, ("field_contract.py", "package_contract.py")),
            (self.pts_dir, ("pts_contract.py", "a_contract.py")),
            (self.pts_dir / "vendor", ("p2j_core.py", "independent_validate.py")),
            (self.pts_dir / "vendor/frozen_strict_loader", ("__init__.py",)),
        ):
            for name in names:
                self.write(directory / name, b"# synthetic immutable CPU dependency\n")
        self.config = self.write(self.original / "config.json", {})
        self.sources, records, clock_document = [], [], {}
        self.old_clocks = {}
        self.field_rows = []
        for sid, count in (("0", 3), ("1", 2)):
            media = self.write(self.root / (sid + ".media"), b"synthetic media identity " + sid.encode())
            pts = [str(Fraction(frame, 30)) for frame in range(count)]
            end = str(Fraction(count, 30))
            clock_document[sid] = dict(source_sha256=media["sha256"], normalized_exact_pts=pts,
                                       physical_end_exact=end)
            self.old_clocks[sid] = dict(pts=list(map(Fraction, pts)), duration=Fraction(end))
            record = dict(video_id=sid, source_sha256=media["sha256"], source_path=media["path"],
                          n_frames=count, width=100, height=80, targetRatioWH=[16, 9])
            records.append(record)
            self.sources.append(dict(video_id=sid, media=media, width=100, height=80,
                                     n_frames=count, targetRatioWH=[16, 9]))
            for frame in range(2):
                self.field_rows.append(dict(video_id=sid, source_frame=frame))
        self.clocks = self.write(self.root / "source_clocks.json", clock_document)
        for source in self.sources:
            source["clock"] = dict(self.clocks, source_key=source["video_id"])
        arrays = [self.write(self.root / (sid + "_arrays.json"), {"synthetic": sid}) for sid in ("0", "1")]
        registry = self.write(self.root / "clock_registry.json",
                              {"records": [{"clock_arrays": identity} for identity in arrays]})
        manifest = self.write(self.root / "manifest.json", {"records": records, "clock_registry": registry})
        metadata = self.write(self.root / "metadata.json", {"records": records})
        inputs = {"source_manifest": manifest, "metadata": metadata, "source_clocks": self.clocks,
                  "source_field_files": {name: self.write_lines(name, self.field_rows if "field_" in name else [])
                                         for name in sorted(field.FIELD_NAMES)}}
        self.inputs = inputs
        package = self.write(self.root / "package_inputs.json", inputs)
        self.assets = dict(workspace_root=str(self.root), sources=self.sources,
            adopted_inputs={"package_inputs": package},
            baseline_registration_provenance={"registration_refs": {"config": self.config}},
            protected_baselines={name: self.baseline(name) for name in ("40.48", "40.47")})
        self.render_calls = 0

    def write(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(value, bytes):
            path.write_bytes(value)
            return ref(path)
        return save_new(path, value)

    def write_lines(self, name, rows):
        path = self.root / name
        path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
        return ref(path)

    def baseline(self, name, *, wrong=False):
        path = self.root / (name + ("wrong" if wrong else "") + ".zip")
        rows = [dict(video_id=sid, targetRatioWH=[16, 9], predictions=[
            dict(frame=0, bboxes=[99, 0, 20] if wrong else [10, 0, 20])]) for sid in ("0", "1")]
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("predictions.jsonl", "".join(json.dumps(row) + "\n" for row in rows))
        return ref(path)

    @contextmanager
    def renderer(self, spec, workspace):
        self.assertEqual(workspace, self.root)
        def compose(manifest, selected, shots, requests, outputs):
            self.render_calls += 1
            self.assertEqual(selected, self.field_rows)
            self.assertEqual(shots, self.field_rows)
            rows = [dict(video_id=sid, targetRatioWH=[16, 9], predictions=[
                dict(frame=row["source_frame"], bboxes=[10 + row["source_frame"], 0, 20])
                for row in selected if row["video_id"] == sid]) for sid in ("0", "1")]
            provenance = [dict(row, box_xyw=[10 + row["source_frame"], 0, 20], legal=True,
                               spatial_source="QWEN_ANCHOR_SAME_FRAME", shot_id=0) for row in selected]
            return rows, provenance
        yield SimpleNamespace(compose_from_field=compose), SimpleNamespace(
            load_clocks=lambda *args: self.old_clocks, legacy_manifest=lambda manifest: manifest)

    def render(self):
        with patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": ""}), patch.object(
                field, "bound_renderer", self.renderer):
            return field.render_cache(self.assets, self.root / "new_cache", expected_count=2)

    def test_entire_field_rendered_once_partial_support_and_exact_baselines(self):
        receipt = self.render()
        cached = field.load_cache(receipt, self.assets)
        self.assertEqual(cached["boxes"]["0"], {0: [10, 0, 20], 1: [11, 0, 20]})
        self.assertEqual(cached["support"], {"0": [0, 1], "1": [0, 1]})
        self.assertNotIn(2, cached["boxes"]["0"])
        metadata = cached["metadata"]
        self.assertEqual(metadata["unsupported_native_points"], [{"video_id": "0", "frame": 2}])
        self.assertEqual(metadata["domain_status"], "PARTIAL_NATIVE_ACTION_DOMAIN")
        self.assertEqual((metadata["field_frames"], metadata["native_frames"]), (4, 5))
        self.assertTrue(all(check["all_boxes_exact"] for check in metadata["baseline_overlap"].values()))
        self.assertEqual(self.render(), receipt)
        self.assertEqual(self.render_calls, 1)

    def test_missing_legacy_size_measured_without_replacing_old_sha(self):
        old = {key: self.config[key] for key in ("path", "sha256")}
        self.assertEqual(field._reference(old), self.config)
        with self.assertRaisesRegex(ValueError, "SHA256 changed"):
            field._reference(dict(old, sha256="0" * 64))

    def test_supported_native_pts_mismatch_blocks_before_renderer(self):
        self.old_clocks["0"]["pts"][1] = Fraction(1, 29)
        with self.assertRaisesRegex(ValueError, "native PTS mismatch: 0:1"):
            self.render()
        self.assertEqual(self.render_calls, 0)

    def test_domain_is_not_extended_from_a_longer_old_clock(self):
        self.old_clocks["0"]["pts"].append(Fraction(1, 10))
        cached = field.load_cache(self.render())
        self.assertEqual(cached["source_checks"]["0"]["original_clock_frames"], 4)
        self.assertEqual(cached["support"]["0"], [0, 1])

    def test_baseline_overlap_mismatch_stops_cache_publication(self):
        self.assets["protected_baselines"]["40.48"] = self.baseline("40.48", wrong=True)
        with self.assertRaisesRegex(ValueError, "baseline frame/box differs"):
            self.render()
        self.assertFalse((self.root / "new_cache/receipt.json").exists())

    def test_cache_byte_changes_and_other_assets_rejected(self):
        receipt = self.render()
        other = copy.deepcopy(self.assets)
        other["sources"][0]["n_frames"] += 1
        with self.assertRaisesRegex(ValueError, "different current assets"):
            field.load_cache(receipt, other)
        Path(receipt["cache_ref"]["path"]).write_text("{}", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "byte count changed"):
            field.load_cache(receipt)

    def test_gpu_process_cannot_import_original_renderer(self):
        with patch.dict(os.environ, {"CUDA_VISIBLE_DEVICES": "0"}), patch.object(
                field, "bound_renderer", side_effect=AssertionError("must not import")):
            with self.assertRaisesRegex(ValueError, "isolated CUDA_VISIBLE_DEVICES"):
                field.render_cache(self.assets, self.root / "not_created", expected_count=2)

    def test_changed_media_mapping_stops_before_render(self):
        self.assets["sources"][0]["media"]["sha256"] = "f" * 64
        with self.assertRaisesRegex(ValueError, "media mapping differs"):
            self.render()

    def test_export_projects_saved_rows_and_provenance_without_recompose(self):
        receipt = self.render()
        cached = field.load_cache(receipt)
        selection = {"0": [1], "1": []}
        exported = field.export_selection(cached, selection, self.root / "selection")
        self.assertEqual(field.lines(exported["selected_ref"]["path"]), [self.field_rows[1]])
        proof = field.lines(exported["provenance_ref"]["path"])
        self.assertEqual([(row["video_id"], row["source_frame"], row["box_xyw"]) for row in proof],
                         [("0", 1, [11, 0, 20])])
        self.assertEqual(field.export_selection(receipt, selection, self.root / "selection"), exported)
        self.assertEqual(self.render_calls, 1)
        with self.assertRaisesRegex(ValueError, "outside frozen native action domain"):
            field.export_selection(cached, {"0": [2], "1": []}, self.root / "invalid_selection")

    def install_original_validator(self):
        vendor = (Path(field.__file__).resolve().parents[2] / "reports/round6_score_alignment"
                  "/rematch_execution/rematch_exec_20261005T1215Z/baseline_a_pts_v1/vendor")
        self.write(self.pts_dir / "vendor/independent_validate.py", (vendor / "independent_validate.py").read_bytes())
        for source in (vendor / "frozen_strict_loader").rglob("*.py"):
            self.write(self.pts_dir / "vendor/frozen_strict_loader" /
                       source.relative_to(vendor / "frozen_strict_loader"), source.read_bytes())

    def package_inputs(self, *, wrong_box=False):
        self.install_original_validator()
        receipt = self.render()
        exported = field.export_selection(receipt, {"0": [1], "1": []}, self.root / "selection")
        rows = [dict(video_id=sid, targetRatioWH=[16, 9], predictions=(
            [dict(frame=1, bboxes=[12 if wrong_box else 11, 0, 20])] if sid == "0" else []))
            for sid in ("0", "1")]
        predictions = self.write_lines("predictions.jsonl", rows)
        zipped = self.root / "candidate.zip"
        with zipfile.ZipFile(zipped, "w") as archive:
            archive.write(predictions["path"], "predictions.jsonl")
        return receipt, exported, predictions, ref(zipped)

    def test_actual_original_independent_validator_passes_all_11_checks(self):
        receipt, exported, predictions, zipped = self.package_inputs()
        result = field.verify_package(receipt, exported, predictions, zipped, self.root / "strict_report.json")
        report = json.loads(Path(result["report_ref"]["path"]).read_text(encoding="utf-8"))
        self.assertEqual(set(report["checks"]), field.STRICT_CHECKS)
        self.assertTrue(all(value is True for value in report["checks"].values()))
        self.assertEqual(report["strict_loader_issues"], [])
        self.assertEqual(self.render_calls, 1)

    def test_three_argument_package_receipt_api_keeps_empty_sources(self):
        receipt, _, predictions, zipped = self.package_inputs()
        cached = field.load_cache(receipt)
        result = field.verify_package(cached, {"member_ref": predictions, "zip_ref": zipped},
                                      self.root / "independent_strict")
        report = json.loads(Path(result["report_ref"]["path"]).read_text(encoding="utf-8"))
        self.assertEqual(report["video_records"], 2)
        self.assertEqual(report["expected_frames"], 1)
        self.assertEqual(report["prediction_frames"], 1)
        self.assertTrue(all(value is True for value in report["checks"].values()))
        self.assertEqual(self.render_calls, 1)

    def test_actual_original_validator_rejects_box_disagreement_and_keeps_report(self):
        receipt, exported, predictions, zipped = self.package_inputs(wrong_box=True)
        report_path = self.root / "strict_failed_report.json"
        with self.assertRaisesRegex(ValueError, "11strict validation failed"):
            field.verify_package(receipt, exported, predictions, zipped, report_path)
        report = json.loads(report_path.read_text(encoding="utf-8"))
        self.assertFalse(report["checks"]["provenance_boxes_match_predictions"])
        self.assertEqual(self.render_calls, 1)

    def test_existing_success_acceptance_is_reused_without_spawning_validator(self):
        receipt, exported, predictions, zipped = self.package_inputs()
        report_path = self.root / "strict_report.json"
        first = field.verify_package(receipt, exported, predictions, zipped, report_path)
        with patch.object(field.subprocess, "run", side_effect=AssertionError("must not repeat validator")):
            second = field.verify_package(receipt, exported, predictions, zipped, report_path)
        self.assertEqual(first, second)
        self.assertEqual(self.render_calls, 1)

    def test_earlier_success_report_can_be_adopted_without_old_acceptance(self):
        receipt, exported, predictions, zipped = self.package_inputs()
        report_path = self.root / "strict_report.json"
        first = field.verify_package(receipt, exported, predictions, zipped, report_path)
        Path(first["acceptance_ref"]["path"]).unlink()  # Synthetic pre-receipt crash window.
        with patch.object(field.subprocess, "run", side_effect=AssertionError("must not repeat validator")):
            adopted = field.verify_package(receipt, exported, predictions, zipped, report_path)
        self.assertEqual(adopted, first)

    def test_failed_existing_report_is_never_restarted_or_overwritten(self):
        receipt, exported, predictions, zipped = self.package_inputs(wrong_box=True)
        report_path = self.root / "strict_failed_report.json"
        with self.assertRaisesRegex(ValueError, "11strict validation failed"):
            field.verify_package(receipt, exported, predictions, zipped, report_path)
        original = report_path.read_bytes()
        with patch.object(field.subprocess, "run", side_effect=AssertionError("must not repeat validator")):
            with self.assertRaisesRegex(ValueError, "11strict validation failed"):
                field.verify_package(receipt, exported, predictions, zipped, report_path)
        self.assertEqual(report_path.read_bytes(), original)
        self.assertFalse((self.root / "strict_failed_report.acceptance.json").exists())

    def test_existing_acceptance_rejects_changed_input_reference(self):
        receipt, exported, predictions, zipped = self.package_inputs()
        report_path = self.root / "strict_report.json"
        field.verify_package(receipt, exported, predictions, zipped, report_path)
        duplicate = self.root / "same_bytes_different_input_path.zip"
        duplicate.write_bytes(Path(zipped["path"]).read_bytes())
        with patch.object(field.subprocess, "run", side_effect=AssertionError("must not repeat validator")):
            with self.assertRaisesRegex(ValueError, "acceptance input binding differs"):
                field.verify_package(receipt, exported, predictions, ref(duplicate), report_path)


if __name__ == "__main__":
    unittest.main()
