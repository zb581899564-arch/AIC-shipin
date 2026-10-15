# Cache v2：持久Linux进程互斥

v2是v1运行模块的独立副本。canonical schema仍 `PRODUCTION_EXACT_STREAM_CACHE_V1`，完整tensor dtype/shape/stride/原bytes、uint8 bit LUT/gzip、私有text/tokenmask、visual实际bytes+identity去重、RGB租约、首次独立proof、自然GPU terminal和append-only release要求均不变。`leases.py` 和 `pixel_dictionary.py` 与v1字节相同；没有新producer/模型/媒体操作或旧删除。

新root policy必须声明 `process_lock_backend: "LINUX_PERSISTENT_FLOCK_V2"`。其余policy/API同v1，root仍严格限定CAMPAIGN直属 `production_stream_vN`；原root自动resume禁止。控制器和所有worker必须加载同一份v2 code/SHA，不可v1/v2混写同root，不把旧v1 policy补改为v2。需要新生产注册后才使用。

`Store.locked()` 对 `permanent/journal_write.lock` 固定持久regular inode使用 `fcntl.flock(LOCK_EX)`，不同process排队等待。所有目录分量通过dir-fd与O_NOFOLLOW打开，guard也O_NOFOLLOW并检查regular、nlink=1和等inode，阻止symlink/hardlink/等待时inode替换。释放只LOCK_UN+close；库永不unlink或rename guard，不修改PID内容。异常离开context仍释放；进程终止由内核关fd释放。guard文件永久保留不是残留失败，不应由任何cleanup删除。

公共 `Store/LeaseStore.create`, `save_input`, `load_input`, `register_rgb`, `accept_consumer`, `release_rgb` 调用签名不变。lock非reentrant：不要在外部with locked中再调用已有内部锁的save/lease mutation。CPU decode/processor及各consumer独立replay可在事务外并行；canonical commit和lease/lifecycle mutation序列化。所有worker应在未持有guard时启动，不在持锁段fork继承文件描述符。新consumer的读/消费仍需其实际prepare成功和批完整准入，不能因进程锁跳过阶段依赖。

自然GPU terminal、首次独立input/output接受、全冻结consumer graph、canonical文件实存SHA和历史RGBleaseSHA接受后才release新临时RGB，门和永久保存均不变。容量不够仍STOP retain，不量化/删canonical。guard互斥不会证明任意source pool并行容量足够，pool/batch按主控实时CPU/内存/disk和实测峰值决定，membership事前冻结，不按输出换单位。

唯一新合成检查限定Linux `CAMPAIGN/cache_codec_12/synthetic_01`：两个worker并发互斥、异常退出context后另一worker接受、persistent guard inode保持、symlink/hardlink guard拒绝。它不执行旧codec全检查，不用Torch/媒体/processor/model或任何生产/旧cache，也不释放RGB。v1及旧全部成功检查保留。
