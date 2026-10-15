# 今晚五新包交付记录

## 2026-10-15 最新成绩反馈

用户明确按原交付顺序上传，截图为时间倒序；以下对应已绑定原ZIP SHA，详见 [成绩回执](user_score_feedback_four_20261015_01.json) 和 [原截图](user_score_feedback_four_20261015_01.png)。成绩来源为用户截图/说明，未独立登录官网。

|上传顺序|包|显示成绩|相对原40.46|截图打分时间|
|---|---|---:|---:|---|
|1|ACTION 动作补召回|40.44|-0.02|2026-10-15 21:53:05|
|2|REACTION 情绪反应补召回|40.46|0.00（显示同分）|2026-10-15 21:53:07|
|3|INFORMATION 信息亮点补召回|40.45|-0.01|2026-10-15 21:53:09|
|4|ORDINARY 相对删弱|38.83|-1.63|2026-10-15 21:53:15|

原高光复核VERIFY40.46继续为基线。相对删弱的外部代理确认通过未转化为线上收益，保留原代理结果和工程验收，不回写原PASS；本轮没有显示提分。情绪反应版仅显示同分，无法据两位分判断更高精度成绩。

实际交付仍4/5；PAIR与SEMANTIC_GUARD均STOP，备用并集仅Linux工程预览，第四风险范围仍未批准。本次只记录成绩，不触发新模型、封包或交付。

当前 **4/5**。PAIR短源确认科学失败、SEMANTIC_GUARD机制门失败，均已停止；备用并集仍待第四风险范围答复。

保护基线：用户反馈高光复核40.46，原ZIP未修改。最新四包用户成绩见上表；原交付时点UNKNOWN及历史验收保持，未自动提交。

|交付顺序|方向|新增/删除原生帧|文件|
|---|---|---|---|
|1|动作亮点补召回（风险）|+124/-0|[下载ZIP](<G:/ai/AIC视频/deliveries/MIDNIGHT_ACTION_RISK_8B_20261015/candidate_MIDNIGHT_ACTION.zip>)|
|2|情绪反应补召回（风险）|+8/-0|[下载ZIP](<G:/ai/AIC视频/deliveries/MIDNIGHT_REACTION_RISK_8B_20261015/candidate_MIDNIGHT_REACTION.zip>)|
|3|信息亮点补召回（风险）|+52/-0|[下载ZIP](<G:/ai/AIC视频/deliveries/MIDNIGHT_INFORMATION_RISK_8B_20261015/candidate_MIDNIGHT_INFORMATION.zip>)|
|4|多候选窗口删除相对最弱片段（外部代理确认通过）|+0/-10060|[下载ZIP](<G:/ai/AIC视频/deliveries/MIDNIGHT_ORDINARY_8B_20261015/candidate_MIDNIGHT_ORDINARY.zip>)|

三个风险方向依用户授权未做离线效果筛选；保留必要工程合法性、实际来源、原生帧及传输完整性检查。ORDINARY是文件名，算法为相对删最弱，不表示已有人工普通片段真值。

4包分别通过426完整非空集合、原生PTS、保留框一致与来源、实际8.78245912B、独立11strict、单JSONL、CRC及成员SHA、历史及彼此真实预测差异、Windows与Linux大小/SHA一致。全部raw/输入/复核证据驻Linux。

PAIR_ONLY原4确认无n2适用窗、精确零变化；一次另登记短源4确认后，有1源真实删除130帧，但该源F1损失0.1110243，宏F1与precision亦下降，三质量门失败。该方向停止，不封包或扩池改门。现另登记SEMANTIC_GUARD：若三类原明确正语义native区间与弱候选原选帧相交，则完整保留弱候选，否则同WORST_ALL；先在已曝光开发源做新CPU比较，原8门及真实保护/仍删除机制门通过后才新独立确认。尚不计为交付。

教师来源与瓶颈依据见 [TEACHER_BOTTLENECK.md](TEACHER_BOTTLENECK.md)：当前808行标签实际为豆包，不是Gemini；没有同数据的受控Gemini对照。

## 第五份备用预览

三类语义并集候选已在Linux完成工程预览：380660B、122186帧，较40.46新增184/删除0，全部原框/帧保持、11strict与CRC/成员SHA通过，0新模型。它将成为第4个免效果验证风险包，已一次询问人类是否接受3→4范围变更；当前未批准、未回Windows，不计交付。见 [具体预览](FOURTH_RISK_PREVIEW.md)。
