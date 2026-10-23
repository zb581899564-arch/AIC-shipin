"""Optional frozen CLIP-only CG-DETR source selector, with native-time decoding.

This is not the previous custom I3D/UMT transfer head or raw CLIP similarity.
The published Lighthouse checkpoint supplies a trained cross-modal moment
decoder and query-conditioned saliency head.  Existing raw Qwen supplies one
source-grounded query through the caller; no official-source training occurs.

No network, package installation, author demo, or model load runs on import.
The caller binds the exact author source, local CLIP weights, and checkpoint.
The author BasePredictor is deliberately not imported: it auto-loads encoder
weights, rejects >75 cells, and computes normalized visual features but then
concatenates the unnormalized features.  Here normalization follows the pinned
training cg_detr_dataset.py/l2_normalize_np_array, and long sources use fixed
overlapping 75-cell windows with exact native-time support.
"""
from __future__ import annotations

from bisect import bisect_left
import base64
from dataclasses import asdict, dataclass
from fractions import Fraction
import hashlib
import importlib
import json
import math
from pathlib import Path
import subprocess
import sys
import time
from typing import Any, Iterable, Mapping, Sequence

from .contracts import checked, inspect_loaded_parameters, ref, require, stable_key
from .observation import exact_clock

AUTHOR_COMMIT = "3e841d3d662c8440afed514908566fed2d5e82a7"
AUTHOR_TREE = "271085c23c2619f0336186304e7eeb5be328e4cd"
AUTHOR_CHECKPOINT_MD5 = "5a5cfd9cbcdda0c6463fae4b052bf473"
AUTHOR_CHECKPOINT_URL = "https://zenodo.org/records/13363606/files/clip_cg_detr_qvhighlight.ckpt?download=1"
OPENAI_CLIP_SHA256 = "40d365715913c9da98579312b702a82c18be219cc2a73407c4526f58eba950af"
OPENAI_CLIP_URL = "https://openaipublic.azureedge.net/clip/models/" + OPENAI_CLIP_SHA256 + "/ViT-B-32.pt"
OPENAI_CLIP_PARAMETERS = 151277313


@dataclass(frozen=True)
class SpecialistConfig:
    cell_seconds: str = "2"
    maximum_window_cells: int = 75
    window_stride_cells: int = 60
    maximum_duration_fraction: str = "1/4"
    foreground_probability: float = 0.5
    image_batch_size: int = 16
    maximum_forward_windows: int = 6000

    def validate(self) -> None:
        require(Fraction(self.cell_seconds) == 2, "Published checkpoint requires the fixed two-second cell profile")
        require(self.maximum_window_cells == 75 and self.window_stride_cells == 60,
                "Only the registered 75/60-cell long-source window recipe is implemented")
        require(Fraction(self.maximum_duration_fraction) == Fraction(1, 4)
                and self.foreground_probability == .5, "No threshold/duration scan in this registered candidate")
        require(type(self.image_batch_size) is int and 1 <= self.image_batch_size <= 64,
                "Bounded image batch size required")
        require(type(self.maximum_forward_windows) is int and self.maximum_forward_windows > 0,
                "Explicit specialist forward budget required")


def plan_cells(source: Mapping[str, Any], config: SpecialistConfig | None = None) -> list[dict[str, Any]]:
    config = config or SpecialistConfig()
    config.validate()
    points, end = exact_clock(source)
    cells = []
    duration = Fraction(config.cell_seconds)
    for number in range(math.ceil(end / duration)):
        start, stop = number * duration, min(end, (number + 1) * duration)
        first, last = bisect_left(points, start), bisect_left(points, stop)
        if first == last:
            continue  # An empty physical-time bin contains no native frame to predict.
        target = (start + stop) / 2
        right = bisect_left(points, target, first, last)
        options = [value for value in (right - 1, right) if first <= value < last]
        center = min(options, key=lambda value: (abs(points[value] - target), value))
        cells.append({"cell_id": len(cells), "time_bin": number, "first": first, "stop": last,
                      "start_exact": str(start), "end_exact": str(stop),
                      "sample_frame": center, "sample_pts_exact": str(points[center])})
    require(cells and cells[0]["first"] == 0 and cells[-1]["stop"] == len(points)
            and all(a["stop"] == b["first"] for a, b in zip(cells, cells[1:])),
            "Specialist cells must cover each actual native ordinal exactly once")
    return cells


def plan_windows(cells: Sequence[Mapping[str, Any]], config: SpecialistConfig | None = None) -> list[dict[str, Any]]:
    config = config or SpecialistConfig()
    config.validate()
    require(cells and [cell["cell_id"] for cell in cells] == list(range(len(cells))), "Contiguous cell identity required")
    windows = []
    first = 0
    while first < len(cells):
        stop = min(len(cells), first + config.maximum_window_cells)
        windows.append({"window_id": f"cg_{len(windows):05d}", "first_cell": first, "stop_cell": stop,
                        "start_exact": cells[first]["start_exact"], "end_exact": cells[stop - 1]["end_exact"]})
        if stop == len(cells):
            break
        first += config.window_stride_cells
    return windows


def _cell_time(cells: Sequence[Mapping[str, Any]], position: Fraction) -> Fraction:
    """Decode a normalized model coordinate via actual cell physical support."""
    position = max(Fraction(0), min(Fraction(len(cells)), position))
    if position == len(cells):
        return Fraction(cells[-1]["end_exact"])
    index = int(position)
    start, end = Fraction(cells[index]["start_exact"]), Fraction(cells[index]["end_exact"])
    return start + (end - start) * (position - index)


def select_native(source: Mapping[str, Any], cells: Sequence[Mapping[str, Any]],
                  windows: Sequence[Mapping[str, Any]], config: SpecialistConfig | None = None) -> dict[str, Any]:
    """Use learned foreground moments, then rank their frames by saliency.

    The fixed 25% physical-duration budget is an upper bound, never a quota.
    Empty learned foreground support remains a legal empty prediction.  Within
    tied cell saliency, prioritize the learned moment's temporal center; this
    makes a partially retained cell contiguous instead of random frame drops.
    """
    config = config or SpecialistConfig()
    config.validate()
    points, physical_end = exact_clock(source)
    require(list(cells) == plan_cells(source, config), "Specialist cell supports differ from this exact native clock")
    expected = plan_windows(cells, config)
    require(len(windows) == len(expected), "Missing specialist window output")
    sums = [0.0] * len(cells)
    counts = [0] * len(cells)
    intervals = []
    for output, planned in zip(windows, expected):
        require(all(output.get(key) == value for key, value in planned.items()), "Wrong specialist window identity")
        scores = output["saliency"]
        spans = output["spans_cxw"]
        foreground = output["foreground_probability"]
        first, stop = planned["first_cell"], planned["stop_cell"]
        require(len(scores) == stop - first and len(spans) == len(foreground) > 0,
                "Incomplete saliency or moment query output")
        require(all(type(value) in (int, float) and math.isfinite(value) for value in scores),
                "Non-finite model saliency")
        for index, score in enumerate(scores, first):
            sums[index] += float(score)
            counts[index] += 1
        for query_index, (span, probability) in enumerate(zip(spans, foreground)):
            require(len(span) == 2 and all(type(value) in (int, float) and math.isfinite(value)
                    and 0 <= value <= 1 for value in span), "Invalid raw sigmoid moment span")
            require(type(probability) in (int, float) and math.isfinite(probability) and 0 <= probability <= 1,
                    "Invalid learned foreground probability")
            if probability < config.foreground_probability:
                continue
            center, width = map(lambda value: Fraction(str(value)), span)
            a = _cell_time(cells[first:stop], (center - width / 2) * (stop - first))
            b = _cell_time(cells[first:stop], (center + width / 2) * (stop - first))
            if a >= b:
                continue
            lo, hi = bisect_left(points, a), bisect_left(points, b)
            if lo == hi:
                continue
            intervals.append({"start_exact": str(a), "end_exact": str(b), "first": lo, "stop": hi,
                              "center_exact": str((a + b) / 2), "probability": probability,
                              "window_id": planned["window_id"], "query_index": query_index})
    require(all(counts), "Some native cells have no real learned saliency output")
    saliency = [value / count for value, count in zip(sums, counts)]
    ranked_cells = sorted(range(len(cells)), key=lambda index: (-saliency[index], index))
    budget = physical_end * Fraction(config.maximum_duration_fraction)
    selected, spent = [], Fraction(0)
    durations = [(points[index + 1] if index + 1 < len(points) else physical_end) - point
                 for index, point in enumerate(points)]
    for index in ranked_cells:
        cell = cells[index]
        covering = [interval for interval in intervals if interval["first"] < cell["stop"] and interval["stop"] > cell["first"]]
        if not covering:
            continue
        eligible = []
        for frame in range(cell["first"], cell["stop"]):
            matching = [interval for interval in covering if interval["first"] <= frame < interval["stop"]]
            if not matching:
                continue
            best = min(matching, key=lambda value: (-value["probability"], value["window_id"], value["query_index"]))
            eligible.append((abs(points[frame] - Fraction(best["center_exact"])), frame))
        for _, frame in sorted(eligible):
            if spent + durations[frame] <= budget:
                selected.append(frame)
                spent += durations[frame]
    selected.sort()
    require(len(selected) == len(set(selected)) and spent <= budget, "Native source budget accounting failed")
    return {"selected_frames": selected, "cell_saliency": saliency,
            "foreground_moments": intervals, "selected_duration_exact": str(spent),
            "duration_budget_exact": str(budget), "empty_is_model_policy": len(selected) == 0,
            "selection_rule": "LEARNED_FOREGROUND_GE_0_5_THEN_NATIVE_DURATION_CAPPED_SALIENCY",
            "whole_source_coverage": len(selected) / len(points),
            "offline_quality_validation": "NOT_RUN", "official_quality": "UNKNOWN"}


def preprocess_clip_image(rgb: Any) -> Any:
    """Native sample -> author-compatible short-side224 center crop, RGB float."""
    import numpy as np
    from PIL import Image
    image = np.asarray(rgb)
    require(image.dtype == np.uint8 and image.ndim == 3 and image.shape[2] == 3,
            "Actual uint8 native RGB required by CLIP")
    height, width = image.shape[:2]
    require(min(height, width) > 0, "Empty CLIP image")
    new_height, new_width = ((int(height * 224 / width), 224) if height >= width
                             else (224, int(width * 224 / height)))
    resized = Image.fromarray(image).resize((new_width, new_height), resample=Image.Resampling.BICUBIC)
    left, top = int((new_width - 224) / 2), int((new_height - 224) / 2)
    pixels = np.asarray(resized.crop((left, top, left + 224, top + 224)), dtype=np.float32) / 255.0
    mean = np.array([.48145466, .4578275, .40821073], dtype=np.float32)
    std = np.array([.26862954, .26130258, .27577711], dtype=np.float32)
    return np.ascontiguousarray(((pixels - mean) / (std + 1e-8)).transpose(2, 0, 1))


def normalize_features(array: Any) -> Any:
    """Match pinned training normalization; do not reuse the demo's unused norm."""
    import numpy as np
    values = np.asarray(array, dtype=np.float32)
    require(values.ndim >= 2 and values.shape[-1] == 512 and np.isfinite(values).all(),
            "Finite 512-dimensional CLIP feature rows required")
    return values / (np.linalg.norm(values, axis=-1, keepdims=True) + 1e-5)


def pack_float32(array: Any) -> dict[str, Any]:
    """Lossless compact JSON of actual float32 bytes; never quantize/truncate."""
    import numpy as np
    values = np.ascontiguousarray(array, dtype="<f4")
    require(values.ndim >= 1 and all(size > 0 for size in values.shape)
            and bool(np.isfinite(values).all()), "Finite nonempty float32 tensor required")
    raw = values.tobytes(order="C")
    return {"schema": "AIC_FINAL_F32_BASE64_V1", "encoding": "base64", "dtype": "<f4",
            "shape": list(values.shape), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
            "data": base64.b64encode(raw).decode("ascii")}


def unpack_float32(packet: Mapping[str, Any], expected_shape: Sequence[int]) -> Any:
    """Verify shape/size/SHA/finite before returning writable float32 values."""
    import numpy as np
    require(isinstance(packet, dict) and set(packet) ==
            {"schema", "encoding", "dtype", "shape", "bytes", "sha256", "data"},
            "Incomplete compact tensor envelope")
    expected = list(expected_shape)
    require(expected and all(type(size) is int and size > 0 for size in expected)
            and packet["shape"] == expected and all(type(size) is int for size in packet["shape"])
            and packet["schema"] == "AIC_FINAL_F32_BASE64_V1"
            and packet["encoding"] == "base64" and packet["dtype"] == "<f4",
            "Compact tensor shape/dtype/schema differs")
    length = math.prod(expected) * 4
    require(type(packet["bytes"]) is int and packet["bytes"] == length
            and isinstance(packet["data"], str) and len(packet["data"]) == 4 * ((length + 2) // 3),
            "Compact tensor byte length differs")
    raw = base64.b64decode(packet["data"], validate=True)
    require(len(raw) == length and base64.b64encode(raw).decode("ascii") == packet["data"]
            and hashlib.sha256(raw).hexdigest() == packet["sha256"],
            "Compact tensor checksum/encoding differs")
    values = np.frombuffer(raw, dtype="<f4").reshape(expected)
    require(bool(np.isfinite(values).all()), "Nonfinite tensor is an execution failure")
    return values.copy()


class _Options(dict):
    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__


def validate_clip_tokens(tokens: Any) -> list[list[int]]:
    """Check the actual OpenAI token contract before computing/caching features.

    Token zero may also encode punctuation before EOT; keep the author's mask
    rule (token != 0), rather than inventing a different tokenizer or padding
    policy.  An overlong query is rejected by tokenize(truncate=False).
    """
    require(isinstance(tokens, list) and len(tokens) == 1 and isinstance(tokens[0], list)
            and len(tokens[0]) == 77, "Actual OpenAI CLIP query tokens must have shape [1,77]")
    row = tokens[0]
    require(all(type(value) is int and 0 <= value < 49408 for value in row)
            and row[0] == 49406 and row.count(49406) == 1 and row.count(49407) == 1,
            "Wrong CLIP vocabulary or start/end token identity")
    end = row.index(49407)
    require(end > 0 and all(value == 0 for value in row[end + 1:]),
            "CLIP query padding after EOT is invalid")
    return tokens


def _clip_runtime_identity(clip_module: Any, torch_module: Any) -> dict[str, Any]:
    """Deterministic implementation/tokenizer identity; no clocks or PID fields."""
    import numpy as np
    import PIL
    require(callable(getattr(clip_module, "load", None))
            and callable(getattr(clip_module, "tokenize", None)),
            "The installed clip module is not the OpenAI CLIP API")
    package = Path(clip_module.__file__).resolve(strict=True).parent
    names = ("__init__.py", "clip.py", "model.py", "simple_tokenizer.py",
             "bpe_simple_vocab_16e6.txt.gz")
    files = {name: ref(package / name) for name in names}
    return {"clip_package_files": files, "torch": str(torch_module.__version__),
            "numpy": np.__version__, "pillow": PIL.__version__,
            "tokenizer_contract": "OPENAI_BPE_49408_SOT49406_EOT49407_CONTEXT77_NO_TRUNCATION"}


def _git(source: Path, *arguments: str) -> str:
    return subprocess.run(["git", "-C", str(source), *arguments], check=True,
                          capture_output=True, text=True).stdout.strip()


def _verify_source(spec: Mapping[str, Any]) -> Path:
    path = Path(spec["path"]).resolve(strict=True)
    require(spec["commit"] == AUTHOR_COMMIT and spec["tree_sha"] == AUTHOR_TREE,
            "Only the researched exact Lighthouse author source is allowed")
    require(_git(path, "rev-parse", "HEAD") == AUTHOR_COMMIT
            and _git(path, "rev-parse", "HEAD^{tree}") == AUTHOR_TREE,
            "Lighthouse checkout differs from the registered commit/tree")
    require(not _git(path, "diff", "--name-only", "HEAD", "--", "lighthouse"),
            "Lighthouse tracked source changed after checkout")
    require(not _git(path, "ls-files", "--others", "--exclude-standard", "--", "lighthouse"),
            "Untracked source may shadow the fixed Lighthouse implementation")
    return path


def _inventory(model: Any, component: str, weights: Mapping[str, Any]) -> dict[str, Any]:
    tensors, seen = [], set()
    for name, value in model.named_parameters():
        if id(value) in seen:
            continue
        seen.add(id(value))
        tensors.append({"name": name, "shape": list(value.shape), "dtype": str(value.dtype), "numel": value.numel()})
    total = sum(value["numel"] for value in tensors)
    require(total > 0, "Actual loaded model has no parameter inventory")
    return {"component": component, "parameters": total, "weights": dict(weights),
            "tensors": tensors, "tensor_inventory_sha256": stable_key(tensors)}


class SpecialistRuntime:
    """Local-only published CG-DETR with one shared CLIP image/text instance."""

    def __init__(self, spec: Mapping[str, Any], device: str = "cuda:0",
                 config: SpecialistConfig | None = None, *, call_cache=None):
        self.spec, self.device = dict(spec), device
        self.config = config or SpecialistConfig()
        self.config.validate()
        self.clip_model = self.model = self.torch = self.clip = None
        self.parameter_inventory: list[dict[str, Any]] = []
        self.forward_windows = 0
        self.image_count = 0
        self.gpu_seconds = 0.0
        self.call_cache = call_cache
        self.query_forwards = 0
        self.runtime_identity: dict[str, Any] = {}

    def _cached(self, kind: str, payload: Mapping[str, Any], compute) -> dict[str, Any]:
        bound = dict(payload, specialist_spec_sha256=stable_key(self.spec),
                     fixed_recipe=asdict(self.config), runtime_identity=self.runtime_identity)
        if self.call_cache is None:
            return compute()
        result = self.call_cache(kind, stable_key(kind, bound), bound, compute)
        require(isinstance(result, dict), "Durable specialist call cache returned an invalid success artifact")
        return result

    def load(self) -> "SpecialistRuntime":
        if self.model is not None:
            return self
        import torch
        import clip
        torch.set_num_threads(2)
        source = _verify_source(self.spec["source"])
        checkpoint_path = checked(self.spec["checkpoint"])
        clip_path = checked(self.spec["clip_checkpoint"])
        require(self.spec["clip_checkpoint"]["sha256"] == OPENAI_CLIP_SHA256,
                "This candidate requires the original OpenAI ViT-B/32 checkpoint; a similar/converted/fine-tuned file is not an identity proof")
        runtime_identity = _clip_runtime_identity(clip, torch)
        validate_clip_tokens(clip.tokenize("A visible action.", context_length=77, truncate=False).tolist())
        md5 = hashlib.md5()
        with checkpoint_path.open("rb") as stream:
            for block in iter(lambda: stream.read(8 << 20), b""):
                md5.update(block)
        require(self.spec.get("published_md5") == AUTHOR_CHECKPOINT_MD5
                and md5.hexdigest() == AUTHOR_CHECKPOINT_MD5,
                "Author-published CG-DETR checkpoint checksum differs")
        require(torch.cuda.is_available() and self.device.startswith("cuda"),
                "Real local GPU required; do not pass CPU mock inference as a model smoke")
        for name, module in list(sys.modules.items()):
            if name == "lighthouse" or name.startswith("lighthouse."):
                location = getattr(module, "__file__", None)
                require(location is not None and Path(location).resolve().is_relative_to(source),
                        "A different Lighthouse source is already imported")
        sys.path.insert(0, str(source))
        # The author artifact contains its options object; both full SHA256
        # and the independent publisher MD5 were verified BEFORE deserialization.
        # This loader never deserializes arbitrary unchecked user paths.
        checkpoint = torch.load(str(checkpoint_path), map_location="cpu", weights_only=False)
        require(isinstance(checkpoint, dict) and {"opt", "model"} <= checkpoint.keys(),
                "Published checkpoint schema differs")
        options = checkpoint["opt"]
        args = _Options(dict(options) if isinstance(options, Mapping) else vars(options))
        require(args["v_feat_dim"] == 514 and args["t_feat_dim"] == 512
                and args.get("a_feat_dim", 0) == 0 and args["clip_length"] == 2
                and args["span_loss_type"] == "l1" and args["max_v_l"] >= 75
                and args["dset_name"] == "qvhighlight", "Wrong checkpoint feature/model identity")
        args.device = self.device
        author = importlib.import_module("lighthouse.common.cg_detr")
        require(Path(author.__file__).resolve() == source / "lighthouse/common/cg_detr.py",
                "Wrong imported author implementation")
        model, _criterion = author.build_model(args)
        model.load_state_dict(checkpoint["model"], strict=True)
        del _criterion, checkpoint
        clip_model, _unused_transform = clip.load(str(clip_path), device=self.device, jit=False)
        require(tuple(clip_model.visual.conv1.weight.shape) == (768, 3, 32, 32)
                and clip_model.visual.input_resolution == 224 and clip_model.context_length == 77
                and tuple(clip_model.visual.positional_embedding.shape) == (50, 768)
                and tuple(clip_model.visual.proj.shape) == (768, 512)
                and tuple(clip_model.token_embedding.weight.shape) == (49408, 512)
                and tuple(clip_model.positional_embedding.shape) == (77, 512)
                and tuple(clip_model.text_projection.shape) == (512, 512)
                and len(clip_model.visual.transformer.resblocks) == 12
                and len(clip_model.transformer.resblocks) == 12,
                "Actual loaded CLIP is not the required shared ViT-B/32")
        model.to(self.device).eval()
        clip_model.eval()
        for loaded in (model, clip_model):
            for parameter in loaded.parameters():
                parameter.requires_grad_(False)
        inventory = [_inventory(clip_model, "CLIP_ViT_B32_SHARED_IMAGE_TEXT", self.spec["clip_checkpoint"]),
                     _inventory(model, "CG_DETR_CLIP_QVHIGHLIGHTS", self.spec["checkpoint"])]
        require(inventory[0]["parameters"] == OPENAI_CLIP_PARAMETERS,
                "Actual OpenAI CLIP main+text tensors differ from the original ViT-B/32 architecture")
        # Publish the loaded state only after every identity/count gate passed.
        self.model, self.clip_model, self.torch, self.clip = model, clip_model, torch, clip
        self.runtime_identity, self.parameter_inventory = runtime_identity, inventory
        return self

    def parameter_receipts(self) -> list[dict[str, Any]]:
        """Canonical actual-loaded parameter inventories for the outer 9B union."""
        self._ready()
        result = []
        for module, component, weights in ((self.clip_model, "clip_vit_b32", self.spec["clip_checkpoint"]),
                                           (self.model, "cg_detr", self.spec["checkpoint"])):
            mapping = {name: {"weight_ref": weights, "tensor_name": name}
                       for name, _parameter in module.named_parameters(remove_duplicate=False)}
            receipt = inspect_loaded_parameters(module, component, [weights], parameter_sources=mapping)
            receipt["loading_proof"] = {"specialist_spec_sha256": stable_key(self.spec),
                "source": self.spec["source"], "strict_state_load": component == "cg_detr",
                "clip_local_checkpoint_author_loader": component == "clip_vit_b32",
                "shared_clip_image_text_instance": True, "runtime_identity": self.runtime_identity}
            result.append(receipt)
        return result

    def _ready(self) -> None:
        require(self.model is not None and self.clip_model is not None, "SpecialistRuntime.load() must succeed first")

    def encode_images(self, images: Sequence[Any]) -> Any:
        self._ready()
        import numpy as np
        require(len(images) > 0, "Image encoder was called without observations")
        payload = {"pixel_sha256": [hashlib.sha256(image.tobytes(order="C")).hexdigest() for image in images],
                   "shapes": [list(image.shape) for image in images],
                   "preprocess": "native_rgb_short224_floor_center_bicubic_clip_norm_l2_plus1e-5"}
        def compute():
            tensor = self.torch.from_numpy(np.stack([preprocess_clip_image(image) for image in images])).to(self.device)
            self.torch.cuda.synchronize(self.device)
            started = time.monotonic()
            try:
                with self.torch.inference_mode():
                    encoded = self.clip_model.encode_image(tensor).float().cpu().numpy()
                self.torch.cuda.synchronize(self.device)
                self.image_count += len(images)
                return {"features": pack_float32(normalize_features(encoded)), "image_count": len(images),
                        "gpu_seconds": time.monotonic() - started, "physical_model_forwards": 1}
            finally:
                self.gpu_seconds += time.monotonic() - started
        result = self._cached("clip_images", payload, compute)
        require(result.get("image_count") == len(images), "Cached CLIP image count differs")
        return unpack_float32(result["features"], (len(images), 512))

    def encode_source(self, source: Mapping[str, Any], observations: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
        import numpy as np
        cells = plan_cells(source, self.config)
        collected, pending, blocks = [], [], []
        def flush() -> None:
            if not pending:
                return
            features = self.encode_images([row["rgb"] for row in pending])
            blocks.append(features)
            for row in pending:
                collected.append({key: row[key] for key in ("cell_id", "frame", "pts", "pixel_sha256")} |
                                 {"source_id": source["video_id"],
                                  "source_sha256": source["media"]["sha256"]})
            pending.clear()
        count = 0
        for observed in observations:
            require(count < len(cells), "Extra CLIP center observation")
            cell = cells[count]
            require(observed["frame"] == cell["sample_frame"] and observed["pts"] == cell["sample_pts_exact"],
                    "CLIP source center/native PTS differs")
            require(observed.get("source_id") == source["video_id"]
                    and tuple(observed["rgb"].shape) == (source["height"], source["width"], 3),
                    "CLIP observation source/native geometry differs")
            raw_sha = hashlib.sha256(observed["rgb"].tobytes(order="C")).hexdigest()
            require(observed.get("pixel_sha256") == raw_sha, "CLIP native image SHA witness differs")
            pending.append(dict(observed, cell_id=cell["cell_id"]))
            count += 1
            if len(pending) == self.config.image_batch_size:
                flush()
        flush()
        require(count == len(cells), "Missing CLIP center observations")
        return {"rows": collected, "features": pack_float32(np.concatenate(blocks, axis=0))}

    def _encode_query(self, query: str) -> tuple[Any, Any, str]:
        require(isinstance(query, str) and query.strip() and len(query) <= 1000, "Source-grounded nonempty query required")
        torch = self.torch
        # No silent CLIP truncation; root's fixed overview request asks <=30 words.
        token_list = validate_clip_tokens(self.clip.tokenize(query, context_length=77, truncate=False).tolist())
        token_sha = stable_key(token_list)
        def compute():
            tokens = torch.tensor(token_list, dtype=torch.long, device=self.device)
            dtype = self.clip_model.visual.conv1.weight.dtype
            self.query_forwards += 1
            torch.cuda.synchronize(self.device)
            started = time.monotonic()
            try:
                with torch.inference_mode():
                    hidden = self.clip_model.token_embedding(tokens).to(dtype)
                    hidden = hidden + self.clip_model.positional_embedding.to(dtype)
                    hidden = self.clip_model.transformer(hidden.permute(1, 0, 2)).permute(1, 0, 2)
                    hidden = self.clip_model.ln_final(hidden).float()
                    hidden = hidden / (torch.linalg.vector_norm(hidden, dim=-1, keepdim=True) + 1e-5)
                    mask = (tokens != 0).float()
                require(bool(torch.isfinite(hidden).all()), "Non-finite actual CLIP query hidden features")
                torch.cuda.synchronize(self.device)
                return {"hidden": pack_float32(hidden.cpu().numpy()), "mask": mask.cpu().tolist(),
                        "token_sha256": token_sha, "gpu_seconds": time.monotonic() - started,
                        "physical_model_forwards": 1}
            finally:
                self.gpu_seconds += time.monotonic() - started
        result = self._cached("clip_query", {"query": query, "token_sha256": token_sha}, compute)
        require(result["token_sha256"] == token_sha, "Cached CLIP query token identity differs")
        hidden = torch.from_numpy(unpack_float32(result["hidden"], (1, 77, 512))).to(self.device)
        mask = torch.tensor(result["mask"], dtype=torch.float32, device=self.device)
        require(hidden.shape == (1, 77, 512) and mask.shape == (1, 77)
                and bool(torch.isfinite(hidden).all()) and bool(((mask == 0) | (mask == 1)).all()),
                "Cached CLIP query features/mask invalid")
        require(result["mask"] == [[float(token != 0) for token in token_list[0]]],
                "Cached CLIP padding mask differs from actual author tokenizer")
        return hidden, mask, token_sha

    def score_source(self, source: Mapping[str, Any], feature_table: Mapping[str, Any], query: str) -> dict[str, Any]:
        self._ready()
        import numpy as np
        torch = self.torch
        cells = plan_cells(source, self.config)
        planned = plan_windows(cells, self.config)
        require(isinstance(feature_table, dict) and set(feature_table) == {"rows", "features"},
                "Complete compact source feature table required")
        feature_rows = feature_table["rows"]
        require(len(feature_rows) == len(cells), "Incomplete CLIP source feature table")
        for row, cell in zip(feature_rows, cells):
            require(row["cell_id"] == cell["cell_id"] and row["frame"] == cell["sample_frame"]
                    and row["pts"] == cell["sample_pts_exact"]
                    and row["source_id"] == source["video_id"]
                    and row["source_sha256"] == source["media"]["sha256"],
                    "Shared feature/cell native source identity differs")
        values = unpack_float32(feature_table["features"], (len(cells), 512))
        norms = np.linalg.norm(values, axis=1)
        require(bool(((norms > .99) & (norms <= 1.00001)).all()),
                "Visual features are not the normalized trained CG-DETR input profile")
        text, text_mask, query_token_sha = self._encode_query(query)
        outputs = []
        for window in planned:
            first, stop = window["first_cell"], window["stop_cell"]
            video = torch.from_numpy(values[first:stop]).to(self.device)
            count = stop - first
            begin = torch.arange(count, device=self.device, dtype=torch.float32) / count
            tef = torch.stack([begin, begin + 1 / count], dim=1)
            inputs = {"src_vid": torch.cat([video, tef], dim=1).unsqueeze(0),
                      "src_vid_mask": torch.ones((1, count), device=self.device),
                      "src_txt": text, "src_txt_mask": text_mask, "src_aud": None, "vid": None, "qid": None}
            input_sha = stable_key(hashlib.sha256(values[first:stop].tobytes(order="C")).hexdigest(),
                                   tef.cpu().tolist(), query_token_sha)
            def compute():
                require(self.forward_windows < self.config.maximum_forward_windows, "Specialist forward budget reached")
                self.forward_windows += 1
                torch.cuda.synchronize(self.device)
                started = time.monotonic()
                try:
                    with torch.inference_mode():
                        prediction = self.model(**inputs)
                    torch.cuda.synchronize(self.device)
                    logits = prediction["pred_logits"]
                    spans = prediction["pred_spans"]
                    saliency = prediction["saliency_scores"]
                    require(logits.ndim == 3 and logits.shape[0] == 1 and logits.shape[2] == 2
                            and spans.shape == logits.shape and saliency.shape == (1, count)
                            and all(bool(torch.isfinite(item).all()) for item in (logits, spans, saliency)),
                            "Actual CG-DETR output contract failed; not a legal empty result")
                    return dict(window, saliency=saliency[0].float().cpu().tolist(),
                                logits=logits[0].float().cpu().tolist(), spans_cxw=spans[0].float().cpu().tolist(),
                                foreground_probability=logits.softmax(-1)[0, :, 0].float().cpu().tolist(),
                                gpu_seconds=time.monotonic() - started, model_input_sha256=input_sha,
                                physical_model_forwards=1)
                finally:
                    self.gpu_seconds += time.monotonic() - started
            output = self._cached("cg_window", {"source_sha256": source["media"]["sha256"],
                "window": window, "model_input_sha256": input_sha}, compute)
            require(output["model_input_sha256"] == input_sha, "Cached CG-DETR input identity differs")
            outputs.append(output)
        selection = select_native(source, cells, outputs, self.config)
        return dict(selection, cells=cells, window_outputs=outputs,
                    query=query, query_tokens_sha256=query_token_sha,
                    feature_table_sha256=stable_key(feature_table),
                    source_sha256=source["media"]["sha256"],
                    # Complete canonical inventories live once in the outer
                    # model_parameters receipts, not 426 times in source JSON.
                    parameter_inventory=[{key: value for key, value in item.items() if key != "tensors"}
                                         for item in self.parameter_inventory],
                    diagnostics={"images_encoded_this_runtime": self.image_count,
                                 "forward_windows_this_runtime": self.forward_windows,
                                 "query_forwards_this_runtime": self.query_forwards,
                                 "gpu_seconds_this_runtime": self.gpu_seconds,
                                 "config": asdict(self.config), "actual_loaded_parameters": sum(
                                     item["parameters"] for item in self.parameter_inventory),
                                 "qwen_and_other_producers_must_be_added_by_outer_inventory": True})

    def process_source(self, source: Mapping[str, Any], observations: Iterable[Mapping[str, Any]], query: str) -> dict[str, Any]:
        """Convenience complete entry; outer immutable journal may cache features."""
        features = self.encode_source(source, observations)
        result = self.score_source(source, features, query)
        result["features"] = features
        return result
