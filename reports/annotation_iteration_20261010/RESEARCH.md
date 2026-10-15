# 调研与独立讨论结论

本轮用户明确让主控接替网页Pro，并开一个专门讨论子agent。Pro实际0次。主控和独立agent往返审查，未把agent意见当实验成功证据。

## 当前问题与优先次序

1. 时间身份和输出协议先于更多弱标签：600旧Gemini自由报秒候选中已有37rz内容错位，输入工具成功不等于事件时间准确。
2. 先使用已有人工评分，而不是新收低质weaklabels：48源完整native/人工向量对齐证据比当前自动标注更可靠；新agy短视频只做标注流程检验和未来弱监督准备。
3. 原pilot仅20优化步、lr1e-5，不能据此宣布8B不能学，但必须先完整比较基座/常数/源排序，不能只看loss。新的3epochs/lr1e-4是主控预先指定的一次实验配方，不声称Qwen官方保证这一学习率。
4. 学生train/infer保持同16images/scores_x20任务，禁止把它直接加载到原B0 native-video segment提示。空间crop本轮不同时换。

## 官方和论文资料

- Qwen官方微调入口区分image/video媒体标签、真实输入对应关系，并提供grounding格式示例和vision冻结配置；所用imagecollator和实际输入检查符合这一原则，但本项目脚本与官方整套框架不同：https://github.com/QwenLM/Qwen3-VL/blob/main/qwen-vl-finetune/README.md
- TVSum作者说明50视频及每源20人人工重要性，摘要的固定预算是研究协议；不能认为这些主观重要性等于AIC高光动作金标：https://github.com/yalesong/tvsum/blob/master/README.md
- Otani et al., CVPR2019, Rethinking the Evaluation of Video Summaries：作者发现旧摘要指标很受分段影响，并建议直接检查重要性相关性。我们因此按source macro排序、人类效用和native扩段效果一起报告，避免只优化常数可获益的MAE：https://openaccess.thecvf.com/content_CVPR_2019/html/Otani_Rethinking_the_Evaluation_of_Video_Summaries_CVPR_2019_paper.html
- QVHighlights原论文是query-conditioned moments+saliency，与不带query的AIC裁剪高光不是同一任务；适合作后续明确query任务的数据候选，本轮不盲目下载大型新包：https://arxiv.org/abs/2107.09609

## 独立agent质疑与主控采纳

最强反例：常数重要性降低MAE而排序为0；固定15%把无高光视频变正例；2秒中点不代表整个2秒动作；换image-score adapter回原B0构成输入、任务、解码三重迁移。主控接受：不造TVSum0分负例、不每视频强制topk、不换crop、不把弱标注当gold。

研究门完整89行全分母、按源macro Spearman/固定top15%效用，常数源记0，固定nativeordinal tie-break；至少5/9源排序改善且两macro正改善。另12个train-only hash预选16图行跨来源交换图，比较原目标NLL，正常图整体和多数更低才能视为有输入依赖。仅输入有影响不能证明高光质量。

source bootstrap CI和最差源退化完整报告，可能改善极小而CI跨0；不声称统计确定性。第二阶段阈值49只由训练评分q80决定，可空，并用完整human native向量对扩段选择评估，不凭排序门直接推426。

agy3train源6短clip，固定2s candidate ID且native PTS精确映射、无音频、声明有损视频派生，模型工具报告1fps不能当独立全域覆盖证明。首中末原生PNG人工式视觉检查仅是稀疏观察，绝不升级成逐帧全通过。若实质错位则拒该段、不平移修标签；本轮不把新weaklabels加入人工训练目标。
