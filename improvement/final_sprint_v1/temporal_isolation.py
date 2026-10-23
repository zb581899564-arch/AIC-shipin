"""Registered temporal mechanisms on the exact accepted spatial action domain.

The spatial policy applies uniformly to every source. Missing spatial support is
recorded as UNKNOWN before selection, never replaced by a fabricated crop.
"""
from pathlib import Path

from .contracts import checked, ref, require, strict_load, total_parameters
from .frozen_field import load_cache
from .runner import Engine, phase_options
from .temporal import select_source


POLICY = "FROZEN_EXISTING_SOURCE_FIELD"
DERIVED = {"m_time_prune", "m_time_add", "m_time_generic_prune", "r_time_apex"}


def enabled(candidate):
    return candidate.get("spatial_policy") == POLICY


class TemporalFieldEngine(Engine):
    def __init__(self, assets, assets_path, candidate_id, budget):
        super().__init__(assets, assets_path, candidate_id, budget)
        self.field = load_cache(strict_load(checked(assets["frozen_spatial_field"])), assets)
        self.field["support"] = {sid: set(frames) for sid, frames in self.field["support"].items()}
        if assets.get("phase_call_adoption"):
            require(candidate_id.startswith("r_"), "FP32 adoption is exclusive to R")
            from .phase_call_adoption import PhaseCallJournal, validate_manifest
            self.journal = PhaseCallJournal(self.journal,
                validate_manifest(assets, assets["phase_call_adoption"]))

    def parameters(self, *, require_complete=False):
        found = super().parameters(require_complete=False)
        found += self.assets["baseline_parameter_receipts"]
        # BASE/CLIP/CG files are written by this run's actual model loads.
        if require_complete:
            actual = total_parameters(found)
            require(set(self.candidate["required_model_components"]) == set(actual["components"]),
                    "Temporal isolation lacks actual main/auxiliary inventories")
            require(actual["total_elements"] == self.candidate["parameter_budget"]["expected_total"],
                    "Actual complete temporal+field model union differs")
        return found

    def query(self, source):
        if self.candidate_id == "m_time_generic":
            return self.candidate["configuration"]["query_policy"], []
        return super().query(source)

    def _selection(self, source):
        sid = source["video_id"]
        if self.candidate_id in DERIVED:
            parent, identity = self.parent_source(self.candidate["parent_candidate"], source)
            prior = {p["frame"] for p in parent["predictions"]}
            references = [identity, parent["evidence"]]
            if self.candidate_id == "r_time_apex":
                phases, phase_refs = self.phases(source, cached_only=True)
                result = select_source(source, phases, policy="apex", **phase_options(self.candidate))
                chosen = set(result["frames"]) & self.field["support"][sid]
                require(chosen <= prior, "Apex must retain exact parent event identities")
                return chosen, result, references + phase_refs
            base = set(self.base[sid])
            operator = self.candidate["selection_operator"]
            chosen = prior & base if operator == "intersection" else prior | base
            require(operator in {"intersection", "union"}, "Unknown registered set operation")
            return chosen, {"operator": operator, "parent": identity,
                            "baseline": self.assets["protected_baselines"]["40.48"],
                            "no_new_model_calls": True}, references
        if self.candidate_id == "r_time_event":
            phases, references = self.phases(source)
            result = select_source(source, phases, policy="event", **phase_options(self.candidate))
            return set(result["frames"]), result, references
        frames, result, references = self.specialist_selection(source)
        return set(frames), result, references

    def produce_source(self, source):
        sid = source["video_id"]
        proposed, selection, references = self._selection(source)
        support = self.field["support"][sid]
        excluded = sorted(proposed - support)
        chosen = sorted(proposed & support)
        predictions = [{"frame": frame, "bboxes": self.field["boxes"][sid][frame]}
                       for frame in chosen]
        selection = dict(selection, proposed_frames=len(proposed),
                         unsupported_proposals_unknown=excluded, supported_frames=len(chosen),
                         spatial_action_domain="PREDECLARED_FROZEN_FIELD_SUPPORT")
        field_refs = [self.assets["frozen_spatial_field"], self.field["spec_ref"],
                      self.field["cache_ref"], self.field["metadata_ref"]]
        result = self._finish_source(source, predictions,
            {"uniform_frozen_field": True, "no_new_spatial_inference": True,
             "no_fallback": True, "support_count": len(support),
             "source_check": self.field["source_checks"][sid]},
            [*field_refs, *references], selection)
        for row in result["spatial_provenance"]:
            row["kind"] = "native_spatial_field"
        return result


def package_history(engine):
    return Path(engine.assets.get("global_package_history", engine.root / "package_history.jsonl"))


def strict_accept(engine, receipt):
    """Keep original independent format/native checks separate from packaging."""
    from .frozen_field import export_selection, verify_package
    from .packaging import read_zip_rows
    rows = read_zip_rows(checked(receipt["zip_ref"]))
    selected = {row["video_id"]: [p["frame"] for p in row["predictions"]] for row in rows}
    folder = engine.directory / "independent_strict"
    exported = export_selection(engine.field, selected, folder)
    return verify_package(engine.field, exported, receipt["member_ref"], receipt["zip_ref"],
                          folder / "validation.json")
