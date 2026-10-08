"""Prepare untouched non-test 128/32 natural windows and a 16/8 pilot on CPU.

The fixed R7 manifests supply source identities only. All old 160 source groups
and all registered context-diagnostic groups are excluded before source ranking.
No label, teacher answer, pixel or GPU inference is used by this preparation.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUN = HERE.parent
SEED = "aic-complete-window-supervision-20261008-v8-untouched"
COUNTS = {"train": 128, "dev": 32}
PILOT_COUNTS = {"train": 16, "dev": 8}
PILOT_RULE = "SHA256_WINDOW_ID_ASCENDING_16TRAIN_8DEV"
SELECTOR_PATH = RUN / "next_round_v1/supervision_v2/select_windows.py"
SELECTOR_SHA256 = "42660202fca9fb6a9d7709461c390954ade9246d7d14e0aaf622d0d99a7ff419"
OLD_RECEIPT_SHA256 = "ecf72676c2d46cbe7dea3b8bd3aab1bbedec765e431ce53731b22dd394705ead"
FFPROBE = "/home/inspur/anaconda3/envs/Andy/bin/ffprobe"


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 2**20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def rows(path):
    return [json.loads(line) for line in Path(path).read_text(encoding="utf-8").splitlines() if line.strip()]


def save_json(path, value):
    with Path(path).open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def load_selector():
    require(sha256(SELECTOR_PATH) == SELECTOR_SHA256, "inherited v2 selector byte identity differs")
    spec = importlib.util.spec_from_file_location("aic_v8_pinned_native_selector", SELECTOR_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # A separate import instance gives v8 its preregistered ranking/identity seed.
    # The inherited selection and sampling functions themselves stay unchanged.
    module.SEED = SEED
    return module


SELECTOR = load_selector()


def context_manifests():
    expected = {RUN / f"teacher_context_diagnostic_v{i}/manifest.json" for i in (1, 2, 3)}
    found = set(RUN.glob("teacher_context_diagnostic_v*/manifest.json"))
    require(expected <= found, "all three prior context registrations must be present")
    return sorted(found, key=lambda path: str(path))


def load_exclusions(old_dir, contexts, *, selector=SELECTOR, expected_receipt_sha=OLD_RECEIPT_SHA256):
    """Read unlabelled identities; fail if any registered context cannot resolve."""
    old_dir = Path(old_dir)
    receipt_path = old_dir / "selection_receipt.json"
    require(sha256(receipt_path) == expected_receipt_sha, "original selection receipt byte identity differs")
    receipt = read_json(receipt_path)
    require(receipt.get("status") == "PASS_CPU_SELECTION_UNLABELLED"
            and receipt.get("confirm_opened") is False and receipt.get("contest_assets_opened") is False,
            "original successful isolated unlabelled selection required")
    require(receipt.get("counts") == COUNTS, "original exclusion denominator must remain all 160 windows")
    original = {}
    evidence_files = {str(receipt_path): sha256(receipt_path)}
    for split in ("train", "dev"):
        manifest = receipt.get("manifests", {}).get(split, {})
        expected_rows, expected_groups, expected_sha = selector.PINNED[split]
        require(manifest.get("sha256") == expected_sha and manifest.get("rows") == expected_rows
                and manifest.get("youtube_groups") == expected_groups, "original pinned manifest identity differs")
        path = old_dir / ("selected_" + split + ".jsonl")
        require(sha256(path) == receipt.get("files", {}).get(path.name), "original selected bytes differ")
        original[split] = rows(path)
        require(len(original[split]) == COUNTS[split]
                and all(row.get("split") == split for row in original[split]), "original split/window count differs")
        evidence_files[str(path)] = sha256(path)
    selector.validate_isolation(original["train"], original["dev"])
    combined = original["train"] + original["dev"]
    require(len({row.get("window_id") for row in combined}) == 160, "original window IDs are not unique")
    require(all(isinstance(row.get("source_group"), str) and row["source_group"]
                and row["source_group"] == row.get("youtube_id") for row in combined), "old YouTube leakage unit missing")
    require(len({row["source_group"] for row in combined}) == 160, "original exclusion must cover 160 distinct groups")
    identity = {row["window_id"]: {key: row[key] for key in ("window_id", "split", "source_group", "youtube_id", "source_path")}
                for row in combined}
    context_ids, context_groups, context_evidence = set(), set(), []
    require(contexts, "prior context registrations cannot be silently omitted")
    for path in contexts:
        manifest = read_json(path)
        window_ids = manifest.get("window_ids")
        require(isinstance(window_ids, list) and window_ids and all(isinstance(w, str) and w for w in window_ids)
                and len(set(window_ids)) == len(window_ids), "invalid prior context identity registration")
        require(set(window_ids) <= set(identity), "prior context window lacks old source-group identity; STOP exclusion")
        context_ids.update(window_ids)
        context_groups.update(identity[w]["source_group"] for w in window_ids)
        context_evidence.append({"path": str(path), "sha256": sha256(path), "window_ids": window_ids,
                                 "source_groups": sorted({identity[w]["source_group"] for w in window_ids})})
    groups = {row["source_group"] for row in combined} | context_groups
    paths = {row["source_path"] for row in combined}
    evidence = {"rule": "EXCLUDE_ALL_OLD_160_YOUTUBE_GROUPS_AND_ALL_REGISTERED_CONTEXT_GROUPS_BEFORE_RANKING",
        "original_window_count": 160, "original_source_group_count": 160,
        "context_window_count": len(context_ids), "context_source_group_count": len(context_groups),
        "excluded_source_group_count": len(groups), "excluded_source_groups": sorted(groups),
        "original_identity_files_sha256": evidence_files, "context_registrations": context_evidence,
        "old_labels_or_answers_read": False, "identity_only_exclusion": True}
    return groups, paths, evidence, receipt


def candidates_for_split(identities, split, excluded_groups, excluded_paths, count, *, selector=SELECTOR):
    eligible = [row for row in identities if row["youtube_id"] not in excluded_groups
                and row["source_path"] not in excluded_paths]
    ranked = selector.rank_sources(eligible, split)
    require(len(ranked) >= count, "insufficient untouched approved distinct " + split + " groups")
    selected = ranked[:count]
    require(len({row["source_group"] for row in selected}) == count, "duplicate fresh source groups")
    require(not ({row["source_group"] for row in selected} & excluded_groups), "old source group entered fresh selection")
    return selected, len(ranked)


def validate_selected(selected, excluded_groups, excluded_paths, *, counts=COUNTS, selector=SELECTOR):
    require(set(selected) == {"train", "dev"}, "fresh split keys differ")
    selector.validate_isolation(selected["train"], selected["dev"])
    combined = selected["train"] + selected["dev"]
    for split in ("train", "dev"):
        require(len(selected[split]) == counts[split] and all(row.get("split") == split for row in selected[split]),
                "fresh split denominator differs")
    require(len({row["window_id"] for row in combined}) == sum(counts.values()), "duplicate fresh window identity")
    require(len({row["source_group"] for row in combined}) == sum(counts.values()), "fresh selection repeats YouTube group")
    require(all(row["source_group"] == row["youtube_id"] for row in combined), "fresh leakage unit differs")
    require(not ({row["source_group"] for row in combined} & excluded_groups), "fresh selection intersects old source groups")
    require(not ({row["source_path"] for row in combined} & excluded_paths), "fresh selection intersects old source paths")
    require(all(row.get("label_status") == "UNLABELLED" and row.get("old_positive_segments_used") is False
                for row in combined), "fresh selection must stay unlabelled")


def check_output(path, owner_root=HERE):
    resolved, root = Path(path).resolve(), Path(owner_root).resolve()
    require(root in resolved.parents, "outputs must stay within owned v8 directory")
    require(not resolved.exists(), "never overwrite an existing v8 preparation")
    return resolved


def pilot_choice(selected):
    def ranked(population, count):
        require(len(population) >= count, "insufficient fresh pilot population")
        return sorted(population, key=lambda row: (hashlib.sha256(row["window_id"].encode()).hexdigest(), row["window_id"]))[:count]
    return {split: ranked(selected[split], PILOT_COUNTS[split]) for split in ("train", "dev")}


def write_pilot(selection_dir, out_dir, prompt_path, *, owner_root=HERE, selector=SELECTOR):
    """Create one immutable subset receipt compatible with the teacher validator."""
    selection_dir = Path(selection_dir)
    receipt_path = selection_dir / "selection_receipt.json"
    original = read_json(receipt_path)
    require(original.get("status") == "PASS_CPU_SELECTION_UNLABELLED" and original.get("counts") == COUNTS,
            "fresh full 128/32 selection must pass before pilot registration")
    require(original.get("seed") == SEED and original.get("fresh_source_groups_disjoint_from_all_prior") is True,
            "pilot requires v8 untouched selection")
    for name, digest in original["files"].items():
        require(name in ("selected_train.jsonl", "selected_dev.jsonl", "source_clocks.jsonl"), "unexpected parent selection file")
        require(sha256(selection_dir / name) == digest, "fresh parent selection bytes differ")
    require(set(original["files"]) == {"selected_train.jsonl", "selected_dev.jsonl", "source_clocks.jsonl"}, "parent selection byte binding incomplete")
    selected = {split: rows(selection_dir / ("selected_" + split + ".jsonl")) for split in ("train", "dev")}
    excluded = set(original["exclusion"]["excluded_source_groups"])
    validate_selected(selected, excluded, set(), selector=selector)
    pilot = pilot_choice(selected)
    validate_selected(pilot, excluded, set(), counts=PILOT_COUNTS, selector=selector)
    require(Path(prompt_path).is_file(), "actual v8 teacher prompt required before pilot registration")
    out = check_output(out_dir, owner_root)
    out.mkdir(parents=True)
    for split in ("train", "dev"):
        selector.write_jsonl(out / ("selected_" + split + ".jsonl"), pilot[split])
    receipt = {**original, "schema": "aic_preregistered_nontest_pilot_subset_v8", "purpose": "PILOT_ONLY_NOT_FULL_STUDENT_ADMISSION",
        "counts_requested": PILOT_COUNTS, "counts": PILOT_COUNTS, "parent_counts": COUNTS,
        "parent_selection_receipt": {"path": str(receipt_path), "sha256": sha256(receipt_path)},
        "files": {name: sha256(out / name) for name in ("selected_train.jsonl", "selected_dev.jsonl")},
        "pilot_rule": PILOT_RULE, "label_values_or_prior_answers_read": False,
        "selected_windows": PILOT_COUNTS, "created_utc": dt.datetime.now(dt.timezone.utc).isoformat()}
    save_json(out / "selection_receipt.json", receipt)
    manifest = {"status": "PASS_PREREGISTERED_LABEL_INDEPENDENT_PILOT",
        "window_ids": [row["window_id"] for row in pilot["train"] + pilot["dev"]],
        "counts": PILOT_COUNTS, "rule": PILOT_RULE,
        "parent_files_sha256": {name: sha256(selection_dir / name)
            for name in ("selected_train.jsonl", "selected_dev.jsonl", "selection_receipt.json")},
        "selection_receipt_sha256": sha256(out / "selection_receipt.json"), "no_label_access": True,
        "teacher_prompt_sha256": sha256(prompt_path), "fresh_source_groups_disjoint_from_all_prior": True,
        "old_12_are_regression_only_not_pilot": True}
    save_json(out / "manifest.json", manifest)
    return manifest


def run_selection(train_manifest, dev_manifest, old_dir, contexts, out_dir, pilot_dir, prompt_path, ffprobe,
                  source_timeout=240, *, selector=SELECTOR, owner_root=HERE, expected_old_receipt_sha=OLD_RECEIPT_SHA256):
    require(type(source_timeout) is int and source_timeout > 0, "invalid full-source clock-scan timeout")
    require(Path(ffprobe).is_file(), "existing ffprobe required; no automatic installation")
    require(Path(prompt_path).is_file(), "finish the v8 teacher prompt before preregistering pilot")
    out = check_output(out_dir, owner_root)
    check_output(pilot_dir, owner_root)
    require(Path(pilot_dir).resolve() != out, "full selection and pilot must have distinct output directories")
    exclusions, excluded_paths, evidence, old_receipt = load_exclusions(old_dir, contexts, selector=selector,
        expected_receipt_sha=expected_old_receipt_sha)
    manifests = {"train": Path(train_manifest), "dev": Path(dev_manifest)}
    identities = {split: selector.load_identities(manifests[split], split) for split in ("train", "dev")}
    selector.validate_isolation(identities["train"], identities["dev"])
    # Check both complete populations before any clock probing or output creation.
    candidates, available = {}, {}
    for split in ("train", "dev"):
        candidates[split], available[split] = candidates_for_split(identities[split], split, exclusions,
            excluded_paths, COUNTS[split], selector=selector)
    out.mkdir(parents=True)
    receipt = {key: value for key, value in old_receipt.items() if key not in ("files", "counts", "structural_strata",
        "non_sampleable_time_cell_count", "sources_with_non_sampleable_time_cells", "all_sources_have_actual_pts_grid_coverage")}
    receipt.update(schema="aic_complete_window_selection_receipt_v2", started_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
        status="CPU_SELECTION_IN_PROGRESS", tier="first", counts_requested=COUNTS, seed=SEED,
        manifests={split: {"path": str(manifests[split]), "sha256": selector.PINNED[split][2],
            "rows": selector.PINNED[split][0], "youtube_groups": selector.PINNED[split][1]} for split in ("train", "dev")},
        first_is_prefix_of_expanded=False, exclusion=evidence, available_untouched_source_groups=available,
        preregistered_source_groups={split: [source["source_group"] for source in candidates[split]]
            for split in ("train", "dev")},
        source_selector={"path": str(SELECTOR_PATH), "sha256": SELECTOR_SHA256,
            "algorithm": "INHERITED_V2_NATIVE_FULL_SOURCE_PTS_30S_GRID_64_INTEGER_FLOOR_ENDPOINT_SAMPLING"},
        fresh_source_groups_disjoint_from_all_prior=True, prior_12_regression_only=True,
        labels_generated=False, gpu_used=False, confirm_opened=False, contest_assets_opened=False)
    save_json(out / "preregistration.json", receipt)
    selected, clocks, current_source = {"train": [], "dev": []}, [], None
    try:
        for split in ("train", "dev"):
            for source in candidates[split]:
                current_source = source
                points, clock = selector.probe_source(source["source_path"], ffprobe, source_timeout)
                clock["natural_grid_audit"] = selector.audit_grid(points, clock)
                clocks.append({"split": split, "source_group": source["source_group"], **clock})
                selected[split].append(selector.make_window(source, points, clock))
                print(json.dumps({"split": split, "completed": len(selected[split]), "requested": COUNTS[split]}), flush=True)
        validate_selected(selected, exclusions, excluded_paths, selector=selector)
        for split in ("train", "dev"):
            selector.write_jsonl(out / ("selected_" + split + ".jsonl"), selected[split])
        selector.write_jsonl(out / "source_clocks.jsonl", clocks)
        receipt.update(status="PASS_CPU_SELECTION_UNLABELLED", counts={split: len(values) for split, values in selected.items()},
            structural_strata={split: {kind: sum(row["structural_stratum"] == kind for row in values)
                for kind in ("source_beginning", "interior", "source_end")} for split, values in selected.items()},
            non_sampleable_time_cell_count=sum(len(clock["natural_grid_audit"]["non_sampleable_time_cells"]) for clock in clocks),
            sources_with_non_sampleable_time_cells=sum(bool(clock["natural_grid_audit"]["non_sampleable_time_cells"]) for clock in clocks),
            all_sources_have_actual_pts_grid_coverage=True,
            files={name: sha256(out / name) for name in ("selected_train.jsonl", "selected_dev.jsonl", "source_clocks.jsonl")},
            preregistration_sha256=sha256(out / "preregistration.json"), completed_utc=dt.datetime.now(dt.timezone.utc).isoformat())
    except Exception as exc:
        receipt.update(status="STOP_CPU_SELECTION_CLOCK_OR_IDENTITY", reason=f"{type(exc).__name__}: {exc}",
            failed_source=current_source, completed_unlabelled_counts={split: len(values) for split, values in selected.items()},
            partial_files_are_unlabelled_not_full_selection_pass=True)
        selector.write_jsonl(out / "partial_source_clocks.jsonl", clocks)
        for split in ("train", "dev"):
            selector.write_jsonl(out / ("partial_selected_" + split + ".jsonl"), selected[split])
        save_json(out / "selection_receipt.json", receipt)
        raise
    save_json(out / "selection_receipt.json", receipt)
    manifest = write_pilot(out, pilot_dir, prompt_path, owner_root=owner_root, selector=selector)
    return {"status": receipt["status"], "counts": receipt["counts"], "selection_receipt_sha256": sha256(out / "selection_receipt.json"),
        "pilot_counts": manifest["counts"], "pilot_manifest_sha256": sha256(Path(pilot_dir) / "manifest.json"), "gpu_used": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train-manifest", type=Path, required=True)
    parser.add_argument("--dev-manifest", type=Path, required=True)
    parser.add_argument("--old-selection-dir", type=Path, default=RUN / "next_round_v1/supervision_v2/selection_02")
    parser.add_argument("--out-dir", type=Path, default=HERE / "selection_01")
    parser.add_argument("--pilot-dir", type=Path, default=HERE / "pilot_selection")
    parser.add_argument("--teacher-prompt", type=Path, default=HERE / "teacher_prompt.txt")
    parser.add_argument("--ffprobe", default=FFPROBE)
    parser.add_argument("--source-timeout", type=int, default=240)
    args = parser.parse_args()
    result = run_selection(args.train_manifest, args.dev_manifest, args.old_selection_dir, context_manifests(), args.out_dir,
        args.pilot_dir, args.teacher_prompt, args.ffprobe, args.source_timeout)
    print(json.dumps(result, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
