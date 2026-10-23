"""Shared, local-only Qwen runtime for physical phases and subject grounding.

The same BASE tensor objects serve both roles.  Optional original TIME is
counted even when disabled for a BASE call.  No historical launcher, global
prefix, language-layer surgery, training, or external inference is involved.
Actual CUDA behavior still requires the Linux engineering smoke.
"""
from __future__ import annotations

from contextlib import contextmanager, nullcontext
from fractions import Fraction
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import re
import time

PHASES = ("ordinary", "setup", "apex", "resolution")
ORIGINAL_BASE_PARAMETERS = 8_767_123_696
ORIGINAL_BASE_CANONICAL_SHA256 = "74bcce81cfcb0893cf4b4c25ae36ec908d6ea669583aedd0f3940063080b8b59"
TRANSITIONS = {
    # A physically isolated clip may begin inside an event. Do not force its
    # observed resolution to become a new apex merely because context starts.
    "start": PHASES,
    "ordinary": ("ordinary", "setup", "apex"),
    "setup": ("ordinary", "setup", "apex"),
    "apex": ("ordinary", "apex", "resolution"),
    "resolution": ("ordinary", "resolution"),
}


def _require(value, message):
    if not value:
        raise ValueError(message)


def _digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def _verify_files(files):
    from .contracts import checked
    _require(isinstance(files, list) and files, "Explicit complete model-file inventory required")
    for item in files:
        checked(item)


def _original_base_identity(model, torch):
    """Verify the inherited BASE identity with its exact canonical algorithm.

    This pure historical helper imports no launcher and changes no protocol.
    Hashing occurs once, before an optional adapter is attached.  Later image,
    phase and parameter-receipt calls reuse this completed loading proof.
    """
    from improvement.native_preference_v1 import runtime as historical_runtime
    from .contracts import ref
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    started = time.monotonic()
    identity = historical_runtime.canonical_frozen_hash(model, torch)
    _require(identity.get("sha256") == ORIGINAL_BASE_CANONICAL_SHA256
             and identity.get("parameters") == ORIGINAL_BASE_PARAMETERS,
             "Loaded BASE differs from the protected inherited canonical frozen model")
    return dict(identity, expected_sha256=ORIGINAL_BASE_CANONICAL_SHA256,
                verified_before_adapter=True, hash_calls_this_load=1,
                wall_seconds=time.monotonic() - started,
                hash_function="improvement.native_preference_v1.runtime.canonical_frozen_hash",
                hash_function_file=ref(historical_runtime.__file__))


def _commit_phase_cache(cache, selected_indices, *, prefix_length, suffix_length):
    """Keep one semantic branch and remove its right-padding cache slots.

    The following group consequently has a dense, unpadded logical prefix;
    physical cache positions and logical text positions cannot drift apart.
    """
    _require(all(hasattr(cache, name) for name in ("batch_select_indices", "crop", "get_seq_length")),
             "Pinned DynamicCache selection/cropping API unavailable")
    target = prefix_length + suffix_length
    _require(suffix_length > 0 and int(cache.get_seq_length()) >= target,
             "Semantic branch cache is shorter than its complete native prefix")
    cache.batch_select_indices(selected_indices)
    cache.crop(target)
    _require(int(cache.get_seq_length()) == target, "Committed semantic cache retained padding or lost native tokens")
    return cache


def _parameter_inventory(model):
    """Count actual loaded unique tensors, including vision and any adapter.

    Shared Parameter aliases are counted once.  Distinct Parameter views of
    the same contiguous storage are rejected instead of silently undercounted.
    This loader does not enable quantization, so numel is the logical count.
    """
    identities = {}
    storage = {}
    rows = []
    for name, value in model.named_parameters(remove_duplicate=False):
        if id(value) in identities:
            rows[identities[id(value)]]["aliases"].append(name)
            continue
        pointer = (str(value.device), value.untyped_storage().data_ptr())
        if pointer in storage:
            raise ValueError("Distinct Parameter objects share storage; explicit union accounting required")
        storage[pointer] = name
        identities[id(value)] = len(rows)
        rows.append(dict(name=name, aliases=[], shape=list(value.shape), numel=value.numel(),
                         dtype=str(value.dtype), trainable=bool(value.requires_grad)))
    return dict(parameter_count=sum(row["numel"] for row in rows),
                tensor_count=len(rows), inventory_sha256=_digest(rows), tensors=rows,
                counted_from_actual_loaded_tensors=True, quantization=False)


def _tensor_signature(values):
    output = {}
    for key, tensor in values.items():
        if hasattr(tensor, "detach"):
            value = tensor.detach().cpu().contiguous()
            # Inputs are float32/int64; byte view is also safe for other dtypes.
            data = value.view(__import__("torch").uint8).numpy().tobytes()
            output[key] = dict(shape=list(value.shape), dtype=str(value.dtype),
                               sha256=hashlib.sha256(data).hexdigest())
    return dict(tensors=output, sha256=_digest(output))


def _validate_local_observation(observation):
    """Bind the actual RGB buffer to the local native-frame request.

    This check runs before tokenization. A caller cannot supply one clip's
    pixels alongside another clip's timestamps and then claim physical local
    isolation merely because the resulting token tensor has a hash.
    """
    import numpy as np
    clip, rgb = observation["clip"], observation["rgb"]
    indices = clip["sample_ordinals"]
    points = [Fraction(value) for value in clip["sample_pts_exact"]]
    start, stop = Fraction(clip["start_exact"]), Fraction(clip["end_exact"])
    _require(0 <= start < stop and stop - start <= 8,
             "Physical local input interval must be positive and at most8seconds")
    _require(type(observation["source_n_frames"]) is int and observation["source_n_frames"] > 0
             and 0 <= clip["first"] < clip["stop"] <= observation["source_n_frames"],
             "Physical local frame range differs from source bounds")
    _require(1 <= len(indices) <= 32 and len(indices) == len(points)
             and all(type(value) is int and clip["first"] <= value < clip["stop"] for value in indices)
             and all(a < b for a, b in zip(indices, indices[1:]))
             and all(start <= value < stop for value in points)
             and all(a < b for a, b in zip(points, points[1:])),
             "Local observations are not unique chronological native samples in their physical interval")
    groups = [indices[offset:offset + 2] for offset in range(0, len(indices), 2)]
    _require([cell["observed_ordinals"] for cell in clip["cells"]] == groups,
             "Semantic action cells differ from the actual two-frame visual groups")
    _require(isinstance(rgb, np.ndarray) and rgb.dtype == np.uint8 and rgb.ndim == 4
             and rgb.shape[0] == len(indices) and rgb.shape[-1] == 3
             and min(rgb.shape[1:3]) > 0,
             "Actual local uint8 RGB/native sample inventory differs")
    actual = [hashlib.sha256(frame.tobytes(order="C")).hexdigest() for frame in rgb]
    _require(actual == observation["pixel_sha256"], "Actual local RGB bytes differ from decoded pixel evidence")
    _require(isinstance(observation["source_id"], str) and observation["source_id"]
             and re.fullmatch(r"[0-9a-f]{64}", observation["source_sha256"]) is not None,
             "Exact physical source identity is missing")
    return dict(source_id=observation["source_id"], source_sha256=observation["source_sha256"],
                interval_exact=[str(start), str(stop)], native_ordinals=list(indices),
                sample_pts_exact=[str(value) for value in points], pixel_sha256=actual,
                buffer_shape=list(rgb.shape), only_registered_local_pixels=True)


@contextmanager
def _native_timestamps(processor, observation):
    """Instance-local native PTS encoding; validate actual video timestamps."""
    clip = observation["clip"]
    indices = list(clip["sample_ordinals"])
    start = Fraction(clip["start_exact"])
    points = [Fraction(value) - start for value in clip["sample_pts_exact"]]
    padded = points + ([points[-1]] if len(points) % 2 else [])
    group_times = [float((padded[i] + padded[i + 1]) / 2) for i in range(0, len(padded), 2)]
    processor_ids = indices + indices if len(indices) == 1 else indices
    existed = "_calculate_timestamps" in getattr(processor, "__dict__", {})
    original = processor._calculate_timestamps
    calls = []

    def calculate(actual_indices, fps, merge_size=2):
        _require(list(actual_indices) == processor_ids and merge_size == 2,
                 "Processor resampled or changed physical local observations")
        calls.append(list(actual_indices))
        return list(group_times)

    processor._calculate_timestamps = calculate
    evidence = dict(native_group_pts=group_times, unique_native_ordinals=indices,
                    processor_input_ordinals=processor_ids, calls=calls,
                    global_prefix_present=False)
    try:
        yield evidence
        _require(len(calls) == 1, "Exactly one actual local timestamp encoding required")
    finally:
        if existed:
            processor._calculate_timestamps = original
        else:
            delattr(processor, "_calculate_timestamps")


def phase_prompt(observation):
    count = len(observation["clip"]["cells"])
    return (
        "Inspect this short continuous video in chronological order. Each consecutive pair "
        f"of sampled frames is one temporal group. There are exactly {count} groups. "
        "Describe the action phase of EVERY group using one word per line, in order. "
        "ordinary = idle, repetitive, transitional or unremarkable material; "
        "setup = the necessary lead-in to a meaningful action, demonstration, revelation, "
        "emotional reaction or outcome; apex = the decisive action, skill, surprise, useful "
        "revelation or emotional payoff itself; resolution = its immediate visible outcome. "
        "An ordinary clip may have only ordinary groups. Do not invent an event, enforce "
        "a quota, or use camera motion alone as evidence. A new event begins after ordinary. "
        "The first group may already be a resolution if the event began before this clip. "
        "Output only the words ordinary, setup, apex or resolution, one per group."
    )


class QwenRuntime:
    def __init__(self, model_spec, *, device="cuda:0"):
        self.spec = dict(model_spec)
        self.device = device
        self.model = self.processor = self.torch = None
        self.inventory = None
        self.original_base_identity = None
        self.counts = dict(image_generations=0, video_prefills=0, phase_branch_batches=0,
                           phase_alternatives=0, generated_tokens=0, reference_forwards=0,
                           physical_model_forwards=0)

    def load(self):
        if self.model is not None:
            return self.identity()
        _require(self.device == "cuda:0" and os.environ.get("CUDA_VISIBLE_DEVICES", "") not in ("", "-1"),
                 "The Linux wrapper must explicitly choose an authorized CUDA device")
        _verify_files(self.spec["files"])
        import torch
        from transformers import AutoProcessor, Qwen3VLForConditionalGeneration
        _require(torch.cuda.is_available(), "Real local CUDA is required")
        versions = {name: importlib.metadata.version(name) for name in ("torch", "transformers", "safetensors")}
        _require(versions["transformers"] == "4.57.1", "Pinned transformers 4.57.1 required")
        model_dir = Path(self.spec["model_dir"]).resolve(strict=True)
        _require(model_dir.is_dir() and self.spec.get("revision"), "Exact local model revision required")
        allowed_files = {Path(item["path"]).resolve(strict=True) for item in self.spec["files"]}
        actual_files = {path.resolve() for path in model_dir.rglob("*") if path.is_file()
                        and path.suffix in (".json", ".safetensors", ".model", ".txt", ".tiktoken")}
        _require(actual_files <= allowed_files, "Unbound model, tokenizer or processor file")
        self.torch = torch
        torch.set_num_threads(2)
        torch.manual_seed(int(self.spec.get("seed", 20261023)))
        base, loading = Qwen3VLForConditionalGeneration.from_pretrained(
            str(model_dir), revision=self.spec["revision"], local_files_only=True,
            trust_remote_code=False, torch_dtype=torch.bfloat16,
            device_map={"": self.device}, low_cpu_mem_usage=True, attn_implementation="sdpa",
            output_loading_info=True)
        _require(all(not loading.get(key) for key in ("missing_keys", "unexpected_keys", "mismatched_keys", "error_msgs")),
                 "BASE strict checkpoint load has missing, unexpected or mismatched entries")
        _require(sum(parameter.numel() for parameter in base.parameters())
                 == int(self.spec.get("expected_base_parameters", ORIGINAL_BASE_PARAMETERS))
                 == ORIGINAL_BASE_PARAMETERS,
                 "Actual BASE logical parameter count differs")
        original_base_identity = _original_base_identity(base, torch)
        model = base
        if self.spec.get("adapter_dir"):
            from peft import PeftModel
            versions["peft"] = importlib.metadata.version("peft")
            _require(versions["peft"] == "0.17.1", "Pinned PEFT0.17.1 required")
            adapter_dir = Path(self.spec["adapter_dir"]).resolve(strict=True)
            _require(all(path.resolve() in allowed_files for path in adapter_dir.iterdir()
                         if path.suffix in (".json", ".safetensors")), "Unbound adapter file")
            model = PeftModel.from_pretrained(base, str(adapter_dir), is_trainable=False,
                                             autocast_adapter_dtype=True)
        for parameter in model.parameters():
            parameter.requires_grad_(False)
        model.eval()
        model.gradient_checkpointing_disable()
        inventory = _parameter_inventory(model)
        expected = ORIGINAL_BASE_PARAMETERS
        if self.spec.get("adapter_dir"):
            expected += int(self.spec.get("expected_adapter_parameters", 15_335_424))
        _require(inventory["parameter_count"] == expected <= 9_000_000_000,
                 "Actual shared main/adapter tensor count differs or exceeds9B")
        processor = AutoProcessor.from_pretrained(str(model_dir), revision=self.spec["revision"],
                                                  local_files_only=True, trust_remote_code=False)
        native = model.get_base_model() if self.spec.get("adapter_dir") else model
        def physical_forward(_module, _args):
            self.counts["physical_model_forwards"] += 1
        self._forward_hook = native.model.register_forward_pre_hook(physical_forward)
        # A partial load must never look reusable after an identity/interface
        # failure.  Publish the runtime only after all loading checks succeed.
        self.model, self.processor = model, processor
        self.inventory, self.versions = inventory, versions
        self.original_base_identity = original_base_identity
        return self.identity()

    def identity(self):
        _require(self.model is not None, "Model has not been loaded")
        return dict(model_id=self.spec.get("model_id", "original_qwen3vl_8b"),
                    revision=self.spec["revision"], files=self.spec["files"], versions=self.versions,
                    parameter_inventory=self.inventory, role="shared_BASE_and_optional_TIME",
                    original_base_identity=self.original_base_identity,
                    parameter_count=self.inventory["parameter_count"], counts=dict(self.counts))

    def _role(self, role):
        _require(role in ("base", "time"), "Only explicit BASE or original TIME roles supported")
        if role == "time":
            _require(self.spec.get("adapter_dir"), "TIME role requires the exact original adapter")
        return self.model.disable_adapter() if role == "base" and self.spec.get("adapter_dir") else nullcontext()

    def parameter_receipt(self):
        """Actual module tensors mapped to exact safetensors shard/key identity."""
        self.load()
        from safetensors import safe_open
        from .contracts import checked, inspect_loaded_parameters
        weight_refs = [dict(item) for item in self.spec["files"] if Path(item["path"]).suffix == ".safetensors"]
        keys = {}
        for identity in weight_refs:
            with safe_open(str(checked(identity)), framework="pt", device="cpu") as stream:
                for key in stream.keys():
                    _require(key not in keys, "Duplicate checkpoint key across registered Qwen shards")
                    keys[key] = dict(weight_ref=identity, tensor_name=key,
                                     shape=tuple(stream.get_slice(key).get_shape()))
        mapping, aliases = {}, {}
        for name, parameter in self.model.named_parameters(remove_duplicate=False):
            if id(parameter) in aliases:
                mapping[name] = mapping[aliases[id(parameter)]]
                continue
            candidates = {name, name.replace(".base_layer.", ".")}
            for candidate in tuple(candidates):
                if candidate.startswith("base_model.model."):
                    candidates.add(candidate[len("base_model.model."):])
                candidates.add(re.sub(r"(\.lora_[AB])\.default\.", r"\1.", candidate))
            matches = [keys[candidate] for candidate in candidates if candidate in keys]
            _require(len(matches) == 1, "Actual Qwen parameter lacks a unique checkpoint key: " + name)
            _require(matches[0]["shape"] == tuple(parameter.shape), "Loaded/checkpoint tensor shape differs: " + name)
            mapping[name] = {key: matches[0][key] for key in ("weight_ref", "tensor_name")}
            aliases[id(parameter)] = name
        receipt = inspect_loaded_parameters(self.model, "qwen_base", weight_refs, parameter_sources=mapping)
        _require(receipt["total_elements"] == self.inventory["parameter_count"], "Parameter receipt count differs")
        receipt["loading_proof"] = self._parameter_loading_proof()
        return receipt

    def _parameter_loading_proof(self):
        # The immutable receipt is adopted across separate candidate processes.
        # Load duration stays in identity() runtime statistics, never in this
        # deterministic tensor/model identity artifact.
        fields = ("sha256", "parameters", "method", "expected_sha256", "verified_before_adapter",
                  "hash_calls_this_load", "hash_function", "hash_function_file")
        proof = {key: self.original_base_identity[key] for key in fields}
        return dict(local_only=True, strict_BASE_loading_info_checked=True,
                    revision=self.spec["revision"], all_runtime_parameter_keys_bound=True,
                    original_base_identity=proof,
                    optional_TIME_loaded=bool(self.spec.get("adapter_dir")))

    def close(self):
        """Release this process's owned model/cache before another GPU stage."""
        if self.model is not None:
            self._forward_hook.remove()
            self.model = None
            self.processor = None
            self.inventory = None
            self.original_base_identity = None
            import gc
            gc.collect()
            self.torch.cuda.empty_cache()

    def _chat(self, content):
        return self.processor.apply_chat_template([dict(role="user", content=content)],
                                                  tokenize=False, add_generation_prompt=True,
                                                  enable_thinking=False)

    def _check_encoded(self, encoded, max_tokens=8192):
        _require(0 < encoded["input_ids"].shape[1] <= max_tokens, "Actual input exceeds fixed token budget")
        _require(bool((encoded["attention_mask"] == 1).all()), "Initial local prefix must be unpadded")
        return _tensor_signature(encoded)

    def generate_images(self, images, prompt, max_new_tokens=192, *, role="base"):
        self.load()
        import numpy as np
        from PIL import Image
        _require(images and all(isinstance(value, np.ndarray) and value.dtype == np.uint8
                                and value.ndim == 3 and value.shape[-1] == 3 for value in images),
                 "Actual uint8 RGB images required")
        _require(0 < max_new_tokens <= 256, "Generation budget must be1..256")
        text = self._chat([dict(type="image") for _ in images] + [dict(type="text", text=prompt)])
        encoded = self.processor(text=[text], images=[Image.fromarray(value) for value in images],
                                 images_kwargs={"size": {"shortest_edge": 65536, "longest_edge": 131072}},
                                 text_kwargs={"padding": False, "truncation": False},
                                 common_kwargs={"return_tensors": "pt"})
        signature = self._check_encoded(encoded)
        gpu = encoded.to(self.device)
        length = gpu["input_ids"].shape[1]
        started = time.monotonic()
        forwards_before = self.counts["physical_model_forwards"]
        with self._role(role), self.torch.inference_mode():
            result = self.model.generate(**gpu, do_sample=False, max_new_tokens=max_new_tokens,
                                         return_dict_in_generate=True)
        self.torch.cuda.synchronize()
        ids = result.sequences[0, length:]
        eos = self.model.generation_config.eos_token_id
        allowed_eos = [eos] if isinstance(eos, int) else eos
        _require(len(ids) and int(ids[-1]) in allowed_eos, "Truncated image generation is an execution failure")
        raw = self.processor.tokenizer.decode(ids, skip_special_tokens=True,
                                              clean_up_tokenization_spaces=False)
        self.counts["image_generations"] += 1
        self.counts["generated_tokens"] += len(ids)
        return dict(raw_text=raw, input_sha256=signature["sha256"], input_identity=signature,
                    output_token_ids=ids.cpu().tolist(), output_tokens=len(ids),
                    physical_model_forwards=self.counts["physical_model_forwards"] - forwards_before,
                    gpu_seconds=time.monotonic() - started, role=role,
                    parameter_count=self.inventory["parameter_count"],
                    parameter_inventory_sha256=self.inventory["inventory_sha256"],
                    deterministic=True, complete_eos=True)

    def ground_image(self, image, metadata):
        return self.generate_images([image], metadata["prompt"], metadata.get("max_new_tokens", 192),
                                    role=metadata.get("role", "base"))

    def _encode_clip(self, observation):
        torch = self.torch
        local_proof = _validate_local_observation(observation)
        rgb = observation["rgb"]
        clip = observation["clip"]
        array = torch.from_numpy(rgb).permute(0, 3, 1, 2)
        indices = list(clip["sample_ordinals"])
        if len(indices) == 1:
            array = torch.cat([array, array], dim=0)
            indices = indices + indices
        # fps is metadata only.  The timestamp callback uses every actual PTS.
        metadata = dict(fps=1.0, frames_indices=indices, total_num_frames=observation["source_n_frames"],
                        video_backend="pyav")
        text = self._chat([dict(type="video"), dict(type="text", text=phase_prompt(observation))])
        with _native_timestamps(self.processor, observation) as native:
            encoded = self.processor(text=[text], videos=[array],
                text_kwargs={"padding": False, "truncation": False},
                common_kwargs={"return_tensors": "pt"},
                videos_kwargs={"video_metadata": [metadata], "do_sample_frames": False,
                               "return_metadata": True,
                               "size": {"shortest_edge": 4096, "longest_edge": len(array) * 131072}})
        grid = encoded["video_grid_thw"].tolist()
        _require(len(grid) == 1 and grid[0][0] == len(clip["cells"]),
                 "Actual native two-frame groups differ from action cells")
        decoded = self.processor.tokenizer.decode(encoded["input_ids"][0], skip_special_tokens=False)
        times = [float(value) for value in re.findall(r"<([0-9]+(?:\.[0-9]+)?) seconds>", decoded)]
        _require(len(times) == len(native["native_group_pts"]) and all(
            abs(a - b) <= 0.05000001 for a, b in zip(times, native["native_group_pts"])),
            "Actual processor timestamp text differs from native PTS")
        return encoded, dict(native=native, input_identity=self._check_encoded(encoded),
                             video_grid_thw=grid, physical_source_sha256=observation["source_sha256"],
                             pixel_sha256=observation["pixel_sha256"], local_input=local_proof)

    def _suffixes(self, logical_ids):
        tokenizer = self.processor.tokenizer
        text = tokenizer.decode(logical_ids, skip_special_tokens=False, clean_up_tokenization_spaces=False)
        _require(tokenizer.encode(text, add_special_tokens=False) == logical_ids,
                 "Actual expanded local prefix cannot round-trip")
        rows = []
        for phase in PHASES:
            complete = tokenizer.encode(text + phase + "\n", add_special_tokens=False)
            _require(complete[:len(logical_ids)] == logical_ids,
                     "Complete semantic word tokenization changed prefix")
            suffix = complete[len(logical_ids):]
            _require(suffix and len(suffix) <= 8, "Unexpected semantic phase token length")
            rows.append(suffix)
        return rows

    def _reference_words(self, original_gpu, logical_ids, suffixes, cached_scores):
        """First-smoke independent full unpadded forwards, never a fallback."""
        torch = self.torch
        compared = []
        for suffix, cached in zip(suffixes, cached_scores):
            values = dict(original_gpu)
            complete = logical_ids + suffix
            values["input_ids"] = torch.tensor([complete], dtype=torch.long, device=self.device)
            values["attention_mask"] = torch.ones_like(values["input_ids"])
            output = self.model(**values, use_cache=False, return_dict=True,
                                logits_to_keep=len(suffix) + 1)
            projected = output.logits[0, :-1].float().log_softmax(-1)
            _require(projected.shape[0] == len(suffix), "Reference causal suffix positions differ")
            actual = [float(projected[position, token]) for position, token in enumerate(suffix)]
            expected = cached["token_log_probabilities"]
            errors = [abs(a - b) for a, b in zip(actual, expected)]
            mean_error = abs(sum(actual) / len(actual) - cached["mean_log_probability"])
            # BF16 batched GEMM and unbatched full-prefix GEMM have different
            # rounding.  Limits are fixed before the first real smoke, not
            # widened after results.  This compares complete semantic outputs.
            _require(max(errors) <= 0.20 and mean_error <= 0.08,
                     "Cached native phase scores disagree with independent unpadded full-prefix reference")
            compared.append(dict(phase=cached["phase"], reference_token_log_probabilities=actual,
                                 max_token_error=max(errors), mean_score_error=mean_error,
                                 complete_full_vocabulary_log_softmax=True))
            self.counts["reference_forwards"] += 1
            del output, projected, values
        return dict(status="PASS_CACHED_VS_UNPADDED_REFERENCE", comparisons=compared,
                    token_absolute_tolerance=0.20, mean_score_absolute_tolerance=0.08,
                    forward_count=4, no_reference_substitution=True)

    def phase_clip(self, observation, *, role="base", verify_reference=False):
        """Autoregressive semantic-word decoding with exact full-vocab scores.

        One physical local video prefill is shared by four complete word+LF
        branches per group.  A branch cache is selected after the decision;
        unselected branches do not become evidence.  Length-normalized scores
        are a registered decoding heuristic, not calibrated event probability.
        No query letters, hidden-state head or global-source KV is used.
        """
        self.load()
        torch = self.torch
        encoded, proof = self._encode_clip(observation)
        logical_ids = encoded["input_ids"][0].tolist()
        gpu = encoded.to(self.device)
        started = time.monotonic()
        forwards_before = self.counts["physical_model_forwards"]
        with self._role(role), torch.inference_mode():
            result = self.model(**gpu, use_cache=True, logits_to_keep=1, return_dict=True)
            cache = result.past_key_values
            _require(cache is not None and result.rope_deltas is not None
                     and tuple(result.rope_deltas.shape) == (1, 1), "Native Qwen prefix cache/RoPE unavailable")
            rope = int(result.rope_deltas[0, 0])
            attention = gpu["attention_mask"]
            previous_logits = result.logits[0, -1].float()
            _require(bool(torch.isfinite(previous_logits).all()), "Native local-prefix vocabulary logits are nonfinite")
            del result
            self.counts["video_prefills"] += 1
            phase_rows, reference_checks = [], []
            previous_phase = "start"
            for group, cell in enumerate(observation["clip"]["cells"]):
                suffixes = self._suffixes(logical_ids)
                maximum = max(map(len, suffixes))
                pad = self.processor.tokenizer.pad_token_id
                _require(type(pad) is int, "Actual tokenizer pad ID required")
                ids = torch.full((4, maximum), pad, device=self.device, dtype=torch.long)
                mask = torch.zeros_like(ids)
                for index, suffix in enumerate(suffixes):
                    ids[index, :len(suffix)] = torch.tensor(suffix, device=self.device)
                    mask[index, :len(suffix)] = 1
                physical = int(cache.get_seq_length())
                _require(physical == len(logical_ids) == attention.shape[1]
                         and bool((attention == 1).all()), "Semantic prefix cache is not dense and unpadded")
                # The previous prefix is consumed by these branches; retaining
                # a deep copy wastes KV memory without adding evidence.
                branch = cache
                _require(all(hasattr(branch, name) for name in
                             ("batch_repeat_interleave", "batch_select_indices", "crop")),
                         "Pinned DynamicCache branching API unavailable")
                branch.batch_repeat_interleave(4)
                positions = torch.arange(len(logical_ids) + rope,
                                         len(logical_ids) + rope + maximum, device=self.device)
                position_ids = positions.view(1, 1, -1).expand(3, 4, -1)
                branch_attention = torch.cat([attention.expand(4, -1), mask], dim=1)
                output = self.model(input_ids=ids, attention_mask=branch_attention,
                    position_ids=position_ids, cache_position=torch.arange(physical, physical + maximum,
                                                                           device=self.device),
                    past_key_values=branch, use_cache=True, return_dict=True)
                logits = output.logits.float()
                _require(tuple(logits.shape[:2]) == (4, maximum) and bool(torch.isfinite(logits).all()),
                         "Complete actual LM vocabulary logits invalid")
                first_logp = previous_logits.log_softmax(-1)
                logp = logits.log_softmax(-1)
                scores = []
                for index, suffix in enumerate(suffixes):
                    values = [float(first_logp[suffix[0]])]
                    values.extend(float(logp[index, j - 1, value]) for j, value in enumerate(suffix[1:], 1))
                    scores.append(dict(phase=PHASES[index], token_ids=suffix,
                                       token_log_probabilities=values, log_probability_sum=sum(values),
                                       mean_log_probability=sum(values) / len(values)))
                if verify_reference and group in (0, len(observation["clip"]["cells"]) - 1):
                    reference_checks.append(dict(group=group, **self._reference_words(
                        gpu, logical_ids, suffixes, scores)))
                allowed = TRANSITIONS[previous_phase]
                selected = max((i for i, phase in enumerate(PHASES) if phase in allowed),
                               key=lambda i: (scores[i]["mean_log_probability"], -i))
                chosen = PHASES[selected]
                ordinary = scores[0]["mean_log_probability"]
                phase_rows.append(dict(group=group, cell=cell, phase=chosen,
                    alternatives=scores, allowed_phases=list(allowed),
                    selected_minus_ordinary=scores[selected]["mean_log_probability"] - ordinary,
                    physical_prefill_reused_within_clip_only=True))
                chosen_length = len(suffixes[selected])
                cache = _commit_phase_cache(output.past_key_values,
                    torch.tensor([selected], device=self.device),
                    prefix_length=physical, suffix_length=chosen_length)
                attention = branch_attention[selected:selected + 1, :physical + chosen_length]
                previous_logits = logits[selected, chosen_length - 1].clone()
                logical_ids.extend(suffixes[selected])
                previous_phase = chosen
                self.counts["phase_branch_batches"] += 1
                self.counts["phase_alternatives"] += 4
                self.counts["generated_tokens"] += len(suffixes[selected])
                _require(len(logical_ids) - encoded["input_ids"].shape[1] <= 256,
                         "Action phase output exceeds registered256-token ceiling")
                del output, branch, logits, logp, ids, mask
        torch.cuda.synchronize()
        return dict(status="LEGAL_EMPTY" if all(row["phase"] == "ordinary" for row in phase_rows) else "MODEL_OK",
                    clip=observation["clip"], phases=phase_rows, input_proof=proof, role=role,
                    gpu_seconds=time.monotonic() - started, parameter_count=self.inventory["parameter_count"],
                    parameter_inventory_sha256=self.inventory["inventory_sha256"],
                    score_definition="MEAN_COMPLETE_SEMANTIC_WORD_AND_LF_FULL_VOCAB_LOGPROB",
                    physical_video_prefills=1, physical_branch_batches=len(phase_rows),
                    physical_semantic_alternatives=4 * len(phase_rows),
                    independent_unpadded_reference_checks=reference_checks,
                    independent_reference_forwards=4 * len(reference_checks),
                    physical_model_forwards=self.counts["physical_model_forwards"] - forwards_before,
                    raw_text="\n".join(row["phase"] for row in phase_rows) + "\n",
                    no_global_source_prefix=True, training_updates=0)
