"""Synthetic CPU contracts only: no real media, Torch, model or old pipeline."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from . import assets
from .inputs import NativeInputStore
from .render import bound_renderer, canonical, lines, validate_selections


class Fixture:
    def __init__(self, root, *, same_media=False):
        self.root = Path(root)
        self.kwargs = dict(workspace_root=self.root, output="private_assets.json", rights_declaration="rights.json",
            train_registration="train_registration.json", train_acceptance="train_acceptance.json",
            check_registration="check_registration.json", check_acceptance="check_acceptance.json",
            generation_registration="generation.json", protected_registration="protected_registration.json",
            protected_zip="protected.zip", code_root=self.root / "code")
        self.put("code/runtime.py", b"# synthetic source file; never executed\n")
        self.put("model/config.json", b'{"synthetic":true}\n')
        self.put("model/weights.safetensors", b"synthetic closed model bytes; never loaded")
        weights = self.put("adapter/adapter_model.safetensors", b"synthetic original TIME; never loaded")
        self.put("adapter/adapter_config.json", b'{"synthetic":true}\n')
        cfg = self.save("model_config.json", dict(model_dir=str(self.root / "model"),
            model_revision="pinned-synthetic-revision", expected_base_sha256="a" * 64,
            b_adapter=str(self.root / "adapter"), b_adapter_sha256=weights["sha256"]))
        contract = self.put("old_code/summary_contract.py", b"# bound original helper; never executed\n")
        grammar = self.put("old_code/summary_grammar6.py", b"# bound original grammar; never executed\n")
        codec = self.put("old_code/codec.py", b"# synthetic lossless codec; never executed\n")
        dictionary = self.put("old_code/dictionary.py", b"# synthetic dictionary; never executed\n")
        self.save("generation.json", dict(model_config_ref=cfg, initial_TIME_ref=weights,
            code={"summary_contract.py": contract, "summary_grammar6.py": grammar},
            pixel_codec_ref=codec, pixel_dictionary_ref=dictionary))
        head = self.put("old_head.pt", b"synthetic inherited head; never loaded")
        self.save("protected_registration.json", dict(selected_head=head,
            actual_resident_parameters=assets.PROTECTED_PIPELINE_PARAMETERS))
        self.protected = self.put("protected.zip", b"synthetic protected bytes; not a deliverable ZIP")
        self.put(assets.RUN_RELATIVE + "/resource_unlimited_v1_20261007/gpu_run.py", b"# Never execute this synthetic wrapper\n")
        authors, catalogs, requests = [], {}, {}
        for group, sid in (("train", "SYN_T"), ("check", "SYN_C")):
            media = self.put(sid + "/source.fake", ("synthetic source " + ("DUPLICATE" if same_media else sid)).encode())
            clock = self.save(sid + "/clock.json", dict(source_sha256=media["sha256"],
                normalized_exact_pts=["0", "1", "2", "3"], physical_end_exact="4"))
            label_path = self.root / sid / "human.npz"
            np.savez(label_path, baseline=np.asarray([True, False, False, True]),
                     labels=np.asarray([[True, False], [False, True], [False, True], [False, False]]))
            data = assets.path_ref(label_path)
            authors.append(dict(sid=sid, name=sid, group=group, media=media, clock_ref=clock, data_ref=data))
            pixels = self.put(sid + "/patches.pt", b"synthetic patch file; tensor contents deliberately never loaded")
            common = dict(**pixels, samples=[0, 1, 2, 3])
            source = dict(id=sid, name=sid, source_sha256=media["sha256"], clock=clock)
            if group == "train":
                source.update(native=data, feature_cells=4, chunks=[dict(**common,
                    grid=[[1, 2, 2]] * 4, pixel_shape=[16, 1536], pixel_sha256="b" * 64)])
            else:
                source.update(cells=4, context_cases=[dict(**common, grids=[[1, 2, 2]] * 4)])
            catalogs[group] = self.save(group + "_catalog.json", dict(sources=[source]))
            requests[group] = []
            for index, (start, end, ordinals) in enumerate(((0, 2, [0, 1]), (2, 4, [2, 3]))):
                uid = sid + "_W" + str(index)
                owner = dict(source_id=sid, source_sha256=media["sha256"])
                videos = [dict(role="Overview", owner=owner, native_ordinals=[0, 3], exact_pts=["0", "3"],
                    origin_exact="0", padding=0, observations=2, groups=1),
                    dict(role="Excerpt", owner=owner, native_ordinals=ordinals, exact_pts=list(map(str, ordinals)),
                    origin_exact=str(start), padding=0, observations=2, groups=1)]
                prefix = self.put(sid + "/" + uid + ".prefix.pt", ("synthetic prefix " + uid).encode())
                signatures = {key: dict(shape=[1, 2], dtype="torch.int64", sha256="c" * 64)
                    for key in ("input_ids", "attention_mask", "pixel_values_videos", "video_grid_thw")}
                requests[group].append(self.save(sid + "/" + uid + ".json", dict(uid=uid, sid=sid,
                    source_sha256=media["sha256"], source_clock_ref=clock, grid_hw=[2, 2], prefix_ref=prefix,
                    input_signature=signatures, text=dict(prefix_tokens=2), first_new_pixel_text_native_QA=True,
                    plan=dict(window_start_exact=str(start), window_end_exact=str(end), videos=videos))))
        adoption = self.save("source_adoption.json", dict(sources=authors))
        for group in ("train", "check"):
            registration = self.save(group + "_registration.json", dict(source_registration=adoption))
            prepared = self.save(group + "_prepared.json", dict(inputs=requests[group], source_catalog=catalogs[group]))
            self.save(group + "_acceptance.json", dict(status="PASS_SYNTHETIC_EXISTING_INPUTS", sources=1, windows=2,
                prepared=prepared, registration=registration))
        basis = self.put("rights_basis.txt", b"Synthetic test fixture only; no actual media permissions asserted")
        self.save("rights.json", dict(schema="AIC_NATIVE_PREFERENCE_RIGHTS_V1",
            source_registration_sha256=adoption["sha256"], local_research_training_and_evaluation_allowed=True,
            historical_exposure_acknowledged=True, summary_selection_not_exhaustive_highlight_labels=True,
            basis_refs=[basis]))

    def put(self, name, value):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value)
        return assets.path_ref(path)

    def save(self, name, value):
        return self.put(name, (json.dumps(value, allow_nan=False) + "\n").encode())

    def create(self):
        with patch.object(assets, "PROTECTED_SHA256", self.protected["sha256"]), \
             patch.object(assets, "PROTECTED_BYTES", self.protected["bytes"]):
            reference = assets.bootstrap(**self.kwargs)
            return assets.load_assets(reference["path"], verify_files=True)

    def preflight(self, manifest):
        with patch.object(assets, "PROTECTED_SHA256", self.protected["sha256"]), \
             patch.object(assets, "PROTECTED_BYTES", self.protected["bytes"]):
            return assets.preflight_assets(manifest)

    def add_check_known(self, known, key="known"):
        path = self.root / "SYN_C" / "human.npz"
        with np.load(path, allow_pickle=False) as original:
            baseline, labels = original["baseline"], original["labels"]
        np.savez(path, baseline=baseline, labels=labels, **{key: known})
        adoption = assets.read_json(self.root / "source_adoption.json")
        next(s for s in adoption["sources"] if s["sid"] == "SYN_C")["data_ref"] = assets.path_ref(path)
        adoption_ref = self.save("source_adoption.json", adoption)
        for group in ("train", "check"):
            registration = self.save(group + "_registration.json", dict(source_registration=adoption_ref))
            gate = assets.read_json(self.root / (group + "_acceptance.json"))
            gate["registration"] = registration
            self.save(group + "_acceptance.json", gate)
        rights = assets.read_json(self.root / "rights.json")
        rights["source_registration_sha256"] = adoption_ref["sha256"]
        self.save("rights.json", rights)


class AssetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="aic_native_preference_synthetic_")
        self.addCleanup(self.temp.cleanup)
        self.fixture = Fixture(self.temp.name)

    def test_explicit_legacy_bootstrap_and_rater_orientation(self):
        before = "torch" in sys.modules
        manifest = self.fixture.create()
        result = self.fixture.preflight(manifest)
        self.assertEqual(result["scopes"], {"train": {"sources": 1, "windows": 2}, "check": {"sources": 1, "windows": 2}})
        self.assertFalse(result["GPU_started"])
        store = NativeInputStore(manifest, "train")
        human = store.source_supervision("SYN_T")
        self.assertEqual(human["baseline"], {0, 3})
        self.assertEqual(human["raters"], [{0}, {1, 2}])
        self.assertEqual(human["known_masks"], [[True] * 4, [True] * 4])
        self.assertEqual(len(store.case_ids), 2)
        self.assertEqual(before, "torch" in sys.modules)
        self.assertEqual(manifest["actual_pipeline_parameters"], 8797892873)
        with self.assertRaises(FileExistsError):
            self.fixture.create()

    def test_explicit_unknown_is_preserved_not_zero_label(self):
        known = np.ones((4, 2), dtype=bool); known[2, 1] = False
        self.fixture.add_check_known(known)
        manifest = self.fixture.create()
        source = manifest["scopes"]["check"]["sources"][0]
        self.assertEqual(source["supervision_contract"]["known_key"], "known")
        human = NativeInputStore(manifest, "check").source_supervision("SYN_C")
        self.assertEqual(human["raters"][1], {1, 2})
        self.assertFalse(human["known_masks"][1][2])
        source["supervision_contract"]["known_key"] = None
        with self.assertRaisesRegex(ValueError, "known-mask column differs"):
            NativeInputStore(manifest, "check").source_supervision("SYN_C")

    def test_undeclared_known_column_is_rejected(self):
        self.fixture.add_check_known(np.ones((4, 2), dtype=bool), key="label_known")
        with self.assertRaisesRegex(ValueError, "Unregistered known-mask column"):
            self.fixture.create()

    def test_local_model_snapshot_symlink_is_bound_by_name_and_bytes(self):
        self.fixture.put("blobs/existing_weight", b"existing shared local model bytes")
        link = self.fixture.root / "model" / "local_snapshot_weight"
        link.symlink_to(self.fixture.root / "blobs" / "existing_weight")
        manifest = self.fixture.create()
        self.assertIn("local_snapshot_weight", {row["relative_path"] for row in manifest["model_files"]})
        self.fixture.put("blobs/other_weight", b"other local model bytes")
        link.unlink(); link.symlink_to(self.fixture.root / "blobs" / "other_weight")
        with self.assertRaisesRegex(ValueError, "model directory inventory changed"):
            self.fixture.preflight(manifest)

    def test_missing_window_rejected_by_preflight_and_store(self):
        manifest = self.fixture.create()
        manifest["scopes"]["check"]["requests"].pop()
        with self.assertRaisesRegex(ValueError, "Complete accepted source/catalog/window"):
            self.fixture.preflight(manifest)
        with self.assertRaisesRegex(ValueError, "Complete source window coverage"):
            NativeInputStore(manifest, "check")

    def test_source_clock_mismatch_rejected(self):
        manifest = self.fixture.create()
        source = manifest["scopes"]["train"]["sources"][0]
        source["source_sha256"] = "f" * 64
        with self.assertRaisesRegex(ValueError, "Complete accepted source/catalog/window"):
            self.fixture.preflight(manifest)

    def test_fit_and_check_cannot_share_source_bytes(self):
        duplicate = Fixture(self.fixture.root / "overlap_fixture", same_media=True)
        with self.assertRaisesRegex(ValueError, "Fit and external check sources overlap"):
            duplicate.create()

    def test_changed_model_file_and_new_unbound_runtime_file_rejected(self):
        manifest = self.fixture.create()
        path = self.fixture.root / "model" / "weights.safetensors"
        old = path.read_bytes(); path.write_bytes(old.replace(b"model", b"MODEL"))
        with self.assertRaisesRegex(ValueError, "SHA256 changed"):
            self.fixture.preflight(manifest)
        path.write_bytes(old)
        self.fixture.put("code/unbound.py", b"# Not in the adopted code closure\n")
        with self.assertRaisesRegex(ValueError, "runtime Python code inventory changed"):
            self.fixture.preflight(manifest)

    def test_false_rights_and_wrong_gate_registration_rejected(self):
        rights = assets.read_json(self.fixture.root / "rights.json")
        rights["historical_exposure_acknowledged"] = False
        self.fixture.save("rights.json", rights)
        with self.assertRaisesRegex(ValueError, "source-use/task/exposure"):
            self.fixture.create()
        rights["historical_exposure_acknowledged"] = True
        self.fixture.save("rights.json", rights)
        gate = assets.read_json(self.fixture.root / "check_acceptance.json")
        gate["registration"] = assets.path_ref(self.fixture.root / "train_registration.json")
        self.fixture.save("check_acceptance.json", gate)
        with self.assertRaisesRegex(ValueError, "another registration"):
            self.fixture.create()

    def test_strict_json_and_reference_reject_unsafe_inputs(self):
        path = self.fixture.root / "duplicate.json"
        path.write_text('{"a":1,"a":2}')
        with self.assertRaisesRegex(ValueError, "Duplicate JSON"):
            assets.read_json(path)
        path.write_text('{"a":NaN}')
        with self.assertRaisesRegex(ValueError, "Nonfinite JSON"):
            assets.read_json(path)
        for literal in ("1e309", "-1e309"):
            path.write_text('{"a":' + literal + '}')
            with self.assertRaisesRegex(ValueError, "Nonfinite JSON"):
                assets.read_json(path)
            with self.assertRaisesRegex(ValueError, "Nonfinite JSON"):
                lines(path.read_bytes())
        with self.assertRaisesRegex(ValueError, "must be absolute"):
            assets.check_ref(dict(path="relative.json", sha256="a" * 64))

    def test_legal_empty_failed_and_native_ordinal_contract(self):
        counts = {"0": 4, "1": 2}
        selected = {"0": dict(status="ACCEPTED", selected_ordinals=[]),
                    "1": dict(status="ACCEPTED", selected_ordinals=[1])}
        self.assertEqual(validate_selections(selected, counts), {("1", 1)})
        for change in (dict(status="FAILED", selected_ordinals=[]),
                       dict(status="ACCEPTED", selected_ordinals=[True]),
                       dict(status="ACCEPTED", selected_ordinals=[1, 1]),
                       dict(status="ACCEPTED", selected_ordinals=[4])):
            with self.subTest(change=change), self.assertRaises(ValueError):
                validate_selections({**selected, "0": change}, counts)
        with self.assertRaisesRegex(ValueError, "Missing/extra"):
            validate_selections({"1": selected["1"]}, counts)

    def test_renaming_or_parameter_claim_does_not_change_canonical_predictions(self):
        before = [dict(video_id="0", targetRatioWH=[9, 16], predictions=[], model_params_b=8.7),
                  dict(video_id="1", targetRatioWH=[16, 9], predictions=[dict(frame=1, bboxes=[[0, 0, 2]])])]
        after = copy.deepcopy(before[::-1]); after[1]["model_params_b"] = 8.8
        self.assertEqual(canonical(before), canonical(after))
        after[0]["predictions"] = []
        self.assertNotEqual(canonical(before), canonical(after))

    def test_renderer_full_transitive_closure_and_cached_module_binding(self):
        root = self.fixture.root / "renderer"
        for name, source in (("field_contract", "import package_contract\nimport p2j_core\n"),
                             ("pts_contract", "import a_contract\n"),
                             ("package_contract", "VALUE=1\n"), ("p2j_core", "VALUE=2\n"),
                             ("a_contract", "VALUE=3\n")):
            self.fixture.put("renderer/" + name + ".py", source.encode())
        self.fixture.put("renderer/strict/__init__.py", b"# synthetic strict loader\n")
        code = [assets.path_ref(path) for path in root.rglob("*.py")]
        renderer = dict(code_refs=code, import_paths=[str(root)], strict_loader_root=str(root / "strict"),
            field_contract_ref=assets.path_ref(root / "field_contract.py"),
            pts_contract_ref=assets.path_ref(root / "pts_contract.py"))
        names = ["field_contract", "pts_contract", "package_contract", "p2j_core", "a_contract"]
        with patch.dict(sys.modules):
            for name in names:
                sys.modules.pop(name, None)
            with bound_renderer(renderer, self.fixture.root) as (field, pts):
                self.assertEqual(field.package_contract.VALUE, 1)
                self.assertEqual(pts.legacy.VALUE if hasattr(pts, "legacy") else pts.a_contract.VALUE, 3)
            self.fixture.put("renderer/unbound.py", b"# new unbound code\n")
            with self.assertRaisesRegex(ValueError, "inventory differs"):
                with bound_renderer(renderer, self.fixture.root):
                    pass


if __name__ == "__main__":
    unittest.main()
