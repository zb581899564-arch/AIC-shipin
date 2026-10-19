"""SYNTHETIC driver integration, not real Linux/model/tokenizer/media QA.

Actual temporary-file references, admission validation, source decisions and
the renderer's admission boundary execute.  Asset loading/preflight, review
eligibility, retained-output rereading, input stores and runtime execution are
explicit mocks.  The formal fixture has 426 source identities and 522 window
identities; it does NOT manufacture 522 accepted real model answers.  No model,
Torch tensor, actual processor, protected ZIP or production asset is opened.

These regressions cover sequencing and interfaces previously broken at the
driver boundary.  test_adoption, test_render and the separate mandatory Torch
gate cover their own distinct boundaries; this suite does not replace them.
"""
from contextlib import ExitStack
from copy import deepcopy
from pathlib import Path
import tempfile
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from . import observation, render, run
from .contracts import pipeline_parameters, reference, save_new, strict_load


FIXTURE = "SYNTHETIC_CONTENT_CHOICE_DRIVER_TEST_NOT_REAL_QA"


class SyntheticBudget:
    def check(self, *args, **kwargs):
        pass

    def snapshot(self):
        return {"fixture": FIXTURE, "actual_model_calls": 0}


class SyntheticJournal:
    def __init__(self, path):
        self.stream = path.open("x", encoding="utf-8")
        self.stream.write('{"fixture":"' + FIXTURE + '"}\n')
        self.context = {}

    def __call__(self, *args, **kwargs):
        pass

    def close(self):
        self.stream.close()


class SyntheticRuntime:
    """load records ordering only; all actual model operations are forbidden."""
    def __init__(self, identity, events):
        self._identity = deepcopy(identity)
        self.events = events
        self.tokenizer = object()
        self.counts = dict(generation_calls=0, sequence_score_calls=0, sample_generation_calls=0)
        self.generate = Mock(side_effect=AssertionError("SYNTHETIC DRIVER MUST NOT CALL A MODEL"))
        self.generate_sample = self.score_features = self.generate

    def load(self):
        self.events.append("mock_runtime_load")

    def identity(self):
        return deepcopy(self._identity)

    def verify_frozen(self):
        return dict(fixture=FIXTURE, actual_weights_verified=False, actual_model_calls=0)


class DriverFixture:
    """Metadata-only fixtures; each scenario owns a new temporary directory."""
    def __init__(self, root, candidate="observation"):
        self.root, self.candidate = Path(root), candidate
        self.root.mkdir(parents=True, exist_ok=True)
        self.events, self.budget = [], SyntheticBudget()
        self.code = dict(synthetic_release=FIXTURE)
        self.identity = dict(schema="SYNTHETIC_RUNTIME_NOT_EXECUTION_EVIDENCE", fixture=FIXTURE,
                             environment="synthetic-reviewed-environment")
        self.config = dict(fixture=FIXTURE, max_production_sources=426, max_production_windows=522)
        config_ref = self.save("inputs/config.json", self.config)
        self.manifest = dict(fixture=FIXTURE, workspace_root=str(self.root))
        assets_ref = self.save("inputs/pilot_assets.json", self.manifest)
        self.formal = dict(fixture=FIXTURE, workspace_root=str(self.root))
        formal_ref = self.save("inputs/formal_assets.json", self.formal)
        self.formal["_asset_manifest_ref"] = formal_ref
        self.binding = dict(config_ref=config_ref, asset_manifest_ref=assets_ref, code_identity=self.code)
        self.plan_ref = self.save("inputs/plan.json", dict(fixture=FIXTURE))
        self.collect_ref = self.save("inputs/collect_check.json", dict(fixture=FIXTURE))
        self.formal_qa_ref = self.save("inputs/formal_qa.json", dict(fixture=FIXTURE, real_QA=False))
        self.torch_ref = self.save("inputs/torch_checks.json", dict(fixture=FIXTURE, real_Torch_QA=False))
        self.head = dict(schema="AIC_SOURCE_UTILITY_CRITIC_V1", feature_kind="content", parameters=131,
            weights=[1.0] + [0.0] * 130, scaling_folded_into_inference_weights=True, fixture=FIXTURE)
        self.fitted = dict(fixture=FIXTURE, heads={"content": self.head})
        self.reviewed = dict(fixture=FIXTURE, runtime=self.identity, plan_ref=self.plan_ref,
                            collect_check_ref=self.collect_ref)
        if candidate == "observation":
            self.reviewed["observation_ref"] = self.save("inputs/observation.json", dict(fixture=FIXTURE))
        elif candidate == "critic":
            self.reviewed.update(fit_ref=self.save("inputs/fit.json", self.fitted),
                weights_ref=self.save("inputs/weights.json", self.head),
                collect_train_ref=self.save("inputs/collect_train.json", dict(fixture=FIXTURE)))
        self.review_ref = self.save("inputs/review.json", self.reviewed)
        self.source_ids = tuple(map(str, range(426)))
        self.case_ids = tuple("SYNTHETIC_WINDOW_" + str(i).zfill(4) for i in range(522))
        self.store = SimpleNamespace(scope="production", source_ids=self.source_ids,
            case_ids=self.case_ids, workspace=self.root, manifest=self.formal, close=Mock())
        self.selected = {sid: ([] if sid == "0" else [1]) for sid in self.source_ids}
        self.sources = {sid: self.source(sid) for sid in self.source_ids}
        self.observed = dict(fixture=FIXTURE, selections=self.selected, output_refs={},
            source_count=426, window_count=522, changed_input_windows=0, adopted_unchanged_windows=522)
        self.pool = dict(fixture=FIXTURE, sources=self.sources, window_refs={},
            source_count=426, window_count=522, control_windows_adopted=522)
        self.production_expected = dict(config_ref=config_ref, asset_manifest_ref=assets_ref,
            production_assets_ref=formal_ref, review_ref=self.review_ref, formal_qa_ref=self.formal_qa_ref,
            plan_ref=self.plan_ref, collect_check_ref=self.collect_ref)
        for key in ("fit_ref", "weights_ref", "observation_ref", "collect_train_ref"):
            if key in self.reviewed:
                self.production_expected[key] = self.reviewed[key]
        self.production_admission = self.admission("production", self.production_expected)
        admission_ref = self.save("inputs/production_admission.json", self.production_admission)
        self.args = SimpleNamespace(candidate=candidate, review_run=Path(self.review_ref["path"]),
            production_assets=Path(formal_ref["path"]), formal_qa=Path(self.formal_qa_ref["path"]),
            admission=Path(admission_ref["path"]), torch_checks=Path(self.torch_ref["path"]))
        self.runtime = SyntheticRuntime(self.identity, self.events)
        self.journal = None

    def save(self, name, value):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        return save_new(path, value)

    def source(self, sid):
        rows = []
        for slot, selected in enumerate(([0], self.selected[sid], [2], [])):
            score = 1.0 if slot == 1 else 0.0
            rows.append(dict(slot=slot, selected_ordinals=selected, feature=[score] + [0.0] * 130,
                permuted_feature=None, suffix_tokens=10, logprob_sum=-10.0, mean_logprob=-1.0,
                contrast=score))
        return dict(status="ACCEPTED", fixture=FIXTURE, source_id=sid, native_count=3, candidates=rows)

    def admission(self, action, expected):
        return dict(schema="AIC_CONTENT_CHOICE_ADMISSION_V1", action=action, candidate=self.candidate,
            approved=True, reviewed_by="SYNTHETIC TEST REVIEWER", reviewed_at="2026-10-19T00:00:00Z",
            review_notes="Temporary fixture only; not an execution authorization or real QA result.",
            fixture=FIXTURE, **expected)

    def directory(self, name):
        path = self.root / name
        path.mkdir()
        return path

    def install_common(self, stack):
        def load_assets(path, *, verify_files=False):
            if not verify_files:
                raise AssertionError("Formal file verification must occur before runtime/packaging")
            if Path(path) != self.args.production_assets:
                raise AssertionError("Wrong explicitly selected production manifest")
            self.events.append("formal_load_verify_files_true")
            return self.formal

        mocks = {}
        mocks["assets"] = stack.enter_context(patch.object(run.asset_api, "load_assets", side_effect=load_assets))
        mocks["compatibility"] = stack.enter_context(patch.object(run, "require_production_assets",
            side_effect=lambda *a: self.events.append("formal_compatibility")))
        mocks["review"] = stack.enter_context(patch.object(run, "load_review", return_value=self.reviewed))
        mocks["store"] = stack.enter_context(patch.object(run, "NativeInputStore", return_value=self.store))
        mocks["fit"] = stack.enter_context(patch.object(run, "load_fit", return_value=self.fitted))
        return mocks

    def install_production(self, stack, directory, *, preflight_failure=False):
        mocks = self.install_common(stack)

        def preflight(manifest, scope, *, verify_files):
            self.events.append("formal_cpu_preflight")
            if manifest is not self.formal or scope != "production" or verify_files is not False:
                raise AssertionError("Unexpected formal CPU preflight arguments")
            if preflight_failure:
                raise ValueError("SYNTHETIC_FORMAL_PREFLIGHT_REJECTED")
            return dict(fixture=FIXTURE, actual_assets_verified=False)

        def context(*args):
            self.events.append("mock_runtime_context")
            self.journal = SyntheticJournal(directory / "events.jsonl")
            return self.runtime, self.journal, self.torch_ref

        def adopted(*args):
            self.events.append("mock_adopt_formal")
            return {uid: {"fixture": FIXTURE} for uid in self.case_ids}

        mocks["preflight"] = stack.enter_context(patch.object(run.asset_api, "preflight_assets", side_effect=preflight))
        mocks["runtime"] = stack.enter_context(patch.object(run, "runtime_context", side_effect=context))
        mocks["grammar"] = stack.enter_context(patch.object(run, "grammar_module",
            return_value=SimpleNamespace(ascii_token_candidates=lambda tokenizer: [])))
        mocks["adopt"] = stack.enter_context(patch.object(run, "adopt_formal", side_effect=adopted))
        mocks["observation"] = stack.enter_context(patch.object(run, "observation_core", return_value=self.observed))
        mocks["collection"] = stack.enter_context(patch.object(run, "collect_core", return_value=self.pool))
        return mocks

    def prepare_package(self, *, change_selection=None, change_admission=None):
        selection = dict(schema="AIC_CONTENT_CHOICE_SELECTION_V1", sources={sid:
            dict(status="ACCEPTED", selected_ordinals=values) for sid, values in self.selected.items()})
        if change_selection:
            change_selection(selection)
        selection_ref = self.save("completed/selection.json", selection)
        frozen_ref = self.save("completed/frozen.json", dict(fixture=FIXTURE, actual_weights_verified=False))
        event_ref = self.save("completed/events.json", dict(fixture=FIXTURE, actual_model_calls=0))
        self.complete = dict(schema="AIC_CONTENT_CHOICE_PRODUCTION_V1", fixture=FIXTURE,
            status="COMPLETE_PRODUCTION_NOT_PACKAGED", candidate=self.candidate, **self.binding,
            runtime=self.identity, actual_pipeline_parameters=pipeline_parameters(self.candidate),
            production_assets_ref=self.formal["_asset_manifest_ref"], review_ref=self.review_ref,
            selection_ref=selection_ref, frozen_verification_ref=frozen_ref, event_journal_ref=event_ref,
            admission_ref=reference(self.args.admission), formal_qa_ref=self.formal_qa_ref,
            source_count=426, window_count=522)
        complete_ref = self.save("completed/completion.json", self.complete)
        expected = dict(config_ref=self.binding["config_ref"], asset_manifest_ref=self.binding["asset_manifest_ref"],
            production_assets_ref=self.formal["_asset_manifest_ref"], production_completion_ref=complete_ref,
            selection_ref=selection_ref, review_ref=self.review_ref)
        self.package_admission = self.admission("package", expected)
        if change_admission:
            change_admission(self.package_admission)
        admission_ref = self.save("inputs/package_admission.json", self.package_admission)
        self.args.production_run = Path(complete_ref["path"])
        self.args.admission = Path(admission_ref["path"])
        return selection

    def install_package(self, stack):
        mocks = self.install_common(stack)
        mocks["observation"] = stack.enter_context(patch.object(run, "read_observation", return_value=(
            dict(fixture=FIXTURE), {sid: set(v) for sid, v in self.selected.items()})))
        mocks["collection"] = stack.enter_context(patch.object(run, "load_collection", return_value=self.pool))
        mocks["runtime"] = stack.enter_context(patch.object(run, "runtime_context",
            side_effect=AssertionError("Package stage must not construct a model runtime")))
        stack.enter_context(patch.object(render, "code_identity", return_value=self.code))

        def boundary(manifest, selection, output_dir, **kwargs):
            # Execute the actual lightweight renderer interface/admission gate,
            # then stop before spatial inputs, media or a ZIP could be touched.
            render._admitted_selection(manifest, selection, kwargs["candidate"],
                kwargs["parameter_count"], kwargs["admission"], kwargs["expected_refs"])
            return dict(fixture=FIXTURE, rendering_executed=False, zip_created=False)

        mocks["render"] = stack.enter_context(patch.object(render, "render_candidate", side_effect=boundary))
        return mocks


class DriverTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="aic_content_driver_SYNTHETIC_")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_production_preflights_before_model_and_saves_strict_selection(self):
        fixture = DriverFixture(self.root)
        directory = fixture.directory("production")
        with ExitStack() as stack:
            mocks = fixture.install_production(stack, directory)
            result = run.production(fixture.config, fixture.manifest, fixture.binding,
                                    directory, fixture.budget, fixture.args)
        self.assertLess(fixture.events.index("formal_load_verify_files_true"),
                        fixture.events.index("mock_runtime_context"))
        self.assertLess(fixture.events.index("formal_cpu_preflight"), fixture.events.index("mock_runtime_load"))
        self.assertLess(fixture.events.index("mock_runtime_load"), fixture.events.index("mock_adopt_formal"))
        preflight = strict_load(directory / "formal_asset_preflight.json")
        self.assertFalse(preflight["model_loaded"])
        completed = strict_load(result["path"])
        selected = strict_load(completed["selection_ref"]["path"])
        self.assertEqual(set(selected), {"schema", "sources"})
        self.assertEqual(len(selected["sources"]), 426)
        self.assertEqual(selected["sources"]["0"], dict(status="ACCEPTED", selected_ordinals=[]))
        self.assertEqual((completed["source_count"], completed["window_count"]), (426, 522))
        self.assertFalse(completed["automatic_package"])
        mocks["adopt"].assert_called_once()
        fixture.runtime.generate.assert_not_called()
        self.assertTrue(fixture.journal.stream.closed)
        fixture.store.close.assert_called_once()

    def test_formal_preflight_failure_precedes_runtime_and_adoption(self):
        fixture = DriverFixture(self.root)
        directory = fixture.directory("production")
        with ExitStack() as stack:
            mocks = fixture.install_production(stack, directory, preflight_failure=True)
            with self.assertRaisesRegex(ValueError, "SYNTHETIC_FORMAL_PREFLIGHT_REJECTED"):
                run.production(fixture.config, fixture.manifest, fixture.binding, directory, fixture.budget, fixture.args)
        mocks["runtime"].assert_not_called()
        mocks["adopt"].assert_not_called()
        self.assertFalse((directory / "selection.json").exists())

    def test_reviewed_runtime_drift_fails_before_adoption_or_generation(self):
        fixture = DriverFixture(self.root)
        fixture.runtime._identity["environment"] = "synthetic-different-runtime"
        directory = fixture.directory("production")
        with ExitStack() as stack:
            mocks = fixture.install_production(stack, directory)
            with self.assertRaisesRegex(ValueError, "exact reviewed pilot runtime"):
                run.production(fixture.config, fixture.manifest, fixture.binding, directory, fixture.budget, fixture.args)
        self.assertIn("mock_runtime_load", fixture.events)
        mocks["grammar"].assert_not_called()
        mocks["adopt"].assert_not_called()
        mocks["observation"].assert_not_called()
        fixture.runtime.generate.assert_not_called()
        self.assertTrue(fixture.journal.stream.closed)
        fixture.store.close.assert_called_once()

    def test_incomplete_formal_denominator_stops_before_runtime(self):
        for sources, windows in ((425, 522), (426, 521)):
            with self.subTest(sources=sources, windows=windows):
                fixture = DriverFixture(self.root / str(sources))
                fixture.store.source_ids = fixture.source_ids[:sources]
                fixture.store.case_ids = fixture.case_ids[:windows]
                directory = fixture.directory("production")
                with ExitStack() as stack:
                    mocks = fixture.install_production(stack, directory)
                    with self.assertRaisesRegex(ValueError, "formal426/522"):
                        run.production(fixture.config, fixture.manifest, fixture.binding,
                                       directory, fixture.budget, fixture.args)
                mocks["runtime"].assert_not_called()
                mocks["adopt"].assert_not_called()

    def test_package_passes_document_strict_selection_and_candidate_inventory_to_real_boundary(self):
        for candidate in ("observation", "contrast", "critic"):
            with self.subTest(candidate=candidate):
                fixture = DriverFixture(self.root / candidate, candidate)
                expected_selection = fixture.prepare_package()
                directory = fixture.directory("package")
                with ExitStack() as stack:
                    mocks = fixture.install_package(stack)
                    result = run.package(fixture.config, fixture.manifest, fixture.binding,
                                         directory, fixture.budget, fixture.args)
                positional, named = mocks["render"].call_args
                self.assertIs(positional[0], fixture.formal)
                self.assertEqual(positional[1], expected_selection)
                self.assertEqual(set(positional[1]), {"schema", "sources"})
                self.assertEqual(positional[2], directory / "rendered")
                self.assertEqual(named["admission"], fixture.package_admission)
                self.assertEqual(named["admission"]["schema"], "AIC_CONTENT_CHOICE_ADMISSION_V1")
                self.assertEqual(named["candidate"], candidate)
                self.assertEqual(named["parameter_count"], pipeline_parameters(candidate))
                self.assertEqual(named["expected_refs"]["selection_ref"], fixture.complete["selection_ref"])
                self.assertFalse(strict_load(result["path"])["receipt"]["zip_created"])
                qa = strict_load(directory / "independent_production_output_qa.json")
                self.assertEqual((qa["source_count"], qa["window_count"], qa["model_calls"]), (426, 522, 0))
                mocks["runtime"].assert_not_called()
                if candidate == "observation":
                    mocks["observation"].assert_called_once()
                    mocks["collection"].assert_not_called()
                else:
                    mocks["observation"].assert_not_called()
                    mocks["collection"].assert_called_once()
                fixture.store.close.assert_called_once()

    def test_package_recomposition_rejects_extra_schema_fields_and_selection_drift(self):
        changes = (
            lambda value: value.update(candidate="observation"),
            lambda value: value["sources"]["1"].update(selected_ordinals=[2]),
            lambda value: value["sources"]["0"].update(status="FAILED"),
            lambda value: value["sources"].pop("425"),
        )
        for index, change in enumerate(changes):
            with self.subTest(change=index):
                fixture = DriverFixture(self.root / str(index))
                fixture.prepare_package(change_selection=change)
                directory = fixture.directory("package")
                with ExitStack() as stack:
                    mocks = fixture.install_package(stack)
                    with self.assertRaisesRegex(ValueError, "decision review changed packaged selections"):
                        run.package(fixture.config, fixture.manifest, fixture.binding,
                                    directory, fixture.budget, fixture.args)
                mocks["render"].assert_not_called()
                self.assertFalse((directory / "completion.json").exists())

    def test_stale_package_admission_fails_before_renderer(self):
        fixture = DriverFixture(self.root)
        fixture.prepare_package(change_admission=lambda value: value.update(selection_ref=fixture.plan_ref))
        directory = fixture.directory("package")
        with ExitStack() as stack:
            mocks = fixture.install_package(stack)
            with self.assertRaisesRegex(ValueError, "Stale admission: selection_ref"):
                run.package(fixture.config, fixture.manifest, fixture.binding, directory, fixture.budget, fixture.args)
        mocks["render"].assert_not_called()
        mocks["runtime"].assert_not_called()

    def original_request(self):
        prefix = save_new(self.root / "synthetic_prefix_metadata.json", dict(fixture=FIXTURE, actual_tensor=False))
        clock_ref = save_new(self.root / "synthetic_clock.json", dict(normalized_exact_pts=["0", "1"],
            physical_end_exact="2", source_sha256="a" * 64, fixture=FIXTURE))
        return dict(uid="SYN_WINDOW", sid="SYN_SOURCE", source_sha256="a" * 64,
            source_clock_ref=clock_ref, prefix_ref=prefix, grid_hw=[2, 2],
            plan=dict(window_start_exact="0", window_end_exact="2", videos=[{"cells": [0, 1]}]),
            text=dict(expanded_text="SYNTHETIC ORIGINAL PREFIX", prefix_tokens=3),
            input_signature={key: dict(sha256=str(index) * 64, shape=[1, 3], fixture=FIXTURE)
                for index, key in enumerate(("input_ids", "attention_mask", "pixel_values_videos", "video_grid_thw"), 1)})

    def test_no_effect_helper_allows_provenance_but_rejects_every_original_field_change(self):
        original = self.original_request()
        proposed = dict(deepcopy(original), old_input_ref={"fixture": FIXTURE}, observation_policy="SYNTHETIC")
        self.assertTrue(run.original_request_core_equal(proposed, original))
        for key in original:
            with self.subTest(field=key):
                missing = deepcopy(proposed)
                del missing[key]
                self.assertFalse(run.original_request_core_equal(missing, original))
                changed = deepcopy(proposed)
                changed[key] = {"changed": "SYNTHETIC"}
                self.assertFalse(run.original_request_core_equal(changed, original))
        proposed["plan"]["videos"][0]["cells"] = [0, 2]
        self.assertFalse(run.original_request_core_equal(proposed, original))

    def test_no_effect_driver_adopts_original_ref_with_no_torch_save_or_generation(self):
        original = self.original_request()
        original_ref = save_new(self.root / "original_request.json", original)
        proposed = dict(deepcopy(original), old_input_ref=original_ref,
                        observation_policy=observation.POLICY, proposed_plan_discarded=True)
        controls = {original["uid"]: save_new(self.root / "control.json", dict(fixture=FIXTURE,
            status="ACCEPTED", input_signature=original["input_signature"], text='{"segments":[]}', ids=[7]))}
        store = SimpleNamespace(scope="check", case_ids=[original["uid"]], source_ids=[original["sid"]],
            workspace=self.root, requests={original["uid"]: original}, request_refs={original["uid"]: original_ref})
        directory = self.root / "observation"
        directory.mkdir()
        runtime = SyntheticRuntime({"fixture": FIXTURE}, [])
        journal = SyntheticJournal(directory / "events.jsonl")
        self.addCleanup(journal.close)
        synthetic_transformers, synthetic_torch = ModuleType("transformers"), ModuleType("torch")
        synthetic_transformers.AutoProcessor = SimpleNamespace(from_pretrained=Mock(return_value=object()))
        synthetic_torch.save = Mock(side_effect=AssertionError("NO_EFFECT must not save a changed prefix"))
        manifest = dict(model_spec=dict(model_dir="SYNTHETIC_NO_REAL_MODEL_DIRECTORY", revision="SYNTHETIC"))
        diagnostic = dict(status="NO_EFFECT", old_success_can_be_adopted=True, fixture=FIXTURE)
        with patch.dict("sys.modules", {"transformers": synthetic_transformers, "torch": synthetic_torch}), \
             patch.object(observation, "build_observation_case", return_value=(proposed,
                 {"fixture": FIXTURE}, {"fixture": FIXTURE}, diagnostic)), \
             patch.object(run, "ordered_cases", return_value=[original["uid"]]), \
             patch.object(run, "grammar_module", return_value=SimpleNamespace(ascii_token_candidates=lambda t: [])), \
             patch.object(run, "validate_answer", return_value=[]) as native_mock, \
             patch.object(run, "verify_saved_observation", side_effect=AssertionError("NO_EFFECT keeps the old prefix")):
            result = run.observation_core(runtime, store, manifest, controls, directory, journal, SyntheticBudget())
        self.assertEqual((result["changed_input_windows"], result["adopted_unchanged_windows"]), (0, 1))
        answer = strict_load(result["output_refs"][original["uid"]]["path"])
        self.assertEqual(answer["request_ref"], original_ref)
        self.assertFalse(answer["new_model_call"])
        self.assertTrue(answer["legal_empty"])
        self.assertEqual(answer["original_control_ref"], controls[original["uid"]])
        runtime.generate.assert_not_called()
        synthetic_torch.save.assert_not_called()
        native_mock.assert_called_once()  # This boundary is explicitly NOT real token/native QA.


if __name__ == "__main__":
    unittest.main()
