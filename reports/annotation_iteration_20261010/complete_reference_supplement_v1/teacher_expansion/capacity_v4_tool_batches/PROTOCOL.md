# 固定 fresh 双窗工具批次容量协议 v4

仅前瞻替换尚未执行的 jobs6..23，固定九对 CLI28..36，每对新独立会话7200秒，无自动重试。绑定根主控 teacher_dispatch_capacity_v4_authorization.json 及真实既有 batch stream 证据SHA。当前v3 call01、历史25/75分钟失败、所有冻结/原始输出/费用UNKNOWN保持；未完成HT5 W10不补空、不恢复重问；已完成W02独立证据保持。新授权只涉及工程容量及工具提交粒度，科学协议和准入门不变。

每窗64原始PNG、16组，每组按slot0..3在同一次 agent_response 提交4个独立view_file工具调用；客户端可顺序执行，不能声称工具并发。等待4图实际DONE后立即一次write_to_file本组4条静态事实，之后才可下一组。每图只能读一次，每事实只参考对应单图；subject/composition/subtitle presence+literal/中文visible_fact，身份由程序绑定。不从单帧猜动作、心理、动机或字幕语言。事实成功输出不可覆盖。16组全部封存才读本窗clip一次；随后按冻结顺序同一response提交8个effective student preview独立view_file，全8DONE后才写完整proposal。实际学生native processor64帧，教师只8预览。保持原geometry/RGB/source/domain/PTS/SHA，成功媒体不重新decode。

proposal保持完整连续KEEP/NO/UNKNOWN、独立事件、全部NO理由、事实support、边界不确定range和limitations。短高光包含完整亮点，不把whole-window叙事/持续说话/常态或重复状态/字幕内容自动当高光，不设事件数量配额；真实UNKNOWN/空events合法，不用失败转空。各窗证据独立，禁止旧标签、预测、分数或其他评审。只允许view_file/write_to_file，禁止terminal/code/web/search/其他模型/subagent。已写指定自身输出最多一次写后核对，不得写前读或覆盖。

启动前冻结全部输入、输出/读取白名单、模型gemini-3.8-flash-high、授权/证据、执行代码和prompt模板SHA。独立实核actual工具顺序、4-image barrier、clip+8preview、结构覆盖/identity+geometry、真实终态/rawSHA/账本，错误保存，不自动重试。历史真实batch只证明同response多工具能力，不保证本次时间或语义质量。九对固定顺序，不基于semantic挑窗；根审核无模型dry-run后另发启动消息才注册CLI。结构PASS不是semantic正确/human gold/训练准入，仍需root和独立学生审阅。现金UNKNOWN；本任务新GPU/Qwen/decoder/optimizer/训练/426/100confirm均0。
