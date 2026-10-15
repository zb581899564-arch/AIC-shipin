# Qwen8B 本地训练准备 v2：选定版本

本版本用于两个独立 LoRA 先导实验：裁剪框和时间重要性评分。没有启动模型权重加载、GPU推理、loss前向或optimizer更新，不替换任何现有生产模型。

## 实际选定数据

|任务|训练|验证|来源|
|---|---:|---:|---|
|像素裁剪框|181条，40源|148条，10源|已复核的模型弱标签；训练含143条实际裁剪和38条保留原图的校准样本|
|时间重要性|314条序列，39源|89条序列，9源|48源的TVSum原始20人人工评分；固定2秒网格共6047张原生帧，每序列最多16张|

选定配置只有 `configs/crop.json` 和 `configs/temporal_fixed.json`。较早的整分和按人工分数变化取样版本留在原准备目录作诊断，不进入本传输包。所有视频保持原40/10划分；时间任务另外排除 Se3oxnaPsz0、WG0MBPpPC6I，因为原生帧数与人工向量各差一帧。没有补齐、平移或修改划分。

## 时间边界的实际结论

原Gemini 600条候选已逐条核对原生时间域并保存 disposition。输入和时钟合法不能证明事件语义起止正确；原37rzWOQsNIw已知错位，其余仍未经逐段语义验收。**600条Gemini事件边界均未进入训练目标，不宣称已全部精标通过。**

时间训练采用官方人工帧重要性，而非这些事件区间。原TSV与MAT文件的50源、每源20人工向量交叉一致。48源的原生顺序帧数、完整PTS与标注长度匹配，源帧按真实PTS核对，不通过 round(time*fps) 定位。每个固定 `[2k,2k+2)` 秒采样域选原生序号中点，目标是该帧20人的评分总和。采样不读人工评分变化，也不读Gemini候选。

目标JSON为 `{"scores_x20":[...]}`，每项20..100；除以20恢复原1..5均分，保留0.05分精度。这些域是输入采样域，不是人的动作开始/结束边界，不能把采样边缘称为精确动作高光边界。TVSum主观重要性也不等同赛题高光金标。

裁剪目标仍为 `{"box_xyw":[x,y,width]}`，原图整数像素；高度由目标比例推导，严格拒绝越界、非整数、比例不合法或格式错误，不自动修框。时间低分来自真实人工评分，不是给未观察域制造负例。

## 已通过的检查

- 独立从原TSV重新计算6047个选定帧的目标，核对图片SHA、图像解码、PTS、连续采样域与源划分。
- 实际全部329条裁剪和403条时间序列通过真实Qwen3VLProcessor的CPU预检。最大输入为319/1618 tokens，分别低于16384上限；助手目标非空。
- 真实图片的长短序列混合batch检查通过：视觉输入数量一致，padding与用户/图片token为-100，解码出的监督内容与目标JSON一致。CUDA未初始化。
- 解析器拒绝错误长度、布尔/小数评分、越界评分、越界框及非整数比例高度。评估入口的echo数据仅为程序检查，绝不是学生模型成绩。
- 现有Linux训练环境的Trainer、Qwen3VL、PEFT可导入。Windows使用已有torch_env做CPU预检，其未安装PEFT/accelerate，不将它宣称为本地训练环境。无新环境安装。

未加载8B权重、未计算实际模型loss、未做optimizer smoke step，故不宣称完整优化运行或成绩提升已验证。正式开训前仍须实时检查共享资源、确认授权，做有限首步观测，再决定继续；旧运行的资源快照不是持续准入。

## 入口与评估

`verify_bundle.py` 校验选定发布的全文件哈希。`train_lora.py` 默认仅做CPU预检；只有显式 `--train` 才加载权重并训练。两个任务分开保存adapter，初始配方为rank8、学习率1e-5、一轮，仅是未经质量验证的先导配方。没有自动重试、恢复或覆盖旧输出。

Linux示例（目录在获准上传与安全解压后才存在）：

```bash
DATASET_ROOT=/home/inspur/aic_video_work/datasets/qwen8b_annotation_20261009_v2
PYTHON=/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python
MODEL=/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/models/Qwen3-VL-8B-Instruct
$PYTHON -B $DATASET_ROOT/training_v2/verify_bundle.py --dataset-root $DATASET_ROOT
$PYTHON -B $DATASET_ROOT/training_v2/train_lora.py --config $DATASET_ROOT/training_v2/configs/crop.json --dataset-root $DATASET_ROOT --model $MODEL --output /home/inspur/aic_video_work/runs/qwen_annotation_v2_crop_preflight_001
$PYTHON -B $DATASET_ROOT/training_v2/train_lora.py --config $DATASET_ROOT/training_v2/configs/temporal_fixed.json --dataset-root $DATASET_ROOT --model $MODEL --output /home/inspur/aic_video_work/runs/qwen_annotation_v2_temporal_preflight_001
```

CPU预检完成目录不能复用作新训练目录。获准训练后选择独立新output并显式添加 `--train`，不得直接重复已完成的输出目录。实际8B权重的加载、首步loss与显存峰值属于下一阶段，未在这批准备结果中伪报为通过。

训练后 `predict_rows.py` 只将用户提示和图片送入模型，助手金标不进入生成输入。`evaluate_predictions.py` 检查完整ID集合，报告非法输出率、时间评分MAE/RMSE和逐源Spearman；裁剪IoU只衡量与模型弱标签的一致性。保留原图/实际裁剪要分别查看效果，不能只看总体loss。训练均分常数基线在独立审核回执中，MAE约0.5016、RMSE约0.5946，供模型比较，不是学生成绩。

本包仅含所选训练/验证图片、人工目标、配置、脚本、词表与检查回执；不含完整视频、模型权重、赛事测试输入或旧实验raw。当前只在Windows本地准备，未经新的大流量许可不上传Linux，不自动开训。
