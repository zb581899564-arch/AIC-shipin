# Round 3: temporal query-transfer diagnostic

This is a bounded **diagnostic**, not new training. The accepted data is
QVHighlights `query_moment_retrieval`: its target windows are relevant to each
row's query. No credible query-free AIC saliency ground truth or bounding-box
ground truth is available here, so these scripts never train on query windows
as generic highlights and never report generic arms as AIC accuracy.

The first two arms are the primary matched comparison on 12 source-disjoint
accepted dev rows: frozen base versus the round-2 LoRA, both with the query.
The next two remove the query under the same inference settings. They measure
prompt-transfer sensitivity only and are scored against query windows solely
as an explicitly labelled OOD stress reference.

GPU launch (supervisor-owned; hard cap 3600 seconds):

```bash
cd /home/inspur/aic_video_work
/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python improvement_round1/budget_run.py \
  --name r3_temporal_2x2_12g --max-seconds 3600 -- \
  /home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python \
  round3_20260912/temporal_query_transfer/run_contrast.py --num-groups 12 \
  --include-lora-query-128
```

The runner checks fixed SHA-256 values for the accepted dev file, adapter and
three inference sources; verifies the gate, task, split, source-group overlap,
media presence and the source-attestation semantic limitation; creates one
deterministic row per source group; forces offline mode; and writes a partial
`report.json` after each arm. The optional fifth arm repeats LoRA + query at
128 sampled frames after the four primary cells, testing a real sampling
change without risking the earlier paired results. Existing matching results
must start with empty output files: any existing non-empty temporal prediction
file causes a fail-closed rejection so a formal rerun cannot silently skip old
rows. A different frozen index is also rejected.

CPU-only preflight (does not import Torch or start the model):

```bash
cd /home/inspur/aic_video_work
/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python \
  round3_20260912/temporal_query_transfer/run_contrast.py --num-groups 12 \
  --include-lora-query-128 --prepare-only
```

Primary decision metric: paired mean duration-union F1 delta for
`lora_query - base_query`, plus win/tie/loss and parse/empty rates. Generic
arms additionally report output duration ratio and query-removal deltas, but
must not be used to claim AIC generic-highlight quality.

The closest existing 64-frame temporal run averaged 3.15 seconds per video;
allow about 8-20 minutes for 60 calls plus five model loads and the 128-frame
arm. The 3600 s wrapper remains the hard bound and records peak GPU memory.
Outputs stay under
`round3_20260912/temporal_query_transfer/runs`; no checkpoints are created.
