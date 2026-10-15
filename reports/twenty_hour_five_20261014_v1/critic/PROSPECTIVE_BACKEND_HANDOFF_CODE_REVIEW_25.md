# 新缓存与剩余控制的静态审查

范围：只读 `prospective_cache_backend_v1`、`temporal_production_phase_v1/source.py`、`temporal_production_control_v6` 的新代码及必要旧接口。没有运行纯检查、读取真实媒体/张量、解码、processor、模型、launcher 或发送进程信号。此回执不授予生产准入，也不构成效果或科学通过。

## 已确认的窄接口

- SOURCE 的 FunctionType 副本共用一个新 globals 字典，原 module-local helper 都通过新 IO facade；原函数 bytecode/defaults/closure、旧 module/class 保留。新 writer 的实际代码身份由 phase/backend 回执声明，不能声称旧 prepare.py 直接使用旧 backend 执行。
- 在 `libraries(cpu=True)` 前校验原代码、全图和未启动 SOURCE；旧 launch、native、RGB、clock、CPU input、canonical manifest/private、lease 或结构结果存在即拒绝整源隐式重试。新 SOURCE 只处理预登记未启动集合，旧成功以 REUSE 保留。
- structural UNKNOWN 原 body 不追加字段；独立 producer companion 先写，SOURCE completion/failure 再绑定。普通 proof 和 canonical metadata 加入实际新 writer 身份；preprocessing code 复制原 map 后只追加两份实际新代码 SHA。PR5 的既有字段、完整 signature 和首次独立 QA 接口兼容。
- backend 用 consumer→visual→global 的持久 Linux flock 顺序；重打包和完整精确 roundtrip 在 key 锁内、global 锁外，同 visual key 仍实际重建并 byte-exact 比较。manifest/index/journal 的提交保留短 global 互斥，没有反向取 key 锁。
- byte-only lifecycle 仍核实际 canonical manifest/private/visual 的 SHA/bytes，并要求首次 ordinary processor、GPU/tokens/native/raw、唯一自然 completed resource/ledger 和全部 frozen consumer。继承原安全 staging unlink；实际新 close/backend refs 进入新 closure/global completion。它不替代生产保存或首次输入 QA。
- SOURCE/backend/C6 都要求真实 `MAIN_CONTROLLED_HANDOFF_STOP`、全部已开始子进程自然终态、active old writer 为零及旧调度停止；parent hold 本身不能准入。新旧 writer 不应同时运行。

## 实际发现及处理边界

1. C6 SOURCE adoption 最初将实际 completion 的 dict-entry 列表与 request-ID 字符串列表直接比较，会拒绝真实旧成功。作者已改为按 `entry.consumer` 比较顺序，并逐 entry 核 CPU proof、manifest 和 frozen lease；已静态读回该修复，未实际执行 adoption。
2. C6 每个 first-input-QA 子进程最初调用完整 handoff load，重复扫描全部 adopted SOURCE 的 canonical 大载荷。这是代码可见的新吞吐瓶颈。已静态读回新增入口：parent 完整 load 成功后 create-x 写 `parent_handoff_validation.json` 并由 launch claim 绑定 SHA；QA 子用 `io.load(child=True)` 核 registration、全图、quiescent ref、原 adopted 小完成回执及实际代码 map，不扫其他 consumer 的 canonical 大载荷。本 consumer 仍进入未修改的 INPUT5 first_input_replay，保留普通 processor、canonical 完整 signature/bit-exact 首次 QA。该修改没有实际运行或性能测量。
3. 后续现有 package binder 仍只接受 CONTROL5 两份自然 completion，且将 `actual_new_model_calls` 与全图 actual-ID 数直接比较。CONTROL6 合法采用已完成 GPU 后，两处都会假拒。已通知 binder 作者使用独立版本准确绑定 CONTROL6，核 original-graph total、new calls 和 adopted unique calls 的闭合，保留真实旧 controlled STOP；不能补写旧 CONTROL5 PASS 或把 new calls 冒充 total。此问题不要求重建全图或重复模型。

## 控制恢复要求

旧 journal 每个 BEGIN 必须对应真实自然 exit-0 和原完成证据，未知 BEGIN 不得重启。已成功 GPU job、SOURCE、first-input QA、output QA、accept/release 分阶段继承，不能整链重跑。旧父应持续停止或在已核所有子自然结束后明确 relinquish；旧失败和 controlled STOP 不冒充自然 PASS。新 admission/registration 必须绑定实际 phase/backend/C6 代码、旧 journal prefix、全图和上述真实 handoff 回执。

尚未确认新 admissions、真实子终态、剩余运行、容量或吞吐改善。原角色、模型、输入/native/color 数学、49 批图、科学门及原八臂均保持。
