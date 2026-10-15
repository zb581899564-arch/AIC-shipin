# 条件候选包实现范围（尚未启动推理）

实现当前 `runtime/` 中新的 `candidate_*.py` 文件；不要运行历史 launcher，不修改既有冻结目录。训练与独立质量门成功之前，候选入口必须拒绝模型加载。允许本地纯 CPU/stdlib 验证；所有真实模型和 426 推理由主控另行准入。

## 身份和准入

- 当前 config/source_lock 与已实际接受的 CPU preflight、唯一 final training receipt、24 个最终非测试比较回答、evaluation receipt 和 scientific_gate 都须 SHA 绑定；质量门必须 `PASS_FIXED_SILVER_QUALITY_GATE`，不是仅 engineering PASS。
- `common.admit(..., phase='candidate')` 已支持 config 的全新 `candidate_output_dir`。输出路径不得存在。训练/评估内容必须自然完成，原 B 的 adapter SHA不能作为新 final SHA。
- 固定模型 Qwen3-VL-8B，base/vision hash、288语言 LoRA参数、保存后重载身份、4或6次真实更新、原 prompt/grammar/greedy/input16384/output256/像素预算都继承。新整个模型参数按共享 base计一次。
- 旧 B 时间回答一条也不能视为新 final 回答。全部复赛426源、521窗实际新生成；允许复用原生输入准备证据，但不能复用旧输出。所有真实 GPU 作业沿用现有 resource_runner 的独立实际终态费用账本，本实验条件426预算7200秒，总10800秒。

## 原生窗口与结果

从历史 `balanced_two_window_risk_v3` 的实际冻结计划取426/521身份。只有原恰好两窗且30<总域<60秒的窗使用精确 Fraction 中点均衡及 `bw_native.decode_balanced_window` 规则；其他窗使用原 student native decoder 和原 processor 编码，不将 bw decoder 强用于未变窗口。原source97色彩白名单、顺序native PTS、floor64及half-open域不变。

changed116输入与旧balanced实际CPU输入证明核对；其余405窗与原native身份/processor证明核对。new model生成必须独占保存raw/token IDs/input evidence，随后原grammar/parser及独立exact native集合校验。合法空段支持；失败永不转为空，也不补裁段/并集/epsilon。首条真实回答须有独立 CPU原生/processor/token/parser回放入口；不重复模型生成。所有521回答都须绑定当前final adapter、当前code/config/source lock。

## 空间与包

历史 `b_score_aligned_package_v4/rematch_01` 的时间独立完整空间源场可 exact引用，新的空间模型调用0；检查实际源、field算法、requests、原空间模型、全部相关文件 SHA。原空间18723.876秒及历史时间/训练费用保留。不要直接执行旧 packager，它硬编码原B/optimizer0/旧source lock。

用当前新时间选择在完整源场 compose 所选框，保持原最大anchor gap8、16:9与9:16比值字段及原 provenance协议。全部426记录、所选key集合、顺序/唯一性、框/来源/provenance、单文件predictions.jsonl、ZIP CRC与解包回合等原11strict接受；需独立最终验收入口核对包、文件与实际回执SHA。

新包命名包含当前候选身份，真实训练步数/模型 SHA，不声称新optimizer0、不把旧37.66当新官网分。官网分UNKNOWN、自动官网提交false、生产替换false。旧37.66包保持原字节作为备份，不用它冒充新模型改善。

## 实现与验证

历史实际源码本地只读镜像：`G:/ai/AIC视频/reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z`。若镜像不全，报告确切缺项，主控只读取对应远端文件；不猜 API、不整体同步模型/源数据。

当前 runtime 未冻结，新增 candidate模块必须在最终 Linux projection与source_lock生成之前纳入全部Python文件锁。任何后续代码修复均独立版本保留失败证据；不覆写已封存成功代码或回执。代码可先实现，不能创建伪 final training/evaluation/quality回执或启动实际推理。
