"""Actual pure renderer/PTS/11-check execution on entirely synthetic fixtures.

The protected identity is patched only inside these tests because a synthetic
ZIP cannot have the real protected ZIP's hash.  No real media, model, production
asset, report, launch wrapper or protected file is opened or changed.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from . import render
from .contracts import pipeline_parameters
from ..native_preference_v1.assets import path_ref, read_json


REPO = Path(__file__).resolve().parents[2]
LEGACY = REPO / "reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z"


class RenderFixture:
    identity = {"synthetic_release": "explicit_test_fixture_not_a_deployment_receipt"}

    def __init__(self, root, *, middle_in_field=True, clock_mismatch=False):
        self.root = Path(root)
        self.version = 0
        directories = [self.root / "run/b_score_aligned_package_v4", self.root / "run/baseline_a_pts_v1",
                       self.root / "run/baseline_a_pts_v1/vendor"]
        needed = ((0, "field_contract.py"), (0, "package_contract.py"), (0, "contracts.py"),
                  (1, "pts_contract.py"), (1, "a_contract.py"), (2, "p2j_core.py"), (2, "independent_validate.py"))
        for index, name in needed:
            directories[index].mkdir(parents=True, exist_ok=True)
            relative = directories[index].relative_to(self.root / "run") / name
            shutil.copyfile(LEGACY / relative, directories[index] / name)
        strict = directories[2] / "frozen_strict_loader"
        shutil.copytree(LEGACY / "baseline_a_pts_v1/vendor/frozen_strict_loader", strict)
        records, clock_records, array_refs, sources = [], [], [], []
        frames, shots, requests, outputs, baseline = [], [], [], [], []
        for number in range(426):
            sid = str(number)
            source_sha = hashlib.sha256(("SYNTHETIC_UNREAD_SOURCE_" + sid).encode()).hexdigest()
            ratio = [16, 9] if number % 2 == 0 else [9, 16]
            record = dict(video_id=sid, source_group="synthetic:" + sid,
                source_path=str(self.root / "unread_synthetic_sources" / (sid + ".not_media")),
                source_sha256=source_sha, width=160, height=160, n_frames=3,
                fps_num=20, fps_den=1, targetRatioWH=ratio, scope_start_sec=0, scope_end_sec=0.15,
                clock_branch="CFR_LEGACY", clock_record_id=sid)
            records.append(record)
            clock = self.save("inputs/" + sid + ".clock.json", dict(source_sha256=source_sha,
                normalized_exact_pts=["0", "1/25" if clock_mismatch and sid == "0" else "1/20", "1/10"], physical_end_exact="3/20"))
            sources.append(dict(id=sid, group="production", source_sha256=source_sha, clock_ref=clock))
            array_ref = self.save("clock_registry/arrays/" + sid + ".json", dict(schema="aic_source_clock_arrays_v1",
                video_id=sid, source_sha256=source_sha, n_frames=3, raw_time_base="1/20", raw_first_pts_ticks=100,
                native_pts_ticks=[100, 101, 102], source_relative_pts_rational=["0", "1/20", "1/10"],
                source_relative_pts=[0.0, 0.05, 0.1]), with_bytes=False)
            array_refs.append(array_ref)
            clock_records.append(dict(video_id=sid, source_sha256=source_sha, n_frames=3, fps_num=20, fps_den=1,
                identity_pass=True, cfr_eligible=True, failures=[], decord_binding=dict(start_pass=True, legacy_interval_pass=True),
                clock_arrays=array_ref, raw_time_base="1/20", raw_first_pts_ticks=100,
                duration_seconds=0.15, terminal_evidence=dict(kind="LEGACY_CFR_N_DIV_FPS")))
            def box(frame):
                return [0, 10 + frame * 2, 160] if ratio == [16, 9] else [10 + frame * 2, 0, 90]
            baseline.append(dict(video_id=sid, targetRatioWH=ratio,
                                 predictions=[dict(frame=0, bboxes=box(0))], model_params_b=8.782557449))
            for ordinal in ([0, 1, 2] if middle_in_field else [0, 2]):
                frame = dict(video_id=sid, source_frame=ordinal, source_path=record["source_path"],
                    source_width=160, source_height=160, source_n_frames=3, fps=20.0, target_ratio_wh=ratio)
                pixel_sha = hashlib.sha256(("SYNTHETIC_PIXEL_" + sid + ":" + str(ordinal)).encode()).hexdigest()
                frames.append(frame)
                shots.append(dict(video_id=sid, source_frame=ordinal, decoded_pixel_sha256=pixel_sha,
                                  is_shot_start=ordinal == 0 or not middle_in_field))
                if ordinal in (0, 2):
                    request = dict(**frame, kind="QWEN_ANCHOR_SAME_FRAME", expected_pixel_sha256=pixel_sha)
                    request["anchor_request_sha256"] = hashlib.sha256(json.dumps(request,
                        ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
                    requests.append(request)
                    outputs.append(dict(video_id=sid, source_frame=ordinal, status="MODEL_OK", used_fallback=False,
                        spatial_source="QWEN_ANCHOR_SAME_FRAME", anchor_request_sha256=request["anchor_request_sha256"],
                        decoded_pixel_sha256=pixel_sha, box_xyw=box(ordinal)))
        registry = self.save("clock_registry/registry.json", dict(schema="aic_source_clock_registry_v4", kind="REMATCH426",
            expected_count=426, all_identity_pass=True, all_sources_usable=True, inference_allowed=False,
            failed_video_ids=[], input_manifest_sha256="e" * 64, records=clock_records), with_bytes=False)
        manifest_ref = self.save("field/source_manifest.json", dict(schema="aic_rematch_A_input_v2", kind="REMATCH426",
            expected_count=426, clock_registry=registry, input_manifest_sha256="e" * 64,
            input_contract=dict(status="APPROVED_METADATA_ONLY", data_use_evidence="Synthetic test only",
                target_ratio_evidence="Synthetic mixed ratios", metadata_role_evidence="No actual media",
                contest_jsonl_values_used=False), allowed_source_roots=[str(self.root / "unread_synthetic_sources")], records=records))
        metadata = self.save("field/metadata.json", dict(records=records))
        field_files = {name: self.jsonl("field/" + name, value) for name, value in (
            ("field_frames.jsonl", frames), ("field_shots.jsonl", shots),
            ("anchor_requests.jsonl", requests), ("anchor_output.jsonl", outputs))}
        package_inputs = self.save("field/package_inputs.json", dict(source_manifest=manifest_ref,
            metadata=metadata, source_field_files=field_files))
        renderer = dict(package_inputs_ref=package_inputs, source_manifest_ref=manifest_ref, metadata_ref=metadata,
            clock_registry_ref=registry, clock_array_refs=array_refs, field_files=field_files,
            import_paths=list(map(str, directories)), strict_loader_root=str(strict),
            code_refs=[path_ref(p) for directory in directories for p in directory.glob("*.py")]
                + [path_ref(p) for p in strict.rglob("*.py")],
            field_contract_ref=path_ref(directories[0] / "field_contract.py"),
            pts_contract_ref=path_ref(directories[1] / "pts_contract.py"),
            independent_validator_ref=path_ref(directories[2] / "independent_validate.py"),
            spatial_policy="intersect_with_frozen_field")
        protected = self.root / "synthetic_protected.zip"
        with zipfile.ZipFile(protected, "x", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("predictions.jsonl", "".join(json.dumps(row) + "\n" for row in baseline))
        self.baseline_ref = path_ref(protected)
        self.manifest = dict(workspace_root=str(self.root), protected_baseline_ref=self.baseline_ref,
            scopes={"production": dict(sources=sources, requests=[{"synthetic_window": str(i)} for i in range(426)])},
            renderer=renderer, code_refs=[], runtime_python=sys.executable)
        self.manifest["_asset_manifest_ref"] = self.save("assets.json", self.manifest)
        self.config_ref = self.save("config.json", dict(synthetic_only=True))
        self.select = {sid: dict(status="ACCEPTED", selected_ordinals=[0, 1]) for sid in map(str, range(426))}
        self.select["0"]["selected_ordinals"] = []
        self.bind()

    def save(self, name, value, with_bytes=True):
        path = self.root / name; path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, ensure_ascii=False, allow_nan=False) + "\n")
        ref = path_ref(path)
        if not with_bytes: ref.pop("bytes")
        return ref

    def jsonl(self, name, value):
        path = self.root / name; path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(json.dumps(row, allow_nan=False) + "\n" for row in value))
        return path_ref(path)

    def bind(self, candidate="observation"):
        self.version += 1
        self.candidate = candidate
        self.selection = dict(schema=render.SELECTION_SCHEMA, sources=deepcopy(self.select))
        selection_ref = self.save("review/selection_" + str(self.version) + ".json", self.selection)
        complete = dict(status=render.COMPLETE_STATUS, candidate=candidate, actual_pipeline_parameters=pipeline_parameters(candidate),
            config_ref=self.config_ref, asset_manifest_ref=self.manifest["_asset_manifest_ref"], selection_ref=selection_ref,
            source_count=426, window_count=426, code_identity=self.identity)
        self.expected = dict(config_ref=self.config_ref, asset_manifest_ref=self.manifest["_asset_manifest_ref"],
            production_completion_ref=self.save("review/completion_" + str(self.version) + ".json", complete), selection_ref=selection_ref)
        self.admission = dict(schema="AIC_CONTENT_CHOICE_ADMISSION_V1", action="package", candidate=candidate, approved=True,
            reviewed_by="Synthetic test reviewer", review_notes="No real production admission", reviewed_at="2026-10-19T00:00:00Z", **self.expected)

    def render(self, **kwargs):
        with patch.object(render, "PROTECTED_SHA256", self.baseline_ref["sha256"]), \
             patch.object(render, "PROTECTED_BYTES", self.baseline_ref["bytes"]), \
             patch.object(render, "code_identity", return_value=self.identity):
            return render.render_candidate(self.manifest, self.selection, self.root / "new_rendered",
                candidate=self.candidate, parameter_count=kwargs.pop("parameter_count", pipeline_parameters(self.candidate)),
                admission=self.admission, expected_refs=self.expected, **kwargs)


class RenderTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="aic_content_render_synthetic_")
        self.root = Path(self.temp.name)
        self.before_bytecode = sys.dont_write_bytecode
        self.addCleanup(self.cleanup)

    def cleanup(self):
        # The retained renderer uses bare module names; remove only this test's
        # actual temporary modules so independent fixtures cannot reuse them.
        for name, module in list(sys.modules.items()):
            filename = getattr(module, "__file__", None)
            if filename and Path(filename).resolve().is_relative_to(self.root):
                sys.modules.pop(name, None)
        sys.dont_write_bytecode = self.before_bytecode
        self.temp.cleanup()

    def test_real_frozen_field_pts_and_all11_strict_checks_with_legal_empty(self):
        fixture = RenderFixture(self.root)
        before = fixture.baseline_ref.copy()
        result = fixture.render()
        self.assertEqual(result["empty_source_ids"], ["0"])
        self.assertEqual(result["records"], 426)
        self.assertEqual(result["frames"], 850)
        self.assertEqual(result["added_frames"], 425)
        self.assertEqual(result["removed_frames"], 1)
        report = read_json(result["independent_validation_ref"]["path"])
        self.assertEqual(len(report["checks"]), 11)
        self.assertTrue(all(report["checks"].values()))
        self.assertFalse(report["strict_loader_issues"])
        self.assertEqual(path_ref(before["path"]), before)
        with zipfile.ZipFile(result["zip_ref"]["path"]) as archive:
            self.assertEqual(archive.namelist(), ["predictions.jsonl"])
            rows = render.lines(archive.read("predictions.jsonl"))
        self.assertTrue(all(row["model_params_b"] == 8.782557449 for row in rows))
        self.assertIn("OBSERVATION", Path(result["zip_ref"]["path"]).name)

    def test_critic_parameter_inventory_is_distinct_and_not_dpo(self):
        fixture = RenderFixture(self.root); fixture.bind("critic")
        result = fixture.render()
        self.assertEqual(result["actual_pipeline_parameters"], 8782557580)
        self.assertIn("CRITIC", Path(result["zip_ref"]["path"]).name)

    def test_same_canonical_baseline_is_rejected_without_zip(self):
        fixture = RenderFixture(self.root)
        fixture.select = {str(i): dict(status="ACCEPTED", selected_ordinals=[0]) for i in range(426)}
        fixture.bind()
        with self.assertRaisesRegex(ValueError, "DUPLICATE_PROTECTED_BASELINE"):
            fixture.render()
        self.assertEqual(list((self.root / "new_rendered").glob("*.zip")), [])
        self.assertFalse(read_json(self.root / "new_rendered/no_effect.json")["new_zip"])

    def test_field_exclusion_stops_before_any_zip_and_records_evidence(self):
        fixture = RenderFixture(self.root, middle_in_field=False)
        with self.assertRaisesRegex(ValueError, "STOP_FIELD_DOMAIN_EXCLUSION"):
            fixture.render()
        report = read_json(self.root / "new_rendered/field_eligibility.json")
        self.assertEqual(report["excluded_unavailable_field_frames"], 425)
        self.assertFalse(report["external_check_has_equivalent_field_evidence"])
        self.assertEqual(list((self.root / "new_rendered").glob("*.zip")), [])

    def test_failed_or_missing_source_never_becomes_empty(self):
        fixture = RenderFixture(self.root)
        fixture.select["0"]["status"] = "FAILED"; fixture.bind()
        with self.assertRaisesRegex(ValueError, "Failed source"):
            fixture.render()
        fixture.select.pop("0"); fixture.bind()
        with self.assertRaisesRegex(ValueError, "Missing/extra"):
            fixture.render()
        self.assertFalse((self.root / "new_rendered").exists())

    def test_stale_admission_wrong_candidate_or_parameter_count_is_rejected(self):
        fixture = RenderFixture(self.root)
        original = deepcopy(fixture.admission)
        for mutate in (lambda a: a.update(approved=False), lambda a: a.update(candidate="critic"),
                       lambda a: a.update(reviewed_at="2026-10-19T00:00:00"),
                       lambda a: a["selection_ref"].update(sha256="f" * 64)):
            fixture.admission = deepcopy(original); mutate(fixture.admission)
            with self.assertRaises(ValueError):
                fixture.render()
        fixture.admission = original
        with self.assertRaisesRegex(ValueError, "parameter inventory"):
            fixture.render(parameter_count=8797892873)
        self.assertFalse((self.root / "new_rendered").exists())

    def test_same_frame_count_but_different_native_pts_is_rejected(self):
        fixture = RenderFixture(self.root, clock_mismatch=True)
        with self.assertRaisesRegex(ValueError, "Actual source PTS"):
            fixture.render()
        self.assertEqual(list((self.root / "new_rendered").glob("*.zip")), [])

    def test_selection_document_mutation_after_review_is_rejected(self):
        fixture = RenderFixture(self.root)
        fixture.selection["sources"]["1"]["selected_ordinals"] = []
        with self.assertRaisesRegex(ValueError, "admitted immutable selection"):
            fixture.render()
        self.assertFalse((self.root / "new_rendered").exists())


if __name__ == "__main__":
    unittest.main()
