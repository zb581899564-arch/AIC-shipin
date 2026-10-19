"""Explicit CPU-only critic selection from an admitted complete contrast pool.

The origin owns every historical generation/teacher-forcing call and its real
frozen-model receipt.  This stage only rereads those immutable outputs, verifies
their native/source identities and applies the already fitted 131-weight head.
It never creates a model runtime, repeats a sample, or creates a new receipt
claiming that a model was loaded or checked in this stage.
"""
from copy import deepcopy

from .contracts import (admission_gate, bind_artifact, checked, pipeline_parameters,
    reference, require, same_reference, sample_seed, save_new, strict_load)
from .selection import choose
from .critic import score_source


MODE = "CPU_CRITIC_FROM_ADMITTED_CONTRAST_POOL"
RECEIPT_SCHEMA = "AIC_CONTENT_CHOICE_CPU_POOL_REUSE_VERIFICATION_V1"
ORIGIN_REF_FIELDS = {
    "origin_production_admission_ref": "admission_ref",
    "origin_review_ref": "review_ref",
    "origin_frozen_verification_ref": "frozen_verification_ref",
    "origin_event_journal_ref": "event_journal_ref",
    "origin_torch_checks_ref": "torch_checks_ref",
}
ZERO_COUNTS = dict(sequence_score_calls=0, sequence_scores_completed=0,
    generation_calls=0, generations_completed=0, top_level_forward_calls=0,
    backward_calls=0, backwards_completed=0, optimizer_steps=0,
    sample_generation_calls=0, samples_completed=0, feature_score_calls=0,
    feature_scores_completed=0)
COUNTS_ROLE = "THIS_CPU_STAGE_ONLY; origin calls are charged once to production_pool_ref"
RUNTIME_ROLE = "ADOPTED_ORIGIN_FEATURE_EXTRACTOR_NOT_EXECUTED_HERE"


def _origin_header(value):
    require(value.get("schema") == "AIC_CONTENT_CHOICE_PRODUCTION_V1"
            and value.get("status") == "COMPLETE_PRODUCTION_NOT_PACKAGED"
            and value.get("candidate") == "contrast" and "execution_mode" not in value
            and "production_pool_ref" not in value and value.get("labels_read") is False
            and value.get("source_count") == 426 and value.get("window_count") == 522
            and value.get("control_windows_adopted") == 522
            and value.get("actual_pipeline_parameters") == pipeline_parameters("contrast")
            and isinstance(value.get("window_refs"), dict) and len(value["window_refs"]) == 522
            and isinstance(value.get("sources"), dict) and set(value["sources"]) == set(map(str, range(426))),
            "Only an independently completed original contrast426/522 full pool can be reused")


def production_pool_refs(path):
    """Bind exact explicit origin and approvals in an unapproved draft or job."""
    ref = reference(path)
    value = strict_load(checked(ref))
    _origin_header(value)
    return dict(production_pool_ref=ref,
                **{key: value[field] for key, field in ORIGIN_REF_FIELDS.items()})


def validate_origin(pool_ref, binding, manifest, formal, reviewed, formal_qa_ref, store):
    """Re-read all522 outputs and frozen receipts; no model or pixel loading."""
    from .admission import production_refs
    from .run import load_collection, load_review
    workspace = manifest["workspace_root"]
    value = strict_load(checked(pool_ref, workspace))
    _origin_header(value)
    bind_artifact(value, binding)
    require(same_reference(value["production_assets_ref"], formal["_asset_manifest_ref"])
            and same_reference(value["formal_qa_ref"], formal_qa_ref),
            "Reused formal assets or original formalQA differ")
    require(value["runtime"] == reviewed["runtime"],
            "Reused feature extractor/sampler differs from the exact reviewed critic runtime")
    require(store.scope == "production" and len(store.source_ids) == 426
            and set(store.source_ids) == set(map(str, range(426))) and len(store.case_ids) == 522,
            "Reuse needs all426 registered sources and all522 original windows")
    origin_review = load_review(checked(value["review_ref"], workspace), binding, manifest, "contrast")
    require(origin_review["runtime"] == reviewed["runtime"]
            and all(same_reference(origin_review[key], reviewed[key])
                    for key in ("plan_ref", "collect_check_ref")),
            "Contrast and critic reviews must share the same source plan, control collection and runtime")
    original_expected = production_refs(binding, origin_review, value["review_ref"]["path"],
        value["production_assets_ref"]["path"], value["formal_qa_ref"]["path"])
    original_admission = strict_load(checked(value["admission_ref"], workspace))
    require("production_pool_ref" not in original_admission,
            "The origin must own the original contrast execution, not another reuse")
    admission_gate(original_admission, "production", "contrast", original_expected, workspace)
    # This existing reader checks the actual saved answer/EOS/native membership,
    # request/clock identities, full source composition, aliases, counts and
    # origin frozen receipt.  Its tokenizer is local; no Qwen is constructed.
    pool = load_collection(checked(pool_ref, workspace), binding, formal, store)
    require(pool == value, "Origin completion changed while rereading its complete pool")
    for uid, ref in pool["window_refs"].items():
        row = strict_load(checked(ref, workspace))
        require(row["counterfactual"] == "HALF_TEMPORAL_GROUP_CIRCULAR_SHIFT_PER_VIEW"
                and row.get("control_ref") is not None,
                "Origin must retain the complete contrast path and adopted TIME control for each window")
        checked(row["control_ref"], workspace)
        require(all(row["slots"][slot]["sample_seed"] == sample_seed(row["source_sha256"], uid, slot)
                    for slot in (1, 2)), "Origin sample seeds differ from this exact frozen candidate pool")
    checked(pool_ref, workspace)
    return pool


def _accounting(pool):
    return dict(counts=deepcopy(ZERO_COUNTS), counts_role=COUNTS_ROLE,
        adopted_origin_counts=deepcopy(pool["counts"]), adopted_origin_budget=deepcopy(pool["budget"]),
        runtime=deepcopy(pool["runtime"]), runtime_identity_role=RUNTIME_ROLE,
        model_runtime_created=False, frozen_model_verification_performed_here=False,
        actual_new_qwen_calls=0, actual_gpu_execution=False, actual_linear_fits=0)


def production_from_pool(config, manifest, binding, directory, budget, args):
    """Optional critic production route; existing single-candidate routes remain."""
    from .admission import production_refs
    from . import run
    run.required(args, "candidate", "review_run", "production_assets", "formal_qa", "admission", "production_pool")
    require(args.candidate == "critic", "Explicit pool reuse is only available for the critic")
    reviewed = run.load_review(args.review_run, binding, manifest, "critic")
    formal = run.asset_api.load_assets(args.production_assets, verify_files=True)
    run.require_production_assets(manifest, formal)
    save_new(directory / "formal_asset_preflight.json", dict(status="PASS_FORMAL_ASSET_BYTES_CPU_REUSE",
        production_assets_ref=reference(args.production_assets), model_loaded=False,
        report=run.asset_api.preflight_assets(formal, "production", verify_files=False)))
    budget.check(force_disk=True)
    expected = production_refs(binding, reviewed, args.review_run, args.production_assets,
                               args.formal_qa, production_pool=args.production_pool)
    admitted = strict_load(checked(reference(args.admission), manifest["workspace_root"]))
    admission_gate(admitted, "production", "critic", expected, manifest["workspace_root"])
    require(config["max_production_sources"] == 426 and config["max_production_windows"] == 522,
            "CPU reuse cannot reduce the formal426/522 denominator")
    store = run.NativeInputStore(formal, "production")
    journal = run.Journal(directory / "events.jsonl")
    try:
        pool = validate_origin(expected["production_pool_ref"], binding, manifest, formal, reviewed,
                               expected["formal_qa_ref"], store)
        budget.check()
        fitted = run.load_fit(checked(reviewed["fit_ref"], store.workspace), binding, manifest)
        require(same_reference(fitted["weights_ref"], reviewed["weights_ref"]),
                "Reuse must apply the critic weights admitted by its independent review")
        head = fitted["heads"]["content"]
        selected = {sid: choose(source, score_source(head, source))["selected_ordinals"]
                    for sid, source in pool["sources"].items()}
        selection_ref = save_new(directory / "selection.json", dict(schema="AIC_CONTENT_CHOICE_SELECTION_V1",
            sources={sid: dict(status="ACCEPTED", selected_ordinals=values) for sid, values in selected.items()}))
        accounting = _accounting(pool)
        refs = {key: expected[key] for key in ("production_pool_ref", *ORIGIN_REF_FIELDS)}
        receipt = dict(schema=RECEIPT_SCHEMA, status="PASS_CPU_RECOMPUTED_ALL426_CRITIC_DECISIONS",
            execution_mode=MODE, **binding, **refs, **accounting,
            review_ref=expected["review_ref"], weights_ref=reviewed["weights_ref"],
            production_assets_ref=expected["production_assets_ref"], formal_qa_ref=expected["formal_qa_ref"],
            admission_ref=reference(args.admission), selection_ref=selection_ref, source_count=426, window_count=522)
        receipt_ref = save_new(directory / "cpu_reuse_verification.json", receipt)
        journal("cpu_critic_pool_reuse_complete", dict(production_pool_ref=expected["production_pool_ref"],
            selection_ref=selection_ref, new_counts=ZERO_COUNTS, original_cost_charged_to_origin_only=True))
        journal.close()
        checked(expected["production_pool_ref"], store.workspace)
        budget.check(force_disk=True)
        return save_new(directory / "completion.json", dict(schema="AIC_CONTENT_CHOICE_PRODUCTION_V1",
            status="COMPLETE_PRODUCTION_NOT_PACKAGED", candidate="critic", execution_mode=MODE,
            **binding, **refs, **accounting, production_assets_ref=expected["production_assets_ref"],
            review_ref=expected["review_ref"], formal_qa_ref=expected["formal_qa_ref"],
            weights_ref=reviewed["weights_ref"], admission_ref=reference(args.admission), selection_ref=selection_ref,
            source_count=426, window_count=522, actual_pipeline_parameters=pipeline_parameters("critic"),
            cpu_reuse_verification_ref=receipt_ref, event_journal_ref=reference(directory / "events.jsonl"),
            budget=budget.snapshot(), labels_read=False, automatic_package=False, website_submitted=False))
    finally:
        if not journal.stream.closed:
            journal.close()
        store.close()


def load_reused_production(complete, binding, manifest, formal, store, reviewed):
    """Independent package reread; never reinterpret origin costs as new calls."""
    from .admission import production_refs
    require(complete.get("schema") == "AIC_CONTENT_CHOICE_PRODUCTION_V1"
            and complete.get("status") == "COMPLETE_PRODUCTION_NOT_PACKAGED"
            and complete.get("candidate") == "critic" and complete.get("execution_mode") == MODE
            and complete.get("source_count") == 426 and complete.get("window_count") == 522
            and complete.get("labels_read") is False
            and "frozen_verification_ref" not in complete and "torch_checks_ref" not in complete
            and "window_refs" not in complete and "sources" not in complete,
            "A complete CPU reuse result must explicitly reference its origin, not pose as a new model run")
    bind_artifact(complete, binding)
    workspace = manifest["workspace_root"]
    checked(complete["production_pool_ref"], workspace)
    expected = production_refs(binding, reviewed, complete["review_ref"]["path"],
        formal["_asset_manifest_ref"]["path"], complete["formal_qa_ref"]["path"],
        production_pool=complete["production_pool_ref"]["path"])
    for key, ref in expected.items():
        if key in ("plan_ref", "collect_check_ref", "fit_ref", "collect_train_ref"):
            continue  # These are bound by the independently reloaded review/admission.
        require(key in complete and same_reference(complete[key], ref), "CPU reuse origin/review binding changed: " + key)
        checked(complete[key], workspace)
    admitted = strict_load(checked(complete["admission_ref"], workspace))
    admission_gate(admitted, "production", "critic", expected, workspace)
    pool = validate_origin(complete["production_pool_ref"], binding, manifest, formal, reviewed,
                           complete["formal_qa_ref"], store)
    accounting = _accounting(pool)
    require(all(complete.get(key) == value for key, value in accounting.items())
            and all(type(value) is int for value in complete["counts"].values()),
            "CPU reuse new-call accounting changed or duplicated the origin's model cost")
    receipt = strict_load(checked(complete["cpu_reuse_verification_ref"], workspace))
    require(receipt.get("schema") == RECEIPT_SCHEMA
            and receipt.get("status") == "PASS_CPU_RECOMPUTED_ALL426_CRITIC_DECISIONS"
            and all(receipt.get(key) == complete[key] for key in (
                "execution_mode", "config_ref", "asset_manifest_ref", "code_identity", "production_pool_ref",
                *ORIGIN_REF_FIELDS, *accounting, "review_ref", "weights_ref", "production_assets_ref",
                "formal_qa_ref", "admission_ref", "selection_ref", "source_count", "window_count")),
            "CPU reuse receipt differs from the immutable origin or independent critic decision")
    checked(complete["event_journal_ref"], workspace)
    return pool
