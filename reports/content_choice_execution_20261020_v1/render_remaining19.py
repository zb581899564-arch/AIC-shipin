"""Independent admitted packaging of content-choice temporal candidates.

Only the original, hash-bound spatial field is used.  Every admitted source is
represented, including successful empty selections.  Failure, field exclusion,
stale review or unchanged protected predictions cannot become a new ZIP.
"""
import hashlib
from pathlib import Path
import subprocess
import zipfile

from ..native_preference_v1.assets import (
    PROTECTED_BYTES, PROTECTED_SHA256, _clock, check_ref, path_ref, read_json,
    require, same_ref, sha, write_new)
from ..native_preference_v1.render import (
    bound_renderer, canonical, dump_lines, keymap, lines, validate_selections)
from .contracts import admission_gate, code_identity, pipeline_parameters
from clock_bridge19 import compare_clock_frames
RECOVERY_REGISTRATION_REF = None


SELECTION_SCHEMA = "AIC_CONTENT_CHOICE_SELECTION_V1"
COMPLETE_STATUS = "COMPLETE_PRODUCTION_NOT_PACKAGED"


def _admitted_selection(manifest, selection, candidate, parameter_count, admission, expected_refs):
    """Small independently testable boundary before spatial work or output creation."""
    workspace = Path(manifest["workspace_root"]).resolve(strict=True)
    require(type(parameter_count) is int and parameter_count == pipeline_parameters(candidate)
            and parameter_count <= 9_000_000_000, "Candidate parameter inventory differs")
    require(isinstance(selection, dict) and set(selection) == {"schema", "sources"}
            and selection["schema"] == SELECTION_SCHEMA and isinstance(selection["sources"], dict),
            "One explicit CONTENT_CHOICE selection document required")
    needed = {"config_ref", "asset_manifest_ref", "production_completion_ref", "selection_ref"}
    require(isinstance(expected_refs, dict) and needed <= set(expected_refs),
            "Package review must bind config, assets, completed production and selections")
    admission_gate(admission, "package", candidate, expected_refs, workspace)
    require(read_json(check_ref(expected_refs["selection_ref"], workspace)) == selection,
            "Passed selections differ from admitted immutable selection bytes")
    actual_assets = expected_refs.get("production_assets_ref", expected_refs["asset_manifest_ref"])
    require(same_ref(actual_assets, manifest["_asset_manifest_ref"]),
            "Production spatial assets differ from the independent admission")
    complete = read_json(check_ref(expected_refs["production_completion_ref"], workspace))
    require(complete.get("status") == COMPLETE_STATUS and complete.get("candidate") == candidate
            and complete.get("actual_pipeline_parameters") == parameter_count
            and same_ref(complete["config_ref"], expected_refs["config_ref"])
            and same_ref(complete["asset_manifest_ref"], expected_refs["asset_manifest_ref"])
            and same_ref(complete.get("production_assets_ref", complete["asset_manifest_ref"]), actual_assets)
            and same_ref(complete["selection_ref"], expected_refs["selection_ref"]),
            "Complete exact candidate production/config/selection binding required")
    require(complete.get("code_identity") == code_identity(), "Production uses a different executable release")
    return workspace, complete


def render_candidate(manifest, selection, output_dir, *, candidate, parameter_count, admission, expected_refs):
    """Create a separately reviewed ZIP; never invoke a model or media decoder.

    ``manifest`` is an explicit native-preference asset manifest, reused only as
    a registered input/renderer inventory.  Its historical DPO parameter field
    does not describe this candidate; ``parameter_count`` must match the new
    code's closed candidate inventory.  ``output_dir`` is the final new directory
    (the caller may pass ``stage / 'rendered'``), not its parent.
    """
    workspace, complete = _admitted_selection(manifest, selection, candidate, parameter_count, admission, expected_refs)
    require("production" in manifest["scopes"] and manifest.get("renderer") is not None,
            "Explicit production input and frozen spatial renderer assets required")
    renderer = manifest["renderer"]
    require(renderer["spatial_policy"] == "intersect_with_frozen_field", "Unknown spatial reuse policy")
    for reference in manifest["code_refs"]:
        check_ref(reference, workspace)
    data = manifest["scopes"]["production"]
    sources = {source["id"]: source for source in data["sources"]}
    expected = {str(index) for index in range(426)}
    require(len(data["sources"]) == 426 and set(sources) == expected
            and all(source["group"] == "production" for source in sources.values())
            and complete.get("source_count") == 426
            and complete.get("window_count") == len(data["requests"]),
            "All426 admitted sources and all registered windows must have completed")
    counts, clocks = {}, {}
    for sid, source in sources.items():
        clock = read_json(check_ref(source["clock_ref"], workspace))
        _clock(clock)
        require(clock["source_sha256"] == source["source_sha256"], "Formal native clock/source bytes differ")
        clocks[sid], counts[sid] = clock, len(clock["normalized_exact_pts"])
    raw = validate_selections(selection["sources"], counts)
    package_inputs = read_json(check_ref(renderer["package_inputs_ref"], workspace))
    require(same_ref(package_inputs["source_manifest"], renderer["source_manifest_ref"])
            and same_ref(package_inputs["metadata"], renderer["metadata_ref"])
            and package_inputs["source_field_files"] == renderer["field_files"],
            "Renderer inputs differ from the exact frozen spatial registration")
    source_manifest = read_json(check_ref(renderer["source_manifest_ref"], workspace))
    records = {row["video_id"]: row for row in source_manifest["records"]}
    require(len(source_manifest["records"]) == 426 and set(records) == expected
            and all(row["source_sha256"] == sources[sid]["source_sha256"] and row["n_frames"] == counts[sid]
                    for sid, row in records.items()), "Model inputs and frozen spatial media identities differ")
    fields = {name: check_ref(reference, workspace) for name, reference in renderer["field_files"].items()}
    require(set(fields) == {"field_frames.jsonl", "field_shots.jsonl", "anchor_requests.jsonl", "anchor_output.jsonl"},
            "Complete original spatial field inputs required")
    field_rows = lines(fields["field_frames.jsonl"])
    field_map = {(row["video_id"], row["source_frame"]): row for row in field_rows}
    require(len(field_map) == len(field_rows) and all(sid in expected and type(frame) is int
                and 0 <= frame < counts[sid] for sid, frame in field_map),
            "Frozen field has foreign or duplicate native frames")
    domain = set(field_map)
    excluded = raw - domain
    out = Path(output_dir).resolve()
    require(out.is_relative_to(workspace) and out != workspace, "New package output escaped workspace")
    out.mkdir(parents=True, exist_ok=False)
    eligibility = dict(status="STOP_FIELD_DOMAIN_EXCLUSION_REQUIRES_NEW_REVIEW" if excluded else "PASS_NO_FIELD_DOMAIN_EXCLUSION",
        candidate=candidate, policy="intersect_with_frozen_field", raw_native_frames=len(raw),
        eligible_native_frames=len(raw & domain), excluded_unavailable_field_frames=len(excluded),
        excluded_original_source_ordinals=[dict(sid=sid, source_frame=frame) for sid, frame in sorted(excluded)],
        external_check_has_equivalent_field_evidence=False, exclusion_blocks_package=True,
        source_selection_ref=expected_refs["selection_ref"], field_ref=renderer["field_files"]["field_frames.jsonl"],
        successful_empty_preserved=True)
    write_new(out / "field_eligibility.json", eligibility)
    require(not excluded, "STOP_FIELD_DOMAIN_EXCLUSION_REQUIRES_NEW_REVIEW")
    protected = check_ref(manifest["protected_baseline_ref"], workspace)
    require(manifest["protected_baseline_ref"]["sha256"] == PROTECTED_SHA256
            and protected.stat().st_size == PROTECTED_BYTES, "Exact protected40.47 ZIP required")
    with zipfile.ZipFile(protected) as archive:
        require(archive.namelist() == ["predictions.jsonl"] and archive.testzip() is None,
                "Protected baseline ZIP shape or CRC differs")
        baseline = lines(archive.read("predictions.jsonl"))
    require(len(baseline) == 426 and {row["video_id"] for row in baseline} == expected,
            "Protected baseline lost original426 identities")
    old = keymap(baseline)
    require(set(old) <= domain, "Frozen field no longer covers the protected baseline")
    chosen = [field_map[key] for key in sorted(raw)]
    with bound_renderer(renderer, workspace) as (field, pts):
        require(same_ref(source_manifest["clock_registry"], renderer["clock_registry_ref"]),
                "Original spatial native-clock registry differs")
        registry_path = check_ref(renderer["clock_registry_ref"], workspace)
        registry = read_json(registry_path)
        require([row["clock_arrays"] for row in registry["records"]] == renderer["clock_array_refs"],
                "Frozen field clock array inventory differs")
        for reference in renderer["clock_array_refs"]:
            check_ref(reference, workspace)
        original_clocks = pts.load_clocks(source_manifest, registry_path, renderer["clock_registry_ref"]["sha256"])
        # Remaining-only recovery19: frame coordinates must match exactly.  The
        # immutable clocks retain distinct terminal policies; no duration is replaced.
        require(set(original_clocks) == expected, "Original clock source set differs")
        bridge_rows = {}
        for sid in expected:
            points, physical_end = _clock(clocks[sid])
            original = original_clocks[sid]
            bridge_rows[sid] = compare_clock_frames(points, physical_end,
                original["pts"], original["duration"], selection["sources"][sid]["selected_ordinals"])
        write_new(out / "exact_frame_clock_compatibility19.json", dict(
            status="PASS_ALL426_EXACT_POINTS_AND_SELECTED_FRAME_DOMAINS",
            sources=bridge_rows, endpoint_policy_differences=sum(not v["terminal_policies_equal"]
                for v in bridge_rows.values()), physical_endpoints_unchanged=True,
            renderer_endpoints_unchanged=True, selected_ordinals_unchanged=True,
            recovery_registration_ref=RECOVERY_REGISTRATION_REF))
        rows, provenance = field.compose_from_field(pts.legacy_manifest(source_manifest), chosen,
            lines(fields["field_shots.jsonl"]), lines(fields["anchor_requests.jsonl"]), lines(fields["anchor_output.jsonl"]))
    for row in rows:
        row["model_params_b"] = parameter_count / 1e9
    current = keymap(rows)
    ratios = {row["video_id"]: row["targetRatioWH"] for row in baseline}
    require(len(rows) == 426 and {row["video_id"] for row in rows} == expected and set(current) == raw
            and all(current[key] == old[key] for key in raw & set(old))
            and all(row["targetRatioWH"] == ratios[row["video_id"]] for row in rows),
            "Selected frames, inherited overlap boxes or target ratios differ")
    checksum = canonical(rows)
    if checksum == canonical(baseline):
        write_new(out / "no_effect.json", dict(status="DUPLICATE_PROTECTED_BASELINE", candidate=candidate,
            canonical_sha256=checksum, selection_ref=expected_refs["selection_ref"], new_zip=False))
        raise ValueError("DUPLICATE_PROTECTED_BASELINE: unchanged predictions are not a new candidate")
    dump_lines(out / "predictions.jsonl", rows)
    dump_lines(out / "selected.jsonl", chosen)
    dump_lines(out / "provenance.jsonl", provenance)
    write_new(out / "metadata.json", read_json(check_ref(renderer["metadata_ref"], workspace)))
    pending = out / ("candidate_CONTENT_CHOICE_" + candidate.upper() + ".PENDING.zip")
    with zipfile.ZipFile(pending, "x", zipfile.ZIP_DEFLATED) as archive:
        archive.write(out / "predictions.jsonl", "predictions.jsonl")
    python = Path(manifest["runtime_python"]).resolve(strict=True)
    require(python.is_file(), "Explicit registered isolated Python is unavailable")
    subprocess.run([str(python), "-B", str(check_ref(renderer["independent_validator_ref"], workspace)),
        "--strict-loader-root", renderer["strict_loader_root"], "--metadata", str(out / "metadata.json"),
        "--selected", str(out / "selected.jsonl"), "--predictions", str(out / "predictions.jsonl"),
        "--provenance", str(out / "provenance.jsonl"), "--zip", str(pending),
        "--report", str(out / "independent_validation.json")], check=True, timeout=1800,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    validation = read_json(out / "independent_validation.json")
    require(len(validation["checks"]) == 11 and all(value is True for value in validation["checks"].values())
            and not validation["strict_loader_issues"], "All11 real independent strict checks must pass")
    with zipfile.ZipFile(pending) as archive:
        require(archive.namelist() == ["predictions.jsonl"] and archive.testzip() is None
                and hashlib.sha256(archive.read("predictions.jsonl")).hexdigest() == sha(out / "predictions.jsonl"),
                "Single-member ZIP CRC or prediction byte roundtrip failed")
    check_ref(manifest["protected_baseline_ref"], workspace)
    # Recheck the new code as well as the renderer's full dependency inventory.
    require(complete["code_identity"] == code_identity(), "Code changed during packaging")
    final = out / ("candidate_CONTENT_CHOICE_" + candidate.upper() + ".zip")
    pending.rename(final)
    receipt = dict(status="NEW_ENGINEERING_ACCEPTED_OFFICIAL_EFFECT_UNKNOWN", candidate=candidate,
        zip_ref=path_ref(final), canonical_sha256=checksum, records=426, frames=len(raw),
        added_frames=len(raw - set(old)), removed_frames=len(set(old) - raw),
        empty_source_ids=sorted(expected - {sid for sid, _ in raw}, key=int),
        field_eligibility_ref=path_ref(out / "field_eligibility.json"),
        independent_validation_ref=path_ref(out / "independent_validation.json"),
        protected_baseline_ref=manifest["protected_baseline_ref"], protected_baseline_unchanged=True,
        actual_pipeline_parameters=parameter_count, official_score="UNKNOWN", website_submitted=False,
        code_identity=complete["code_identity"], **expected_refs)
    receipt.update(execution_recovery="REMAINING_CPU_CLOCK_BRIDGE19",
        exact_frame_clock_compatibility_ref=path_ref(out / "exact_frame_clock_compatibility19.json"),
        recovery_registration_ref=RECOVERY_REGISTRATION_REF,
        original_physical_endpoint_equality_gate="FAILED_AND_PRESERVED_NOT_RELABELED")
    write_new(out / "package_receipt.json", receipt)
    return receipt
