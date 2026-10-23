"""Small public command surface; all predictions and proofs stay on owned Linux."""
from __future__ import annotations

import argparse
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import sys

from .contracts import checked, ref, require, strict_load, validate_sources


def configure_process(assets):
    threads = assets["resources"]["cpu_threads"]
    require(type(threads) is int and 1 <= threads <= 2, "Protect Java: one or two CPU threads only")
    for name in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
        os.environ[name] = str(threads)
    os.environ["TOKENIZERS_PARALLELISM"] = "false"
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["HF_DATASETS_OFFLINE"] = "1"
    os.environ["TMPDIR"] = assets["resources"]["scratch_dir"]
    configured = str(assets["resources"]["gpu_index"])
    if "CUDA_VISIBLE_DEVICES" in os.environ:
        require(os.environ["CUDA_VISIBLE_DEVICES"] == configured,
                "CUDA_VISIBLE_DEVICES must equal the explicit physical GPU index")
    else:
        os.environ["CUDA_VISIBLE_DEVICES"] = configured


def dependencies(candidate):
    required = ["torch", "transformers", "numpy", "PIL", "av", "cv2", "safetensors"]
    if candidate.startswith("m_"):
        required += ["clip", "scipy", "einops"]
    missing = [name for name in required if importlib.util.find_spec(name) is None]
    require(not missing, "Missing existing Linux runtime dependencies: " + ", ".join(missing))
    versions = {}
    for distribution in ("torch", "transformers", "numpy", "av", "safetensors"):
        versions[distribution] = importlib.metadata.version(distribution)
    require(versions["transformers"] == "4.57.1", "Qwen cache interface is pinned to transformers4.57.1")
    return versions


def status(assets):
    from .resources import cumulative_execution
    from .assets import candidate_registry
    root = Path(assets["run_root"])
    states = {}
    for candidate in candidate_registry()["candidates"]:
        directory = root / "candidates" / candidate
        source_files = list((directory / "sources").glob("*/result.json")) if directory.exists() else []
        receipt = directory / "package" / "package_receipt.json"
        states[candidate] = {"durable_source_result_files": len(source_files),
                             "package_receipt": ref(receipt) if receipt.exists() else None}
    unresolved = []
    for pointer in (root / "journal" / "tasks").glob("*/state.json"):
        value = strict_load(pointer)
        attempt = pointer.parent / "attempts" / str(value["active_attempt"])
        if not (attempt / "success.json").exists():
            unresolved.append({"task_id": pointer.parent.name, "state": value["status"],
                               "claim": ref(attempt / "claim.json")})
    return {"status": "READ_ONLY_STATUS", "candidates": states, "unresolved_claims": unresolved,
            "cost": cumulative_execution(assets), "no_media_raw_or_tensor_output": True}


def reconcile_wrapper(assets, assets_path, terminal_path):
    from .resources import resolve_command_budget
    from .runtime_cache import CallJournal
    proof_ref = ref(terminal_path)
    wrapper = strict_load(checked(proof_ref))
    require(wrapper.get("schema") == "AIC_FINAL_OWNED_WRAPPER_V1" and wrapper.get("work_terminated") is True
            and wrapper.get("asset_lock") == ref(assets_path)
            and wrapper.get("no_external_task_signaled") is True, "Exact terminated owned wrapper required")
    journal = CallJournal(Path(assets["run_root"]) / "journal",
        {"asset_lock": ref(assets_path), "code": assets["source_commit"], "no_training": True, "seed": 20261023})
    tasks, commands = [], []
    for item in wrapper["task_terminals"]:
        tasks.append(journal.reconcile(item["task_id"], item["terminal_ref"]))
    for item in wrapper["command_terminals"]:
        commands.append(resolve_command_budget(assets, item["command_id"], item["terminal_ref"]))
    return {"status": "EXACT_TERMINALS_RECONCILED_NO_MODEL_CALLS", "tasks": len(tasks),
            "commands": len(commands), "wrapper_terminal": proof_ref}


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    sub = result.add_subparsers(dest="action", required=True)
    bind = sub.add_parser("bind", help="Hash and bind explicit existing private assets")
    bind.add_argument("--mapping", required=True)
    bind.add_argument("--output", required=True)
    bind.add_argument("--expected-commit", required=True)
    for name in ("preflight", "smoke", "forecast", "run", "package", "status", "reconcile"):
        cmd = sub.add_parser(name)
        cmd.add_argument("--assets", required=True)
        cmd.add_argument("--expected-commit", required=True)
        if name in {"preflight", "smoke", "run", "package"}:
            cmd.add_argument("--candidate", required=True)
        if name == "preflight":
            cmd.add_argument("--gpu", action="store_true", help="Check real available GPU without allocating it")
        if name == "reconcile":
            cmd.add_argument("--wrapper-terminal", required=True)
    return result


def main(argv=None):
    args = parser().parse_args(argv)
    from . import assets as asset_api
    if args.action == "bind":
        result = asset_api.bind(args.mapping, args.output, expected_commit=args.expected_commit)
    else:
        if args.action in {"smoke", "run"}:
            require(os.environ.get("AIC_FINAL_WRAPPER_ID"),
                    "Production commands must use python -m improvement.final_sprint_v1.supervise for bounded owned execution")
        assets = asset_api.load(args.assets, expected_commit=args.expected_commit)
        if args.action in {"preflight", "smoke", "run"}:
            configure_process(assets)
        from . import runner
        if args.action == "preflight":
            require(args.candidate in asset_api.candidate_registry()["candidates"], "Unknown candidate")
            runner.check_baseline_auxiliaries(assets, args.candidate)
            validate_sources(assets["sources"], verify_media=True)
            from .resources import snapshot
            plan = None
            if args.candidate.startswith("g_"):
                plan = runner.grounding_plan(runner.enriched_sources(assets),
                    runner.baseline_frames(assets["protected_baselines"])["40.48"],
                    asset_api.candidate_registry()["shared_spatial_configuration"])
                require(not plan["sources_impossible_under_fixed_cap"],
                        "FIXED_GROUNDING_CAP_INSUFFICIENT: native metadata proves this recipe cannot finish; "
                        "inspect forecast before any GPU work, do not substitute baseline frames on failure")
            result = {"status": "ENGINEERING_PREFLIGHT_PASS_NO_MODEL_INFERENCE",
                      "candidate": args.candidate, "runtime_versions": dependencies(args.candidate),
                      "resources": snapshot(assets, require_gpu=args.gpu),
                      "grounding_plan": plan,
                      "quality_validated": False}
        elif args.action == "forecast":
            result = runner.forecast(assets)
        elif args.action == "smoke":
            dependencies(args.candidate)
            result = runner.smoke(assets, args.assets, args.candidate)
        elif args.action == "run":
            result = runner.run(assets, args.assets, args.candidate)
        elif args.action == "package":
            result = runner.package_only(assets, args.assets, args.candidate)
        elif args.action == "status":
            result = status(assets)
        else:
            result = reconcile_wrapper(assets, args.assets, args.wrapper_terminal)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print(json.dumps({"status": "EXECUTION_FAILED_NOT_EMPTY_PREDICTION", "error_type": type(error).__name__,
                          "error": str(error)}, ensure_ascii=False), file=sys.stderr)
        raise
