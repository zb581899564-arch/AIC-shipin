# 新生产阶段缓存保存契约草案 05

状态：独立批判草案；没有生产准入、部署、媒体读取/解码、processor/model 调用或删除操作。仅用于后续新阶段，不能回写当前 smoke、旧实验或成功材料的保存约定。

## 结论与适用边界

“永久保存确切模型输入，full-resolution native RGB 从一开始登记为 staging，在 GPU 和首次独立 CPU 重放都通过后释放”能够保存实际推理的输入及重现证据。条件是保留全部真实输入 tensor 字节，而不只是像素摘要或所谓视觉 embedding；原媒体、原生时钟、代码/processor 身份、全部请求文字、真实回答/token 和完整证明也必须保留。

目前 `local_boundary_v2` 的 `cache_pixels`、`runtime.baseline_frames`、CPU/GPU input lock 校验仍直接要求 `frame_array_path` 存在并核其 SHA。它不支持本契约。须另建独立新版本和根目录，再冻结新的阶段校验语义；不能删除文件后把旧 required_files 的缺失当作通过，不能修改已冻结旧锁，也不能清除旧 v1/v2、Charades、SumMe 或 VideoXum 成功 RGB。

本策略中的新 RGB 在首次生成前已登记为临时 working artifact，允许释放的条件也在首次模型调用前冻结；历史成功实验不能事后改称 staging。草案本身不授权实际释放。

## 永久保存的最小材料

| 材料 | 需要保存的身份和内容 |
| --- | --- |
| 原 426 媒体与旧证据 | 原文件、原成功媒体 SHA/bytes、旧 clock、field、coarse/raw/失败/费用全部不动；沿用原成功身份，不重复旧解码或模型 |
| 全局新计划 | 426 source 身份、算法/参数/代码、完整事件和请求分母、START/END/VERIFY 请求顺序、采样 ordinals、精确 PTS/normalized origin、窗口/端点/anchor、动作规则及冲突处理；首个模型结果前冻结 |
| 每个新实际模型输入 | 完整 encoded dict 的每个 tensor：key、dtype、shape、layout/stride、确切数值字节 SHA 和无损存储引用；包括 input_ids、mask、所有视频/位置/网格相关项，不能只保存 pixel tensor |
| 输入生成证据 | 原 source SHA、每个原生 ordinal 和精确 PTS、原帧 RGB 像素 SHA、原 RGB staging 文件 SHA/bytes、实际 resize/grid、时间戳注入/native processor identity、完整原文 prompt/chat template/tokenizer/processor assets 及运行版本/代码锁 |
| 模型及输出证据 | 实际 base/adapter/参数/144 层状态、真实 GPU 输入 tensor signature、request、raw、token IDs/scores、grammar/parser/native membership、唯一 BEGIN/ACCEPTED 和自然终态 ledger/resource |
| 独立重放与释放证据 | 首次独立进程从尚在的真实 RGB 经正常 processor 重放每个不同请求，核完整 tensor dict 与真实 GPU 输入一致、核输出 tokens/parser/native；保存 proof、完成回执，以及独立 release manifest |

永久 `.pt.gz` 无损保存可作为第一实现：不得改 dtype、量化、裁剪、补帧、resize 规则或数值。保存后需读回完整文件（含 gzip CRC），核所有 tensor key/dtype/shape/字节签名；GPU 搬运后再次核一致。文件 SHA 和逻辑 tensor SHA 各自保存。若使用分块或字典序列化，重组后须等于原完整 encoded dict，不能仅核总字节数。

这足以直接重放真实输入 tensor。原媒体、精确 ordinals 和冻结 decode/processor 身份还保留了再次重建 RGB/输入的途径；未进行额外重建时，不声称未来任意环境都会生成相同解码字节。后续普通核验使用保留的规范输入及既有独立 proof，不自动重做已经成功的原准备/重放。

## 去重必须保持完整输入身份

“相同 source ordinals + resize grid”是必要条件，不是充分条件。现有 `runtime.encode` 的 native 时间注入还读取 source-relative PTS、window_start、fps、total_num_frames、video metadata 和 processor 身份。视觉去重键至少绑定 source SHA、有序 ordinals、逐帧像素 SHA、几何/实际 grid、精确 PTS、context origin、全部影响视觉/位置 tensor 的 metadata、processor/preprocessing 代码与 assets、dtype/layout。只在实际已生成的相关 tensor 字节相同后建立共享引用。

VERIFY 可在同一旧 coarse window 的不同候选间共享视觉 payload；665 个事件映射到 521 个旧窗口是最多 521 类视觉输入的待验证上界，不能单凭窗口名宣布 521 个实际共享 cache。每个不同候选 prompt 仍有独立 text/input_ids/mask/位置等完整输入引用与 CPU proof，也保留 665 个 VERIFY 模型调用的分母。候选内容和文本不能从其他事件借用。

优先采用文件级内容寻址：视觉 tensor 只存一次，各请求永久 manifest 引用公共 tensor 和其各自文本 tensor，GPU 前组回完整 dict 并核该请求完整签名。文字“token-only cache”不能等同只 tokenize 一段裸文本；必须保留真正 chat template、视频占位符/时间戳、mask 和其他实际输入项。新 token-only 路径若不能证明与正常 processor 的完整输入相同，就使用正常完整编码并只在保存时去重，不引入未验的拼接逻辑。

START/END 只有完整键及真实相关 tensor 一致时才共享；邻近或重叠帧、相同 RGB 的不同时间上下文不能直接共享整段 encoded dict。禁止从重编码视频、低分辨率 RGB、近似 embedding 或更低 tensor 精度替代实际输入。

## 全局冻结、批次锁和暂存状态

| 阶段 | 校验与可释放范围 |
| --- | --- |
| 全局计划冻结 | 全部算法/source/event/request 身份和顺序、去重规则、批次形成规则、证据保存契约冻结；不含将来必定释放的 RGB 作为永久 required file |
| 批次 CPU 准备 | 该批所有请求的实际 CPU 输入、永久 canonical tensor、metadata/proof 全部通过后，才能消费该批；不依早期回答修改后续采样、算法或来源 |
| GPU/首次独立 replay | 永久输入锁要求 tensor/metadata 完整，staging lock 另要求 RGB 实存且 SHA 一致；每个请求真实回答及独立正常 processor 重放均通过，不能以 UNKNOWN/空回答代替工程失败 |
| 批次闭合 | 校验唯一自然 GPU 终态、全部请求 proof 分母、所有 canonical tensor 完整；写 append-only closure 与 release manifest；任何失败或未完成保留 RGB 和全部部分成功 |
| 临时 RGB 释放 | 只释放本次专用 staging allowlist 中、所有引用者已完成首次独立 replay 的新文件；永久文件和旧成功路径不得包含在该集合内 |
| 已释放状态核验 | 原 input metadata 的 RGB path/SHA 仍如实保留为历史生成记录，追加 `artifact_role=EPHEMERAL_NATIVE_RGB_STAGING`、release receipt、实际删除状态；不声称文件仍存在，不改写原 metadata SHA 或旧 lock |

一个 staging RGB 被多个请求复用时，必须直到最后一个已冻结引用者完成重放后才释放。若后续批次仍需要该 RGB，就保留其 staging lease，或在模型开始前按确定规则将同源依赖放在可闭合组内；不能提前删除后为另一个请求重新执行已成功的相同 materialization。永久视觉 tensor 则可以跨批复用，不受 RGB staging release 影响。

消费者显式按阶段校验。完整 permanent source/input lock 不得包含一个以后故意删除却仍假装 required 的路径。RGB staging lock 始终保留其原 SHA 记录；在已释放阶段，以永久 canonical tensor、闭合/独立 replay/release 证明验证生命周期，而不是对不存在的 RGB 计算 SHA。任何 release 计划先写候选精确路径及资格证据，执行后另写实际释放回执；未执行或中途失败不能记为已释放。

释放实现须解析并核所有绝对目标均在本轮独占 staging 根内，无符号链接逃逸；只按精确 allowlist 操作，不递归删除源根/批次根/旧成功目录，也不删共享 canonical tensor。这个草案没有执行上述操作。

## 容量和停止策略

已完成的只读预算为 426 来源、521 原窗口、665 粗事件；共享三种回答最多 1995 调用。未去重的新 native RGB 粗总量约 416,968,584,192B，像素 tensor 下界约 566,669,869,056B。当前约 158,193,520,640B 空间是一次快照，不能作为固定准入线。[预算回执](production_budget_04.json)

首 Charades gzip 比率只能作情景估计，不能担保生产 fit。每批准入使用实际已占用字节、当时 free space、实际 pending canonical payload/serialized 上界、staging 峰值、首次独立 replay 的同时驻留副本和临时写入、完成前不能释放的 lease，以及已测 CPU/RAM/GPU峰值与共享任务。只在尚无实测数据的项上采用保守原字节/格式上界；gzip 压缩可能无法节省，不能凭一个首源比率预支容量。

批次大小只可按已冻结的资源规则和真实大小调整，保持全局请求顺序及方法不变。每批成功后将永久 canonical 增长量累加，再计算下一批及最终剩余输出的保守需求。实际空间不能保证下一阶段时停止并保留全部成功，不删除永久 tensor、不改输入精度、不缩短参考窗或减请求分母，也不以工程空间失败转空预测。

若累计规范输入仍不能容纳，最小替代是上述无损内容寻址的共享 tensor 字典/精确分块序列化，保留所有完整输入 manifest，读回拼装同一 tensor dict；其次是等待新增容量或明确新保存位置。扩大存储和大传输不是本草案自动授权。不能使用有损序列化或删除成功 canonical 输入来保证完成五包。

## 下一步仅限后续主控准入

主控选择新的独立 cache schema/根目录后，先审生命周期消费者和 allowlist，使用已有新接口 smoke 的实际大小评估新阶段容量；旧 smoke 成功代码/输入不改。本草案不将算法、外部科学代理或五包质量判定变成通过，不启动 426 大规模 CPU/GPU。
