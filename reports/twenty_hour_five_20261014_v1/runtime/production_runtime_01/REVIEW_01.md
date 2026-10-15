# 单批 runtime 有界审查

8py + README。只新 temporal_production_runtime_v1，input 8py、v3、CV和critic cache库均未改。Linux一次stdin纯检查14项和12文件AST通过，不读取正式source/GT，不load实际tokenizer/processor/模型，不进行cache IO/lease acceptance/release；代码未部署。

原全图1995逻辑上限不等于真实modelcalls；budget逐批按project冻结MODEL请求表实际长度。同source所有ENDPOINT+VERIFY与typed short skip同批，source顺序连续；ROOT容量分批controller和global无遗漏/重复完成聚合不属于本模块。single global GPU job不能提前自然terminal释放RGB的容量冲突已交root；裁决为多批独立自然终态，此实现遵循新裁决，不改变critic自然终态门。

每批一次load原物理8.78245912B base+TIME。TIME/BASE endpoint角色由root开发selection绑定，代码无默认自动选择；VERIFY TIME。全144状态/gradient0/inventory每call核；disable context finally先显式requires_grad_(False)，避免PEFT reenable遗留trainable标志。开始full engine identity、末尾full base+288adapter hash；中间不重复全8B hash。新GPU input storage/layout/alias完整签名由输入层ABI实测，不允许bf16改CPUproof。每次generate独立prefill，无past KV或先前回答。

BEGIN/raw先永久保存，raw/token/score/postcontext失败保留并阻断，不转UNKNOWN；typed no64不BEGIN、不fake actual_model_call。独立output QA只local tokenizer，复用first independent RGB→普通processor证明；不重新encode vision/read RGB/媒体/load模型。strict full-token prefixes、finitegrammar、raw/parser、source/native clock与v3 independent conversion、原VERIFY candidate gating、GPU实际signature/weights/144/grad和唯一ledger同时核。

自然resource和当时完整ledger以原文件字节写permanent/proofs，相对ref SHA等于捕获原字节SHA；附外部source path、UTC与row count/hash。原ledger之后追加不改此immutable snapshot，不重新核成新SHA。每批request/raw/done/CPU/GPU/input-replay/model/terminal refs均在新Store永久区保留。

source_id→video_id严格从输入full_plan原video_id自动一对一0..425映射，要求完整426；不重算event/endpoint ID。输出保留source_id和original video_id，给root package连续空间场映射。旧PTS/geometry/end核继续由input与root package完成，不另读GT或媒体。

close必须先完整batch输出重放成功，再接受所有预冻结consumer；全部accept成功后才调用critic release该批预声明新RGB。不删除canonical/原raw/proof/clock/旧cache，不对失败或部分release自动重试。质量门/线上评分/5包选择仍由root；工程PASS不叫提分或global完成。

接入明确顺序及字段在README：CPU_admission → admit_batch（非GPU许可）→ root GPU_admission/唯一wrapper → infer_batch → terminal byte snapshots → input层first_input_replay每consumer → output-only replay_batch → close_batch。cache policy independent_replay_code_sha256必须冻结为replay_batch.py当前SHA。没有实际426准入或生产执行；父CUDA非空，CPU children只清自身CUDA。