"""Complete Linux production orchestration for the preregistered final sprint.

Every expensive logical call and complete source has an immutable journal.
Raw images stay in memory; compact reusable feature tensors and evidence stay
in the Linux journal. Nothing is sent to an external inference service.
No proxy labels, old launchers, default answers or platform submission APIs.
"""
from __future__ import annotations

from dataclasses import asdict
from fractions import Fraction
import math
import os
from pathlib import Path
import time

from . import assets as asset_api
from .contracts import (atomic_new, checked, ref, require, stable_key, strict_load,
                        total_parameters, utc_now, validate_sources)
from .controls import maximum_width_at_fixed_center
from .observation import decode_native_frames, iter_decoded_clips, plan_clips
from .packaging import baseline_frames, build_package
from .resources import Budget, gpu_lease, snapshot
from .runtime_cache import CallJournal
from .spatial import SpatialConfig, process_source, semantic_extent_control
from .temporal import select_source


def write_adopt(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        require(strict_load(path) == value, "Existing artifact differs from exact deterministic result: " + str(path))
    else:
        atomic_new(path, value)
    return ref(path)


def enriched_sources(assets):
    documents, result = {}, []
    for source in assets["sources"]:
        identity = source["clock"]
        key = (identity["path"], identity["sha256"])
        if key not in documents:
            documents[key] = strict_load(checked(identity))
        clock = documents[key]
        if "source_key" in identity:
            clock = clock[identity["source_key"]]
        result.append(dict(source, normalized_exact_pts=clock["normalized_exact_pts"],
                           physical_end_exact=clock["physical_end_exact"],
                           first_original_pts_exact=clock.get("first_original_pts_exact"),
                           physical_endpoint_evidence=clock.get("physical_endpoint_evidence")))
    return sorted(result, key=lambda row: stable_key("source-order20261023", row["media"]["sha256"]))


def route_family(candidate_id):
    if candidate_id.startswith("g_"):
        return "grounding"
    if candidate_id.startswith("r_"):
        return "phase"
    return "specialist"


DERIVED_CANDIDATES = {"r_phase_apex", "g_center_control", "g_semantic_extent_control"}


def phase_options(candidate):
    """Execute the registered recipe, rather than similar function defaults."""
    config = candidate["configuration"]
    return {"clip_seconds": config["clip_seconds"], "samples_per_clip": config["samples_per_clip"],
            "fraction": Fraction(config["duration_fraction"]),
            "segment_penalty": config["event_start_penalty"],
            "cost_resolution_ms": config["cost_resolution_ms"],
            "event_utility": config["event_utility"]}


def specialist_options(candidate):
    from .specialist import SpecialistConfig
    config = candidate["configuration"]
    result = SpecialistConfig(cell_seconds=str(config["cell_seconds"]),
        maximum_window_cells=config["max_cells"], window_stride_cells=config["stride_cells"],
        maximum_duration_fraction=config["duration_fraction"],
        foreground_probability=config["foreground_probability"],
        image_batch_size=config["image_batch_size"],
        maximum_forward_windows=config["maximum_forward_windows"])
    result.validate()
    return result


class Engine:
    def __init__(self, assets, assets_path, candidate_id, budget):
        self.assets, self.assets_path, self.candidate_id = assets, assets_path, candidate_id
        self.binding = asset_api.binding(assets, assets_path, candidate_id)
        self.candidate = self.binding["candidate"]
        self.root = Path(assets["run_root"])
        self.directory = self.root / "candidates" / candidate_id
        self.budget = budget
        self.sources = enriched_sources(assets)
        self.source_map = {s["video_id"]: s for s in self.sources}
        self.base = baseline_frames(assets["protected_baselines"])["40.48"]
        self.base_binding = {"asset_lock": ref(assets_path), "code": assets["source_commit"],
                             "no_training": True, "seed": 20261023}
        self.journal = CallJournal(self.root / "journal", self.base_binding, budget)
        if assets.get("pure_call_adoption"):
            require(route_family(candidate_id) != "phase", "FP32 phase cannot inherit BF16 calls")
            from .pure_call_adoption import PureCallJournal, validate_manifest
            entries = validate_manifest(assets, assets["pure_call_adoption"])
            self.journal = PureCallJournal(self.journal, entries)
        self._qwen = None
        self._specialist = None
        self.inherited_grounding = {}
        if assets.get("inherited_grounding"):
            from .inherited_grounding import validate_manifest
            self.inherited_grounding = validate_manifest(assets, assets["inherited_grounding"])
        self.ground_refs = []
        self.adopted_ground_calls = 0
        self.adopted_ground_seconds = 0.0
        self.spatial_config = SpatialConfig(**asset_api.candidate_registry()["shared_spatial_configuration"])
        self.spatial_config.validate()
        self.model_initialization_seconds = 0.0
        self.specialist_spec_sha256 = stable_key(self.assets.get("specialist"))

    def qwen(self):
        if self._qwen is None:
            from .qwen_runtime import QwenRuntime
            self.budget.check()
            started = time.monotonic()
            specification = dict(self.assets["qwen"])
            profile = self.candidate["configuration"].get("arithmetic_profile")
            if profile:
                require(route_family(self.candidate_id) == "phase", "Only R uses registered FP32 arithmetic")
                specification["arithmetic_profile"] = profile
            self._qwen = QwenRuntime(specification)
            self._qwen.load()
            identity = self._qwen.parameter_receipt()
            write_adopt(self.root / "model_parameters" / "qwen_base.json", identity)
            self.parameters()
            self.model_initialization_seconds += time.monotonic() - started
        return self._qwen

    def specialist(self):
        require(self.assets.get("specialist"), "Published specialist assets were not bound; run another registered route")
        if self._specialist is None:
            from .specialist import SpecialistRuntime
            self.budget.check()
            started = time.monotonic()

            def cache(kind, key, payload, compute):
                call_id = "specialist_" + kind + "_" + stable_key(key, payload)[:36]
                call_binding = {"kind": kind, "key": key, "payload": payload,
                                "specialist_spec_sha256": self.specialist_spec_sha256}
                return self.journal.call(call_id, call_binding, compute)

            self._specialist = SpecialistRuntime(self.assets["specialist"],
                config=specialist_options(self.candidate), call_cache=cache).load()
            for receipt in self._specialist.parameter_receipts():
                write_adopt(self.root / "model_parameters" / (receipt["component_id"] + ".json"), receipt)
            self.model_initialization_seconds += time.monotonic() - started
            # Count every actual producer, including the shared Qwen query/space
            # model, BEFORE the first specialist prediction is generated.
            self.qwen()
            self.parameters()
        return self._specialist

    def parameters(self, *, require_complete=False):
        names = self.candidate["required_model_components"]
        found = []
        for name in ("qwen_base", "clip_vit_b32", "cg_detr"):
            if name not in names:
                continue
            path = self.root / "model_parameters" / (name + ".json")
            if path.exists():
                found.append(ref(path))
            elif require_complete:
                raise ValueError("Actual loaded parameter inventory missing: " + name)
        if self.candidate_id.startswith("g_"):
            found += self.assets["baseline_parameter_receipts"]
        if not found:
            require(not require_complete, "No actual model inventory")
            return []
        actual = total_parameters(found)
        if require_complete or set(names) <= set(actual["components"]):
            require(set(names) <= set(actual["components"]), "Incomplete main+auxiliary dependency inventory")
            if self.candidate_id.startswith("g_"):
                require(actual["total_elements"] == 8816809946,
                        "Protected40.48 dependency inventory differs; do not borrow another pipeline's parameter total")
        return found

    def ground(self, source, image, metadata):
        call_binding = {"source_sha256": source["media"]["sha256"], "clock": source["clock"],
                        "request": metadata, "model": self.assets["qwen"]["asset_tree"],
                        "spatial_config": asdict(self.spatial_config)}
        task_id = "ground_" + stable_key(call_binding)[:48]
        if self.inherited_grounding:
            from .inherited_grounding import adopt_result
            adopted = adopt_result(self.inherited_grounding, task_id, call_binding)
            if adopted is not None:
                result, identity = adopted
                self.adopted_ground_calls += 1
                self.adopted_ground_seconds += result["gpu_seconds"]
                self.ground_refs.append(identity)
                return result
        result = self.journal.call(task_id, call_binding,
                                   lambda: self.qwen().ground_image(image, metadata))
        self.ground_refs.append(self.journal.result_ref(task_id, call_binding))
        return result

    def phases(self, source, *, smoke=False, cached_only=False):
        options = phase_options(self.candidate)
        plans = plan_clips(source, clip_seconds=options["clip_seconds"],
                           samples_per_clip=options["samples_per_clip"])
        if smoke:
            plans = plans[:1]
        results, pending, bindings = {}, [], {}
        for plan in plans:
            task_id = "phase_" + source["video_id"] + "_" + plan["clip_id"]
            call_binding = {"source": source["media"], "clock": source["clock"], "clip": plan,
                            "model": self.assets["qwen"]["asset_tree"],
                            "algorithm": "NATIVE_ACTION_PHASE_SEMANTIC_WORDS_V2"}
            bindings[plan["clip_id"]] = (task_id, call_binding)
            cached = self.journal.get(task_id, call_binding)
            if cached is None:
                pending.append(plan)
            else:
                results[plan["clip_id"]] = cached
        if pending:
            require(not cached_only, "CPU-only derived candidate is missing a successful parent phase call")
            for observation in iter_decoded_clips(source, pending):
                task_id, call_binding = bindings[observation["clip"]["clip_id"]]
                results[observation["clip"]["clip_id"]] = self.journal.call(task_id, call_binding,
                    lambda obs=observation: self.qwen().phase_clip(obs, verify_reference=smoke))
        ordered = [results[plan["clip_id"]] for plan in plans]
        references = [self.journal.result_ref(*bindings[plan["clip_id"]]) for plan in plans]
        if smoke:
            require(all(row.get("independent_reference_forwards", 0) > 0 for row in ordered),
                    "Phase smoke lacks actual full-prefix reference comparison; do not silently re-run successful calls")
        return ordered, references

    def query(self, source):
        if self.candidate_id == "m_generic_control":
            return self.candidate["configuration"]["query_policy"], []
        prompt = ("These chronological observations come from one video. In at most30 English words, "
                  "describe the single concrete action, demonstration, reveal or interaction most worth "
                  "showing. Describe visible participants and what happens, not timestamps or camera "
                  "quality. Return only one English sentence. Do not invent an unseen event.")
        count = source["n_frames"]
        ordinals = sorted({round(i * (count - 1) / 7) for i in range(8)})
        request = {"source": source["media"], "clock": source["clock"], "ordinals": ordinals,
                   "prompt": prompt, "model": self.assets["qwen"]["asset_tree"]}
        task_id = "query_" + source["video_id"]
        def compute():
            images = [row["rgb"] for row in decode_native_frames(source, ordinals=ordinals)]
            return self.qwen().generate_images(images, prompt, max_new_tokens=96)
        response = self.journal.call(task_id, request, compute)
        raw = response["raw_text"].strip()
        require(raw and len(raw) <= 1000, "Automatic query is empty/truncated/invalid")
        return raw, [self.journal.result_ref(task_id, request)]

    def specialist_selection(self, source):
        from .specialist import plan_cells
        cells = plan_cells(source, specialist_options(self.candidate))
        binding = {"source": source["media"], "clock": source["clock"], "cells": cells,
                   "specialist_spec_sha256": self.specialist_spec_sha256}
        task_id = "clip_features_" + source["video_id"]
        features = self.journal.call(task_id, binding, lambda: {
            "features": self.specialist().encode_source(source,
                decode_native_frames(source, ordinals=[c["sample_frame"] for c in cells]))})
        query, references = self.query(source)
        score_binding = dict(binding, query=query, features_ref=self.journal.result_ref(task_id, binding))
        score_id = "specialist_source_" + stable_key(source["video_id"], query)[:40]
        result = self.journal.call(score_id, score_binding,
            lambda: self.specialist().score_source(source, features["features"], query))
        references += [self.journal.result_ref(task_id, binding), self.journal.result_ref(score_id, score_binding)]
        return result["selected_frames"], result, references

    def _proof(self, source, predictions, detail, references):
        path = self.directory / "sources" / source["video_id"] / "spatial_evidence.json"
        proof = {"schema": "AIC_FINAL_SPATIAL_EVIDENCE_V1", "video_id": source["video_id"],
                 "source_sha256": source["media"]["sha256"], "binding_sha256": stable_key(self.binding),
                 "algorithm": self.candidate["spatial"],
                 "model_components": self.candidate["required_model_components"],
                 "input_refs": [source["media"], source["clock"], *references],
                 "frames": predictions, "observed_pixel_evidence": detail}
        return write_adopt(path, proof)

    def _finish_source(self, source, predictions, detail, references, selection):
        proof = self._proof(source, predictions, detail, references)
        result = {"video_id": source["video_id"], "source_sha256": source["media"]["sha256"],
                  "status": "SUCCESS_NONEMPTY" if predictions else "SUCCESS_EMPTY",
                  "predictions": predictions, "selection": selection,
                  "spatial_provenance": [{"frame": p["frame"], "kind": "automatic_spatial",
                      "source_sha256": source["media"]["sha256"], "evidence": proof} for p in predictions],
                  "binding_sha256": stable_key(self.binding), "evidence": proof,
                  "quality": "UNVALIDATED_PRODUCTION_EXPLORATION"}
        return result

    def parent_source(self, parent_id, source):
        path = self.root / "candidates" / parent_id / "sources" / source["video_id"] / "result.json"
        result = strict_load(path)
        parent_binding = asset_api.binding(self.assets, self.assets_path, parent_id)
        call_binding = {"source": source["media"], "clock": source["clock"], "binding": parent_binding}
        durable = self.journal.get("source_" + parent_id + "_" + source["video_id"], call_binding)
        require(durable is not None and durable == result,
                "Parent result must equal the exact durable successful source call")
        require(result["binding_sha256"] == stable_key(parent_binding) and
                result["source_sha256"] == source["media"]["sha256"] and
                result["status"] in {"SUCCESS_EMPTY", "SUCCESS_NONEMPTY"},
                "Exact successful preregistered parent source required")
        checked(result["evidence"])
        return result, ref(path)

    def derive_source(self, source):
        if self.candidate_id == "r_phase_apex":
            parent, parent_ref = self.parent_source("r_phase_event", source)
            phases, refs = self.phases(source, cached_only=True)
            selection = select_source(source, phases, policy="apex", **phase_options(self.candidate))
            chosen = set(selection["frames"])
            predictions = [p for p in parent["predictions"] if p["frame"] in chosen]
            require({p["frame"] for p in predictions} == chosen,
                    "Apex selection lacks actual parent spatial support")
            return self._finish_source(source, predictions, {"exact_parent_subset": True},
                                       [parent_ref, parent["evidence"], *refs], selection)
        parent, parent_ref = self.parent_source("g_subject", source)
        if self.candidate_id == "g_semantic_extent_control":
            proof = strict_load(checked(parent["evidence"]))
            control = semantic_extent_control(source, proof, self.base[source["video_id"]], self.spatial_config)
            return self._finish_source(source, control["predictions"],
                {"frame_evidence": control["spatial_evidence"], "diagnostics": control["diagnostics"]},
                [parent_ref, parent["evidence"]], {"protected40.48_frames": True,
                "actual_change": "RAW_SEMANTIC_EXTENT_WITH_SAME_MEASURED_PARENT_TRANSFORMS",
                "no_new_model_calls": True, "independent_tracking_evidence": False})
        require(self.candidate_id == "g_center_control", "Unimplemented derived candidate")
        predictions, geometry = [], []
        for prediction in parent["predictions"]:
            box, witness = maximum_width_at_fixed_center(prediction["bboxes"], source)
            predictions.append({"frame": prediction["frame"], "bboxes": box})
            geometry.append(dict(frame=prediction["frame"], **witness))
        return self._finish_source(source, predictions,
                                   {"maximum_width_subject_center_control": True, "geometry": geometry},
                                   [parent_ref, parent["evidence"]], {"protected40.48_frames": True})

    def produce_source(self, source):
        if self.candidate_id in DERIVED_CANDIDATES:
            return self.derive_source(source)
        references, original_boxes = [], {}
        if self.candidate_id == "g_subject":
            original_boxes = self.base[source["video_id"]]
            frames = sorted(original_boxes)
            selection = {"protected40.48_frames": True, "baseline": self.assets["protected_baselines"]["40.48"]}
            references.append(self.assets["protected_baselines"]["40.48"])
        elif self.candidate_id == "r_phase_event":
            phases, references = self.phases(source)
            selection = select_source(source, phases, policy="event", **phase_options(self.candidate))
            frames = selection["frames"]
        else:
            frames, selection, references = self.specialist_selection(source)
        self.ground_refs = []
        spatial = process_source(decode_native_frames(source, ordinals=frames) if frames else [],
            frames, original_boxes, source["targetRatioWH"],
            lambda image, metadata: self.ground(source, image, metadata), self.spatial_config)
        unique_refs = {r["path"]: r for r in self.ground_refs}
        return self._finish_source(source, spatial["predictions"],
            {"frame_evidence": spatial["spatial_evidence"], "groundings": spatial["groundings"],
             "diagnostics": spatial["diagnostics"]}, [*references, *unique_refs.values()], selection)

    def run_sources(self):
        results = []
        fresh_seconds, fresh_duration, fresh_sources = 0.0, Fraction(0), 0
        for source in self.sources:
            sid = source["video_id"]
            task_id = "source_" + self.candidate_id + "_" + sid
            bind = {"source": source["media"], "clock": source["clock"], "binding": self.binding}
            reused = self.journal.has(task_id, bind)
            started = time.monotonic()
            load_before = self.model_initialization_seconds
            historical_before = (self.adopted_ground_seconds +
                                 getattr(self.journal, "historical_seconds_for_forecast", 0.0))
            result = self.journal.call(task_id, bind, lambda s=source: self.produce_source(s))
            write_adopt(self.directory / "sources" / sid / "result.json", result)
            results.append(result)
            print(f"SOURCE_COMPLETE candidate={self.candidate_id} sources={len(results)}/426 "
                  f"frames={len(result['predictions'])} status={result['status']}", flush=True)
            if not reused:
                fresh_sources += 1
                fresh_duration += Fraction(source["physical_end_exact"])
                fresh_seconds += max(0.0, time.monotonic() - started -
                                     (self.model_initialization_seconds - load_before))
                # Exact prior successes cost no new inference. Restore their
                # historical durations only to the cold throughput forecast.
                historical_after = (self.adopted_ground_seconds +
                                    getattr(self.journal, "historical_seconds_for_forecast", 0.0))
                fresh_seconds += historical_after - historical_before
            if fresh_sources >= 5:
                remaining = sum((Fraction(s["physical_end_exact"]) for s in self.sources[len(results):]), Fraction(0))
                estimate = fresh_seconds / float(fresh_duration) * float(remaining) * 1.2
                # A production throughput stop, never an F1/quality screen.
                self.budget.check(estimate)
        return results

    def close(self):
        if self._qwen is not None:
            self._qwen.close()
            self._qwen = None
        if self._specialist is not None:
            # Only objects owned by this command are released; no other process
            # or shared service is stopped.
            self._specialist = None
        import gc
        gc.collect()


def check_baseline_auxiliaries(assets, candidate_id):
    if not candidate_id.startswith("g_"):
        return
    receipts = assets.get("baseline_parameter_receipts", [])
    require(receipts, "Bind actual original TIME/semantic/I3D/UMT inventories before G smoke")
    budget = asset_api.validate_baseline_auxiliaries(assets)
    require(set(budget["components"]) == {"original_time", "semantic_residual", "i3d", "sport_umt"}
            and budget["total_elements"] == 49_686_250,
            "The exact protected40.48 auxiliary tensor union is required before any new G call")


def read_smoke(assets, assets_path, family):
    output = Path(assets["run_root"]) / "smoke" / family / "completion.json"
    result = strict_load(output)
    expected = {"asset_lock": ref(assets_path), "code": assets["source_commit"], "family": family}
    require(result["binding"] == expected and result["status"] == "REAL_ENGINEERING_SMOKE_PASS",
            "Existing smoke belongs to another implementation")
    require(result["source_sha256"] in {s["media"]["sha256"] for s in assets["sources"]},
            "Smoke source is not an actual bound input")
    for identity in result["evidence_refs"]:
        checked(identity)
    total_parameters(result["parameter_receipts"])
    return result


def _smoke_source(engine):
    # Selection depends only on original media metadata/hash, never labels or
    # predicted quality.  One representative small real source keeps it bounded.
    eligible = [s for s in engine.sources if Fraction(s["physical_end_exact"]) >= 8 and s["n_frames"] >= 32]
    require(eligible, "No source can exercise the fixed physical-input smoke")
    return min(eligible, key=lambda s: (abs(Fraction(s["physical_end_exact"]) - 24),
                                      stable_key(s["media"]["sha256"])))


def smoke(assets, assets_path, candidate_id):
    require(candidate_id in asset_api.candidate_registry()["candidates"], "Unknown candidate")
    check_baseline_auxiliaries(assets, candidate_id)
    family = route_family(candidate_id)
    output = Path(assets["run_root"]) / "smoke" / family / "completion.json"
    expected = {"asset_lock": ref(assets_path), "code": assets["source_commit"], "family": family}
    if output.exists():
        return read_smoke(assets, assets_path, family)
    with gpu_lease(assets), Budget(assets, "smoke_" + family, 1800) as budget:
        engine = Engine(assets, assets_path, candidate_id, budget)
        source = _smoke_source(engine)
        engine.qwen()
        if family == "specialist":
            engine.specialist()
        # Separate one-time model loading/inventory from warm throughput.
        initialization_seconds = engine.model_initialization_seconds
        phases, references, phase_seconds = [], [], 0.0
        if family == "phase":
            start = time.monotonic()
            phases, references = engine.phases(source, smoke=True)
            phase_seconds = time.monotonic() - start
        if family == "specialist":
            start = time.monotonic()
            adopted_before = getattr(engine.journal, "historical_seconds_for_forecast", 0.0)
            _, selection, refs = engine.specialist_selection(source)
            references.extend(refs)
            specialist_seconds = (time.monotonic() - start +
                                  getattr(engine.journal, "historical_seconds_for_forecast", 0.0) - adopted_before)
        else:
            specialist_seconds = 0.0
        first = 0
        if family == "grounding" and engine.base[source["video_id"]]:
            first = min(engine.base[source["video_id"]])
        first = min(first, source["n_frames"] - 16)
        # Adjacent real frames exercise grounding, flow and legal native output.
        frames = list(range(first, min(first + 16, source["n_frames"])))
        start = time.monotonic()
        spatial = process_source(decode_native_frames(source, ordinals=frames), frames, {}, source["targetRatioWH"],
            lambda image, metadata: engine.ground(source, image, metadata), engine.spatial_config)
        spatial_seconds = time.monotonic() - start
        require(len(spatial["predictions"]) == len(frames), "Real spatial input/output smoke incomplete")
        evidence = write_adopt(output.with_name("spatial.json"), spatial)
        references.extend(engine.ground_refs + [evidence])
        parameters = engine.parameters(require_complete=True)
        ground_seconds = sum(strict_load(checked(identity))["result"].get("gpu_seconds", 0.0)
                             for identity in {r["path"]: r for r in engine.ground_refs}.values())
        result = {"status": "REAL_ENGINEERING_SMOKE_PASS", "binding": expected, "source_sha256": source["media"]["sha256"],
                  "evidence_refs": references, "parameter_receipts": parameters,
                  "phase_seconds": phase_seconds, "phase_clips": len(phases),
                  "specialist_seconds": specialist_seconds, "source_duration_exact": source["physical_end_exact"],
                  "spatial_seconds": spatial_seconds, "spatial_frames": len(frames),
                  "adopted_ground_calls": engine.adopted_ground_calls + getattr(engine.journal, "adopted_ground_calls", 0),
                  "adopted_historical_gpu_seconds_not_new_charges": engine.adopted_ground_seconds + getattr(engine.journal, "adopted_ground_seconds", 0.0),
                  "source_native_frames": source["n_frames"], "ground_model_seconds": ground_seconds,
                  "model_initialization_seconds": initialization_seconds,
                  "phase_model_seconds_including_reference_qa": sum(p.get("gpu_seconds", 0.0) for p in phases),
                  "phase_actual_groups": sum(len(p["phases"]) for p in phases),
                  "phase_primary_forwards": sum(1 + len(p["phases"]) for p in phases),
                  "phase_reference_forwards": sum(p.get("independent_reference_forwards", 0) for p in phases),
                  "spatial_ground_calls": spatial["diagnostics"]["same_frame_groundings"],
                  "accounting": budget.receipt(), "quality_evaluated": False,
                  "no_f1_no_labels_no_quality_gate": True, "completed_at": utc_now()}
        output.parent.mkdir(parents=True, exist_ok=True)
        atomic_new(output, result)
        engine.close()
        return result


def grounding_plan(sources, baseline, configuration):
    """A metadata-only lower bound; tracking failures can only add calls."""
    interval = Fraction(configuration["ground_interval_seconds"])
    count, maximum, over_cap = 0, 0, []
    for source in sources:
        last, previous, local = None, None, 0
        pts = list(map(Fraction, source["normalized_exact_pts"]))
        for frame in sorted(baseline[source["video_id"]]):
            if last is None or frame != previous + 1 or pts[frame] - last >= interval:
                local += 1
                last = pts[frame]
            previous = frame
        count += local
        maximum = max(maximum, local)
        if local > configuration["max_ground_calls"]:
            over_cap.append({"video_id": source["video_id"], "mandatory_calls": local})
    return {"minimum_ground_calls": count, "maximum_source_minimum_calls": maximum,
            "per_source_call_cap": configuration["max_ground_calls"],
            "sources_impossible_under_fixed_cap": over_cap,
            "not_an_upper_bound_or_completion_guarantee": True}


def forecast(assets):
    sources = enriched_sources(assets)
    duration = sum((Fraction(s["physical_end_exact"]) for s in sources), Fraction(0))
    registry = asset_api.candidate_registry()
    phase_config = phase_options(registry["candidates"]["r_phase_event"])
    plans = [plan_clips(s, clip_seconds=phase_config["clip_seconds"],
                       samples_per_clip=phase_config["samples_per_clip"]) for s in sources]
    clips = sum(map(len, plans))
    primary_forwards = sum(1 + len(clip["cells"]) for source_plans in plans for clip in source_plans)
    baseline = baseline_frames(assets["protected_baselines"])["40.48"]
    selected = sum(len(v) for v in baseline.values())
    root = Path(assets["run_root"])
    output = {"sources": 426, "total_native_frames": sum(s["n_frames"] for s in sources),
              "source_duration_seconds": float(duration), "phase_clips": clips,
              "phase_primary_forwards_from_actual_groups": primary_forwards,
              "phase_primary_forward_upper_bound": clips * 17, "baseline_selected_frames": selected,
              "estimates": {}, "shared_gpu_wait_not_hidden": True}
    # Minimum periodic/gap grounding count under successful transport. Cuts or
    # tracking loss add calls. This is a planning estimate, not an admission gate.
    output["grounding_plan"] = grounding_plan(sources, baseline, registry["shared_spatial_configuration"])
    base_anchors = output["grounding_plan"]["minimum_ground_calls"]
    for family in ("grounding", "phase", "specialist"):
        path = root / "smoke" / family / "completion.json"
        if not path.exists():
            continue
        proof = strict_load(path)
        ground_per_call = proof["ground_model_seconds"] / max(1, proof["spatial_ground_calls"])
        # The smoke fully scans one native source; CPU time also includes its
        # selected-frame foreground/flow work. Sparse selection extrapolation
        # is uncertain and is replaced by actual production accounting.
        # Adopted calls cost no new GPU time, but their original duration must
        # be restored for a cold production forecast, not subtracted as CPU.
        equivalent = proof["spatial_seconds"] + proof.get("adopted_historical_gpu_seconds_not_new_charges", 0.0)
        native_cpu = max(0.0, equivalent - proof["ground_model_seconds"])
        decode_cpu = native_cpu / proof["source_native_frames"] * output["total_native_frames"]
        anchors = base_anchors if family == "grounding" else math.ceil(float(duration) / 8) + 426 * 2
        spatial_seconds = ground_per_call * anchors + decode_cpu
        temporal_seconds = 0.0
        if family == "phase":
            model = proof["phase_model_seconds_including_reference_qa"]
            temporal_seconds = model / max(1, proof["phase_primary_forwards"]) * primary_forwards + \
                max(0.0, proof["phase_seconds"] - model) / proof["source_native_frames"] * output["total_native_frames"]
        elif family == "specialist":
            temporal_seconds = proof["specialist_seconds"] / float(Fraction(proof["source_duration_exact"])) * float(duration)
        seconds = proof["model_initialization_seconds"] + temporal_seconds + spatial_seconds
        output["estimates"][family] = {"linear_smoke_extrapolation_seconds": seconds,
            "planning_with_30pct_margin_seconds": seconds * 1.3,
            "one_time_load_seconds": proof["model_initialization_seconds"],
            "temporal_component_seconds": temporal_seconds, "spatial_component_seconds": spatial_seconds,
            "assumed_periodic_and_gap_groundings": anchors,
            "limits": "One engineering source;phase referenceQA retained as conservative cost and weighted by real group count, not old122 timing;cuts,flow loss,event fragmentation,VFR and sharedGPU vary. All R/M spatial cost is INCLUDED. Not a completion guarantee."}
    return output


def package_only(assets, assets_path, candidate_id):
    """Revalidate/adopt completed source calls and pack without any model runtime."""
    check_baseline_auxiliaries(assets, candidate_id)
    read_smoke(assets, assets_path, route_family(candidate_id))
    class NoModelBudget:
        def check(self, *unused):
            raise ValueError("Packaging may adopt completed calls only; inference is forbidden")
    engine = Engine(assets, assets_path, candidate_id, NoModelBudget())
    results = []
    for source in engine.sources:
        task_id = "source_" + candidate_id + "_" + source["video_id"]
        call_binding = {"source": source["media"], "clock": source["clock"], "binding": engine.binding}
        result = engine.journal.get(task_id, call_binding)
        require(result is not None, "Cannot package unfinished source: " + source["video_id"])
        path = engine.directory / "sources" / source["video_id"] / "result.json"
        write_adopt(path, result)
        results.append(result)
    params = engine.parameters(require_complete=True)
    receipt = build_package(candidate_id=candidate_id, sources=assets["sources"], source_results=results,
        parameter_receipts=params, protected_baselines=assets["protected_baselines"], binding=engine.binding,
        output_dir=engine.directory / "package", history_path=engine.root / "package_history.jsonl")
    delivery = delivery_manifest(receipt, assets)
    return {"status": receipt["status"], "candidate_id": candidate_id, "zip_ref": receipt["zip_ref"],
            "package_receipt": ref(engine.directory / "package" / "package_receipt.json"),
            "delivery_manifest": delivery, "changes": receipt["changes_from_baselines"], "model_calls": 0}


def delivery_manifest(receipt, assets):
    """Small receiver-facing identity, with no raw/model/private input lock."""
    value = {"schema": "AIC_FINAL_DELIVERY_V1", "candidate_id": receipt["candidate_id"],
             "status": receipt["status"], "commit": assets["source_commit"]["commit"],
             "zip_filename": Path(receipt["zip_ref"]["path"]).name,
             "zip_bytes": receipt["zip_ref"]["bytes"], "zip_sha256": receipt["zip_ref"]["sha256"],
             "member_sha256": receipt["member_sha256"], "prediction_sha256": receipt["prediction_sha256"],
             "actual_parameters": receipt["parameter_budget"]["total_elements"],
             "changes_from_baselines": receipt["changes_from_baselines"],
             "source_count": 426, "quality_validated": False, "website_submitted": False}
    return write_adopt(Path(receipt["output_dir"]) / "delivery.json", value)


def run(assets, assets_path, candidate_id):
    candidate = asset_api.candidate_registry()["candidates"][candidate_id]
    family = route_family(candidate_id)
    derived = candidate_id in DERIVED_CANDIDATES
    check_baseline_auxiliaries(assets, candidate_id)
    package_path = Path(assets["run_root"]) / "candidates" / candidate_id / "package" / "package_receipt.json"
    if package_path.exists():
        return package_only(assets, assets_path, candidate_id)
    smoke_path = Path(assets["run_root"]) / "smoke" / family / "completion.json"
    require(smoke_path.exists(), "Run the single targeted real engineering smoke first")
    read_smoke(assets, assets_path, family)
    from contextlib import nullcontext
    with (nullcontext() if derived else gpu_lease(assets)):
        with Budget(assets, "run_" + candidate_id, candidate["stage_seconds_cap"]) as budget:
            engine = Engine(assets, assets_path, candidate_id, budget)
            results = engine.run_sources()
            params = engine.parameters(require_complete=True)
            engine.close()
            receipt = build_package(candidate_id=candidate_id, sources=assets["sources"], source_results=results,
                parameter_receipts=params, protected_baselines=assets["protected_baselines"], binding=engine.binding,
                output_dir=engine.directory / "package", history_path=engine.root / "package_history.jsonl")
            delivery = delivery_manifest(receipt, assets)
            return {"status": receipt["status"], "candidate_id": candidate_id, "zip_ref": receipt["zip_ref"],
                    "package_receipt": ref(engine.directory / "package" / "package_receipt.json"),
                    "delivery_manifest": delivery, "changes": receipt["changes_from_baselines"],
                    "accounting": budget.receipt()}
