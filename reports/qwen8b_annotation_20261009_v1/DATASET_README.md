# Qwen8B 标注前置数据 v1

这批数据使用本地 TVSum50：50 个视频、10 类，每条视频固定抽取 12 张原生帧，共 600 张。每帧标注 16:9 与 9:16 两个比例。裁剪由 Codex 直接查看源图、给框、查看实际裁图后复核。Gemini 通过 agy 原生读取 MP4，另行给出视频高光候选。

## 裁剪结果

600 张抽样帧的 1200 个比例任务均有记录。当前选定版本中有 **679 个 PASS、496 个 UNKNOWN、25 个 REJECT**。训练文件仅包含 PASS；UNKNOWN 和 REJECT 不作为负例。

| 文件（相对本目录） | 行数 | 用途 |
| --- | ---: | --- |
| `exports/codex_crop_v1/labels.jsonl` | 1200 | 全部原始目标、框、状态、源身份、裁图和复核依据 |
| `exports/codex_crop_v1/crop_sft_train.jsonl` | 531 | 完整有效训练集，40 个视频；横框 426、竖框 105 |
| `exports/codex_crop_v1/crop_sft_validation.jsonl` | 148 | 完整有效验证集，10 个视频；横框 107、竖框 41 |
| `exports/codex_crop_v1/crop_sft_train_nonidentity.jsonl` | 143 | 去掉“保留原图不裁”的样本，37 个视频；横框 38、竖框 105 |
| `exports/codex_crop_v1/crop_sft_validation_nonidentity.jsonl` | 76 | 对应的非原图验证子集，10 个视频；横框 35、竖框 41 |

先用非原图子集做裁剪任务的小规模训练准备更合适。完整集合中 460 条横框就是保留整个 16:9 原图，直接全部混用会让这些简单样本占大多数。非原图子集保持原来视频划分，没有重复采样或重新标注。

`split.json` 在生成标签前固定：每类 4 条 train、1 条 validation，合计 40/10。同一个视频的帧和两种比例跟随同组。验证标签也来自模型及模型自检，不能当人类金标或官网质量分。

## 训练行与坐标

每条 SFT 行包括 `id`、`source_id`、`source_group`、`images`、`messages`、`label_record`。`images` 指向无框、无坐标网格的原生 PNG，助手输出为：

```json
{"box_xyw":[x,y,width]}
```

全部为原图整数像素；左上角为 `(x,y)`，高度由 `width * ratio_height / ratio_width` 精确推导。坐标以顺序解码帧和真实 PTS 绑定，不以缩略图或四舍五入后的帧率定位。后续训练程序读取 `images` 路径及 `messages` 即可；迁移目录时需显式重定位图片路径。

这是**新的像素裁剪框任务**。现有生产模型的中心点输出与 decoder 没有改动，不能把这个文件直接塞给旧目标的训练入口而不适配。

## 高光结果

实时状态在 `gemini_progress.json`。已完成的原回答及原生视频工具回执保存在 `raw/gemini/<source_id>/attempt_*/`；成功回答不重复调用，不覆盖旧回答。失败、超时钟和缺少输出的尝试保留原证据，另开新版本重试。

`exports/temporal_event_candidates.jsonl` 保存 KEEP/UNKNOWN 候选，并用完整 `native_pts.npz` 将候选区间关联到顺序解码帧。映射精确不代表教师边界精确：内部采样覆盖和所报时间仍缺少逐帧独立证明。未标区间不补成负例；完整时间训练目标当前为 **0 条**。

已发现 `37rzWOQsNIw` 的部分事件与实际抽样帧不匹配，记录在 `temporal_quality/37rzWOQsNIw.json`。原回答和结构通过回执保留，该源的时间标签标为不可进入训练；裁剪标签使用原生源帧，不受影响。其余高光目前仍是待质量核验的模型候选。

豆包原稿由用户负责，保存在独立目录；本批训练集选用 Codex 已复核版本，未与豆包或 Gemini 的另一个裁剪版本重复拼接。

## 已完成的核验

`exports/codex_crop_v1/independent_audit.json` 独立核对了全部 50 个 MP4、600 张源 PNG、完整 PTS 文件、原稿与复核 SHA、坐标、比例、分组和 SFT 输出。704 张候选实际裁图（含被拒框）均与原图指定区域 RGB 像素相同；679 条有效训练/验证目标无重复，同源组无交叉。

`exports/temporal_independent_audit.json` 核对已完成高光的原生工具路径、实际 CLI 终态、回答 SHA 与事件范围。它确认输入与输出链路，不确认连续观看或高光质量。

人工 TVSum 重要性没有暴露给教师。两条视频 `Se3oxnaPsz0`、`WG0MBPpPC6I` 的原生帧数与人工向量长度各差一帧，人工序号标签未强行对齐。现有元数据的源 ID/SHA 比对没有匹配，仍不宣称排除了所有转码或局部重复。

本轮只做本地标注和数据准备，没有启动微调、GPU、远端上传或新比赛推理。

四个代表样本的原生像素对照位于 `exports/codex_crop_v1/representative_native_crops.png`，左边为原图、右边为实际竖裁，分别展示车轴操作、奔跑、兽医与犬、食物制作。这张图用于查看选框效果，不代表整体质量分。
