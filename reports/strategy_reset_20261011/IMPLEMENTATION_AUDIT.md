# 37.66 实现只读审查证据

本轮不运行模型、解码或processor，不查看复赛图像，不修改任何冻结管线。以下为实现可确认项，不能用于推断官方分项损失比例。

## 空间尺度与输入

执行根：`G:/ai/AIC视频/reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/`。

- `b_score_aligned_package_v4/spatial_baseline.py:113–137`，compute_crop_size根据原图宽高与target ratio生成最大可容纳整数宽度；宽源取floor(H*tw/th)，其他取W。函数不接受模型预测尺度。
- 同文件`:140–155`，center_to_box将中心转换为左上角并clamp，宽度保持cw。中心预测准确也不能生成更紧的框。
- `b_score_aligned_package_v4/production.py:177–183`，真实路径predict_focus → parse_focus_norm → compute_crop_size → center_to_box。
- `spatial_baseline.py:382–398`，提示为单帧与target ratio，输出center整数0..1000。没有尺度候选、事件描述、邻帧或时间适配器信息。
- `b_score_aligned_package_v4/field_contract.py:170–176`，同镜头内插值xyw；同源宽度固定，线性插值/PCHIP不能补出未表达的尺度。
- 原空间源场先于时间筛选建立；这是合法的时间独立缓存，不能把它说成时间选择后的错误稀疏场，也不能把复用成本记为0。

改进空间应先验证是否需要w小于最大宽度，不能只调center或平滑。新同8B多候选是方案，不是已上线行为。

## 历史对照的实际限制

- `b_boundary_diagnostic_v1/diagnostic_completion.json`：16事件、42个真实32B上下文调用；全部上下文唯一重叠仅3事件，独立弱方向2事件；外部弱event macro delta=-0.11320021399718093。工程失败0不等于边界可靠。参考覆盖/语义真值UNKNOWN，training_admitted=false。
- `teacher_semantic_diagnostic_v1/completion.json`：12条review，3 supported、9 rejected_or_uncertain；同教师一致性不是独立真值，学生训练未准入。
- `G:/ai/AIC视频/deliveries/SILVER24_SFT_20261011/evidence/independent_quality_receipt.json`：真实训练/评估已发生且独立CPU重构通过，但scientific_status=STOP_FIXED_SILVER_QUALITY_GATE_NO_426_NO_RETUNING。锁定macro F1增0.0198626，四项门失败；不能重跑该配方或换锁定样本补考。
- `G:/ai/AIC视频/reports/annotation_iteration_20261010/next_candidate_diagnostics_v1/RESULT.md`：四个GNMC静态16:9只提供几何上限，缺实际同源B框和合格双比例视频构图参考；不能据此宣布空间候选质量通过。

上述32B/B历史对照各自输入、提示与参考不同于37.66完整双窗，因此用于排除无依据重复，不当作37.66官方误差统计。

## 时间、锚点与已完成聚合审查

- `balanced_two_window_risk_v3/bw_native.py:11–23`：最多64帧，整数floor均匀序号采样含端点；原恰好两个连续窗且总域30–60秒才精确Fraction中点均分，无重叠。
- `balanced_two_window_risk_v3/bw_attempt.py:23–53`：原B、greedy、0–5段grammar生成区间；`packager.py:39–69`选区间内全部原生源帧。没有逐帧重要性分数或置信度阈值；已读输入无音轨。
- `b_score_aligned_package_v4/production.py:102–126`：相邻源帧直方图距离/灰度差分切镜头；`baseline_a_pts_v1/vendor/p2j_core.py:123–159`：每8个源帧设锚点、保留末帧，按帧序号线性插值xyw。
- `controller/SG8_scientific_stop_acceptance_20261009_summary.json`：confirmation均值-0.0026950569、全8组-0.0023075514，正确认组3/所需4，固定门失败，未进入新426。只否定该次有限路线，不推广成所有PCHIP无效。
- `controller/NRA_scientific_stop_acceptance_20261009_summary.json`：104弱参考均值+0.0028675084，expanded72为-0.0113707974，CI跨零，固定门失败；改采样对齐没有支持继续扩大投入。
- `controller/REMAINING_MECHANISM_READONLY_AUDIT_20261009_summary.json`：112旧raw均被规范grammar接受、纯空白拒绝0。自由解码对照仍有耦合，已观察开发集，不能宣称放松grammar已证实提分。

子代理只读审查已完成，未改文件、看426图像或启动计算。density/globalcontext最终STOP聚合未在该子任务详读，不补其统计结论。原始37.66格式验收只引用既有回执，不重跑成功生成或验收。
