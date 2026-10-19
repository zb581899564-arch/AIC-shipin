"""SYNTHETIC CPU reuse/accounting integration, never real Linux execution QA.

References/admissions, 522 window byte hashes and deterministic seed bindings,
426 whole-source critic decisions, zero-new-call accounting and the renderer's
admission interface run for real.  Asset/eligibility/fit loading and the existing
full token/native/frozen-receipt reader are explicit mocks.  The origin counts,
features and approvals are synthetic fixture values, not measured model calls.
This suite verifies reuse delegates that full reader; it cannot replace the
reader's tests or the execution agent's actual original-run acceptance.
"""
from contextlib import ExitStack, redirect_stdout
from copy import deepcopy
import io
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from . import admission, render, reuse, run
from .contracts import checked, pipeline_parameters, reference, sample_seed, strict_load
from .test_driver import DriverFixture, FIXTURE, SyntheticBudget


class ReuseFixture(DriverFixture):
    def __init__(self, root):
        super().__init__(root, "critic")
        self.fitted["weights_ref"] = self.reviewed["weights_ref"]
        # Contrast prefers slot1, while the synthetic 131-weight critic prefers
        # slot2. Reuse must select from all four slots, not the origin decision.
        self.expected_selected = {}
        for sid, source in self.sources.items():
            for slot in source["candidates"]:
                slot["feature"] = [float(slot["slot"] == 2)] + [0.0] * 130
            if sid == "0":
                source["candidates"][2]["selected_ordinals"] = []
            self.expected_selected[sid] = source["candidates"][2]["selected_ordinals"]
        self.origin_review = dict(self.reviewed)
        for key in ("fit_ref", "weights_ref", "collect_train_ref"):
            self.origin_review.pop(key, None)
        self.origin_review_ref = self.save("origin/review.json", self.origin_review)
        origin_expected = admission.production_refs(self.binding, self.origin_review, self.origin_review_ref["path"],
            self.args.production_assets, self.args.formal_qa)
        origin_admission = self.admission("production", origin_expected)
        origin_admission["candidate"] = "contrast"
        origin_admission_ref = self.save("origin/admission.json", origin_admission)
        control_ref = self.save("origin/SYNTHETIC_control.json", dict(fixture=FIXTURE, real_QA=False))
        windows = {}
        for index, uid in enumerate(self.case_ids):
            sid = self.source_ids[index % 426]
            source_sha = __import__("hashlib").sha256(("SYNTHETIC_" + sid).encode()).hexdigest()
            windows[uid] = self.save("origin/windows/" + uid + ".json", dict(fixture=FIXTURE,
                uid=uid, source_id=sid, source_sha256=source_sha, status="ACCEPTED",
                counterfactual="HALF_TEMPORAL_GROUP_CIRCULAR_SHIFT_PER_VIEW", control_ref=control_ref,
                slots=[dict(slot=slot, sample_seed=sample_seed(source_sha, uid, slot) if slot in (1, 2) else None)
                       for slot in range(4)]))
        self.origin_counts = dict(reuse.ZERO_COUNTS)
        self.origin_counts.update(generation_calls=1044, generations_completed=1044,
            sample_generation_calls=1044, samples_completed=1044, sequence_score_calls=4176,
            sequence_scores_completed=4176, feature_score_calls=4176, feature_scores_completed=4176,
            top_level_forward_calls=5220)
        self.origin = dict(schema="AIC_CONTENT_CHOICE_PRODUCTION_V1", fixture=FIXTURE,
            status="COMPLETE_PRODUCTION_NOT_PACKAGED", candidate="contrast", **self.binding,
            production_assets_ref=self.formal["_asset_manifest_ref"], formal_qa_ref=self.formal_qa_ref,
            review_ref=self.origin_review_ref, admission_ref=origin_admission_ref,
            frozen_verification_ref=self.save("origin/SYNTHETIC_frozen.json", dict(fixture=FIXTURE, real_QA=False)),
            event_journal_ref=self.save("origin/SYNTHETIC_events.json", dict(fixture=FIXTURE)),
            torch_checks_ref=self.torch_ref, runtime=self.identity, counts=self.origin_counts,
            budget=dict(fixture=FIXTURE, elapsed_seconds=123.0), actual_pipeline_parameters=pipeline_parameters("contrast"),
            sources=self.sources, window_refs=windows, source_count=426, window_count=522,
            control_windows_adopted=522, labels_read=False)

    def prepare(self, *, change_origin=None, change_review=None):
        if change_origin:
            change_origin(self.origin)
        if change_review:
            change_review(self.reviewed)
            self.review_ref = self.save("reuse/changed_critic_review.json", self.reviewed)
            self.args.review_run = Path(self.review_ref["path"])
        self.pool_ref = self.save("origin/completion.json", self.origin)
        # Construct a visibly SYNTHETIC admission even for malformed origins, so
        # the actual production entry, not a fixture helper, must reject them.
        expected = admission.production_refs(self.binding, self.reviewed, self.args.review_run,
                                             self.args.production_assets, self.args.formal_qa)
        expected.update(production_pool_ref=self.pool_ref,
            **{key: self.origin[field] for key, field in reuse.ORIGIN_REF_FIELDS.items()})
        approved = self.admission("production", expected)
        approved_ref = self.save("reuse/production_admission.json", approved)
        self.args.production_pool = Path(self.pool_ref["path"])
        self.args.admission = Path(approved_ref["path"])
        del self.args.torch_checks  # CPU reuse must not need a new Torch/model gate.

    def install(self, stack):
        mocks = self.install_common(stack)
        mocks["review"].side_effect = lambda path, binding, manifest, candidate: (
            self.origin_review if candidate == "contrast" else self.reviewed)
        mocks["preflight"] = stack.enter_context(patch.object(run.asset_api, "preflight_assets",
            return_value=dict(fixture=FIXTURE, actual_assets_verified=False)))
        # Real delegate wiring and referenced bytes are tested. Token grammar,
        # raw native QA, source feature construction and origin frozen receipt
        # remain the explicitly mocked existing-reader boundary.
        mocks["reader"] = stack.enter_context(patch.object(run, "load_collection",
            side_effect=lambda path, *a: strict_load(checked(reference(path), self.root))))
        for name in ("runtime_context", "collect_core", "observation_core", "adopt_formal"):
            mocks[name] = stack.enter_context(patch.object(run, name,
                side_effect=AssertionError("CPU reuse must never call " + name)))
        self.store.case = Mock(side_effect=AssertionError("CPU reuse must not reconstruct visual tensors"))
        stack.enter_context(patch.object(render, "code_identity", return_value=self.code))

        def renderer(manifest, selection, output_dir, **kwargs):
            render._admitted_selection(manifest, selection, kwargs["candidate"], kwargs["parameter_count"],
                                       kwargs["admission"], kwargs["expected_refs"])
            return dict(fixture=FIXTURE, rendering_executed=False, zip_created=False)

        mocks["render"] = stack.enter_context(patch.object(render, "render_candidate", side_effect=renderer))
        return mocks

    def produce(self, directory):
        return run.production(self.config, self.manifest, self.binding, directory, self.budget, self.args)

    def package_args(self, complete_ref):
        complete = strict_load(complete_ref["path"])
        expected = admission.package_refs(self.binding, complete, complete_ref["path"], self.args.production_assets)
        ref = self.save("reuse/package_admission.json", self.admission("package", expected))
        args = SimpleNamespace(**vars(self.args))
        args.production_run, args.admission = Path(complete_ref["path"]), Path(ref["path"])
        return args


class ReuseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="aic_content_reuse_SYNTHETIC_")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_all_four_slot_pool_is_reused_with_zero_new_model_cost(self):
        fixture = ReuseFixture(self.root)
        fixture.prepare()
        with ExitStack() as stack:
            mocks = fixture.install(stack)
            ref = fixture.produce(fixture.directory("production_critic"))
        value = strict_load(ref["path"])
        self.assertEqual(value["execution_mode"], reuse.MODE)
        self.assertEqual(value["counts"], reuse.ZERO_COUNTS)
        self.assertEqual(value["adopted_origin_counts"], fixture.origin_counts)
        self.assertEqual(value["adopted_origin_counts"]["sample_generation_calls"], 1044)
        self.assertEqual(value["production_pool_ref"], fixture.pool_ref)
        self.assertFalse(value["actual_gpu_execution"])
        self.assertFalse(value["model_runtime_created"])
        self.assertFalse(value["frozen_model_verification_performed_here"])
        self.assertNotIn("frozen_verification_ref", value)
        self.assertNotIn("torch_checks_ref", value)
        self.assertNotIn("window_refs", value)
        self.assertEqual(value["actual_pipeline_parameters"], 8782557580)
        selection = strict_load(value["selection_ref"]["path"])
        self.assertEqual({sid: row["selected_ordinals"] for sid, row in selection["sources"].items()},
                         fixture.expected_selected)
        self.assertEqual(selection["sources"]["0"], dict(status="ACCEPTED", selected_ordinals=[]))
        mocks["reader"].assert_called_once()
        for name in ("runtime_context", "collect_core", "observation_core", "adopt_formal"):
            mocks[name].assert_not_called()
        fixture.store.case.assert_not_called()

    def test_package_rereads_origin_and_uses_independent_critic_admission(self):
        fixture = ReuseFixture(self.root)
        fixture.prepare()
        with ExitStack() as stack:
            mocks = fixture.install(stack)
            ref = fixture.produce(fixture.directory("production_critic"))
            args = fixture.package_args(ref)
            result = run.package(fixture.config, fixture.manifest, fixture.binding,
                                 fixture.directory("package_critic"), fixture.budget, args)
        self.assertEqual(mocks["reader"].call_count, 2)
        self.assertTrue(all(Path(call.args[0]) == Path(fixture.pool_ref["path"])
                            for call in mocks["reader"].call_args_list))
        _, kwargs = mocks["render"].call_args
        self.assertEqual(kwargs["admission"]["candidate"], "critic")
        self.assertEqual(kwargs["admission"]["action"], "package")
        self.assertEqual(kwargs["expected_refs"]["production_pool_ref"], fixture.pool_ref)
        self.assertIn("cpu_reuse_verification_ref", kwargs["expected_refs"])
        self.assertFalse(strict_load(result["path"])["receipt"]["zip_created"])
        mocks["runtime_context"].assert_not_called()

    def test_failed_missing_or_noncontrast_origin_is_never_adopted(self):
        mutations = (lambda value: value.update(status="FAILED"),
                     lambda value: value.update(candidate="critic"),
                     lambda value: value["window_refs"].pop(next(iter(value["window_refs"]))),
                     lambda value: value["sources"].pop("425"))
        for index, change in enumerate(mutations):
            with self.subTest(mutation=index):
                fixture = ReuseFixture(self.root / str(index))
                fixture.prepare(change_origin=change)
                with ExitStack() as stack:
                    mocks = fixture.install(stack)
                    with self.assertRaisesRegex(ValueError, "completed original contrast426/522"):
                        fixture.produce(fixture.directory("production_critic"))
                mocks["reader"].assert_not_called()
                mocks["runtime_context"].assert_not_called()

    def test_bound_origin_changed_after_admission_is_rejected(self):
        fixture = ReuseFixture(self.root)
        fixture.prepare()
        path = fixture.args.production_pool
        value = strict_load(path)
        value["budget"]["elapsed_seconds"] += 1
        path.write_text(json.dumps(value), encoding="utf-8")
        with ExitStack() as stack:
            mocks = fixture.install(stack)
            with self.assertRaisesRegex(ValueError, "Stale admission: production_pool_ref"):
                fixture.produce(fixture.directory("production_critic"))
        mocks["reader"].assert_not_called()
        mocks["runtime_context"].assert_not_called()

    def test_bound_window_bytes_and_fixed_seed_are_rechecked(self):
        for wrong_seed in (False, True):
            with self.subTest(wrong_seed=wrong_seed):
                fixture = ReuseFixture(self.root / str(wrong_seed))
                uid = next(iter(fixture.origin["window_refs"]))
                old = fixture.origin["window_refs"][uid]
                if wrong_seed:
                    changed = strict_load(old["path"])
                    changed["slots"][1]["sample_seed"] += 1
                    fixture.origin["window_refs"][uid] = fixture.save("origin/wrong_seed.json", changed)
                fixture.prepare()
                if not wrong_seed:
                    with Path(old["path"]).open("a", encoding="utf-8") as stream:
                        stream.write(" ")
                with ExitStack() as stack:
                    mocks = fixture.install(stack)
                    with self.assertRaises(ValueError):
                        fixture.produce(fixture.directory("production_critic"))
                mocks["reader"].assert_called_once()
                mocks["runtime_context"].assert_not_called()

    def test_different_review_plan_or_runtime_stops_before_full_reader(self):
        for field in ("plan_ref", "runtime"):
            with self.subTest(field=field):
                fixture = ReuseFixture(self.root / field)
                if field == "plan_ref":
                    alternate = fixture.save("other_plan.json", dict(fixture=FIXTURE))
                    change = lambda value: value.update(plan_ref=alternate)
                else:
                    change = lambda value: value.update(runtime=dict(fixture.identity, changed_environment=True))
                fixture.prepare(change_review=change)
                with ExitStack() as stack:
                    mocks = fixture.install(stack)
                    with self.assertRaisesRegex(ValueError, "reviewed critic runtime|same source plan"):
                        fixture.produce(fixture.directory("production_critic"))
                mocks["reader"].assert_not_called()
                mocks["runtime_context"].assert_not_called()

    def test_failed_full_reader_propagates_without_model_or_completion(self):
        fixture = ReuseFixture(self.root)
        fixture.prepare()
        directory = fixture.directory("production_critic")
        with ExitStack() as stack:
            mocks = fixture.install(stack)
            mocks["reader"].side_effect = ValueError("SYNTHETIC_FULL_NATIVE_QA_REJECTION")
            with self.assertRaisesRegex(ValueError, "SYNTHETIC_FULL_NATIVE_QA_REJECTION"):
                fixture.produce(directory)
        self.assertFalse((directory / "completion.json").exists())
        self.assertFalse((directory / "selection.json").exists())
        mocks["runtime_context"].assert_not_called()

    def test_origin_cost_cannot_be_relabelled_as_new_execution_cost(self):
        fixture = ReuseFixture(self.root)
        fixture.prepare()
        with ExitStack() as stack:
            mocks = fixture.install(stack)
            ref = fixture.produce(fixture.directory("production_critic"))
            complete = strict_load(ref["path"])
            complete["counts"] = dict(fixture.origin_counts)
            altered = fixture.save("reuse/altered_cost_completion.json", complete)
            args = fixture.package_args(altered)
            with self.assertRaisesRegex(ValueError, "duplicated the origin's model cost"):
                run.package(fixture.config, fixture.manifest, fixture.binding,
                            fixture.directory("package_critic"), fixture.budget, args)
        mocks["render"].assert_not_called()
        mocks["runtime_context"].assert_not_called()

    def test_reuse_admission_cannot_trigger_gpu_if_explicit_pool_flag_is_omitted(self):
        fixture = ReuseFixture(self.root)
        fixture.prepare()
        fixture.args.production_pool = None
        fixture.args.torch_checks = Path(fixture.torch_ref["path"])
        with ExitStack() as stack:
            mocks = fixture.install(stack)
            with self.assertRaisesRegex(ValueError, "cannot authorize a new model run"):
                fixture.produce(fixture.directory("production_critic"))
        mocks["runtime_context"].assert_not_called()
        mocks["reader"].assert_not_called()

    def test_main_uses_cpu_budget_zero_forward_and_reports_no_gpu_execution(self):
        fixture = ReuseFixture(self.root)
        fixture.prepare()
        config = dict(fixture.config, max_cpu_seconds=1800, max_output_bytes=1048576,
                      run_root=str(self.root / "run"), run_id="run")
        directory = fixture.directory("main_cpu_stage")
        record = {}

        def budget(root, seconds, bytes_limit, forwards):
            record.update(seconds=seconds, forwards=forwards)
            return SyntheticBudget()

        def execute(config, manifest, binding, directory, budget, args):
            return fixture.save("main_cpu_stage/completion.json", dict(status="SYNTHETIC_CPU_ONLY", **binding))

        output = io.StringIO()
        with patch.object(run, "validate_config", return_value=config), \
             patch.object(run, "code_identity", return_value=fixture.code), \
             patch.object(run.asset_api, "load_assets", return_value=fixture.manifest), \
             patch.object(run.asset_api, "preflight_assets", return_value={"fixture": FIXTURE}), \
             patch.object(run, "claim", return_value=directory), \
             patch.object(run, "StageBudget", side_effect=budget), \
             patch.object(run, "production", side_effect=execute), redirect_stdout(output):
            status = run.main(["--stage", "production", "--candidate", "critic",
                "--config", fixture.binding["config_ref"]["path"], "--assets", fixture.binding["asset_manifest_ref"]["path"],
                "--production-pool", str(fixture.args.production_pool)])
        self.assertEqual(status, 0)
        self.assertEqual(record, dict(seconds=1800, forwards=0))
        self.assertFalse(json.loads(output.getvalue())["actual_gpu_execution"])


if __name__ == "__main__":
    unittest.main()
