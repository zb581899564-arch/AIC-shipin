# 豆包 2.1 Pro 本地视频标注小试

用户授权：用豆包工作客户端的 2.1 Pro 直接读取视频，测试高光片段和构图框，判断是否可与 Gemini 配合。仅进行标注与本地效果检查。

## 输入与固定比较范围

- 原始 MP4：`G:/ai/AIC视频/reports/antigravity_label_probe_20261009/input/native_video_tvsum_v1/GsAD1KT1xo8.mp4`
- 身份与视频元数据：同目录 `manifest.json`。
- 源：TVSum `GsAD1KT1xo8`，640×360，145.3452 秒。
- SHA256：`a195fc9d8e5330ee55c62dfc0a99eb5d130bf0444bb412992d1204eecd8f3a86`。
- 不向豆包提供 Gemini 输出、TVSum 人工重要性分数或已有构图标签。
- 先核实 UI 中实际模型为 2.1 Pro，再提交任务，不替换模型。
- 首先测试原始 MP4 的直接读取；明确区分本地文件工具读取、上传原生视频和无法读取。

## 高光任务

完整观察视频。选出有完整动作、明显视觉事件、适合跑酷高光剪辑的片段，排除仅有围观、闲聊和转场的片段。记录开始时间、结束时间、可见动作及边界不确定性。无法读取、无法观察或无法定位时如实记录，不能依据文件名推断内容。

输出原始 JSON，字段：`source_id`、`actual_model_ui`、`input_mode`、`actual_read_tool`、`observation_scope`、`events`。每个 event 含 `start_seconds`、`end_seconds_exclusive`、`event_type`、`visible_evidence`、`boundary_uncertainty_seconds`。

## 构图任务

给出构图裁切框，不是人物检测框。源尺寸 640×360；每个观察点分别给出 16:9 和 9:16 裁切，坐标用原始像素 `[x,y,w]`，高度由 `h=w*target_h/target_w` 推导。框必须在源图内。判断主体、动作关键部位和环境关系是否保留，不能只满足几何合法。

优先直接观察视频中的固定时间点：10.0100、10.276933333333333、10.8108、11.077733333333333、11.578233333333333、50.5000、86.2500、135.0000 秒。前五个点用于与 Gemini 已标样本对照，后三个点用于动作场景诊断。时间点观察无法精确定位时报告实际观察时间与不确定性，不伪造原始帧号。没有实际图像读取则记 UNKNOWN。

输出 `crop_keyframes.json`：`source_id`、`actual_model_ui`、`input_mode`、`frames`。每项记录 `requested_seconds`、`actual_observed_seconds`、`visible_content`、`crops`；每个 crop 包含 `targetRatioWH`、`state`（CROP/UNKNOWN）、`box_xyw`、`reason`。

## 保存与评价

原始回复保存在本目录的 `raw/`，不修正模型原始坐标或区间。直接视频读取受限时，保留原限制和原回复，再另做明确记录的抽帧诊断，不把抽帧成功写成原生视频成功。

分别评价：读取能力、时间区间结构、实际高光内容、构图裁切效果。模型互相一致不是独立正确性证明。当前测试未建立人工构图真值，不报告准确率。

最终状态：已完成。用户处理系统位置权限弹窗后，实测本地Read MP4及MP4附件两次视频输入失败；明确抽帧后，8原图/13时间轴拼图成功，产出18段粗高光和16框。实际裁图发现首稿漏主体，另读8张裁图反馈，完成image_v3复核16框；两版独立几何/原生帧身份验收通过，视觉仍有局限。完整结果见RESULT.md。未训练、未启动 GPU、未传输远端文件或修改主实验。
