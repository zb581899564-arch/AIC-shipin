"""One frozen advisory recipe: exact native CPU preflight and owned GPU jobs.

No grading data is used by selection or inference. Reference-set agreement is
computed separately after the four complete developer arms are committed.
"""
import argparse
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys
import time
import traceback

import context_contract as cc
import runtime as rt

HERE, RUN = rt.HERE, rt.RUN


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for b in iter(lambda: f.read(8 << 20), b""):
            h.update(b)
    return h.hexdigest()


def progress(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)
    print(json.dumps(value), flush=True)


def verify():
    lock = read(HERE / "source_lock.json")
    for path, wanted in lock["files"].items():
        cc.require(sha(path) == wanted, "registered dependency changed: " + path)
    return lock


def scope_plan(scope):
    student, old, frames, production = rt.bind_helpers()
    ref, manifest, clocks = old.inputs(scope)
    jobs, sources = [], {}
    source_clock = rt.load(HERE / "prepare.py", "cad_prepare").source_clock
    for item in manifest["records"]:
        clock = clocks[item["video_id"]]
        a = clock["arrays"]
        tick = Fraction(a["raw_time_base"])
        points = [float(x * tick) for x in a["native_pts_ticks"]]
        key = item["source_sha256"]
        # Independently scan the actual terminal packet. Do not infer an
        # overview endpoint from nominal CFR FPS or frame count.
        physical = source_clock(item, manifest["allowed_source_roots"])
        cc.require(physical["pts"] == points, "current scope registry differs from native full-source PTS")
        sources[key] = physical
        windows = []
        for j, (start, end) in enumerate(frames.window_schedule(item, manifest["kind"], clock)):
            raw_start, raw_end = production.raw_window_bounds(a, start, end)
            w = student.window_from_pts(item["source_path"], key, points, raw_start, raw_end,
                item["video_id"] + ":CAD:" + str(j), width=item["width"], height=item["height"])
            w["window_duration_sec"] = end - start
            windows.append({"start_sec": start, "end_sec": end, "window": w,
                "clock_record_sha256": clock["clock_record_sha256"], "clock_branch": clock["branch"],
                "raw_source_pts_origin_sec": float(a["raw_first_pts_ticks"] * tick)})
        jobs.append(dict(video_id=item["video_id"], source_key=key, source_group=item["source_sha256"],
            metadata=item, windows=windows))
        print(json.dumps({"stage": "SCOPE_NATIVE_CPU_SCAN", "scope": scope, "sources": len(sources)}), flush=True)
    mapping = cc.deterministic_derangement(list(sources), {k: c["duration_sec"] for k, c in sources.items()}) if scope == "nontest" else {}
    value = dict(scope=scope, jobs=jobs, sources=sources, shuffle_source_mapping=mapping, input_ref=ref,
        overview_source_files=len(sources), records=len(jobs), windows=sum(len(x["windows"]) for x in jobs),
        no_model_calls=True)
    rt.raw_write(HERE / "input_01" / (scope + "_plan.json"), value)
    return value


def overview_window(source, key):
    return cc.overview_plan(source["source_path"], key, source["pts"], source["raw_end_exclusive_sec"],
        key + ":SOURCE_OVERVIEW", width=source["width"], height=source["height"],
        observation_authority="EXACT_PERMITTED_SOURCE_FILE_NO_CROSS_FILE_UNION")


def source_tables(plan):
    return {k: read(p) for k, p in plan["source_clocks"].items()} if "source_clocks" in plan else plan["sources"]


def base_texts(old):
    from contracts import EMPTY_PROMPT
    tc = rt.load(RUN / "baseline_a_pts_v1/vendor/temporal_common.py", "cad_prompt_only")
    return {"B1": tc.PROMPT, "B0": EMPTY_PROMPT}


def arm_text(arm, window, table, donor_table, texts):
    if arm in texts:
        return texts[arm], {}
    if arm == "N":
        context = json.dumps({"source_context_provided": False,
            "missing_context_does_not_mean_no_events": True}, separators=(",", ":"))
        audit = {"context_not_provided": True}
    else:
        selected = table if arm == "R" else donor_table
        count = len(selected["overview_window"]["planned_actual_pts_sec"])
        own_pts = table["overview_window"]["planned_actual_pts_sec"]
        value = selected["events"]
        if count != len(own_pts):
            # Same normalized rank map for all legal short-source denominators.
            mapped = {"events": [dict(e, first=(e["first"] * (len(own_pts) - 1) // max(count - 1, 1)),
                last=(e["last"] * (len(own_pts) - 1) // max(count - 1, 1))) for e in value["events"]]}
        else:
            mapped = value
        context = cc.render_event_table(mapped, own_pts, window["window_pts_start_sec"], window["window_pts_end_exclusive_sec"])
        audit = {"context_source_sha256": selected["overview_window"]["source_sha256"],
            "recipient_source_sha256": window["source_sha256"], "donor_raw_receipt": selected["raw_receipt"],
            "deliberately_wrong_context_diagnostic_only": arm == "X", "not_recipient_evidence": arm == "X"}
    return texts["B0"] + rt.ADVISORY_TEXT + context, audit


def tensor_sha(value):
    return hashlib.sha256(value.detach().cpu().contiguous().view(__import__('torch').uint8).numpy().tobytes()).hexdigest()


def video_signature(encoded):
    return {k: {"shape": list(v.shape), "dtype": str(v.dtype), "sha256": tensor_sha(v)}
        for k, v in encoded.items() if k in ("pixel_values_videos", "video_grid_thw")}


def cpu_preflight(draft=False):
    if not draft:
        verify()
    student, old, frames, production = rt.bind_helpers()
    from transformers import AutoProcessor
    from constrained_json import ascii_token_candidates
    checks = rt.load(HERE / "tests.py", "cad_tests").test_contracts()
    cfg = old.read(RUN / "b_score_aligned_package_v4/config.json")
    processor = AutoProcessor.from_pretrained(cfg["model_dir"], local_files_only=True, min_pixels=131072, max_pixels=131072)
    candidates = rt.overview_candidates(processor.tokenizer)
    # Check the actual fixed tokenizer's whole-context ASCII additivity on all
    # candidates in several syntax/description contexts, not synthetic mocks.
    tok = processor.tokenizer
    for prefix in ('', '{"events":[{"first":', '{"events":[{"first":0,"last":0,"description":"'):
        ids = tok.encode(prefix, add_special_tokens=False)
        actual = tok.decode(ids, skip_special_tokens=False, clean_up_tokenization_spaces=False)
        for token, piece in candidates:
            cc.require(tok.decode(ids + [token], skip_special_tokens=False, clean_up_tokenization_spaces=False) == actual + piece,
                "actual ASCII candidate is context-dependent")
    plan = read(HERE / "input_01/nontest_plan.json")
    texts, proofs = base_texts(old), []
    import torch
    for job in plan["jobs"]:
        window = job["windows"][0]["window"]
        decoded = student.decode_window(window)
        ov = overview_window(plan["sources"][job["source_key"]], job["source_key"])
        # Test real overview decode and processor without any GPU model call.
        over_decoded = student.decode_window(ov)
        overview_encoded, ov_evidence = rt.encode_decoded(processor, over_decoded, rt.OVERVIEW_TEXT)
        dummy = {"events": {"events": [{"first": 0, "last": 0, "description": "visible activity"}]},
            "overview_window": ov, "raw_receipt": "CPU_CONTRACT_ONLY"}
        common = None
        for arm in ("B1", "B0", "N", "R", "X"):
            text, audit = arm_text(arm, window, dummy, dummy, texts)
            encoded, identity = rt.encode_decoded(processor, decoded, text)
            signature = video_signature(encoded)
            if common is None:
                common = signature
            cc.require(signature == common, "advisory changed local video tensor/grid")
            if arm == "B0":
                original, original_identity = student.production_encode(processor, window)
                cc.require(set(original) == set(encoded) and all(torch.equal(original[k], encoded[k]) for k in encoded),
                    "new B0 encoding differs from actual V14 production function")
                cc.require(original_identity["frame_pixel_sha256"] == identity["frame_pixel_sha256"], "B0 pixel identity")
                del original
            del encoded
        proofs.append({"video_id": job["video_id"], "all_five_vision_tensors_equal": True,
            "B0_all_encoded_tensors_equal_actual_V14": True, "pixel_sha256": decoded[3]["frame_pixel_sha256"],
            "overview_pixels": ov_evidence["frame_pixel_sha256"], "overview_input_tokens": int(overview_encoded["input_ids"].shape[1])})
        del overview_encoded, over_decoded, decoded
        print(json.dumps({"stage": "CPU_REAL_PROCESSOR_NONTEST", "videos": len(proofs), "total": 8}), flush=True)
    cc.require(len(proofs) == 8, "NONTEST8 CPU denominator")
    rt.raw_write(HERE / ("draft_preflight.json" if draft else "preflight.json"), dict(checks, status="PASS_REAL_CPU_NATIVE_PROCESSOR_CONTRACTS_NO_GPU_CALLS",
        tokenizer_candidate_count=len(candidates), tokenizer_ascii_contexts=3, non_test_proofs=proofs,
        source_lock_sha256=None if draft else sha(HERE / "source_lock.json")))


def loaded_model():
    student, old, _, production = rt.bind_helpers()
    from sft_contract import verify_live_gpu_reservation
    from engine import load_model
    from verify_saved_smoke import canonical_frozen_hash
    from constrained_json import ascii_token_candidates
    import torch
    verify_live_gpu_reservation()
    cfg = read(RUN / "b_score_aligned_package_v4/config.json")
    cc.require(sha(Path(cfg["b_adapter"]) / "adapter_model.safetensors") == cfg["b_adapter_sha256"], "B adapter file changed")
    model, processor, count = load_model(cfg, adapter=True)
    base_hash = canonical_frozen_hash(model, torch)
    production.check_base_hash(base_hash, cfg)
    from safetensors.torch import load_file
    saved = load_file(str(Path(cfg["b_adapter"]) / "adapter_model.safetensors"), device="cpu")
    actual = {name.replace("base_model.model.", "", 1).replace(".default", ""): p.detach().cpu() for name, p in model.named_parameters() if "lora_" in name}
    # Peft save keys retain the base_model.model prefix. Match only its declared
    # canonical key transformation, not fuzzy suffixes.
    expected = {name.replace("base_model.model.", "", 1): p for name, p in saved.items()}
    cc.require(len(actual) == len(expected) == 288 and set(actual) == set(expected) and
        all(torch.equal(actual[name], expected[name]) for name in actual), "loaded 288 adapter tensors differ from B saved bytes")
    cc.require(not model.training and not any(p.requires_grad for p in model.parameters()), "inference model not frozen/eval")
    identity = dict(base_hash=base_hash, logical_parameters=count, adapter_sha256=cfg["b_adapter_sha256"],
        adapter_saved_tensor_equality=288, new_optimizer_updates=0)
    return student, old, model, processor, ascii_token_candidates(processor.tokenizer), rt.overview_candidates(processor.tokenizer), identity


def checked_done(path, request):
    value = read(path)
    cc.require(value["request_sha256"] == cc.digest(request), "attempt cache request differs")
    for p, wanted in value["bound_files"].items():
        cc.require(sha(p) == wanted, "completed attempt byte identity changed")
    cc.require(value.get("output_valid") is True, "attempt cache was invalid")
    return value


def run(stage):
    verify()
    cc.require(read(HERE / "preflight.json")["status"] == "PASS_REAL_CPU_NATIVE_PROCESSOR_CONTRACTS_NO_GPU_CALLS", "preflight missing")
    if stage in ("nontest", "rematch"):
        plan = read(HERE / "input_01" / (stage + "_plan.json"))
        jobs = plan["jobs"]
        out = HERE / (stage + "_01")
        arms = ("B1", "B0", "N", "R", "X") if stage == "nontest" else ("R",)
    else:
        plan = read(HERE / "input_01/developer_plan.json")
        jobs = plan["developer_jobs"]
        if stage == "pilot":
            jobs = [x for x in jobs if x["video_id"] in plan["pilot_video_ids"]]
        out = HERE / "developer_01"
        arms = ("B1", "B0", "N", "R", "X") if stage == "pilot" else ("B0", "N", "R", "X")
    out.mkdir(exist_ok=True)
    started = time.monotonic()
    student, old, model, processor, local_candidates, event_candidates, model_identity = loaded_model()
    rt.raw_write(out / (stage + ".model.json"), model_identity)
    sources = source_tables(plan)
    needed = {j["source_key"] for j in jobs}
    if "X" in arms:
        needed |= {plan["shuffle_source_mapping"][j["source_key"]] for j in jobs}
    tables, fresh_overview, reused_overview = {}, 0, 0
    for key in sorted(needed):
        w = overview_window(sources[key], key)
        request = {"kind": "overview", "window": w, "prompt": rt.OVERVIEW_TEXT, "model": model_identity,
            "max_input": 16384, "max_output": 1280, "adapter_disabled": True}
        folder = out / "overview" / key
        done = folder / "done.json"
        if done.exists():
            table = checked_done(done, request); reused_overview += 1
        else:
            encoded, evidence = rt.encode_decoded(processor, student.decode_window(w), rt.OVERVIEW_TEXT)
            raw = folder / "raw.json"
            table = rt.attempt(model, processor, encoded, evidence, w, raw, overview=True, event_candidates=event_candidates)
            table.update(overview_window=w, request_sha256=cc.digest(request), model_identity=model_identity,
                bound_files={str(raw): sha(raw)}, overview_input_tokens=int(encoded["input_ids"].shape[1]))
            rt.raw_write(done, table); fresh_overview += 1
            del encoded
        cc.validate_overview(table["raw_output"], w["planned_actual_pts_sec"])
        tables[key] = table
        progress(out / "progress.json", {"stage": stage + "_OVERVIEW", "completed": len(tables), "total": len(needed),
            "fresh_model_calls": fresh_overview, "reused_calls": reused_overview, "wall_seconds": time.monotonic() - started})
    texts = base_texts(old)
    fresh, reused = 0, 0
    for num, job in enumerate(jobs, 1):
        table = tables[job["source_key"]]
        donor = tables[plan["shuffle_source_mapping"][job["source_key"]]] if "X" in arms else table
        for ix, part in enumerate(job["windows"]):
            w = part["window"]
            decoded = student.decode_window(w)
            vision_signature = None
            for arm in arms:
                text, audit = arm_text(arm, w, table, donor, texts)
                request = {"kind": "local", "window": w, "arm": arm, "prompt": text, "model": model_identity,
                    "max_input": 16384, "max_output": 256, "allow_empty": arm != "B1", "context_audit": audit}
                folder = out / "local" / cc.digest(job["video_id"]) / str(ix) / arm
                done = folder / "done.json"
                if done.exists():
                    value = checked_done(done, request); reused += 1
                else:
                    encoded, evidence = rt.encode_decoded(processor, decoded, text)
                    sig = video_signature(encoded)
                    if vision_signature is None:
                        vision_signature = sig
                    cc.require(sig == vision_signature, "arm changed local vision tensor")
                    raw = folder / "raw.json"
                    value = rt.attempt(model, processor, encoded, evidence, w, raw, allow_empty=arm != "B1", local_candidates=local_candidates)
                    value.update(request_sha256=cc.digest(request), bound_files={str(raw): sha(raw)}, arm=arm,
                        window=w, model_identity=model_identity, context_audit=audit, vision_tensor_signature=sig)
                    rt.raw_write(done, value); fresh += 1
                    del encoded
                # Validate even exactly reused attempts against current original validator.
                from contracts import parse_segments
                parsed, errors, _ = parse_segments(value["raw_output"], w["window_duration_sec"], allow_empty=arm != "B1")
                cc.require(not errors and parsed == value["parsed_segments"], "reused original validator differs")
                if vision_signature is None:
                    vision_signature = value["vision_tensor_signature"]
                cc.require(value["vision_tensor_signature"] == vision_signature, "reused arm video identity differs")
            del decoded
        progress(out / "progress.json", {"stage": stage + "_LOCAL", "videos": num, "total": len(jobs),
            "fresh_local_calls": fresh, "reused_local_calls": reused, "fresh_overviews": fresh_overview,
            "reused_overviews": reused_overview, "wall_seconds": time.monotonic() - started})
    rt.raw_write(out / (stage + ".completion.json"), {"status": "PASS_ALL_REGISTERED_ADVISORY_ATTEMPTS",
        "stage": stage, "records": len(jobs), "source_files": len(needed), "arms": list(arms),
        "fresh_local_calls": fresh, "reused_local_calls": reused, "fresh_overview_calls": fresh_overview,
        "reused_overview_calls": reused_overview, "model_identity": model_identity, "wall_seconds": time.monotonic() - started})


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=("prepare-nontest", "prepare-rematch", "draft-preflight", "preflight", "nontest", "pilot", "full", "rematch"))
    args = parser.parse_args()
    if args.stage.startswith("prepare-"):
        scope_plan(args.stage.split("-", 1)[1])
    elif args.stage in ("preflight", "draft-preflight"):
        cpu_preflight(draft=args.stage == "draft-preflight")
    else:
        run(args.stage)
