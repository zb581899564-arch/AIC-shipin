2026-10-15 本地实现回执：

- 所有修改限定本目录；没有 SSH、下载、decode、processor encode、真实 CPU 输入准备、GPU、launcher、封包或 Goal/自动化操作。
- 新 `positive_contract` / `positive_grammar` 独立 namespace；原旧文件不覆盖。新正面准入关注完整候选减去原 baseline 的全部 novel native runs。原端点保持、baseline 不交给新决策删除、UNKNOWN/DROP 不新增。
- 每个 novel run 从原 PTS + next PTS/physical end 映射并 clip 在原候选内；prompt 给出每段 local spans、原采样 native ordinal 和 local PTS。任何 run 没有可见 sample 时 canonical grammar 硬禁 KEEP，只允许真实模型 UNKNOWN/DROP。当前十条实际候选据主线程 inventory 均有可见 samples。
- 采用完整原 26 B0 / 37 VERIFY 的终态、共享 ledger 与旧首次 QA 证明；仅 old overlap KEEP 且存在 baseline 外真实帧才新调用。数学无效候选保留完整分母审计，不按参考标签选择。
- 新 token 缓存 exclusive create，reload/signature 验证。独立 partition + tokenizer.encode 首次 new-input QA 在 GPU 前，新 prompt 的视觉和原生时间 prefix 均保持逐比特相同。GPU 后只 output token/grammar/独立 parser/native QA，引用首次输入证明，不再 tokenizer input encode 或旧 vision processor。
- `positive_chain.py` 仅 dev，父 CUDA0 与独立 CPU 子进程 own CUDA mask；现有唯一共享 GPU wrapper、自然 completed/exit0、唯一共享账本。工程失败保留 raw/failure/success 并阻断；没有 UNKNOWN/EMPTY/repair 或自动恢复。
- 全部八门精确采用主线程 active `protocol_v2.json` 的 gate 字段，含 macro precision 不降、recall 至少 0.01、逐源 F1 最低 -0.01、最少 2 个实际新增来源。dev PASS 只冻结待首次新确认，不自动 fixed40/426/ZIP。
- 已执行 `python -B improvement/recall_positive_admission_v1/check_pure.py` PASS：精确 novel runs、UNKNOWN/DROP 不新增、零可见 sample 禁 KEEP、严格有限 grammar、原 baseline 与旧 source_prediction 合成一致性、完整八门及精度失败拒绝。
- 已对 8 个 `.py` 执行 AST syntax 检查 PASS。实际 Linux 元数据适配、tokenizer roundtrip/input budget、GPU/科学质量尚未运行，不能称已验收。

主线程在真实准备前仍需核 registration 的路径/SHA，尤其原 `reference_completion_dev.json` pointer 与目标 completion 两层 SHA 分开绑定；README schema 允许 pointer 或目标 receipt，但不能使用 inventory 同名字段覆盖后的摘要当原 ref。
