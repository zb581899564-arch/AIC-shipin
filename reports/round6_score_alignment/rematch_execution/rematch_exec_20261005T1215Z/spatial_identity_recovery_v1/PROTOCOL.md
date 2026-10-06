# A 空间帧身份恢复 V1

原空间运行在2026-10-06 04:02因8个已登记帧像素身份失败停止，13,014个MODEL_OK与原失败证据保持只读；8个失败均在模型调用前，原始模型输出为空。用户已要求解决并继续推理、打包、开训，主控只修对应解码身份：从源ordinal0顺序解码，仍要求同一expected_pixel_sha256、源SHA、source_frame、尺寸、时钟与请求绑定。真实CPU恢复8/8一致；lossless17帧fixture检查五次采样，逆向请求与错像素SHA均拒绝。未查看测试画面、模型原文或标签。

只执行8次原未微调4B/adapter-off空间调用，模型、提示词、解析器、crop规则、选帧、镜头与插值保持。成功13014条保留原行字节，原13022失败运行仍失败。新run复制并逐文件SHA核原temporal/selected/shots/requests/metadata；恢复完整13022锚点后，复用冻结compose/package及独立strict loader，426视频/93155帧/0fallback、ZIP仅predictions.jsonl、CRC和SHA必须通过。任一失败STOP，不裁段/删帧/空值/中心框填补，不重跑原成功模型。

单作业经既有gpu_run.py共享锁与追加账本，实际资源/80GiB容量门继续，计划产物406549675字节、上限900秒含合成/封包；不抢占外部任务、不安装、不上传。源码与CPU证据绑定新source_lock.json。A严格包通过后主控恢复已经登记的8B区间SFT五次真实更新，其原C/BCE STOP和完整训练/弱开发验收边界保持。
