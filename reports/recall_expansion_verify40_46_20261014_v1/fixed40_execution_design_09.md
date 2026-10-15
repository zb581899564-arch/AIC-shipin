# 固定40：9源17原源视图的来源接口与分层否决设计

2026-10-15。本报告只覆盖既有固定观察点的补召回否决接口。新代码为 `improvement/recall_fixed40_v1/source_audit.py` 和 `facts_veto.py`；不改旧冻结协议、旧否决器、dev/confirm源码或旧成功/失败/费用。

## 结论与执行边界

需要首次真实准备和执行的最小事实范围为 **9个原媒体、17个15秒/7.5秒完整原源网格视图**。9源均已在Linux驻留，完整clock已成功测量；无需下载媒体、重新测clock、回传完整clock或采用旧112窗导出。此次只读核查没有执行新download、decode、encode、processor、模型或replay。

主代理报告dev已通过；confirm仍须其唯一在途链完整终态和独立准入，本文不读取确认指标、不提前登记执行PASS。未来只有dev与confirm均按原门通过，且新独立fixed40登记和资源准入完整后，才能执行这17视图。B0需17个首次调用；VERIFY数量由全部实际B0原段唯一决定，不能预称17或把未完成原段当空。登记上限沿运行代码120，实际数及费用必须据真实回执记录。

科学事实门可在实际KEEP集合K不触任何222个已知ORDINARY点时，通过原零新增门的充分条件；不需要为该分支再推56个旧段来虚构VERIFY基线。KEEP不删由固定合并实现的任意B集合恒等性证明。最终426产物逐帧、逐框、ratio和原对象字节保持必须在产出后实际验收，当前明确未发生。代理dev/confirm与这项事实门通过，也不代表线上质量提高。

## 原事实文件与最小传输

原文件 `reports/reliable_reference_20261012_v1/coverage_diagnostic_01.json` 为594,682 B，SHA256：

`37a7c93876334b3a5d0c222e3a7f99727778d50f28f3a1172e860d19d3dc82b8`

该文件是 `AI_REVIEWED_SILVER_NOT_HUMAN_GOLD`。保留 `STOP_REFERENCE_COVERAGE_INSUFFICIENT`、`coverage_pass=false`、`reference_quality_pass=false` 和旧正式质量FAILED。独立重数40个不同来源、3081点：KEEP184/6源、ORDINARY222/9源、UNKNOWN2675。UNKNOWN、未选择、原查询任务标签都不改称普通。该40源已经曝光，只用于原已知观察点否决，不是新盲测、真值、调参集或普适高光评测。

`source_audit.load_reference()` 只接受上述完整文件的实际字节SHA和大小，重新计算全部40源/3081点/222 ORDINARY/9源，而非相信调用方compact SHA或预填计数。随后把222点逐项按 `ordinal + exact_pts` 与对应原clock绑定。其余KEEP/UNKNOWN点保持原计数与语义，不为了本轮重新标注。

旧 `reports/boundary_refinement_20261012_v1/developer_readonly_export.json` 为5,631,700 B，SHA256 `7feb4cbec6567612e99a98bca708deb5041e38cd0735500a1016263fb43cc8d6`；包含104任务/112旧窗，本固定40子集45个旧B窗/56段。它只作历史出处，新运行接口不依赖该文件，不强迫5.63 MB往返，也不据它声称新输入或VERIFY身份相同。

本轮严格home SSH批读仅检查这两个明确Linux位置，均不存在：

- `<RUN>/reliable_reference_20261012_v1/coverage_diagnostic_01.json`
- `<RUN>/boundary_refinement_20261012_v1/developer_readonly_export.json`

这只证明指定路径不存在，没有搜索全盘，不能称Linux任何位置都没有。后续按主登记部署594,682 B原银标及小量新代码即可；原银标实际Linux落点由 `reference_ref={path,sha256}` 和 `required_files` 明确固定，部署完整性另按原传输规则核验。此报告不启动上传。9份原clock共1,220,183 B、9媒体共108,338,197 B均在Linux；本轮只stat媒体，不重新读取媒体正文或重算其SHA。

## 原始来源、完整clock与实际字段

`<RUN>` 为：

`/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z`

每个clock的实际固定路径为 `<RUN>/context_advisory_v1/input_01/<source_key>.clock.json`。下面完整SHA同时是原已验证物理媒体SHA的 `source_key`；`source_sha256=source_key`，不是video_id或source_group的文本哈希。此次只读批核clock文件SHA与银标一致、clock内source_sha字段一致及原媒体存在/大小；未来独立CPU登记仍会重核实际 `required_files` 中媒体SHA，不能将本次stat冒充新的媒体正文SHA验收。

| case | video_id / source_group | source_key（实际媒体SHA256） | clock SHA256 |
| --- | --- | --- | --- |
| R07 | qvh_000263_9x16 / IdpHJK90VDw | 822cdc171cc21e37df7f744af73ba2b1de285f2e4628e0708f9a97ba4505c3d2 | d5a77136ae413ed28e18ea972f6547a3d377a7d6085f61a8d76a54a03020aa8e |
| R11 | qvh_000159_9x16 / MC6y7jwenlE | d04f9d5ef5a5a37084acc4756e55a1fb033498ef1fd50b730573aad462ca8a98 | f8e00ec8d82bf10498603004fb408bf54013894514d61159e9a0cad2ec154124 |
| R15 | qvh_000679_9x16 / 8vUjoQd0fYY | 5d11deec3842e880a5a2d9dd9d233fdc651e61a883095d6a120e07978dec8d69 | 7c6e7f3f50fff7527becbd69b58d89a462a4a3a20d6763c6d38f8b50c15d8b8a |
| R18 | qvh_000750_9x16 / Y2GVVC_cD_E | db905f1b79ec7d3771a363a0ef9788b05170a0358a6df9d5d7d1f767a17e3638 | e0869b5122f9256645167268e9472af5807370c6798aeb4555d4c44493dc3642 |
| R19 | qvh_000265_9x16 / p-III2A1E2o | 14a7f250c237708d35ac9fcdf2de48efda96e1c298f5843a095d3094fd3100b0 | c1fc134f6640a32d7d065b6b4ae3318a953e8c2ae88fe518df4fb6442067c6cb |
| S08 | qvh_000882_9x16 / QXC-pnmOGnM | 7874f5ad5ef45349b8894353377c1e0664f19054483903e763e7f1c64f5124b4 | 9c0070ce8d6ed17a96b0872d1011fa295d4732625943f7aa353cc7c3f5213dad |
| S30 | qvh_000729_9x16 / E6yFTWlChmE | cafe9f8e5b93f40917d37aad3a1003dfa133f2d41fc714d6a0021eb18e591dab | 081c08ec454a983a7210ec8926f92ac51666857b0575e461786ed19167e9a7ac |
| S32 | qvh_000481_9x16 / iuH6szYVWw4 | 9829f8a967daf3926f9b6e9416a1ebe498c9dec40c6211eb5bf07d2d28b1f78f | 6e55e5c882c998d9473b3d6a8cd953a7aa73912860b15cc96b11de58b30405f0 |
| S36 | qvh_000482_9x16 / TNkHgO68F6U | a4227c55bbdc30b160f5bf9e63fc177d3a69310db5aa20fd3bc3e37227acae95 | 93e2dfae3f42c7c226f25c0d45f3ba0d8b19a50f723e291641b18ce5ec002d3a |

源路径前缀为 `/home/inspur/aic_video_data/videos/`，下表尾部直接拼接得原 `source_path`。全部实际width=534、height=300；fps为已存 `fps_num/fps_den`，不从名义150秒或画幅猜。全部原 `pts_rational[0]='0'`、`raw_origin_sec=0.0`，不平移原PTS；`endpoint_kind='ACTUAL_LAST_DECODED_FRAME_PACKET_DURATION'`。

| case | source_path尾部 | media B / clock B | n_frames | fps_num/fps_den | physical_endpoint_rational | 最末pts_rational |
| --- | --- | ---: | ---: | --- | --- | --- |
| R07 | i/IdpHJK90VDw_60.0_210.0.mp4 | 14599788 / 143742 | 3597 | 24000/1001 | 1200199/8000 | 899899/6000 |
| R11 | m/MC6y7jwenlE_210.0_360.0.mp4 | 13910673 / 178988 | 4496 | 30000/1001 | 281281/1875 | 899899/6000 |
| R15 | 8/8vUjoQd0fYY_210.0_360.0.mp4 | 12596238 / 149214 | 4500 | 30/1 | 150 | 4499/30 |
| R18 | y/Y2GVVC_cD_E_360.0_510.0.mp4 | 9732406 / 133840 | 3354 | 24000/1001 | 559559/4000 | 3356353/24000 |
| R19 | p/p-III2A1E2o_510.0_660.0.mp4 | 11363788 / 95399 | 3750 | 25/1 | 150 | 3749/25 |
| S08 | q/QXC-pnmOGnM_510.0_660.0.mp4 | 9375930 / 95399 | 3750 | 25/1 | 150 | 3749/25 |
| S30 | e/E6yFTWlChmE_360.0_510.0.mp4 | 10444125 / 95400 | 3750 | 25/1 | 150 | 3749/25 |
| S32 | i/iuH6szYVWw4_210.0_360.0.mp4 | 11469791 / 149214 | 4500 | 30/1 | 150 | 4499/30 |
| S36 | t/TNkHgO68F6U_660.0_810.0.mp4 | 14845458 / 178987 | 4496 | 30000/1001 | 281281/1875 | 899899/6000 |

实际clock schema统一含 `source_path, source_sha256, pts, pts_rational, raw_origin_sec, raw_end_exclusive_sec, physical_endpoint_rational, duration_sec, n_frames, width, height, fps_num, fps_den, endpoint_kind, sequential_scan_seconds`。精确计算只用完整 `pts_rational` 和 `physical_endpoint_rational`；不从float `pts/duration_sec`、最后PTS或 `1/fps` 猜物理终点。canonical `last_frame_duration_exact` 仅为已存精确终点减最后精确PTS，没有新增measure。clock未提供streamindex/timebase；后续真实decode若执行，必须从实际唯一video stream读取并逐帧核 `frame.pts*timebase == original_exact_pts`，不得在此补猜。

R18真实物理终点为139.88975秒，右尾起点124.88975秒；不是文件名名义150秒。现有精确字段已消除17–19窗的不确定性，不重新测量该成功clock。

## 17窗与两种几何

本轮scope固定 `FULL_ORIGINAL_SOURCE_ZERO_ORIGIN_15_STRIDE7_5`。从原源0起排 `[s,s+15)`、s每次加15/2，另加 `[physical_end-15,physical_end)` 并去重，然后仅筛出能触及至少一个原ORDINARY观察点的窗。完整网格剩余窗与O不交；其任何窗内新KEEP也不可能覆盖O。该几何减量只解决原已知点否决，不将17窗等同全生产候选域。

| case | O点 | 原源半开窗口 |
| --- | ---: | --- |
| R07 | 26 | [105,120), [225/2,255/2) |
| R11 | 55 | [120,135), [255/2,285/2) |
| R15 | 25 | [90,105), [195/2,225/2) |
| R18 | 39 | [499559/4000,559559/4000) |
| R19 | 45 | [195/2,225/2), [105,120) |
| S08 | 3 | [0,15) |
| S30 | 13 | [90,105), [195/2,225/2), [105,120) |
| S32 | 4 | [225/2,255/2), [120,135) |
| S36 | 12 | [30,45), [75/2,105/2) |

每窗选窗内全部原帧中的64个不同序号：若eligible为连续n帧、首序号a，则第j项为 `a+floor(j*(n-1)/63)`、j=0..63；PTS直接取原clock。n<64拒绝，不补帧、不重采样、不平移。每个新段必须仍在产生它的原窗内，半开membership严格按真实PTS，没有额外padding。

旧“观察clip内部重新从0排窗”的62视图会改变全源起点和右尾，不能冒充本次17个完整原源网格。旧45 B窗/56段及VERIFY40.46生产回执也未证明与新17输入在源/clock/64帧/像素/张量/prompt/model全部相同；当前可精确identity采用的新B0或VERIFY调用为0。9源默认未来各做一次wanted-ordinal RGB union、17视图各一次首次encode；没有已证明可用的lossless PNG manifest，代码不隐式搜索旧缓存。

## 可执行接口与闭包

`source_audit.py`只用stdlib，提供：

- `load_reference(path) -> full_reference_dict`：实际完整原SHA/大小及40源/3081点重数。
- `audit_source_descriptors(reference, run_root=RUN) -> list[9]`：指定原clock逐SHA核、原媒体只exist/stat，构造来源元数据。
- `load_source_clock(descriptor) -> canonical_clock`：完整原生精确PTS、真实已存fps/end，不shift。
- `point_covering_views(reference, descriptors) -> list[17]`：222个原O点逐ordinal/PTS绑定，完整原源网格、canonical64与全点覆盖。
- `validate_registered_sources(registration) -> (sources, views)`：以 `reference_ref` 原文件重新生成，与登记 `sources/views` 逐项相等；全部原媒体/clock SHA必须进 `required_files`。

descriptor字段：`case_id, video_id, source_group, source_key, source_sha256, source_path, source_bytes, clock_path, clock_sha256, clock_bytes, width, height, n_frames, fps_num, fps_den, physical_end_exact, pts_field='pts_rational', physical_end_field='physical_endpoint_rational', endpoint_kind`。

canonical clock字段：`original_exact_pts`（完整有理数字符串列表）、`original_zero_origin_verified=true, first_original_pts_exact='0', last_original_pts_exact, last_frame_duration_exact, physical_end_exact, timeline_shift_applied=false, native_frames, width, height, fps_num, fps_den, endpoint_kind, source_sha256, source_clock_sha256`。它不捏造streamindex/timebase。

view字段：`case_id='fixed40.<源case>.overlapNNNN'`（每源筛后顺序）、`fixed_case_id`、`source_name=video_id, source_sha256, source_clock_sha256, window_start, window_end, source_frame_ordinals[64], sample_exact_pts[64], window_role='overlap', view_roles=['overlap'], original_grid_index`。B0真实case_id用该唯一view_id；source文件夹仍用R07等固定source case。

登记为 `root/registration.json`，schema `RECALL_FIXED40_EXECUTION_REGISTRATION_V1`、status `REGISTERED_FIXED40_EXECUTION_AFTER_DEV_CONFIRM_PASS`、group=facts、source_scope=EXTERNAL_NONTEST_ONLY、source_count9、unique_input_count17、model_parameters8782459120、optimizer_updates0。保留真实 `main_protocol_ref/authorization_ref/dev_result_ref/confirm_result_ref`、绝对路径SHA `required_files`、全部8个新代码 `required_code_files`。`source_plan_ref`可绑定与登记scope/sources/views相同的独立metadata镜像；适配器本身只用直接登记的sources/views/reference_ref/scope，不依赖旧source_export或proxy四源ref03。

`facts_prepare.py/facts_admit.py`归CPU代理；`facts_common.py/facts_infer.py/facts_verify.py/facts_chain.py`归runtime代理。`facts_veto.py`加入8文件代码闭包，并独立CPU运行；chain不自动调用质量否决或提前准入生产。

## 实际执行证据与纯否决器

否决器只读以下未来真实完成材料，不重做已成功的首次QA：

- `root/execution_export_01/execution_receipt.json`：全17实际inputs，包含input、CPU proof、request、raw、done、first QA各自path/SHA；全N `verification_decisions`含KEEP、UNKNOWN、DROP全部同类引用，不能只导出KEEP。绑定原登记SHA、全17view计划、9源、B0=17/VERIFY=N及唯一自然终态。
- `root/execution_export_01/first_independent_qa.json`：绑定实际execution SHA，采用已经完成的B0/VERIFY首次独立QA，不重新decode/encode/replay。
- `root/facts/B0/{gpu_01,replay_01}` 与 `root/facts/VERIFY/{cpu_01,gpu_01,replay_01}`：原request/raw/done、实际BEGIN/ACCEPTED journal、首次QA及CPU输入。实际resource必须唯一自然completed/exit0且与共享ledger一致。
- `root/facts/VERIFY/verification_export.json`：全部N原生决策；只有完整17个实际B0及首次QA后所有原段真实为空，才允许零VERIFY特例，不创建0-call GPU作业，不把遗漏/失败转空。

`facts_veto.py`采用已完成首次B0 token/grammar/parser QA，重新核原raw SHA、原done/segments和QA逐字节绑定；独立从原段构造全部event_id、绝对有理数端点、真实native范围。再直接按VERIFY原raw的有限canonical响应重新解析每个KEEP/UNKNOWN/DROP，并与request、done、首次QA和导出结果逐项相等；仅显式KEEP进入K。它不重复模型、processor、tokenizer、媒体解码或首次replay。缺任一执行证据/原段/决策/首次QA或分母不完整即拒绝，不能靠“原B帧还在”自动PASS。

`registration.merge_implementation_ref={path,sha256}`必须指向已修正真实基线格式的 `merge_keep.py`，SHA固定 `4b3e5b4ba95d9dff278e7dde6b9d4389a09ea538c10fbee05b427dd1f872d277`，并进入required_files。该实现以 `merged=dict(old)` 保留全部旧对象，仅在 `set(K)-set(old)` 写新帧；UNKNOWN/DROP不贡献新帧，函数末还实际检查旧帧/框对象及ratio原字节相等。基线每行严格含 `video_id,targetRatioWH,predictions,model_params_b` 四字段，`model_params_b` 必须为实际数值8.78245912，并保持其原JSON数值字节。主代理的针对性合成KEEP新增/旧帧框/CRLF/参数写法保持及缺失、错误、布尔参数拒绝检查通过，Linux真实VERIFY ZIP首行与原metadata格式检查通过，见 `merge_actual_schema_acceptance_17.json`；这只是实际schema检查，不是全426产物QA。这里固定实现并证明一般不删除恒等性，不执行一个虚构的本次426合并。

## 原门不变的严格分支

令O为冻结222个明确ORDINARY点，K为上述完整真实执行/首次QA后显式KEEP对应的原生帧并集，B为任意未知的真实VERIFY基线帧集合。合并M=B∪K，故 `B⊆M`，KEEP删除恒为0；且 `(B∪K)\B ⊆ K`。

当 `K∩O=∅`，有 `((B∪K)\B)∩O=∅`，因此对任意真实B，原差分ORDINARY新增必为0。否决器给 `PASS_KNOWN_ORDINARY_SUFFICIENT_CONDITION_NOT_QUALITY`；它是原零阈值的充分证明，不是更严替代阈值，不把D8冒VERIFY，不要求为这分支新增56个真实baseline调用。

当 `K∩O≠∅`，仅能给 `INCONCLUSIVE_NEEDS_REAL_VERIFY_BASELINE`。这些点可能已在真实B内，不能直接称原差分FAIL；当前也不能假PASS。必须另有与真实VERIFY身份完全绑定的基线mask才能判原差集，本实现不推测或自动启动补算。

该新结果不会把原coverage/reference_quality失败改为通过，不称人工GT，不重标UNKNOWN；固定40只提供已知点否决能力。旧 `fixed40_recall_veto_v1.py` 草案要求先提供实际baseline-retention proof的架构不用于迫使本分支额外重推/大传；旧草案保留原状，本文和新独立facts_veto按上述分层证据执行。

科学充分门与一般B∪K证明通过以后，生产426还必须实际使用同一冻结merge，逐来源验真实VERIFY基线的全部原帧、原框对象、ratio及model_params_b原数值字节保持、新增帧有KEEP原生来源、426非空、原PTS/全源场、11strict、8.78245912B、单JSONL/ZIP CRC/SHA/成员SHA及实际预测差异。新否决输出明确 `production_final_QA_already_performed=false`、`production_admitted=false`；这些生产产物在此阶段不存在，不能虚报已验收。

## 本次完成与未完成

已完成一次严格 `aic-inspur-home` 主机身份确认和9个指定clock的小量只读元数据批核、两条指定旧报告路径exist检查；未扫全盘或读媒体正文。本地仅新增两份小量Python实现和本报告，完成AST语法/接口导入、原银标完整SHA与3081→222计数核对及必要纯函数边界检查。

未运行任何新facts CPU准备、decode、encode、clock测量、模型、replay、正式科学否决或生产426；不声明这17窗已成功、固定事实门已通过、独立确认已通过或线上提分。后续实际运行、预算、资源和准入由主代理在原门完整满足后独立登记。
