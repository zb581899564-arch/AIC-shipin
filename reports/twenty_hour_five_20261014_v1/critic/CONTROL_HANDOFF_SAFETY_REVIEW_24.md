# CONTROL5 可逆 hold 与未来 remaining handoff 的安全条件

root 报告 23:42:33Z 已对唯一核实 argv/注册 SHA 的 owned 父 PID 1244689 发 SIGSTOP，并确认 State T；七个已启动直接孩子（一个 B000 wrapper、六个 SOURCE）继续自然完成，没有对子/外部任务发信号。当前只是可逆 hold，Goal active；不是 FAILED、自然 PASS 或新 controller 准入。

父 control 只有自身 Python 线程锁；SOURCE/GPU/QA 的 cache flock 在独立子进程，stdout 直接写文件，因此停父本身不应阻住孩子自然完成。还必须核父全部线程停稳、未持有共享 kernel lock，记录 PID starttime 防重用，并枚举完整 descendant，包含 GPU wrapper 的独立 session 模型子进程，不能只凭七个直接 PPID 数量判断全体结束。

Runner.start 在 Popen 前写 BEGIN；暂停可落在 BEGIN 尚未 spawn，或 spawn 后 handle 尚未登记。handoff receipt 应区分实际 begun child 和 BEGIN_WITHOUT_CHILD_OR_STAGE，后者不伪造 FAILED/COMPLETE。停住的父不会 wait/reap 或写孩子 COMPLETE：自然退出但尚未回收的子应在父死亡前保存真实 exit status 与相应最终 proof/resource/unique ledger，不能只有文件存在就补成功。

若扩展不准入，保持全部原文件及原执行状态，SIGCONT 同父可以沿原逻辑继续而不重复。若选择新 controller，则先让全部已开始孩子自然结束、解释所有失败/partial，冻结最终旧 journal prefix、真实子终态及已成功 stage refs，再单独授权停止父。不要 group signal，不裸 SIGCONT 让旧父在 handoff 中继续 spawn。若 SIGTERM 未实际结束 stopped 父，不把信号发送成功当作父已死；在 children 全终态且 root 明确授权后，只对核实仍停止中的 owned 父 SIGKILL 是确定阻止新节点的更窄替代，真实记录 signal 与 MAIN_CONTROLLED_HANDOFF_STOP，不改写旧状态为普通 FAIL/PASS。

新 controller 必须逐 stage 引用 SOURCE completion、GPU 自然 resource/unique ledger、首次 input QA、output QA、accept/release 的实际成功。GPU 同名已成功 job 不再次调用。已有 SOURCE/QA launch 而无完整成功不能 whole source 重启；任何实际 partial 都需要有界 remaining recovery。不得只重建一个空 journal 就忽略旧已完成操作。

per-visual-key writer 必须等旧 v2 writer 全退出才激活。旧 writer 只认 global flock，新 key lock 不能保护与它的竞争；不同 source_id 也可能拥有相同 source SHA/ordinals 的视觉 key。新永久 guard 不 unlink，稳定 inode、O_NOFOLLOW/链接逃逸门保留；同 key 核 identity、PTS/origin/grid/processor/dtype/完整视觉 signature，并做实际 exact bytes 相等去重，不仅 hash 比较。payload 完整无损 roundtrip 后才发布 index/manifest；旧 partial 文件不能覆盖或直接当成功。

hash-only 生命周期可以消除首次 QA 后的重复 Torch 重建，但 canonical manifest/private/visual 的实际 bytes/SHA 存在、完整 signature 与首次 input/GPU/output proof、自然 ledger、retained refs、仍在 RGB SHA/inode、全冻结 consumer 和 append-only intent/release 门全部要保留。新 helper 的真实 code/admission/provenance 必须进入新注册、产物与最终 closure；不能用旧 input5/cache2 SHA 冒称新 storage backend。预处理算法未变允许仍引用原预处理代码，实际序列化 writer 则另行披露。

本报告只审边界。新 helper 代码尚待其作者最终交付与独立静态审查；没有发送信号、启动 controller、读正式 raw、媒体/tensor/权重体或重跑已有 proof/probe/model。
