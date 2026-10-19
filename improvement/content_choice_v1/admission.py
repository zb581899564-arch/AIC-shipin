"""Prepare an unapproved execution-agent review record; never run a model/job."""
from __future__ import annotations

if __package__ in (None, ""):
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "improvement.content_choice_v1"

import argparse
from pathlib import Path

from .contracts import (CANDIDATES, bind_artifact, checked, code_identity, reference,
    require, same_reference, save_new, strict_load, validate_config)


def production_refs(binding, reviewed, review_path, formal_path, formal_qa, *, production_pool=None):
    expected = dict(config_ref=binding["config_ref"], asset_manifest_ref=binding["asset_manifest_ref"],
        review_ref=reference(review_path), production_assets_ref=reference(formal_path),
        formal_qa_ref=reference(formal_qa), plan_ref=reviewed["plan_ref"],
        collect_check_ref=reviewed["collect_check_ref"])
    for key in ("fit_ref", "weights_ref", "observation_ref", "collect_train_ref"):
        if key in reviewed:
            expected[key] = reviewed[key]
    if production_pool is not None:
        from .reuse import production_pool_refs
        expected.update(production_pool_refs(production_pool))
    return expected


def package_refs(binding, complete, complete_path, formal_path):
    result = dict(config_ref=binding["config_ref"], asset_manifest_ref=binding["asset_manifest_ref"],
        production_assets_ref=reference(formal_path), production_completion_ref=reference(complete_path),
        selection_ref=complete["selection_ref"], review_ref=complete["review_ref"])
    if complete.get("execution_mode") is not None:
        from .reuse import MODE, ORIGIN_REF_FIELDS
        require(complete["execution_mode"] == MODE and complete.get("candidate") == "critic",
                "Unknown production reuse mode")
        result.update({key: complete[key] for key in ("production_pool_ref", *ORIGIN_REF_FIELDS,
                                                      "weights_ref", "cpu_reuse_verification_ref")})
    return result


def main(argv=None):
    from improvement.native_preference_v1 import assets as asset_api
    from improvement.native_preference_v1.run import require_production_assets
    from .run import load_review
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--action", required=True, choices=("production", "package"))
    parser.add_argument("--candidate", required=True, choices=CANDIDATES)
    for name in ("config", "assets", "production-assets", "output"):
        parser.add_argument("--" + name, required=True, type=Path)
    for name in ("review-run", "formal-qa", "production-run", "production-pool"):
        parser.add_argument("--" + name, type=Path)
    args = parser.parse_args(argv)
    require(args.production_pool is None or (args.action == "production" and args.candidate == "critic"),
            "--production-pool is only valid for an explicit critic production review")
    validate_config(strict_load(args.config))
    manifest = asset_api.load_assets(args.assets)
    formal = asset_api.load_assets(args.production_assets)
    require_production_assets(manifest, formal)
    binding = dict(code_identity=code_identity(), config_ref=reference(args.config),
                   asset_manifest_ref=reference(args.assets))
    if args.action == "production":
        require(args.review_run and args.formal_qa, "Explicit --review-run and --formal-qa required")
        reviewed = load_review(args.review_run, binding, manifest, args.candidate)
        expected = production_refs(binding, reviewed, args.review_run, args.production_assets, args.formal_qa,
                                   production_pool=args.production_pool)
    else:
        require(args.production_run, "Explicit --production-run required")
        complete = strict_load(checked(reference(args.production_run), manifest["workspace_root"]))
        bind_artifact(complete, binding)
        require(complete.get("status") == "COMPLETE_PRODUCTION_NOT_PACKAGED"
                and complete.get("candidate") == args.candidate
                and same_reference(complete["production_assets_ref"], reference(args.production_assets)),
                "A complete separate production result is required")
        load_review(complete["review_ref"]["path"], binding, manifest, args.candidate)
        expected = package_refs(binding, complete, args.production_run, args.production_assets)
    for value in expected.values():
        checked(value, manifest["workspace_root"])
    output = args.output.resolve()
    require(output.is_relative_to(Path(manifest["workspace_root"]).resolve())
            and not output.is_relative_to(Path(manifest["model_spec"]["model_dir"]).resolve()),
            "Private draft must remain inside the workspace and outside the model directory")
    result = save_new(output, dict(schema="AIC_CONTENT_CHOICE_ADMISSION_V1", candidate=args.candidate,
        action=args.action, approved=False, reviewed_by="", reviewed_at="", review_notes="",
        draft_only=True, automatic_execution=False, **expected))
    print(__import__("json").dumps(dict(status="UNAPPROVED_DRAFT_ONLY", output=result)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
