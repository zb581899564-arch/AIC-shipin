# 旧调用复用身份定点诊断（15）

日期：2026-10-15（Asia/Taipei）。范围仅为元数据与代码只读诊断；不构成生产、CPU 输入准入或旧调用复用准入。

**结论：目前可核实几何与部分执行身份，但尚不能证明任一抽查旧 B0 调用与未来新 15 秒/native64 调用完全相同，严格复用结论为 UNKNOWN。** 不能把所有旧成功、全部短源、141 个几何候选或 967 个新物理视图直接计作可复用，也不能把旧 VERIFY 回答代替 B0。这次没有复用、准备或重新运行任何调用。

## 1. 检查边界与实际访问

- 本地读取新 `model_common.py`、`pilot_runtime.py`、原 `temporal_refinement_pilot/runtime.py`、旧 `package_family.py`、原缓存 ref schema 和 balanced 路线源码；只新增本报告，未改现有代码或冻结文件。
- 第一次 Linux 元数据批读于 `2026-10-14T16:38:52.375941Z` 返回；先核主机为 `inspur-NP5570M5`、活动任务与资源，已有任务保持运行。使用现有严格 `aic-inspur-home`，未改 SSH、网络或服务。
- 第二次定点批读因只读 adapter 将缓存 ref 错当作 `{path, sha256}` 而遇到 `KeyError: 'path'`，没有启动模型或输入处理。该失败保留于本记录，不冒充完整检查。
- 主代理明确追加授权第三次且最后一次定点批读；于 `2026-10-14T16:44:14.700662Z` 成功返回。按真实 `{relative, sha256, bytes}` schema 解析显式缓存引用。没有第四次远端访问。
- 三次访问均只读已知路径下的 JSON/JSONL 元数据和小回执；没有读取媒体、帧、tensor body、模型参数 body，没有重新哈希模型，没有搬回完整 raw，没有下载、HEAD、decode、encode、model、replay、指标或生产操作。
- 第三次输出的中部被工具截断；未据此补猜遗漏字段，也未为补齐输出追加查询。下列签名是已保存回执中的声明及小 JSON 绑定结果，不是本次读取 tensor 后独立重新计算的签名。

容量入口仍为 `production_metadata_budget_10.json`：426 个记录、425 个物理 SHA、968 个记录视图、967 个物理视图，0 个不足 native64；该预算明确写有 `accepted_old_B0_view_reuse_not_yet_audited=true`。本报告不修改这些预算，也不依据抽查扣减模型调用数。

## 2. 显式元数据入口与缓存 ref

Linux 根路径缩写如下；它们仅为下表拼接，不能作为递归扫描范围：

```text
RUN=/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z
TW=/home/inspur/aic_video_work/twenty_hour_five_20261014_v1
EXP=TW/temporal_global_recovery_control7_v1/exports_01
CACHE=TW/production_stream_v5
```

本地 `improvement/temporal_family_native_v3/package_family.py::checked_inputs()` 从 `TW/temporal_family_native_package_v3/package_inputs.json` 取得 events、verification、source_clocks、production_completion 等显式 refs，并与 package lock 绑定；这比寻找任意旧目录中的成功文件更窄。此次核到的实际入口为：

| 项目 | 实际路径（按上述根拼接） | SHA256 |
| --- | --- | --- |
| events | `EXP/events.json` | `c87c7a54c2918a312c34cffb20bc4e2a68169e5839749b3ca43b507b0fc9f4b0` |
| verification | `EXP/verification.json` | `ec1a3e85de6bd2404911150dd84c4c4ebcd53163d0fbd26a09e943fdea7ad110` |
| source clocks | `EXP/source_clocks.json` | `7052a91331c758737d16b3f1e0e9aaea2d318a1c6d686c6ee8af156ad111c866` |
| original metadata | `RUN/b_score_aligned_package_v4/rematch_01/metadata.json` | `c3612851513f83b2ea1968f3149bf64fbdd57a6d654370ecb31f15c817768936` |
| production completion | `EXP/global_completion.json` | `b072d049588217f14efe1133a3f40c0e4ed54fe5f19deea055cf67741a5e5dfc` |
| production input registration | `TW/temporal_production_inputs_v5/registration.json` | `125d4adc2581381ec13d7dc9d02ce00f2e0553cc7611047b3c9672358d3a509e` |
| original B0 plan | `RUN/balanced_two_window_risk_v3/input_01/rematch_plan.json` | `6ac37ae102836fdf2a44cbf676129a2678019fda34f81874601fe1c5dc055ae7` |
| accepted coarse temporal | `RUN/balanced_two_window_risk_v3/rematch_01/temporal.jsonl` | `22df3234d0cc73d376c7e2beb7d68732fc19c5f123a05bb18bba52851cf001ce` |
| D8 normalized windows | `RUN/boundary_refinement_20261012_v1/input_export_02/temporal_inputs.json` | `240c8b0adbaabf092648bb407d72d82fbe598a40c5fa90c1917096812c254715` |

`global_completion.json` 实际状态为 `PASS_COMPLETE_ALL_PROSPECTIVE_TEMPORAL_REQUESTS_AND_FIRST_INDEPENDENT_REPLAYS`，声明实际参数 8782459120、optimizer 0、VERIFY 与 refiner 为 `TIME_ENABLED`。这是旧链完成证据，不等于新请求身份相同。

进一步的定点路径是 `global_completion.actual_unique_MODEL_proofs[]`，按 `consumer` 找 `first_independent_replay_ref`；该首次 QA 中的 `retained_evidence_refs` 指向 request、done、CPU proof、GPU input、model identity、activation 与 resource/ledger。绝对 ref 与缓存 ref 必须分别处理：

- 普通 ref：`{path, sha256}`；限定为登记的绝对路径。
- stream-cache ref：`{relative, sha256, bytes}`；缓存根来自登记的 `CACHE`，成员必须为其下 `permanent/...`，不接受 `..`、转义或任意根推断。`improvement/production_stream_cache_v2/codec.py::Store.ref()` 明确返回这种格式。
- 本次没有调用 `Store.load_input()`，没有打开其 tensor/visual payload；仅解析已知 JSON refs。不同无损 codec 的压缩文件 SHA 不必相同，是否复用应比较原始逻辑 tensor 身份与完整证据链，不能拿压缩 blob 差异冒充 tensor 差异。

## 3. 新旧调用身份必须分支判断

新入口固定身份：

| 字段 | 新 B0 要求 |
| --- | --- |
| 模型 | 8782459120 参数，原 base 与原 TIME adapter，144 层全部 enabled，optimizer 0 |
| base SHA | `74bcce81cfcb0893cf4b4c25ae36ec908d6ea669583aedd0f3940063080b8b59` |
| adapter SHA | `8e2cca463d8aac39f7a709bdf562373e3e47a3a8da490991c303d5e03b803b23` |
| 文本 | `EMPTY_PROMPT`，SHA `dc0aa31d4a4df1894457a636ace17c55159122d62d7200fd2490ede06e19bce0` |
| grammar/parser | 原 constrained JSON，`allow_empty=True`；保留合法空与工程失败的区别 |
| 生成 | `do_sample=False`、max input 16384、max output 256；相同 tokenizer/chat template/EOS 与 grammar 代码资产 |
| 视图 | 0 起 15 秒/7.5 秒网格；短源为 `[0, physical_end_exact]`；真实 native64、无补帧、无 audio/参考标签 |
| 输入身份 | 全原生 clock、64 个 source ordinals/exact PTS、RGB SHA、processor 资产与 native evidence、完整 tensor signature |

不能把旧 `b_score_aligned_package_v4/config.json` 的 `UNCHANGED_B_1_TO_5`/`allow_empty=false`，或 vendor `PROMPT` SHA `6294dddea26e8ba8ea4d516c2ff39333dbd9a511b4ddc1d9ccb4db3cb9153ea8`，套到所有旧已采用 B0 上。它们与新 `EMPTY_PROMPT` 不同，若某条旧实际请求证明使用它们，则该条请求应排除直接复用；但本次实际 accepted coarse 指向 balanced 路线。

实际 `balanced_two_window_risk_v3/rematch_01/temporal.stage.json` 声明 426 videos、521 windows、invalid 0、`allow_empty=true`、fresh model calls 116、exact original calls reused 405、overview calls 0、原 adapter SHA、optimizer 0。本地源码进一步区分：

- `bw_engine.py::encode_balanced()` 使用 `ex.base_texts(None)['B0']`；其 `bw_common.helpers()` 绑定 `context_advisory_v1/experiment.py::base_texts()`，后者明确 `B0=EMPTY_PROMPT`、`B1=vendor PROMPT`。`bw_engine.py` 新调用显式传入 `allow_empty=True`。
- `part.window == part.base_window` 时采用原 V14 authority handoff，不能把聚合 stage 声明当作每条 reused 分支的原 request、模型 activation 和首次 QA。
- `bw_common.py::local_request()`、`bw_engine.py` 与旧 done 支持 `request_sha256`、`model_identity`、`vision_tensor_signature` 等更深层证据；此次对抽查 B0 聚合记录未取齐这些原始逐调用 refs。`video_identity.tensor_signature` 缺字段不意味着旧系统从未保存任何 vision signature。
- 同目录未见名为 `model_identity.json` 的文件不表示无模型证据；本地代码把 fresh 模型身份写为 `rematch_01/model.json`。它及 reused 分支的原身份来源属于后续精确 lookup，不能凭文件名猜结论。

因此，仅在证明某条旧实际请求使用 vendor PROMPT 且与新 EMPTY 不同时，才能据此排除该条复用；不能将它作为整个 accepted_coarse 的通用排除条件。本次既没有证明所有旧 B0 prompt 不同，也没有证明每条旧 B0 已与新调用相同。

## 4. 两条按几何选择的实际样本

选择规则先固定为：按数字 `video_id` 升序，取 `physical_end<=15` 且旧 normalized window 与新 `[0,physical_end]` 有理端点完全相等的前两条；没有按回答、KEEP/DROP、预测内容或分数挑选。元数据中短源计数为 231，其中精确几何候选 141；两者只是元数据筛选计数，不是可复用数。最终样本为 `video_id=0` 与 `video_id=3`。

另一个先期检查到的短源 `video_id=2` 已给出几何排除反例：其新物理末端为 `69091/7500`，旧 recipe window end 为 `4606061111111111/500000000000000`，两者严格不相等。不能截断、伸缩、加 epsilon 或修写旧 end 来凑复用；同为短源、帧数相同不够。

### 4.1 B0 几何与证据边界

两样本的 B0 计划定位为上述 `rematch_plan.json` 的 `jobs[video_id]/windows[0]/window`，完成记录定位为已绑定 `temporal.jsonl` 的对应 `video_id/windows[0]`。这是实际记录选择器，不冒称另有已读取的独立 request 文件。

| 字段 | video 0 | video 3 |
| --- | --- | --- |
| source SHA | `c2273f4fc696c8fa746997e4f2757e8aefcd905418860f01436eca4b57b72038` | `a31665de7b7d5e45600c59dac7d72284b0e77702e71eedd06233e061ff561f3d` |
| window 几何 | 精确等于新短源窗，末端 `21021/2000` | 精确相等的 selector 已通过；不从被截断输出猜末端数值 |
| physical samples | 真实 64，无 native padding copies | 真实 64 |
| source ordinals | 与新 floor64 计划相等；首 0、9，尾 619、629 | 与新 floor64 计划相等；首 0、3，尾 241、245 |
| ordinals canonical SHA | `3eea42e8e75cf34c19f9372dffae2fbfa4ad2da7f0907192dbba1430b6284106` | `8ea2fb5e7d0a8ea9e43a0c50e3f0e20d515036a0b43599a0d22cb626ed8029cd` |
| `video_identity.tensor_signature` | 未保存该字段 | 未保存该字段 |
| 逐调用 `adapter_enabled` | 本次所读位置无该字段，不能解释为 false | 同左 |
| 完整新旧 B0 tensor/prompt 实证 | UNKNOWN | UNKNOWN |

video 0 原 B0 视觉元数据另有 input tokens 12066、video grid `[32,52,28]`、每帧 pixels 372736、shortest/longest edge 4096/25165824、truncation false，64 个 frame pixel SHA 列表的 canonical SHA 为 `8f25d94945274306d55499882a5418c6fb709ed972a9118779b5a643cd5ddfc2`。这些可以帮助定位，但还不是完整新 B0 tensor 等价证明。

补充主代理实际小回执 `actual_video_grid_observation_18.json`：新 confirm 的真实64帧输入为 actual pixels 372736、grid `[32,28,52]`、tokens 12085、pixel values float32 `[46592,1536]`。因此 loader 的 min/max kwargs 131072 不是实际视频 pixels cap，不能用它排除旧 video 0 的 372736 pixels；新 video_size 仍为原 config。两样本复用须比较实际 grid/完整签名，结论继续 UNKNOWN。此条引用主代理新观测，没有追加 SSH。

### 4.2 实际旧 VERIFY 的 request/input/done/首次 QA

两样本确实各有一个旧 VERIFY consumer：

```text
video 0: P_98089e6d36f78e9766c9ea34d5acb361_W000_E00.verify
video 3: P_a4aab3f1f08004e907d2357fafe74cab_W000_E00.verify
```

令 `C` 为该行 consumer，各实际路径为：

```text
request: CACHE/permanent/proofs/runtime_v5/B000/gpu/C/request.json
done:    CACHE/permanent/proofs/runtime_v5/B000/gpu/C/done.json
input:   CACHE/permanent/inputs/C.json
CPU QA:  CACHE/permanent/proofs/C_CPU_input.json
firstQA: CACHE/permanent/proofs/runtime_v5/B000/output_replay/C.json
model:   CACHE/permanent/proofs/runtime_v5/B000/gpu/model_identity.json
active:  CACHE/permanent/proofs/runtime_v5/B000/gpu/C/activation_inside.json
```

| 小回执 SHA256 | video 0 | video 3 |
| --- | --- | --- |
| request | `62639856f3d1bef595bc3c8c4b67667193d5ffc40bf035df3fd8c744acf217a8` | `aa87edf533cfe1cf68565f740b09a717ec0da4768a447edf83ae36943c86eb07` |
| done | `411fa5db502618d47542a658e3a0fe2eb83cf12bb06d171dfe823820d13685f6` | `9925c5511517e09844ef0d35cbf8ba6e947debdb035723d04fb4e0a9b9f16547` |
| input manifest | `7cd93cd720bf16f222dd9604e60b9111d9858f7606c667b6c667e8a2f43fd555` | `cb950dedc8d633e079d46d413e1f3037f1cd014f730b35fd1505e68101dd4bc8` |
| CPU input proof | `cba13fa0174231149539793f298e92a47c2efaa12410d7ad838bcf761e4b3a0f` | `c81b18a050d188f0a1837d12848db5949c6da1a9a27c5a7d07c5770d724c0446` |
| first QA | `b950bd6a299d5ae4a10fd181c1488ca0e4d9fde46a40e65601cb950a592315ec` | `9b9e6bfe5b9073c45292bf3a8aea93fca508108eeef89b38753849a626c5135b` |
| actual prompt | `97659163e29eef972f563b0725bc15720ea5d20da9fc1eadb520eb4b6369b935` | `abcf2f7afe82349579e106c37c32348ae909aca29fb4c979983258ddf63b906f` |

两条首次 QA 均为 `PASS_FIRST_INDEPENDENT_REPLAY`，保存 normal processor from RGB、token/grammar/parser/native QA 的通过声明；done 为 `PASS_PRODUCTION_BATCH_DECISION_NOT_QUALITY`。request 类型为 `VERIFY`、角色 `TIME_ENABLED`、有限分类响应 grammar、max output 256、do_sample false。分类 grammar 没有 `grammar_allow_empty` 字段属于此接口不适用，不能擅自读作 false，也不能将它等同 B0 段列表 grammar。

两条 input manifest 均保存真实 physical64、完整 tensor signature；ordinals 与各自新 floor64 计划相等：

| 保存的 tensor 元数据 | video 0 | video 3 |
| --- | --- | --- |
| exact sample PTS canonical SHA | `fe5618579c286655ad0bc7395348fec29fca039175de51f69c7abc8d1c1af6a3` | `c88b51bfa3081e1a2168e5544bc49ed1a1d0925714175427ea58e6d3acdc75c2` |
| input_ids | int64 `[1,12243]`，SHA `076b424026399e9d8c0bfd69d90315297cc49fb56bf5e3255ef286f479bd5f34` | int64 `[1,12231]`，SHA `35df5db416a4084369b00d17dca28e1433ba1df6e52c881cb4734b5020afb2bb` |
| attention_mask SHA | `567ffafe09246882bfceb032fc30ea4a8e26f6d6feea47cf072d114a099e0207` | `e5ba3872401043826847e884e86b95d93337655c59326947467121f367df0133` |
| pixel_values_videos | float32 `[46592,1536]`，SHA `d75c5341ab30d0e3543858c02aabfa5accccfbef794270f81b7af6326c9223e7` | float32 `[46592,1536]`，SHA `879d37a69af02c0d17abc28c4451056eee1e63a71be3f3d25e589774ee66a170` |
| video_grid_thw | int64 `[1,3]`，SHA `0003332c7e92dec32d3f589d4846a734f59ae6aec3f65a7e510c413dc67513fd` | 同左 |

共同 model identity SHA 为 `28c216fa0eea1b846186ea64c3775549a7e0be2dbf2dc305889f535494da2225`；包含 logical parameters 8782459120、base parameters 8767123696、上述原 base/adapter SHA、288 adapter tensors、saved values equality、adapter enabled、optimizer 0。两条 activation inside 小回执 SHA 均为 `99557e2679992419c4919065833fd2a9f2d801b8e1c62a238d6ee2370fe5c675`，声明 144 层、144 个 `disable_adapters=false`、active adapter default、activated parameters 8782459120、TIME_ENABLED。

这证明了这两个旧 VERIFY 存在可定位的真实执行与首次 QA 身份证据，不证明尚未生成的新 VERIFY request 与它们相同。新 B0 的 EMPTY_PROMPT 与这里的 VERIFY prompt 属于不同任务；旧 VERIFY 响应不能充作 B0，也不能在新 event/原段区间未冻结时预先抵扣未来 VERIFY 调用。

## 5. 可直接采用旧成功的严格条件

后续若要登记旧调用复用，必须逐 actual view/call 给出完整比较，任何缺项保持 UNKNOWN：

1. **源与时钟**：同一物理 source SHA、完整原 clock identity、相同有理 window start/end/physical end、相同 origin；64 个真实 source ordinals 与 exact PTS 全相同，无 padding/插值/epsilon。
2. **实际模型输入**：相同 RGB/frame pixel identity、processor/tokenizer/config/chat-template/preprocessing 资产和 native 参数；所有实际输入 tensor 的 key、shape、dtype、逻辑字节 SHA 与 token prefix 一致，包含 input_ids/attention/vision/grid/时间相关键。仅“64 帧”“同分辨率”或 vision grid 一样不够。不同无损存储格式须有既有严格恢复证据，不能用 codec 名相近代替等价证明。
3. **请求与 grammar**：同 task、原始完整 prompt 和渲染/token 身份、generation 参数、EOS、grammar/parser 代码及 `allow_empty`、时域和 native 映射完全一致。若旧实际调用采用 B1 的旧 PROMPT/禁止空，而新为 B0 EMPTY/允许空，直接排除；不得更改旧请求或旧 raw 后重新命名为相同。
4. **实际模型**：原 base/adapter 哈希、实际参数数、144 层 TIME activation 与各层 adapter 状态、运行角色及 optimizer 0 已在该调用的绑定证据中成立，不能只靠全局配置或相邻调用身份。
5. **成功与唯一性**：原 request/raw/done、输入 proof、首次独立 input/token/grammar/parser/native QA 和共享 wrapper 自然 completed/exit0、唯一 ledger/resource 闭环；新登记只引用这一次原成功，不重复模型或成功 QA。失败、缺失 raw 或未完成不能作为合法空。
6. **VERIFY 额外要求**：同一原 event、原段 exact interval/native range、原 case/segment index、同 context view 和精确 token-only 请求；不把 D8 padding、基线 UNKNOWN-retain、candidate_kept 等含义误充 overlap 的显式 KEEP。仅像素相同最多支持后续另登记的视觉输入采用，不能直接采用分类决策。
7. **新入口采用**：新 source/input/code/phase lock 显式包含所采用旧证据与不可变映射，别名指向同一次实际成功。现有新入口不会因为发现旧文件自行绕过自己的 CPU/缓存门；采用逻辑与准入需要单独登记，本报告没有实现或启用它。

两抽查样本只满足其中部分条件。当前缺口是 B0 逐分支原 request/done/provenance、完整输入身份与对应模型/首次 QA/resource 绑定，以及未来请求的精确身份比较；不能从旧 VERIFY 完整性反推同源 B0 完整性。

## 6. 后续一次全量 metadata lookup 的边界（本次未执行）

如主流程另行安排，适合一次在 Linux 内完成固定 lookup 并只返回小统计，避免再零碎 SSH 或扫描磁盘：

1. 只从本报告固定的 package inputs refs、`temporal_production_inputs_v5/registration.json`、original plan、accepted coarse temporal、D8 normalized windows、global completion 以及它们直接登记的 proof refs 出发；读新 967 视图的纯 metadata 计划。以 source SHA + exact domain + 64 ordinals/exact PTS 建候选索引，不根据预测内容挑样本。
2. 对旧 521 windows 识别 `window==base_window` 的原 V14 handoff 与 fresh balanced 分支，沿 `original_success_alias`/authority、原 done 的 `request_sha256`、`model_identity`、`vision_tensor_signature`、registered prompt、原首次 QA 和 `model.json` 等显式 refs 找到实际证据。若原 request 是确定性摘要而非独立文件，只能按冻结的原 constructor/代码 SHA重建同一摘要，不能虚构 request 文件。
3. 对 `actual_unique_MODEL_proofs` 只读每个候选所指向的小 JSON，正确区分绝对 ref 与 stream-cache relative ref；逐项输出 `IDENTICAL_METADATA_PROVEN`、`DIFFERENT` 或 `UNKNOWN_MISSING_EVIDENCE` 以及缺项/冲突原因。没有新输入或没有可比较的完整旧 tensor signature时，明确保留 UNKNOWN。
4. 在单独新登记的 Linux metadata index 保存 refs/摘要/原因；不读取媒体、tensor/model body，不重新编码或推理、不执行原 QA、不重新哈希模型、不拉回完整 raw。若需要 payload级恢复校验或新准入，那是后续独立工作，不能塞入此 metadata lookup。
5. 只输出候选、排除、UNKNOWN 的实际计数与必要小 refs；不得先把几何候选数写为调用节省数，也不自动推进 prepare、model、旧 label/raw采用或生产。

本报告完成即停止定点查询。实际可复用调用数、可节省处理量与生产采用状态仍为 UNKNOWN。
