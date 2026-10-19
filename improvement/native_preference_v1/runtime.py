"""One original-TIME adapter, fixed-reference sequence DPO, and native generation.

Importing this module does not import Torch, allocate CUDA, load weights, or start
work.  ``load_tokenizer`` / ``tokenize_answer`` support CPU preparation; the
execution agent must explicitly call ``QwenPreferenceRuntime.load`` for CUDA.
No historical launcher, input cache, BASE role, or second adapter is used.
"""
from __future__ import annotations

import hashlib
import importlib.metadata
import json
import math
import os
from pathlib import Path
import random
import re
import time

from .contracts import checked, digest, reference, require, strict_load


BASE_PARAMETERS = 8_767_123_696
ADAPTER_PARAMETERS = 15_335_424
SEMANTIC_PARAMETERS = 98_329
PIPELINE_PARAMETERS = BASE_PARAMETERS + 2 * ADAPTER_PARAMETERS + SEMANTIC_PARAMETERS
MAX_SEQUENCE_TOKENS = 12_288
MAX_ANSWER_TOKENS = 512
INITIAL_TOLERANCE_NATS = 0.02
ADAPTER_NAME = "policy"
TRAINABLE = re.compile(
    r"language_model\.layers\.(\d+)\.self_attn\."
    r"(q_proj|k_proj|v_proj|o_proj)\.lora_(A|B)\.policy\.weight$"
)
INPUT_KEYS = frozenset({"input_ids", "attention_mask", "pixel_values_videos", "video_grid_thw"})


def _json_digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def _model_spec(spec):
    require(isinstance(spec, dict), "Explicit model specification required")
    for name in ("model_dir", "revision", "base_sha256", "adapter_weights", "adapter_config"):
        require(name in spec, "Missing explicit model specification: " + name)
    model_dir = Path(spec["model_dir"])
    require(model_dir.is_absolute() and model_dir.is_dir(), "Existing absolute local model_dir required")
    require(isinstance(spec["revision"], str) and bool(spec["revision"]), "Pinned base revision required")
    require(re.fullmatch(r"[0-9a-f]{64}", spec["base_sha256"]) is not None,
            "Explicit canonical original-base SHA256 required")
    return spec


def load_tokenizer(model_spec):
    """Load the already-present pinned tokenizer on CPU; never download weights."""
    spec = _model_spec(model_spec)
    from transformers import AutoTokenizer
    return AutoTokenizer.from_pretrained(spec["model_dir"], revision=spec["revision"],
                                         local_files_only=True, trust_remote_code=False)


def _prefix_ids(values):
    ids = values["input_ids"] if isinstance(values, dict) else values
    data = ids.tolist() if hasattr(ids, "tolist") else ids
    require(isinstance(data, list) and len(data) == 1 and isinstance(data[0], list)
            and data[0] and all(type(v) is int and v >= 0 for v in data[0]),
            "One nonempty exact prefix token row required")
    return data[0]


def tokenize_answer(tokenizer, values, answer, *, request_text=None):
    """Re-encode complete expanded prefix + answer + EOS and bind the prefix.

    Encoding an answer in isolation is insufficient: tokenization may merge at
    the prompt boundary.  The actual cached prefix must survive complete-text
    tokenization unchanged.  The returned suffix includes terminal im_end.
    """
    require(isinstance(answer, str) and answer and "<|" not in answer,
            "Nonempty answer without special-token spellings required")
    prefix = _prefix_ids(values)
    decoded = tokenizer.decode(prefix, skip_special_tokens=False, clean_up_tokenization_spaces=False)
    text = decoded if request_text is None else request_text
    require(isinstance(text, str) and tokenizer.encode(text, add_special_tokens=False) == prefix,
            "Expanded request text does not reconstruct actual cached prefix")
    require(tokenizer.encode(decoded, add_special_tokens=False) == prefix,
            "Cached prefix cannot round-trip through pinned tokenizer")
    full = tokenizer.encode(text + answer + "<|im_end|>", add_special_tokens=False)
    require(full[:len(prefix)] == prefix, "Complete answer tokenization changed the visual/prompt prefix")
    suffix = full[len(prefix):]
    eos = tokenizer.convert_tokens_to_ids("<|im_end|>")
    require(type(eos) is int and eos >= 0 and suffix and suffix[-1] == eos
            and eos not in suffix[:-1], "Exactly one terminal im_end must be supervised")
    require(len(suffix) <= MAX_ANSWER_TOKENS and len(full) <= MAX_SEQUENCE_TOKENS,
            "Complete answer exceeds registered token budget; truncation is forbidden")
    require(tokenizer.decode(suffix[:-1], skip_special_tokens=False,
                             clean_up_tokenization_spaces=False) == answer,
            "Actual suffix does not exactly decode to the candidate answer")
    return suffix


def build_training_tokens(torch, values, suffix):
    """CPU batch-one causal mask: every answer token and EOS, no prompt target."""
    prefix = values["input_ids"] if isinstance(values, dict) else values
    require(prefix.device.type == "cpu" and prefix.dtype == torch.int64
            and prefix.ndim == 2 and prefix.shape[0] == 1 and prefix.shape[1] > 0,
            "CPU int64 batch-one prefix required")
    if isinstance(values, dict):
        mask = values["attention_mask"]
        require(mask.shape == prefix.shape and mask.dtype == torch.int64
                and mask.device.type == "cpu" and bool((mask == 1).all()),
                "Unpadded CPU prefix attention mask required")
    require(isinstance(suffix, list) and suffix and all(type(v) is int and v >= 0 for v in suffix),
            "Nonempty exact integer suffix required")
    tail = torch.tensor([suffix], dtype=torch.int64)
    full = torch.cat((prefix, tail), dim=1).contiguous()
    require(full.shape[1] <= MAX_SEQUENCE_TOKENS and len(suffix) <= MAX_ANSWER_TOKENS,
            "Complete sequence exceeds fixed budget")
    labels = torch.full_like(full, -100)
    labels[:, prefix.shape[1]:] = tail
    return dict(input_ids=full, attention_mask=torch.ones_like(full), labels=labels,
                positions=torch.arange(prefix.shape[1] - 1, full.shape[1] - 1, dtype=torch.int64),
                targets=tail)


def sequence_log_probability(torch, logits, targets):
    """Unnormalized whole-answer log probability, including the EOS token."""
    require(logits.ndim == 3 and targets.ndim == 2 and logits.shape[:2] == targets.shape,
            "Logit/target causal geometry differs")
    return -torch.nn.functional.cross_entropy(logits.float().reshape(-1, logits.shape[-1]),
                                              targets.reshape(-1), reduction="sum")


def dpo_tensor_loss(torch, policy_chosen, policy_rejected, reference_chosen, reference_rejected, beta):
    """Autograd form used by the independent CPU derivative check."""
    margin = (policy_chosen - policy_rejected) - (reference_chosen - reference_rejected)
    return torch.nn.functional.softplus(-beta * margin)


def dpo_loss_and_coefficient(policy_chosen, policy_rejected, reference_chosen, reference_rejected, beta):
    """Stable scalar loss and d(loss)/d(policy_chosen logp).

    The rejected coefficient is its negative.  These detached coefficients are
    recomputed at the CURRENT unchanged policy, never from a prior optimizer
    step.  Recomputing/backpropagating the two branches separately gives the
    same first derivative while only one multimodal graph is live at a time.
    """
    require(type(beta) in (int, float) and math.isfinite(beta) and beta > 0, "Positive finite beta required")
    require(all(math.isfinite(float(v)) for v in
                (policy_chosen, policy_rejected, reference_chosen, reference_rejected)),
            "Finite complete-sequence log probabilities required")
    margin = (float(policy_chosen) - float(policy_rejected)) - (float(reference_chosen) - float(reference_rejected))
    x = -float(beta) * margin
    loss = max(x, 0.0) + math.log1p(math.exp(-abs(x)))
    sigmoid = 1.0 / (1.0 + math.exp(-x)) if x >= 0 else math.exp(x) / (1.0 + math.exp(x))
    return loss, -float(beta) * sigmoid, margin


def freeze_except(model, names):
    """Require an explicit complete allowlist, also usable by the CPU test."""
    names = set(names)
    actual = {name for name, _ in model.named_parameters()}
    require(names <= actual, "Trainable parameter allowlist names are missing")
    for name, parameter in model.named_parameters():
        parameter.requires_grad_(name in names)
        if name not in names:
            parameter.grad = None


def canonical_frozen_hash(model, torch):
    """Exact historical canonical base hash, excluding all LoRA parameters."""
    parameters, seen = {}, set()
    for name, parameter in model.named_parameters(remove_duplicate=False):
        if id(parameter) in seen or "lora_" in name:
            continue
        seen.add(id(parameter))
        require(not parameter.requires_grad, "Base/vision parameter became trainable")
        canonical = name.removeprefix("base_model.model.").replace(".base_layer.", ".")
        require(canonical not in parameters, "Ambiguous canonical frozen parameter")
        parameters[canonical] = parameter
    result, count = hashlib.sha256(), 0
    for name, parameter in sorted(parameters.items()):
        result.update(name.encode())
        result.update(str(tuple(parameter.shape)).encode())
        result.update(str(parameter.dtype).encode())
        flat = parameter.detach().reshape(-1)
        for offset in range(0, flat.numel(), 1 << 22):
            result.update(flat[offset:offset + (1 << 22)].contiguous().view(torch.uint8).cpu().numpy().tobytes())
        count += parameter.numel()
    return dict(sha256=result.hexdigest(), parameters=count,
                method="sorted canonical names and all unique frozen parameter bytes")


def tensor_signature(torch, values):
    return {name: dict(shape=list(value.shape), dtype=str(value.dtype), sha256=hashlib.sha256(
        value.detach().cpu().contiguous().view(torch.uint8).numpy().tobytes()).hexdigest())
        for name, value in sorted(values.items())}


def _pair_payload(pair):
    require(isinstance(pair, dict), "Explicit pair record required")
    for name in ("pair_id", "input_key"):
        require(isinstance(pair.get(name), str) and pair[name], "Pair identity missing: " + name)
    chosen, rejected = pair.get("chosen_ids"), pair.get("rejected_ids")
    require(isinstance(chosen, list) and isinstance(rejected, list) and 0 < len(chosen) == len(rejected)
            and len(chosen) <= MAX_ANSWER_TOKENS and chosen != rejected
            and all(type(v) is int and v >= 0 for v in chosen + rejected),
            "Matched nonidentical exact suffix-token sequences required")
    return {name: pair[name] for name in ("pair_id", "input_key", "chosen_ids", "rejected_ids")}


class QwenPreferenceRuntime:
    """Explicit lazy GPU runtime for one fixed pilot and its reviewed final.

    ``check_budget`` follows StageBudget.check(*, forward=False).
    ``on_event(kind, payload)`` must persist events before returning.  In
    particular generation_raw is emitted before EOS/grammar validation so an
    unsuccessful attempt cannot silently turn into a legal empty answer.
    """

    def __init__(self, model_spec, check_budget=None, on_event=None, seed=20261019):
        self.spec = json.loads(json.dumps(_model_spec(model_spec)))
        require(seed == 20261019, "Fixed registered seed required")
        self.seed, self.check_budget, self.on_event = seed, check_budget, on_event
        self.model = self.native = self.tokenizer = self.torch = None
        self.mode, self.training, self.trained = "unloaded", False, False
        self._reference_digest = None
        self._saved_identity = None
        self.counts = dict(sequence_score_calls=0, sequence_scores_completed=0,
                           generation_calls=0, generations_completed=0,
                           top_level_forward_calls=0, backward_calls=0,
                           backwards_completed=0, optimizer_steps=0)

    def _check(self, *, forward=False):
        if self.check_budget is not None:
            self.check_budget(forward=True) if forward else self.check_budget()

    def _event(self, kind, **payload):
        if self.on_event is not None:
            self.on_event(kind, dict(mode=self.mode, counts=dict(self.counts), **payload))

    def _require_loaded(self):
        require(self.model is not None and self.torch is not None, "Explicit runtime.load() is required")

    def _original_files(self):
        weights, config = checked(self.spec["adapter_weights"]), checked(self.spec["adapter_config"])
        require(weights.name == "adapter_model.safetensors" and config.name == "adapter_config.json"
                and weights.parent == config.parent, "Bound original TIME adapter directory required")
        return weights, config

    @staticmethod
    def _validate_adapter_config(config, *, original):
        require(config.get("r") == 16 and config.get("lora_alpha") == 32
                and config.get("bias") == "none" and config.get("modules_to_save") is None
                and set(config.get("target_modules", [])) == {"q_proj", "k_proj", "v_proj", "o_proj"}
                and config.get("lora_dropout") == (0.05 if original else 0.0)
                and not config.get("use_dora", False) and not config.get("use_rslora", False)
                and not config.get("rank_pattern") and not config.get("alpha_pattern"),
                "Unexpected original TIME / policy adapter architecture")

    def _adapter_state(self):
        from peft import get_peft_model_state_dict
        state = {name: value.detach().cpu().contiguous().clone() for name, value in
                 get_peft_model_state_dict(self.model, adapter_name=ADAPTER_NAME).items()}
        require(len(state) == 288 and all("lora_" in name and value.dtype == self.torch.float32
                and bool(self.torch.isfinite(value).all()) for name, value in state.items()),
                "Exactly 288 finite FP32 adapter matrices required")
        return state

    def _restore_fp32(self, state):
        """Upcast destinations BEFORE copy, then check actual bytes, not rounded values."""
        from peft import set_peft_model_state_dict
        require(len(state) == 288 and all(value.dtype == self.torch.float32
                and bool(self.torch.isfinite(value).all()) for value in state.values()),
                "Saved TIME/policy must contain 288 finite FP32 matrices")
        for name, parameter in self.model.named_parameters():
            if "lora_" in name:
                require(TRAINABLE.search(name) is not None, "Unregistered adapter parameter")
                parameter.data = parameter.data.to(dtype=self.torch.float32)
        set_peft_model_state_dict(self.model, state, adapter_name=ADAPTER_NAME)
        actual = self._adapter_state()
        require(set(actual) == set(state) and all(actual[name].dtype == state[name].dtype
                and self.torch.equal(actual[name].view(self.torch.uint8), state[name].contiguous().view(self.torch.uint8))
                for name in state), "Actual adapter differs from saved FP32 bytes after loading")

    def _inventory(self, training=False):
        torch = self.torch
        base_count = adapter_count = 0
        names, parameters = [], []
        for name, parameter in self.model.named_parameters():
            if "lora_" in name:
                match = TRAINABLE.search(name)
                require(match is not None and parameter.ndim == 2 and parameter.dtype == torch.float32
                        and (parameter.shape[0] if match[3] == "A" else parameter.shape[1]) == 16
                        and parameter.requires_grad is training, "Unexpected policy matrix: " + name)
                names.append(name)
                parameters.append(parameter)
                adapter_count += parameter.numel()
            else:
                require(not parameter.requires_grad and parameter.grad is None,
                        "Base, vision, embeddings and vocabulary head must remain frozen")
                base_count += parameter.numel()
        layers = [module for module in self.model.modules() if hasattr(module, "lora_A")]
        require(base_count == BASE_PARAMETERS and adapter_count == ADAPTER_PARAMETERS and len(parameters) == 288
                and len(layers) == 144 and self.model.active_adapter == ADAPTER_NAME
                and all(set(module.lora_A) == {ADAPTER_NAME} and set(module.lora_B) == {ADAPTER_NAME}
                        and list(module.active_adapters) == [ADAPTER_NAME] and not module.disable_adapters
                        for module in layers), "Actual base/policy inventory or active adapter differs")
        require(PIPELINE_PARAMETERS == 8_797_892_873 <= 9_000_000_000, "Complete pipeline exceeds 9B")
        self._policy_names, self._policy_parameters, self._adapter_layers = names, parameters, layers
        return dict(base=base_count, policy=adapter_count, old_TIME_reference_counted=ADAPTER_PARAMETERS,
                    inherited_semantic_counted=SEMANTIC_PARAMETERS,
                    conservative_full_pipeline=PIPELINE_PARAMETERS,
                    physical_resident=base_count + adapter_count, matrices=288, language_targets=144,
                    trainable_parameters=adapter_count if training else 0, resident_adapters=1)

    def _disable_dropout(self):
        torch = self.torch
        for module in self.model.modules():
            if isinstance(module, torch.nn.modules.dropout._DropoutNd):
                module.p = 0.0
            for field in ("attention_dropout", "hidden_dropout", "activation_dropout", "resid_pdrop", "embd_pdrop", "attn_pdrop"):
                if type(getattr(module, field, None)) in (int, float):
                    setattr(module, field, 0.0)
        self.model.peft_config[ADAPTER_NAME].lora_dropout = 0.0

    def _inference_mode(self):
        self.training = False
        freeze_except(self.model, ())
        self.model.eval()
        self.model.gradient_checkpointing_disable()
        self.model.config.use_cache = True
        self.native.config.text_config.use_cache = True
        self._disable_dropout()

    def load(self):
        """Load local Qwen bf16 once and restore the sole TIME adapter bitexact FP32."""
        if self.model is not None:
            return self.identity()
        self._check()
        import torch
        from peft import PeftModel
        from safetensors.torch import load_file
        from transformers import Qwen3VLForConditionalGeneration
        require(torch.cuda.is_available(), "CUDA execution requires an independently admitted Linux GPU stage")
        require(os.environ.get("CUDA_VISIBLE_DEVICES", "").strip() not in ("", "-1"),
                "Execution wrapper must explicitly select the authorized GPU")
        self.versions = {name: importlib.metadata.version(name) for name in ("torch", "transformers", "peft", "safetensors")}
        require(self.versions["transformers"] == "4.57.1" and self.versions["peft"] == "0.17.1",
                "Pinned Qwen/PEFT execution versions differ")
        weights, config = self._original_files()
        self._validate_adapter_config(strict_load(config), original=True)
        self.torch = torch
        random.seed(self.seed)
        torch.manual_seed(self.seed)
        torch.cuda.manual_seed_all(self.seed)
        try:
            import numpy as np
            np.random.seed(self.seed)
        except ImportError:
            pass
        self._event("model_load_begin", model_spec=self.spec, versions=self.versions)
        base = Qwen3VLForConditionalGeneration.from_pretrained(
            self.spec["model_dir"], revision=self.spec["revision"], local_files_only=True,
            trust_remote_code=False, torch_dtype=torch.bfloat16, device_map={"": "cuda:0"},
            low_cpu_mem_usage=True, attn_implementation="sdpa")
        freeze_except(base, ())
        self.base_before = canonical_frozen_hash(base, torch)
        require(self.base_before["parameters"] == BASE_PARAMETERS
                and self.base_before["sha256"] == self.spec["base_sha256"],
                "Actual original-base bytes differ from registered base")
        self._check()
        self.model = PeftModel.from_pretrained(base, str(weights.parent), adapter_name=ADAPTER_NAME,
                                              is_trainable=False, autocast_adapter_dtype=True)
        self.native = self.model.get_base_model()
        original = load_file(str(weights), device="cpu")
        self._restore_fp32(original)
        del original
        self.tokenizer = load_tokenizer(self.spec)
        self.eos = self.tokenizer.convert_tokens_to_ids("<|im_end|>")
        self.video_token = self.tokenizer.convert_tokens_to_ids("<|video_pad|>")
        require(type(self.eos) is int and self.eos >= 0 and type(self.video_token) is int
                and self.video_token >= 0 and self.eos != self.video_token, "Actual pinned EOS/video IDs invalid")
        self._inference_mode()
        inventory = self._inventory(False)
        self.mode = "reference"

        def before_native_forward(_module, _args):
            self._check(forward=True)
            require(self.model.active_adapter == ADAPTER_NAME and all(
                not module.disable_adapters and list(module.active_adapters) == [ADAPTER_NAME]
                for module in self._adapter_layers), "Sole policy adapter was disabled or switched")
            self.counts["top_level_forward_calls"] += 1

        self._forward_hook = self.native.model.register_forward_pre_hook(before_native_forward)
        self._event("model_loaded", inventory=inventory, identity=self.identity(), dropout=0.0,
                    adapter_restore="288_FP32_MATRIX_BYTES_EXACT", base=self.base_before,
                    counter_scope="native.model top-level calls; excludes internal layer checkpoint recomputation")
        return self.identity()

    def identity(self):
        self._require_loaded()
        return dict(schema="AIC_NATIVE_PREFERENCE_RUNTIME_V1", base_sha256=self.spec["base_sha256"],
                    model_dir=self.spec["model_dir"], revision=self.spec["revision"],
                    original_TIME_weights=self.spec["adapter_weights"],
                    original_TIME_config=self.spec["adapter_config"], versions=self.versions,
                    base_dtype="torch.bfloat16", adapter_dtype="torch.float32", seed=self.seed,
                    dropout=0.0, eos_token_id=self.eos, video_token_id=self.video_token,
                    runtime_source_sha256=digest(Path(__file__)), sequence_logprob="SUM_ALL_SUFFIX_INCLUDING_EOS",
                    resident_adapters=1, conservative_full_pipeline_parameters=PIPELINE_PARAMETERS)

    def _values(self, values):
        self._require_loaded()
        torch = self.torch
        require(isinstance(values, dict) and set(values) == INPUT_KEYS
                and all(isinstance(value, torch.Tensor) and value.device.type == "cpu" for value in values.values()),
                "Exactly four CPU input tensors required")
        prefix, mask = values["input_ids"], values["attention_mask"]
        require(prefix.dtype == mask.dtype == torch.int64 and prefix.ndim == 2 and prefix.shape[0] == 1
                and 0 < prefix.shape[1] <= MAX_SEQUENCE_TOKENS - MAX_ANSWER_TOKENS
                and mask.shape == prefix.shape and bool((mask == 1).all()), "Unpadded actual prefix budget/geometry")
        require(bool((prefix >= 0).all()) and bool((prefix < self.native.config.text_config.vocab_size).all()),
                "Prefix token ID outside pinned vocabulary")
        pixels, grid = values["pixel_values_videos"], values["video_grid_thw"]
        require(pixels.dtype == torch.float32 and pixels.ndim == 2 and pixels.shape[1] == 1536
                and bool(torch.isfinite(pixels).all()) and grid.dtype == torch.int64
                and grid.shape == (2, 3) and bool((grid > 0).all()),
                "Finite original Overview/Excerpt patches and two actual video grids required")
        rows = 0
        for t, h, w in grid.tolist():
            require(h % 2 == 0 and w % 2 == 0, "Merge2 spatial geometry required")
            rows += t * h * w
        require(rows == pixels.shape[0] and int((prefix == self.video_token).sum()) == rows // 4,
                "Actual input video tokens, patch rows and grids disagree")
        return values

    def _suffix(self, suffix):
        require(isinstance(suffix, list) and 0 < len(suffix) <= MAX_ANSWER_TOKENS
                and all(type(value) is int and 0 <= value < self.native.config.text_config.vocab_size for value in suffix)
                and suffix[-1] == self.eos and self.eos not in suffix[:-1], "Complete EOS-terminated suffix required")

    def tokenize_answer(self, values, answer, *, request_text=None):
        self._require_loaded()
        return tokenize_answer(self.tokenizer, values, answer, request_text=request_text)

    def _sum_logprob(self, values, suffix, *, gradient=False):
        self._suffix(suffix)
        self._check()
        require(not gradient or self.training, "Policy training context required for backward-enabled score")
        torch = self.torch
        tokens = build_training_tokens(torch, values, suffix)
        gpu = dict(input_ids=tokens["input_ids"].to("cuda:0"),
                   attention_mask=tokens["attention_mask"].to("cuda:0"),
                   pixel_values_videos=values["pixel_values_videos"].to("cuda:0"),
                   video_grid_thw=values["video_grid_thw"].to("cuda:0"))
        self.counts["sequence_score_calls"] += 1
        context = torch.enable_grad() if gradient else torch.no_grad()
        with context:
            result = self.native.model(**gpu, use_cache=False, return_dict=True)
            hidden = result.last_hidden_state.index_select(1, tokens["positions"].to("cuda:0"))
            logits = self.native.lm_head(hidden)
            logprob = sequence_log_probability(torch, logits, tokens["targets"].to("cuda:0"))
        require(bool(torch.isfinite(logprob)) and (not gradient or logprob.requires_grad),
                "Finite connected whole-suffix log probability required")
        self.counts["sequence_scores_completed"] += 1
        return logprob

    def score(self, values, suffix):
        """One no-grad actual Qwen forward; return SUM logp of complete suffix."""
        values = self._values(values)
        return float(self._sum_logprob(values, suffix, gradient=False).detach().cpu())

    def generate(self, values, constraint):
        """One deterministic actual-Qwen generation; raw failure is never [] fallback."""
        require(not self.training, "Generation must not interleave with training/backward")
        values = self._values(values)
        require(callable(constraint) and getattr(constraint, "prompt_length", None) == values["input_ids"].shape[1]
                and getattr(constraint, "eos_token_ids", None) == frozenset({self.eos})
                and getattr(getattr(constraint, "grammar", None), "allow_empty", None) is True
                and getattr(constraint.grammar, "max_segments", None) == 6,
                "Frozen six-segment allow-empty PrefixConstraint required")
        self._check()
        self._inference_mode()
        gpu = {name: value.to("cuda:0") for name, value in values.items()}
        started = time.monotonic()
        self.counts["generation_calls"] += 1
        with self.torch.inference_mode():
            output = self.model.generate(**gpu, do_sample=False, num_beams=1, num_return_sequences=1,
                max_new_tokens=MAX_ANSWER_TOKENS,
                prefix_allowed_tokens_fn=constraint, eos_token_id=self.eos, pad_token_id=self.eos,
                return_dict_in_generate=True, output_scores=False, use_cache=True)
        sequence = output.sequences[0].detach().cpu().tolist()
        prefix = values["input_ids"][0].tolist()
        ids = sequence[len(prefix):]
        raw = self.tokenizer.decode(ids, skip_special_tokens=False, clean_up_tokenization_spaces=False)
        self._event("generation_raw", ids=ids, raw_text=raw, input_signature=tensor_signature(self.torch, values),
                    seconds=time.monotonic() - started, actual_model_call=True,
                    constraint_stats=dict(getattr(constraint, "stats", {})))
        require(sequence[:len(prefix)] == prefix, "Generation changed the actual input prefix")
        require(ids and ids[-1] == self.eos and self.eos not in ids[:-1],
                "Generation did not finish with exactly one actual EOS; no repair/empty fallback")
        require(len(ids) <= MAX_ANSWER_TOKENS, "Generation exceeded fixed token budget")
        text = self.tokenizer.decode(ids[:-1], skip_special_tokens=False, clean_up_tokenization_spaces=False)
        require(constraint.assert_complete(ids) == json.loads(text), "Constrained output/decoded JSON disagreement")
        self.counts["generations_completed"] += 1
        return dict(text=text, ids=ids, eos=True, eos_token_id=self.eos, actual_model_call=True,
                    seconds=time.monotonic() - started, counts=dict(self.counts),
                    input_signature=tensor_signature(self.torch, values), constraint_stats=dict(constraint.stats))

    def cache_reference(self, pairs, get_input):
        self._require_loaded()
        require(self.mode == "reference" and not self.trained and not self.training
                and self._reference_digest is None, "Reference cache may be created once before any policy update")
        require(isinstance(pairs, list) and 0 < len(pairs) <= 48, "Bounded train+heldout reference pair list required")
        require(len({pair["pair_id"] for pair in pairs}) == len(pairs), "Duplicate reference pair ID")
        self._inference_mode()
        original, _ = self._original_files()
        from safetensors.torch import load_file
        self._restore_fp32(load_file(str(original), device="cpu"))
        entries = {}
        for pair in pairs:
            payload = _pair_payload(pair)
            values = self._values(get_input(payload["input_key"]))
            signature = tensor_signature(self.torch, values)
            chosen = float(self._sum_logprob(values, payload["chosen_ids"]).detach().cpu())
            rejected = float(self._sum_logprob(values, payload["rejected_ids"]).detach().cpu())
            row = dict(**payload, input_signature=signature, chosen_logprob=chosen, rejected_logprob=rejected,
                       pair_sha256=_json_digest(payload))
            entries[payload["pair_id"]] = row
            self._event("reference_pair", **row)
        cache = dict(schema="AIC_FIXED_TIME_REFERENCE_LOGPROBS_V1", identity=self.identity(),
                     entries=entries, complete=True, reference_never_updated=True)
        self._reference_digest = _json_digest(cache)
        self._event("reference_cache_complete", pairs=len(entries), sha256=self._reference_digest)
        return cache

    def _reference_entry(self, cache, pair, values):
        require(cache.get("schema") == "AIC_FIXED_TIME_REFERENCE_LOGPROBS_V1" and cache.get("complete") is True
                and cache.get("reference_never_updated") is True and cache.get("identity") == self.identity(),
                "Reference cache model/tokenizer/precision identity changed")
        payload = _pair_payload(pair)
        row = cache["entries"][payload["pair_id"]]
        require(all(row.get(name) == value for name, value in payload.items())
                and row.get("pair_sha256") == _json_digest(payload)
                and row.get("input_signature") == tensor_signature(self.torch, values)
                and all(type(row.get(name)) in (int, float) and math.isfinite(row[name])
                        for name in ("chosen_logprob", "rejected_logprob")),
                "Reference answer, visual/prompt input, or log probability differs")
        return row

    def train_pairs(self, pairs, get_input, reference_cache, *, updates=16, grad_accum=2, lr=1e-5, beta=0.1):
        """One fixed 32-pair pass, 16 AdamW updates, no checkpoint selection.

        Each pair uses TWO current-policy no-grad scores, then TWO separate
        current-policy forward/backward branches with the exact detached DPO
        coefficients.  Only one graph is retained; parameters cannot change
        until both branches of both accumulation pairs have completed.
        """
        self._require_loaded()
        require(not self.trained and not self.training and self.mode == "reference", "Policy may train once from original TIME")
        require((updates, grad_accum, lr, beta) == (16, 2, 1e-5, 0.1) and len(pairs) == updates * grad_accum
                and len({pair["pair_id"] for pair in pairs}) == len(pairs), "Exactly registered 32 pairs / 16 updates required")
        require(self._reference_digest is not None and _json_digest(reference_cache) == self._reference_digest,
                "Complete immutable in-session reference cache required before policy training")
        original_path, _ = self._original_files()
        from safetensors.torch import load_file
        original = load_file(str(original_path), device="cpu")
        actual = self._adapter_state()
        require(set(actual) == set(original) and all(self.torch.equal(actual[name].view(self.torch.uint8),
                original[name].contiguous().view(self.torch.uint8)) for name in actual),
                "Training must initialize at exact original TIME bytes")
        del actual, original
        self._inventory(False)
        freeze_except(self.model, self._policy_names)
        self.training = True
        self.mode = "policy"
        self.model.config.use_cache = False
        self.native.config.text_config.use_cache = False
        self.model.train()
        self._disable_dropout()
        for name, module in self.model.named_modules():
            if name.endswith(".visual"):
                module.eval()
        self.model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
        inventory = self._inventory(True)
        torch = self.torch
        optimizer = torch.optim.AdamW(self._policy_parameters, lr=lr, betas=(0.9, 0.999), eps=1e-8, weight_decay=0)
        order = list(range(len(pairs)))
        random.Random(self.seed).shuffle(order)
        schedule = [pairs[index]["pair_id"] for index in order]
        report = dict(schema="AIC_NATIVE_PREFERENCE_TRAIN_V1", updates=updates, grad_accum=grad_accum,
                      learning_rate=lr, beta=beta, weight_decay=0, grad_clip=1, dropout=0,
                      inventory=inventory, schedule=schedule, schedule_sha256=_json_digest(schedule),
                      reference_cache_sha256=self._reference_digest, steps=[], checkpoint_selection="FINAL_ONLY",
                      gradient_method="EXACT_CURRENT_THETA_SEPARATE_BRANCH_RECOMPUTE",
                      teacher_forced_improvement_is_not_generation_admission=True)
        try:
            # Fixed first scheduled pair, before any update.  Byte equality is
            # separately mandatory for ALL matrices, independent of tolerance.
            first = pairs[order[0]]
            values = self._values(get_input(first["input_key"]))
            row = self._reference_entry(reference_cache, first, values)
            pc = float(self._sum_logprob(values, first["chosen_ids"]).detach().cpu())
            pr = float(self._sum_logprob(values, first["rejected_ids"]).detach().cpu())
            loss, _, margin = dpo_loss_and_coefficient(pc, pr, row["chosen_logprob"], row["rejected_logprob"], beta)
            initial = dict(pair_id=first["pair_id"], policy_chosen=pc, policy_rejected=pr,
                           reference_chosen=row["chosen_logprob"], reference_rejected=row["rejected_logprob"],
                           reference_relative_margin=margin, loss=loss, expected_loss=math.log(2),
                           tolerance_nats=INITIAL_TOLERANCE_NATS, all_288_initial_matrices_bitexact=True)
            report["initial_check"] = initial
            self._event("initial_reference_equality", **initial)
            require(max(abs(pc - row["chosen_logprob"]), abs(pr - row["rejected_logprob"]), abs(margin),
                        abs(loss - math.log(2))) <= INITIAL_TOLERANCE_NATS,
                    "Initial policy/reference probabilities differ; fixed tolerance exceeded")
            for step in range(updates):
                optimizer.zero_grad(set_to_none=True)
                records = []
                for index in order[step * grad_accum:(step + 1) * grad_accum]:
                    pair = pairs[index]
                    values = self._values(get_input(pair["input_key"]))
                    row = self._reference_entry(reference_cache, pair, values)
                    pc = float(self._sum_logprob(values, pair["chosen_ids"]).detach().cpu())
                    pr = float(self._sum_logprob(values, pair["rejected_ids"]).detach().cpu())
                    loss, coefficient, margin = dpo_loss_and_coefficient(pc, pr, row["chosen_logprob"], row["rejected_logprob"], beta)
                    record = dict(pair_id=pair["pair_id"], policy_chosen=pc, policy_rejected=pr,
                                  reference_chosen=row["chosen_logprob"], reference_rejected=row["rejected_logprob"],
                                  loss=loss, reference_relative_margin=margin, chosen_coefficient=coefficient)
                    self._event("policy_pair_scalar", update=step + 1, **record)
                    for name, sign, scalar in (("chosen", 1.0, pc), ("rejected", -1.0, pr)):
                        value = self._sum_logprob(values, pair[name + "_ids"], gradient=True)
                        recomputed = float(value.detach().cpu())
                        require(abs(recomputed - scalar) <= INITIAL_TOLERANCE_NATS,
                                "Current-theta branch changed during deterministic DPO recomputation")
                        self._check()
                        self.counts["backward_calls"] += 1
                        (value * (sign * coefficient / grad_accum)).backward()
                        self.counts["backwards_completed"] += 1
                        record[name + "_recomputed_logprob"] = recomputed
                        del value
                        self._event("policy_branch_backward", update=step + 1, pair_id=pair["pair_id"], branch=name,
                                    recomputed_logprob=recomputed, coefficient=sign * coefficient / grad_accum)
                    records.append(record)
                gradients = [parameter.grad for parameter in self._policy_parameters]
                require(all(value is not None and bool(torch.isfinite(value).all()) for value in gradients),
                        "Every one of 288 policy matrices must have a connected finite gradient")
                nonzero = sum(bool(torch.count_nonzero(value)) for value in gradients)
                norm = float(torch.nn.utils.clip_grad_norm_(self._policy_parameters, 1.0).detach().cpu())
                require(nonzero > 0 and math.isfinite(norm) and norm > 0, "Actual first/current gradient must be finite and nonzero")
                self._inventory(True)
                self._check()
                optimizer.step()
                self.counts["optimizer_steps"] += 1
                require(all(bool(torch.isfinite(parameter).all()) for parameter in self._policy_parameters),
                        "Optimizer produced nonfinite policy weights")
                result = dict(update=step + 1, gradient_norm_before_clip=norm,
                              finite_gradient_matrices=288, nonzero_gradient_matrices=nonzero, pairs=records)
                report["steps"].append(result)
                self._event("optimizer_step_complete", **result)
            optimizer.zero_grad(set_to_none=True)
            self.trained = True
        finally:
            optimizer.zero_grad(set_to_none=True)
            self._inference_mode()
            del optimizer
        require(self.counts["optimizer_steps"] == updates, "Incomplete fixed optimizer schedule")
        require(_json_digest(reference_cache) == self._reference_digest, "Fixed reference cache mutated during training")
        report["final_verification"] = self.verify_final()
        report["counts"] = dict(self.counts)
        report["status"] = "ENGINEERING_COMPLETE_REQUIRES_FREE_GENERATION_REVIEW"
        self._event("training_complete", report=report)
        return report

    def save_policy(self, directory):
        """Write exactly one final standard PEFT checkpoint to a new directory."""
        self._require_loaded()
        require(self.trained and not self.training and self.counts["optimizer_steps"] == 16,
                "Only the completed registered final policy can be saved")
        require(self._saved_identity is None, "Single final checkpoint only")
        self._check()
        path = Path(directory)
        require(path.is_absolute(), "Explicit absolute final checkpoint directory required")
        path.mkdir(parents=True, exist_ok=False)
        from safetensors.torch import load_file, save_file
        state = self._adapter_state()
        self.model.peft_config[ADAPTER_NAME].save_pretrained(str(path))
        weight_path, config_path = path / "adapter_model.safetensors", path / "adapter_config.json"
        save_file(state, str(weight_path), metadata={"format": "pt"})
        saved = load_file(str(weight_path), device="cpu")
        require(set(state) == set(saved) and all(self.torch.equal(state[name].view(self.torch.uint8),
                saved[name].contiguous().view(self.torch.uint8)) for name in state), "Final safetensors save lost actual bytes")
        self._validate_adapter_config(strict_load(config_path), original=False)
        self._saved_identity = dict(directory=str(path.resolve()), adapter_weights=reference(weight_path),
                                    adapter_config=reference(config_path), runtime=self.identity(),
                                    final_only=True, completed_updates=16, matrices=288, parameters=ADAPTER_PARAMETERS)
        self._event("final_policy_saved", identity=self._saved_identity)
        return self._saved_identity

    def load_policy(self, directory, expected_sha256):
        """Reload a bound final into the same sole adapter, never load_adapter()."""
        self._require_loaded()
        require(not self.training, "Cannot reload an adapter with a pending backward")
        path = Path(directory).resolve(strict=True)
        weights = checked(dict(path=str(path / "adapter_model.safetensors"), sha256=expected_sha256))
        config_path = path / "adapter_config.json"
        config = strict_load(config_path)
        self._validate_adapter_config(config, original=False)
        self._check()
        from safetensors.torch import load_file
        self._restore_fp32(load_file(str(weights), device="cpu"))
        self._inference_mode()
        self.mode = "policy"
        self._inventory(False)
        identity = dict(directory=str(path), adapter_weights=reference(weights), adapter_config=reference(config_path),
                        runtime=self.identity(), reloaded_288_fp32_matrices_bitexact=True)
        self._saved_identity = identity
        self._event("policy_reload_complete", identity=identity)
        return identity

    def verify_final(self):
        self._require_loaded()
        require(not self.training, "Final verification cannot overlap training")
        self._check()
        inventory = self._inventory(False)
        base = canonical_frozen_hash(self.model, self.torch)
        require(base == self.base_before, "Original base/vision/embedding/head bytes changed")
        original, _ = self._original_files()
        from safetensors.torch import load_file
        state, source = self._adapter_state(), load_file(str(original), device="cpu")
        changed = sum(not self.torch.equal(state[name].view(self.torch.uint8), source[name].contiguous().view(self.torch.uint8))
                      for name in state)
        if self.trained:
            require(changed > 0 and self.counts["optimizer_steps"] == 16,
                    "Completed policy must change actual adapter bytes through exactly 16 updates")
        return dict(base=base, original_TIME_files_unchanged=True, changed_adapter_matrices=changed,
                    inventory=inventory, counts=dict(self.counts), runtime=self.identity(),
                    saved_policy=self._saved_identity, requires_free_generation_review=True)
