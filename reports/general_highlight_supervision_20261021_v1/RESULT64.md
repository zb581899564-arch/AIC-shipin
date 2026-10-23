# 今晚Goal交付：两份窄域路由新候选，40.47原包保持

已实际交付两份新的Windows ZIP，线上分数均UNKNOWN，没有自动官网提交。此处完成的是本轮2–3份候选的交付目标，不是证明突破40.47或解决通用高光选择。新非竞技LVSum、整源语音、原作者QV47等固定配方仍STOP，失败、成功、raw和费用保持；没有拿这些失败配方直接封包。

采用已得到外部收益支持的固定窄域路由：原I3D K400分类头整源平均概率的top1属于事前固定四类时，采用冻结SportCLIP专家；其余来源保持40.47。没有根据测试画面、标签或官方反馈选择新类别、阈值或逐源开关。只有一条已曝光的外部跳水录制提供强原TIME及完整40.47参考对照，不能称新盲测或普遍提分。32条外部非路由来源保持原输出，不证明误报率为零。

| 新候选 | 选帧数 | 相对40.47实际变化 | Windows ZIP大小 | SHA256 |
|---|---:|---|---:|---|
| SPORT_ROUTE_RERANK_8B | 123506 | 11源，新增724/移除724；每源总选帧数不变 | 384575B | f9bd8474b07365893498d27b16c16fa21f5e7ea677e37e125b2437c50f455a6f |
| SPORT_ROUTE_REMOVE_8B | 123479 | 3源，仅移除27帧 | 384482B | 85778a086f3fb0152947ece40b8dc258c7fef717b40519fe3e23fd4f7b0fabbe |

两者均完整426条、无空源；本轮12源触发路由。非路由来源逐帧保持，所有保留的原帧框完全相同；新增重排帧直接采用已验收的连续原生空间场。实际全部主辅8816809946参数（8.816809946B），真实模型计数与声明一致。模型返回、独立CPU分类/专家算术、原生PTS与分组、策略重放均通过；两份分别通过冻结独立11strict、单JSONL、CRC/member SHA及Windows大小/SHA/内容一致性。与本地55份完整历史交付及彼此的真实预测身份不同，不靠model_params或ZIP元数据制造差异。

全量3870个native64单元/234159原生帧的真实CPU输入完成，采用60的97份成功、62只补329源；特殊SHA绑定色彩格式沿用40.47原有转换，不改预测。唯一`semantic_sport_expert_route426_20261022_remaining62`自然completed/exit0，43.195088秒，唯一GPU账本一致，0新8B调用/0训练。全部首次独立CPU复核完成后，按登记白名单释放本阶段自有/dev/shm临时RGB/groups，原媒体、模型、输入身份、raw和复核保留。60原失败、57末标记检查失败及59显式CPU采用不回写、不重跑。

封包前已获取当前官网正文、5307通知和通知目录，并核当前通知三附件URL与既有完整阅读一致。此次没有重复下载PDF，也没有声称再次核验当前PDF全部字节。规则解释不是组委会特别许可；全模型≤9B、来源/用途披露、测试保密和不得标注训练/反构规则继续适用。

Windows实际接收前核两端EasyTier同一对peer、UDP cost1、同下一跳、双方p2p_only，以及WLAN/eno2物理路由；127.0.0.1:22022实际由原EasyTier进程转发到Linux。只接收两个最终ZIP及短回执，没有媒体/tensor/raw往返，没有修改连接/路由/服务。完成后的原生结果短回执6704B与Linux字节/SHA一致。CONTROL5原start_ticks491630308仍T，未发信号；本阶段实际活动命令为空。

交付路径：

- `G:\ai\AIC视频\deliveries\SPORT_ROUTE_RERANK_8B_20261022\candidate_SPORT_ROUTE_RERANK_8B.zip`
- `G:\ai\AIC视频\deliveries\SPORT_ROUTE_REMOVE_8B_20261022\candidate_SPORT_ROUTE_REMOVE_8B.zip`

建议优先看重排版；删弱版仅27帧，属于极小修正，不应期待大幅跃升。也不能因为改动少就擅自扩类别或调阈值凑第三包。40.47基线384630B/SHA b37c4a2e6593fc800f54ecce2f860fee5e7d5dc74e17ce280f9ee6722afbccd3在Linux与Windows均保持。

本地权威交付回执：`reports/overnight_candidates_20261022_v1/windows_delivery64.json`、`accepted_runtime64.json`、`short_receipt_identity64.json`及`direct_delivery_route64.json`。Linux权威终态分别在`routing_production62/model_and_selection_completion.json`与`routing_package63/completion.json`。Goal工具终态另见`goal_completion64.json`；不由本说明冒充工具状态。没有新定时任务。
