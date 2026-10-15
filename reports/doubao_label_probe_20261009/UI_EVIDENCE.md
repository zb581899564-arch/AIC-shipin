# 豆包工作客户端操作证据

2026-10-09，Windows Doubao 工作任务“本地视频标注小试（豆包2.1 Pro）”。模型选择器明确显示“豆包 2.1 Pro”，仅核验 UI 选择，不能独立核查后端权重版本。

通过 computer-use 的 sky 原生窗口操作，未控制当前 Codex 窗口。sky 返回的 app 标识有误，因此另外只读核验：窗口17959898属于 Doubao.exe（PID58984），可执行文件 D:\软件\Doubao\app\Doubao.exe；窗口画面及标题为豆包。进程身份是当时快照。

本地文件请求和附件请求的原始结果分别保存 raw/native_v1、raw/native_attachment_v1。Read 工具拒绝读取 binary .mp4；附件入口虽接受视频卡片，但模型报告只有本地文件引用，没有实际解码帧。两次均不能据此产生负标签。

raw/image_v1 为模型误用旧 antigravity 根目录的失败记录。展开实际“已查找文件”返回，确认为旧根路径，不是本轮图片目录缺失。明确纠正后 raw/image_v2 原生图片 Read 成功。

本轮逐项展开 image_v2 的工具分组，实际窗口中显示：

- “核实图片读取情况”：本轮 input/keyframes_v1/k00.png、k01.png、k02.png、k03.png 已读取。
- “核查图片内容情况”：同一目录 k04.png、k05.png、k06.png、k07.png 已读取。
- “明确拼图网格规格”：本轮 input/timeline_v1/timeline_00.png 至 timeline_03.png 已读取。
- “记录指定片段”：timeline_04.png 至 timeline_07.png 已读取。
- “记录指定片段信息”：timeline_08.png、timeline_09.png、timeline_10.png 已读取。
- “记录指定时间范围内容”：timeline_11.png、timeline_12.png 已读取。

共8张原图、13张拼图的真实工具条目均检查了正确根路径，非仅依赖最终回答的读取声明。工作请求自然结束后停止按钮恢复话筒。

最终落盘 image_v2：18段粗高光、8帧×2比例共16框。写入有工具失败和一次6条中间文件，模型后续补齐8条；验收在请求自然结束后执行，未将中间文件作为完整结果。

独立视觉检查发现竖屏框问题，于同一任务提交 crop_review_prompt.txt：只让模型读自己的8张实际裁图和原图，再输出新 image_v3，不提供 Gemini 输出或人工主体坐标。固定比例几何限制已提供。它收到的纠错意见属于人为提示，因此此轮不是独立盲评。

约15:23–15:27逐项展开复核工具分组：“分析复核裁切初稿”显示manifest与review_k00/k01/k02；“复核裁剪框问题”显示review_k03/k04/k05/k06；“复核图裁剪校正”显示review_k07。全部路径为本次input/crop_review_v1。新文件实际写入后原生Read再次检查，UI停止按钮恢复话筒，自然结束。
