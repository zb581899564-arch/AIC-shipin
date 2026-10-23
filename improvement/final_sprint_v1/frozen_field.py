"""CPU-only reuse of the original, continuously rendered spatial action domain.

The saved field determines the domain before temporal selection. Missing native
points remain unsupported; this module neither decodes media nor supplies boxes.
Run the CLI in a separate process with CUDA_VISIBLE_DEVICES='' before inference.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
import json
import os
from pathlib import Path
import subprocess
import sys
import zipfile

from ..native_preference_v1.render import bound_renderer, lines
from .contracts import (PROTECTED, checked, iter_refs, ref, require, save_new, stable_key,
                        strict_load, validate_sources)
from .spatial import validate_box

FIELD_NAMES = {"field_frames.jsonl", "field_shots.jsonl", "anchor_requests.jsonl", "anchor_output.jsonl"}
SCHEMA = "AIC_FROZEN_SPATIAL_FIELD_CACHE_V1"
STRICT_CHECKS = {"strict_loader_ok", "video_record_set_exact", "selected_key_set_exact", "ratio_fields_exact",
    "frames_sorted", "provenance_key_set_exact", "provenance_boxes_match_predictions", "provenance_all_legal",
    "provenance_sources_allowed", "archive_single_file", "archive_roundtrip_exact"}


def _reference(value):
    """Add only measured size to an old path/SHA pair, retaining its old SHA."""
    require(isinstance(value, dict) and {"path", "sha256"} <= value.keys(),
            "Original frozen-field path/SHA reference required")
    path = Path(value["path"]).resolve(strict=True)
    identity = dict(value, path=str(path), bytes=value.get("bytes", path.stat().st_size))
    checked(identity)
    return identity


def _binding(assets):
    return stable_key(assets["sources"], assets["protected_baselines"],
                      assets["adopted_inputs"]["package_inputs"],
                      assets["baseline_registration_provenance"]["registration_refs"]["config"])


def build_spec(assets, *, expected_count=426):
    """Bind the exact registered original renderer closure and four field files."""
    workspace = Path(assets["workspace_root"]).resolve(strict=True)
    package_ref = _reference(assets["adopted_inputs"]["package_inputs"])
    config_ref = _reference(assets["baseline_registration_provenance"]["registration_refs"]["config"])
    package = strict_load(checked(package_ref))
    original = Path(config_ref["path"]).parent
    require(original.name == "b_score_aligned_package_v4", "Exact original b_score_aligned_package_v4 required")
    directories = [original, original.parent / "baseline_a_pts_v1", original.parent / "baseline_a_pts_v1/vendor"]
    strict_root = directories[-1] / "frozen_strict_loader"
    require(strict_root.is_dir() and all(directory.is_dir() for directory in directories),
            "Original renderer/PTS/vendor/strict-loader closure unavailable")
    paths = {p.resolve() for directory in directories for p in directory.glob("*.py")}
    paths.update(p.resolve() for p in strict_root.rglob("*.py"))
    require(paths, "Empty original renderer closure")
    inputs = {key: _reference(package[key]) for key in ("source_manifest", "metadata", "source_clocks")}
    manifest = strict_load(checked(inputs["source_manifest"]))
    registry_ref = _reference(manifest["clock_registry"])
    registry = strict_load(checked(registry_ref))
    arrays = [_reference(row["clock_arrays"]) for row in registry["records"]]
    fields = package["source_field_files"]
    require(set(fields) == FIELD_NAMES, "Exactly the four original field files are required")
    renderer = dict(package_inputs_ref=package_ref, source_manifest_ref=inputs["source_manifest"],
        metadata_ref=inputs["metadata"], clock_registry_ref=registry_ref, clock_array_refs=arrays,
        field_files={name: _reference(fields[name]) for name in sorted(FIELD_NAMES)},
        import_paths=list(map(str, directories)), code_refs=[ref(p) for p in sorted(paths)],
        field_contract_ref=ref(original / "field_contract.py"),
        pts_contract_ref=ref(directories[1] / "pts_contract.py"),
        independent_validator_ref=ref(directories[2] / "independent_validate.py"),
        strict_loader_root=str(strict_root), spatial_policy="predeclared_frozen_field_action_domain")
    baselines = {name: _reference(identity) for name, identity in assets["protected_baselines"].items()}
    require(set(baselines) == {"40.48", "40.47"}, "Both protected baselines required")
    if expected_count == 426:
        require(all(all(baselines[name][key] == value for key, value in expected.items())
                    for name, expected in PROTECTED.items()), "Protected baseline identity differs")
    require(len(manifest["records"]) == len(arrays) == len(assets["sources"]) == expected_count,
            "Original field/current native source denominator differs")
    spec = dict(schema="AIC_FROZEN_SPATIAL_FIELD_SPEC_V1", asset_binding=_binding(assets),
                expected_count=expected_count, workspace_root=str(workspace), config_ref=config_ref,
                inputs=inputs, renderer=renderer, protected_baselines=baselines)
    for identity in iter_refs(spec):
        checked(identity, workspace)
    return spec


def _source_identity(assets, spec):
    sources = {source["video_id"]: source for source in assets["sources"]}
    originals = strict_load(checked(spec["inputs"]["source_manifest"]))
    records = {row["video_id"]: row for row in originals["records"]}
    metadata_rows = strict_load(checked(spec["inputs"]["metadata"]))["records"]
    metadata = {row["video_id"]: row for row in metadata_rows}
    require(len(sources) == len(records) == len(metadata) == len(metadata_rows) == spec["expected_count"]
            and set(sources) == set(records) == set(metadata), "Frozen/current source identities differ")
    if spec["expected_count"] == 426:
        require(set(sources) == {str(i) for i in range(426)}, "Original426 IDs required")
    for sid, source in sources.items():
        for original in (records[sid], metadata[sid]):
            require(original["source_sha256"] == source["media"]["sha256"]
                    and Path(original["source_path"]).resolve() == Path(source["media"]["path"]).resolve()
                    and original["width"] == source["width"] and original["height"] == source["height"],
                    "Frozen/current media mapping differs: " + sid)
        require(records[sid]["targetRatioWH"] == source["targetRatioWH"], "Original target ratio differs: " + sid)
    clocks = validate_sources(assets["sources"], expected_count=spec["expected_count"], verify_media=False)
    return sources, originals, clocks


def _domain(rows, sources):
    domain = {}
    for row in rows:
        sid, frame = row["video_id"], row["source_frame"]
        require(sid in sources and type(frame) is int and 0 <= frame < sources[sid]["n_frames"],
                "Frozen field contains a foreign/out-of-native-domain frame")
        require((sid, frame) not in domain, "Duplicate original frozen-field frame")
        domain[sid, frame] = row
    return domain


def _render(assets, spec):
    sources, manifest, clocks = _source_identity(assets, spec)
    renderer = spec["renderer"]
    files = {name: lines(checked(identity)) for name, identity in renderer["field_files"].items()}
    domain = _domain(files["field_frames.jsonl"], sources)
    require(set(domain) == {(row["video_id"], row["source_frame"]) for row in files["field_shots.jsonl"]},
            "Original field frame/shot domains differ")
    with bound_renderer(renderer, Path(spec["workspace_root"])) as (field, pts):
        old_clocks = pts.load_clocks(manifest, Path(renderer["clock_registry_ref"]["path"]),
                                     renderer["clock_registry_ref"]["sha256"])
        require(set(old_clocks) == set(sources), "Original clock source set differs")
        for sid, frame in domain:
            require(frame < len(old_clocks[sid]["pts"]) and
                    Fraction(old_clocks[sid]["pts"][frame]) == clocks[sid][0][frame],
                    "Frozen field/native PTS mismatch: " + sid + ":" + str(frame))
        rows, provenance = field.compose_from_field(pts.legacy_manifest(manifest),
            files["field_frames.jsonl"], files["field_shots.jsonl"],
            files["anchor_requests.jsonl"], files["anchor_output.jsonl"])
    cache, checks = _validate_rendered(rows, domain, sources, clocks, old_clocks, manifest)
    _validate_provenance(provenance, domain, cache)
    overlap = _baseline_overlap(spec, cache, sources)
    unsupported = [{"video_id": sid, "frame": frame} for sid in sorted(sources)
                   for frame in range(sources[sid]["n_frames"]) if str(frame) not in cache[sid]["boxes"]]
    metadata = dict(schema="AIC_FROZEN_SPATIAL_FIELD_METADATA_V1", sources=checks,
        field_frames=len(domain), native_frames=sum(source["n_frames"] for source in sources.values()),
        domain_status="PARTIAL_NATIVE_ACTION_DOMAIN" if unsupported else "FULL_NATIVE_ACTION_DOMAIN",
        unsupported_native_points=unsupported, unsupported_policy="UNKNOWN_NO_BOX_NO_ACTION",
        baseline_overlap=overlap, spatial_code_refs=renderer["code_refs"],
        spatial_input_refs=dict(spec["inputs"], **renderer["field_files"]),
        clock_registry_ref=renderer["clock_registry_ref"], clock_array_refs=renderer["clock_array_refs"],
        renderer_provenance_rows=len(provenance), new_model_calls=0, new_media_decodes=0)
    return dict(schema=SCHEMA, format_revision=2, spec_sha256=stable_key(spec), sources=cache,
                field_frames_ref=renderer["field_files"]["field_frames.jsonl"]), metadata, provenance


def _validate_provenance(provenance, domain, cache):
    seen = set()
    for row in provenance:
        sid, frame = row["video_id"], row["source_frame"]
        require(type(frame) is int and (sid, frame) in domain and (sid, frame) not in seen
                and row["box_xyw"] == cache[sid]["boxes"][str(frame)] and row.get("legal") is True
                and row.get("spatial_source") in {"QWEN_ANCHOR_SAME_FRAME", "SHOT_LINEAR_INTERPOLATION"},
                "Original renderer provenance/domain/box differs")
        seen.add((sid, frame))
    require(seen == set(domain), "Original renderer provenance does not cover the field")


def _validate_rendered(rows, domain, sources, clocks, old_clocks, manifest):
    require(len(rows) == len(sources) and {row["video_id"] for row in rows} == set(sources),
            "Original renderer lost or duplicated a source")
    original_records = {row["video_id"]: row for row in manifest["records"]}
    cache, checks, seen = {}, {}, set()
    for row in rows:
        sid = row["video_id"]
        source = sources[sid]
        require(row["targetRatioWH"] == source["targetRatioWH"], "Rendered target ratio differs")
        boxes, pts_values = {}, {}
        for item in row["predictions"]:
            frame = item["frame"]
            require(type(frame) is int and (sid, frame) in domain and (sid, frame) not in seen,
                    "Original renderer changed frozen field domain")
            validate_box(item["bboxes"], source["width"], source["height"], source["targetRatioWH"])
            seen.add((sid, frame))
            boxes[str(frame)] = item["bboxes"]
            pts_values[str(frame)] = str(clocks[sid][0][frame])
        support = sorted(map(int, boxes))
        require(support, "Frozen field has no action support for source: " + sid)
        cache[sid] = dict(boxes=boxes, native_pts=pts_values, support=support)
        checks[sid] = dict(source_sha256=source["media"]["sha256"], native_frames=source["n_frames"],
            original_manifest_frames=original_records[sid]["n_frames"], original_clock_frames=len(old_clocks[sid]["pts"]),
            supported_frames=len(support), all_supported_native_pts_equal=True,
            supported_pts_sha256=stable_key([(frame, pts_values[str(frame)]) for frame in support]),
            native_physical_end=str(clocks[sid][1]), original_clock_end=str(old_clocks[sid]["duration"]))
    require(seen == set(domain), "Original renderer omitted frozen field points")
    return cache, checks


def _baseline_overlap(spec, cache, sources):
    overlap = {}
    for name, identity in spec["protected_baselines"].items():
        with zipfile.ZipFile(checked(identity)) as archive:
            require(archive.namelist() == ["predictions.jsonl"] and archive.testzip() is None,
                    "Protected ZIP member/CRC differs")
            rows = lines(archive.read("predictions.jsonl"))
        require(len(rows) == len(sources) and {row["video_id"] for row in rows} == set(sources),
                "Protected baseline source denominator differs")
        count, seen = 0, set()
        for row in rows:
            sid = row["video_id"]
            require(row["targetRatioWH"] == sources[sid]["targetRatioWH"], "Protected target ratio differs")
            for prediction in row["predictions"]:
                frame = prediction["frame"]
                require(type(frame) is int and (sid, frame) not in seen and
                        str(frame) in cache[sid]["boxes"] and
                        prediction["bboxes"] == cache[sid]["boxes"][str(frame)],
                        "Protected baseline frame/box differs from original field: " + name)
                seen.add((sid, frame))
                count += 1
        overlap[name] = dict(frames=count, all_frames_supported=True, all_boxes_exact=True)
    return overlap


def render_cache(assets, output_dir, *, expected_count=426):
    """Render saved field once; repeated calls read immutable cached artifacts."""
    require(os.environ.get("CUDA_VISIBLE_DEVICES") == "", "Render frozen field in an isolated CUDA_VISIBLE_DEVICES='' CPU process")
    output = Path(output_dir).resolve()
    require(output.is_relative_to(Path(assets["workspace_root"]).resolve(strict=True)), "Frozen cache escaped workspace")
    receipt_path = output / "receipt.json"
    if receipt_path.exists():
        receipt = strict_load(receipt_path)
        load_cache(receipt, assets)
        return receipt
    spec = build_spec(assets, expected_count=expected_count)
    cache, metadata, provenance = _render(assets, spec)
    output.mkdir(parents=True, exist_ok=True)
    cache["provenance_ref"] = _save_lines(output / "rendered_provenance.jsonl", provenance)
    refs = {name + "_ref": save_new(output / (name + ".json"), value)
            for name, value in (("spec", spec), ("cache", cache), ("metadata", metadata))}
    receipt = dict(schema="AIC_FROZEN_SPATIAL_FIELD_RECEIPT_V1", status="CPU_FIELD_RENDERED_DOMAIN_LOCKED",
                   asset_binding=spec["asset_binding"], **refs)
    save_new(receipt_path, receipt)
    return receipt


def load_cache(receipt, assets=None):
    """Return source -> integer native frame -> exact old box, without imports."""
    require(receipt.get("schema") == "AIC_FROZEN_SPATIAL_FIELD_RECEIPT_V1", "Wrong frozen-field receipt")
    spec = strict_load(checked(receipt["spec_ref"]))
    cache = strict_load(checked(receipt["cache_ref"]))
    metadata = strict_load(checked(receipt["metadata_ref"]))
    require(cache.get("schema") == SCHEMA and cache["spec_sha256"] == stable_key(spec)
            and receipt["asset_binding"] == spec["asset_binding"], "Frozen cache/spec binding differs")
    if assets is not None:
        require(_binding(assets) == spec["asset_binding"], "Frozen cache belongs to different current assets")
    boxes, support = {}, {}
    for sid, source in cache["sources"].items():
        points = source["support"]
        require(all(type(frame) is int and frame >= 0 for frame in points) and points == sorted(set(points))
                and set(source["boxes"]) == set(source["native_pts"]) == {str(frame) for frame in points},
                "Frozen cache support/PTS/box keys differ")
        boxes[sid] = {int(frame): box for frame, box in source["boxes"].items()}
        support[sid] = points
    require(sum(map(len, support.values())) == metadata["field_frames"], "Frozen cache domain count differs")
    witness_refs = {}
    if cache.get("format_revision", 1) >= 2:
        require(cache["field_frames_ref"] == spec["renderer"]["field_files"]["field_frames.jsonl"],
                "Cached original field-frame reference differs")
        witness_refs = {key: cache[key] for key in ("field_frames_ref", "provenance_ref")}
        for identity in witness_refs.values():
            checked(identity)
    return dict(boxes=boxes, support=support, source_checks=metadata["sources"], metadata=metadata,
                native_pts={sid: source["native_pts"] for sid, source in cache["sources"].items()},
                **witness_refs,
                **{key: receipt[key] for key in ("spec_ref", "cache_ref", "metadata_ref")})


def _save_lines(path, rows):
    with Path(path).open("x", encoding="utf-8", newline="\n") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False, separators=(",", ":"), allow_nan=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    return ref(path)


def _locked_cache(cache):
    """Re-read immutable refs rather than trust mutable caller dictionaries."""
    if cache.get("schema") == "AIC_FROZEN_SPATIAL_FIELD_RECEIPT_V1":
        return load_cache(cache)
    spec = strict_load(checked(cache["spec_ref"]))
    receipt = dict(schema="AIC_FROZEN_SPATIAL_FIELD_RECEIPT_V1", asset_binding=spec["asset_binding"],
                   **{key: cache[key] for key in ("spec_ref", "cache_ref", "metadata_ref")})
    return load_cache(receipt)


def export_selection(cache, selected_by_source, output):
    """Project saved field rows/provenance only; never re-run composition."""
    cached = _locked_cache(cache)
    require({"field_frames_ref", "provenance_ref"} <= cached.keys(),
            "Old cache has no saved provenance witnesses; explicit new CPU cache required")
    require(isinstance(selected_by_source, dict) and set(selected_by_source) == set(cached["support"]),
            "Selection must explicitly cover every cached source, including empty")
    chosen = set()
    for sid, frames in selected_by_source.items():
        require(isinstance(frames, list) and all(type(frame) is int for frame in frames)
                and frames == sorted(set(frames)) and set(frames) <= set(cached["support"][sid]),
                "Selected frame lies outside frozen native action domain or is duplicated: " + sid)
        chosen.update((sid, frame) for frame in frames)
    directory = Path(output).resolve()
    spec = strict_load(checked(cached["spec_ref"]))
    require(directory.is_relative_to(Path(spec["workspace_root"])), "Selection export escaped workspace")
    document = directory / "selection_export.json"
    binding = dict(cache_ref=cached["cache_ref"], spec_ref=cached["spec_ref"], metadata_ref=cached["metadata_ref"],
                   selection_sha256=stable_key(selected_by_source))
    if document.exists():
        exported = strict_load(document)
        require(all(exported.get(key) == value for key, value in binding.items()), "Selection export binding differs")
        checked(exported["selected_ref"])
        checked(exported["provenance_ref"])
        return exported
    selected = _project_rows(cached["field_frames_ref"], chosen)
    provenance = _project_rows(cached["provenance_ref"], chosen)
    require(all(row["box_xyw"] == cached["boxes"][row["video_id"]][row["source_frame"]]
                for row in provenance), "Cached selected provenance differs from rendered boxes")
    directory.mkdir(parents=True, exist_ok=True)
    exported = dict(schema="AIC_FROZEN_FIELD_SELECTION_EXPORT_V1", selected_frames=len(chosen), **binding,
        selected_ref=_save_lines(directory / "selected.jsonl", selected),
        provenance_ref=_save_lines(directory / "provenance.jsonl", provenance))
    save_new(document, exported)
    return exported


def _project_rows(identity, chosen):
    selected, seen = [], set()
    for row in lines(checked(identity)):
        key = (row["video_id"], row["source_frame"])
        if key in chosen:
            require(key not in seen, "Duplicate selected cached witness")
            selected.append(row)
            seen.add(key)
    require(seen == chosen, "Missing selected cached witness")
    return sorted(selected, key=lambda row: (row["video_id"], row["source_frame"]))


def verify_package(cache, package_or_export, predictions_or_output, zip_ref=None, report_path=None, *,
                   python_executable=None, timeout_seconds=1800):
    """Validate a package receipt, or an already exported exact selection.

    The primary call is ``verify_package(cache, package_receipt, output_dir)``.
    An explicit export may instead supply prediction/ZIP refs and report path.
    Both forms only project the same saved field and provenance.
    """
    if zip_ref is None and report_path is None:
        package = package_or_export
        predictions_ref = package["member_ref"]
        zip_ref = package["zip_ref"]
        cached = _locked_cache(cache)
        rows = lines(checked(predictions_ref))
        require(len(rows) == len(cached["support"]) and
                {row["video_id"] for row in rows} == set(cached["support"]),
                "Independent package source denominator differs")
        selected = {row["video_id"]: [item["frame"] for item in row["predictions"]] for row in rows}
        directory = Path(predictions_or_output).resolve()
        exported = export_selection(cached, selected, directory)
        report_path = directory / "validation.json"
    else:
        require(zip_ref is not None and report_path is not None, "Explicit validator ZIP and report path required")
        cached, exported, predictions_ref = cache, package_or_export, predictions_or_output
    return _verify_projected_package(cached, exported, predictions_ref, zip_ref, report_path,
                                    python_executable=python_executable, timeout_seconds=timeout_seconds)


def _verify_projected_package(cache, selection_export, predictions_ref, zip_ref, report_path, *,
                              python_executable=None, timeout_seconds=1800):
    """Run the exact original independent validator and require all 11 checks."""
    cached = _locked_cache(cache)
    require(selection_export.get("schema") == "AIC_FROZEN_FIELD_SELECTION_EXPORT_V1" and
            all(selection_export[key] == cached[key] for key in ("spec_ref", "cache_ref", "metadata_ref")),
            "Independent validation selection/cache binding differs")
    spec = strict_load(checked(cached["spec_ref"]))
    renderer = spec["renderer"]
    report_path = Path(report_path).resolve()
    require(report_path.is_relative_to(Path(spec["workspace_root"])), "Independent report escaped workspace")
    identities = dict(selected=selection_export["selected_ref"], provenance=selection_export["provenance_ref"],
                      predictions=predictions_ref, zip=zip_ref, metadata=renderer["metadata_ref"])
    _validate_export_projection(cached, selection_export)
    for identity in [*renderer["code_refs"], *identities.values()]:
        checked(identity)
    binding = dict(schema="AIC_FROZEN_FIELD_STRICT_ACCEPTANCE_V1", status="PASS_INDEPENDENT_STRICT_VALIDATION",
        cache_ref=cached["cache_ref"], selection_export=selection_export, **identities,
        validator_ref=renderer["independent_validator_ref"], code_refs=renderer["code_refs"],
        strict_loader_root=renderer["strict_loader_root"])
    acceptance_path = report_path.with_name(report_path.stem + ".acceptance.json")
    if acceptance_path.exists() or report_path.exists():
        return _accept_strict_report(report_path, acceptance_path, binding, cached, renderer)
    command = [str(Path(python_executable or sys.executable).resolve(strict=True)), "-B",
               str(checked(renderer["independent_validator_ref"])), "--strict-loader-root", renderer["strict_loader_root"]]
    for name, identity in identities.items():
        command.extend(["--" + name, str(checked(identity))])
    command.extend(["--report", str(report_path)])
    result = subprocess.run(command, env=dict(os.environ, CUDA_VISIBLE_DEVICES=""),
                            capture_output=True, text=True, timeout=timeout_seconds, check=False)
    require(report_path.is_file(), "Original independent validator produced no report: " + result.stderr[-2000:])
    require(result.returncode == 0, "Original independent 11strict validation failed; report preserved: " + str(report_path))
    for identity in [*renderer["code_refs"], *identities.values()]:
        checked(identity)
    return _accept_strict_report(report_path, acceptance_path, binding, cached, renderer)


def _accept_strict_report(report_path, acceptance_path, binding, cached, renderer):
    """Adopt an existing success only after complete immutable input checks."""
    if acceptance_path.exists():
        accepted = strict_load(acceptance_path)
        require(all(accepted.get(key) == value for key, value in binding.items()),
                "Existing independent acceptance input binding differs")
        require(Path(accepted["report_ref"]["path"]).resolve() == report_path,
                "Existing independent acceptance report path differs")
        checked(accepted["report_ref"])
    _check_strict_report(report_path, binding, cached, renderer)
    accepted = dict(binding, report_ref=ref(report_path))
    if not acceptance_path.exists():
        save_new(acceptance_path, accepted)
    return dict(accepted, acceptance_ref=ref(acceptance_path))


def _check_strict_report(report_path, binding, cached, renderer):
    report = strict_load(report_path)
    require(report.get("status") == "PASS_INDEPENDENT_STRICT_VALIDATION"
            and set(report.get("checks", {})) == STRICT_CHECKS
            and all(value is True for value in report["checks"].values()) and report.get("strict_loader_issues") == [],
            "Original independent 11strict validation failed; report preserved: " + str(report_path))
    for key in ("predictions", "provenance", "zip"):
        require(report.get(key + "_sha256") == binding[key]["sha256"], "Independent report input SHA differs: " + key)
    scoring_path = Path(renderer["strict_loader_root"]) / "aic6/scoring.py"
    scoring = [identity for identity in renderer["code_refs"] if Path(identity["path"]).resolve() == scoring_path.resolve()]
    require(len(scoring) == 1 and report.get("strict_loader_sha256") == scoring[0]["sha256"],
            "Independent report strict-loader SHA differs")
    count = binding["selection_export"]["selected_frames"]
    require(report.get("video_records") == len(cached["support"]) and
            report.get("expected_frames") == report.get("prediction_frames") == count and
            all(report.get(key) == 0 for key in ("duplicate_frames", "missing", "extra")),
            "Independent report source/frame counts differ")
    return report


def _validate_export_projection(cached, exported):
    selected = lines(checked(exported["selected_ref"]))
    chosen = {(row["video_id"], row["source_frame"]) for row in selected}
    require(len(chosen) == len(selected) == exported["selected_frames"], "Exported selected witness count differs")
    for row in selected:
        sid, frame = row["video_id"], row["source_frame"]
        require(sid in cached["support"] and type(frame) is int and frame in cached["support"][sid],
                "Exported selection is outside frozen native action domain")
    require(selected == _project_rows(cached["field_frames_ref"], chosen)
            and lines(checked(exported["provenance_ref"])) == _project_rows(cached["provenance_ref"], chosen),
            "Exported selected/provenance witnesses differ from saved renderer output")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assets", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    receipt = render_cache(strict_load(args.assets), args.output)
    print(json.dumps(receipt, ensure_ascii=False))


if __name__ == "__main__":
    main()
