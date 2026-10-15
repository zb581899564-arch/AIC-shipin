最新成绩反馈（用户截图与明确上传顺序，未独立登录官网）

| 上传顺序 | 方案 | 显示分数 | 截图打分时间 |
| --- | --- | ---: | --- |
| 1 | 起点细化 START | 40.43 | 2026-10-14 20:17:14 |
| 2 | 终点细化 END | 40.44 | 2026-10-14 20:17:16 |
| 3 | 双端细化 BOTH | 40.43 | 2026-10-14 20:17:19 |
| 4 | 高光复核 VERIFY | 40.46 | 2026-10-14 20:18:21 |
| 5 | 复核加双端细化 VERIFY_BOTH | 40.46 | 2026-10-14 20:18:23 |

VERIFY 与 VERIFY_BOTH 同为显示40.46，较此前D8用户40.44高0.02。相同两位小数显示分数不证明预测相同或未四舍五入的分数严格相等。原冻结实验基线/质量门与交付时点UNKNOWN不回写；当前记录VERIFY为较简单的同分参考，没有启动新实验。

以下为原交付时点记录。

5/5 本轮新提交包已交付

完成时间：2026-10-14 19:36:11 Asia/Taipei；原截止19:56:40。正式成绩与提升效果未知，均为按冻结协议生成的合理探索风险包，不宣称科学质量通过。

| 顺序 | 方案 | 新ZIP | 选中帧 | 相比D8新增/删除 |
| --- | --- | --- | ---: | ---: |
| 1 | 起点细化 START | [ZIP](G:/ai/AIC视频/deliveries/AIC20H_TEMPORAL_START_20261014/candidate_TEMPORAL_START.zip) | 121949 | +0 / -101 |
| 2 | 终点细化 END | [ZIP](G:/ai/AIC视频/deliveries/AIC20H_TEMPORAL_END_20261014/candidate_TEMPORAL_END.zip) | 122028 | +7 / -29 |
| 3 | 双端细化 BOTH | [ZIP](G:/ai/AIC视频/deliveries/AIC20H_TEMPORAL_BOTH_20261014/candidate_TEMPORAL_BOTH.zip) | 121927 | +7 / -130 |
| 4 | 高光复核 VERIFY | [ZIP](G:/ai/AIC视频/deliveries/AIC20H_TEMPORAL_VERIFY_20261014/candidate_TEMPORAL_VERIFY.zip) | 122002 | +0 / -48 |
| 5 | 复核及双端细化 VERIFY_BOTH | [ZIP](G:/ai/AIC视频/deliveries/AIC20H_TEMPORAL_VERIFY_BOTH_20261014/candidate_TEMPORAL_VERIFY_BOTH.zip) | 121879 | +7 / -178 |

顺序来自推理前固定优先级，不表示预计成绩排序。每份426条非空视频记录，原PTS/空间来源、保留D8帧的框、独立11项格式检查、实际8782459120参数均通过；单JSONL、ZIP大小/SHA/CRC/成员SHA及Windows实际canonical与历史/彼此差异均已验收。5份ZIP总载荷1,900,206字节，只下载最终ZIP和小回执，没有完整raw/clock/tensor/log往返。未自动提交官网。

全量1992模型回答（1959新、33采用）及1992首次独立输入/输出QA、426原生来源、49批自然终态全部保留。C6仅最终汇总身份字典适配失败，新C7仅恢复该失败汇总，后续两个元数据适配失败原样保留后窄恢复；没有重复成功模型、QA或封包。当前D8用户反馈40.44仍是已知成绩基线。

[最终本地验收回执](G:/ai/AIC视频/reports/twenty_hour_five_20261014_v1/final_windows_delivery_acceptance_01.json)；[唯一状态](G:/ai/AIC视频/reports/twenty_hour_five_20261014_v1/current_state.json)。
