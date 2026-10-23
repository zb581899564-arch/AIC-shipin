"""SHA-bound reuse of completed independent calls, never spatial/source results.

Old packets, claims, failures and charges remain at their original identities.
The wrapper performs no inference and creates no new success or budget charge.
"""
from __future__ import annotations

import math
from pathlib import Path

from .contracts import checked, iter_refs, ref, require, stable_key, strict_load

SCHEMA = "AIC_FINAL_PURE_CALL_ADOPTION_V1"
OLD_COMMIT = "04731cab0d1d805608924e38aa64e7ab5083ab0b"
ALLOWED_OLD_COMMITS = frozenset((OLD_COMMIT, "083d437e2ea3f0b12e83e0d11f982252b7bdc83d"))
PREFIXES = ("ground_", "query_", "clip_features_", "specialist_")
COMMON = ("qwen", "sources", "protected_baselines", "baseline_parameter_receipts")


def compatible_assets(old, new):
    require(old["source_commit"]["commit"] in ALLOWED_OLD_COMMITS, "Unaudited old source implementation")
    require("arithmetic_profile" not in old["qwen"] and "arithmetic_profile" not in new["qwen"],
            "Pure-call adoption requires unchanged default BF16 arithmetic")
    for key in COMMON:
        require(old[key] == new[key], "Pure-call adoption changed actual inputs/model: " + key)
    if old.get("specialist"):
        require(old["specialist"] == new.get("specialist"), "Pure-call adoption changed specialist")


def parent_documents(parent):
    old = strict_load(checked(parent["old_assets"]))
    wrapper = strict_load(checked(parent["wrapper"]))
    require(old["source_commit"]["commit"] in ALLOWED_OLD_COMMITS, "Unaudited old source implementation")
    require(wrapper.get("schema") == "AIC_FINAL_OWNED_WRAPPER_V1"
            and wrapper.get("asset_lock") == parent["old_assets"]
            and wrapper.get("work_terminated") is True
            and wrapper.get("termination_basis") == "owned_wrapper_terminal"
            and wrapper.get("no_external_task_signaled") is True
            and wrapper.get("stopped_owned_process") is False
            and wrapper.get("stop_reason") is None
            and type(wrapper.get("child_exit_code")) is int and wrapper["child_exit_code"] in (0, 1),
            "Exact naturally terminated successful/cost-STOP wrapper required")
    require(isinstance(wrapper.get("owned_wrapper_id"), str) and wrapper["owned_wrapper_id"]
            and isinstance(wrapper.get("task_terminals"), list), "Wrapper ownership/table missing")
    return old, wrapper


def collect_rows(parent, parent_index):
    """Follow only this wrapper's explicit terminals; never search attempts/latest."""
    old, wrapper = parent_documents(parent)
    rows, excluded = [], []
    for item in wrapper["task_terminals"]:
        task_id = item["task_id"]
        if not task_id.startswith(PREFIXES):
            excluded.append(dict(parent=parent_index, task_id=task_id, reason="NOT_AN_INDEPENDENT_CALL"))
            continue
        terminal = strict_load(checked(item["terminal_ref"]))
        claim_ref = terminal["claim_ref"]
        claim_path = checked(claim_ref)
        claim = strict_load(claim_path)
        require(terminal.get("task_id") == claim.get("task_id") == task_id
                and terminal.get("claim_sha256") == claim_ref["sha256"]
                and terminal.get("owned_wrapper_id") == claim.get("owned_wrapper_id") == wrapper["owned_wrapper_id"]
                and terminal.get("work_terminated") is True
                and terminal.get("no_external_task_signaled") is True
                and terminal.get("termination_basis") == "owned_wrapper_terminal",
                "Call terminal/claim has different owned-wrapper identity")
        expected_base = dict(asset_lock=parent["old_assets"], code=old["source_commit"],
                             no_training=True, seed=20261023)
        binding = claim["binding"]
        require(binding == dict(base=expected_base, call=binding.get("call"), journal_schema="AIC_FINAL_CALL_V1")
                and isinstance(binding["call"], dict) and binding["call"]
                and claim["binding_sha256"] == stable_key(binding), "Old call/base binding differs")
        directory = claim_path.parent
        if not all((directory / name).is_file() for name in ("success.json", "returned_result.json")):
            excluded.append(dict(parent=parent_index, task_id=task_id, reason="NO_COMPLETE_DURABLE_SUCCESS"))
            continue
        row = dict(parent=parent_index, task_id=task_id, terminal=item["terminal_ref"], claim=claim_ref,
                   success=ref(directory / "success.json"), returned=ref(directory / "returned_result.json"))
        validate_row(row)
        rows.append(row)
    return rows, excluded


def _semantic(value):
    if isinstance(value, dict):
        return {key: _semantic(item) for key, item in value.items()
                if key not in {"gpu_seconds", "gpu_seconds_this_runtime"}}
    return [_semantic(item) for item in value] if isinstance(value, list) else value


def validate_row(row):
    claim, success, packet = [strict_load(checked(row[key])) for key in ("claim", "success", "returned")]
    binding_sha = stable_key(claim["binding"])
    require(success.get("status") == "SUCCESS" and success.get("task_id") == row["task_id"]
            and success.get("artifacts", {}).get("result") == row["returned"]
            and packet.get("schema") == "AIC_FINAL_CALL_V1"
            and packet.get("status") == "FUNCTION_RETURNED_COMPLETE"
            and packet.get("task_id") == claim.get("task_id") == row["task_id"]
            and packet.get("binding_sha256") == claim.get("binding_sha256") == success.get("binding_sha256") == binding_sha
            and isinstance(packet.get("result"), dict), "Successful raw/claim/packet identity differs")
    for identity in iter_refs(packet["result"]):
        checked(identity)
    seconds = packet.get("accounting", {}).get("wall_seconds")
    gpu_seconds = packet["result"].get("gpu_seconds", 0.0)
    require(all(type(v) in (int, float) and math.isfinite(v) and v >= 0 for v in (seconds, gpu_seconds)),
            "Invalid original successful-call accounting")
    return dict(call_binding=claim["binding"]["call"], returned=row["returned"],
                semantic_sha256=stable_key(_semantic(packet["result"])),
                historical_wall_seconds=float(seconds), ground_gpu_seconds=float(gpu_seconds),
                forecast_seconds=float(seconds if row["task_id"].startswith(("clip_features_", "specialist_source_")) else gpu_seconds),
                forecast_includes_cold_load=row["task_id"].startswith(("clip_features_", "specialist_source_")))


def _nested_components(task_id, entries, values, sources):
    """Match saved producer requests, never infer dependencies from durations."""
    entry, value = entries[task_id], values[task_id]
    binding = entry["call_binding"]
    spec = binding["specialist_spec_sha256"]
    source = sources[stable_key(binding["source"])]
    require(source["clock"] == binding["clock"], "Outer native clock differs")
    dependencies = {}

    def match(kind, predicate):
        matches = []
        for name, candidate in entries.items():
            request = candidate["call_binding"]
            if request.get("kind") != kind or request.get("specialist_spec_sha256") != spec:
                continue
            payload = request["payload"]
            key = stable_key(kind, payload)
            require(request["key"] == key and payload["specialist_spec_sha256"] == spec
                    and name == "specialist_" + kind + "_" + stable_key(key, payload)[:36],
                    "Nested specialist cache request identity differs")
            if predicate(payload, values[name]):
                matches.append(name)
        require(len(matches) == 1, "Missing or ambiguous exact nested " + kind + " success")
        name = matches[0]
        seconds = values[name].get("gpu_seconds")
        require(type(seconds) in (int, float) and math.isfinite(seconds) and seconds >= 0,
                "Nested successful producer lacks finite measured GPU time")
        dependencies[name] = float(seconds)
        return values[name]

    if task_id.startswith("clip_features_"):
        rows = value["features"]["rows"]
        require(rows and len(rows) == len(binding["cells"]), "Incomplete outer feature/native row table")
        for row, cell in zip(rows, binding["cells"]):
            require(row["cell_id"] == cell["cell_id"] and row["frame"] == cell["sample_frame"]
                    and row["pts"] == cell["sample_pts_exact"] and row["source_id"] == source["video_id"]
                    and row["source_sha256"] == source["media"]["sha256"], "Feature/native source row differs")
        first = 0
        while first < len(rows):
            def image_batch(payload, output):
                size = payload["fixed_recipe"]["image_batch_size"]
                require(type(size) is int and 1 <= size <= 64, "Invalid nested image batch recipe")
                chunk = rows[first:first + size]
                return (payload["pixel_sha256"] == [row["pixel_sha256"] for row in chunk]
                        and payload["shapes"] == [[source["height"], source["width"], 3]] * len(chunk)
                        and payload["preprocess"] == "native_rgb_short224_floor_center_bicubic_clip_norm_l2_plus1e-5"
                        and output["image_count"] == len(chunk))
            output = match("clip_images", image_batch)
            first += output["image_count"]
    else:
        features = [name for name, item in entries.items() if item["returned"] == binding["features_ref"]]
        require(len(features) == 1 and features[0].startswith("clip_features_"), "Exact old feature packet dependency missing")
        feature_entry = entries[features[0]]
        require(all(feature_entry["call_binding"][key] == binding[key] for key in
                    ("source", "clock", "cells", "specialist_spec_sha256"))
                and value["feature_table_sha256"] == stable_key(values[features[0]]["features"])
                and value["source_sha256"] == source["media"]["sha256"]
                and value["query"] == binding["query"] and value["cells"] == binding["cells"],
                "Scoring source/query/features dependency differs")
        match("clip_query", lambda payload, output:
              payload["query"] == binding["query"]
              and payload["token_sha256"] == output["token_sha256"] == value["query_tokens_sha256"]
              and payload["query_layout"] == output["query_layout"] == value["query_feature_layout"])
        windows = value["window_outputs"]
        require(windows and len({window["window_id"] for window in windows}) == len(windows),
                "Incomplete or duplicate scoring window table")
        for window in windows:
            match("cg_window", lambda payload, output:
                  payload["source_sha256"] == source["media"]["sha256"]
                  and payload["model_input_sha256"] == window["model_input_sha256"]
                  and payload["window"] == {key: window[key] for key in payload["window"]}
                  and _semantic(output) == _semantic(window))
    return dependencies


def _bind_nested_forecasts(entries, assets):
    outer = [name for name in entries if name.startswith(("clip_features_", "specialist_source_"))]
    values = {name: strict_load(checked(item["returned"]))["result"] for name, item in entries.items()
              if name in outer or item["call_binding"].get("kind") in ("clip_images", "clip_query", "cg_window")}
    sources = {stable_key(source["media"]): source for source in assets["sources"]}
    for name in outer:
        entry = entries[name]
        try:
            components = _nested_components(name, entries, values, sources)
        except (ValueError, KeyError, TypeError, IndexError) as error:
            entry["forecast_blocker"] = "Exact warm dependency proof unavailable: " + str(error)
            continue
        entry.update(forecast_components=components, forecast_seconds=sum(components.values()),
                     forecast_includes_cold_load=False, forecast_basis="EXACT_NESTED_WARM_GPU",
                     forecast_cpu_seconds_bounds=[0.0, entry["historical_wall_seconds"]],
                     forecast_cpu_basis="CPU/load not separately metered; interval, never an assumed zero")


def validate_manifest(assets, identity):
    from .prepare_pure_adoption import audit_sources
    manifest = strict_load(checked(identity))
    require(manifest.get("schema") == SCHEMA
            and manifest.get("new_implementation") == assets["source_commit"]["commit"],
            "Pure-call adoption belongs to another implementation")
    sources = manifest["new_sources"]
    require({name: item["sha256"] for name, item in sources.items()} == assets["source_commit"]["code"]["files"],
            "New implementation source inventory differs")
    require("arithmetic_profile" not in assets["qwen"], "FP32 routes must not use pure-call adoption")
    rows, excluded = [], []
    require(isinstance(manifest.get("parents"), list) and manifest["parents"], "Explicit ordered parents required")
    for index, parent in enumerate(manifest["parents"]):
        old, _ = parent_documents(parent)
        compatible_assets(old, assets)
        require(audit_sources(old, parent["source_dir"], sources) == parent["source_audit"],
                "Producer/source audit changed")
        found, omitted = collect_rows(parent, index)
        rows.extend(found)
        excluded.extend(omitted)
    require(rows == manifest["rows"] and excluded == manifest["excluded"], "Explicit successful-call inventory differs")
    result = {}
    for row in rows:
        entry = validate_row(row)
        previous = result.setdefault(row["task_id"], entry)
        require(previous["call_binding"] == entry["call_binding"]
                and previous["semantic_sha256"] == entry["semantic_sha256"],
                "Duplicate task has conflicting request or semantic output")
    require(result, "No complete independent calls eligible for adoption")
    _bind_nested_forecasts(result, assets)
    return result


class PureCallJournal:
    def __init__(self, delegate, entries):
        self.delegate, self.entries = delegate, entries
        self.historical_seconds_for_forecast = self.adopted_ground_seconds = 0.0
        self.historical_wall_seconds_for_forecast = 0.0
        self.historical_forecast_cold_uncertainty, self.historical_forecast_cold_tasks = False, []
        self.historical_forecast_cold_reasons, self.historical_forecast_cpu_bounds = {}, {}
        self.historical_forecast_cpu_uncertainty = False
        self._forecast_used = set()
        self.adopted_ground_calls, self._used = 0, set()

    def __getattr__(self, name):
        return getattr(self.delegate, name)

    def _entry(self, task_id, call_binding):
        entry = self.entries.get(task_id)
        if entry is not None:
            require(task_id.startswith(PREFIXES) and entry["call_binding"] == call_binding,
                    "Adopted independent request changed pixels/native PTS/prompt/model/config")
            checked(entry["returned"])
        return entry

    def _use(self, task_id, entry):
        if task_id not in self._used:
            self._used.add(task_id)
            # Individual GPU timings begin after load; outer calls include cold
            # loading and nested calls. Flag their wall timing before projection.
            components = entry.get("forecast_components", {task_id: entry["forecast_seconds"]})
            for name, seconds in components.items():
                if name not in self._forecast_used:
                    self._forecast_used.add(name)
                    self.historical_seconds_for_forecast += seconds
            self.historical_wall_seconds_for_forecast += entry["historical_wall_seconds"]
            if "forecast_cpu_seconds_bounds" in entry:
                self.historical_forecast_cpu_uncertainty = True
                self.historical_forecast_cpu_bounds[task_id] = entry["forecast_cpu_seconds_bounds"]
            if entry["forecast_includes_cold_load"]:
                self.historical_forecast_cold_uncertainty = True
                self.historical_forecast_cold_tasks.append(task_id)
                self.historical_forecast_cold_reasons[task_id] = entry.get("forecast_blocker", "Unseparated outer wall time")
            if task_id.startswith("ground_"):
                self.adopted_ground_calls += 1
                self.adopted_ground_seconds += entry["ground_gpu_seconds"]
        return strict_load(checked(entry["returned"]))["result"]

    def call(self, task_id, call_binding, fn):
        entry = self._entry(task_id, call_binding)
        return self._use(task_id, entry) if entry is not None else self.delegate.call(task_id, call_binding, fn)

    def get(self, task_id, call_binding):
        entry = self._entry(task_id, call_binding)
        return self._use(task_id, entry) if entry is not None else self.delegate.get(task_id, call_binding)

    def has(self, task_id, call_binding):
        return self._entry(task_id, call_binding) is not None or self.delegate.has(task_id, call_binding)

    def result_ref(self, task_id, call_binding):
        entry = self._entry(task_id, call_binding)
        return entry["returned"] if entry is not None else self.delegate.result_ref(task_id, call_binding)
