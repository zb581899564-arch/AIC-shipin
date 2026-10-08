"""CPU contracts for untouched selection, native clocks and pilot preregistration.

The integration fixture calls the production selection entry point with actual
metadata-parsing/grid/sampling code and a deterministic CPU clock probe stub.
It performs no remote, media, model, pixel or GPU operation.
"""
from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

import prepare_selection as p

sys.path.insert(0, str(p.HERE / "supervision"))
SPEC = importlib.util.spec_from_file_location("v8_selection_original_validator", p.HERE / "supervision/validate_teacher.py")
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


def identity(split, group):
    return {"sample_id": group + "-sample", "video_id": group + "-video", "youtube_id": group,
            "source_group": group + "-clip", "source_path": "/home/inspur/aic_video_data/videos/" + group + ".mp4",
            "split": split, "retained_segments": "MUST_NOT_SELECT_USING_THIS_VALUE"}


def old_window(split, group):
    value = identity(split, group)
    value.update(source_group=group, window_id="old-" + group, label_status="UNLABELLED")
    return value


def full_clock(path, short=False):
    points = [5.0, 5.25, 5.5] if short else [i / 10 for i in range(901)]
    frames = [{"best_effort_timestamp_time": str(point), "pkt_duration_time": "0.25" if short else "0.1"} for point in points]
    parsed, clock = p.SELECTOR.parse_clock_frames(frames)
    clock.update(source_path=str(path), source_sha256=hashlib.sha256(str(path).encode()).hexdigest(),
        media_bytes=100, ffprobe="CPU_STUB", frame_metadata_decode_performed=True, pixels_exported_or_inspected=False, gpu_used=False)
    return parsed, clock


class Fixture:
    def __init__(self, root):
        self.root = Path(root)
        self.old = self.root / "old"
        self.old.mkdir()
        self.context = self.root / "context.json"
        self.prompt = self.root / "teacher_prompt.txt"
        self.prompt.write_text("fresh v8 prompt\n", encoding="utf-8")
        self.ffprobe = self.root / "ffprobe"
        self.ffprobe.write_bytes(b"CPU_EXISTING_PROGRAM_FIXTURE")
        self.manifests, self.population = {}, {}
        old = {split: [old_window(split, f"old-{split}-{i:03d}") for i in range(p.COUNTS[split])]
               for split in ("train", "dev")}
        receipt = {"schema": "aic_complete_window_selection_receipt_v2", "status": "PASS_CPU_SELECTION_UNLABELLED",
            "counts": p.COUNTS, "counts_requested": p.COUNTS, "seed": "old-seed", "confirm_opened": False,
            "contest_assets_opened": False, "gpu_used": False, "labels_generated": False,
            "old_positive_segments_used": False, "files": {}, "manifests": {}}
        for split in ("train", "dev"):
            selected = self.old / ("selected_" + split + ".jsonl")
            p.SELECTOR.write_jsonl(selected, old[split])
            receipt["files"][selected.name] = p.sha256(selected)
            pinned = p.SELECTOR.PINNED[split]
            receipt["manifests"][split] = {"sha256": pinned[2], "rows": pinned[0], "youtube_groups": pinned[1]}
            self.population[split] = [identity(split, row["source_group"]) for row in old[split]] + [
                identity(split, f"fresh-{split}-{i:03d}") for i in range(140 if split == "train" else 40)]
            path = self.root / (split + "_manifest.jsonl")
            p.SELECTOR.write_jsonl(path, self.population[split])
            self.manifests[split] = path
        p.save_json(self.old / "selection_receipt.json", receipt)
        self.old_receipt_sha = p.sha256(self.old / "selection_receipt.json")
        p.save_json(self.context, {"window_ids": [old["train"][0]["window_id"], old["dev"][0]["window_id"]]})
        self.probed = []
        self.selector = SimpleNamespace(**{name: getattr(p.SELECTOR, name) for name in (
            "PINNED", "rank_sources", "validate_isolation", "write_jsonl", "audit_grid", "make_window")})
        self.selector.load_identities = self.load_identities
        self.selector.probe_source = self.probe_source

    def load_identities(self, path, split):
        # Match the pinned production loader's identity-only projection.
        return [{key: row[key] for key in ("sample_id", "video_id", "youtube_id", "source_group", "source_path")}
                for row in p.rows(path)]

    def probe_source(self, path, ffprobe, timeout):
        self.probed.append(path)
        return full_clock(path, short=path.endswith("fresh-train-000.mp4"))

    def run(self, out="selection", pilot="pilot"):
        with contextlib.redirect_stdout(io.StringIO()):
            return p.run_selection(self.manifests["train"], self.manifests["dev"], self.old, [self.context],
                self.root / out, self.root / pilot, self.prompt, self.ffprobe, selector=self.selector,
                owner_root=self.root, expected_old_receipt_sha=self.old_receipt_sha)


class SelectionContracts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="aic-v8-selection-")
        self.addCleanup(self.temp.cleanup)
        self.f = Fixture(self.temp.name)

    def test_full_entrypoint_preserves_denominators_exclusions_and_validator(self):
        result = self.f.run()
        self.assertEqual(result["status"], "PASS_CPU_SELECTION_UNLABELLED")
        self.assertEqual(result["counts"], {"train": 128, "dev": 32})
        self.assertEqual(result["pilot_counts"], {"train": 16, "dev": 8})
        receipt = p.read_json(self.f.root / "selection/selection_receipt.json")
        self.assertEqual(receipt["exclusion"]["original_window_count"], 160)
        self.assertEqual(receipt["exclusion"]["excluded_source_group_count"], 160)
        selected = {split: p.rows(self.f.root / f"selection/selected_{split}.jsonl") for split in ("train", "dev")}
        self.assertEqual(len(self.f.probed), 160)
        self.assertFalse(any("/old-" in path for path in self.f.probed))
        self.assertEqual(len({row["source_group"] for row in selected["train"] + selected["dev"]}), 160)
        for row in selected["train"] + selected["dev"]:
            VALIDATOR.validate_window(row)
            self.assertFalse(row["old_positive_segments_used"])
            self.assertEqual(row["label_status"], "UNLABELLED")
        VALIDATOR.validate_isolation(selected["train"], selected["dev"])
        for name, digest in receipt["files"].items():
            self.assertEqual(p.sha256(self.f.root / "selection" / name), digest)
        clocks = p.rows(self.f.root / "selection/source_clocks.jsonl")
        self.assertEqual(len(clocks), 160)
        self.assertTrue(all(c["clock_scan_full_source"] and c["natural_grid_audit"]["all_source_pts_covered_once"] for c in clocks))
        self.assertTrue(all(c["gpu_used"] is False and c["pixels_exported_or_inspected"] is False for c in clocks))

    def test_new_seed_controls_source_and_window_identity(self):
        self.assertEqual(p.SELECTOR.SEED, p.SEED)
        self.assertNotEqual(p.SEED, "aic-complete-window-supervision-20261007-v1")
        row = p.SELECTOR.rank_sources([identity("train", "g")], "train")[0]
        pts, clock = full_clock(row["source_path"])
        new = p.SELECTOR.make_window(row, pts, clock)
        with mock.patch.object(p.SELECTOR, "SEED", "aic-complete-window-supervision-20261007-v1"):
            old = p.SELECTOR.make_window(row, pts, clock)
        self.assertNotEqual(new["window_id"], old["window_id"])

    def test_identity_population_order_and_old_labels_do_not_change_selection(self):
        groups, paths, _, _ = p.load_exclusions(self.f.old, [self.f.context], selector=self.f.selector,
            expected_receipt_sha=self.f.old_receipt_sha)
        population = self.f.load_identities(self.f.manifests["train"], "train")
        first, available = p.candidates_for_split(population, "train", groups, paths, 128)
        second, _ = p.candidates_for_split(list(reversed(population)), "train", groups, paths, 128)
        self.assertEqual(first, second)
        self.assertEqual(available, 140)

    def test_old_group_excluded_even_if_another_clip_path(self):
        row = identity("train", "old-train-000")
        row["source_path"] = "/home/inspur/aic_video_data/videos/a-different-clip.mp4"
        fresh = identity("train", "g")
        selected, available = p.candidates_for_split([row, fresh], "train", {"old-train-000"}, set(), 1)
        self.assertEqual(available, 1)
        self.assertEqual(selected[0]["source_group"], "g")

    def test_old_path_excluded_even_if_group_was_inconsistent(self):
        row = identity("train", "g")
        with self.assertRaisesRegex(ValueError, "insufficient untouched"):
            p.candidates_for_split([row], "train", set(), {row["source_path"]}, 1)

    def test_unknown_context_stops_instead_of_silently_ignoring(self):
        bad = self.f.root / "unknown_context.json"
        p.save_json(bad, {"window_ids": ["not-in-old-selection"]})
        with self.assertRaisesRegex(ValueError, "lacks old source-group"):
            p.load_exclusions(self.f.old, [bad], selector=self.f.selector, expected_receipt_sha=self.f.old_receipt_sha)

    def test_missing_context_stops(self):
        with self.assertRaisesRegex(ValueError, "cannot be silently omitted"):
            p.load_exclusions(self.f.old, [], selector=self.f.selector, expected_receipt_sha=self.f.old_receipt_sha)

    def test_mutated_old_selected_bytes_stops(self):
        with (self.f.old / "selected_train.jsonl").open("a", encoding="utf-8") as stream:
            stream.write("\n")
        with self.assertRaisesRegex(ValueError, "original selected bytes"):
            self.f.run()
        self.assertEqual(self.f.probed, [])

    def test_mutated_old_receipt_stops(self):
        with (self.f.old / "selection_receipt.json").open("a", encoding="utf-8") as stream:
            stream.write("\n")
        with self.assertRaisesRegex(ValueError, "receipt byte identity"):
            self.f.run()

    def test_insufficient_untouched_population_fails_before_probe_or_output(self):
        self.f.selector.load_identities = lambda path, split: [identity(split, f"only-{split}-{i}") for i in range(3)]
        with self.assertRaisesRegex(ValueError, "insufficient untouched"):
            self.f.run()
        self.assertEqual(self.f.probed, [])
        self.assertFalse((self.f.root / "selection").exists())

    def test_source_split_leakage_fails_before_probe(self):
        original = self.f.selector.load_identities
        def leaked(path, split):
            population = original(path, split)
            population.append(identity(split, "shared-youtube"))
            return population
        self.f.selector.load_identities = leaked
        with self.assertRaisesRegex(ValueError, "YouTube train/dev leakage"):
            self.f.run()
        self.assertEqual(self.f.probed, [])

    def test_output_and_pilot_never_overwrite(self):
        self.f.run()
        digest = p.sha256(self.f.root / "selection/selection_receipt.json")
        count = len(self.f.probed)
        with self.assertRaisesRegex(ValueError, "never overwrite"):
            self.f.run()
        self.assertEqual(p.sha256(self.f.root / "selection/selection_receipt.json"), digest)
        self.assertEqual(len(self.f.probed), count)
        with self.assertRaisesRegex(ValueError, "never overwrite"):
            p.write_pilot(self.f.root / "selection", self.f.root / "pilot", self.f.prompt, owner_root=self.f.root)

    def test_output_escape_rejected(self):
        with self.assertRaisesRegex(ValueError, "owned v8 directory"):
            p.check_output(self.f.root.parent / "escape", self.f.root)

    def test_pilot_selection_independent_of_order_and_exact24(self):
        self.f.run()
        selected = {split: p.rows(self.f.root / f"selection/selected_{split}.jsonl") for split in ("train", "dev")}
        first = p.pilot_choice(selected)
        second = p.pilot_choice({split: list(reversed(values)) for split, values in selected.items()})
        self.assertEqual(first, second)
        self.assertEqual({split: len(values) for split, values in first.items()}, p.PILOT_COUNTS)
        manifest = p.read_json(self.f.root / "pilot/manifest.json")
        self.assertEqual(manifest["window_ids"], [r["window_id"] for r in first["train"] + first["dev"]])
        self.assertEqual(manifest["teacher_prompt_sha256"], p.sha256(self.f.prompt))
        self.assertTrue(manifest["old_12_are_regression_only_not_pilot"])
        receipt = p.read_json(self.f.root / "pilot/selection_receipt.json")
        self.assertEqual(receipt["counts"], p.PILOT_COUNTS)
        self.assertEqual(receipt["parent_counts"], p.COUNTS)
        for name, digest in receipt["files"].items():
            self.assertEqual(p.sha256(self.f.root / "pilot" / name), digest)

    def test_parent_byte_mutation_rejected_before_pilot(self):
        self.f.run()
        with (self.f.root / "selection/selected_dev.jsonl").open("a", encoding="utf-8") as stream:
            stream.write("\n")
        with self.assertRaisesRegex(ValueError, "parent selection bytes"):
            p.write_pilot(self.f.root / "selection", self.f.root / "newpilot", self.f.prompt, owner_root=self.f.root)
        self.assertFalse((self.f.root / "newpilot").exists())

    def test_short_source_is_not_padded_and_is_validator_compatible(self):
        source = p.SELECTOR.rank_sources([identity("train", "short")], "train")[0]
        pts, clock = full_clock(source["source_path"], short=True)
        window = p.SELECTOR.make_window(source, pts, clock)
        self.assertEqual(window["planned_source_frame_ordinals"], [0, 1, 2])
        self.assertEqual(window["planned_actual_pts_sec"], pts)
        self.assertEqual(window["window_duration_sec"], 0.75)
        VALIDATOR.validate_window(window)

    def test_duration_only_tail_is_evidence_not_empty_label(self):
        frames = [{"best_effort_timestamp_time": "0", "pkt_duration_time": "1"},
                  {"best_effort_timestamp_time": "29", "pkt_duration_time": "3"}]
        pts, clock = p.SELECTOR.parse_clock_frames(frames)
        audit = p.SELECTOR.audit_grid(pts, clock)
        self.assertEqual(audit["natural_window_count"], 2)
        self.assertEqual(audit["eligible_window_ordinals"], [0])
        self.assertEqual(audit["non_sampleable_time_cells"][0]["empty_semantic_label"], False)
        self.assertTrue(audit["all_source_pts_covered_once"])

    def test_missing_or_nonincreasing_pts_rejected(self):
        for frames in ([{"best_effort_timestamp_time": "0"}, {"pkt_duration_time": "1"}],
                       [{"best_effort_timestamp_time": "1"}, {"best_effort_timestamp_time": "1", "pkt_duration_time": "1"}]):
            with self.assertRaises(ValueError):
                p.SELECTOR.parse_clock_frames(frames)

    def test_native_sampling_preserves_integer_floor_endpoints(self):
        actual = p.SELECTOR.spaced_indices(41, 1039)
        self.assertEqual(actual, [41 + i * 997 // 63 for i in range(64)])
        self.assertEqual(actual[0], 41)
        self.assertEqual(actual[-1], 1038)

    def test_clock_failure_writes_stop_without_skipping_or_pilot(self):
        def fail(path, ffprobe, timeout):
            self.f.probed.append(path)
            if len(self.f.probed) == 2:
                raise ValueError("REAL_CLOCK_FAILURE_FIXTURE")
            return full_clock(path)
        self.f.selector.probe_source = fail
        with self.assertRaisesRegex(ValueError, "REAL_CLOCK_FAILURE_FIXTURE"):
            self.f.run()
        receipt = p.read_json(self.f.root / "selection/selection_receipt.json")
        self.assertEqual(receipt["status"], "STOP_CPU_SELECTION_CLOCK_OR_IDENTITY")
        self.assertEqual(receipt["completed_unlabelled_counts"], {"train": 1, "dev": 0})
        self.assertEqual(len(self.f.probed), 2)
        self.assertFalse((self.f.root / "pilot").exists())
        self.assertFalse((self.f.root / "selection/selected_train.jsonl").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
