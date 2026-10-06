# AIC temporal inference v2

This directory is independent of the accepted baseline.  It reuses the
frozen baseline's media, crop, and geometry helpers without editing
`../inference/baseline_qwen3vl.py`.

## Contracts

- `single`: the original generic one-clip prompt and one whole-video call.
- `multi`: zero to four chronological, non-overlapping clips in one call.
- `windowed`: 30-second reader ranges at a 25-second step.  The model sees
  clip-local Qwen timestamps, local predictions are offset once to the
  original timeline, and true overlap is deduplicated without merging merely
  adjacent frame ranges.
- Seconds are half-open `[start_sec,end_sec)`.  `segments_frames` are original
  media `[start_frame,end_frame_exclusive)` ranges.
- `--query-aware` requires each input row to contain a string `query`.
  Without it, the AIC generic prompt is used.
- `--temporal-only` skips all subject-crop calls and writes the temporal
  schema.  `valid_empty` is successful; malformed output is `invalid`.
- `--temporal-adapter PATH` loads a PEFT adapter for stage 1.  All weights are
  frozen for inference, and the adapter is disabled around every stage-2 crop
  call.  A missing PEFT import fails clearly without changing the environment.
- `--constrained-json` adds an lm-format-enforcer prefix callback only to
  stage-1 generation. The compact grammar permits exactly the object
  `{"segments": [...]}`, with 0..1 pairs for `single` and 0..4 pairs for
  `multi`/`windowed`. Numeric bounds and ordering remain strict post-generation
  checks. Tokenizer vocabulary normalization is cached once per tokenizer.

lm-format-enforcer 0.11.3's `JsonSchemaParser` has a verified nested-array
`maxItems` off-by-one: a schema value of 4 permits only three fixed-size pairs.
The public schema remains truthful (`maxItems` 1/4), while the runtime uses the
library's `RegexParser` with the same official transformers prefix builder.
No third-party source is patched and the strict response parser is unchanged.

The shared training API is:

```python
from inference_v2.qwen_io import encode_qwen3vl_messages

encoded = encode_qwen3vl_messages(processor, messages, device=device)
processor_tensors = encoded.inputs
prefix_token_ids = encoded.prefix_input_ids
```

No truncation or maximum sequence length is applied.  Video metadata is
mandatory and passed separately with `do_sample_frames=False`.

## Commands

CPU contract and boundary tests:

```bash
/home/inspur/aic_video_work/env/qwen3vl/bin/python -m unittest discover \
  -s /home/inspur/aic_video_work/inference_v2/tests -v
/home/inspur/aic_video_work/env/qwen3vl/bin/python -m inference_v2.baseline_v2 \
  --print-contract
```

Bounded query-aware temporal smoke (GPU scheduling is owned by the
supervisor; do not run outside that allocation):

```bash
cd /home/inspur/aic_video_work
/home/inspur/aic_video_work/env/qwen3vl/bin/python -m inference_v2.baseline_v2 \
  --index /home/inspur/aic_video_work/improvement_round1/dev_frozen.jsonl \
  --temporal-only --query-aware --temporal-policy multi --num-videos 1 \
  --temporal-out /home/inspur/aic_video_work/runs/inference_v2_query_smoke/temporal_predictions.jsonl \
  --raw-out /home/inspur/aic_video_work/runs/inference_v2_query_smoke/raw.jsonl
```

Full AIC output keeps the accepted baseline JSONL schema:

```bash
cd /home/inspur/aic_video_work
/home/inspur/aic_video_work/env/qwen3vl/bin/python -m inference_v2.baseline_v2 \
  --index inference/test_index.json --temporal-policy multi --num-videos 1 \
  --out runs/inference_v2_multi_smoke/predictions.jsonl \
  --raw-out runs/inference_v2_multi_smoke/raw.jsonl \
  --status-out runs/inference_v2_multi_smoke/status.jsonl
```
