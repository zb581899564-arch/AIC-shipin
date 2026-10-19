"""Frozen original-TIME sampling and candidate-conditioned evidence.

The inherited loader verifies the original local base and every FP32 TIME
matrix.  This runtime never trains or replaces that adapter.  It evaluates
complete candidate answers, including their real EOS, in one teacher-forced
forward.  Importing this module does not import Torch or load any model.

The temporal permutation is deliberately a counterfactual: image groups move
while their text timestamps stay fixed.  It must not be registered as a new
truthful native observation.  A likelihood difference is visual sensitivity,
not by itself evidence of better highlight quality.
"""
from __future__ import annotations

from contextlib import contextmanager
from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path
import time

from improvement.native_preference_v1 import runtime as inherited
from improvement.native_preference_v1.contracts import digest, reference, require


BASE_PARAMETERS = inherited.BASE_PARAMETERS
ADAPTER_PARAMETERS = inherited.ADAPTER_PARAMETERS
SEMANTIC_PARAMETERS = inherited.SEMANTIC_PARAMETERS
PIPELINE_PARAMETERS = BASE_PARAMETERS + ADAPTER_PARAMETERS + SEMANTIC_PARAMETERS
HIDDEN_SIZE = 4096
FEATURE_SIZE = 128
PROJECTION_GROUPS = HIDDEN_SIZE // FEATURE_SIZE
PROJECTION_SEED = 20261019
PROJECTION_DOMAIN = "AIC_CONTENT_CHOICE_PROJECTION_V1"
MAX_ANSWER_TOKENS = inherited.MAX_ANSWER_TOKENS
SAMPLE_TEMPERATURE = 0.8
SAMPLE_TOP_P = 0.9
SAMPLE_TOP_K = 0

# These functions retain the original full-prefix re-encoding, causal mask,
# input byte signature and explicit local-only tokenizer contracts.
load_tokenizer = inherited.load_tokenizer
tokenize_answer = inherited.tokenize_answer
tensor_signature = inherited.tensor_signature
build_training_tokens = inherited.build_training_tokens
sequence_log_probability = inherited.sequence_log_probability


@lru_cache(maxsize=1)
def projection_signs():
    """A portable fixed transform; no Python hash or RNG-version dependency."""
    return tuple(1 if hashlib.sha256(
        f"{PROJECTION_DOMAIN}:{PROJECTION_SEED}:{index}".encode("ascii")
    ).digest()[0] & 1 else -1 for index in range(HIDDEN_SIZE))


def projection_spec():
    signs = projection_signs()
    return dict(input_dimensions=HIDDEN_SIZE, output_dimensions=FEATURE_SIZE,
                bucket="input_index_modulo_128", sign_domain=PROJECTION_DOMAIN,
                sign_seed=PROJECTION_SEED, sign="SHA256_first_byte_low_bit_1_means_plus",
                signs_sha256=hashlib.sha256(bytes(1 if x == 1 else 0 for x in signs)).hexdigest(),
                accumulation="FP32_IN_ASCENDING_INPUT_INDEX_WITHIN_EACH_BUCKET",
                normalization="DIVIDE_EACH_BUCKET_BY_SQRT_32", learned_parameters=0)


def project_numpy(hidden):
    """CPU reference for the exact 4096 -> 128 signed-hash transform."""
    import numpy as np
    require(isinstance(hidden, np.ndarray) and hidden.shape == (HIDDEN_SIZE,)
            and np.issubdtype(hidden.dtype, np.floating) and bool(np.isfinite(hidden).all()),
            "Projection requires one finite floating 4096-vector")
    signs = np.asarray(projection_signs(), dtype=np.float32)
    blocks = (hidden.astype(np.float32, copy=False) * signs).reshape(PROJECTION_GROUPS, FEATURE_SIZE)
    result = np.zeros(FEATURE_SIZE, dtype=np.float32)
    # Fixed summation order also makes the Torch CPU implementation comparable.
    with np.errstate(over="ignore", invalid="ignore"):
        for block in blocks:
            result = result + block
        result = result / np.float32(math.sqrt(PROJECTION_GROUPS))
    require(bool(np.isfinite(result).all()), "Projected hidden state is not finite")
    return result


def project_torch(torch, hidden):
    """Project on the hidden state's device; never retain a 4096-vector on disk."""
    require(isinstance(hidden, torch.Tensor) and tuple(hidden.shape) == (HIDDEN_SIZE,)
            and torch.is_floating_point(hidden) and bool(torch.isfinite(hidden).all()),
            "Projection requires one finite floating 4096-vector")
    signs = torch.tensor(projection_signs(), dtype=torch.float32, device=hidden.device)
    blocks = (hidden.detach().to(dtype=torch.float32) * signs).reshape(PROJECTION_GROUPS, FEATURE_SIZE)
    result = torch.zeros(FEATURE_SIZE, dtype=torch.float32, device=hidden.device)
    for block in blocks.unbind(0):
        result = result + block
    result = result / math.sqrt(PROJECTION_GROUPS)
    require(bool(torch.isfinite(result).all()), "Projected hidden state is not finite")
    return result


def eos_feature_position(prefix_tokens, suffix_tokens):
    """Absolute hidden position that predicts EOS, before consuming EOS."""
    require(type(prefix_tokens) is int and prefix_tokens > 0
            and type(suffix_tokens) is int and suffix_tokens > 0,
            "Positive actual prefix and suffix token counts required")
    return prefix_tokens + suffix_tokens - 2


def permutation_plan(grid):
    """Describe the two independent view rotations in raw patch-row space."""
    rows = grid.tolist() if hasattr(grid, "tolist") else grid
    require(isinstance(rows, list) and len(rows) == 2
            and all(isinstance(row, list) and len(row) == 3
                    and all(type(x) is int and x > 0 for x in row) for row in rows),
            "Exactly two positive integer [temporal_groups, height, width] grids required")
    offset, result = 0, []
    for view, (groups, height, width) in enumerate(rows):
        require(height % 2 == width % 2 == 0, "Merge2 spatial geometry required")
        count = groups * height * width
        result.append(dict(view=view, groups=groups, height=height, width=width,
                           shift_groups=groups // 2, patch_start=offset, patch_rows=count))
        offset += count
    return result


def permute_visual(values):
    """Return four tensors/arrays with whole-group rotations inside each view.

    This preserves patch-row contents (including the two-frame patch vector),
    spatial order inside a group, all view boundaries and the input shape.
    Input IDs, attention and grid are the unchanged original objects.  Only
    the pixels receive a new allocation; the input is never modified.
    """
    require(isinstance(values, dict) and set(values) == inherited.INPUT_KEYS,
            "Exactly the four native input fields are required for permutation")
    pixels, grid = values["pixel_values_videos"], values["video_grid_thw"]
    plan = permutation_plan(grid)
    require(getattr(pixels, "ndim", None) == 2 and pixels.shape[1] == 1536
            and pixels.shape[0] == sum(row["patch_rows"] for row in plan),
            "Pixel rows must exactly match both video grids")
    if type(pixels).__module__.split(".")[0] == "numpy":
        import numpy as np
        require(isinstance(pixels, np.ndarray) and isinstance(grid, np.ndarray)
                and pixels.dtype == np.float32 and grid.dtype == np.int64
                and bool(np.isfinite(pixels).all()), "Finite original FP32 pixels and int64 NumPy grid required")
        output = np.empty_like(pixels)
    else:
        import torch
        require(isinstance(pixels, torch.Tensor) and isinstance(grid, torch.Tensor)
                and pixels.device.type == grid.device.type == "cpu"
                and pixels.dtype == torch.float32 and grid.dtype == torch.int64
                and not pixels.requires_grad and bool(torch.isfinite(pixels).all()),
                "Finite original CPU FP32 pixels and CPU int64 grid required")
        output = torch.empty_like(pixels)
    for row in plan:
        start, count = row["patch_start"], row["patch_rows"]
        moved = row["shift_groups"] * row["height"] * row["width"]
        cut = count - moved
        # Right rotation by floor(groups / 2), without splitting any raw patch
        # vector or creating an additional full-view temporary.
        if moved:
            output[start:start + moved] = pixels[start + cut:start + count]
        output[start + moved:start + count] = pixels[start:start + cut]
    return dict(values, pixel_values_videos=output)


@contextmanager
def sampled_rng(torch, seed, *, device="cuda:0"):
    """Seed and restore CPU plus the one participating CUDA RNG, even on error."""
    require(type(seed) is int and 0 <= seed < (1 << 63), "Sampling seed must be an int in [0, 2**63)")
    target = torch.device(device)
    require(target.type == "cpu" or target.type == "cuda" and target.index == 0,
            "Sampling is restricted to CPU checks or authorized CUDA:0")
    devices = [] if target.type == "cpu" else [0]
    with torch.random.fork_rng(devices=devices):
        # torch.manual_seed would also reseed other visible CUDA devices.  These
        # local generators only touch the states saved by the fork above.
        torch.set_rng_state(torch.Generator(device="cpu").manual_seed(seed).get_state())
        if devices:
            torch.cuda.set_rng_state(torch.Generator(device=target).manual_seed(seed).get_state(), device=0)
        yield


def teacher_forced_features(torch, native, values, suffix, *, device):
    """The shared real tensor path, also exercised by small CPU-Torch checks.

    The caller verifies the registered Qwen identity, input and unique final
    EOS.  This function makes exactly one native.model forward and one lm_head
    call; feature extraction does not call the model again.
    """
    tokens = build_training_tokens(torch, values, suffix)
    placed = dict(input_ids=tokens["input_ids"].to(device),
                  attention_mask=tokens["attention_mask"].to(device),
                  pixel_values_videos=values["pixel_values_videos"].to(device),
                  video_grid_thw=values["video_grid_thw"].to(device))
    position = eos_feature_position(values["input_ids"].shape[1], len(suffix))
    require(int(tokens["positions"][-1]) == position, "Causal EOS feature index disagrees with suffix labels")
    with torch.inference_mode():
        result = native.model(**placed, use_cache=False, return_dict=True)
        hidden = result.last_hidden_state
        require(tuple(hidden.shape) == (1, tokens["input_ids"].shape[1], HIDDEN_SIZE),
                "Actual Qwen last_hidden_state must be batch-one with 4096 hidden dimensions")
        causal = hidden.index_select(1, tokens["positions"].to(device))
        logits = native.lm_head(causal)
        logprob = sequence_log_probability(torch, logits, tokens["targets"].to(device))
        feature = project_torch(torch, hidden[0, position])
        require(bool(torch.isfinite(logprob)) and not logprob.requires_grad
                and not feature.requires_grad, "Finite frozen complete-answer score and feature required")
        return dict(logprob=float(logprob.detach().cpu()), suffix_tokens=len(suffix),
                    feature=feature.detach().cpu().tolist(), feature_position=position)


def assert_original_adapter_unchanged(torch, state, source):
    """No numerical tolerance: all 288 original FP32 matrices must match bytes."""
    require(len(state) == 288 and set(state) == set(source)
            and all(state[name].dtype == source[name].dtype == torch.float32
                    and state[name].shape == source[name].shape for name in state),
            "Actual TIME matrix inventory differs from the original checkpoint")
    changed = sum(not torch.equal(state[name].detach().cpu().contiguous().view(torch.uint8),
                  source[name].detach().cpu().contiguous().view(torch.uint8)) for name in state)
    require(changed == 0, "Frozen original TIME bytes changed; candidate choice may not update LoRA")
    return changed


class QwenChoiceRuntime(inherited.QwenPreferenceRuntime):
    """One immutable original TIME; candidate choice lives outside this class."""

    def __init__(self, model_spec, check_budget=None, on_event=None, seed=20261019):
        super().__init__(model_spec, check_budget=check_budget, on_event=on_event, seed=seed)
        self.counts.update(sample_generation_calls=0, samples_completed=0,
                           feature_score_calls=0, feature_scores_completed=0)

    def load(self):
        super().load()
        require(self.native.config.text_config.hidden_size == HIDDEN_SIZE,
                "Registered original Qwen must have exactly 4096 language hidden dimensions")
        self.mode = "original_TIME"
        self._assert_frozen_state()
        return self.identity()

    def _assert_frozen_state(self):
        self._require_loaded()
        require(not self.training and not self.trained and self._saved_identity is None
                and not self.model.training and all(self.counts[name] == 0 for name in
                    ("backward_calls", "backwards_completed", "optimizer_steps")),
                "Content choice must use unchanged original TIME with zero backward/updates")
        require(all(not parameter.requires_grad and parameter.grad is None
                    for parameter in self.model.parameters()), "Every base and TIME parameter must remain frozen without gradients")

    def _inventory(self, training=False):
        require(training is False, "Content choice cannot enable trainable TIME parameters")
        report = super()._inventory(False)
        # There is one original TIME dependency, with no updated-policy copy.
        report.pop("old_TIME_reference_counted")
        report["original_TIME"] = report.pop("policy")
        report["conservative_full_pipeline"] = PIPELINE_PARAMETERS
        report["projection_learned_parameters"] = 0
        require(PIPELINE_PARAMETERS == 8_782_557_449 <= 9_000_000_000,
                "Complete frozen pipeline parameter inventory differs")
        return report

    def identity(self):
        result = super().identity()
        result.update(schema="AIC_CONTENT_CHOICE_RUNTIME_V1", active_weights="ORIGINAL_TIME_UNCHANGED",
                      runtime_source_sha256=digest(Path(__file__)),
                      inherited_runtime=reference(Path(inherited.__file__)),
                      conservative_full_pipeline_parameters=PIPELINE_PARAMETERS,
                      optimizer_updates=0, projection=projection_spec(),
                      feature_state="LAST_CAUSAL_STATE_PREDICTING_FINAL_EOS_NOT_CONSUMING_EOS",
                      sampling=dict(do_sample=True, temperature=SAMPLE_TEMPERATURE, top_p=SAMPLE_TOP_P,
                                    top_k=SAMPLE_TOP_K, typical_p=1.0, repetition_penalty=1.0,
                                    max_new_tokens=MAX_ANSWER_TOKENS, num_beams=1,
                                    num_return_sequences=1, retries=0, seed_scope="SOURCE_SHA_UID_SLOT"),
                      counterfactual="EACH_VIEW_WHOLE_TEMPORAL_GROUP_ROLL_FLOOR_HALF_WITH_FIXED_TEXT_TIMESTAMPS")
        return result

    def score_features(self, values, suffix):
        """One actual frozen TF call: SUM complete logp + EOS-predicting feature."""
        self._assert_frozen_state()
        values = self._values(values)
        self._suffix(suffix)
        self._check()
        self.counts["sequence_score_calls"] += 1
        self.counts["feature_score_calls"] += 1
        result = teacher_forced_features(self.torch, self.native, values, suffix, device="cuda:0")
        self.counts["sequence_scores_completed"] += 1
        self.counts["feature_scores_completed"] += 1
        result.update(actual_model_call=True, counts=dict(self.counts))
        return result

    def _sum_logprob(self, values, suffix, *, gradient=False):
        require(gradient is False, "Frozen content choice cannot score with a backward graph")
        self._assert_frozen_state()
        return super()._sum_logprob(values, suffix, gradient=False)

    def generate(self, values, constraint):
        """Original greedy for sources without an exact historical output."""
        self._assert_frozen_state()
        return super().generate(values, constraint)

    def generate_sample(self, values, constraint, seed):
        """One fixed nucleus sample; persist raw output before validating EOS."""
        self._assert_frozen_state()
        require(type(seed) is int and 0 <= seed < (1 << 63), "Sampling seed must be an int in [0, 2**63)")
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
        called = False
        options = dict(do_sample=True, temperature=SAMPLE_TEMPERATURE, top_p=SAMPLE_TOP_P,
                       top_k=SAMPLE_TOP_K, typical_p=1.0, repetition_penalty=1.0,
                       no_repeat_ngram_size=0, num_beams=1, num_return_sequences=1,
                       max_new_tokens=MAX_ANSWER_TOKENS, prefix_allowed_tokens_fn=constraint,
                       eos_token_id=self.eos, pad_token_id=self.eos,
                       return_dict_in_generate=True, output_scores=False, use_cache=True)
        try:
            with sampled_rng(self.torch, seed), self.torch.inference_mode():
                self.counts["generation_calls"] += 1
                self.counts["sample_generation_calls"] += 1
                called = True
                output = self.model.generate(**gpu, **options)
        except Exception as error:
            self._event("generation_exception", seed=seed, actual_model_call=called,
                        exception_type=type(error).__name__, error=str(error), seconds=time.monotonic() - started)
            raise
        require(output.sequences.ndim == 2 and output.sequences.shape[0] == 1,
                "Exactly one actual sampled output sequence required")
        sequence = output.sequences[0].detach().cpu().tolist()
        prefix = values["input_ids"][0].tolist()
        ids = sequence[len(prefix):]
        signature = tensor_signature(self.torch, values)
        raw = self.tokenizer.decode(ids, skip_special_tokens=False, clean_up_tokenization_spaces=False)
        self._event("generation_raw", ids=ids, raw_text=raw, input_signature=signature,
                    seconds=time.monotonic() - started, actual_model_call=True, seed=seed,
                    generation="FIXED_NUCLEUS_SAMPLE", temperature=SAMPLE_TEMPERATURE,
                    top_p=SAMPLE_TOP_P, top_k=SAMPLE_TOP_K,
                    constraint_stats=dict(getattr(constraint, "stats", {})))
        require(sequence[:len(prefix)] == prefix, "Generation changed the actual input prefix")
        require(ids and ids[-1] == self.eos and self.eos not in ids[:-1],
                "Generation did not finish with exactly one actual EOS; no repair/empty fallback")
        require(len(ids) <= MAX_ANSWER_TOKENS, "Generation exceeded fixed token budget")
        text = self.tokenizer.decode(ids[:-1], skip_special_tokens=False, clean_up_tokenization_spaces=False)
        require(constraint.assert_complete(ids) == json.loads(text), "Constrained output/decoded JSON disagreement")
        self.counts["generations_completed"] += 1
        self.counts["samples_completed"] += 1
        return dict(text=text, ids=ids, eos=True, eos_token_id=self.eos, actual_model_call=True,
                    seed=seed, temperature=SAMPLE_TEMPERATURE, top_p=SAMPLE_TOP_P, top_k=SAMPLE_TOP_K,
                    seconds=time.monotonic() - started, counts=dict(self.counts),
                    input_signature=signature, constraint_stats=dict(constraint.stats))

    def verify_frozen(self):
        """Compare actual final base and all 288 TIME matrices with originals."""
        self._assert_frozen_state()
        self._check()
        inventory = self._inventory(False)
        base = inherited.canonical_frozen_hash(self.model, self.torch)
        require(base == self.base_before, "Original base/vision/embedding/head bytes changed")
        original, _ = self._original_files()
        from safetensors.torch import load_file
        state, source = self._adapter_state(), load_file(str(original), device="cpu")
        assert_original_adapter_unchanged(self.torch, state, source)
        return dict(schema="AIC_CONTENT_CHOICE_FROZEN_VERIFICATION_V1", base=base,
                    original_TIME_files_unchanged=True, changed_adapter_matrices=0,
                    optimizer_steps=0, backward_calls=0, inventory=inventory,
                    counts=dict(self.counts), runtime=self.identity(),
                    independent_source_generation_review_required=True)

    def verify_final(self):
        return self.verify_frozen()

    def train_pairs(self, *args, **kwargs):
        raise ValueError("Frozen original TIME choice runtime forbids training or optimizer updates")

    def cache_reference(self, *args, **kwargs):
        raise ValueError("Content choice does not create or use a DPO reference-pair cache")

    def save_policy(self, *args, **kwargs):
        raise ValueError("Frozen original TIME choice runtime cannot save a newly trained policy")

    def load_policy(self, *args, **kwargs):
        raise ValueError("Frozen original TIME choice runtime cannot load a DPO or replacement policy")
