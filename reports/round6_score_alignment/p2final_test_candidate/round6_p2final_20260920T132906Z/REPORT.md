# P2-Final 测试集自动推理与候选打包报告

状态：`PACKAGED_NOT_UPLOADED`  
run_id：`round6_p2final_20260920T132906Z`  
范围：用户已授权比赛测试集本地自动推理与打包，明确暂不上传。

## 结论

已生成一份可供用户后续手动上传的候选 ZIP。候选包含 174 个视频、36,345 个预测帧，内置严格校验与冻结 P1a/P2 严格 loader 的独立复核均通过。ZIP 只包含根目录下的 `predictions.jsonl`，没有其他文件。

- ZIP：`package/round6_p2t2_qwen_sparse_candidate.zip`
- ZIP SHA-256：`31a3739c243303f3a3cf121f219c0092eae54ebe47084078e44a0070f65b3e8d`
- `predictions.jsonl` SHA-256：`7b65d3f65ad9a75819e1b181fdd0bb297ca9c63970f519919bb31882e3396bc3`
- 上传状态：`false`
- 官方分数与排名：`NOT_AVAILABLE`

格式与工程通过不表示模型质量或官方提分已通过。本阶段没有官方 evaluator，也没有读取测试内容作人工判断。

## 冻结协议与实际规模

时序侧使用 P2-T2 最终 adapter，SHA-256 为 `c9bf3754a05a42d69ee8c4d11f56c41346d927094fd643863f0cb55626b8e6a0`。推理采用 30 秒非重叠窗口、`ceil + [start,end)` 帧映射；203 个窗口全部合法，0 个无效窗口，最终选择 36,345 帧，174 个视频均为非空预测。

空间侧固定为未微调 Qwen3-VL-4B，同一套 CPU 镜头门阈值为直方图距离 0.35、灰度 MAD 0.18。398 个镜头段按首尾帧和最多 8 帧锚点间隔生成 5,065 个同帧模型调用，其余 31,280 帧只在同一镜头内线性插值；空间模型调用减少 86.0641%。最终比例为 119 个 16:9 视频和 55 个 9:16 视频。

生产链明确禁止并实测为 0：跨镜头框复用、无界最近框复用、弱 ROI 注入、旧比赛测试框、中心框静默回退。

## 解码身份修复

首次 5,065 锚点作业中有 154 行因 `decoded frame identity changed` 失败，这些行未调用模型，失败输出原样保留。随后只处理这 154 行：

- 136 行通过顺序 OpenCV 解码恢复真实解码顺序帧；
- 18 行均来自视频 97。该视频带 `color_transfer=log316`，OpenCV/libswscale 转换得到不稳定缓冲区；Decord 对指定帧三次复开解码的像素哈希一致，因此只对视频 97 的相关选中帧改用 Decord；
- 定向修复后 5,065/5,065 输出为 `MODEL_OK`，0 fallback；
- 原有 4,911 个有效 JSON 对象逐对象一致，0 变化；
- 修复没有调整时序结果、镜头阈值、空间提示词、锚点间隔或候选门槛。

修复输出 SHA-256 为 `ecc1d7d6295e88ca3603d490ae1eeb9945a5ee2ca7456c5af1a10b64af1705f6`。独立检查见 `evidence/repair_output_verification_v3.json`。前两版检查报告保留：它们错误地要求修复输出携带旧解码哈希，属于验证器口径错误，不是模型或候选失败；最终 v3 改为核对冻结修复清单与请求哈希。

## 合成与双重校验

合成报告 `evidence/composition_report.json`：

- 174/174 视频；36,345/36,345 选中帧完整覆盖；
- 5,065 个 `QWEN_ANCHOR_SAME_FRAME`；31,280 个 `SHOT_LINEAR_INTERPOLATION`；
- missing 0、extra 0、illegal 0、cross-shot reuse 0、silent fallback 0；
- provenance SHA-256：`0200d3221f51786fc61df670fc77df25a8ae35b922b715583a41705310b73a2f`。

第一套打包校验 `evidence/package_validation.json` 检查了 JSONL 结构、视频集合、帧范围、重复帧、整数框、画幅边界、目标比例、ZIP 单文件与回读哈希，状态为 `PASS_STRICT_FORMAT_AND_PACKAGE`。

第二套独立校验 `evidence/independent_validation.json` 使用冻结的 P1a/P2 `aic6.scoring.load_predictions`，并独立核对选择帧集合、provenance 与预测框逐项一致、来源白名单、帧排序和 ZIP 回读，状态为 `PASS_INDEPENDENT_STRICT_VALIDATION`。结果为 0 issue、0 duplicate、0 missing、0 extra。

## 资源

P2-J 完成后累计为 16.890870 GPU 小时。本阶段资源账本计费：

| 作业 | 计费秒数 | 结果 |
|---|---:|---|
| P2-T2 测试时序 174 视频 | 999.462 | 成功 |
| 首次 5,065 锚点推理 | 3,726.928 | 154 个解码身份失败，模型对其未执行 |
| 154 锚点定向修复 | 121.126 | 成功 |

阶段新增约 1.346533 GPU 小时；项目累计约 18.237403/24 小时，剩余约 5.762597 小时。最高采样显存：时序 15,388 MiB，空间作业 9,070 MiB。结束时 GPU 空闲、无活动锁。远端文件系统剩余约 141 GiB。

## 边界与下一步

本阶段未上传、未打开排行榜、未取得官方分数；没有把严格格式检查写成提分证据。用户可在决定提交时上传冻结 ZIP。上传属于新的外部写操作，本报告不授权自动执行。

远端 154 帧修复用的 `.npy` 中间缓存约 807 MiB 留在本阶段独立目录，用于复核；本地仅同步清单、哈希、模型输出、provenance、报告和候选包，没有复制该缓存。原始测试视频、旧模型、旧 adapter、历史报告与提交包均未修改。
