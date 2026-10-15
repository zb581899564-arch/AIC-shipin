# 下一候选诊断实际结果

CPU工程验收完成，下一候选质量准入仍被真实参考缺口阻塞。本目录没有新的提交ZIP。

- W01发布TSV/MAT的20×3896评分逐值相同，publisher均值/nframes一致；899原生帧内143次评分变化/14个序号全部在2秒格边界。不是高光边界或AIC目标等价证明。
- 原B登记SFT 724窗/704父样本/602原始源；固定24窗的12源ID与媒体SHA均0匹配。仅排除登记SFT的直接匹配，不恢复盲测资格。
- 开放GNMC四dev最大整数宽度的最佳位置IoU上限依次0.951748、0.602094、0.498462、0.915703；后三项最佳-最差精确为0，无法区分中心。实际模型框未提供，actual IoU与center gap保持null。
- 6项测试实际通过；160个固定随机几何样例的最大/最小值与独立位置穷举一致。独立审查另外验证966最大值样例/34非法宽度拒绝，后续只读确认新增最小值公式。
- 首版TSV读取范围声明过强，原报告保留，ENGINEERING_ERRATUM.json已实际落盘。B曝光首实现混淆clip group与原始YouTube source，失败记录保留，按原合同修复。

## 最小缺件

时间：完整、任务匹配、独立裁定且学生可观察的取舍与边界。原冻结训练/锁定质量门不变；现有重要性分数、叙事提案和四图事实不能自动补成KEEP/NO。已有视频可作为新增独立标注的输入，不必要求用户重新上传媒体。

空间：获准使用的非测试双比例视频构图参考，独立性与source/frame/PTS完整绑定，以及固定比较帧上的原B输出。GNMC仅静态16:9，本次量化不能外推复赛；弱框不能升级为真值。

当前已有材料核查已补齐可证的发布包一致性与原B登记SFT身份信息；其余需要新增独立标注/合格参考阶段，不能靠扩大训练或重复制包解决。

37.66保底包SHA保持07730c9e02e68d1a1ce54e7ef5a8aa616346cf8f2f8d78426ed36bc3eb481496；本轮模型/GPU/optimizer/426/传输均0。Pro6/8未调用。

## 复现

使用既有slot6_silver24_v1/cpu_env/Scripts/python.exe -B。几何与时间工具的输出使用独占创建，不覆写现有成功回执；复现应指定新的输出路径。
geometry_diagnostic.py --manifest ../../round6_score_alignment/p2r_reference_gate/round6_p2r_20260919T154701Z/pilot/gnmc/selected/dev_manifest.jsonl --output NEW_PATH
temporal_reference_diagnostic.py --root G:/ai/AIC视频 --output NEW_PATH
audit_B_exposure.py --root G:/ai/AIC视频 --output NEW_PATH
python -B -m unittest test_geometry test_temporal -v

完整逐项缺件见reference_gaps.json；当前身份与验收见acceptance_v2.json，初版acceptance.json保留。传输解码错误没有被记作研究STOP，也没有重启后台进程。

最后独立审查确认原B completion当前SHA正确，但要求入口在读取前固定该SHA。代码已加入断言；acceptance_v2.json追加绑定修订代码和原回执。已成功的时间/空间/曝光诊断均只引用，不重跑。这个工程收紧不改变数据、结果、质量门或生产。
