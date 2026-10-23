"""Prepare explicit cross-code pure-call adoption; no decode/token replay/model.

Each --parent is a JSON object or JSON file with old_assets, wrapper and
source_dir (the exact old final_sprint_v1 directory). Parent order pins ties.
Actual new-asset compatibility is mandatory later at bind and runtime.
"""
from __future__ import annotations

import argparse
import ast
import copy
import json
from pathlib import Path
import re

from .contracts import atomic_new, checked, ref, require, stable_key, strict_load, strict_loads
from .pure_call_adoption import (COMMON, SCHEMA, collect_rows, compatible_assets,
                                 parent_documents, validate_row)

HERE = Path(__file__).resolve().parent
WHOLE_FILES = ("specialist.py", "observation.py", "grounding_grammar.py")
PRODUCERS = {
    "qwen_runtime.py": ("QwenRuntime.generate_images", "QwenRuntime.ground_image", "QwenRuntime._chat",
                        "QwenRuntime._check_encoded", "QwenRuntime._role", "_tensor_signature",
                        "_original_base_identity", "_parameter_inventory", "_verify_files"),
    "runner.py": ("Engine.query", "Engine.specialist_selection", "Engine.ground"),
}
OPT_IN = {
    "__init__": ("from .numeric_precision import requested_profile",
                 "self.arithmetic_profile = requested_profile(self.spec)", "self.arithmetic_conversion = None"),
    "load": ("arithmetic_conversion = None", "self.arithmetic_conversion = arithmetic_conversion",
             "if self.arithmetic_profile:\n from .numeric_precision import lossless_fp32_conversion\n"
             " arithmetic_conversion = lossless_fp32_conversion(base, torch, original_base_identity)"),
}


def source_files(directory, expected=None):
    root = Path(directory).resolve(strict=True)
    require(root.is_dir(), "Explicit implementation source directory required")
    files = {p.name: ref(p) for p in sorted(root.iterdir()) if p.is_file() and p.suffix in {".py", ".json"}}
    require(files and all(Path(name).name == name for name in files), "Empty/unsafe source inventory")
    if expected is not None:
        require({name: item["sha256"] for name, item in files.items()} == expected,
                "Source directory bytes differ from immutable source_commit.code.files")
    return files


def _node(tree, dotted):
    current = tree
    for name in dotted.split("."):
        found = [item for item in current.body if isinstance(item, (ast.ClassDef, ast.FunctionDef)) and item.name == name]
        require(len(found) == 1, "Missing/ambiguous audited producer: " + dotted)
        current = found[0]
    return current


def _dump(node):
    return ast.dump(node, include_attributes=False)


def _default_bf16(node, method):
    """Erase only the reviewed, exact opt-in statements; reject all other edits."""
    result = copy.deepcopy(node)
    permitted = {_dump(ast.parse(text).body[0]) for text in OPT_IN[method]}
    result.body = [statement for statement in result.body if _dump(statement) not in permitted]
    return _dump(result)


def _prompt(tree):
    values = [item.value for item in tree.body if isinstance(item, ast.Assign)
              and any(isinstance(target, ast.Name) and target.id == "GROUNDING_PROMPT" for target in item.targets)]
    require(len(values) == 1, "One actual grounding prompt literal required")
    value = ast.literal_eval(values[0])
    require(isinstance(value, str) and value, "Invalid actual grounding prompt")
    return value


def audit_sources(old, old_directory, new_sources):
    old_sources = source_files(old_directory, old["source_commit"]["code"]["files"])
    for name, identity in new_sources.items():
        require(Path(name).name == name, "Unsafe source inventory member")
        checked(identity)
    for name in WHOLE_FILES:
        require(old_sources[name]["sha256"] == new_sources[name]["sha256"], "Changed independent producer file: " + name)
    fingerprints = {}
    trees = {}
    for name, names in PRODUCERS.items():
        before, after = [ast.parse(checked(files[name]).read_text(encoding="utf-8")) for files in (old_sources, new_sources)]
        trees[name] = (before, after)
        for dotted in names:
            old_ast, new_ast = [_dump(_node(tree, dotted)) for tree in (before, after)]
            require(old_ast == new_ast, "Changed independent producer AST: " + dotted)
            fingerprints[name + ":" + dotted] = stable_key(old_ast)
    for method in OPT_IN:
        before, after = [_node(tree, "QwenRuntime." + method) for tree in trees["qwen_runtime.py"]]
        old_default, new_default = [_default_bf16(node, method) for node in (before, after)]
        require(old_default == new_default, "Default BF16 loader changed: " + method)
        fingerprints["qwen_runtime.py:default_BF16_" + method] = stable_key(old_default)
    prompts = [_prompt(ast.parse(checked(files["spatial.py"]).read_text(encoding="utf-8")))
               for files in (old_sources, new_sources)]
    configurations = [strict_load(checked(files["candidates.json"]))["shared_spatial_configuration"]
                      for files in (old_sources, new_sources)]
    require(prompts[0] == prompts[1] and configurations[0] == configurations[1],
            "Actual grounding prompt/shared spatial configuration changed")
    return dict(source_files=old_sources, whole_files=list(WHOLE_FILES), producer_fingerprints=fingerprints,
                grounding_prompt_sha256=stable_key(prompts[0]), shared_spatial_configuration=configurations[0],
                default_BF16_load_unchanged_after_exact_opt_in_statements=True)


def _identity(value):
    if isinstance(value, str):
        return ref(value)
    checked(value)
    return value


def prepare_manifest(specifications, expected_commit, source_dir=HERE, new_assets=None):
    require(re.fullmatch(r"[0-9a-f]{40}", expected_commit) is not None, "Full new implementation commit required")
    require(specifications, "At least one explicitly ordered parent required")
    new_sources = source_files(source_dir)
    parents, rows, excluded, common, expert = [], [], [], None, None
    for index, spec in enumerate(specifications):
        parent = dict(old_assets=_identity(spec["old_assets"]), wrapper=_identity(spec["wrapper"]),
                      source_dir=str(Path(spec["source_dir"]).resolve(strict=True)))
        old, _ = parent_documents(parent)
        if common is None:
            common = old
        require(all(old[key] == common[key] for key in COMMON), "Ordered parents have different shared model/inputs")
        require("arithmetic_profile" not in old["qwen"], "Old FP32 calls are not eligible for BF16 adoption")
        if old.get("specialist"):
            expert = old["specialist"] if expert is None else expert
            require(old["specialist"] == expert, "Ordered parents have different specialist")
        parent["source_audit"] = audit_sources(old, parent["source_dir"], new_sources)
        parents.append(parent)
        found, omitted = collect_rows(parent, index)
        rows.extend(found)
        excluded.extend(omitted)
    previous = {}
    for row in rows:
        entry = validate_row(row)
        first = previous.setdefault(row["task_id"], entry)
        require(first["call_binding"] == entry["call_binding"] and first["semantic_sha256"] == entry["semantic_sha256"],
                "Duplicate task has conflicting request or semantic output")
    require(rows, "No complete independent calls eligible for adoption")
    if new_assets is not None:
        require(new_assets["source_commit"]["commit"] == expected_commit
                and new_assets["source_commit"]["code"]["files"] == {n: r["sha256"] for n, r in new_sources.items()},
                "Optional new asset implementation/source differs")
        for parent in parents:
            compatible_assets(strict_load(checked(parent["old_assets"])), new_assets)
    return dict(schema=SCHEMA, new_implementation=expected_commit, new_sources=new_sources,
                parents=parents, rows=rows, excluded=excluded, new_inference_calls=0,
                original_failure_and_costs_not_modified=True,
                actual_new_asset_compatibility="MANDATORY_AT_BIND_AND_RUNTIME")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parent", action="append", required=True, help="Encoded JSON spec or exact JSON spec path")
    parser.add_argument("--expected-commit", required=True)
    parser.add_argument("--source-dir", default=str(HERE))
    parser.add_argument("--new-assets")
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    specs = [strict_loads(item) if item.lstrip().startswith("{") else strict_load(item) for item in args.parent]
    value = prepare_manifest(specs, args.expected_commit, args.source_dir,
                             strict_load(args.new_assets) if args.new_assets else None)
    identity = atomic_new(args.output, value)
    print(json.dumps(dict(status="PURE_CALL_ADOPTION_PREPARED_NO_NEW_INFERENCE", manifest=identity,
                          rows=len(value["rows"]), excluded=len(value["excluded"])), sort_keys=True))


if __name__ == "__main__":
    main()
