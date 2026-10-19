"""Source-streamed adoption of already accepted patches, prefixes and clocks.

Constructing the store and reading human summary membership are CPU-only and
do not import torch.  Tensor reconstruction is explicit in case(), uses only
retained local patches, and checks the original four-tensor byte signatures.
"""
from fractions import Fraction
import gzip
import importlib.util
import os
from pathlib import Path
import sys

from .assets import _clock, _known_key, check_ref, load_assets, read_json, require, same_ref


def _bound_module(name, reference, workspace):
    path = check_ref(reference, workspace)
    if name in sys.modules:
        module = sys.modules[name]
        require(getattr(module, "__file__", None) is not None
                and Path(module.__file__).resolve() == path, "An unbound module already owns " + name)
        return module
    before = os.environ.get("CUDA_VISIBLE_DEVICES")
    present = "CUDA_VISIBLE_DEVICES" in os.environ
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    try:
        spec.loader.exec_module(module)
        require(os.environ.get("CUDA_VISIBLE_DEVICES") == before
                and ("CUDA_VISIBLE_DEVICES" in os.environ) == present,
                "Retained helper mutated GPU visibility")
    except BaseException:
        sys.modules.pop(name, None)
        if present:
            os.environ["CUDA_VISIBLE_DEVICES"] = before
        else:
            os.environ.pop("CUDA_VISIBLE_DEVICES", None)
        raise
    return module


class NativeInputStore:
    """One source of retained pixel tensors in memory, never an all-source cache."""

    def __init__(self, manifest, scope="train"):
        self.manifest = load_assets(manifest) if isinstance(manifest, (str, Path)) else manifest
        require(scope in {"train", "check", "production"} and scope in self.manifest["scopes"],
                "Explicit available input scope required")
        self.scope = scope
        self.workspace = Path(self.manifest["workspace_root"]).resolve(strict=True)
        data = self.manifest["scopes"][scope]
        self.sources = {s["id"]: s for s in data["sources"]}
        require(self.sources and len(self.sources) == len(data["sources"]), "Unique source catalog required")
        self.source_ids = tuple(self.sources)
        self.requests, self.request_refs, self.clocks = {}, {}, {}
        self.by_source = {sid: [] for sid in self.source_ids}
        for sid, source in self.sources.items():
            require(source["group"] == scope, "Source belongs to a different scope")
            clock = read_json(check_ref(source["clock_ref"], self.workspace))
            _clock(clock)
            require(clock["source_sha256"] == source["source_sha256"], "Input clock/source bytes differ")
            self.clocks[sid] = clock
        for reference in data["requests"]:
            request = read_json(check_ref(reference, self.workspace))
            uid, sid = request["uid"], request["sid"]
            require(isinstance(uid, str) and uid and uid not in self.requests and sid in self.sources,
                    "Duplicate/foreign accepted input")
            require(request["source_sha256"] == self.sources[sid]["source_sha256"]
                    and same_ref(request["source_clock_ref"], self.sources[sid]["clock_ref"])
                    and request.get("first_new_pixel_text_native_QA") is True,
                    "Request must adopt the actual accepted source clock")
            self.requests[uid], self.request_refs[uid] = request, reference
            self.by_source[sid].append(uid)
        self.case_ids = tuple(self.requests)
        for sid, ids in self.by_source.items():
            ranges = []
            for uid in ids:
                plan = self.requests[uid]["plan"]
                require(all(type(plan[k]) in (str, int) for k in ("window_start_exact", "window_end_exact")),
                        "Exact registered window endpoints required")
                start, end = Fraction(plan["window_start_exact"]), Fraction(plan["window_end_exact"])
                require(0 <= start < end <= Fraction(self.clocks[sid]["physical_end_exact"]),
                        "Registered window outside native source")
                ranges.append((start, end))
            ranges.sort()
            require(ranges and ranges[0][0] == 0
                    and ranges[-1][1] == Fraction(self.clocks[sid]["physical_end_exact"])
                    and all(a[1] == b[0] for a, b in zip(ranges, ranges[1:])),
                    "Complete source window coverage required; missing windows cannot be empty")
        self._cached_sid, self._pixels = None, None
        self._contract, self._dictionary = None, None

    def source_supervision(self, sid):
        """Return full-native sets, with known masks in [reviewer][native] order.

        Dense original summary membership declares both selection and omission
        from that author's summary.  Omission is not a universal no-highlight
        annotation.  An explicit known mask is preserved, including False; the
        preference utility is responsible for rejecting unknown supervision.
        """
        require(self.scope in {"train", "check"} and sid in self.sources,
                "Official production sources have no human supervision interface")
        import numpy as np
        source = self.sources[sid]
        clock = self.clocks[sid]
        label_clock = read_json(check_ref(source["supervision_clock_ref"], self.workspace))
        require(_clock(label_clock) == _clock(clock)
                and label_clock["source_sha256"] == source["source_sha256"],
                "Human source/reference clock differs from input clock")
        contract = source["supervision_contract"]
        require(contract.get("dense_all_rater_source_summary_membership") is True
                and contract.get("unselected_is_not_exhaustive_no_highlight_label") is True
                and contract.get("baseline_kind") == "HISTORICALLY_EXPOSED_EXTERNAL_40_47_PROXY",
                "Original all-rater summary and exposed40.47 proxy contract required")
        with np.load(check_ref(source["supervision_ref"], self.workspace), allow_pickle=False) as data:
            baseline, labels = data[contract["baseline_key"]], data[contract["labels_key"]]
            size = len(clock["normalized_exact_pts"])
            require(baseline.dtype == labels.dtype == np.bool_ and baseline.shape == (size,)
                    and labels.ndim == 2 and labels.shape[0] == size and labels.shape[1] > 0,
                    "Full-source Boolean baseline[native] and labels[native,reviewer] required")
            key = contract.get("known_key")
            require(_known_key(data.files) == key, "Actual known-mask column differs from explicit source adoption")
            if key is None:
                known = np.ones(labels.shape, dtype=np.bool_)
            else:
                require(isinstance(key, str) and key in data.files, "Explicit known-mask column is absent")
                known = data[key]
                require(known.dtype == np.bool_ and known.shape == labels.shape,
                        "Known mask must match original native-by-reviewer Boolean matrix")
            return dict(clock=clock, baseline=set(np.flatnonzero(baseline).tolist()),
                raters=[set(np.flatnonzero(labels[:, col]).tolist()) for col in range(labels.shape[1])],
                known_masks=[known[:, col].tolist() for col in range(labels.shape[1])],
                source_sha256=source["source_sha256"], group=self.scope)

    def _helpers(self):
        if self._contract is None:
            reference = self.manifest["input_code"]["summary_contract"]
            self._contract = _bound_module("aic_preference_summary_contract_" + reference["sha256"][:16],
                                            reference, self.workspace)
        return self._contract

    def _dictionary_helper(self):
        if self._dictionary is None:
            code = self.manifest["input_code"]
            # The old lossless dictionary imports codec by this exact name.
            # An unrelated cached codec must never silently satisfy that import.
            _bound_module("codec", code["codec"], self.workspace)
            self._dictionary = _bound_module("aic_preference_dictionary_" + code["dictionary"]["sha256"][:16],
                                               code["dictionary"], self.workspace)
        return self._dictionary

    def _source_pixels(self, sid):
        import torch
        if self._cached_sid == sid:
            return self._pixels
        self._cached_sid, self._pixels = None, None
        source, contract = self.sources[sid], self._helpers()
        frames, grids, ordinals = [], [], []
        for record in source["patches"]:
            path = check_ref(record, self.workspace)
            with path.open("rb") as stream:
                compressed = stream.read(2) == b"\x1f\x8b"
            if compressed:
                with gzip.open(path, "rb") as stream:
                    payload = self._dictionary_helper().unpack(torch.load(stream, map_location="cpu", weights_only=True))
            else:
                payload = torch.load(path, map_location="cpu", weights_only=True)
            pixels, grid = payload["pixel_values"], payload["image_grid_thw"]
            require(pixels.device.type == grid.device.type == "cpu" and pixels.dtype == torch.float32
                    and grid.dtype == torch.int64 and pixels.ndim == 2 and pixels.shape[1] == 1536
                    and grid.ndim == 2 and grid.shape[1] == 3 and bool(torch.isfinite(pixels).all()),
                    "Finite retained CPU float32 image patches and int64 grids required")
            expected_grid = record["grid"] if source["patch_format"] == "CHUNKS" else record["grids"]
            require(grid.tolist() == expected_grid and len(grid) == len(record["samples"]),
                    "Retained patch geometry/source order changed")
            require(source["patch_format"] != "CHUNKS" or "sample_ordinals" in payload,
                    "Original train patch payload lost its native ordinal mapping")
            if "sample_ordinals" in payload:
                require(payload["sample_ordinals"] == record["samples"], "Payload native sample order changed")
            if "pixel_shape" in record:
                require(list(pixels.shape) == record["pixel_shape"], "Retained pixel shape changed")
            if "pixel_sha256" in record:
                require(contract.signature({"pixels": pixels})["pixels"]["sha256"] == record["pixel_sha256"],
                        "Actual retained pixel tensor SHA changed")
            offset = 0
            for temporal, height, width in grid.tolist():
                require(temporal == 1 and height > 0 and width > 0, "Individual real image observations required")
                frames.append(pixels[offset:offset+height*width])
                grids.append([height, width]); offset += height*width
            require(offset == len(pixels), "Incomplete retained patch accounting")
            ordinals.extend(record["samples"])
        require(frames and len(frames) == len(ordinals) == source["cells"]
                and all(value == grids[0] for value in grids)
                and all(type(i) is int and 0 <= i < len(self.clocks[sid]["normalized_exact_pts"]) for i in ordinals)
                and ordinals == sorted(set(ordinals)), "Complete single-grid source observations/native order required")
        self._cached_sid, self._pixels = sid, (frames, grids[0], ordinals)
        return self._pixels

    def case(self, uid):
        """Return (bound request, exactly four checked CPU tensors, full clock)."""
        require(uid in self.requests, "Unknown accepted window")
        import torch
        request = read_json(check_ref(self.request_refs[uid], self.workspace))
        require(request == self.requests[uid], "Accepted request changed since the store was opened")
        sid, plan = request["sid"], request["plan"]
        clock = self.clocks[sid]
        check_ref(self.sources[sid]["clock_ref"], self.workspace)
        frames, grid, ordinals = self._source_pixels(sid)
        require(grid == request["grid_hw"], "Accepted request grid differs from retained source pixels")
        contract = self._helpers()
        pixels, actual_plan = contract.build_pixels(frames, grid, ordinals, clock["normalized_exact_pts"],
            plan["window_start_exact"], plan["window_end_exact"],
            dict(source_id=sid, source_sha256=request["source_sha256"]))
        require(actual_plan == plan, "Reconstructed two-view native input plan differs")
        prefix = torch.load(check_ref(request["prefix_ref"], self.workspace), map_location="cpu", weights_only=True)
        require(isinstance(prefix, dict) and set(prefix) == {"input_ids", "attention_mask"}
                and all(value.device.type == "cpu" and value.dtype == torch.int64 and value.ndim == 2
                        and value.shape[0] == 1 for value in prefix.values())
                and prefix["input_ids"].shape == prefix["attention_mask"].shape
                and prefix["input_ids"].shape[1] == request["text"]["prefix_tokens"],
                "Exact retained single-case CPU prefix required")
        values = dict(**pixels, **prefix)
        require(contract.signature(values) == request["input_signature"], "Actual four-tensor input byte signature differs")
        return request, values, clock

    def close(self):
        self._cached_sid, self._pixels = None, None

