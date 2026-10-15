只准备，尚未执行上传、远端验收、freeze、check-only 或 pipeline。ROOT 完成最终24窗 registry 准入后，按以下顺序显式调用。所有失败保留原目录/日志，不自动重试或删除；`native_sources` 的12视频只校验 SHA，不上传。

1. ROOT 先使用既有 `prepare_linux_projection.py` 生成新 metadata projection 目录及 ZIP（本工具不代替科学准入）。将最终24窗准入 receipt 的实际路径/SHA、projection目录/ZIP代入：

```powershell
python -B reports/annotation_iteration_20261010/complete_reference_supplement_v1/deployment_tools_v1/deploy_metadata.py prepare --projection '<新projection目录>' --zip '<对应zip>' --root-admission '<ROOT最终准入receipt>' --expected-root-admission '<实际SHA>' --source-upload-receipt 'reports/annotation_iteration_20261010/complete_reference_supplement_v1/source_transfer_completed_v1/upload_validation_receipt.json' --expected-source-upload-receipt ca34a6d30041575adfe1e84593bd814626a308e77b41a666e19f00dd0d6458eb --output '<新manifest.json>'
```

该命令实际校验固定24分母的20个原 reference（4拒绝项不要求 reference）、所有 projection receipt 源绑定/语义路径投影、ZIP CRC/全部成员 SHA、当前23个 runtime Python SHA，x写 manifest。最终ROOT receipt要求字段：`registry_binding:{path,sha256}` 等于 projection原registry；`denominator:{total:24,qualified:20,rejected:4,pending:0}`、`train_windows:8`、`evaluation_windows:12`、`fully_known_locked:6`、`original_silver_actual_verified:true`。绑定实际上传12视频receipt；原projection的静态泛用 `source_upload_still_required` 已由实际receipt满足，不改原bytes。它不代替 ROOT 逐窗科学裁决。输出会给出已填路径/SHA的三个具体ROOT命令，start只保留实际远端acceptanceSHA占位。

2. ROOT 明确上传时：

```powershell
& reports/annotation_iteration_20261010/complete_reference_supplement_v1/deployment_tools_v1/upload_metadata.ps1 -Zip '<对应zip>' -Manifest '<新manifest.json>' -ExpectedManifest '<实际manifest SHA>' -RootAuthorizeUpload
```

脚本读 Mac 唯一工作目录的 AGENTS，经既有 runner 核在线身份；无 Mac 落盘。SSH/SCP 使用既有 alias、严格主机校验；传输使用 `scp -J macmini`，Mac 不可达就停止，不直传。远端只新建 `deployment_metadata_v1`，目标 `inputs` 必须不存在。脚本不启动任何远端工作。

3. ROOT 显式远端验收（ZIP安全提取后每文件SHA；一次 freeze 和 `train --check-only`）：

```powershell
ssh -o BatchMode=yes -o StrictHostKeyChecking=yes aic-inspur-home '/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python -B /home/inspur/aic_video_work/annotation_iteration_20261010/complete_reference_supplement_v1/deployment_metadata_v1/deploy_metadata.py accept --zip /home/inspur/aic_video_work/annotation_iteration_20261010/complete_reference_supplement_v1/deployment_metadata_v1/metadata.zip --manifest /home/inspur/aic_video_work/annotation_iteration_20261010/complete_reference_supplement_v1/deployment_metadata_v1/manifest.json --expected-manifest <实际manifestSHA>'
```

验收保存 `accept_attempt.json`、`freeze.log`、`check_only.log`、`acceptance.json`，freeze 自身另存 `source_lock.creation_receipt.json`。任何步骤失败自然报错，不重新 freeze。路径拒绝绝对/反斜线/冒号/`.`/`..`、重复、symlink、非普通成员和加密文件；输入集合和每个CRC/SHA严格相等。

4. ROOT 查看上步实际 receipt 后，明确授权一次 pipeline 启动，传入实际 acceptance SHA：

```powershell
ssh -o BatchMode=yes -o StrictHostKeyChecking=yes aic-inspur-home '/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python -B /home/inspur/aic_video_work/annotation_iteration_20261010/complete_reference_supplement_v1/deployment_metadata_v1/deploy_metadata.py start --zip /home/inspur/aic_video_work/annotation_iteration_20261010/complete_reference_supplement_v1/deployment_metadata_v1/metadata.zip --manifest /home/inspur/aic_video_work/annotation_iteration_20261010/complete_reference_supplement_v1/deployment_metadata_v1/manifest.json --expected-manifest <实际manifestSHA> --expected-acceptance <实际acceptanceSHA> --root-authorize-start'
```

该显式 flag 是 ROOT 动作授权，不由 preparation 自动追加。启动前重核全部输入/lock，所有既有 pipeline/train/evaluate/candidate/native_inputs 输出目录必须不存在。`nohup` + 独立 session + `python -B`，stdin `/dev/null`、offline/no-user-site 环境；不改 HOME 或现有代理。x写 `start_attempt.json`、`startup.json` 和 `pipeline.nohup.log`，保存实际 PID、`/proc/PID/cmdline`、lockSHA。启动成功仅为 `STARTED_NOT_VALIDATED`，训练、质量、426和ZIP结果继续以 unchanged pipeline 自然终态为准。共享GPU动态准入仍归 pipeline 的既有 shared-runner，无新增固定资源门。
