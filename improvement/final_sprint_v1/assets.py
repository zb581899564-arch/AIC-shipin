"""Bind existing private assets to a new sprint without copying media or clocks.

Only explicit paths are adopted.  Historical launchers and admissions are never
executed.  This module knows the actual package_inputs/source_clocks schema used
by the October 22 production packages; binding it does not revive that experiment.
"""
from __future__ import annotations

from datetime import datetime, timezone
from fractions import Fraction
import json
import math
from pathlib import Path
import subprocess

from .contracts import (atomic_new, checked, iter_refs, protected_baselines, ref, require,
                        save_new, stable_key, strict_load, total_parameters, utc_now, validate_sources)

BASE_COMMIT = "e8224c4339007790a1be383be19fdb200cc817bc"
HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
SCHEMA = "AIC_FINAL_SPRINT_ASSETS_V1"


def code_identity():
    """A closed identity of the new implementation, separate from frozen history."""
    files = sorted(p for p in HERE.iterdir() if p.suffix in {".py", ".json"})
    return {"base_commit": BASE_COMMIT,
            "files": {p.name: ref(p)["sha256"] for p in files}}


def git_identity(expected_commit=None):
    def git(*args):
        return subprocess.check_output(["git", "-C", str(REPO), *args], text=True).strip()
    head = git("rev-parse", "HEAD")
    require(len(head) == 40, "A real full Git commit is required")
    if expected_commit:
        require(head == expected_commit, "Checkout is not the explicitly requested full commit")
    require(not git("status", "--porcelain", "--untracked-files=no"),
            "Tracked source changes must be committed before Linux execution")
    relative = HERE.relative_to(REPO).as_posix()
    tracked = {Path(name).name for name in git("ls-tree", "-r", "--name-only", "HEAD", "--", relative).splitlines()
               if Path(name).parent.as_posix() == relative and Path(name).suffix in {".py", ".json"}}
    actual = {p.name for p in HERE.iterdir() if p.is_file() and p.suffix in {".py", ".json"}}
    require(actual == tracked, "Every sprint Python/config file must exist in the pinned Git commit")
    subprocess.run(["git", "-C", str(REPO), "merge-base", "--is-ancestor", BASE_COMMIT, head], check=True)
    return {"commit": head, "code": code_identity()}


def _identity(value):
    if isinstance(value, str):
        return ref(value)
    checked(value)
    return dict(value)


def _tree(directory):
    root = Path(directory).resolve(strict=True)
    require(root.is_dir(), "Explicit existing model/source directory required")
    paths = sorted(p for p in root.rglob("*") if p.is_file() and
                   ".git" not in p.relative_to(root).parts and
                   "__pycache__" not in p.relative_to(root).parts)
    require(paths, "Empty asset tree")
    return {"directory": str(root), "files": [dict(relative_path=str(p.relative_to(root)), **ref(p))
                                               for p in paths]}


def _qwen_spec(mapping):
    value = dict(mapping)
    model_dir = Path(value["model_dir"]).resolve(strict=True)
    # No 'latest', model search, symlink retargeting or implicit Hub download.
    tree = _tree(model_dir)
    inventory = {r["relative_path"]: r for r in tree["files"]}
    require("config.json" in inventory, "Qwen config.json missing")
    config = strict_load(checked(inventory["config.json"]))
    require(config.get("model_type") == "qwen3_vl", "Expected the existing Qwen3-VL family")
    weights = [r for name, r in inventory.items() if name.endswith(".safetensors")]
    require(weights, "Exact local safetensors shards required")
    if "model.safetensors.index.json" in inventory:
        names = set(strict_load(checked(inventory["model.safetensors.index.json"]))["weight_map"].values())
        require(names == {r["relative_path"] for r in weights}, "Missing/extra model shard inventory")
    require(isinstance(value.get("revision"), str) and value["revision"].strip(),
            "Existing model provenance revision must be supplied explicitly")
    value.update(model_dir=str(model_dir), asset_tree=tree, weight_files=weights, files=tree["files"],
                 expected_base_parameters=8767123696,
                 local_files_only=True, trust_remote_code=False, role="base")
    # New mechanisms use raw BASE.  Original TIME remains an inherited dependency
    # only when a candidate actually adopts the protected temporal selection.
    require(not value.get("adapter_dir"), "New raw-BASE routes do not silently load a TIME/failed actor")
    return value


def normalize_color_policy(color):
    """Adopt the existing complete config/policy without silently dropping its sources."""
    color_ref = None
    if isinstance(color, str) or (isinstance(color, dict) and "path" in color):
        color_ref = _identity(color)
        color = strict_load(checked(color_ref))
    if "source_color_repair" in color:
        color = color["source_color_repair"]
    if "sources" in color:
        require(isinstance(color["sources"], dict) and "matrix" in color and
                "transfer_tag_for_conversion" in color, "Incomplete original color repair policy")
        color = {sha: dict(profile, source_sha256=sha,
                    matrix=color["matrix"], transfer_tag_for_conversion=color["transfer_tag_for_conversion"])
                 for sha, profile in color["sources"].items()}
    require(isinstance(color, dict), "Explicit source-SHA color policy required")
    return color, color_ref


def _source_rows(package_inputs, base_rows, mapping):
    metadata_ref = _identity(package_inputs["metadata"])
    clocks_ref = _identity(package_inputs["source_clocks"])
    metadata = strict_load(checked(metadata_ref))
    clocks = strict_load(checked(clocks_ref))
    originals = {row["video_id"]: row for row in base_rows}
    records = metadata["records"]
    require(len(records) == 426 and set(originals) == {str(i) for i in range(426)},
            "Actual protected426/source metadata required")
    color, color_ref = normalize_color_policy(mapping.get("color_repairs", {}))
    result = []
    for row in records:
        sid = row["video_id"]
        require(sid in clocks and sid in originals, "Source metadata/index mismatch")
        path = Path(row["source_path"]).resolve(strict=True)
        media = {"path": str(path), "bytes": path.stat().st_size,
                 "sha256": row["source_sha256"]}
        clock = clocks[sid]
        require(clock["source_sha256"] == media["sha256"], "Clock/media identity mismatch")
        source = dict(video_id=sid, media=media, clock=dict(clocks_ref, source_key=sid),
                      width=row["width"], height=row["height"], n_frames=row["n_frames"],
                      targetRatioWH=originals[sid]["targetRatioWH"],
                      index_row={k: v for k, v in originals[sid].items()
                                 if k not in {"predictions", "model_params_b"}})
        if media["sha256"] in color:
            recipe = color[media["sha256"]]
            require(recipe.get("source_sha256") == media["sha256"] and
                    recipe.get("width") == row["width"] and recipe.get("height") == row["height"] and
                    all(key in recipe for key in ("matrix", "transfer_tag_for_conversion", "format",
                                                  "color_trc", "colorspace", "color_primaries", "color_range")),
                    "Frozen color policy does not match source geometry/identity")
            source["color_conversion"] = recipe
        result.append(source)
    require({s["video_id"] for s in result} == set(originals), "Duplicate/missing source metadata")
    inherited = {"metadata": metadata_ref, "source_clocks": clocks_ref}
    if color_ref is not None:
        inherited["source_color_repair"] = color_ref
    return result, inherited


def bind(mapping_path, output_path, *, expected_commit=None):
    """Write a compact, exact local asset lock; no video decode or GPU work."""
    from .packaging import read_zip_rows
    mapping = strict_load(mapping_path)
    mapping_sha = ref(mapping_path)["sha256"]
    require(mapping.get("schema") == "AIC_FINAL_SPRINT_MAPPING_V1", "Wrong mapping schema")
    root = Path(mapping["run_root"]).resolve()
    workspace = Path(mapping["workspace_root"]).resolve(strict=True)
    require(root.is_relative_to(workspace) and root != workspace, "New run root must stay in the Linux workspace")
    require(root.name not in {"t_branch_execution_20261022_v1", "CONTROL5"}, "New sprint root required")
    baselines = {k: _identity(v) for k, v in mapping["protected_baselines"].items()}
    protected_baselines(baselines)
    package_ref = _identity(mapping["package_inputs"])
    package = strict_load(checked(package_ref))
    sources, inherited = _source_rows(package, read_zip_rows(checked(baselines["40.48"])), mapping)
    qwen = _qwen_spec(mapping["qwen"])
    dependencies = [_identity(r) for r in mapping.get("baseline_parameter_receipts", [])]
    deadline = datetime.fromisoformat(mapping["deadline"].replace("Z", "+00:00"))
    require(deadline.tzinfo is not None, "Deadline must carry the user's timezone")
    require(0 < (deadline - datetime.now(timezone.utc)).total_seconds() <= 24 * 3600,
            "Deadline must be inside the user-provided remaining24h window")
    value = {"schema": SCHEMA, "created_at": utc_now(), "mapping_sha256": mapping_sha, "source_commit": git_identity(expected_commit),
             "workspace_root": str(workspace), "run_root": str(root), "deadline": mapping["deadline"],
             "deadline_source": "USER_QQ_UPDATE_NOT_INDEPENDENTLY_VERIFIED_EXTENSION",
             "protected_baselines": baselines, "sources": sources, "qwen": qwen,
             "baseline_parameter_receipts": dependencies,
             "baseline_registration_provenance": mapping.get("baseline_registration_provenance"),
             "baseline_inventory_completion": mapping.get("baseline_inventory_completion"),
             "baseline_expected_parameters": 8816809946,
             "adopted_inputs": {"package_inputs": package_ref, **inherited},
             "resources": dict(mapping["resources"]),
             "offline_quality_gate": "EXPLICITLY_SKIPPED_NEW_PRODUCTION_RISK_EXPLORATION",
             "automatic_website_submission": False}
    if mapping.get("specialist"):
        expert = dict(mapping["specialist"])
        expert["source_tree"] = _tree(expert["source_dir"])
        for key in ("checkpoint", "clip_checkpoint"):
            expert[key] = _identity(expert[key])
        expert["source_dir"] = expert["source_tree"]["directory"]
        expert["source"] = {"path": expert["source_dir"],
                            "commit": "3e841d3d662c8440afed514908566fed2d5e82a7",
                            "tree_sha": "271085c23c2619f0336186304e7eeb5be328e4cd"}
        value["specialist"] = expert
        clock_documents, total_cells = {}, 0
        for source in sources:
            clock_ref = source["clock"]
            key = (clock_ref["path"], clock_ref["sha256"])
            if key not in clock_documents:
                clock_documents[key] = strict_load(checked(clock_ref))
            clock = clock_documents[key][source["video_id"]]
            total_cells += math.ceil(Fraction(clock["physical_end_exact"]) / 2)
        compact_features = 8192 * total_cells + 300000 * 427
        value["resources"]["planned_output_bytes"] = max(value["resources"]["planned_output_bytes"],
                                                           (1 << 30) + compact_features)
        value["capacity_estimate"] = {"native2second_cells": total_cells,
            "compact_shared_feature_and_query_bytes": compact_features,
            "other_routes_proofs_and_journal_allowance_bytes": 1 << 30,
            "basis": "8192*sum(ceil(native_duration/2))+300000*427;lossless_f32_base64;not_weight_downloads",
            "first_production_sources_must_check_actual_growth": True}
    if dependencies:
        validate_baseline_auxiliaries(value)
    # Dedicated sprint output ownership, without changing any adopted model tree.
    forbidden_trees = [Path(qwen["model_dir"]).resolve()]
    if value.get("specialist"):
        forbidden_trees.append(Path(value["specialist"]["source_dir"]).resolve())
    for directory in mapping.get("protected_directories", []):
        forbidden_trees.append(Path(directory).resolve(strict=True))
    require(not any(root.is_relative_to(directory) for directory in forbidden_trees),
            "New sprint output cannot enter an adopted model/code/protected dependency directory")
    value["protected_directories"] = [str(path) for path in forbidden_trees]
    marker_path = root / "sprint_owner.json"
    owner = {"schema": "AIC_FINAL_SPRINT_OWNER_V1", "mapping_sha256": mapping_sha,
             "run_root": str(root), "source_commit": value["source_commit"]}
    if root.exists():
        require(root.is_dir(), "New sprint root is not a directory")
        if marker_path.exists():
            require(strict_load(marker_path) == owner, "Run root belongs to different sprint assets/code")
        else:
            require(not any(root.iterdir()), "Existing nonempty directory is not owned by this new sprint")
    # Check outputs against every adopted dependency before creating directories.
    for identity in iter_refs(value):
        require(not Path(identity["path"]).resolve().is_relative_to(root),
                "New output root contains an existing adopted asset")
    validate_sources(sources, verify_media=True)
    root.mkdir(parents=True, exist_ok=True)
    if not marker_path.exists():
        atomic_new(marker_path, owner)
    if Path(output_path).exists():
        old = strict_load(output_path)
        require(old.get("mapping_sha256") == mapping_sha and old.get("source_commit") == value["source_commit"],
                "Existing asset lock belongs to a different mapping/code")
        # created_at is observational only; every executable binding must match.
        require({k: v for k, v in old.items() if k != "created_at"} ==
                {k: v for k, v in value.items() if k != "created_at"}, "Asset lock bytes/identities drifted")
        value = old
    else:
        atomic_new(output_path, value)
    return {"status": "BOUND_EXISTING_PRIVATE_ASSETS_NO_MODEL_CALLS", "asset_lock": ref(output_path),
            "sources": 426, "source_commit": value["source_commit"]}


def load(path, *, expected_commit=None):
    value = strict_load(path)
    require(value.get("schema") == SCHEMA, "Wrong sprint asset schema")
    git = git_identity(expected_commit)
    require(value["source_commit"] == git, "Asset lock belongs to a different immutable implementation")
    protected_baselines(value["protected_baselines"])
    owner = strict_load(Path(value["run_root"]) / "sprint_owner.json")
    require(owner == {"schema": "AIC_FINAL_SPRINT_OWNER_V1", "mapping_sha256": value["mapping_sha256"],
                      "run_root": value["run_root"], "source_commit": value["source_commit"]},
            "Sprint run-root ownership differs")
    for tree in [value["qwen"]["asset_tree"]] + ([value["specialist"]["source_tree"]] if value.get("specialist") else []):
        for identity in tree["files"]:
            checked(identity)
    return value


def candidate_registry():
    return strict_load(HERE / "candidates.json")


def binding(assets, assets_path, candidate_id):
    candidates = candidate_registry()["candidates"]
    require(candidate_id in candidates, "Candidate ID is not preregistered")
    candidate = candidates[candidate_id]
    require(candidate["implementation_status"] == "IMPLEMENTED", "Research-only candidate cannot launch")
    return {"candidate_id": candidate_id, "candidate": candidate,
            "asset_lock": ref(assets_path), "source_commit": assets["source_commit"],
            "registry_ref": ref(HERE / "candidates.json"),
            "protected_baselines": assets["protected_baselines"],
            "required_model_components": candidate["required_model_components"]}


def validate_baseline_inventory(assets, qwen_ref):
    """Count real current BASE plus all inherited40.48 dependency inventories."""
    dependencies = assets.get("baseline_parameter_receipts", [])
    require(dependencies, "Exact loaded TIME/semantic/I3D/UMT inventories must be bound before baseline reuse")
    budget = total_parameters([qwen_ref, *dependencies])
    require(budget["total_elements"] == 8_816_809_946,
            "Actual baseline dependency union differs from the accepted40.48 pipeline; inspect missing/double-counted tensors")
    return budget


def validate_baseline_auxiliaries(assets):
    """Prove actual inherited tensors came from the exact original registrations."""
    provenance = assets.get("baseline_registration_provenance")
    completion_ref = assets.get("baseline_inventory_completion")
    require(isinstance(provenance, dict) and completion_ref,
            "Original baseline registration provenance and CPU inventory completion required")
    require(provenance.get("schema") == "AIC_FINAL_BASELINE_DEPENDENCIES_V1" and
            provenance.get("protected_baselines") == assets["protected_baselines"],
            "Baseline dependency provenance refers to different protected archives")
    for identity in iter_refs(provenance):
        checked(identity)
    completion = strict_load(checked(completion_ref))
    dependencies = assets["baseline_parameter_receipts"]
    require(completion.get("schema") == "AIC_FINAL_BOOTSTRAP_INVENTORY_COMPLETION_V1" and
            completion.get("baseline_provenance") == provenance and
            completion.get("parameter_receipts") == dependencies,
            "Bound baseline inventories differ from their actual completed bootstrap")
    names = set()
    for identity in dependencies:
        receipt = strict_load(checked(identity))
        component = receipt.get("component_id")
        require(component in provenance["checkpoint_refs"] and component not in names and
                receipt.get("baseline_provenance") == provenance and
                receipt.get("weight_files") == [provenance["checkpoint_refs"][component]],
                "Inherited component is not the checkpoint used by the protected baseline")
        names.add(component)
    require(names == {"original_time", "semantic_residual", "i3d", "sport_umt"},
            "All four actual inherited auxiliary components are required")
    actual = total_parameters(dependencies)
    require(actual["total_elements"] == 49_686_250, "Actual inherited auxiliary tensor union differs")
    return actual
