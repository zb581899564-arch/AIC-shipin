# 双视角补召回：全量缓存边界审核 15

日期：2026-10-15。状态：只读工程审核，**不是生产准入、真实输入 QA 或容量实测通过**。本次只读本地模块/旧 CPU profile/历史预算并计算字节公式；未 SSH、下载、解码、运行 processor/model/QA、重做全量计划或计算源码 SHA。未读取测试 GT、图片或逐条预测内容，未构造旧 `Store`，未清理任何文件。

当前双视角开发 8 源已通过；fresh 4 的 VERIFY 尚在运行，质量结论未齐，后续事实门与生产登记仍须自然通过。保护 VERIFY40.46 原 ZIP（SHA `86593725c6bad919dc0d342fe98ad65e489a13a6e492da5de3afd247a3226543`）、原 122002 帧及双比例框/参数原字节；新方案仍是原 8,782,459,120 参数、native64、原 RGB/PTS/窗口与 prompt/grammar，不更改科学输入。

## 1. 可行结论及不可直接沿用的部分

新独立生产实现可以按“单源 wanted RGB union 只解码一次并留 RAM → 每唯一实际视图一次 primary processor → 位无损缓存 → 独立进程对同原 RGB 做首次真实 processor QA → 源内全通过才释放 RAM”执行。这样无需生成新 PNG/NPZ，也无需删除或重编码任何旧成功材料。全部源的该阶段缓存与独立输入验收齐全后才启动该阶段共享 GPU。

这在输入值与独立验证上可保持原科学契约，但**现有冻结实现尚不支持此证据生命周期**：旧首 QA 同时验证 RGB/processor 和 GPU 后 token/grammar/parser/native；新实现必须明确拆成 GPU 前真实 input QA 与 GPU 后输出 QA，两者共同闭环。不能把 `first_replay=True` 提前写入，不能以 cache roundtrip 代替真实 processor QA，也不能在 GPU 后再重复已成功的 input processor QA。

按原协议因果顺序分阶段冻结：全 B0 实际输入与首次视觉 input QA 通过后才 B0 GPU；B0 自然终态后冻结完整 VERIFY 请求，全部 token/完整 input 验收后才 VERIFY GPU。不能要求预先知道 B0 候选，也不能声称 GPU 前已验收尚不存在的 VERIFY 请求。同一已证明视觉 identity 的首次独立 processor QA 只在原 RGB union 仍在 RAM 时执行一次；后续请求引用这份实际逐 bit 回执，按原 prompt 构造并验收各自 token/private input，不重复成功视觉 encode。合法 GPU 后输出 QA 只首次核当前 raw/token/grammar/parser/native 与 cache 加载身份。共享视觉缓存只减少已证明完全相同的视觉张量存储；不同请求的原 prompt/token/mask 与完整输入证据仍独立保留。

## 2. 已读代码中可复用的准确切片

| 文件 / 接口 | 可复用范围 | 限制 |
| --- | --- | --- |
| `improvement/recall_production_v1/rgb_memory.py`: `SourceIdentity`, `payload_requirements`, `MemoryRGBUnion.add_frame/seal/manifest/view64/close` | 原 source/clock/尺寸、wanted ordinal、逐帧像素 SHA、严格 floor64、只读单视图 lease 与 RAM 生命周期 | 不解码、不运行或认证 QA；`manifest()` 明确未完成 QA。`view64()` 会另分配一个拼接的 native64 RGB；只读 memoryview 不等于跨进程零拷贝；调用者须销毁逃逸的派生 buffer，否则 `close()` 不保证实际 RSS 已释放。 |
| `improvement/production_stream_cache_v2/pixel_dictionary.py`: `pack/unpack/validate_roundtrip` | 对新实际张量作 uint32 位模式 LUT 编码、位完全相等读回；可复用算法与拒绝/回退条件 | 只处理键 `pixel_values_videos` 的 CPU float32、非空 2D、三等分列块、C stride/offset0、无 requires_grad/跨键 alias 的情形；每块实际位模式须 ≤256。其余保留原 torch 张量，不能量化、截 LUT、改布局。 |
| 同目录 `codec.py`: `signature/exact_equal` | 纯内存检查原 CPU 张量的可见原始 bytes、dtype/shape/stride/offset/alias groups，包括 NaN payload 与 -0 | 入口要求非空 dict；应仅将已验证的 `Mapping` 容器转成 `dict(encoded)`，不转 dtype/设备/布局。`signature()` 会产生逻辑原字节副本，必须计峰内存。 |
| `improvement/recall_production_v1/array_bit_codec.py`: `encode_array/inspect_cache/decode_array` | NumPy 非空、明确 offset0 的原 C 数组；plain zlib 与按 itemsize byte-plane shuffle 后 zlib 在 RAM 比较，只写更短者；header/payload/raw SHA 全核 | 不是现有 torch 字典缓存的 drop-in adapter；torch-backed NumPy 的 owner 可能被拒绝。不得用隐式 copy/contiguous 修复不支持布局。跨键 alias 及完整输入字典须由新 adapter 处理。无已知真实压缩率保证。 |
| `improvement/charades_native_v2/charades_cpu.py`: `_checked_cpu_proofs`, `_reuse_cpu_completion`, `_load_cpu_runtime`, `_check_capacity` | 继承完整时钟、只读成功 proof/cache 身份与原 runtime 路径核对的思路；whole-video budget 公式正确 | profile 的特定 root/来源/旧格式和固定 serial CPU 设置不能作为本轮通用资源策略；旧 QA/路径契约不可改写。 |
| `improvement/temporal_production_inputs_v5/prepare_source.py`: `capacity`, `decode_once`, `validate_full_identity_before_terminal` | source wanted union、完整原时钟/几何逐项核对、实际 tensor 字节再验容量的结构 | `save_frozen_rgb_checkpoint` 会写逐组 NPZ；当前 RAM 方案不能调用它。原完整 clock 直接引用，不重新执行旧成功测量。新像素解码途中的 PTS 比对是该次读取身份校验，不是重写原 clock。 |

`codec.Store` 构造函数绑定旧 campaign 路径并读取/核验旧 policy；`create/save_input/_save_tensors` 与 `LeaseStore` 会写缓存、锁、lease 或 journal，均不属于可直接调用的纯模块。旧 `LeaseStore.accept_consumer/release_rgb` 强制 GPU completed/exit0、唯一 ledger、仍存在的 RGB 文件及 GPU 后全首 QA；不能用于本次 GPU 前 RAM 释放，也不能在旧根上实例化以“复用压缩”。新 adapter/receipt 必须属于新的独立生产目录。

## 3. 永久磁盘：字典压缩是实际条件，不是四倍保证

历史 `production_metadata_budget_10.json`（2026-10-14 16:24Z）只有元数据预算：426 records、425 physical sources、968 record views、967 physical views、1 个尚未证明 tensor/prompt/model 同一性的 metadata alias；全部 RGB union 为 205,832,573,568 B，最大单源 union 为 15,010,790,400 B。它不是本轮冻结生产清单，967 不能直接作为新模型或 QA 分母。以下乘法仅说明该历史规模的风险，没有重新规划或裁减视图。

原 Qwen3VL `video_processor.size.longest_edge=25,165,824` 约束整个 64 帧 video 的 `t_bar*h_bar*w_bar`，不是单帧上限；不得再次乘 64。原 `min_pixels=max_pixels=131072` loader 参数也不能当作实际 video cap。给定原 `smart_resize(64,H,W,temporal_factor=2,factor=32,min_pixels=4096,max_pixels=25165824)` 的结果 `(h,w)`：

```text
D = 3*H*W                         # 原尺寸单帧 uint8 RGB
R = 64*D                          # 一个原 native64 RGB
U = wanted_unique_ordinals*D      # 单源 union
P = 64*h*w*3*4                    # 实际 float32 pixel tensor bytes
  = product(video_grid_thw)*1536*4
P <= 25,165,824*3*4 = 301,989,888 B
T_ids_mask <= 16384*2*8 = 262,144 B; video_grid_thw int64[3] = 24 B
```

这里 262,168 B 只覆盖这两项 int64 token 数组和 grid；实际返回若有其他键、共享 storage、位置/时间字段，须另计，不能丢弃。已有实际输入样本 `grid=[32,28,52]`、pixel tensor `[46592,1536]` float32 为 286,261,248 B、12085 tokens；约 250MB 只是量级说明，不能当上界。

字典算法在三块都合格时，N=P/4 个 float32 元素编码为 N 个 uint8 索引，加最多 `3*256*4=3072 B` LUT；这只是未封装的字典内容字节。原 uint32 位模式直接查表还原，-0 与不同 NaN 位模式不合并。不能从原输入为 RGB uint8 推定 resize/normalize 后各块必然 ≤256 位模式；当前未读真实张量检查这一条件。

| 仅作历史规模算术 | 字节数 | 解释 |
| --- | ---: | --- |
| 967 × 250,000,000 | 241,750,000,000 | 约 250MB/窗的 pixel 原量级示例，非上界 |
| 967 × 286,261,248 | 276,814,626,816 | 上述单个已知样本乘历史窗数，非总体估计/上界 |
| 967 × 301,989,888 | 292,024,221,696 | whole-video 预算导出的 pixel 原字节上界示意 |
| 967 × (301,989,888/4 + 3072 + 262168) | 73,262,542,504 | **全合格字典**时索引+LUT+两 token/grid 的未封装预算，不是总缓存上界 |
| 清理后可用磁盘快照 | 80,116,281,344 | 已有观察，非本次实时核验，也非可独占额度 |
| 快照减上一行字典预算 | 6,853,738,840 | 尚未扣封装/证据/其他实际输入/VERIFY 私有输入/失败与暂存 |

旧 v2 字典最终仍用 `torch.save + gzip(level=1)`：需计 pickle/zip storage 元数据、gzip 膨胀和私有输入文件，不可把 indexed bytes 当实际文件上界；字典不合格时原 torch/gzip 回退大小也未知。`array_bit_codec` 的两种 zlib 候选只决定相对更短，并不保证小于 raw，更不保证能放入 80.1GB。它的通用 fallback 可以保持 bits，却没有解决最坏磁盘不足。

新缓存必须只永久保留一种选定 representation 与全输入 manifest，禁止同时永久保留原 float cache、字典 cache、NPZ、PNG 四套。原媒体、完整 clock、ordinal/PTS/像素 SHA、主 lossless tensor、两次真实 evidence、输入 QA/serializer proof、全部 request/raw/tokens/done/费用/失败/源码锁仍保留。既有旧成功 cache 只引用，不重新转码后删除。视觉共享可避免同一已证明视觉输入在 B0/VERIFY 中重复存 P，但每种原 prompt 的私有完整 token 输入与证据不能省略；尚未形成的 VERIFY 数量与字节也不能计为零。

容量判定应比较当前实际 free 与本次写入前的完整保守上界，并考虑当前资源冲突；逐源写入后记实际文件字节、codec 条件与实际 RSS，再核剩余尚未处理输入的**允许回退上界**。若剩余最坏回退放不下，应在解码/primary 前等待或 STOP 并保留材料；不能到中途靠量化、删永久物或改变成员凑通过。要以实测压缩支持全量，须有冻结且可完成剩余输入的容量策略；只看到前几个 cache 较小不足以保证余量。

## 4. 峰内存：精确 payload 与未知运行时峰分开

只准单源 union、单 active view、串行 primary/codec/独立 QA，禁止后台积压多个 view 或复制全 source union 给 QA 进程。原帧 `MemoryRGBUnion.add_frame` 复制 immutable bytes，`view64` 的 `b''.join` 另分配 R；需销毁派生 NumPy/memoryview 才能释放。跨进程可以只传一个有显式大小的 view，由独立进程核逐帧 SHA 后调用原 processor；IPC 不能默认零拷贝或无限队列。

历史最大 native 几何 1920×1080（横竖同字节）：D=6,220,800 B、R=398,131,200 B。将最大 U 与最大 R 保守组合：

```text
U_max + 3*R_max + D_max = 16,211,404,800 B
```

这是 union + 最多三份 view payload + 一个 decoder RGB 帧的精确 payload 预算，不是 RSS 上界；实际 IPC 若出现更多副本须改 c 的实数。当前约 126GB available 的观察显示 RGB 量级有空间，但不构成实时资源承诺。完整峰值应按阶段取 max：

```text
M_peak = U + c*R + decoder_buffers + clock/Python_metadata
         + processor_resident/working_memory
         + max(primary_codec_phase, independent_input_QA_phase)
```

其中各阶段至少计：

- 主 tensor 与私有字段 F=P+T；写前立即 durable 保存原 `encode_evidence.json`。codec 操作只消费已有主 tensor，不再调用 processor。落盘并独立读回后释放主 tensor 和所有 codec 临时对象，再进入 QA，避免无理由同时保留三份主 tensor。
- `pixel_dictionary.pack`：原 P；`np.unique` 对一块 `P/3` 的非连续列切片产生展平/排序/去重工作区，实际 unique 可非常大，发现 >256 时才回退；不能按 256 项预分配峰值。`searchsorted` 的临时 intp 索引在 64 位环境单块为 `2P/3`，转 uint8 单块另 `P/12`，三块已完成索引累计至 P/4；`LUT[indices]` 校验另有单块 P/3 临时。排序及 NumPy 内部工作区需要纳入实测，不能只算 P/4。
- `unpack`：索引 payload 约 P/4+LUT、还原 float32 backing P、一次查表临时 P/3。`signature()` 对 C 张量 `.tobytes()` 再产生 P；不支持布局的 fallback 还可能因 `.contiguous()` 增加副本。`validate_roundtrip` 与写后读回可多次恢复 bits，但不产生第二次 primary processor 调用。
- 首次独立 input QA：独立原 processor 产生 Q≈F；从已提交 cache 取回的主输入 F；逐 bit 比较/签名时的原字节临时约 P，另有真实 processor 工作区和 cache 解码临时。宜先读回释放 codec 工作区再 QA，不同时压缩下一 view。`U+cR+2F+P` 只是这部分可见 payload，未含 processor 峰。
- `array_bit_codec.encode_array`：调用者原 P + raw P + planes P + plain 压缩 C0 + shuffle 压缩 C1；返回拼接 cache 又分配 header+选中 Cs（表达式中间拼接也须计）；zlib 工作区另计。加载 shuffle 表示时 cache Cs + inflated P + unshuffle raw P；不能用“只落一种 payload”误推 RAM 只持有一种。

因此可精确计算 geometry/R/U/F 和上述显式缓冲字节，**当前证据不能给出精确整体 RSS 峰或保证全量可运行**。新实现只在本来必须发生的首次 primary/首次 QA 中记录各阶段实际高水位，并结合当前外部作业动态准入，不为测峰额外编码旧成功输入；不得预设固定 GiB、利用率、核号或 worker 数。

## 5. RGB 何时可以释放，何时不能

源内每个未采用旧成功 identity 的实际 view 都必须完成以下真实闭环：

1. 原媒体/全 clock 身份冻结，wanted ordinal 实际解码像素与完整 PTS/尺寸核对；一个只读 native64 RGB 同时有逐帧 SHA、精确采样、窗口/原点/全源绑定，无 padding/shift/resize 输入修复。
2. 原 processor **一次 primary encode**，返回即保存实际 evidence；完整 Mapping 的每个 tensor 以原 bits/布局保存，文件独占创建、flush/fsync，读回 exact_equal，落完整 cache/signature/raw hash。工程异常是真 failure，不能转 UNKNOWN 或换成员。
3. 另一个 CPU 进程从同一 source/view 原 RGB 核 SHA、原 clock/floor64 和 processor/model/prompt/grammar 身份，独立原 processor **一次 input QA encode**；与已留主 cache 逐 tensor raw bytes/dtype/shape/stride/offset/alias 及 tokens/grid 完全一致，保存自己的实际 evidence、PID/实现与主 evidence 的绑定。两次 encode 分别是必要 primary 与首次独立 QA，不是两个 primary，也不存在第三次“压缩时重编码”。
4. 源内所有 view 的主 cache、两份真实 evidence、serializer proof、独立 input-QA receipt、完整 source/clock/pixel manifest 均 durable commit 并独立读回；无 pending view、未闭合 IPC/派生 RGB consumer，才可释放该源 RAM。不同源逐一完成，不让 205.8GB union 同时驻留。

RAM 释放后，GPU 只加载已验收主 cache；实际 GPU load signature 与锁中的同一完整输入相等，request/done/raw/token/ledger 绑定这份 cache。GPU 后仍做 output token/decode/grammar/parser/native 与真实 semantic 复核；它消费已成功 input-QA proof，不重做 vision processor。GPU 前 receipt 不得伪造 GPU_input_signature、模型实际调用或输出 QA。

在上述**新生命周期先冻结并实际通过**的前提下，原 RGB 不必作为额外永久 PNG/NPZ 留存：原媒体+原解码/颜色转换实现身份+完整 clock/ordinals/pixel hashes 保留来源与重建信息，主 lossless tensor 保留实际模型输入，两份 evidence 与真实输入 QA 保留独立验证事实。只保存像素 hashes 而没有实际独立 processor QA 不成立；仅 serializer roundtrip 也不成立。若未来要独立重新从媒体审计像素，那是另一个明确授权读取，不应伪称本轮已做。

失效边界：释放 RAM 前进程崩溃会丢失尚未持久保存的 RGB，pixel SHA 无法重建 pixels；一次 decode 的无失败执行契约不能承诺 crash 后仍零重复 decode。失败保留所有已有 cache/evidence/receipt，显式新恢复只补尚未成功 primary/QA；若必须再次解码以取得遗失 RGB，应登记这笔实际费用与原因、复核新 RGB SHA，不能自动隐式 resume 或把成功 encode/QA 重做。要保证中途崩溃也绝不重复 decode，就需要另立 durable RGB spool/可恢复内存机制与容量，这超出当前 RAM-only 方案，不能暗中声称已解决。

## 6. 旧输入采用与 no_delta 的证明边界

旧成功调用/准备/首 QA 只能只读采用，不能凭同 source 名或窗口几何避免身份核对，更不能为新压缩再运行旧 processor。采用 receipt 至少绑定：

- 原 source bytes/SHA、完整 clock/原点/物理末端、窗口精确端点及半开 native 范围、64 ordinals/PTS/逐帧像素 SHA/尺寸、原颜色转换和 processor 全 assets/安装实现/video_size/实际 grid。
- 原完整 prompt 字节、tokenizer/special/EOS/grammar/parser 实现身份、input_ids/mask 与所有实际张量 keys、dtype/shape/stride/offset/可见 bits/alias signature；原 model base/TIME adapter/config、启用层和真实 8,782,459,120 参数身份。
- 同一 cache/输入的实际 primary evidence、真正首次独立 input QA（不是摘要 bool）、原实际模型 request/raw/tokens/done 与唯一自然终态/ledger、GPU 实际加载输入身份。只继承 CPU cache 时只能声称相应 CPU 身份通过，不能顺便声称旧模型回答或 QA 可用于新请求。

历史的一个 physical metadata alias 尚未证明以上 tensor/prompt/model 同一性；不能先把它减为一次模型调用。原 140 成功调用/媒体、TW permanent、40.46 基线、模型与原比赛数据继续保护。若身份缺口无法从既有完整证据补齐，应报告未证明的采用阻塞，不能悄悄重新编码/QA。

`improvement/recall_production_v1/no_delta.py:ProtectedNativeFrames.inspect(first,stop)` 只证明 I 中**全部原 native 帧**均在受保护 baseline B 时，对任意合法 K⊆I 有 `B∪K=B`。它检查完整半开 ordinal 范围，不是只看模型见到的 64 帧。两视图共识中，如果完整 view 的所有可能输出原帧都在 B 内，该 view 的 KEEP 对 B 外新帧也无支持，故省略不改变最终新增原帧集合；必须保持其他视角票/原框规则不变并绑定完整 coverage witness。已接受 B0 segment 也只可在其完整合法作用域同样证明后处理。

这不是模型 EMPTY/UNKNOWN，不是实际 processor/model/QA，不证明未观察连续时间区间列表或人类摘要质量等价。每个省略项须另记数学证据、baseline ZIP/原框与 clock/plan/实现身份；实际调用分母与数学省略分母分列，不能给被省略项填“真实推理 QA PASS”。本次未运行 baseline 帧集合或全量 no_delta 规划。

## 7. 最小实现边界与当前阻塞

后续只需在新独立生产根实现四处接口，旧 Store/冻结 profile 不动：

1. **采用清单与阶段清单**：逐个绑定旧成功完整身份、新实际 consumer、共享视觉 identity 与数学省略 witness；只有冻结后的真实集合才是本轮分母，不沿用历史 967 或几何 alias 假设。
2. **单源 RAM producer / 有界单 view QA IPC**：复用 `MemoryRGBUnion` 的纯数据契约，加原颜色转换解码 adapter、source/view durable 状态与显式恢复账目；原完整 clock 只引用，不重新测量。主/QA evidence 返回立即提交，源级成功后关闭 RAM。
3. **新 exact cache adapter**：容器 Mapping-safe；复用字典位模式算法并保留所有 unsupported 原张量/alias 的 lossless fallback，或采用有明确 torch owner/alias 处理的新 array adapter；原始 tensor 只编码一次，储存 roundtrip 从已有 tensor 比较；只有实际完整 identity 相同的视觉部分共享，private token 全留。加入 cache 文件/raw bits/完整输入 manifest 与加载大小界，不能直接调用旧 Store。
4. **独立全阶段 CPU admission**：核全部完整 cache、两份实际 evidence、首次 input-QA receipt、source/code/model/processor/native/token/grammar 锁与动态容量；全过才唯一共享 GPU。GPU 后输出 QA、共识语义复核、baseline 原字节保持与交付差异是后续门，不由本存储审核替代。新加原帧的框仍须引用已自动生成并验收的连续全源空间场，不能因新缓存方案重算或改动 baseline 框。

当前具体阻塞是：fresh 4/后续事实质量门尚未全部完成；新生产生命周期/源码锁/缓存 adapter 尚未冻结；真实字典适用比例与 fallback 总容量未知；运行时 RSS/codec 工作区未实测；旧输入完整身份采用审核与本轮真实分母未完成；RAM-only crash 恢复限制尚需明确登记。因此结论为**可以保留原输入与真实独立 QA 的工程方向，但不能据现有 80.1GB/126GB 快照宣布能装下或生产准入**。本报告完成后停止，不启动任何新实验或全量处理。

## 主代理整合补充：全量时钟原点与字段边界

现有9源事实入口强制其旧原钟为zero-origin；这个特定假设不能复制为426全量的通用假设。新全量实现须引用已验收C7全钟及正末帧duration，分别保留原raw PTS、first original PTS、明确推导的normalized PTS/physical end和ordinal；窗口相对秒与原帧ordinal的映射要绑定原点，不能将normalized数组假称原raw数组，不能再量测、拉伸、截断或修补原钟/标签。新RGB读取时逐帧核原raw PTS和像素身份，是新必要读取的身份核验，不是重写已成功时钟。最终提交仍使用原global frame ordinal；不得因缓存改造换帧或改变保留框。

最终新帧空间结果只从已自动验收的连续全源场按同一原video_id/frame查取，绑定原source SHA、targetRatioWH与四源场文件及其原实现。基线原帧的JSON对象、ratio及model_params原数值字节必须由冻结KEEP-only merge实际保持；旧时间包保框证明和本缓存报告不能代替新合并后的独立11strict与CRC/成员SHA/真实预测差异验收。本补充只审阅接口，不执行全量规划或数据处理。
