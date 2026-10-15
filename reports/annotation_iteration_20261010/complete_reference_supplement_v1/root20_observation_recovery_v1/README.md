# ROOT20 observation-only recovery

最终观察层入口是 `recover_observation_v2.py`，实际已完成并 x 写 `observation_receipt_v2.json`。禁止重复成功运行；入口发现任何已存在完成或部分成功产物会拒绝，异常会 x 写带 traceback 的唯一 failure JSON。v1 source/receipt/artifacts 均保存为历史，不覆盖。

此目录只恢复原 CLI36 的观察来源。状态固定为 `OBSERVATION_ONLY_PENDING_ROOT_NEW_SEMANTICS`，不是 teacher instruction compliance、semantic truth、reference admission 或 whole CLI PASS。原 w20 scope、group04..15 schema failures、原 proposal schema errors、whole CLI rejection、20 crosscheck blocker 均不变。派生容器只将原 bare four-dict list 包入 group/items，全部64原 nested item 值保持；不声称新序列化字节等于原 JSON 字节。

实际证明覆盖：1035 frozen inputs 当前 SHA、request/root gate/index/prefix identity、全部202 ACTIVE/DONE literal tool identity 与顺序、全部文本完整 LF/bytes/marker/ACK 独立 response、原写入 snapshot 不变、两窗32组四图同 response 与下 response fact write、两窗 clip 与各两批4 effective view、20全部64 source ordinal/exactPTS/sourceSHA/PNG身份，以及原64 processor patch_inverse receipt。72 PNG RGB/geometry成功检查从原不可变 audit exact引用，64student PNG/tensor/processor identity从原CPUreceipt exact引用；当前只哈希字节，无模型、processor、native/video/PNG decoder 或图像查看。

`bound_fact_rows64_v2.json` 为64行 list，每行绑定 original identity、原六字段 facts、原及 immutable sealed raw output、实际工具屏障、native pixel proof 和实际student64身份。`derived_fact_containers_v2.json` 为16个容器来源记录。`independent_cpu_proof_v2.json` 为完整 tool/text/group/clip/effective provenance。`rejected_teacher_history_v2.json` 保留原 schema/proposal 拒绝，不能将原 proposal 改为合法 KEEP/NO/UNKNOWN 或给其补默认意见。

新 ROOT reference geometry 状态仍为 `PENDING_ROOT_SEPARATE_REFERENCE`；ROOT 必须另签实际语义、像素、完整有限编辑 partition/NO/UNKNOWN、reference geometry 与原 silver.verify_window 验收。F15..18 consequential UNKNOWN 不因容器恢复清除。既有 blind attestations仅绑定，不制造新的 blind judgement。此脚本不创建 ref/maindecision/registry/admission，不修改 silver/quality/science 合同。

13项纯逻辑测试实际通过；测试覆盖原 fact_items 包装/字段/slot/subtitle拒绝，以及 ERROR/unfinished/duplicate/outside/literalidentity/same-response/factwrite屏障。v1/v2被测纯 helper AST相同。实际CPU执行与序列化原值逐项对照记录在 `validation_manifest_v1.json`；独立静态 review 由另代理写 plan_review，ROOT 最终审理另行负责。
