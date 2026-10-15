# 文件夹原生MP4高光标注已跑通

Gemini 3.8 Flash High通过反重力内置 `view_file` 直接读取本地 `GsAD1KT1xo8.mp4`。UI中实际核对了manifest和MP4的Analyzed条目；本任务没有附加媒体，也没有提供预先抽帧PNG或旧标注。源视频145.3452秒、7,794,439字节，SHA与已下载原件保持一致。

原始输出已落盘：

- `G:/ai/AIC视频/reports/antigravity_label_probe_20261009/output/native_video_tvsum_v1/highlights.json`
- 同目录 `report.md`

共15段KEEP候选高光，区间并集合计60.0秒。结构、来源身份、时间非空和全区间不越界检查通过。详细字节SHA和实际验收见 `native_video_acceptance.json`，没有修正模型原始结果。

模型报告前20秒收到21张逐秒采样图，之后原生多媒体观察覆盖到视频末端，另记录47个观察时间点。我们已验证直接MP4读取成功；服务内部是否完整逐帧解码以及持续观察机制没有独立核实，不把47个时间点说成全源帧逐帧标注。

固定抽查第1、第8、第15个事件的开始、居中、末端三个原生源帧：可以看到相关的越墙、跃下石阶和穿栏动作。实际PTS和RGB SHA保留在 `native_visual_review/manifest.json`，拼图为 `native_highlight_review.png`。这是9帧代表性检查，不能据此给15事件准确率。第一段末端已包含下一镜头，说明区间仍是粗标；模型自报0.5至1秒边界不确定度也不是独立测得的误差。

后续高光标注输入方式：**直接让Gemini原生读取指定文件夹里的原始MP4**，使用 `NATIVE_VIDEO_AGENT_TASK.md` 的任务文案。空间构图可另做逐帧任务。当前真实逐帧小试48帧、96框也已完成；其构图效果与原始标签见 `annotation_pilot_01/GEMINI_RESULT.md`。

本次仍为标注和本地检查，没有训练、远端传输或官网提交。TVSum完整50视频已下载，本轮实际原生高光标注仅覆盖这一个视频。
