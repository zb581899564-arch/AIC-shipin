独立新 activation driver 已完成，实际 admit/processor/media/model=0，未部署。仅3py+README，原 local_boundary_v1/v2/v3 和 Charades 代码、输入、GPU、source locks 均不改。原 v2 全8文件逐 SHA 与原 manifest03 保持。

可执行接口：run_ablation.py --root 固定新Linux root --stage admit|infer|replay。admit 只绑定原已成功 smoke 的2个 accepted CPU cache/proof 与2个 TIME raw/request/done/replay、原GPU唯一终态和ledger、原source/input-lock完整字典、原runtime/processor资产以及新protocol/code。成功 input replay 复用，不读 source/NPZ 或重新 encode。主控之后独立写 gpu_admission 并共享唯一 wrapper；没有自动GPU启动器。

infer 显式核 actual physical8782459120/loaded adapter15335424/activated base8767123696，不卸载。每次 context 前/中/后记录实际 all144 False/True/False及同layer names，前后 full frozen base SHA 和288adapter tensors实值核查，严格 finally 恢复。generate 调用只有一个site且在 disable context 内；保持 frozen v2 prompt/frame/token/grammar/原 generate kwargs，独立prefill，不供 prior outputs/past KV。raw 保存后才解析，失败 raw/成功项保留，无UNKNOWN/空候选fallback。完整2call分母后才完成。

独立 CPU replay 不 encode、不 decode pixels、不调用模型，只读取旧accepted缓存检查signature并复用原成功input replay，核新真实token/score/finitegrammar/raw/原independent_endpoint、context状态和weights/唯一GPUledger，输出对应TIME/disabledBASE行为与charged_seconds。没有GT、F1或质量门；更多变化不当PASS，旧base-only12 STOP/费用不变。

一次Linux in-memory纯静态/合成检查通过：3AST；all144前中后及合成exception恢复；7个拒绝（143层、假状态、卸载adapter/物理参数改变、超过2call、变化作为质量门、旧coarse hypothesis、把物理数当base数）；AST确认唯一generate site在disable context，output replay无input encode/media/model call。未执行真实admit/source/cache/model。

当前新 coarse.py 与 v3 accepted_event 的叶级证据字段兼容：非空done status MODEL_OK/case_id/segments/source_start_exact/source_end_exact/input_evidence/raw/request SHA，CPU proof/真实raw/request的input_evidence及CPU_proof_sha256，replay case_id/status PASS_/CPU_only/new_model_calls0/done_sha256/raw_sha256/input_evidence均具备。v3 whitelist已包含 Charades boundary_v1/v2与charades_coarse_v1，不缺新的coarse GPU/replay root；LEGAL_EMPTY只留源覆盖、不造event。source_separation还须主控 canonical PASS receipt、known_current_b_training_and_426_test_identities_complete（或known_identity_complete）真及交集为空，clock_object_keys使用原wrapper ['clock']；不需要改已冻结v3清单。

预算限制：旧smoke2原83.02639秒包含cold load/hash，而generation仅3.86/3.38秒。此driver额外每call context前后完整weight hash，主控须按新协议保守预留总秒并实际记账；不得用generate秒冒充完整job成本。科学假说批判参见主控critic的LOCAL_ROLE_ACTIVATION_CRITIQUE_07.md，2call只接口/activation行为诊断，不证明TIME偏置或BASE质量。
