# Three fixed anchor-trajectory risk packages

The user explicitly requested three automated risk submissions within three
hours, with no offline quality gate. The earlier human noon deadline remained
04:00 UTC on 2026-10-24. No new Goal or automation was created.

All three preserve the protected 40.48 package's **123,479 native frame members
and every original crop width**. They use the same successful local model
position anchors and original shot identities; the old schedule has maximum
gap **8 native frames**, not eight seconds. Actual native PTS drives the new
interpolation. No labels, individual test-video inspection, per-source knobs,
new model inference, training or decoding are involved.

The recipes were fixed and all packages completed before the first upload:

| ID | Recipe | Changed boxes | Actual official result |
|---|---|---:|---:|
|g_risk_pchip|Shape-preserving cubic through unchanged original anchors|33401|40.43|
|g_risk_median3|Three neighboring same-shot anchor coordinates' median, then linear interpolation|29223|**40.60**|
|g_risk_shot_representative|Actual same-shot anchor nearest coordinate-wise median, held inside that shot|57535|38.73|

All three are 426-source, independently checked, byte-identically received
final ZIPs, and were actually uploaded through user-authorized Edge. Official
DONE times were 09:22:23/09:24:30/09:26:33 Taipei on Oct24. The new observed best
is 40.60 (+0.12 over 40.48). This supports this complete fixed recipe on the
official evaluation, not a claim that arbitrary smoothing or fixed positions
help. No follow-up window/strength scan was performed. Neither old baseline nor
its dependencies were overwritten, and no historical failure was relabeled.

Exact private root: `/home/inspur/aic_video_work/last_three_trajectory_20261024_v1`.
`deploy.py` ships small control only and refuses an existing run root.
`controller.py` executes new targeted CPU tests, binding, derivation and
independent packaging once. `receive.py` fetches only final ZIPs and short
delivery manifests and runs the portable receiver. `archive_results.py` binds
actual browser scores and the private screenshot digest back to Linux.

The frozen original runtime checkout remains
`8dcde128be0ffe2df3ccba75d69929b7a9769a6f`. Actual all-model union remains
8,816,809,946 parameters. The new algorithms have zero learned parameters.
Six new targeted tests cover native-time interpolation, knots, no overshoot,
short shots, shot/gap isolation and duplicate-clock rejection. All three
independent eleven-check validations pass. A separately bound validator copy
only extends the provenance source enum for these declared automatic
derivations; the strict loader and all original checks remain unchanged.

The computation is CPU-only (at most two threads), 190.656057 command wall
seconds in total, with zero new GPU charges. Original model costs are retained.
Only final ZIPs (1,036,739 bytes total) and short receipts returned to Windows
over the verified existing direct ET route. Raw media, tensors, model answers,
full per-source evidence and package receipts remain on Linux. Java/GPU tasks,
CONTROL5, SSH/network/proxy/services are untouched. Official test data and
prediction payloads are not published here.

See `reports/github_status_20261024_v1/LAST_THREE_TRAJECTORY_RESULTS.md` for
final package identities and aggregate observed scores. The 40.60 package,
original 40.48 full pipeline, original anchors, new exact code/config and
complete proofs must be protected together. The older 40.47 also stays intact.
