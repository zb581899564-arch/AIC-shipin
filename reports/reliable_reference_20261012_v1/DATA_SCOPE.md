# 数据用途与语义范围

本轮20源来自已持有的QVHighlights公开视频材料，仅作内部、非商业的事实核查与时间边界开发参考，不作本轮新训练数据，不公开发布原视频或核查图板。

原作者仓库 https://github.com/jayleicn/moment_detr 的LICENSE段落明确：annotation files为CC BY-NC-SA 4.0，code为MIT。不能将代码MIT授权或原始标注授权自动说成每个原YouTube视频的单项许可证已核实。原视频由QVHighlights作者提供研究下载入口；当前逐条原视频许可证仍未逐项核实，未来训练或对外分发须另做适用范围核查和披露。

原数据人工标注是给定自然语言查询的相关片段，2秒粒度；三名标注者的0–4 saliency只覆盖相关片段。它可辅助检查查询描述的动作出现时段，不能拿不相关区间当普通，也不能作为0.25秒精确切点或无条件高光真值。来源 https://github.com/jayleicn/moment_detr/blob/main/data/README.md 。

本轮AI视觉复核不读取候选预测，标签保留AI_REVIEWED_SILVER与UNKNOWN。没有人类确认的结果不得改称HUMAN_GOLD。已有闭源弱标签不充当本轮可靠真值，旧正式质量FAILED仍保存。

源隔离证据见source_separation_audit.json：20个YouTube源组与已查704条训练记录无交集；20个源SHA与426条官方元数据（425个不同源SHA）无字节交集。语义或重编码重叠未获穷尽证明，20源仍为此前暴露的开发源。
