"""Admitted CPU packaging through the original hash-bound spatial renderer.

Successful empty predictions remain empty.  Missing/failed sources, a changed
clock, unbound renderer code, any unavailable selected spatial frame, or a
duplicate protected prediction stop packaging and preserve diagnostic files.
"""
from contextlib import contextmanager
import hashlib
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

from .assets import (PIPELINE_PARAMETERS, PROTECTED_SHA256, _clock, _constant, _float, _unique,
                     check_ref, path_ref, read_json, require, same_ref, sha, write_new)
from .contracts import successful_source_selections, validate_admission


def lines(path_or_bytes):
    text = path_or_bytes.decode("utf-8-sig") if isinstance(path_or_bytes, bytes) else Path(path_or_bytes).read_text(encoding="utf-8-sig")
    return [json.loads(line, object_pairs_hook=_unique, parse_constant=_constant, parse_float=_float)
            for line in text.splitlines() if line.strip()]


def dump_lines(path, rows):
    with Path(path).open("x", encoding="utf-8") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n")
        stream.flush(); os.fsync(stream.fileno())


def canonical(rows):
    relevant = [{key: row[key] for key in ("video_id", "targetRatioWH", "predictions")}
                for row in sorted(rows, key=lambda row: row["video_id"])]
    return hashlib.sha256(json.dumps(relevant, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def keymap(rows):
    result = {(row["video_id"], frame["frame"]): frame["bboxes"] for row in rows for frame in row["predictions"]}
    require(len(result) == sum(len(row["predictions"]) for row in rows), "Duplicate source/native prediction")
    return result


def validate_selections(source_selections, source_counts):
    """Pure native-bound validation; [] is accepted, missing/FAILED is rejected."""
    successful_source_selections(source_selections, source_counts)
    for sid, row in source_selections.items():
        require(type(source_counts[sid]) is int and source_counts[sid] > 0
                and all(value < source_counts[sid] for value in row["selected_ordinals"]),
                "Selected ordinal outside the original native clock: " + sid)
    return {(sid, ordinal) for sid, row in source_selections.items() for ordinal in row["selected_ordinals"]}


@contextmanager
def bound_renderer(renderer, workspace):
    """Bind all actual local Python dependencies, including transitive imports."""
    inventory = {str(check_ref(ref, workspace)): ref for ref in renderer["code_refs"]}
    require(len(inventory) == len(renderer["code_refs"]), "Duplicate renderer code reference")
    directories = [Path(path).resolve(strict=True) for path in renderer["import_paths"]]
    require(directories and all(path.is_relative_to(workspace) for path in directories), "Renderer import path escaped workspace")
    strict_root = Path(renderer["strict_loader_root"]).resolve(strict=True)
    require(strict_root.is_relative_to(workspace), "Strict loader escaped workspace")
    actual = {str(path.resolve()) for directory in directories for path in directory.glob("*.py")}
    actual.update(str(path.resolve()) for path in strict_root.rglob("*.py"))
    require(set(inventory) == actual, "Closed renderer/strict-loader Python inventory differs")
    expected = {name: next((directory / (name + ".py") for directory in directories
                           if (directory / (name + ".py")).is_file()), None)
                for name in ("field_contract", "package_contract", "p2j_core", "pts_contract", "a_contract")}
    require(all(path is not None and str(path.resolve()) in inventory for path in expected.values()),
            "Missing actual spatial renderer dependency")
    for name, path in expected.items():
        if name in sys.modules:
            require(getattr(sys.modules[name], "__file__", None) is not None
                    and Path(sys.modules[name].__file__).resolve() == path.resolve(),
                    "An unbound cached module owns renderer dependency " + name)
    before_modules, before_path = set(sys.modules), list(sys.path)
    visibility, had_visibility = os.environ.get("CUDA_VISIBLE_DEVICES"), "CUDA_VISIBLE_DEVICES" in os.environ
    try:
        sys.path[:0] = list(map(str, directories))
        field = importlib.import_module("field_contract")
        pts = importlib.import_module("pts_contract")
        require(Path(field.__file__).resolve() == check_ref(renderer["field_contract_ref"], workspace)
                and Path(pts.__file__).resolve() == check_ref(renderer["pts_contract_ref"], workspace),
                "Actual field/PTS entry code differs")
        for name in set(sys.modules) - before_modules | set(expected):
            filename = getattr(sys.modules.get(name), "__file__", None)
            if filename is not None:
                path = Path(filename).resolve()
                if path.is_relative_to(workspace):
                    require(str(path) in inventory, "Renderer imported an unbound local dependency: " + str(path))
        require(os.environ.get("CUDA_VISIBLE_DEVICES") == visibility
                and ("CUDA_VISIBLE_DEVICES" in os.environ) == had_visibility,
                "Pure renderer import mutated GPU visibility")
        yield field, pts
        for reference in inventory.values():
            check_ref(reference, workspace)
    finally:
        sys.path[:] = before_path
        if had_visibility:
            os.environ["CUDA_VISIBLE_DEVICES"] = visibility
        else:
            os.environ.pop("CUDA_VISIBLE_DEVICES", None)


def render_package(assets, source_selections, output_dir, admission_ref, *, config_ref,
                   production_completion_ref, python_executable=None):
    workspace = Path(assets["workspace_root"]).resolve(strict=True)
    require("production" in assets["scopes"] and assets.get("renderer") is not None,
            "Separate explicit formal input/renderer assets required")
    renderer = assets["renderer"]
    require(renderer["spatial_policy"] == "intersect_with_frozen_field", "Only the frozen spatial field may be reused")
    complete = read_json(check_ref(production_completion_ref, workspace))
    require(complete.get("status") == "COMPLETE_PRODUCTION_NOT_PACKAGED"
            and same_ref(complete["config_ref"], config_ref), "Complete exact production/config binding required")
    production_assets_ref = complete.get("production_assets_ref", complete["asset_manifest_ref"])
    require(same_ref(production_assets_ref, assets["_asset_manifest_ref"]), "Renderer assets differ from actual production assets")
    expected_refs = dict(config_ref=config_ref, asset_manifest_ref=complete["asset_manifest_ref"],
        production_assets_ref=production_assets_ref, production_completion_ref=production_completion_ref,
        selection_ref=complete["selection_ref"])
    admission = read_json(check_ref(admission_ref, workspace))
    validate_admission(admission, "package", expected_refs, root=workspace)
    selection_document = read_json(check_ref(complete["selection_ref"], workspace))
    require(selection_document.get("schema") == "AIC_NATIVE_PREFERENCE_SELECTION_V1"
            and selection_document.get("sources") == source_selections,
            "Passed source selections differ from admitted immutable production output")
    for reference in assets["code_refs"]:
        check_ref(reference, workspace)
    sources = {s["id"]: s for s in assets["scopes"]["production"]["sources"]}
    expected = {str(index) for index in range(426)}
    require(set(sources) == expected and len(assets["scopes"]["production"]["sources"]) == 426
            and complete["source_count"] == 426
            and complete["window_count"] == len(assets["scopes"]["production"]["requests"]),
            "All admitted formal sources/windows must have completed")
    counts, clocks = {}, {}
    for sid, source in sources.items():
        clock = read_json(check_ref(source["clock_ref"], workspace))
        _clock(clock)
        require(clock["source_sha256"] == source["source_sha256"], "Formal native clock/source bytes differ")
        clocks[sid], counts[sid] = clock, len(clock["normalized_exact_pts"])
    raw = validate_selections(source_selections, counts)
    package_inputs = read_json(check_ref(renderer["package_inputs_ref"], workspace))
    require(same_ref(package_inputs["source_manifest"], renderer["source_manifest_ref"])
            and same_ref(package_inputs["metadata"], renderer["metadata_ref"])
            and package_inputs["source_field_files"] == renderer["field_files"],
            "Renderer inputs differ from the exact adopted spatial field registration")
    source_manifest = read_json(check_ref(renderer["source_manifest_ref"], workspace))
    records = {row["video_id"]: row for row in source_manifest["records"]}
    require(len(source_manifest["records"]) == 426 and set(records) == expected,
            "Spatial source manifest lost original426 identities")
    require(all(row["source_sha256"] == sources[sid]["source_sha256"] and row["n_frames"] == counts[sid]
                for sid, row in records.items()), "Native model inputs and frozen spatial media identities differ")
    fields = {name: check_ref(reference, workspace) for name, reference in renderer["field_files"].items()}
    require(set(fields) == {"field_frames.jsonl", "field_shots.jsonl", "anchor_requests.jsonl", "anchor_output.jsonl"},
            "Complete original spatial inputs required")
    field_rows = lines(fields["field_frames.jsonl"])
    field_map = {(row["video_id"], row["source_frame"]): row for row in field_rows}
    require(len(field_map) == len(field_rows) and all(sid in expected and type(frame) is int
                and 0 <= frame < counts[sid] for sid, frame in field_map), "Frozen field has foreign/duplicate native frames")
    domain = set(field_map)
    chosen_keys, excluded = raw & domain, raw - domain
    out = Path(output_dir).resolve()
    require(out.is_relative_to(workspace), "Package output escaped registered workspace")
    out.mkdir(parents=True, exist_ok=False)
    field_report = dict(status=("STOP_FIELD_DOMAIN_EXCLUSION_REQUIRES_NEW_REVIEW" if excluded else "PASS_NO_FIELD_DOMAIN_EXCLUSION"),
        policy="intersect_with_frozen_field", raw_native_frames=len(raw),
        eligible_native_frames=len(chosen_keys), excluded_unavailable_field_frames=len(excluded),
        excluded_original_source_ordinals=[dict(sid=sid, source_frame=frame) for sid, frame in sorted(excluded)],
        external_check_has_equivalent_field_evidence=False,
        exclusion_blocks_package=True, source_selection_ref=complete["selection_ref"],
        field_ref=renderer["field_files"]["field_frames.jsonl"], successful_empty_preserved=True)
    write_new(out / "field_eligibility.json", field_report)
    require(not excluded, "STOP_FIELD_DOMAIN_EXCLUSION_REQUIRES_NEW_REVIEW: external temporal utility does not validate removed field frames")
    protected = check_ref(assets["protected_baseline_ref"], workspace)
    require(assets["protected_baseline_ref"]["sha256"] == PROTECTED_SHA256, "Exact protected40.47 ZIP required")
    with zipfile.ZipFile(protected) as archive:
        require(archive.namelist() == ["predictions.jsonl"] and archive.testzip() is None, "Protected baseline ZIP shape/CRC differs")
        baseline = lines(archive.read("predictions.jsonl"))
    require(len(baseline) == 426 and {row["video_id"] for row in baseline} == expected,
            "Protected baseline lost original426 identities")
    old = keymap(baseline)
    require(set(old) <= domain, "Original frozen field no longer contains every protected baseline frame")
    chosen = [field_map[key] for key in sorted(chosen_keys)]
    with bound_renderer(renderer, workspace) as (field, pts):
        require(same_ref(source_manifest["clock_registry"], renderer["clock_registry_ref"]),
                "Frozen spatial source native-clock registry differs")
        registry_path = check_ref(renderer["clock_registry_ref"], workspace)
        registry = read_json(registry_path)
        require([row["clock_arrays"] for row in registry["records"]] == renderer["clock_array_refs"],
                "Frozen field native-clock array inventory differs")
        for reference in renderer["clock_array_refs"]:
            check_ref(reference, workspace)
        original_clocks = pts.load_clocks(source_manifest, registry_path, renderer["clock_registry_ref"]["sha256"])
        require(set(original_clocks) == expected and all(
            _clock(clocks[sid]) == (original_clocks[sid]["pts"], original_clocks[sid]["duration"])
            for sid in expected), "Every actual source PTS/physical endpoint must match the original frozen field clock")
        rows, provenance = field.compose_from_field(pts.legacy_manifest(source_manifest), chosen,
            lines(fields["field_shots.jsonl"]), lines(fields["anchor_requests.jsonl"]), lines(fields["anchor_output.jsonl"]))
    require(assets["actual_pipeline_parameters"] == PIPELINE_PARAMETERS <= 9_000_000_000,
            "Complete inherited dependency inventory must fit9B")
    for row in rows:
        row["model_params_b"] = PIPELINE_PARAMETERS / 1e9
    current = keymap(rows)
    ratios = {row["video_id"]: row["targetRatioWH"] for row in baseline}
    require(len(rows) == 426 and {row["video_id"] for row in rows} == expected and set(current) == chosen_keys
            and all(current[key] == old[key] for key in chosen_keys & set(old))
            and all(row["targetRatioWH"] == ratios[row["video_id"]] for row in rows),
            "Actual selected frames, inherited boxes or original target ratios differ")
    checksum = canonical(rows)
    require(checksum != canonical(baseline), "DUPLICATE_PROTECTED_BASELINE: renaming unchanged predictions is not a candidate")
    dump_lines(out / "predictions.jsonl", rows)
    dump_lines(out / "selected.jsonl", chosen)
    dump_lines(out / "provenance.jsonl", provenance)
    write_new(out / "metadata.json", read_json(check_ref(renderer["metadata_ref"], workspace)))
    pending = out / "candidate_NATIVE_PREFERENCE.PENDING.zip"
    with zipfile.ZipFile(pending, "x", zipfile.ZIP_DEFLATED) as archive:
        archive.write(out / "predictions.jsonl", "predictions.jsonl")
    python = Path(python_executable or assets["runtime_python"]).resolve(strict=True)
    require(python == Path(assets["runtime_python"]).resolve(strict=True), "Use only the explicitly registered isolated Python")
    subprocess.run([str(python), "-B", str(check_ref(renderer["independent_validator_ref"], workspace)),
        "--strict-loader-root", renderer["strict_loader_root"], "--metadata", str(out / "metadata.json"),
        "--selected", str(out / "selected.jsonl"), "--predictions", str(out / "predictions.jsonl"),
        "--provenance", str(out / "provenance.jsonl"), "--zip", str(pending),
        "--report", str(out / "independent_validation.json")], check=True, timeout=1800)
    validation = read_json(out / "independent_validation.json")
    checks = validation["checks"]
    require(len(checks) == 11 and all(value is True for value in checks.values())
            and not validation["strict_loader_issues"], "Actual11 independent strict checks must pass")
    with zipfile.ZipFile(pending) as archive:
        require(archive.namelist() == ["predictions.jsonl"] and archive.testzip() is None
                and hashlib.sha256(archive.read("predictions.jsonl")).hexdigest() == sha(out / "predictions.jsonl"),
                "Single prediction JSONL ZIP CRC/member SHA differs")
    check_ref(assets["protected_baseline_ref"], workspace)
    final = out / "candidate_NATIVE_PREFERENCE.zip"
    pending.rename(final)
    receipt = dict(status="NEW_ENGINEERING_ACCEPTED_OFFICIAL_EFFECT_UNKNOWN", zip_ref=path_ref(final),
        canonical_sha256=checksum, records=426, frames=len(chosen_keys),
        added_frames=len(chosen_keys - set(old)), removed_frames=len(set(old) - chosen_keys),
        empty_source_ids=sorted(expected - {sid for sid, _ in chosen_keys}, key=int),
        field_eligibility_ref=path_ref(out / "field_eligibility.json"),
        independent_validation_ref=path_ref(out / "independent_validation.json"),
        protected_baseline_ref=assets["protected_baseline_ref"], protected_baseline_unchanged=True,
        package_admission_ref=admission_ref, **expected_refs,
        actual_pipeline_parameters=PIPELINE_PARAMETERS, website_submitted=False, official_score="UNKNOWN")
    write_new(out / "package_receipt.json", receipt)
    return receipt
