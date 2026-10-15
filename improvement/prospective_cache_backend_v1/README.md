# Prospective exact cache backend

仅用于受控、全部已 BEGIN 子进程自然终态后的新 phase；没有部署或正式执行许可。旧 LC2/INPUT5/PR5/CONTROL5/policy/graph/49 batch 的 bytes 均保留。

`backend.open_store(original_LeaseStore, existing_cache_root, backend_admission_path)` 返回显式新类。它不修改原 module/class/global。独立 admission 必须绑定新实际代码、原 LeaseStore SHA、原 policy/frozen consumer ref、真实 `MAIN_CONTROLLED_HANDOFF_STOP`，以及事前冻结的 remaining producer/accept/lease 子集。parent hold 本身不够。

`save_input` 锁顺序固定 `CONSUMER_THEN_VISUAL_THEN_GLOBAL`。持久 consumer/key guards 从 Linux dirfd/O_NOFOLLOW 打开，nlink=1，不删除；same key 查实际视觉 tensor 并 exact_equal，首次 LUT/gzip/CRC/完整 roundtrip 以及全 dict 重建都在 global lock 外。global lock 仅提交 visual index、最终 manifest 和 journal。private 每 consumer 独立。缺最终 manifest 的残留 payload 不自动重试或删除；读者仍需完整 source commit barrier。

`accept_consumer`/`_closure` 逐实际 manifest、private/visual payload 核 SHA/bytes，保留完整 signatures、首次普通 processor QA、GPU/native/token/raw/weights/resource/唯一 ledger/retained evidence。它们仅省去重复 torch 反序列化/重建。首次普通 RGB→processor 以及 GPU loader 保持原 INPUT5/PR5 全量检查；原 secure release/unlink 方法继承不变，永久 tensor/raw/proof/guard 不删。

`close_phase.py --protocol PR5/protocol.json --batch-id Bnnn --phase-admission CONTROL6/close_phase_admission.json` 仅执行未开始的 close，生成独立 new completion 并明确新 driver/backend/admission refs。已成功 acceptance/release 精确引用，partial release/旧 attempted close 阻断，不自动重做。

新 Linux stdin 合成 fixture `pure_01` 已一次通过同-key 两进程真实 exact dedup、NaN/signed-zero、>256 fallback、global 锁无 tensor 工作、lifecycle 无重建、损坏载荷/不安全 guard/重复接受拒绝。没有正式输入、processor、媒体或模型调用。新增 first-QA status/CPU proof/call-count guard 仅按原真实 schema 加强，未重跑已成功 race fixture。
