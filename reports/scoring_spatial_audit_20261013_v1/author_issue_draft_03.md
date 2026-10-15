# 作者仓库询问稿：未发送

目的：补齐 LIVE-YT VC 的少量本地研究验证使用范围与 videoN 原始来源映射。拟发布到作者公开仓库 https://github.com/steven413d/LIVE-YT-VideoCropping 的新 Issue。只发送下方英文标题与正文；不发送队名、个人身份、模型权重、测试数据、预测、代码、成绩或私有文件。

Title: Clarifying evaluation-only use and original source mapping for LIVE-YT VC

Hello, thank you for releasing LIVE-YT VC. We are preparing a small offline cropping evaluation for a video highlight/reframing competition research project.

We would use only a limited subset of the original six-second study clips and sparse human crop annotations for local evaluation. We would not train on the data, redistribute videos or annotations, include them in a submission, or send them to an external model service. The resulting automatic cropping code would be evaluated separately on the competition data.

Could you clarify:

1. Is this evaluation-only, competition-related research use of the original `study_videos` and `video_bbox_labels.csv` permitted? Which data usage terms and citation/attribution requirements apply?
2. Is there a mapping from the released `videoN` identifiers to the original YouTube-UGC or LSVQ source identifiers? We need it for attribution and to exclude known source overlap.
3. Are `left`, `right`, `top`, and `bottom` source-pixel coordinates with exclusive right/bottom edges, and do `frame0`, `frame6`, etc. refer to zero-based decoded frame ordinals of the released clips?

Thank you.

状态：DRAFT_ONLY_NOT_SENT。只有用户明确批准这一公开 Issue 后才可发送；此前“去做”不被解释为外发消息授权。许可、来源映射未齐时不启动 LIVE-YT 媒体/标签获取或模型实验。
