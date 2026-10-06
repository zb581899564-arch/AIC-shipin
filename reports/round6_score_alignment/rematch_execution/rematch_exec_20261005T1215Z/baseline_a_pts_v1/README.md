# A_NATIVE_PTS_COMPAT_V1

本目录是独立 A-PTS variant，生产 revision 04 已冻结。它支持与旧 A 不同的
native presentation clock 输入合同；不能将其写成原 A 科学协议完全未变。
旧 `baseline_production_v1`、`baseline_a`、v3 审计及其阻断结果保持只读。
帧编号是 source decoded-order ordinal。官方输出使用源 frame 编号；本地
PTS/Decord 原点绑定是工程 identity 合同，不声称为官方 timestamp 原点要求。

## 冻结身份与改动范围

`snapshot_lock.json` 保存从 `baseline_production_v1` 复制的 11 个小源码/
配置文件的字节身份。`vendor_lock.json` 的历史 vendor 保持原字节。
`additional_frozen_dependencies.json` 记录已存在的四个 strict loader 文件，
仅复制到本新目录满足原 vendor lock，不回写旧目录。

新生产入口是 `run_pts.py`；七个新生产文件由 `source_lock.json` 绑定：

| 文件 | revision 04 SHA-256 |
| --- | --- |
| `pts_contract.py` | `0e18b306d75df10e4af5f794d19c69f0deb09585893a5452738acdd570e9b784` |
| `exact_pts.py` | `30d4012a34646b59c56a8d77ecd7807cd13845dfe63ab3f70259902e560ed6b1` |
| `native_frames.py` | `f2fd7900d1862a2e25fd42af6554888c5b9b7e31a8340bccdcbe9444447bedbf` |
| `run_pts.py` | `2a34da6c76e7d76fd974518c385991968e64115701f1bbf8643a9134842c3f57` |
| `infer_temporal_pts.py` | `016e6f1186b8fdfe93216c4a0fb1de14a2917e667bcfb842241f576d6a98f8e0` |
| `detect_shots_pts.py` | `b71dceee4209752b4b3cd70be36379800abc486768cbff62a4ef87b1bfb77d7a` |
| `infer_anchors_pts.py` | `c3baa687c6e37173a1856967b61c1ff794df7892e01dabc6c77afa32fc0cec4f` |

Source lock SHA-256：
`86fc0da7cf631a2afe33c54fb5b66246bba88adfd95c1d8ce80ccbf73522d70d`。
冻结 `config_a.json` SHA-256：
`137a60e3efae567794105bac8d2fcb4288c7d1b289ab4ad1d0a81e2ba11c5414`。
P2-T2 adapter SHA-256：
`c9bf3754a05a42d69ee8c4d11f56c41346d927094fd643863f0cb55626b8e6a0`。
完整 base-model 和 spatial baseline 字节身份继续从该原 config 校验。
Prompt、模型、adapter、配置、采样上限、shot 阈值、锚点间隔和框规则均
沿用原版本。文档和测试文件不进入生产 lock；测试 receipt 单独绑定测试 SHA。

## 时钟分支

读取 `baseline_pts_v4/SCHEMA.md` 定义的 v2 manifest 和 v4 registry；每次执行
验证两者 SHA、完整 426/8 分母、每源身份、clock arrays SHA、分数时钟和分支。
分支只依据原时钟格式资格，不依据质量、内容、模型输出或线上分数。

`CFR_LEGACY`（本轮 416 源）需要原 `1/fps+1e-6` CFR 资格、start binding 和
`legacy_interval_pass`。其 duration、窗口、temporal clip、processor、parser、
秒转 frame 选择和空间 OpenCV 路径沿用旧 A。原 CFR interval 证据不等于
native packet endpoint 证据；这里不要求 CFR 的 native `end_pass=true`。

`NATIVE_PTS`（本轮 10 源）需要全部 integer starts、positive packet durations
和 Decord float32 starts/ends 精确绑定。终点是末源帧 native packet end 与
Decord actual end 的交叉证实，header duration 差异仅诊断。缺终点或任何身份
失败均 STOP，不删除源、不将旧 CFR fail 改写为 CFR pass。

Native 窗口沿用不重叠 30 秒与末段短于 0.2 秒不建窗口的规则；实际 source
帧通过 `[start,end)` 的 `bisect_left` 确定。窗口内最多 64 个均匀 source-frame
ordinal 样本，未改为时间均匀采样。Processor 时间采用实际 relative PTS 减
window start；每两个时间 patch 取实际时间均值，最后 odd padding 的时间是
重复末 physical frame 的时间。Override 只作用该 processor 实例，退出时恢复。

实际 Fast processor 在 pixel 长度 1 时先拒绝输入，尚未执行其 odd padding。
Revision 03 因此仅把单 physical frame 的像素和 processor metadata source ID
显式复制一次；不增加源 frame 或时间。记录保留唯一 physical IDs、processor
input IDs、显式/隐式 padding 数。3/63 等 odd 长度仍采用原 processor padding。

原 parser 可能把分数 duration round4 后表示为稍大于真实末端的值。Native
wrapper 先调用原 parser，只对其已接受且 `end==round(duration,4)>duration`
的末端恢复真实 duration，并记录 `LEGACY_ROUND4_NATIVE_ENDPOINT_RESTORED`。
原 raw output 保留。原 `1e-3` 输入规则不扩大，1–5 段、空失败和其他解析
失败不变；无 source-frame 的正时间段仍 STOP。CFR 返回原 parser 结果。

空间 native decode 从零顺序消费 Decord 帧，先验证 source SHA/count/fps 和
全部 starts/ends。Shot descriptor 和空间重开均以同一 source ordinal 取帧，
后者必须匹配 shot 请求中的 BGR pixel SHA。shot gap 与 max-gap 8 都按源
frame 序号计算；原阈值、镜头内插值和框构图逻辑保留。

旧合同投影只用于原 frame/box/provenance 校验；native 窗口和 frame 选择始终
使用 native registry，未用投影的 n/fps 伪时钟推理。

## 已完成与待验收

本地 `cpu_contract_tests_06.json`：30/30 PASS，绑定 revision 04 lock，SHA-256
`18d2661bfcc39cc55adb0d7c00b567b21b862dd203461baf5aad632875235864`。
覆盖 CFR 原 selector 和 prediction JSON 字节一致、native 半开边界及逐帧
往返、分数端点、padding/processor timestamp 接口、异常身份 STOP、无空输出
回退、temporal-only admission 拒绝 spatial。CLI help 和 Python AST 通过。
此 CPU 合同测试没有运行实际 processor、decode 或模型。

`cpu_cli_regression_04.json`：7/7 PASS，SHA-256
`1f3867e28f80f8664e6051530ad929eb97d9d71d151a9af5cdc2a32370b651df`。
它启动实际 shots/spatial 脚本子进程；CFR 与 mixed native 的完整 shots main
运行清单/clock 验证、原 descriptor、shot flags 与序列化，输出字节和原 vendor
shot 算法相同。坏 manifest SHA/schema、registry binding，以及 spatial 坏
request SHA 均在打开 decoder/加载 model 前 STOP。唯独 decoder I/O 是受控的
可区分帧 synthetic 替身，不能将这个测试单独称为真实 codec identity proof。

总控 Linux revision 01 actual processor 的 3/63/64 帧通过、1 帧失败，receipt
`controller/a_pts_processor_01_receipt.json` SHA-256
`2dd16247a3483b06e1cba96cf09a9189f6e3f16304cc8abe64fce4bb589f6e37`。
`runtime_attempt01/` 保留原 lock 和两个修改前模块；
`runtime_attempt02_preterminalfix/` 保留已冻结 deacc revision 02 的七个原生产
文件和 CPU 27-case 证据，逐文件 SHA 复核一致。两处失败详见各目录 FAILURE.md。
`runtime_attempt03_pre_sha_fix/` 保存 revision 03 完整四锁及所有锁定 runtime/
vendor/dependency 文件和原 CPU 30-case receipt。主控 actual NONTEST8 的 temporal
和 select 为 396 帧，shots CLI 在 manifest SHA 检查处失败：`UnboundLocalError`
因为 main 尾部局部 `sha=lambda` 遮蔽了入口的全局导入。Revision 04 只删除
这一个重复局部 lambda，继续使用已导入的相同 SHA-256 函数；其他六个生产
文件完全不变。空间入口已审查，没有同类 local sha 遮蔽。旧实际失败保留，
不得将部分 stage PASS 写成完整 E2E PASS。

主控已报告 revision 03 actual `processor02` 四 case/原限制复现 PASS，独立
`decoder01` 的两个 80-frame lossless RGB marker CFR/VFR+nonzero/gap PASS；
decoder receipt SHA-256 为
`658fc2756918522374a4dbc92baa8c26caa401fc386abc7e5f2a98e677045435`。
该 decoder 测试不覆盖 shots CLI main 的 manifest 前端，所以不能掩盖上述失败。
这两个 receipt 绑定旧 revision 03 lock，主控须对 revision 04 重新核验绑定，
再运行全新 NONTEST8 E2E。Actual processor/decoder 尚未由本执行代理运行。
合成测试只生成新 synthetic pixels，不读取比赛像素/标签。全部通过后，
主控再决定正式 426 分阶段准入；本目录不自动授权训练、提交或上传。

## 主控 CPU 命令

使用已验证 Decord 的既有 Python；不使用未验证环境，不安装依赖。

```bash
RUN=/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z
NEW="$RUN/baseline_a_pts_v1"
PY=/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python

"$PY" -B "$NEW/test_contract_cpu.py" --output "$NEW/cpu_contract_linux_04.json"
"$PY" -B "$NEW/test_shots_cli_cpu.py" --output "$NEW/cpu_cli_linux_04.json"
"$PY" -B "$NEW/test_processor_synthetic.py" \
  --base-model /home/inspur/aic_video_work/models/Qwen3-VL-4B-Instruct \
  --output-root "$NEW/real_processor_03"
```

Actual processor receipt：`real_processor_03/processor_receipt.json`。保留原
`real_processor_01` 和 `02`。脚本要求同一 frozen tokenizer/model config 字节，只加载
processor，CPU arrays，不加载 model weights，不跑 GPU。1、3、63、64 四 case
均需 PASS，另要求 unpadded single-frame 的实际限制复现 PASS；记录 actual
patch grid、末 patch 时间、实例恢复、physical/padded IDs 与 runtime/test SHA。
黑数组证明 timestamp 接口，不证明不同源帧 pixel identity。

独立 decoder CLI 由 `test_decoder_synthetic.py --help` 与其单独说明定义：
应传既有 `/home/inspur/anaconda3/envs/Andy/bin/ffmpeg` 和 `ffprobe`，产物 root
为本新目录下独立 synthetic evidence root。其源码/receipt SHA 由主控登记，
必须验证区分每帧 marker、native reader、descriptor/anchor 和空间重开身份。

## 新入口与准入

每个 stage 使用相同新 manifest、registry 和独立 run-dir；stage 已有 receipt
时拒绝重跑覆盖。八 stage：`preflight temporal select shots anchors spatial
compose package`。只在主控准入和 shared GPU wrapper 内运行 GPU stages。

```bash
# MANIFEST/REGISTRY 填 v4 builder 的实际输出路径；先独立复核 SHA。
"$PY" -B "$NEW/run_pts.py" --stage preflight \
  --manifest "$MANIFEST" --expected-manifest-sha256 "$MANIFEST_SHA" \
  --clock-registry "$REGISTRY" --expected-clock-registry-sha256 "$REGISTRY_SHA" \
  --run-dir "$E2E_RUN"

# 对 temporal / spatial，命令须由 controller/gpu_run.py 的正式资源登记包装。
"$PY" -B "$NEW/run_pts.py" --stage "$STAGE" \
  --manifest "$MANIFEST" --expected-manifest-sha256 "$MANIFEST_SHA" \
  --clock-registry "$REGISTRY" --expected-clock-registry-sha256 "$REGISTRY_SHA" \
  --run-dir "$E2E_RUN" --admission "$ADMISSION"
```

已由主控报告的 v4 registry/manifest SHA（仍需部署端路径绑定）：

| Scope | registry | manifest |
| --- | --- | --- |
| NONTEST8 | `7f57785312c94b1658cb002b2432d09b318ae2943e3297a0c45536d1bd8cd3ea` | `ba34a284183e8a079054ffe811d7ec096e6b47c94e6edf812a37fd11b92d8dd7` |
| REMATCH426 | `1058aba02e5e959bc8e4842cbde0eadced192a8201d5c833ae50a7c0aac07909` | `ceb91ee9434ce3de6a55abf727e613b83368b547d3be3d1e71b46414c2f019f8` |

Admission 必须绑定 `variant`、manifest/registry/source_lock SHA、精确 run-dir、
`stage=A_PTS_NONTEST_E2E` 或 `A_PTS_REMATCH426_INFERENCE`，以及主控确认的
资源 preflight、queue、80 GiB 峰值、budget runner。`allowed_stages` 必须含当前
GPU stage，spatial 另需 `space_inference_admitted=true`。文件不替代实时共享
active_gpu_job 的祖先进程核验。

REMATCH admission 另需新 `non_test_e2e_pass`、`synthetic_processor_pass`、
`synthetic_decoder_pass` 及三个独立 evidence SHA。首次 REMATCH 仅 time 和
CPU scheduling，space 要主控根据实际选中帧/shot/anchor 数单独登记。NONTEST8
可由主控在独立小 scope 一次授予全部八 stage；不能把它伪写成 426 gate PASS。
`admission_template.json` 是未授权模板，填值和放行仅由主控完成。

## 成功和停止标准

成功需要：新源码身份成立；全分母 source-clock 身份可用；actual processor
所有 case、区分帧 synthetic decoder 和新 NONTEST8 完整链路验收；所有时间
窗口有效；选中、锚点、合法框、provenance 完整；空间重开 pixel SHA 一致；
独立 strict loader/package 校验成立。任一失败保留原记录并阻断下游，不能
drop 源/段、改阈值、静默补框、改原 CFR 资格或把失败改成空输出。

最终 `candidate_A_PTS.zip` 仅包含 `predictions.jsonl`，其 frame 为原 source
ordinal；package PASS 只代表工程/格式证据，不能声称构图质量、官方提分或
上传成功。验收运行的真实耗时、内存/磁盘和 GPU 账本由主控追加保存。
