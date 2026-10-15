# v8v4 新版静态复审清单（待实际准备完成）

时间 2026-10-11T00:46:28.456444+00:00。当前仅检查原v8v3源码并整理独立复审目标，没有v8v4模型/AGY/上传/训练权限；原科学正文/27片已通过部分只用SHA与output-only投影引用。不能把本清单当v8v4验收或启动门。

## 新版必须集中核对

1. 全raw tool ERROR/失败输出始终保留；同step的ERROR→DONE也拒绝。latest仅用于总结自然终态，不删除曾发生的失败。对每条tool update审核tool_name、白名单、完整literal参数；同step身份/参数变化拒绝，而不是只审最后一条。
2. native四ACTIVE确实存在，planning response在ACTIVE之前，ACTIVE在对应DONE之前，四图同一个planning response，全四DONE在新的fact planning response之前，fact planning在WRITE ACTIVE之前；缺失ACTIVE/DONE、异常时序、四图拆response/跨批、事实提前规划均拒绝。按原raw位置证明，不把-1当合法切片。
3. effective严格分成两批各4，同response的ACTIVE、DONE位置显式验收；第二批planning须在首批全DONE之后，proposal planning须在全部8DONE之后。memory positive也必须采用同样两批路线，不能现有八个逐response“positive”。四图batch是真实工具提交粒度，不声称并发。
4. facts/proposal selfread：仅已写成功输出、最多一次、当前输出严格<30000、尾LF/noCR/行数/实际bytes完整metadata绑定；工具截断/错metadata/写前read/ACK selfread/字节漂移拒绝。输出content与程序identity区分，不能只凭read字符串成功。
5. 第一36正常child/exit0/null stop/result SUCCESS/whole strict PASS/两个immutable scopes+全部input/output/prefix不漂移，且全raw无工具ERROR/outside/postproposaltools才允许37；任何最后网络ERROR也STOP，无旧异常例外。constraints/gate/binding必须引用新版本SHA，旧v8v3源码/回执保留。
6. 引用已通过科学/字段文本的SHA，核新增版本只有输出路径/ACK工程路径投影，不改原科学24/21、native64/16facts/clip/effective8/roles/domain/clock/geometry；两call 202/302核心不因guard改变，max37/each7200/no38/no automaticretry/sourcepending保持。
7. 新pure-memory独立测试入口若需运行，先检查其不启动模型、不写teacher输出/冻结文件/真实ledger、不decode；只允许memory fixture和plan_review新证据。既有CPU回执引用，不重复。

## v8v3 同类全raw参数覆盖的明确静态trace

[原engine.py L25](<G:/ai/AIC视频/reports/annotation_iteration_20261010/complete_reference_supplement_v1/teacher_expansion/engineering_CLI36_37_split_fragment_v8v3/engine.py:25>)先压缩updates为latest，L39–44白名单与参数集合检查仅遍历latest。四图屏障L8–15只以step_index找ACTIVE/DONE位置，没有核ACTIVE的工具参数。

以本应F00的工具step K为例，以下原始更新可使危险早期identity从检查中消失（仅说明内存trace，未打开outside路径）：

```json
{"step_index": "K", "state": "ACTIVE", "step_type": "tool", "tool_name": "view_file", "tool_info": {"parameters": {"AbsolutePath": "OUTSIDE_NOT_READ"}}}
{"step_index": "K", "state": "DONE", "step_type": "tool", "tool_name": "view_file", "tool_info": {"parameters": {"AbsolutePath": "EXPECTED_F00_ALIAS"}, "output": "read"}}
```

latest[K]最终仅含EXPECTED_F00_ALIAS，outside检查不见首ACTIVE；ACTIVE原raw位置仍被four_image_barrier使用，因此匹配最终合法路径的正常四图/事实流程可掩盖原outside尝试。另一具体变种：首ACTIVE为EXPECTED_F00_ALIAS但含StartLine/EndLine，最后DONE删去range参数；完整文件参数检查也只见最终单AbsolutePath。write_to_file ACTIVE outsideTarget→DONE legalFactTarget同理。tool_name在同step从非法工具改成view_file也同属identity冲突。

本问题不声称真实运行曾发生该trace；它证明当前guard对全raw危险尝试未覆盖，与明确“任何实际outside/参数变更拒绝”不一致。修全rawERROR必须同时修全raw工具/参数身份，不能只加ERROR数组后保留latest白名单审计。

附带复审问题：各文字read实际DONE之后才可ACK WRITE ACTIVE，不能仅靠latest字典的DONE列表插入顺序推定ACK已发生在读取之后；若新版已有统一raw时序guard，核其覆盖文字/ACK。此项先作静态复审问题，不额外启动实验。

原engine当前SHA `b4a41548540efec5640b021f9606ef3a81a0ce0ae94af9702af74c238dc87a0e`。此文件只属plan_review ownership，无其它目录修改。
