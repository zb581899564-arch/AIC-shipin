> 历史方案提示（2026-10-21）：本文件保留原DPO实施历史。当前真实终态请先读 [最新状态](reports/github_status_20261021_v1/START_HERE.md)；不要按历史待执行条目重启。

# 执行交接：native_preference_v1

**本轮交付代码与真实合成CPU检查；本文件中的Linux资产准备、Torch gate、Qwen调用、训练、实际评分、正式推理和封包均未运行。** 最佳仍为用户反馈40.47。先读 [NEXT_PLAN.md](NEXT_PLAN.md)，再按本文件逐阶段执行；不把README中的历史任务或旧PASS当成本轮准入。

本协议只有一个模型机制：原TIME固定参考、同原生帧数且同实际suffix token数的完整答案DPO。原TIME同输入同解码是唯一机制对照；40.47外部选择是另外的保护参照。没有新模型下载、官方标注/伪标签、闭源服务、阈值扫描、五包融合或自动官网提交。

## 1. 拿到这个确切提交，保持旧资产只读

从PR最终交付的**完整commit SHA**采用独立代码；不要检出不断移动的main或自动挑最新experiment。PR建立在 `42c0a72cf49b5d51784d1ee162630f8b74ccd294` 上，不能丢掉PR #1已有修复。容量紧张时只部署本模块全部Python文件、code_manifest和CPU测试引用的原summary_grammar6.py，并逐成员校验；不要求Linux克隆整个历史仓库。下列clone仅为容量充足时的可选部署方式。

下面的变量在同一个Linux shell设置。唯一需要从本次交付消息填入的是 `AIC_IMPLEMENTATION_SHA`；不是模型revision。

```bash
export AIC_WORK=/home/inspur/aic_video_work
export AIC_REPO="$AIC_WORK/code/AIC-shipin-native-preference"
export AIC_IMPLEMENTATION_SHA='填入本次PR最终完整commit_SHA'
export AIC_PY="$AIC_WORK/env/qwen3vl_isolated_20260910/bin/python"
export AIC_RUN="$AIC_WORK/native_preference_20261019_v1"
export AIC_CODE="$AIC_REPO/improvement/native_preference_v1"
export AIC_ENTRY="$AIC_CODE/run.py"
export AIC_CONFIG="$AIC_RUN/config.json"
export AIC_ASSETS="$AIC_RUN/assets.private.json"
export AIC_FORMAL_ASSETS="$AIC_RUN/production_assets.private.json"
export AIC_GPU_WRAPPER="$AIC_WORK/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/resource_unlimited_v1_20261007/gpu_run.py"

git clone --no-checkout https://github.com/zb581899564-arch/AIC-shipin.git "$AIC_REPO"
git -C "$AIC_REPO" checkout --detach "$AIC_IMPLEMENTATION_SHA"
git -C "$AIC_REPO" merge-base --is-ancestor 42c0a72cf49b5d51784d1ee162630f8b74ccd294 HEAD
test "$(git -C "$AIC_REPO" rev-parse HEAD)" = "$AIC_IMPLEMENTATION_SHA"
mkdir -p "$AIC_RUN"
cp --no-clobber "$AIC_CODE/config.example.json" "$AIC_CONFIG"
cd "$AIC_REPO"
```

若已有同名checkout，先核其确切SHA及工作树；不要用覆盖文件的方式“更新”正在执行的代码。每个stage目录只允许认领一次；如果已存在 `claim.json`，停止并读失败/完成记录。不要删除claim或改名重复失败小试；需要新的科学决策后才另立新的实验。

配置中的run_id/run_root必须与上面一致。机制设置冻结；资源上限只能收紧。执行时 `code_manifest.json` 核验新目录所有Python文件的闭合清单及SHA；私有manifest另外绑定旧helper、实际模型目录和所有数据/输入。入口是绝对路径，能够在旧GPU wrapper切换cwd及PYTHONPATH后正确加载这个独立checkout。

## 2. Linux资产接口：采用明确旧登记，不猜路径

资产bootstrap直接读取下列已知登记链，核SHA后生成本轮私有manifest。以下是固定默认路径相对于 `AIC_WORK` 的含义：

| 入口/资产 | 明确路径 | 用途与限制 |
| --- | --- | --- |
| 原始训练登记 | `bottleneck_24h_20261019_v1/summary_CPU_registration_05.json` | source_registration指向`source_clear_residual_20261018_v1/registration.json`原33来源登记；25个train来源只按源SHA选择固定8个fit来源 |
| 已接受训练输入 | `bottleneck_24h_20261019_v1/summary_inputs_05/input_acceptance.json` | prepared→144窗、source_catalog、原多评审目标；不运行旧prepare launcher |
| 原始开发登记 | `bottleneck_24h_20261019_v1/summary_dev_CPU_registration_09.json` | 同一原始source_registration的8个check来源；matched_fullbaseline_source_adoption绑定下方归一化监督登记，全部历史曝光 |
| 已接受开发输入 | `bottleneck_24h_20261019_v1/summary_dev_inputs_09/input_acceptance.json` | prepared→8来源、43窗；必须等于generation10的first_dev_input_acceptance_ref并完整覆盖每个来源；07/08失败记录不替代此成功链 |
| 归一化完整监督登记 | `meaningful_residual_20261018_v1/registration.json` | 由generation10的baseline_human_adoption_ref明确引用；data_ref提供完整baseline/labels NPZ，clock_ref提供归一化原生时钟，不含media；baseline_ref必须是保护40.47 |
| 原作者训练参考采用证明 | `source_clear_residual_20261018_v1/original_human_label_adoption.json` | 归一化登记original_human_adoption_ref指向此证明而非原33来源登记；25个train证明的sid/label_ref须逐项绑定原始labels_ref |
| 原TIME/BASE身份及pixel helper登记 | `bottleneck_24h_20261019_v1/summary_generation_registration_10.json` | 同时绑定model_config_ref、initial_TIME_ref、code、codec/dictionary及上述监督和开发接受链；不选择objective20权重 |
| 原TIME43控制及首次输出验收 | `bottleneck_24h_20261019_v1/summary_generation_10/INIT_TIME/{completion.json,first_independent_output_QA.json}` | 显式采用同09输入、原TIME/BASE、原grammar6的已成功回答；不重复原43模型调用 |
| 保护生产登记 | `semantic_context_production_20261016_v1/production_registration.json` | 采用selected_head和旧真实参数清点；其中baseline字段可能仍指40.46，不能当40.47包 |
| 保护40.47包 | `semantic_context_production_20261016_v1/package/candidate_CONTEXT_SEMANTIC_RESIDUAL.zip` | 只读；384630B，SHA256见下文 |
| 正式输入登记，只有生产评审时才采用 | `five_summary_sprint_20261019_v41/input_registration41.json` | 原426来源；不执行旧全量launcher |
| 正式输入接受 | `five_summary_sprint_20261019_v41/formal_inputs_41/input_acceptance.json` | 现有522个两视图窗；以真实登记为准，超过有限上限则停 |
| 冻结空间封包输入 | `twenty_hour_five_20261014_v1/temporal_family_native_package_v3/package_inputs.json` | 原field、source manifest、native clock registry及严格验证器闭包 |

保护ZIP SHA256：

```text
b37c4a2e6593fc800f54ecce2f860fee5e7d5dc74e17ce280f9ee6722afbccd3
```

私有manifest不是手填几十个模型/patch SHA。bootstrap沿显式旧ref读取、计算和核对；登记不存在或schema不同就停，把实际差异回报给制定方案的Agent，不自动glob/latest或改指别的实验。没有复制17GB模型、重新下载权重、解码全部媒体或重提特征的步骤。

原33来源登记负责来源身份和用途声明：train使用原`native_ref/labels_ref`，check使用原`reference_ref`，两组均保留`media/clock_ref`。它不提供`data_ref`。归一化监督登记负责既有完整NPZ与归一化时钟；两层完整sid/group/name集合必须一致，媒体SHA取原始登记，归一化监督时钟须与已接受source catalog逐原生PTS及物理终点精确一致。原始clock只保留字节和来源追溯，不把其原始schema当成归一化时钟，也不重新标注或转换参考。

原训练参考采用证明中的`first_human_read_proof.path/sha256`指向已导出的NPY，必须等于`label_ref`，并核原source及读取stage。`original_mat_sha256`是不同原始MAT的历史身份，保留完整证明ref/status/old_protocol_sha256，不与NPY哈希比较，也不声称本轮重读或重新导出MAT。

### 外部来源用途声明

执行Agent先核原33来源登记的实际数据来源、研究训练/评价使用依据、完整评审摘要membership含义与历史曝光。用已有许可/来源证据文件的真实path/SHA登记 `$AIC_RUN/rights.private.json`：

```json
{
  "schema": "AIC_NATIVE_PREFERENCE_RIGHTS_V1",
  "source_registration_sha256": "采用的原33来源登记的真实SHA256",
  "local_research_training_and_evaluation_allowed": true,
  "historical_exposure_acknowledged": true,
  "summary_selection_not_exhaustive_highlight_labels": true,
  "basis_refs": [
    {"path": "/home/inspur/aic_video_work/实际已有来源或使用依据文件", "sha256": "该文件真实SHA256", "bytes": 0}
  ]
}
```

这是schema示意，字符串和0不是可运行资产，不能照抄当证据。若用途、原参考完整性或来源依据未确认，记录缺项并停止，不编造声明。此步骤使用既有文件，不要求新增人工标注。未纳入某个评审摘要仅代表该评审的选择，不能改称客观“无高光”。

### 建立本轮私有manifest

```bash
"$AIC_PY" -B "$AIC_CODE/assets.py" \
  --workspace-root "$AIC_WORK" \
  --code-root "$AIC_CODE" \
  --rights-declaration "$AIC_RUN/rights.private.json" \
  --output "$AIC_ASSETS"
```

主要内存接口：

- `model_spec`：现有model_dir、revision、canonical base SHA、原TIME权重与配置ref。完整model_files同时绑定逻辑文件名和解析后的文件字节，支持工作区内已有HF blob symlink。
- `input_code`：实际旧summary_contract、summary_grammar6、codec、dictionary的ref。
- `source_registration_ref`：原33来源身份与用途声明绑定；`normalized_supervision_registration_ref`和`original_human_label_adoption_ref`分别保留完整NPZ登记与原作者训练参考证明。
- `reference_generation_origin`：bootstrap默认绑定上表原43控制的completion和first QA。真实运行缺少该项会在模型加载前停止；核原输出/token文件、模型/输入/时钟、当前tokenizer/grammar及原生集合后明确标记历史采用，不能说成新生成。
- `scopes.train/check`：完整source catalog、request refs、原生clock refs、retained patches、来源SHA、归一化监督ref，以及原始clock/native/labels或reference refs。
- `source_supervision(sid)`：`baseline[native]` 与 `labels[native,reviewer]` 的原NPZ，转换成全部原评审的完整原生帧集合。显式known列保留UNKNOWN；不声明的known列拒绝，不填成零。
- `NativeInputStore.case(uid)`：request、四个CPU张量、完整clock；重建并核实际两视图plan和四张量shape/dtype/字节SHA。只保留当前来源patch缓存，不缓存整个训练集。
- `renderer`：只在生产manifest中登记。正式来源不提供supervision接口，源SHA不得与train/check重合。

模型、媒体、参考、前缀和像素文件保持在Linux，禁止把这些私有manifest/报告推回公开GitHub。

## 3. CPU检查、资产preflight和配对准备

先跑本次合成检查，以及当前Linux已安装环境中的**真实Torch CPU检查**。后者不加载Qwen、不分配CUDA、不下载任何东西：

```bash
"$AIC_PY" -B "$AIC_CODE/check_cpu.py" --output "$AIC_RUN/linux_synthetic_cpu.json"
"$AIC_PY" -B -m improvement.native_preference_v1.torch_checks \
  --output "$AIC_RUN/torch_cpu_checks.json"

timeout --signal=TERM --kill-after=30s 1800s \
  "$AIC_PY" -B "$AIC_ENTRY" --stage preflight \
  --config "$AIC_CONFIG" --assets "$AIC_ASSETS" \
  --output "$AIC_RUN/preflight.json"

timeout --signal=TERM --kill-after=30s 1800s \
  "$AIC_PY" -B "$AIC_ENTRY" --stage prepare \
  --config "$AIC_CONFIG" --assets "$AIC_ASSETS"
```

本地开发环境的Torch命令实际为NOT_RUN/退出77，不是PASS。Linux必须得到 `schema=AIC_NATIVE_PREFERENCE_TORCH_CPU_CHECKS_V1,status=PASS,torch_passed=true,torch_checks>=5`；报告绑定实际runtime/检查代码SHA。没有Torch或检查失败就停，不能自行安装/切换另一套环境来沿用旧gate。

preflight及每个stage都会读取并hash现有模型、原TIME/head、媒体/参考、patch及代码；**这里有实质磁盘读成本**。CPU准备还读取实际缓存张量并使用原本地tokenizer，因此不等于“只读几个JSON”。stage的时间预算从全资产核验前开始，不隐藏这段成本。

准备阶段先落 `prepare/source_plan.json`，再算效用。固定8训练来源每源4对、8开发来源每源2对；每源最多128个预先哈希排序的seed机会。每个seed只有一次反射，不能在失败后换源、增加偏移、放宽token/段数或重新扫描。全开发来源的原43窗仍完整用于自由生成，不只评价产出配对的窗。

准备成功产出 `prepare/prepared.json`（32train+16check配对及全部check窗）、`pair_diagnostics.json`、逐源接受/拒绝和实际窗口/评审分布。任何固定来源不足配额则写failure并停止，不能进入GPU。

## 4. 首个GPU小试：共享wrapper，执行预算1小时

仅使用既有共享GPU执行wrapper。它采用原resource_policy、gpu.lock、ledger及活动任务登记；本提交不改这些文件，不结束别人的任务，不从Mac启动。原wrapper继承环境，不替调用者设置GPU可见性；下面仅对这两个任务显式采用原登记的GPU 0，仍须通过共享容量/锁检查。裸运行 `run.py --stage pilot` 的进程内检查只能在检查点停止，不能代替wrapper硬墙钟控制。

```bash
CUDA_VISIBLE_DEVICES=0 "$AIC_PY" "$AIC_GPU_WRAPPER" \
  --name native_preference_20261019_v1_pilot \
  --max-seconds 3600 \
  --planned-output-bytes 1073741824 \
  --capacity-reason "Fixed 32-pair original-TIME-reference DPO pilot; one final adapter; no automatic production" \
  --queue-seconds 0 \
  -- "$AIC_PY" -B "$AIC_ENTRY" --stage pilot \
  --config "$AIC_CONFIG" --assets "$AIC_ASSETS" \
  --prepared "$AIC_RUN/prepare/prepared.json" \
  --torch-checks "$AIC_RUN/torch_cpu_checks.json"
```

如果GPU当前不能被准入，就记录wrapper原始结果，不能绕过锁或用另一个launcher抢占。硬终止可能来不及落failure；有claim但没有完整completion也一律视为未完成，绝不补空输出。

3600/7200秒是执行终止阈值。原wrapper每10秒轮询，超限后还需SIGTERM等待及必要的SIGKILL清理；wrapper返回时间与charged_seconds可能略高，不能宣称总返回墙钟严格不超阈值。配置预算若收紧，外层对应timeout/wrapper参数也同步收紧。

### 固定调用、训练、时间和磁盘预算

| 工作 | 固定数量/上限 | 真正被计数的内容 |
| --- | ---: | --- |
| CPU来源机会 | ≤16×128=2048个seed机会 | 构造一次反射、完整来源效用、实际token/grammar检查；0个Qwen调用 |
| Reference teacher-forced | 48对×2=96前向 | 原TIME、包含EOS的整答案sum log probability |
| 初始化检查 | 2前向 | 第一固定训练对，在288矩阵bitexact之外核margin约0/loss约log2 |
| DPO训练 | 32对×4=128前向，64 backward | 同theta两次无梯度评分、分支分别重算反传；非“32次调用” |
| 优化更新 | 16次，grad_accum=2 | AdamW lr1e-5、β0.1、weight decay0、clip1、dropout0；32对只过1遍 |
| Final check teacher-forced | 16对×2=32前向 | final存盘并重载后的真实候选排序 |
| **完整teacher-forced合计** | **258前向** | completion同时核发起/完成计数 |
| 自由生成 | 历史43控制采用＋新policy43次generate | 零重复原TIME生成；final重载后生成43次；每次≤512 tokens；仅合成单测保留模拟86路径 |
| pilot顶层forward保护 | ≤66000 | 最多64窗时2×64×512+258=65794；含逐token模型调用，不含层级checkpoint内部重算 |
| pilot执行预算 | 3600秒终止阈值 | 全部preflight、模型载入、原参考、训练、两角色生成、存盘重载和最终hash均计入；另记录原wrapper清理时间 |
| prepare / CPU review | 各≤1800秒 | 外层timeout与进程内检查；实机成本未测 |
| 正式推理，仅新admission后 | ≤426来源、≤600窗、7200秒执行阈值 | 现有登记522窗；最多307200顶层forward；0训练/0reference评分；另记录清理时间 |
| 新输出总磁盘 | 整个run_root≤1GiB | final权重约61.4MB十进制，另有tokens/配对/日志/报告/1包；不复制大模型或全量输入 |

日志分别给出逻辑generation次数、完整suffix评分次数、native.model顶层forward、backward、update。gradient checkpointing的层内重算是额外实际计算，不能据顶层计数宣称总FLOPs。报告同时保留墙钟、实际观察磁盘字节以及CUDA峰值；这些在真实Linux运行前均未知。

实际模型口径保守计整个继承依赖：BASE 8,767,123,696 + 原TIME 15,335,424 + 新policy 15,335,424 + semantic head 98,329 = **8,797,892,873≤9B**。旧40.47管线是8,782,557,449；不能把旧分母当新候选分母。每次模型载入实际清点，原TIME/base字节不得改变。

每个生成调用先把实际tokens/raw text写events，再核EOS、grammar和原生选择。成功的 `segments=[]` 可以形成空选择；异常、缺窗、截断、错误身份各自留下FAILED或未完成claim，禁止变成空。唯一final只有训练完整16步后才能保存；重载必须保持全部288张FP32矩阵字节。

### 预期产物，不代表现在已经存在

`pilot/` 成功应有 `fixed_reference.json`、`training.json`、`final_adapter/`、`final_adapter_identity.json`、`heldout_pair_scores.json`、两角色逐窗JSON、`generation_manifest.json`、`final_verification.json`、`events.jsonl` 和 `completion.json`。完成状态只能是 `COMPLETE_PILOT_NOT_ADMITTED`。

先检查第一小时内的真实配对准入、原TIME身份、初始化概率、首次梯度、严格只更新LoRA与完整计数。1小时能否完成全流程是待测问题，不是已承诺吞吐。超时、显存不足、数值不一致或配对不足都停止，不自动追加20小时训练。

## 5. 独立CPU终评：判定机制是否值得生产

```bash
timeout --signal=TERM --kill-after=30s 1800s \
  "$AIC_PY" -B "$AIC_ENTRY" --stage review \
  --config "$AIC_CONFIG" --assets "$AIC_ASSETS" \
  --prepared "$AIC_RUN/prepare/prepared.json" \
  --pilot "$AIC_RUN/pilot/completion.json"
```

review从原始逐窗答案独立重解析、用精确原生PTS求完整来源并集，核来源/输入/时钟/EOS身份；以完整评审参考算source-macro F1/P/R和逐来源增删帧。外部baseline是登记NPZ的40.47完整选择代理，不是官方测试标注，也不重建保护包。

以下任一成立，`review.json` 为 `STOP_MECHANISM`，命令退出3：

1. 实际新生成选择与原TIME完全相同。
2. 每个模型自身的raw chosen/rejected log probability排序准确率没有source-macro改善。
3. 完整来源自由生成F1没有同时超过原TIME和40.47外部代理。
4. 有非空参考且两个基线均非空的来源，被新policy变成全空。

任何输入/执行/身份错误则是失败，不能用代理分绕过。通过时仅为 `ELIGIBLE_FOR_EXECUTION_REVIEW`；没有 `approved=true`，没有自动生产。

执行Agent必须检查逐源及逐窗真实选择、配对分布、增加/删除位置和空输出、全量身份、实际预算；候选概率改善但生成不变不合格。可读取既有证据和执行日志，不新增官方人工标注或用官网总分搜索规则。历史8源已曝光，空间联合效果仍UNKNOWN。若收益只来自极少来源/反射位置偏差而无法解释，应停止并报告；不自动追加对照臂或调参。

## 6. 只有独立评审通过才准备正式资产与admission

原pilot manifest不能原地加入426来源。另写正式manifest，采用同样的train/check、模型/代码/保护依赖，同时增加正式scope和renderer：

```bash
"$AIC_PY" -B "$AIC_CODE/assets.py" \
  --workspace-root "$AIC_WORK" --code-root "$AIC_CODE" \
  --rights-declaration "$AIC_RUN/rights.private.json" \
  --production-registration five_summary_sprint_20261019_v41/input_registration41.json \
  --production-acceptance five_summary_sprint_20261019_v41/formal_inputs_41/input_acceptance.json \
  --package-inputs twenty_hour_five_20261014_v1/temporal_family_native_package_v3/package_inputs.json \
  --output "$AIC_FORMAL_ASSETS"
```

下面的CPU脚本只产生 `approved:false` 草稿，**不会准入或执行生产**，路径和SHA均来自本次明确文件：

```bash
"$AIC_PY" -B - <<'PY'
import os
from pathlib import Path
from improvement.native_preference_v1.contracts import reference, save_new, strict_load
r = Path(os.environ["AIC_RUN"])
pilot = strict_load(r / "pilot/completion.json")
review = strict_load(r / "review/review.json")
assert review["status"] == "ELIGIBLE_FOR_EXECUTION_REVIEW"
refs = dict(config_ref=reference(os.environ["AIC_CONFIG"]),
    asset_manifest_ref=reference(os.environ["AIC_ASSETS"]),
    production_assets_ref=reference(os.environ["AIC_FORMAL_ASSETS"]),
    prepared_ref=reference(r / "prepare/prepared.json"),
    pilot_completion_ref=reference(r / "pilot/completion.json"),
    review_ref=reference(r / "review/review.json"),
    final_adapter_ref=pilot["final_adapter_ref"])
save_new(r / "production_admission.draft.json", dict(
    schema="AIC_NATIVE_PREFERENCE_ADMISSION_V1", action="production",
    approved=False, reviewed_by="", reviewed_at=None, review_notes="", **refs))
PY
```

执行Agent完成独立评审后，另存 `production_admission.json`，保留所有ref不变并填 `approved:true`、实际reviewed_by、含时区的真实reviewed_at及具体review_notes。如评审不通过，保存否决原因，终止这个机制。不要把“gate通过”直接改写成“已证明可提分”。代码会再核全部ref、complete和eligibility，正式加载后的Torch/transformers/peft/safetensors等运行身份也必须与pilot完全相同。

## 7. 显式正式推理，然后再单独封包

```bash
CUDA_VISIBLE_DEVICES=0 "$AIC_PY" "$AIC_GPU_WRAPPER" \
  --name native_preference_20261019_v1_production \
  --max-seconds 7200 \
  --planned-output-bytes 1073741824 \
  --capacity-reason "Separately reviewed final policy; one formal candidate; no training or automatic packaging" \
  --queue-seconds 0 \
  -- "$AIC_PY" -B "$AIC_ENTRY" --stage production \
  --config "$AIC_CONFIG" --assets "$AIC_ASSETS" \
  --production-assets "$AIC_FORMAL_ASSETS" \
  --prepared "$AIC_RUN/prepare/prepared.json" \
  --pilot "$AIC_RUN/pilot/completion.json" \
  --review "$AIC_RUN/review/review.json" \
  --torch-checks "$AIC_RUN/torch_cpu_checks.json" \
  --admission "$AIC_RUN/production_admission.json"
```

成功生成 `production/selection.json`、实际逐窗输出与 `completion.json`，状态为 `COMPLETE_PRODUCTION_NOT_PACKAGED`。原始选择含426个source，每个必须 `status=ACCEPTED` 且有排序去重的selected_ordinals，合法空是显式空列表；任何缺源或失败都不能封包。

执行Agent核验正式完整性/预算/选择及原包未变，再建立第二份包级草稿：

```bash
"$AIC_PY" -B - <<'PY'
import os
from pathlib import Path
from improvement.native_preference_v1.contracts import reference, save_new, strict_load
r = Path(os.environ["AIC_RUN"])
done = strict_load(r / "production/completion.json")
assert done["status"] == "COMPLETE_PRODUCTION_NOT_PACKAGED"
save_new(r / "package_admission.draft.json", dict(
    schema="AIC_NATIVE_PREFERENCE_ADMISSION_V1", action="package",
    approved=False, reviewed_by="", reviewed_at=None, review_notes="",
    config_ref=done["config_ref"], asset_manifest_ref=done["asset_manifest_ref"],
    production_assets_ref=done["production_assets_ref"],
    production_completion_ref=reference(r / "production/completion.json"),
    selection_ref=done["selection_ref"]))
PY
```

独立完成包级评审后另存 `package_admission.json`，填写实际四个评审字段，再执行：

```bash
timeout --signal=TERM --kill-after=30s 1800s \
  "$AIC_PY" -B "$AIC_ENTRY" --stage package \
  --config "$AIC_CONFIG" --assets "$AIC_ASSETS" \
  --production-assets "$AIC_FORMAL_ASSETS" \
  --production "$AIC_RUN/production/completion.json" \
  --admission "$AIC_RUN/package_admission.json"
```

封包先与旧冻结field逐来源、逐原生PTS、physical endpoint核同源。**只要新时间选择有一个原生帧不在空间可用域，写 `field_eligibility.json` 并停止，不能偷偷取交集后交包。** 外部check没有等价空间场，这个STOP保护实际被评价的时间方案。

无域外排除才沿真实hash绑定的field_contract、package_contract、p2j_core、pts_contract、a_contract及strict loader闭包渲染。保留旧source ID、targetRatioWH及已有重叠帧的框；合法空不补一帧。只有原11项独立strict检查、ZIP单成员/CRC/SHA、完整426条都实际通过，才把PENDING包改为：

```text
native_preference_20261019_v1/package/rendered/candidate_NATIVE_PREFERENCE.zip
```

相同规范预测仅改名与40.47重复时停止。成功回执为 `package/rendered/package_receipt.json`，只说明工程接受、官方效果UNKNOWN。没有官网API或自动上传命令；本机制最多交1个候选，不按剩余额度拼5包。

## 8. 回传什么，何时结束本轮

向制定方案的Agent回传：实际commit及代码SHA、CPU/Torch结果、资产与配对准入、精确参数/前向/backward/更新计数、每个阶段秒数/磁盘/显存、完整逐源及macro结果、合法空与失败数、原TIME和40.47比较、停止理由；若生产，再加426完整性、空间域排除、11项strict及ZIP SHA。分享脱敏摘要；私有媒体、标签、模型和manifest不进入Git。

没有运行的步骤明确标记NOT_RUN。工程PASS、外部代理变化、用户反馈的官网分数分开记录。如果小试或封包停止，本轮就在该停止点结束；不续训、不换名复刻已失败的SFT/融合，也不暗中消耗其余训练时段。

按2026-10-19核查的[官方赛题](https://www.aicomp.cn/tracks/tracks-6/4267.html)与[复赛通知/0930附件](https://www.aicomp.cn/notice/notice-3/5307.html)：实际主辅模型总参数≤9B；官方测试数据不得上传闭源服务、人工补标/改结果、用于训练或反构规则。每日5次为上限，保留最高有效分；提交截止10月23日20:00、材料截止10月25日23:59。正式操作前核平台采用的中国赛事时区和页面变化；若现行规则变化，先停止执行并更新方案，不能把旧通知视为永远有效。
