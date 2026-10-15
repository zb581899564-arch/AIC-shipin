本目录仅准备新单因素SEMANTIC_GUARD的协议、CPU开发入口。原PAIR短源确认真实STOP及13调用/430.978899209秒费用不动，本方向尚未运行开发或选择新确认源。

固定规则见`semantic_rule.py`：仅n>=2原parsed.redundant唯一最弱候选可删。同一原回答的action/reaction/information非空[a,b]各映射原native ordinal半开区间；b64仅使用原window_native_end_ordinal/exact。三类并集与弱候选原selected_interval_exact实际native集合只要相交1帧，则整个弱候选保留，否则同WORST_ALL删除。绝不新增帧、重新padding、改端点/框、乘fps或扫描阈值。重复event跨case是工程失败。

所有读取都是既有完整JSON证据；无torch/processor/decoder/媒体下载或QA重放。`adopted_bindings.py`采用原8份done/raw/首次inputQA/outputQA绑定，另显式核原native end字段；ordinary只验证原schema，不参与新删除规则。原WORST_ALL只核native集合供机制比较，不重做它的人类参考效果。

Linux新根：`/home/inspur/aic_video_work/midnight_semantic_guard_20261015_v1`，本目录文件部署到其`code/`。旧根/旧代码完全不修改。

先审阅登记：`<隔离python> -B <新根>/code/register_development.py --root <新根>`，生成`protocol.json`和`development_registration.json`。登记只读旧元数据与终态，不读取raters标签内容或执行新效果比较。原4开发全部已曝光；原8回答/原首次QA完整引用，不能称新盲确认。

开发尚未获执行授权。主代理批准后单独创建`development_launch_authorization.json`，scope=`ONE_NEW_SEMANTIC_GUARD_DEVELOPMENT_CPU_COMPARISON`、controller_ref绑定`code/run_development.py`、registration_ref绑定实际登记、automatic_retry=false；仅一次`<隔离python> -B <新根>/code/run_development.py`。输出固定`dev_01/comparison.json`、`dev_01/completion.json`，PASS才有`dev_01/development_selection.json`。工程错误单独failure，不变成空决策或质量UNKNOWN。

结果schema=`MIDNIGHT_SEMANTIC_GUARD_COMPARISON_V1`，group=dev，单臂`SEMANTIC_GUARD`。`passed_policies`与`passed_arms`为同一单bool map；`policies.SEMANTIC_GUARD`含PASS/gates/macro/cases/decision_proofs/prediction_native_sets/mechanism。bindings含protocol_ref、registration_ref、manifest_ref、decisions_ref、prior_unprotected_result_ref、prior_pair_failure_ref。固定10个gates：

- full_group
- macro_F1_not_lower
- macro_precision_not_lower
- every_source_F1_loss_at_most_001
- invalid_decisions_zero
- full_original_rater_denominator
- real_changed_sources
- no_new_native_frames
- semantic_guard_really_restores_native_frames_vs_WORST_ALL
- semantic_guard_still_deletes_native_frames_vs_original_VERIFY

完整4源/全部原raters，F1与precision不降、每源loss<=.01、invalid0、至少1源真实删帧、无新增帧均保持；另外机制必须至少1源相对未保护WORST_ALL恢复真实native帧，且仍有至少1源相对原VERIFY真实删帧。恢复/删除按最终源级native集合差计数，不按事件数或cue数。recall仅报告。

开发FAIL立即STOP，不提前选源、下载或启动确认。只有PASS才另登记全新4确认，按原salt/来源名hash顺序，排除known/全部旧注册及曝光/新增SHORT6和上一old4；总公开候选最多6、具体媒体bytes另登记，沿原max30秒/native64 profile，不强制short。新确认与生产不由本准备代码自动启动。所有证据Linux驻留，16Z截止不变；官方提分UNKNOWN。
