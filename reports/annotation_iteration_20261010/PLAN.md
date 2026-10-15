# 主控接替Pro后的执行协议

用户授权：自行深度调研、与专门子agent讨论、修复、迭代至可提交ZIP，优先终端agy高光标注。网页Pro因电脑操作工具URL安全检查失败未发送，0次；本方案为主控裁决，非Pro意见。

现有最佳已由用户反馈37.66；保留原B权重、全部冻结历史/失败/raw/费用。已有TVSum pilot真实crop12/time20步，但空间合法0/148；时间matched61rows903frames MAE新.54297/base.54175/常数.48817，均不能作为晋升理由。

先不下载新数据：TVSum已有48源native帧与20人人工评分一致，39训练源/9验证源；9源已暴露，只叫development，不能冒充盲测。600旧Gemini候选语义边界未经验收，全部继续排除监督。

## 已冻结的第一阶段

独立TVSum image-score selector，保持scores_x20(20..100)、固定2秒输入网格、16有序images/row。新rank8、alpha16、lr1e-4、3epochs、batch1/acc4，语言qkvo LoRA、视觉冻结，maxpixels65536；全真实输入assistant-only mask，无截断，独立输出。仅一个预先指定最终checkpoint，不依据本轮dev调学习率/阈值或挑checkpoint。原pilot与基座在相同固定长度整数JSON grammar、相同真实输入全89row比较。grammar只保证格式，不证明质量。

主要报告source macro Spearman（常数为0并单列）与每源固定top15%帧的人类重要性效用、全分母合法率、MAE/基座/常数。top15%仅TVSum诊断预算，不自动移植到AIC。预定晋升研究门：全部89row合法、所有目标帧都参与；相对基座macroSpearman和top15%效用均严格改善，且至少5/9源Spearman改善。另做固定train-only视觉依赖对照（真图/置换图），不据dev结果换对照。门只决定下一阶段投入，非AIC金标/官方分保证。

agy先3个已指定train源，每源2个30秒短native MP4，保存顺序原生ordinal/PTS与片内时钟→源时钟映射；固定2秒候选格KEEP/REJECT/UNKNOWN，可见视觉证据和观察限制，不自由生成秒数、不称全帧看过。首/中/末原生帧独立视觉检查；出现实质错位拒该段，不平移修标签，不扩到50源。未观察不生成负例。这批teacher弱标签不进入本轮人工评分训练。

第二阶段取决于首阶段真实结果：如研究门失败，停止本版配方并保留失败，新训练不替换生产；交付本地37.66保底包并透明记录没有新候选。如通过，独立冻结与训练输入一致的时间选择器、train-only阈值（允许空），先非测试，再完整426；原空间源场按精确来源重用，不能把adapter接原B0视频prompt。质量为TVSum代理证据，AIC分仍未知；用户接受风险的新候选必须与保底明显区分。

所有GPU通过现有共享runner和唯一追加账本；实时资源/外部冲突决定准入，无固定资源阈值。新小量控制文件经在线Mac ProxyJump上传；新数据/模型/大ZIP传输仍需要专项流量许可。本轮不需要新大传输。没有官网提交、公开发布、生产替换授权。

最终交付ZIP必须唯一predictions.jsonl、完整426身份/比例、源native合法帧号、整数合法框、无重复遗漏、CRC/解压字节/SHA、独立核验；如保底则原字节引用并标识历史37.66，不伪称本轮新训练结果。

## 资料

Qwen官方微调框架明确区分image/video tags及实际输入，冻结vision的混合图像视频训练建议不能证明本项目配方有效：https://github.com/QwenLM/Qwen3-VL/blob/main/qwen-vl-finetune/README.md

TVSum作者数据说明是50个视频/每源20人人工重要性，摘要预算是一种研究协议，不是AIC高光金标：https://github.com/yalesong/tvsum/blob/master/README.md

独立agent最强反例：TVSum相对重要不等于AIC应提交高光；强制topk会把空高光视频变正例；16images与原native video/B0/segment协议三重迁移不能混套；同源多帧不是独立证据。
