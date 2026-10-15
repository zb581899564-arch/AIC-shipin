# Native terminal compressed-packet witness v1

只用于首次 fixed426 Linux CPU technical measurement，不读预测/标签/GT，不 frame decode、RGB、processor 或 GPU，不改旧 clock。原 rematch plan/clock registry/full integer framePTS/source bytes/SHA 冻结；每源唯一一次全媒体 SHA pass 和一次 `av.open(file).demux(unique_video_stream)`，源码检查没有 `.decode()`。

必须恰好一个 packet 的 exact pts*timebase 等于旧最后 FRAME rawPTS，且它等于该video全部display packetPTS最大值；payload size 与 actual positive duration 必须真实可用。physical end=(oldlastPTS-oldorigin)+packetduration。无匹配/重复/零duration/最大PTS不符明确FAIL，无N/fps、容器duration、猜测或epsilon fallback。10旧明确packet-end ticks须实测相等；416旧CFR N/fps只是原planning，不能要求physical=endnominal。原source bytes/SHA/path/stat或geometry改变立即全STOP，不按格式失败抹其他coverage。

新 Linux root `CAMPAIGN/native_terminal_packet_witness_v1`，pure→freeze→run 各只一次；纯检查无PyAV/Torch/媒体。first426 serial，保护共享任务，不固定CPU/GPU/RAM容量阈值。压缩packetSHA仅last匹配payload，不保媒体或图像。426源总4,781,857,740B，SHA＋demux两pass的逻辑媒体预算9,563,715,480B全部Linux内部、网络新增0。

新witness只证明原last FRAME PTS所对应的compressed packet terminal，不冒称已测新fullframePTS、frame.duration或新模型输入。后续首次RGB实际decode必须独立核全PTS/origin/尺寸/帧数及实际positive last frame.duration与该witness一致。原01/02失败与所有oldclock/model/package不重跑。成功source/packet测量不可再次运行；后续若确需恢复，仅另显式范围读取未成功source，保留本root全部成功/失败。正式模型准入仍由主控决定。
