本目录只准备未来 binder6 的配置。没有执行 binder/cache/模型/封包，没有创建许可或 PASS，旧 config_draft_01、绑定、代码和成功产物不改。

当前模板是 config_template_01.json，24,909 B，SHA256 a8f777bb5d288a7c521fbafa7c63841acfb631c1872006a4347e13ab811069fb。它的 schema 为 TEMPORAL_FAMILY_PACKAGE_BOOTSTRAP_CONTROL6_V1；发布根仍为 /home/inspur/aic_video_work/twenty_hour_five_20261014_v1/temporal_family_native_package_v3。不要把模板本身作为最终执行配置。

已绑定的实际范围：

- CONTROL6 registration.json：63cce177d3dc407c18e6ef28a5049c8bad4e1a7661d3c6fa7ddf0c69ceeff09a。
- quiescent_handoff_completion_01.json：df9918aaa9b3caeda1c9fb7fb3cd23838d8ff7d3490710b856907d8fa9cd369c；原 CONTROL5 是受控 STOP，不能补造 failure 或 natural completion。
- INPUT5 原 registration/full_plan/plan_completion/cache_initialization、PR5 protocol、BOOT2 成功 completion、原 D8、原场四文件、固定 history receipts 沿用旧模板；不重新计算旧 ZIP canonical，也不复制 raw/tensor/source 媒体。
- 426 sources / 521 windows / 665 events / 1995 logical requests / 3 structural / 1992 unique MODEL / 49 source batches 保持。
- 新调用预算 1959，实际继承的原 B000 为 33 请求。B000 原冻结 batch 文件的 path/SHA 已写入模板；最终必须验证 new 1959 + adopted 33 = total 1992，不能把 CONTROL6.actual_new_model_calls 当作全图调用数。
- handoff 中 19 个实际 SOURCE_PREPARE completion refs 已明确列入模板。旧 SOURCE 的 producer provenance 只能保持原状，null 只允许这些精确继承成功；新 SOURCE 必须由其首次 completion 声明实际 phase/backend/admission 与原 prepare code，不能向旧 completion 补写新 writer。
- CONTROL6 的 148 项完整 required_code_files 通过实际 registration ref 闭合，其中 backend/close/SOURCE/control6 新增 13 项的精确 map 也保留在模板。实际 SOURCE/close/backend/main 四个 admission leaf 均已绑定；不重复创建它们。

自动补 SHA 的位置只有以下四处，机器可按模板的 `_root_auto_fill_only_after_real_natural_terminal` 映射定位：

| 字段 | 实际文件与前提 |
| --- | --- |
| production_completion_ref.sha256 | CONTROL6/exports_01/global_completion.json；必须是真实自然 PASS_COMPLETE_ALL_PROSPECTIVE_TEMPORAL_REQUESTS_AND_FIRST_INDEPENDENT_REPLAYS |
| controller_completion_ref.sha256 | CONTROL6/run_01/completion.json；必须是真实自然 PASS_CONTROLLER_ALL_BATCHES_NATURAL_TERMINALS_AND_FIRST_REPLAYS_NOT_QUALITY，并绑定上一文件的同一 SHA |
| package_document_refs.authorization.sha256 | ROOT/authorization.json；由主控另写本轮真实风险授权，不自动批准，不声称质量 PASS |
| package_document_refs.official_rule_check.sha256 | ROOT/official_rule_check.json；由主控在封包前另写当前赛规核对回执，不用旧其它 scope 的回执冒充 |

主控的已有自动接续逻辑应在两个实际终态完整、自然写完后，读取其现存精确字节计算 SHA256，再验证以下字段。PID 消失、部分 GPU resource completed、部分 QA 或原 CONTROL5 STOP 都不能打开此门。

1. GLOBAL engineering_failed_requests=0、missing_requests=0、physical_model_parameters=8782459120、optimizer_updates=0、test_GT_or_annotation_read=false、native_clock_matches_original_full_PTS=true、old_packet_FAIL_reclassified=false、scientific_quality_claim=false；native_terminal_scope 保持 V5。
2. GLOBAL 的 actual_unique_MODEL_ids/proofs 为全图精确 1992，结构请求精确 3，source/event/endpoint/VERIFY 与原 graph 完整闭合；first input/output QA、全部 raw/自然 resource/immutable ledger、7 个 native/original bindings 均实际存在并通过原科学门。
3. CONTROL6 actual_total_model_calls_in_original_graph=1992、actual_new_model_calls=1959、old_successful_operations_repeated=0。GLOBAL 保留原 CONTROL5 registration、真实 handoff、实际新 source/close/backend code/admission refs；33 个继承调用只通过原 B000 的自然成功与独立 QA 证据引用。
4. 原 CONTROL5 的 run_01/completion.json 与 failure.json 均不得为此人为创建。held parent 的旧 BEGIN 未记 COMPLETE 时，只能由 handoff 中另有真实自然子终态和成功 receipt 的该原操作收口，禁止重新执行。

补齐四个 SHA 后，主控另创建新 Linux final config_01.json，保留模板和旧 draft 不动。四个字段应全部为实际小写 64 位 SHA，不能留下 null、PENDING 或虚构值；其他冻结字段不修改。`draft_status`、`_pending_fields`、`_root_auto_fill_only_after_real_natural_terminal` 可作为历史说明保留，或在新 final config 中另记已完成字段；它们不能代替 binder 的真实 gate。

未来部署仅需新 binder6 两个运行文件（不在本任务部署）：

- CAMPAIGN/temporal_family_package_bootstrap_control6_v1/code/bind.py，30,151 B，SHA1134e2547388e76ad1ae3695cb4eea12d64f29e33102d756c0f5f26fd5ab7285。
- 同目录 control6_chain.py，9,612 B，SHAaa54c24cf26beee2bd71ef809c6b67c7177f91d51a433f2f4ee754286aa3d4ac。

原 ROOT/code/package_family.py、combine_events.py、protocol.json 只在缺少时部署相同冻结字节；存在相同成功文件即复用，冲突停止。最终 config 的 required_binder_code_files 必须包括上述两个实际新 writer。CPU 子进程独自 CUDA_VISIBLE_DEVICES=''，不改父/GPU 环境。

未来唯一 binder CLI：

```
python /home/inspur/aic_video_work/twenty_hour_five_20261014_v1/temporal_family_package_bootstrap_control6_v1/code/bind.py --config /home/inspur/aic_video_work/twenty_hour_five_20261014_v1/temporal_family_package_bootstrap_control6_v1/config_01.json
```

这条命令只在主控另行批准且上述真实终态与四 SHA 全齐后执行。binder 技术完成会首次生成 package_inputs/history/source_package_lock/technical_preparation_receipt；之后主控仍须独立作规则、风险和已知严重劣化否决判断，才可创建 ROOT/package_admission.json。模板、手册和 binder 都不能自动创建此最后许可，也不能提前宣称新 ZIP 或 Goal 完成。
