# 提交包—方案—官方分数

初赛与复赛分开记录。八份 ZIP 都已重新核验大小、SHA-256、CRC 和唯一成员 `predictions.jsonl`。成绩来源为原历史记录或用户报告/截图；不存在已确认成绩的候选填写“未确认”，不从前一包继承成绩。

| 阶段 | 包 ID | 官方分数 | 方案 | 下载 | 成绩证据 |
| --- | --- | ---: | --- | --- | --- |
| 初赛 | `initial-baseline-41.09` | **41.09** | 未微调Qwen3-VL单片段基线 | [ZIP](../submissions/qwen3vl_baseline_20260910/baseline_qwen3vl_20260910.zip) | [记录](../submissions/qwen3vl_baseline_20260910/score_history.jsonl) |
| 初赛 | `initial-multi-41.22` | **41.22** | 未微调Qwen3-VL多片段reader | [ZIP](../submissions/qwen3vl_multi_reader_20260910/aic-qwen3vl-multi-20260910.zip) | [记录](../submissions/qwen3vl_multi_reader_20260910/score_history.jsonl) |
| 初赛 | `initial-lora-43.48` | **43.48** | 历史Qwen3-VL LoRA reader | [ZIP](../submissions/qwen3vl_lora_reader_20260912/aic-qwen3vl-lora-reader-20260912.zip) | [记录](../submissions/qwen3vl_lora_reader_20260912/submission_record.json) |
| 初赛 | `initial-round5-unscored` | **未确认** | Round5 S2 temporal候选；上传记录为阻塞，无已确认新成绩 | [ZIP](../submissions/round5_s2_temporal_20260917/aic-round5-s2-temporal-20260917.zip) | [记录](../submissions/round5_s2_temporal_20260917/submission_attempt.json) |
| 初赛 | `initial-p2final-43.94` | **43.94** | P2-T2时间LoRA + 未微调Qwen镜头内稀疏空间锚点 | [ZIP](../submissions/round6_p2t2_qwen_sparse_20260920/round6_p2t2_qwen_sparse_candidate.zip) | [记录](../submissions/round6_p2t2_qwen_sparse_20260920/submission_record.json) |
| 复赛 | `rematch-4b-33.81` | **33.81** | A：4B/P2-T2 + native PTS兼容、受约束JSON、帧身份恢复 | [ZIP](../reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/delivery_A_SPATIAL_IDENTITY_01/recover_01/candidate_A_PTS.zip) | [记录](../reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/controller/official_score_A_33_81_20261006.json) |
| 复赛 | `rematch-linux8b-37.63` | **37.63** | B：Linux 8B区间JSON SFT最终5轮模型 + 同8B无adapter空间链；v3推理上下文修复 | [ZIP](../reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/b_sft8b_package_v3/delivery_01/candidate_B_8B.zip) | [记录](../reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/controller/official_score_B_LINUX_37_63_20261006.json) |

## 每包字节身份

### initial-baseline-41.09

- 原文件名：`baseline_qwen3vl_20260910.zip`
- 大小：191501 字节
- SHA-256：`2f8fe8620c81240cb41f3183ed9815e9fb303ab4e6cdee81a8559777baad7517`
- CRC：PASS；唯一成员：`predictions.jsonl`。

### initial-multi-41.22

- 原文件名：`aic-qwen3vl-multi-20260910.zip`
- 大小：196663 字节
- SHA-256：`6df46d39044e88ca5c41cc7b3af08e20256aadb5f1b3b23cf4aebab9e17a56f2`
- CRC：PASS；唯一成员：`predictions.jsonl`。

### initial-lora-43.48

- 原文件名：`aic-qwen3vl-lora-reader-20260912.zip`
- 大小：256242 字节
- SHA-256：`60188e903a5130a22592b2356f971a89abb33896d6e8fa043e3a5a005518ae9b`
- CRC：PASS；唯一成员：`predictions.jsonl`。

### initial-round5-unscored

- 原文件名：`aic-round5-s2-temporal-20260917.zip`
- 大小：153764 字节
- SHA-256：`e5df99b8c3d32ec6d495ef1aada2b869478f307884ebeedca3df76def36c3584`
- CRC：PASS；唯一成员：`predictions.jsonl`。

### initial-p2final-43.94

- 原文件名：`round6_p2t2_qwen_sparse_candidate.zip`
- 大小：128938 字节
- SHA-256：`31a3739c243303f3a3cf121f219c0092eae54ebe47084078e44a0070f65b3e8d`
- CRC：PASS；唯一成员：`predictions.jsonl`。

### rematch-4b-33.81

- 原文件名：`candidate_A_PTS.zip`
- 大小：266448 字节
- SHA-256：`5b8a186eefc2d162d65f76267979b57a6fbb94ea64fd26461f13270acb66e313`
- CRC：PASS；唯一成员：`predictions.jsonl`。

### rematch-linux8b-37.63

- 原文件名：`candidate_B_8B.zip`
- 大小：310902 字节
- SHA-256：`86bd5301f6f6771a8451b32063781e214cdd70245ae5513f2a767eaecb9ebe54`
- CRC：PASS；唯一成员：`predictions.jsonl`。

## 复赛证据说明

[Linux8B 原截图](../reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/controller/official_score_B_LINUX_37_63_20261006.png)显示 `37.63 / DONE`。完整时间、名次、包名不在截图中；包绑定依据用户“linux8b分数是这个”的指认及本次对话最近交付包。4B 33.81 来源为用户报告。两份原 delivery receipt 的 `uploaded=false` 记录的是当时未上传状态，保持历史字节不回写，后续用户提交成绩在独立 score record 登记。

复赛 A：426 视频、93,155 帧、13,022 空间锚点。复赛 B：426 视频、101,985 帧、13,947 空间锚点；比 A 官方成绩增加 **3.82**。初赛 P2-Final：174 视频、36,345 帧、5,065 锚点，43.94 比 43.48 增加 **0.46**。

Mac8B现已完整交付，官网尚未上传、官方分数未知。


## Mac8B 新交付包（2026-10-07）

- [candidate_MAC_8B.zip](../reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/mac8b_delivery_v2/delivery_01/candidate_MAC_8B.zip)
- 方案：Mac MPS训练64帧低分辨率8B区间SFT；Linux CUDA开发与推理，同8B空间基座；已交付未评分
- 官方分数：**未知，尚未提交/评分**。
- 426视频 / 101880帧 / 14007空间锚点。
- 大小：300152字节；SHA-256：`7f49ff90b5a21fd71a6036d8da0a1b78f3ab9c1d900ab2f81bc1f319e9d4533d`。
- [本机交付收据](../reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/mac8b_delivery_v2/delivery_completion.json)；[独立严格验证](../reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/mac8b_delivery_v2/delivery_01/local_independent_validation.json)。
