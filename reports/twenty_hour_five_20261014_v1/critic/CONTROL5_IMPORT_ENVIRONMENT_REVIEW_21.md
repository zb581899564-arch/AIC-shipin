# CONTROL5 原依赖环境恢复专项审查

静态结论：仅新增 CONTROL5 和显式原 helper 环境的恢复范围合理，未见环境传递或模块归属方面的已知阻塞。input5、runtime5、原 49 batch/index、已成功全局 graph 与 cache initialization 可继续按原 SHA 引用；本审查不启动 source/processor/model，不重复 metadata build。

真实故障是原 pilot runtime 导入 exact_pts 时缺少 baseline_a_pts_v1 查找路径。原 runtime 只插入 b_score 与 balanced 两个目录；lb_io 已明确核 exact_pts/native_frames 的真实 owner 是 baseline_a_pts_v1。实际十个 log 同类 ModuleNotFoundError 和只读 no_source_artifacts_diagnosis_01.json（SHA `1c54f5b73205c8a73223acf24ad8df2d348d6a80a5f4ad4185c07a826e024c01`）共同限定本次恢复：八类 source/native/RGB/clock/CPU/replay 产物均零，失败发生在 source launch、解码和 processor 之前。没有已成功 source 阶段可重做。

CONTROL5 的 explicit_child_environment 是固定、非空、无 cwd 空项的六个原 RUN owner 目录，替换 PYTHONPATH，不追加未知继承项；另设 PYTHONDONTWRITEBYTECODE=1 和 AIC_WORK_ROOT。Runner 对所有子进程先应用相同冻结环境，CPU 子进程再仅清自身 CUDA 并限制 import/CPU 线程；GPU wrapper 保留父 CUDA。现成 wrapper 源码回执的 102/112 行显示其以 os.environ 构造 env 并传给 Popen，没有覆盖 PYTHONPATH，因此 infer 子进程获得同一依赖路径。

source5 的 source_conversion 仍先从原 b_score 绝对路径载入 common/source_color 并检查 namespace owner；旧 legacy_runtime 继续检查 engine/contracts、bw_video、exact_pts/native_frames 各自的真实模块路径。新路径没有替换这些文件或关闭检查。恢复 receipt 另锁 exact_pts→pts_contract→a_contract→vendor/p2j_core、原 temporal_sft8b_v1/sft_contract 等实际 transitive owner；new required map 必须保留全部原 125 SHA，再冻结 CONTROL5 与已测原 owner refs。

新注册保原注册除 schema、code map 与新 admission path 等恢复控制项之外的 graph/batches/role/budget/cache/input/runtime 字段；原 CONTROL4 注册、FAILED terminal、20 行 journal、10 个 log 和零产物回执继续引用。原 batch_index 仅允许 CONTROL4/batch_index.json 这个精确成功 leaf；不开放旧根任意元数据。新 run_01 journal 与 aggregate/control_v5 路径独立，旧代码及失败不热改。

49 个冻结 job name 仅可在 root 确认原 ledger/active 中未启动后沿用。此处不是恢复任何成功模型调用，也不是 whole metadata 重启；若以后出现实际 source 成功或部分 decode/processor 产物，应按该实际新失败单独处理，不能套用本次零阶段恢复。

审查时提醒作者核现成 journal 的 BEGIN/FAILED 同序断言：并发完成顺序一般不受开始顺序保证。本次若真实十条终态恰好同序可通过；无需为了审查重跑来源或修改失败事实。

实际服务器新注册/owner SHA 校验、root 具体 admission 和第一次 source 准备仍待执行。本审查没有导入 Torch/runtime、没有 pure 重跑、媒体/权重体哈希、解码、processor、GPU 或封包；不宣称运行通过或质量改善。
