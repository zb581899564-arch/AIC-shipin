# 生产 RGB 内存与首次独立输入 QA：工程草案

日期：2026-10-15（Asia/Taipei）。状态：**仅方案和纯数据模块，未获生产准入**。

主代理后续查到旧成功生产流已具备 `improvement/production_stream_cache_v2/pixel_dictionary.py` 的 `PIXEL_UINT8_BIT_LUT_V1`：对实际 float32 像素张量的每个原始 uint32 位模式建立最多256项的精确表和索引，加载恢复原float32 bits，并逐张量核 dtype/shape/stride/offset/alias/signature，超出条件保留原始序列化。它是存储编码，不是模型量化。新生产实现优先评估复用这些已存在的纯函数与 `codec.signature/exact_equal`，不重启旧生产 Store 或改其限定根/冻结policy；仍须对每个真正新主cache执行实际bit-roundtrip、记录原始/索引字节与fallback。不能据旧成功就承诺新数据全部满足256模式或一定装下。新 `array_bit_codec.py` 暂是纯合成验证过的备用工程模块，未选为实际生产格式，不为凑完整性再对旧tensor做codec试验。

## 结论与协议边界

可以把新生产的单个物理源 wanted-RGB 并集放在 RAM，逐个构造只读 native64 输入，永久只保留主 tensor lossless cache、原媒体/完整 clock 引用、ordinal/PTS/每帧像素 SHA、两次真实 processor 的独立 evidence，以及全部原始模型输出和 QA。新流程不生成 PNG 或 frames.npz，因而没有任何删除旧成功文件的动作。

此变化只涉及新生产的储存方式及首次输入 QA 时点。完整原源零点的 15 秒/7.5 秒步长、精确右尾去重、原始 64 不同帧与 `first+j*(limit-first-1)//63`、原尺寸 RGB、原显式 `video_size`/实际 video grid 与 processor 身份、input<=16384/out<=256、原 B/TIME、KEEP-only 且不 padding、VERIFY40.46 baseline 帧/双比例原框不变，均须继续使用已冻结科学规则。它不增加实验参数或按测试内容选窗。loader 的 `min_pixels=max_pixels=131072` 构造参数不等于实际视频像素上限。

**不能直接称为沿用旧执行协议。** 现有 dev/confirm/facts 程序的首次 vision-processor replay 在 GPU 后并依赖持久 frames.npz。新生产必须另行冻结“首次独立真实输入 replay 提前到 GPU 前、GPU 后只做 token/grammar/parser/native/output QA”的明确契约和全部实现；不能给旧脚本传一个已完成布尔值跳过 QA。原 dev/confirm/facts 的协议、费用、成功、失败与文件不改。

## 有界空间判断

依据 `production_metadata_budget_10.json` 的 metadata-only 快照、`cpu_storage_observation_14.json` 的 stat-only 快照及主代理补充的 `actual_video_grid_observation_18.json` 已接受 proof 字段回执；本次没有刷新远端资源，也没有打开旧 tensor 或媒体。

| 项目 | 实际记录/纯算术 | 对方案的含义 |
| --- | ---: | --- |
| 记录源/物理 SHA 源 | 426 / 425 | 原 426 分母仍保留 |
| 记录 overlap 窗/物理几何窗 | 968 / 967 | 1 个 alias 尚未证明 tensor/prompt/model 同一，不能据此跳过调用或 QA |
| 全源 wanted-RGB 并集原始字节 | 205,832,573,568 | 不可把所有源同时常驻 RAM，也不将其写成永久 PNG |
| 单源最大 wanted-RGB 并集 | 15,010,790,400 | 只逐源持有一个并集 |
| 逐窗重复 native64 RGB 原始字节 | 211,836,672,000 | 新流程不生成这类持久 NPZ 副本；原 PNG/NPZ 实际压缩大小不由此推断 |
| 最大原尺寸 native64 RGB | 398,131,200 | 1920×1080×3×64；输入仍原尺寸 |
| 最大单源并集+3 份 view+1 解码帧 | 16,211,404,800 | 仅 RGB 算术示例，未包含 processor、IPC、Python/allocator 与系统开销 |
| 磁盘可用快照 | 73,341,693,952 | 历史快照，不能作为后续运行保证 |
| dev 已成功主 cache | 26 份 / 879,620,391；最大 51,471,124 | 只使用 stat 回执，未加载或重编码 |
| confirm 已成功主 cache | 29 份 / 1,431,247,990；最大 79,544,904 | 最大值乘 967 为 76,919,922,168，比磁盘快照多 3,578,228,216，且尚未计其他新产物 |

主代理报告 RAM available 约 120 GB；这不是本模块取得的新资源回执。逐源 RAM 的 RGB 量级较小，但**必须实核同一时点的共享资源、实际 processor/QA/IPC 峰值和外部任务后动态决定**，不设置固定 GiB、百分比或核数准入线。

停止 RGB 落盘可以消除大块中间文件，仍然不能证明永久 tensor cache 必定装下。此前以每帧 131072 像素、64 帧、3 通道 float32 计算单窗 100,663,296 字节、967 窗 97,341,407,232 字节，**只是错误视频像素上限假设下的算术，不是实际 tensor 大小或合法容量上界，不得用作准入**。

实际已接受 confirm 样本 `v_EMDTvPUEr7E.baseline0000` 的原 proof 记录 `video_grid_thw=[32,28,52]`、实际每帧 372736 像素、12085 input tokens、`pixel_values_videos=[46592,1536] float32`，仅这个 tensor 原始位数据就是 **286,261,248 字节**。同一数值乘 967 为 276,814,626,816 字节；这也只是单个真实样本的外推，**不是全量上界或压缩后磁盘大小**。原显式 `video_size`、实际 grid/token/tensor shape、主 lossless cache 字节数必须分别绑定核查，不改原配置来省空间。dev/confirm 平均 cache 大小及已见最大值均不能作为全量上界。当前磁盘快照对 967 份 cache 的平均空间只有约 75,844,564 字节/份，且未扣除其他必要产物与外部写入。

新生产准备必须在各主 cache 成功写入后记录其实际字节数、SHA 和 bit-roundtrip，更新剩余来源/视图、当前 free disk 与其他持久输出预算。VERIFY 只复用已接受的视觉 tensor，不为每个语义请求复制整份视觉 cache。空间不足就保留现有成功/partial 并停止，不能删除旧材料、改用有损 dtype，或承诺平均值一定够用；GPU 前必须全量缓存和 QA 完整验收。

主代理提出的“按 tensor 原始 uint8 位序确定性 byte-shuffle 再 zlib”可作为后续独立 codec 草案；此任务未实现或测试它。若选用，须先冻结字节排列、dtype/shape/stride/offset 等元数据及 serializer，证明主 cache 的每个原始 bit 往返相同，再实测新 cache 大小；不能假设一定比 gzip 小。不得为此加载或重编码旧成功 tensor。

## 新首次 QA 的最低完整流程

1. 首模型结果前冻结生产 manifest、source/model/prompt/runtime/processor/token/grammar/code 锁、实际 source aliases、CPU/GPU 预算和新 QA 时点。模型允许调用数须来自实际输入 identity 审计，不把物理几何去重当模型 identity。
2. 逐个物理源：核原媒体 SHA、已有完整 clock SHA/原点/物理终点；一遍新像素解码只为预登记 wanted ordinals 转 RGB。每帧立即核 ordinal、精确 PTS、原尺寸 uint8，并保存可持久化的像素 SHA manifest。模块不测 clock、不选候选窗、不执行 decoder。
3. 每个唯一视图仅构造一个只读 native64 buffer。主 CPU processor 按原 runtime 调用一次；返回立刻持久保存主 encode evidence，再作 Mapping-safe tensor/cache/实际 tokens/bit-roundtrip，保存唯一主 lossless cache。
4. 把同一视图的精确 header 和 RGB 经**有界、显式、只读的内存/IPC 接口**交给另一个 CPU 进程。独立实现从完整 clock 重算 64 ordinal/PTS，核收到的每帧 pixel SHA；加载原冻结 processor，完成该视图真正第一次独立 `encode`，返回后立即保存第二份真实 encode evidence。加载主 cache，逐 tensor 比 dtype、shape、stride/offset、原始 bit、prompt/processor/model 身份和 tokens，完成独立 serializer roundtrip。QA tensor 可在比较并持久化证明后释放，无需保存第二份永久视觉 cache。
5. 保存双方 evidence 与实际 cache/clock/RGB manifest/代码锁的不可变绑定，明确 `FIRST_INDEPENDENT_INPUT_REPLAY_PRE_GPU`、真实次数各 1、成功时点和 post-GPU 不再重复 vision encode。独立 CPU 全量 admit 只读核所有缓存、证明和锁。完成一个源的全部 primary 与首次 QA 并落盘后，释放该源 RAM。
6. 全部实际输入完整接受才准入唯一共享 GPU 作业。GPU 后仍对全部真实 raw/token IDs/grammar/parser/native/语义 KEEP 决定做首次相应 QA；验证并消费真实 pre-GPU input replay 的证明，不能用它代替模型输出 QA。工程失败不得变 UNKNOWN、EMPTY 或跳过。

独立 QA 必须是实际另一进程/实现调用，不是把主 tensor 的 hash 再算一遍。当前模块不实现 IPC/processor/证据写入或准入。可采用有界 pipe/socket 传一份 view；不能假定 `/dev/shm` 大小足够，不能在初始化含线程的 processor 后随意 fork。IPC 复制数、子进程存活的输入与两份 tensor 峰值仍待生产实现明确与实测。

## 纯模块接口与实际检查

新增 `improvement/recall_production_v1/rgb_memory.py`，无文件 I/O、decoder、NumPy、torch、processor 或 model import。

- `SourceIdentity(source_sha256, clock_sha256, width, height, total_frames)`：冻结物理 source/clock/原几何身份。
- `payload_requirements(...)`：计算精确 RGB payload 字节；明确不含 processor/IPC/Python/RSS 成本，不返回准入。
- `MemoryRGBUnion(identity, full_source_exact_pts, physical_end_exact, wanted_ordinals, max_union_rgb_bytes=...)`：拒绝 float PTS、错 clock 分母、重复/越域 ordinal、超显式 payload allowance。仅接受调用方主动提供的 RGB buffer。
- `add_frame(...)` / `seal()` / `manifest()`：原尺寸 C-contiguous uint8，核源/PTS/可选已知 pixel SHA，内部存不可变 bytes，不 alias 解码 buffer；缺帧、重复成功或封存后写入均拒绝。manifest 不携带像素，也不声称 processor QA 已完成。
- `with union.view64(..., max_view_rgb_bytes=...) as view`：核精确原生 floor64，返回只读 `(64,H,W,3)` uint8 memoryview，一次仅允许一个活跃 lease。可在 lease 内用未来调用方的 NumPy `frombuffer` 构造只读视图。必须在退出前释放所有派生 RGB consumer，禁止把 RGB view 留到 lease 外。退出使本 memoryview 失效；`close()` 仅释放 RAM，未触碰任何磁盘文件。

本次实际通过 AST 和合成 uint8 buffer 检查：输入 buffer 后续改动不影响已封存像素；floor64 首末为 0/127；只读写入拒绝；union 与 view 精确字节边界；不同源、错 PTS/dtype/shape/hash、重复/漏帧/越域、float clock、错误 sampling、少于64帧、活跃 lease 重入、活跃时 close、退出后主 view 失效、closed union 隐式恢复等共 26 个拒绝行为。真实 decoder/processor/model 调用为 0。

## 失效恢复限制

RAM 不具备崩溃恢复性。若某源全部 primary+首次独立 QA/cache/proof 已持久成功，后续 GPU 阶段不再需要其 RGB；成功 encode/QA 不重做。

若进程/OOM/主机故障发生于一个源尚未完成时，原媒体/clock 和已经成功的主 cache/evidence/QA/raw 保持，但 RAM 中尚未完成视图的像素会丢失。像素 SHA 不能恢复像素；从原媒体再解码属于一次额外 decoder 成本，**不能称为零重复恢复或默认为已授权**。旧“成功阶段不重跑”的限制下，此失败必须停止并另行登记显式恢复，列清哪些 primary/QA 已成功不可重复、哪些从未成功，以及新增解码为何必要。若不能接受此故障边界，就需要另行获得足够持久 RGB/临时 source spool 空间；本模块没有偷偷加入磁盘回落、清理或重试。

若实际主 encode 已返回但 evidence/cache 尚未 fsync 完成就崩溃，也不能补造历史 receipt；须保留真实费用与 partial，独立判断可证成功和缺口。主/QA receipt、主 cache、全源 manifest 的提交顺序和异常保存仍须由后续生产 controller 实现并冻结。

到此为工程草案。事实门结果、生产总源码、实际资源/全量缓存容量、新独立 QA 证明和最终生产准入均由主流程后续验收；本次没有改 frozen 4+4/facts 的任何代码或协议，没有启动生产、封包或声明质量通过。
