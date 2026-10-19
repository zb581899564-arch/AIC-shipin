"""Explicit adoption of existing Linux artifacts; no model, download or launcher.

The bootstrap command follows named, hash-bound historical registrations.  It
does not discover a latest experiment and never treats an old PASS as admission
for this new mechanism.  The resulting manifest is PRIVATE and stays on Linux.
"""
import argparse
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
import math
import os
from pathlib import Path
import re

SCHEMA = "AIC_NATIVE_PREFERENCE_ASSETS_V1"
WORKSPACE = Path("/home/inspur/aic_video_work")
PROTECTED_SHA256 = "b37c4a2e6593fc800f54ecce2f860fee5e7d5dc74e17ce280f9ee6722afbccd3"
PROTECTED_BYTES = 384630
PROTECTED_PIPELINE_PARAMETERS = 8782557449
# Shared BASE once, original TIME inherited through B, new DPO TIME, old head.
PIPELINE_PARAMETERS = 8797892873
RUN_RELATIVE = "round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z"


def require(value, message):
    if not value:
        raise ValueError(message)


def _unique(pairs):
    value = {}
    for key, item in pairs:
        require(key not in value, "Duplicate JSON key: " + key)
        value[key] = item
    return value


def _constant(value):
    raise ValueError("Nonfinite JSON constant: " + value)


def _float(value):
    number = float(value)
    require(math.isfinite(number), "Nonfinite JSON number: " + value)
    return number


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"),
                      object_pairs_hook=_unique, parse_constant=_constant, parse_float=_float)


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def path_ref(path):
    path = Path(path).resolve(strict=True)
    require(path.is_file(), "Expected file: " + str(path))
    return dict(path=str(path), bytes=path.stat().st_size, sha256=sha(path))


def check_ref(reference, workspace_root=None, *, verify_hash=True):
    require(isinstance(reference, dict) and isinstance(reference.get("path"), str)
            and isinstance(reference.get("sha256"), str)
            and re.fullmatch(r"[0-9a-f]{64}", reference["sha256"]), "Explicit path/SHA256 reference required")
    raw = Path(reference["path"])
    require(raw.is_absolute(), "Artifact reference must be absolute")
    path = raw.resolve(strict=True)
    if workspace_root is not None:
        require(path.is_relative_to(Path(workspace_root).resolve(strict=True)), "Artifact escaped workspace: " + str(path))
    require(path.is_file(), "Referenced artifact is not a file: " + str(path))
    if "bytes" in reference:
        require(type(reference["bytes"]) is int and reference["bytes"] == path.stat().st_size,
                "Referenced byte count changed: " + str(path))
    require(not verify_hash or sha(path) == reference["sha256"], "Referenced SHA256 changed: " + str(path))
    return path


def same_ref(left, right):
    return (str(Path(left["path"]).resolve()), left["sha256"]) == (str(Path(right["path"]).resolve()), right["sha256"])


def write_new(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n"); stream.flush(); os.fsync(stream.fileno())


def iter_refs(value):
    if isinstance(value, dict):
        if "path" in value and "sha256" in value:
            yield value
        for key, item in value.items():
            if not key.startswith("_"):
                yield from iter_refs(item)
    elif isinstance(value, list):
        for item in value:
            yield from iter_refs(item)


def load_assets(path, workspace_root=None, *, verify_files=False):
    reference = path_ref(path)
    value = read_json(path)
    require(value.get("schema") == SCHEMA, "Unrecognized private asset manifest")
    require(workspace_root is None or Path(workspace_root).resolve() == Path(value["workspace_root"]).resolve(),
            "Asset workspace differs from explicitly requested workspace")
    value["_asset_manifest_ref"] = reference
    if verify_files:
        preflight_assets(value)
    return value


def _clock(clock):
    raw = clock["normalized_exact_pts"]
    require(isinstance(raw, list) and raw and all(type(x) in (str, int) for x in raw), "Exact full native clock required")
    points = [Fraction(x) for x in raw]
    endpoint = clock["physical_end_exact"]
    require(type(endpoint) in (str, int), "Exact measured physical endpoint required")
    end = Fraction(endpoint)
    require(points[0] == 0 and all(a < b for a, b in zip(points, points[1:])) and points[-1] < end,
            "Complete zero-origin monotone native clock required")
    return points, end


def _known_key(keys):
    """One explicit supported NPZ convention; never ignore an unknown mask."""
    candidates = {key for key in keys if "known" in key.lower()}
    require(candidates <= {"known"}, "Unregistered known-mask column requires explicit source adoption")
    return "known" if "known" in candidates else None


def _supervision_adoption(source_adoption, normalized_adoption, protected_ref, workspace):
    """Bind the original source identities to the explicitly adopted full NPZs."""
    original = read_json(check_ref(source_adoption, workspace))
    normalized = read_json(check_ref(normalized_adoption, workspace))
    author, supervision = original["sources"], normalized["sources"]
    require(isinstance(author, list) and isinstance(supervision, list) and author and supervision,
            "Explicit original and normalized supervision sources required")
    require(len({s["sid"] for s in author}) == len(author)
            and len({s["sid"] for s in supervision}) == len(supervision),
            "Duplicate original or normalized supervision source")
    require({(s["sid"], s["group"], s["name"]) for s in author}
            == {(s["sid"], s["group"], s["name"]) for s in supervision}
            and all(s["group"] in {"train", "check"} for s in author),
            "Normalized supervision source identities differ from original adoption")
    require(same_ref(normalized["baseline_ref"], protected_ref),
            "Normalized supervision does not adopt the protected40.47 baseline")
    provenance_ref = normalized["original_human_adoption_ref"]
    provenance = read_json(check_ref(provenance_ref, workspace))
    require(provenance.get("status") == "PASS25_ADOPTED_ORIGINAL_AUTHOR_HUMAN_LABEL_BYTES"
            and isinstance(provenance.get("old_protocol_sha256"), str)
            and re.fullmatch(r"[0-9a-f]{64}", provenance["old_protocol_sha256"]),
            "Explicit original author human-label adoption is required")
    proofs = provenance["proofs"]
    train = {s["sid"]: s for s in author if s["group"] == "train"}
    require(isinstance(proofs, list) and len(proofs) == len(train)
            and {p["sid"] for p in proofs} == set(train),
            "Original human-label adoption does not cover the original training sources")
    for proof in proofs:
        # The historical MAT identity is metadata; the first-read proof path
        # names the exported NPY. Adopt that existing export, never re-decode.
        require(same_ref(proof["label_ref"], train[proof["sid"]]["labels_ref"])
                and same_ref(proof["first_human_read_proof"], proof["label_ref"])
                and isinstance(proof.get("original_mat_sha256"), str)
                and re.fullmatch(r"[0-9a-f]{64}", proof["original_mat_sha256"])
                and proof["first_human_read_proof"]["stage"] == "FIRST_NATIVE_HUMAN_MAT_READ"
                and proof["first_human_read_proof"]["source"] == train[proof["sid"]]["name"],
                "Original human-label proof differs from original source reference")
        check_ref(proof["label_ref"], workspace)
        check_ref(proof["first_human_read_proof"], workspace)
    for key in ("adopted_raw_input_QA", "adopted_raw_output_QA"):
        check_ref(normalized[key], workspace)
    for source in author:
        check_ref(source["media"], workspace)
        check_ref(source["clock_ref"], workspace)
        for key in (("native_ref", "labels_ref") if source["group"] == "train" else ("reference_ref",)):
            check_ref(source[key], workspace)
    for source in supervision:
        for key in ("data_ref", "clock_ref", "language_ref"):
            check_ref(source[key], workspace)
    return original, normalized, provenance_ref


def _scope_from_legacy(group, registration_ref, acceptance_ref, source_adoption, workspace,
                       supervision_adoption=None):
    """Normalize the real prepare_summary/prepare_summary_dev/prepared schemas."""
    reg = read_json(check_ref(registration_ref, workspace))
    gate = read_json(check_ref(acceptance_ref, workspace))
    require(isinstance(gate.get("status"), str) and gate["status"].startswith("PASS_"),
            "Only an existing successful input acceptance may be adopted")
    accepted_reg = gate.get("registration_ref", gate.get("registration"))
    require(accepted_reg is not None and same_ref(accepted_reg, registration_ref),
            "Input acceptance was issued for another registration")
    prepared_ref = gate.get("prepared_ref", gate.get("prepared"))
    require(prepared_ref is not None, "Accepted input gate has no prepared reference")
    prepared = read_json(check_ref(prepared_ref, workspace))
    catalog_ref = prepared.get("source_catalog_ref", prepared.get("source_catalog"))
    catalog = read_json(check_ref(catalog_ref, workspace))["sources"]
    require(isinstance(catalog, list) and catalog and len({s["id"] for s in catalog}) == len(catalog),
            "Unique accepted source catalog required")
    if group != "production":
        require(same_ref(reg["source_registration"], source_adoption), "Train/check source adoption differs")
        registered = read_json(check_ref(source_adoption, workspace))["sources"]
        author = {s["sid"]: s for s in registered if s["group"] == group}
        require(len(author) == sum(s["group"] == group for s in registered), "Duplicate registered external source")
        require(set(author) == {s["id"] for s in catalog}, "All accepted group sources must be adopted")
        adopted = read_json(check_ref(supervision_adoption, workspace))["sources"]
        human = {s["sid"]: s for s in adopted if s["group"] == group}
        require(len(human) == sum(s["group"] == group for s in adopted) and set(human) == set(author),
                "Normalized supervision does not cover accepted source identities")
        if group == "check":
            require(same_ref(reg["matched_fullbaseline_source_adoption"], supervision_adoption),
                    "Accepted development registration uses another normalized supervision adoption")
    else:
        author = {}
    sources = []
    for source in catalog:
        sid = source["id"]
        chunks = source.get("chunks", source.get("context_cases"))
        require(isinstance(chunks, list) and chunks, "Source has no explicit retained patch files")
        normalized = dict(id=sid, name=source.get("name", sid), group=group,
            source_sha256=source["source_sha256"], clock_ref=source["clock"],
            patch_format="CHUNKS" if "chunks" in source else "CONTEXT_CASES",
            patches=chunks, cells=source.get("feature_cells", source.get("cells")))
        if group != "production":
            original, supervised = author[sid], human[sid]
            require(original["media"]["sha256"] == source["source_sha256"]
                    and original["name"] == source["name"] == supervised["name"],
                    "Author/source media identity differs")
            source_clock = read_json(check_ref(source["clock"], workspace))
            label_clock = read_json(check_ref(supervised["clock_ref"], workspace))
            require(_clock(source_clock) == _clock(label_clock)
                    and source_clock["source_sha256"] == label_clock["source_sha256"] == source["source_sha256"],
                    "Normalized supervision and accepted catalog use different native source clocks")
            import numpy as np
            with np.load(check_ref(supervised["data_ref"], workspace), allow_pickle=False) as data:
                known_key = _known_key(data.files)
            normalized.update(supervision_ref=supervised["data_ref"], supervision_clock_ref=supervised["clock_ref"],
                media_ref=original["media"], original_clock_ref=original["clock_ref"],
                original_reference_refs={key: original[key] for key in
                    (("native_ref", "labels_ref") if group == "train" else ("reference_ref",))},
                supervision_contract=dict(labels_key="labels", baseline_key="baseline", known_key=known_key,
                    dense_all_rater_source_summary_membership=True,
                    unselected_is_not_exhaustive_no_highlight_label=True,
                    baseline_kind="HISTORICALLY_EXPOSED_EXTERNAL_40_47_PROXY"))
        if "native" in source:
            normalized["retained_native_ref"] = source["native"]
        sources.append(normalized)
    require(gate["sources"] == len(sources) and gate["windows"] == len(prepared["inputs"]),
            "Accepted source/window denominator differs from prepared artifacts")
    result = dict(sources=sources, requests=prepared["inputs"], source_catalog_ref=catalog_ref,
                  prepared_ref=prepared_ref, input_acceptance_ref=acceptance_ref, input_registration_ref=registration_ref)
    if "training_targets" in prepared:
        result["historical_training_targets_ref"] = prepared["training_targets"]
    return result


def _closed_files(directory, suffix=None, *, allowed_root=None):
    directory = Path(directory).resolve(strict=True)
    files = sorted(p for p in directory.rglob("*") if p.is_file() and (suffix is None or p.suffix == suffix))
    require(files, "Empty required file inventory: " + str(directory))
    boundary = directory if allowed_root is None else Path(allowed_root).resolve(strict=True)
    require(all(p.resolve().is_relative_to(boundary) for p in files), "File inventory symlink escaped its registered boundary")
    if allowed_root is None:
        return [path_ref(p) for p in files]
    # HF snapshots may use local symlinks into the same workspace's blob
    # directory.  Bind each logical filename AND its exact resolved bytes.
    return [dict(**path_ref(p), relative_path=p.relative_to(directory).as_posix()) for p in files]


def bootstrap(*, workspace_root, output, rights_declaration, train_registration,
              train_acceptance, check_registration, check_acceptance, generation_registration,
              protected_registration, protected_zip, production_registration=None,
              production_acceptance=None, package_inputs=None, code_root=None,
              reference_completion=None, reference_output_qa=None):
    """Create a private manifest from explicit existing registrations, never execute them."""
    workspace = Path(workspace_root).resolve(strict=True)
    def inside(path):
        path = Path(path)
        path = path if path.is_absolute() else workspace/path
        require(path.resolve().is_relative_to(workspace), "Bootstrap path escaped workspace")
        return path
    def reference(path):
        return path_ref(inside(path))
    train_ref, check_reg_ref = reference(train_registration), reference(check_registration)
    train_reg = read_json(train_ref["path"])
    adoption = train_reg["source_registration"]
    check_ref(adoption, workspace)
    require(same_ref(read_json(check_reg_ref["path"])["source_registration"], adoption),
            "Train/check must adopt the same explicit original source registration")
    generation_ref = reference(generation_registration)
    generation = read_json(generation_ref["path"])
    normalized_adoption = generation["baseline_human_adoption_ref"]
    require(same_ref(generation["first_dev_input_acceptance_ref"], reference(check_acceptance)),
            "Development acceptance differs from the explicit generation registration")
    cfg_ref = generation["model_config_ref"]
    cfg = read_json(check_ref(cfg_ref, workspace))
    weights = generation["initial_TIME_ref"]
    weight_path = check_ref(weights, workspace)
    require(weight_path == (Path(cfg["b_adapter"])/"adapter_model.safetensors").resolve()
            and weights["sha256"] == cfg["b_adapter_sha256"], "Only the exact original TIME is the starting/reference adapter")
    model_dir = inside(cfg["model_dir"]).resolve(strict=True)
    model_files = _closed_files(model_dir, allowed_root=workspace)
    protected_ref = reference(protected_zip)
    require(protected_ref["sha256"] == PROTECTED_SHA256 and protected_ref["bytes"] == PROTECTED_BYTES,
            "Protected40.47 ZIP identity differs")
    _, _, human_provenance_ref = _supervision_adoption(adoption, normalized_adoption, protected_ref, workspace)
    old_prod_ref = reference(protected_registration)
    old_prod = read_json(old_prod_ref["path"])
    head = old_prod["selected_head"]
    check_ref(head, workspace)
    require(old_prod["actual_resident_parameters"] == PROTECTED_PIPELINE_PARAMETERS, "Protected pipeline parameter inventory differs")
    rights_ref = reference(rights_declaration)
    rights = read_json(rights_ref["path"])
    require(rights.get("schema") == "AIC_NATIVE_PREFERENCE_RIGHTS_V1"
            and rights.get("source_registration_sha256") == adoption["sha256"]
            and rights.get("local_research_training_and_evaluation_allowed") is True
            and rights.get("historical_exposure_acknowledged") is True
            and rights.get("summary_selection_not_exhaustive_highlight_labels") is True
            and isinstance(rights.get("basis_refs"), list) and rights["basis_refs"],
            "Explicit source-use/task/exposure declaration bound to this adoption is required")
    for value in rights["basis_refs"]:
        check_ref(value, workspace)
    scopes = {
        "train": _scope_from_legacy("train", train_ref, reference(train_acceptance), adoption, workspace, normalized_adoption),
        "check": _scope_from_legacy("check", check_reg_ref, reference(check_acceptance), adoption, workspace, normalized_adoption)}
    require((production_registration is None) == (production_acceptance is None), "Both formal registration and first input acceptance are required")
    if production_registration is not None:
        scopes["production"] = _scope_from_legacy("production", reference(production_registration),
            reference(production_acceptance), None, workspace)
    contract_ref = generation["code"]["summary_contract.py"]
    check_ref(contract_ref, workspace)
    renderer = None
    if package_inputs is not None:
        inp_ref = reference(package_inputs)
        inp = read_json(inp_ref["path"])
        source_manifest = read_json(check_ref(inp["source_manifest"], workspace))
        registry_ref = source_manifest["clock_registry"]
        registry = read_json(check_ref(registry_ref, workspace))
        clock_arrays = [row["clock_arrays"] for row in registry["records"]]
        require(len(clock_arrays) == len(source_manifest["records"]), "Original field/native registry denominator differs")
        for clock_ref in clock_arrays:
            check_ref(clock_ref, workspace)
        run = workspace/RUN_RELATIVE
        directories = [run/"b_score_aligned_package_v4", run/"baseline_a_pts_v1", run/"baseline_a_pts_v1/vendor"]
        closure = {str(p.resolve()): path_ref(p) for directory in directories for p in directory.glob("*.py")}
        strict_root = run/"baseline_a_pts_v1/vendor/frozen_strict_loader"
        for value in _closed_files(strict_root, ".py"):
            closure[value["path"]] = value
        renderer = dict(package_inputs_ref=inp_ref, source_manifest_ref=inp["source_manifest"],
            clock_registry_ref=registry_ref, clock_array_refs=clock_arrays,
            metadata_ref=inp["metadata"], field_files=inp["source_field_files"],
            import_paths=list(map(str, directories)), code_refs=list(closure.values()),
            field_contract_ref=path_ref(directories[0]/"field_contract.py"),
            pts_contract_ref=path_ref(directories[1]/"pts_contract.py"),
            independent_validator_ref=path_ref(directories[2]/"independent_validate.py"),
            strict_loader_root=str(strict_root), spatial_policy="intersect_with_frozen_field")
    code_directory = Path(code_root or Path(__file__).resolve().parent).resolve(strict=True)
    require(code_directory.is_relative_to(workspace), "Deployed new code must be inside the registered workspace")
    files = sorted(code_directory.glob("*.py"))
    require(files, "No new implementation source found")
    manifest = dict(schema=SCHEMA, created_utc=datetime.now(timezone.utc).isoformat(),
        workspace_root=str(workspace), protected_baseline_ref=protected_ref, protected_registration_ref=old_prod_ref,
        inherited_baseline_head_ref=head, actual_pipeline_parameters=PIPELINE_PARAMETERS,
        protected_pipeline_parameters=PROTECTED_PIPELINE_PARAMETERS,
        model_spec=dict(model_dir=str(model_dir), revision=cfg["model_revision"], base_sha256=cfg["expected_base_sha256"],
            adapter_weights=weights, adapter_config=path_ref(weight_path.parent/"adapter_config.json")),
        model_config_ref=cfg_ref, model_files=model_files, generation_registration_ref=generation_ref,
        input_code=dict(summary_contract=contract_ref, summary_grammar6=generation["code"]["summary_grammar6.py"],
                        codec=generation["pixel_codec_ref"],
                        dictionary=generation["pixel_dictionary_ref"]),
        rights_declaration_ref=rights_ref, rights_basis_refs=rights["basis_refs"], source_registration_ref=adoption,
        normalized_supervision_registration_ref=normalized_adoption, original_human_label_adoption_ref=human_provenance_ref,
        scopes=scopes, renderer=renderer, code_root=str(code_directory), code_refs=[path_ref(p) for p in files],
        runtime_python=str(workspace/"env/qwen3vl_isolated_20260910/bin/python"),
        gpu_wrapper_ref=path_ref(workspace/RUN_RELATIVE/"resource_unlimited_v1_20261007/gpu_run.py"),
        exposure="All historical external references exposed; this is not a new blind test",
        no_new_model_downloads=True, no_test_labels=True, production_admitted=False,
        historical_targets_adopted_not_relabelled=True)
    require((reference_completion is None) == (reference_output_qa is None),
            "Historical reference completion and first QA must be supplied together")
    if reference_completion is not None:
        manifest["reference_generation_origin"] = dict(
            completion_ref=reference(reference_completion),
            first_output_qa_ref=reference(reference_output_qa))
    # Structural validation checks source and native-clock membership.  A later
    # preflight independently verifies the full inventory's bytes before use.
    preflight_assets(manifest, verify_files=False)
    destination = inside(output)
    write_new(destination, manifest)
    return path_ref(destination)


def preflight_assets(manifest, scope=None, *, verify_files=True):
    require(manifest.get("schema") == SCHEMA, "Private asset schema differs")
    workspace = Path(manifest["workspace_root"]).resolve(strict=True)
    require(manifest["protected_baseline_ref"]["sha256"] == PROTECTED_SHA256
            and manifest["protected_baseline_ref"].get("bytes") == PROTECTED_BYTES,
            "The protected40.47 identity cannot be configured away")
    require(manifest["actual_pipeline_parameters"] == PIPELINE_PARAMETERS <= 9_000_000_000,
            "Complete inherited pipeline must fit9B")
    require(manifest["protected_pipeline_parameters"] == PROTECTED_PIPELINE_PARAMETERS,
            "Protected baseline dependency count differs")
    require({"train", "check"} <= set(manifest["scopes"]) <= {"train", "check", "production"}, "Explicit train/check scopes required")
    require(scope is None or scope in manifest["scopes"], "Requested asset scope is absent")
    checked = set()
    for value in iter_refs(manifest):
        key = (value["path"], value["sha256"])
        if key not in checked:
            check_ref(value, workspace, verify_hash=verify_files)
            checked.add(key)
    model_dir = Path(manifest["model_spec"]["model_dir"]).resolve(strict=True)
    expected_files = {value["relative_path"]: str(check_ref(value, workspace, verify_hash=False)) for value in manifest["model_files"]}
    actual_files = {path.relative_to(model_dir).as_posix(): str(path.resolve()) for path in model_dir.rglob("*") if path.is_file()}
    require(expected_files and len(expected_files) == len(manifest["model_files"])
            and expected_files == actual_files
            and all(Path(path).is_relative_to(workspace) for path in actual_files.values()),
            "Closed local model directory inventory changed")
    code_directory = Path(manifest["code_root"]).resolve(strict=True)
    require(code_directory.is_relative_to(workspace), "New runtime code escaped workspace")
    expected_code = {str(check_ref(value, workspace, verify_hash=False)) for value in manifest["code_refs"]}
    actual_code = {str(path.resolve()) for path in code_directory.glob("*.py")}
    require(expected_code and len(expected_code) == len(manifest["code_refs"]) and expected_code == actual_code,
            "Closed new runtime Python code inventory changed")
    rights = read_json(check_ref(manifest["rights_declaration_ref"], workspace, verify_hash=False))
    require(rights.get("schema") == "AIC_NATIVE_PREFERENCE_RIGHTS_V1"
            and rights.get("source_registration_sha256") == manifest["source_registration_ref"]["sha256"]
            and rights.get("local_research_training_and_evaluation_allowed") is True
            and rights.get("historical_exposure_acknowledged") is True
            and rights.get("summary_selection_not_exhaustive_highlight_labels") is True
            and rights.get("basis_refs") == manifest["rights_basis_refs"] and bool(rights["basis_refs"]),
            "Adopted source-use/task/exposure declaration differs")
    generation = read_json(check_ref(manifest["generation_registration_ref"], workspace, verify_hash=False))
    require(same_ref(generation["baseline_human_adoption_ref"], manifest["normalized_supervision_registration_ref"])
            and same_ref(generation["first_dev_input_acceptance_ref"], manifest["scopes"]["check"]["input_acceptance_ref"]),
            "Generation registration normalized supervision/development acceptance differs")
    _, _, provenance_ref = _supervision_adoption(manifest["source_registration_ref"],
        manifest["normalized_supervision_registration_ref"], manifest["protected_baseline_ref"], workspace)
    require(same_ref(provenance_ref, manifest["original_human_label_adoption_ref"]),
            "Original human-label adoption provenance differs")
    hashes, report = {}, {}
    for name, data in manifest["scopes"].items():
        normalized = _scope_from_legacy(name, data["input_registration_ref"], data["input_acceptance_ref"],
            manifest["source_registration_ref"] if name != "production" else None, workspace,
            manifest["normalized_supervision_registration_ref"] if name != "production" else None)
        require(normalized == data, "Complete accepted source/catalog/window artifacts differ from inline scope")
        sources = {source["id"]: source for source in data["sources"]}
        require(sources and len(sources) == len(data["sources"]), "Duplicate or empty source catalog")
        clocks, windows = {}, {sid: [] for sid in sources}
        for sid, source in sources.items():
            require(source["group"] == name and type(source["cells"]) is int and source["cells"] > 0,
                    "Source group/retained-cell contract differs")
            clock = read_json(check_ref(source["clock_ref"], workspace, verify_hash=False))
            points, end = _clock(clock)
            require(clock["source_sha256"] == source["source_sha256"], "Source bytes/native clock mismatch")
            if name != "production":
                label_clock = read_json(check_ref(source["supervision_clock_ref"], workspace, verify_hash=False))
                require(_clock(label_clock) == (points, end) and label_clock["source_sha256"] == source["source_sha256"],
                        "Summary reference and model input use different native sources")
                require(source["supervision_contract"].get("dense_all_rater_source_summary_membership") is True,
                        "Dense author-summary membership must be declared explicitly")
            clocks[sid] = (points, end)
        ids = set()
        for request_ref in data["requests"]:
            request = read_json(check_ref(request_ref, workspace, verify_hash=False))
            uid, sid = request["uid"], request["sid"]
            require(isinstance(uid, str) and uid and uid not in ids and sid in sources, "Duplicate/foreign accepted request")
            ids.add(uid)
            require(request["source_sha256"] == sources[sid]["source_sha256"]
                    and same_ref(request["source_clock_ref"], sources[sid]["clock_ref"])
                    and request.get("first_new_pixel_text_native_QA") is True, "Accepted input/source identity changed")
            points, physical_end = clocks[sid]
            require(all(type(request["plan"][key]) in (str, int)
                        for key in ("window_start_exact", "window_end_exact")), "Exact window endpoints required")
            start, end = (Fraction(request["plan"][key]) for key in ("window_start_exact", "window_end_exact"))
            require(0 <= start < end <= physical_end, "Window outside native source")
            videos = request["plan"]["videos"]
            require(len(videos) == 2 and [v["role"] for v in videos] == ["Overview", "Excerpt"], "Two-view input contract differs")
            for video in videos:
                ordinals = video["native_ordinals"]
                require(ordinals and all(type(v) is int and 0 <= v < len(points) for v in ordinals)
                        and ordinals == sorted(set(ordinals))
                        and [Fraction(v) for v in video["exact_pts"]] == [points[v] for v in ordinals]
                        and video["owner"] == dict(source_id=sid, source_sha256=sources[sid]["source_sha256"]),
                        "Actual view native ordinals/PTS/source ownership differ")
                require(type(video["origin_exact"]) in (str, int)
                        and Fraction(video["origin_exact"]) == (start if video["role"] == "Excerpt" else 0)
                        and video["padding"] == 0 and video["observations"] == len(ordinals)
                        and 2 <= len(ordinals) <= 64 and len(ordinals) % 2 == 0
                        and video["groups"] == len(ordinals)//2,
                        "Actual two-view origin/group contract differs")
                require(video["role"] != "Excerpt" or all(start <= points[o] < end for o in ordinals),
                        "Excerpt contains observations outside its registered window")
            require(set(request["input_signature"]) == {"input_ids", "attention_mask", "pixel_values_videos", "video_grid_thw"},
                    "Complete four-tensor input signature required")
            check_ref(request["prefix_ref"], workspace, verify_hash=verify_files)
            windows[sid].append((start, end))
        for sid, ranges in windows.items():
            ranges.sort()
            require(ranges and ranges[0][0] == 0 and ranges[-1][1] == clocks[sid][1]
                    and all(a[1] == b[0] for a, b in zip(ranges, ranges[1:])),
                    "Every source needs complete accepted windows; missing windows are not empty")
        hashes[name] = {source["source_sha256"] for source in sources.values()}
        # Formal IDs may legitimately share media bytes at different target
        # ratios.  External source weighting, in contrast, must not duplicate
        # the same source under several author IDs.
        require(name == "production" or len(hashes[name]) == len(sources), "Duplicate external source bytes inside registered group")
        report[name] = dict(sources=len(sources), windows=len(ids))
    require(not hashes["train"] & hashes["check"], "Fit and external check sources overlap by media bytes")
    if "production" in hashes:
        require(not hashes["production"] & (hashes["train"] | hashes["check"]), "Official source bytes overlap external supervision")
    return dict(status="PASS_ASSET_PREFLIGHT_NO_MODEL", scopes=report, bound_files=len(checked),
                file_hashes_verified=verify_files, source_byte_groups_disjoint=True,
                global_source_independence="UNKNOWN", GPU_started=False, production_admitted=False)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace-root", default=str(WORKSPACE))
    parser.add_argument("--output", required=True)
    parser.add_argument("--rights-declaration", required=True)
    parser.add_argument("--train-registration", default="bottleneck_24h_20261019_v1/summary_CPU_registration_05.json")
    parser.add_argument("--train-acceptance", default="bottleneck_24h_20261019_v1/summary_inputs_05/input_acceptance.json")
    parser.add_argument("--check-registration", default="bottleneck_24h_20261019_v1/summary_dev_CPU_registration_09.json")
    parser.add_argument("--check-acceptance", default="bottleneck_24h_20261019_v1/summary_dev_inputs_09/input_acceptance.json")
    parser.add_argument("--generation-registration", default="bottleneck_24h_20261019_v1/summary_generation_registration_10.json")
    parser.add_argument("--protected-registration", default="semantic_context_production_20261016_v1/production_registration.json")
    parser.add_argument("--protected-zip", default="semantic_context_production_20261016_v1/package/candidate_CONTEXT_SEMANTIC_RESIDUAL.zip")
    parser.add_argument("--production-registration")
    parser.add_argument("--production-acceptance")
    parser.add_argument("--package-inputs")
    parser.add_argument("--code-root")
    parser.add_argument("--reference-completion", default="bottleneck_24h_20261019_v1/summary_generation_10/INIT_TIME/completion.json")
    parser.add_argument("--reference-output-qa", default="bottleneck_24h_20261019_v1/summary_generation_10/INIT_TIME/first_independent_output_QA.json")
    args = vars(parser.parse_args())
    print(json.dumps(dict(status="PRIVATE_MANIFEST_CREATED_NO_EXECUTION", manifest_ref=bootstrap(**args))))


if __name__ == "__main__":
    main()
