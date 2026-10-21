# I3D＋UMT留域小试实际结果：未通过，不全量

已按本轮“换可落地公开数据”的授权完成真实小试。SumMe原作者入口本轮Linux直连HEAD成功，复用原作者已验收25个WebM与人工MAT；VideoXum复用已接受的8来源。没有继续查两条YouTube，没有新增模型/视频下载，数据与计算均留Linux。

## 真实执行

- SumMe固定20源训练、5源开发；VideoXum8源整域不参与本新UMT拟合。33源都有历史项目曝光，不称新盲测。
- 33来源、2240个native64时间单元全部通过新RGB/原生时轴输入验收；复用原4个成功I3D单元，新提取2236单元，实际293个批次前向。首次完整RGB约2697461760字节。
- 固定预训练Meta RGB I3D-R50，UMT真实400前向/反向/更新，seed7312、lr1e-4、最终checkpoint。全部原评审摘要成员均值soft BCE，原生帧加权、逐源等权。训练首20步平均loss0.524394、末20步0.376104，下降不作为质量准入。
- 两个唯一共享GPU作业均自然completed/exit0，ledger逐项一致；分别收费21.501257和21.504466秒，合计43.005723秒。wrapper采样峰值分别1722MiB、676MiB，不当作精确Torch瞬时峰值。
- 新可导路径4项CPU契约通过；最终权重保存重载一致。开发/留域全部13来源、每源4种结果的独立CPU原生分组与全评审F1复算通过，0新模型/拟合。短回执5023字节，SHA见short_result14_transfer.json，与Linux逐字节一致。

## 留域结果

以下是人工摘要的时间代理，不是官网分数，也不是40.47生产包的完整外部复现。所有方案使用相同的每源选帧数：8来源共22012原生帧；新UMT相对既有控制改变10680个帧成员，输出没有全空崩塌。

| 方案 | 8源平均配对时间F1 |
| --- | ---: |
| 既有外部TIME/B控制 | 0.2717385990 |
| 新I3D＋UMT | 0.2603001886 |
| 同UMT、固定半序列内容移位 | 0.2590913590 |
| 相同I3D特征的固定ridge对照 | 0.2491030224 |

新UMT比既有控制低0.0114384105，只改善3/8来源，最差下降0.0606107742；真实内容仅比移位高0.0012088295。虽高于简单ridge，但不满足预登记的控制、内容、来源覆盖和最差退化门。开发5源UMT0.203900也低于既有控制0.302941，移位0.223900高于真实输入。

因此保持STOP_CROSS_DATASET_TRANSFER，不新增训练剂量、挑checkpoint或调留域阈值，不进入426或封包。选帧量完全相同且没有全空，说明本次失败不能归为阈值过严或输出空集；当前证据没有证明这套特征与监督能稳定改善内容排序。只否定本次固定配方，不泛化为全部I3D/UMT方法无效。

## 保留与限制

40.47原包仍384630字节/SHA b37c4a2e6593fc800f54ecce2f860fee5e7d5dc74e17ce280f9ee6722afbccd3，原8B/TIME及空间框没有修改。总保守参数8816809946≤9B。最终UMT24,856,937字节/SHA71052865ade76efb70541a174f85ca9fff3af8fc9d811f05a9b8c5eb206a34e7保留为失败研究证据，不作提交模型。

原07工程成功、旧来源失败和新12导入缺helper的0输入/0GPU失败均保留；13仅明确补依赖并首次续接，成功输入/模型不重做。TVSum虽然MIT直连可用，但包首仍要求Yahoo DSA，仅读取262144字节元数据后停止，没有假定已获用途许可。

末GPU184MiB/0%，新链自然结束，CONTROL5同start_ticks仍T、未发信号。新ZIP0、官网提交0，无新Goal/定时/作者或跨聊天消息、网络配置更改。

证据：Linux `/home/inspur/aic_video_work/i3d_umt_cross_domain_20261021_v1/crossdata12/` 内的registration.json、input_acceptance.json、source_input_lock.json、feature_acceptance.json、frozen_final.json、review.json、independent_cpu_audit.json、completion.json及两个唯一resource/ledger。本地仅保留protocol、短结果和一致性回执，不搬运RGB/特征/权重。
