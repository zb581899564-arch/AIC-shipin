# Training entrypoint

`train_lora.py` is fail-closed. It first reads
`/home/inspur/aic_video_work/coordination.json` and
`data_audit/training_gate.json`; only an explicit `training_authorized: true`
plus A's `passed=true`, `alignment_verified=true`, trusted split counts, and
accepted split files can reach the deferred Transformers / PEFT imports. A
`candidate_splits` section is never promoted automatically.

The locked data-gate evidence uses A's fields `passed`,
`alignment_verified`, and `counts[*].trusted_identity`. It must also name
three accepted JSONL files under `accepted_splits`; those paths are separate
from the candidate artifacts:

```json
{
  "passed": true,
  "alignment_verified": true,
  "counts": {
    "train": {"trusted_identity": 200},
    "dev": {"trusted_identity": 50},
    "holdout": {"trusted_identity": 50}
  },
  "accepted_splits": {
    "train": {"path": "accepted_train.jsonl"},
    "dev": {"path": "accepted_dev.jsonl"},
    "holdout": {"path": "accepted_holdout.jsonl"}
  }
}
```

Each file is recounted and parsed before model loading. Counts are taken from
`trusted_identity`, not raw label or candidate-row totals. Every row must have
a usable local video path and a `source_group`; media files must exist, source
groups must be disjoint after recomputation, and no path may point under the
sealed raw test root `/home/inspur/aic_video_data/test`. Rows marked
`candidate_only` or `do_not_use_as_training` are rejected. These checks
supplement A's source hash/media alignment evidence; they do not turn
candidate splits into accepted data.

Current run state is intentionally blocked: the supervisor coordination file
has `training_authorized: false`, and A's audit reports zero trusted pairs
with 75 missing source clips. Running the entrypoint produces
`reports/eval_training_gate.json`, imports no torch/Transformers/PEFT, starts
no GPU, and creates no adapter.

After the supervisor releases both gates, the configured deferred path is
Qwen3-VL-4B-Instruct with video-only temporal inputs: 2 FPS, at most 32
frames, approximately 100,000 pixels per frame, and sequence length 8192.
All visual/connector/main weights are frozen. LoRA is restricted to language
attention `q_proj`, `k_proj`, `v_proj`, and `o_proj` with `r=16`,
`alpha=32`, `dropout=0.05`. Trainer settings are BF16, batch 1,
gradient accumulation 16, AdamW (`weight_decay=0.01`), learning rate
`5e-5`, cosine schedule, warmup ratio `0.05`, gradient clipping `1.0`, seed
42, gradient checkpointing, `use_cache=False`, and 3 epochs with an 8-hour
time limit. `--smoke` selects 16 train samples and 20 optimizer steps, then
checks that `adapter_config.json` exists and PEFT can reload it.

Example (currently expected to exit 2 safely):

```bash
python3 -m training.train_lora --smoke \
  --report reports/eval_training_gate.json
```

Do not install dependencies from this entrypoint; B's independently prepared
environment owns that decision.
