# Summary主线生产前合同只读审阅14

本次仅阅读本地六个指定代码文件，另为核实继承接口阅读`summary_output.py`、`summary_grammar6.py`、已冻结协议06及目标序列化/准备代码。未打开人工目标记录、实际预测或指标，未执行训练、生成、评价、测试、QA、processor、解码或远端命令；唯一新增文件为本报告。GPU与正式代码仍由主代理和其实现代理负责。

**结论：在本次六文件的端到端衔接中，未发现新的确定性阻断bug。代码没有把summary未选改成普通/无高光，没有把局部时间当全源时间，没有丢掉合法空源或缺失输出，也没有按开发结果选择中间checkpoint的分支。这个结论只允许继续已授权的固定序列至一次真实评价；不是训练、能力、正式426或交付PASS。** CPU05宽泛mask声明和旧raw parser问题已有独立新路径处理，本报告不把它们作为未修问题重新提出。

## 合同核对证据

| 核查项 | 代码结论与证据 |
| --- | --- |
| 人工摘要的empty含义 | [summary_contract.py:94](G:/ai/AIC视频/improvement/bottleneck_24h_v1/summary_contract.py:94)的唯一新prompt明确整源摘要、同源Overview/Excerpt、empty表示未入该源摘要而非无值得内容；[summary_gpu_remaining11.py:125](G:/ai/AIC视频/improvement/bottleneck_24h_v1/summary_gpu_remaining11.py:125)检查每条`empty_means_unselected_source_summary_only`，没有删空目标、改成普通负例或按评审挑列的分支。 |
| 两视图与坐标统一 | [summary_contract.py:47](G:/ai/AIC视频/improvement/bottleneck_24h_v1/summary_contract.py:47)先按真实native PTS取Excerpt，Overview origin=0、Excerpt origin=window start；[summary_contract.py:67](G:/ai/AIC视频/improvement/bottleneck_24h_v1/summary_contract.py:67)的组时间减各自origin，文字明确Excerpt-local。训练`InputCache`及[summary_generate.py:85](G:/ai/AIC视频/improvement/bottleneck_24h_v1/summary_generate.py:85)使用同一`build_pixels`，生成复核完整plan与首验input signature；两角色使用相同43份prefix refs，没有在推理重写prompt。 |
| 监督位置与标签隔离 | [summary_gpu_remaining11.py:239](G:/ai/AIC视频/improvement/bottleneck_24h_v1/summary_gpu_remaining11.py:239)仅从`input_ref`读取prefix/pixels，suffix为训练teacher-forcing目标；取实际causal predecessor位置后算CE。新mask06的接受回执与两个mask函数AST在[同文件:101](G:/ai/AIC视频/improvement/bottleneck_24h_v1/summary_gpu_remaining11.py:101)绑定。生成不读取labels或targets，prefix中没有reviewer或目标摘要内容。未在本次重新执行已成功mask QA。 |
| 固定epoch与绝对权重 | [summary_gpu_remaining11.py:117](G:/ai/AIC视频/improvement/bottleneck_24h_v1/summary_gpu_remaining11.py:117)检查2236个唯一window/reviewer目标、25源144窗，权重`2236/(25*W_s*R_sw)`、各源总质量`2236/25`；固定seed生成全排列。 [同文件:251](G:/ai/AIC视频/improvement/bottleneck_24h_v1/summary_gpu_remaining11.py:251)先做每序列token-mean CE，再乘绝对weight/4，不按当前4条的权重和重归一化。2236恰好559×4，没有末批丢弃/补样。 |
| pilot→remaining不重复成功micro | [summary_gpu_remaining11.py:181](G:/ai/AIC视频/improvement/bottleneck_24h_v1/summary_gpu_remaining11.py:181)检查真实pilot4/16、schedule与immutable checkpoint；加载adapter/Adam状态，全部初始化后[同文件:238](G:/ai/AIC视频/improvement/bottleneck_24h_v1/summary_gpu_remaining11.py:238)恢复RNG，step从`start_step+1`到559。无自动重试路径。这里核的是代码合同，不是本次查看实际进度或终态。 |
| FINAL只有一次且未看指标选优 | [run_summary_chain.py:121](G:/ai/AIC视频/improvement/bottleneck_24h_v1/run_summary_chain.py:121)只有完成559/2236后才冻结最终adapter，再运行TRAINED43；[summary_generate.py:126](G:/ai/AIC视频/improvement/bottleneck_24h_v1/summary_generate.py:126)独立要求final559 completion、实际权重ref一致。唯一评价在两角色真实完成和首次独立QA之后；没有按loss/开发指标取中间权重、调参或再次生成的分支。 |
| 真实raw及完整输出 | [summary_generate.py:181](G:/ai/AIC视频/improvement/bottleneck_24h_v1/summary_generate.py:181)先保存真实token，要求自然EOS，再原样decode和精确parser；异常直接failure。 [summary_output_qa.py:35](G:/ai/AIC视频/improvement/bottleneck_24h_v1/summary_output_qa.py:35)查唯一wrapper/ledger completed/exit0，[同文件:58](G:/ai/AIC视频/improvement/bottleneck_24h_v1/summary_output_qa.py:58)逐条核token、raw、request、role、weight、grammar及native范围。评价再要求每角色完整同43 UID，不接纳缺项或失败转空。 |
| 原生全域、空源、共同输出 | [evaluate_summary.py:222](G:/ai/AIC视频/improvement/bottleneck_24h_v1/evaluate_summary.py:222)核原8源时钟/媒体身份并要求全部native frames被原窗口覆盖；不把遗漏窗默认为负。 [同文件:293](G:/ai/AIC视频/improvement/bottleneck_24h_v1/evaluate_summary.py:293)精确Fraction局部区间加window start，半开所属帧与跨窗union去重；所有评审得到同一源mask。 [同文件:110](G:/ai/AIC视频/improvement/bottleneck_24h_v1/evaluate_summary.py:110)保留空预测、逐评审FP/FN与空参考，P=G=0仍按旧计数约定得0，未用1提高空源得分。 |
| matched-K内容控制 | [evaluate_summary.py:135](G:/ai/AIC视频/improvement/bottleneck_24h_v1/evaluate_summary.py:135)将既有`semantic_score[groups]`映射到全源native frame，按score降序、ordinal升序稳定选择；[同文件:356](G:/ai/AIC视频/improvement/bottleneck_24h_v1/evaluate_summary.py:356)仅以TRAINED实际K给定预算。没有用labels选择K、阈值或评审，不保存可提交mask。全40.47、同输入INIT和matched-semantic分别报告，未混成一个控制。 |

## 一项必须保留的重大科学判读边界

**matched-K胜出本身不能排除再次大删选崩塌，也不能证明超越40.47。** 这是已定义诊断的数学边界，不是新代码bug。比如某源某评审有G=1000个参考帧，TRAINED只选1个正确帧、同K semantic恰选错帧，则TRAINED相对matched控制的F1增量为`2/1001>0`，但TRAINED recall只有`1/1000`，其整源摘要可以远差于完整40.47。K=0时两者均为空、F1均0，差值也不会产生任何内容能力证据。此反例为纯数学说明，没有读取真实标签或预测。

现代码已把这个风险暴露出来：逐源与macro的TRAINED-vs完整40.47、recall、coverage、删增帧、空源和worst-source delta都在[evaluate_summary.py:359](G:/ai/AIC视频/improvement/bottleneck_24h_v1/evaluate_summary.py:359)至389保存；结果状态明确`NOT_SCIENTIFIC_PROMOTION`，`production_admitted=False`。 [run_summary_chain.py:141](G:/ai/AIC视频/improvement/bottleneck_24h_v1/run_summary_chain.py:141)完成后也只等待主代理审阅，不自动进入正式426或封包。因此本次没有要求添加事后覆盖阈值、修预测、改K或回滚成增量-only。

生产判断必须使用已冻结[协议06](G:/ai/AIC视频/reports/bottleneck_24h_20261019_v1/SUMMARY_SFT_PROTOCOL_06.md)的完整条件：同输入INIT与同覆盖semantic均有选择能力证据，且相对完整40.47没有明显输出崩塌；不能只拿matched-K正差、loss下降、格式通过或单源均值收益放行。多评审摘要存在分歧，而一次greedy语言输出可能偏向共同的短/空模式；该能力风险只能由这次已注册的真实评价揭示，本报告没有证明其发生或未发生。

另外，matched-K只匹配原生帧数，不匹配事件个数/连续性/播放秒数；它是固定的ranking内容诊断，不是对旧semantic完整生产策略或官方联合空间质量的等价复现。原完整40.47仍是单独对照，空间保持UNKNOWN。所有8源历史曝光事实保持，不能称新盲测或官方质量保证。

## 审阅结论的实际边界

- 没有发现需在继续已启动固定训练/一次评价前修改的新增确定性问题；不授权重跑任何成功阶段。
- 本报告没有查看actual559终态、TRAINED43、真实评价数值或正式输入/生成/封包代码；它们是否通过仍UNKNOWN。
- 任何正式输入、输出、非空/原生/空间/参数与ZIP验收由主代理按随后独立注册执行；本报告不能代替这些证据，也不把“未发现bug”当作能力PASS。
