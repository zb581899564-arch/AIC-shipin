# AIC 数据审计报告

审计时间：2026-09-09（UTC 2026-09-09T14:34:56Z）  
脚本：`data_audit/audit_dataset.py`，版本 `2026-09-09.data-audit.v1`  
原始数据：`/home/inspur/aic_video_data`（只读）  
审计输出：`/home/inspur/aic_video_work/data_audit`，已复制到本地 `data_audit/`

## 执行命令

```bash
python3 /home/inspur/aic_video_work/data_audit/audit_dataset.py \
  --data-root /home/inspur/aic_video_data \
  --out-dir /home/inspur/aic_video_work/data_audit \
  --seed 42
```

脚本只读取 JSON/MP4 容器头，并只对标签引用的 MP4 计算 SHA-256；不会解码或导出视频帧，`teacher_signals`（包括 summary）不写入任何审计产物。

## 已核实事实

- `labels/train.jsonl` 共 987 条，JSON 解析错误 0；原始字段 `dataset_split` 为 887 train、100 val；`schema_version` 全为 `seed_weak_training_label_v1`。
- 987 条 `video_path` 均为空；`targetRatioWH` 均为 `[9,16]`。该比例是目标裁剪比例，不能当作 MP4 编码画幅。
- `videos/**/*.mp4` 共 11,576 个；PyAV 容器/视频流头部读取成功 11,576/11,576。实际编码尺寸以 534×300 为主（11,334 个），FPS 不是单一值，主要出现 29.9700、25、30、23.976 等；时长主要约 150 秒。
- `clip.source_vid` 均为非空字符串，按文件 stem 精确匹配到 912 条；75 条没有对应 MP4。没有用相似文件名或时间窗猜测替代缺失文件。
- 987 条 provenance 都带 64 位 `video_sha256`。对精确匹配到的 912 个 MP4 实际计算 SHA-256 后，912/912 与 provenance 值不一致；因此当前文件只能作为同名文件证据，不能证明它就是生成标注时使用的同一媒体。
- 去除 `clip.source_vid` 末尾数字 `_start_end` 后得到 863 个来源组。原始 train/val 在来源组层面交叠 26 组；原始 split 不能直接作为无泄漏划分。
- 数据目录中没有发现能证明“加工短片到原始长视频”的明确生成/对齐清单；`video_path` 为空也没有提供替代路径证据。任何时间轴或帧率变换均保持未证明。

## 候选来源组划分

使用 seed 42，先对来源组做固定随机排列，再整组分配到 train/dev/holdout。结果如下：

| candidate split | 来源组 | 标签行 | `trusted_identity` |
|---|---:|---:|---:|
| train | 694 | 789 | 0 |
| dev | 84 | 99 | 0 |
| holdout | 85 | 99 | 0 |

候选文件 `data_audit/candidate_groups.jsonl` 和 `data_audit/candidate_splits.jsonl` 的每一行都带 `candidate_only=true`、`do_not_use_as_training=true`。`candidate_split_leakage.json` 重新计算的三组交集均为空（zero group leakage=true）。这些文件只用于审查划分，不能填入训练入口的 `accepted_splits`。

## 训练准入结论

`data_audit/training_gate.json`：`passed=false`，`alignment_verified=false`。

准入阈值为可信 train≥200、dev≥50、holdout≥50。当前严格可信身份行数为 0/0/0，原因是 912 条 hash mismatch、75 条源文件缺失，且缺少加工短片到原始源视频的对齐清单；因此不生成 accepted split，也不把任何标签套到其他源视频。候选行不得触发训练。

## 产物

- `data_audit/audit_dataset.py`：审计脚本。
- `data_audit/video_inventory.tsv`：11,576 个 MP4 的相对路径、大小、PyAV 元信息；仅标签相关文件有 hash 列。
- `data_audit/labels_inventory.jsonl`：987 条脱敏结构清单、匹配/hash/元信息状态和候选分组；不含 teacher summary。
- `data_audit/anomalies.jsonl`：空 `video_path`、75 个缺失文件、912 个 hash mismatch、原始 26 组交叠。
- `data_audit/candidate_groups.jsonl`、`data_audit/candidate_splits.jsonl`：明确 candidate-only 的来源组计划。
- `data_audit/candidate_split_leakage.json`：候选分组零泄漏复核。
- `data_audit/training_gate.json`、`data_audit/audit_summary.json`：准入决定和摘要。

## 复核命令

```powershell
python3 -m py_compile .\data_audit\audit_dataset.py
Get-Content -Raw .\data_audit\training_gate.json
Get-Content .\data_audit\candidate_splits.jsonl |
  ForEach-Object { $_ | ConvertFrom-Json } |
  Group-Object candidate_split | Select-Object Name,Count
```

远端复核应使用同一 SSH 别名和只读数据根；审计写入位置保持在 `/home/inspur/aic_video_work/data_audit`。
