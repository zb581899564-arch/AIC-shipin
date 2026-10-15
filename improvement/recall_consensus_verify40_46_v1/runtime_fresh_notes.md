# Fresh consensus confirmation runtime interface

These are new first-confirmation entry points. They do not run automatically.
Only `/home/inspur/aic_video_work/recall_consensus_verify40_46_20261015_v1`
and `group=confirm` are accepted. The old eight exposed sources are development
evidence, never this confirmation's inputs. No old input/cache/first QA recovery
branch is imported.

## Frozen prerequisites

`root/protocol.json` stays byte-identical to SHA256
`d71d191c2525402872a866ab513e84c1ee032fdb14858ff9034bdb32f93cb236`.
The candidate is `TWO_DISTINCT_OVERLAP_VIEWS_EXPLICIT_KEEP_INTERSECTION`.
`selection_before_fresh_confirmation.json` must have
`FROZEN_CONSENSUS2_AFTER_DEV_PASS`, matching protocol/result SHA and
`fresh_confirm_metrics_examined=false`. Its `development_01/result.json` must
be `PASS_CONSENSUS_DEVELOPMENT_NEEDS_FRESH_CONFIRM`, contain all eight sources
and the original eight true conditions, retain prior gates and deny production.

The single first-written `fresh_confirm_registration.json` uses:

```text
schema: RECALL_CONSENSUS_FRESH4_REFERENCE_REGISTRATION_V1
status: REGISTERED_FIRST_FRESH_CONFIRM_MEDIA_NATIVE_REFERENCE
group: confirm
protocol_ref: {path: root/protocol.json, sha256: ...}
authorization_ref: {path: root/USER_AUTHORIZATION.json, sha256: ...}
development_selection_ref: {path: root/selection_before_fresh_confirmation.json, sha256: ...}
development_result_ref: {path: root/development_01/result.json, sha256: ...}
required_files: {absolute_path: sha256, ...}
required_code_files: {absolute_path: sha256, ...} # subset of required_files
deadline: explicit timezone-aware ISO8601 instant
runtime:
  native_frames: 64
  max_input_tokens: 16384
  max_output_tokens: 256
  baseline_window_seconds: "30"
  candidate_window_seconds: "15"
  candidate_stride_seconds: "15/2"
  B0_prompt_sha256: dc0aa31d4a4df1894457a636ace17c55159122d62d7200fd2490ede06e19bce0
  grammar_allow_empty: true
  model_parameters: 8782459120
  enabled_TIME_layers: 144
  base_sha256: 74bcce81cfcb0893cf4b4c25ae36ec908d6ea669583aedd0f3940063080b8b59
  adapter_sha256: 8e2cca463d8aac39f7a709bdf562373e3e47a3a8da490991c303d5e03b803b23
gpu_budget:
  confirm_B0_max_seconds: 1800
  confirm_VERIFY_max_seconds: 2400
  per_group_max_B0_actual_calls: 48
  per_group_max_VERIFY_actual_calls: 240
```

The registration also contains the media agent's source pool, exclusion,
annotation, prior-media and acquisition fields. It is not amended after media
or CPU work. `model_common.fresh_gate(root, group)` returns `selection_path`,
`selection_sha256`, `result_path`, `result_sha256`, `protocol_sha256`,
`authorization_sha256`, `registration_path`, `registration_sha256`,
`registration`, `runtime`, `gpu_budget`, and the registered `files` mapping.

`code_files()` requires the four runtime/controller scripts, prepare/admit,
consensus/evaluate_development/evaluate_confirmation and unchanged
stage_io/overlap_plan. The source/CPU closure additionally freezes its media
entry, notes, original native-clock helpers, CONFIG/RUNTIME dependency code,
processor assets, and original cv_contract/cv_grammar/cv_tokens before B0.
Original model directories are not scanned to construct a file manifest;
the actual loaded base/adapter identity and all 144 enabled frozen layers
remain checked by the unchanged model execution functions.

## CPU and phase inputs

The media stage must already have completed; the controller never downloads
or measures clocks. `reference_completion_confirm.json` is `{path,sha256}`
pointing to the exact new confirm reference completion, which binds this same
registration and frozen development selection/result.

`prepare_fresh_inputs.py --root ROOT --group confirm` and the independent
`admit_fresh_inputs.py --root ROOT --group confirm` produce:

- `confirm/inputs_01/.../{input.json,encode_evidence.json,proof.json,encoded_tensors.pt.gz}`,
  lossless frame arrays and union PNG evidence retained by the input entry;
- `cpu_acceptance_confirm.json`, status
  `PASS_ALL_RECALL_REAL_CPU_INPUTS_NOT_GPU_ADMISSION`, source_count 4,
  expected_input_count equal to actual unique entries, maximum 48;
- `source_lock_confirm_B0.json`, with `files={absolute_path:sha256}`.

Entries retain `{case_id,group,source_name,input_path,input_sha256,proof_path,proof_sha256}`.
Proofs retain the original native64/cache/evidence schema, plus
`input_evidence_origin=NEW_FRESH_CONSENSUS_CONFIRM_PRIMARY_ENCODE`,
`first_independent_input_replay_pending=true`, saved primary evidence path/SHA,
and no pre-GPU independent replay. Metadata retains baseline/overlap `view_roles`
aliases: an identical actual view is called only once.

The stage admission files are `gpu_admission_confirm_B0.json` and
`gpu_admission_confirm_VERIFY.json`, status
`PASS_INDEPENDENT_CONSENSUS_FRESH_GPU_ADMISSION`. They freeze stage/count,
canonical CPU/lock paths and SHA, protocol/authorization/selection/result/
registration SHA, reference pointer/completion SHA, explicit deadline,
`max_seconds`, scope, model count and the unique job name. The VERIFY lock is a
new file; the B0 lock is never extended in place.

## CLI and outputs

After an explicit authorized deployment, one first chain invocation is:

```text
CUDA_VISIBLE_DEVICES=<actual-index> python -B pilot_chain_fresh.py --root ROOT --group confirm
```

It rejects existing CPU/stage/chain/admission/comparison attempts or either
job's old ledger/resource. The parent retains CUDA; only CPU child environments
set `CUDA_VISIBLE_DEVICES=''`. No resume, retry, fallback or background launcher
is provided. Each stage uses the existing shared `gpu_run.py` and verifies one
natural completed/exit0 resource equal to its sole ledger row:

```text
recall_consensus_fresh4_b0_20261015_v1
recall_consensus_fresh4_verify_20261015_v1
```

Individual stage CLIs retain `--root ROOT --group confirm`:

```text
pilot_runtime.py infer|replay
pilot_verify.py prepare|infer|replay|zero_export
```

All B0 lossless caches pass before model load. Every actual view gets one B0
call then its first independent real input/token/grammar/parser/native QA.
VERIFY prepares the complete actual candidate count and token-only caches
before its job; no vision processor or media is called in VERIFY. Its first
independent output QA preserves KEEP/UNKNOWN/DROP, and only explicit KEEP
supports consensus additions. Original segments are not padded or retimed.

Outputs retain the original stage status/schema under `confirm/B0/{gpu_01,replay_01}`,
`confirm/VERIFY/{cpu_01,gpu_01,replay_01}` and
`confirm/VERIFY/verification_export.json`. Raw/request/done, exact caches,
first QA proofs, terminal SHA and failures remain present. Existing success
directories prevent a second model call or first QA replay.

If complete accepted B0 outputs are all genuinely legal `[]`, the prepared
VERIFY list must truly be empty. `zero_export` creates `events=[]` with explicit
no-VERIFY-GPU/no-VERIFY-QA flags and retained B0 QA bindings. It never creates a
VERIFY admission, terminal or fictitious QA. The scientific no-additions result
must stop at evaluation.

The controller lastly calls only `evaluate_confirmation.py --root ROOT` in a
CPU child and accepts engineering exits 0/5. The actual result is
`confirm/comparison_01/result.json`; its bindings are `protocol_sha256`,
`registration_sha256`, `cpu_acceptance_sha256`, `verification_export_sha256`,
`first_B0_QA_sha256`, and `reference_completion_sha256`. It must contain four
cases and the original eight boolean conditions. `confirm/chain_01/completion.json`
uses `PASS_CONSENSUS_FRESH_CONFIRM_PENDING_FIXED40` or
`STOP_CONSENSUS_FRESH_CONFIRM_REJECTED`, retains both actual unique terminal /
first-QA completion refs (VERIFY not applicable only for true zero), and always
denies production. No fixed40, 426 inference or packaging is started.

Only local AST and bounded pure synthetic guards have been checked during
implementation. These checks are not real media/processor/model/confirmation
acceptance.
