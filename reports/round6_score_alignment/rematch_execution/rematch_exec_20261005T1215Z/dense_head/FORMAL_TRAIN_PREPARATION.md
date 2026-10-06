# 正式 C 入口准备：当前拒绝开训

`train_dense.py` 已准备，**没有启动正式训练**。当前数据审计为 `STOP_C_FORMAL_BCE_UNKNOWN_NEGATIVE_SEMANTICS`：未知范围不能变成负例，当前808行不能直接喂给BCE。本次只做代码、stdlib/CPU/AST拒绝验收，不加载模型、调用GPU、解码视频、创建optimizer或评估模型质量。

`test_formal_cpu.py` 的7项测试通过；其中真实读取当前 `data_audit/gate_decision.json`，故意让admission的布尔字段为true，仍被数据STOP拒绝。新Python进程证明拒绝后 `torch/transformers/peft/decord` 全部未导入、config及训练manifest未打开。AST确认训练栈仅在admission之后调用的 `execute()` 内导入。模板admission为false，全部训练超参数为null，不能直接运行。

## 入口及拒绝顺序

```bash
$PY "$RUN/dense_head/train_dense.py" \
  --admission "$RUN/dense_head/formal_admission_TEMPLATE_DO_NOT_RUN.json" \
  --config "$RUN/dense_head/formal_config_TEMPLATE_DO_NOT_RUN.json" \
  --admission-check-only
```

这个命令的预期结果是 `REJECTED_FORMAL_ADMISSION_OR_CONTRACT`、`started_runtime=false`、退出码1。即使将template中的布尔值改成true，其他证据/哈希缺失或当前STOP仍拒绝。不能改gate状态或捏造证据让它通过。

`formal_contract.admit()`只用stdlib，依次检查：

1. 主控admission `formal_c_bce_admitted is True`、schema `aic_dense_formal_admission_v1`、scope `FORMAL_C_TRAIN_ONLY`。
2. 绑定SHA256的数据gate必须为 `PASS_C_FORMAL_BCE_SUPPORTED_WEAK_SUPERVISION`，formal标志为true；`complete_observation_status/generic_highlight_negative_semantics_status/usage_basis_status` 均PASS，`teacher_negative_rows/verified_observation_rows/known_negative_frame_count` 都大于0。
3. admission绑定run config的SHA256和run_id；data gate绑定目标dense train manifest的SHA256。
4. 只读旧704训练清单，固定SHA256为 `ef427866153a9601be01b6e12356951c2fb56730525b0d7b7c353651c2930ddf`，602个来源组的排序JSON SHA256为 `3bfa284165cd088afb2b5872288e733053af192e6dec9926a2008ab795e34264`。不得重切外层划分或替换704集合。
5. 来源隔离metadata certificate必须PASS并绑定这两个固定hash；train-dev与train-confirm来源组交集为空，`confirm_labels_read_by_this_admission=false`。入口不打开dev或confirm标签，证书只是主控既有来源隔离证明。
6. 真实8B工程报告必须 `PASS_REAL_8B_SYNTHETIC_ENGINEERING_ONLY`、固定revision、总参数8,782,983,665。CPU toy通过不能充当这个门。
7. 目标train manifest每个window、源媒体、完整PTS索引、观察/负语义/使用依据证据，以及完整格目标/mask回放通过结构和哈希合同。
8. 模型下载receipt必须COMPLETE_HASH_VERIFIED，绑定固定revision与model_dir。runtime才独立复核权重文件，且始终local_files_only；源码不下载或安装。

所有证据对象使用 `{path,sha256}`；逐window证据还带 `status:"PASS"`。证书只能是metadata `.json`，不能指向dev/confirm标签 `.jsonl`。两个train manifest对象还需 `split:"train"`，文件名含独立train词、不能含test/dev/confirm/holdout/val词。

## 冻结run config

`formal_config_TEMPLATE_DO_NOT_RUN.json` 列出所有字段，未提供全训默认数值。主控须在有非测试证据后冻结epochs、steps、停止模式、lr、grad_accum、AdamW betas/eps/weight_decay、梯度裁剪、seed、scheduler/warmup/min_lr_ratio、单作业wall stop、窗口/格长度、选帧上限、pixels/token上限、decoder threads和PTS容差。共享资源准入与GPU账继续由主控排队入口执行。

固定技术结构：BF16基座、SDPA、rank16/alpha32/dropout0.05，仅语言q/k/v/o LoRA、冻结视觉/embedding/基座、`use_reentrant=False`，共享4096→128→1头。optimizer只持有LoRA与head；不增token，不启用modules_to_save，不merge，不保存全量基座。

`stop_condition=MAX_STEPS`要求在明确epochs上限内达到指定有效更新数；全UNKNOWN累积不增加该计数，耗尽epochs仍未达到则失败。`stop_condition=EPOCHS`要求完整固定epochs结束；提前触及optimizer cap则失败。wall stop为失败边界，不把截断作业写成完成。前3次有效更新检查head/LoRA B首步与LoRA A后续梯度；LoRA A首步零梯度不误报断连。

## 训练manifest合同

每行需以下字段，不从原始未知标签猜补：

```text
window_id, sample_id, split="train", label_status="WEAK_TEACHER"
source_group, source_path, source_sha256, pts_audit_status="PASS"
pts_index={path,sha256}
window_start_pts, window_end_pts
frame_ids=[已预登记的原始源帧ID，严格递增、偶数数量]
exact_frame_pts=[与完整审计索引逐项相等的真实源PTS]
exact_frame_end_pts=[与完整审计索引逐项相等的源帧结束PTS]
observation_evidence={status="PASS",path,sha256}
negative_semantics_evidence={status="PASS",path,sha256}
usage_basis_evidence={status="PASS",path,sha256}
grid=[{start_pts,end_pts_exclusive,known,target,source_frame_ids,
       known_positive_frame_count,known_negative_frame_count}]
```

sample_id必须在旧704清单中，source_group/source_path与该样本原记录一致。index必须为PASS、绑定source_sha256，列出完整 `source_frame_ids=0..N-1`、`frame_pts/frame_end_pts`及用于processor元数据兼容的真实 `source_avg_fps`。不重跑908条历史PTS审计；需要从已核验索引导出这一显式合同，现有字段缺失时拒绝。

观察证书须绑定源媒体hash，`complete_observation=true`、`observed_start_pts/observed_end_pts`覆盖真实窗口。负语义证书须 `semantics=GENERIC_HIGHLIGHT_UNSELECTED_AFTER_COMPLETE_OBSERVATION`、`query_conditioned=false`、`forced_top_k=false`。使用依据证书须 `rematch_training_use_permitted=true`。这些PASS判断由主控依据真实证据给出，训练程序不自行制造。

完整格目标必须是其全部源帧弱二值标签的正帧比例；两个帧计数之和等于格内源帧数，target等于正帧数/总数。grid的源帧ID必须与完整PTS索引按 `[start,end)` 回放一致。格超过真实窗口、无源帧或未知范围，known=false且target=null；UNKNOWN不自动写0。目标manifest整体必须具有已证负帧支持，不能用全正格绕过数据门。

## 精确PTS与processor身份

Qwen4.57.1原生processor按 `frames_indices/fps` 得到时间；这不适合把可变帧率源时钟伪装成平均fps时钟。`exact_pts.py`只在本processor实例的单次调用中绑定 `_calculate_timestamps`：

- 预选frame IDs与完整已核验PTS索引逐项相等，不重新按fps选帧。
- Decord CPU按这些源帧ID读取，frame count与完整索引一致；`get_frame_timestamp`的起止与精确索引在显式冻结的有限浮点API容差内一致。
- processor仍收到源fps作为API元数据，但展开时钟直接使用 `source_pts-window_start_pts`；每个temporal pair的时间为真实局部PTS平均。它不会用 `frame_id/fps` 替代时间。
- 任何processor重采样、frame ID/fps/merge改变、零次或多次视频展开都拒绝。选帧数须偶数，以免静默补帧。
- query从最终processor展开ID读取；不截断，超过配置token上限立即失败。逐window保存source hash、选帧IDs、精确PTS、decoder PTS、temporal patch PTS、query indices与grid源帧回放。

当前只通过CPU toy可变PTS与恢复/身份拒绝测试；正式入口的真实媒体decoder→processor适配尚未运行，不声称这一链已验收。

## 实际循环与产物边界

代码准备了固定shuffle seed的epochs/累积循环；整个累积批次按已知格数归一化BCE。全UNKNOWN不forward、不optimizer/scheduler step。训练过程中源文件size/mtime、冻结基座全字节hash、配置/admission/源码hash都受检查，异常保留失败report和已生成身份/更新日志。

仅在完成明确停止协议后保存 `adapter/`、`dense_head.pt`、原run config/admission、environment版本、源码hash与产物hash。`source_processor_identity.jsonl`与`updates.jsonl`是执行证据；没有checkpoint择优、dev/confirm评估、真实测试推理、提交包或官方成绩。`COMPLETED_FORMAL_C_WEAK_TRAINING_NOT_QUALITY_ACCEPTANCE`只表示获准弱监督训练按协议完成，不能表示模型质量通过。

当前允许的结果仍是：**入口准备与STOP拒绝通过；正式BCE未获准且未启动。**
