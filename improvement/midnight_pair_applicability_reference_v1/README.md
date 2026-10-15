本目录是唯一补充的短源PAIR适用性确认，尚未launch。旧4确认PAIR因无变化失败的事实保持；本次仅按作者声明0<duration<=30秒分层，按原source-name SHA顺序取4主+2有限工程替补。主源21,961,720B，完整池26,768,757B，Windows只做原6对象匿名HEAD，媒体直接作者公开对象CDN→Linux。

Linux唯一根：`/home/inspur/aic_video_work/midnight_pair_applicability_20261015_v1`。`adopted_source_review/`仅审阅，不部署或执行。其余文件部署到该根相同相对路径，部署清单绑定每个文件的SHA；不覆盖旧根。

主入口和登记顺序：

1. `freeze_metadata.py`仅核原协议07、开发08、旧PAIR neutral-but-no-applicability终态、全部旧26媒体及已注册来源/known ID与bytes隔离，以及作者metadata长度分层，写一次`supplemental_protocol.json`、`new_selection.json`和`source_candidates.json`。没有新模型、标签效果比较或媒体下载。`new_selection.confirm_metrics_examined=false`范围明确为`THIS_NEW_SHORT_COHORT_ONLY`，`prior_confirm_metrics_examined=true`；开发结果引用不重评。
2. Windows `windows_head.py --candidates <这次source_candidates.json小副本> --output <新的HEAD回执目录>`对6个同源对象各一次HEAD。每个成功立刻独立落盘，失败不重试；最终`public_routes.json`绑定源候选文件SHA。小量路由metadata经已获准Tailscale部署Linux，媒体不经Windows。
3. 主审后生成`launch_authorization.json`：`scope=ONE_SUPPLEMENTAL_SHORT_PAIR_MEDIA_CPU_GPU_CHAIN`、`root=<唯一新根>`、`controller_sha256=<实际controller SHA>`、`no_automatic_retry=true`。唯一执行`CUDA_VISIBLE_DEVICES=0 <既有隔离python> -B <新根>/controller.py`，首次preflight保存完整进程argv、活动GPU账本、CPU/内存/磁盘和GPU实况。有既有GPU预约/compute进程则停报，不操作外部任务。
4. `controller.py`先验证所有新代码及原冻结rank代码，写`media_registration.json`再调用`media/confirm_media.py`。媒体一次GET、精确length/ETag、原生zero-origin/物理end<=30秒/64 distinct geometry不放宽；仅404/原生domain明确不合法可按预登记2替补依次替换。模型/标签效果不参与换源。
5. 原4媒体和native完整成功后写`positive_fresh_registration.json`。`code/prepare_inputs.py`生成4个原native64主输入；独立进程`first_input_qa.py`第一次重新由同64RGB/原prompt完整processor核tensor keys/shape/dtype/bits，再锁完整来源/输入/代码。B0后output-only首QA不重复encoder。
6. 原VERIFY候选每窗最多5，因此最多20。`pilot_verify.py prepare`复用原视觉，只生成提示token；独立`verify_input_qa.py`核原视觉、token、prompt/事件绑定并锁来源；唯一VERIFY后output-only首QA不重复成功输入。全部CPU/首QA通过才各自唯一GPU。read-once gzip/BytesIO只存在本新副本；实际首QA仍完整比较bits。
7. `reference/map_confirm_completed.py`采用实际B0/VERIFY/首次QA，输出`rank_mapping_01/inference_entries.json`与完整4源`first_fresh_evaluation_manifest.json`。空基线源保留分母；实际非空rank view在0..4内。若没有任一窗恰好2候选，立即真实`STOP_SUPPLEMENTAL_PAIR_NOT_APPLICABLE`，不伪造rank/QA，不扩池。
8. 有PAIR适用窗才启动原冻结`midnight_five ROOT/relative_code_v1/controller.py --stage relative_pair_short_confirm_22`，提示、grammar、BASE角色与开发完全相同。新rank仅新token/首次输入QA；视觉cache与原B0首QA完整引用，不新vision/decoder。
9. `reference/policy_evaluate.py`只评PAIR_ONLY，保留原07全部门：完整4源/全部raters、macroF1及precision不降、每源F1loss<=.01、invalid0、无新帧、至少1源真实变化。仅recall描述，不增加绝对不降门。真实失败或无适用性均STOP，不追加cohort。

冻结预算（16:00Z后禁止新调用）：

|阶段|唯一job|实际调用上限|秒上限|
|---|---|---:|---:|
|B0|midnight_pair_short4_b0_20261015_v1|4|900|
|VERIFY|midnight_pair_short4_verify_20261015_v1|20|1800|
|rank|midnight_pair_short4_rank_20261015_v1|4|600|

模型实际8,782,459,120参数，原profile/geometry/端点与padding保留。B0/VERIFY使用原角色，rank使用原冻结BASE生成内禁用TIME。没有训练或全量。

固定输出（均Linux绝对路径）：

- comparison：`/home/inspur/aic_video_work/midnight_pair_applicability_20261015_v1/policy_fresh_comparison.json`，schema=`MIDNIGHT_RELATIVE_WORST_POLICY_COMPARISON_V1`，`passed_policies`与`passed_arms`均仅`{"PAIR_ONLY":bool}`；宏指标和逐源仅PAIR。新supplemental protocol/new selection/旧neutral结果都绑定。
- 来源media注册：新根`/media_registration.json`；完整媒体：`/reference_01/completion.json`；原生输入注册：`/positive_fresh_registration.json`。
- 来源/首QA admission：新根`/rank_mapping_01/fresh_admission.json`；完整manifest：`/rank_mapping_01/first_fresh_evaluation_manifest.json`。
- rank注册与完成：`/home/inspur/aic_video_work/midnight_five_verify40_46_20261015_v1/relative_pair_short_confirm_22/registration.json`、同级`completion.json`。
- 控制完成：新根`/control_01/completion.json`。实际3阶段全完成时status=`NATURAL_COMPLETE_FIRST_SHORT_SOURCE_PAIR_APPLICABILITY_CONFIRMATION`，含comparison/media_registration/positive_fresh_registration/rank_completion refs、各自然GPU resource refs、实际B0/VERIFY/rank计数和首次QA refs。提前无适用性明确`STOP_FIRST_SHORT_SOURCE_PAIR_NOT_APPLICABLE`且rank_ref=null。工程失败单独`control_01/failure.json`，不覆盖成功或自动重启。

主代理独立生成封包quality admission和finalizer；本控制不触碰package_inputs，不把代理参考当官方成绩。全部计算/raw/媒体/QA留Linux，仅短回执与最终包回Windows。
