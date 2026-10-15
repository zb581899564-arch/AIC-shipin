# 为什么群里说Gemini标得好，而本项目仍在40分段

现用TIME适配器这批训练标签没有使用Gemini。现存教师语义审计中808条全部声明为`api_doubao_doubao-seed-2-1-pro-260628`，时间与空间观察频率均1fps，schema为弱训练标签；实际训练704个父片段、602个来源、724个窗口、5轮、227次更新。训练报告明确`negative_targets_created=false`，教师审计的训练/开发`teacher_negative_rows`均0。未选时间仍是UNKNOWN，不能补成明确普通或负例。

这证明当前标注来源和监督构成，不能证明豆包一定比Gemini差，也不能证明缺负例是唯一瓶颈。没有同一组合法外部人工参考上的Gemini/豆包受控对照；群里反馈不能当作本项目的实验结果。

有证据支持的不足和仍待证实的推断：

- 监督以非空区间提取为主，缺少明确观察后不选的目标。它可能强化“给出一个片段”的偏好；此前复核全KEEP、补召回伴随精度损失，与这一怀疑相容，但并非因果证明。当前新相对排序避免依赖绝对KEEP判别，另用新4源确认约束删除风险。
- 教师1fps观察和弱标签并不等于原生逐帧高光/双比例构图真值。短暂动作、反应以及细致裁剪可能无法充分监督。后续应在合规外部数据上分别比较教师与8B学生的逐任务表现，不能仅换教师名称或扩大训练量。
- 外部VideoXum参考是事件文本相关的人工摘要代理；本项目正式提交还包含原生高光帧和空间框。本轮参考结论只覆盖声明范围，不能把代理F1当正式分数。旧空间基线的最大合法宽度/中心输出也有能力限制，时间修改不会自动解决它；此前统一缩框失败仍保留，不根据榜单继续扫尺度。

今晚的任务不是重新打标或训练：使用同一个8.78245912B物理模型完成相对删选与三类语义补召回。最多三类探索不做离线效果筛选，明确未知；两个删选方向必须首次新4源确认通过。原40.46 ZIP保持。未调用Gemini或其他闭源API处理测试集，未自动官网提交。

本轮实际证据：

- `reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/data_audit/teacher_semantics_summary.json`
- `reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/temporal_sft8b_full_v1/train_report_completion_01.json`
- Linux本轮`relative_dev_comparison_04.json`及`policy_comparison_08.json`：比较已曝光开发数据，不是新确认或官方提分。
- Linux本轮`production_unique_09`、`relative_confirm/control_14`：实际执行进度与未来首次确认，以真实终态为准。
