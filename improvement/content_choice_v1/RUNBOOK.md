# 执行手册：content_choice_v1 三个独立候选

本文件是交给当前执行 Agent 的**下一轮代码协议**。新候选的真实 Linux 资产验收、Qwen 调用、critic 拟合、代理质量、426 来源生产和正式 ZIP **均未运行**。本地实际结果见 [CPU_NOTES.md](CPU_NOTES.md)；合成 CPU 与真实 Torch gate、工程完成与机制质量、时间摘要代理与官方时空联合分分别报告。

从 `f343a92da467b0e9f4c2677bd2ab75ff88a09df7` 新建的实施分支保留 PR #1、PR #2 和原 DPO 的全部修复与 STOP。根目录旧 NEXT_PLAN/RUNBOOK 是上轮固定 DPO 协议，不能用于启动这轮多候选。

## 1. 入口、执行顺序与依赖

先读 [PLAN.md](PLAN.md) 和 [RESEARCH.md](RESEARCH.md)。推荐顺序：

1. 核精确交付 SHA、现行规则、既有外部数据用途和原包；运行新合成 CPU、真实 Torch CPU、资产 preflight、plan。
2. 只读已完成 DPO 的 16 对绝对概率诊断；不重跑旧 DPO 或 43 个原控制。
3. 新 `collect --partition check`：43 个旧 TIME 控制显式采用，仅生成 86 个固定采样回答；计算四候选的真实/时序移位评分和特征。随后先运行 `review --candidate contrast`，得到同池 raw、contrast、oracle、regret 和完整 8 源结果。该 review 即使科学 STOP，已完成 collection 仍可用于其他独立候选。
4. 先检查固定池是否有超过原 TIME/40.47 代理的 oracle 空间、8 源非平局排序覆盖是否完整。若固定池没有可达空间，停止 critic 的额外 train 采集；不增加采样次数。**oracle 是用外部参考算出的诊断上界，不能作为真实候选或正式选择器。**
5. 主要训练候选是 `critic`：仅在上述诊断值得继续时采集全部 25 个 SumMe/144 窗，拟合 131 权重与两个对照，并做 25 源 LOSO＋全部 8 源跨数据集评价。
6. `observation` 是独立输入机制，最多再产生 43 个原 TIME greedy 回答；预算紧时可在 train 采集之前完成这个较小试验。它不使用 critic 的候选、权重或生成结果。
7. 各候选只在自己的冻结条件通过后，由执行 Agent 独立审查，再决定是否执行该候选的 426 来源生产。不要把三个生产命令串成默认任务。

所有模型路径沿用既有原 BASE/TIME；没有 pip install、模型下载、媒体解码或新服务配置步骤。Linux 仍使用已运行成功的 `qwen3vl_isolated_20260910` 环境；NumPy 执行实际 ridge，Torch/Transformers/PEFT/Safetensors 执行既有 Qwen 接口。缺件或版本不同会明确报错，不自动切换环境。首次加载真实新调用路径仍可能暴露接口或显存问题，必须保留失败再修工程，不能据此改科学门。

| 候选 | 实际新训练 | 复用 | 新推理 | 空间变化 |
| --- | --- | --- | --- | --- |
| `critic` | NumPy 闭式 pairwise ridge；131 个部署权重；没有 Qwen backward | 原 BASE/TIME、原双视图、43/522 原 greedy、共同候选评分缓存 | 固定两次 sample/window；TF 取真实 before-EOS 状态 | 原 field/composer；同帧原框不变，新帧只在已存在 field 定义域内 |
| `contrast` | 无 | 同一四候选池及 TF；不采用 DPO final | 真实条件与固定组移位条件的完整 suffix 评分 | 同上 |
| `observation` | 无 | 原缓存真实帧、原 TIME；输入无变化时采用旧 greedy | 只对实际改变输入的窗口 greedy | 同上 |

## 2. 精确代码部署与运行变量

以下只设置接口，不会启动 GPU。把交付消息的完整 SHA 赋给 `AIC_IMPLEMENTATION_SHA`，不能用移动的 main、PR head 或“最新 vN”替代。已有同名 checkout 必须先核状态；不要覆盖正在运行的目录。

```bash
export AIC_WORK=/home/inspur/aic_video_work
export AIC_REPO="$AIC_WORK/code/AIC-shipin-content-choice"
export AIC_IMPLEMENTATION_SHA='替换为本次交付的完整commit_SHA'
export AIC_PY="$AIC_WORK/env/qwen3vl_isolated_20260910/bin/python"
export AIC_RUN="$AIC_WORK/content_choice_20261019_v1"
export AIC_CODE="$AIC_REPO/improvement/content_choice_v1"
export AIC_ENTRY="$AIC_CODE/run.py"
export AIC_CONFIG="$AIC_RUN/config.json"
export AIC_GPU_WRAPPER="$AIC_WORK/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/resource_unlimited_v1_20261007/gpu_run.py"
export AIC_OLD_ASSETS="$AIC_WORK/native_preference_20261019_v1/assets.private.json"
export AIC_DPO_COMPLETE="$AIC_WORK/native_preference_20261019_v1/pilot/completion.json"
export AIC_DPO_REVIEW="$AIC_WORK/native_preference_20261019_v1/review/review.json"
export AIC_FORMAL_ASSETS="$AIC_RUN/production_assets.private.json"
export AIC_FORMAL_QA="$AIC_WORK/five_summary_sprint_20261019_v41/first_independent_output_QA41.json"
```

`AIC_OLD_ASSETS/AIC_DPO_COMPLETE/AIC_DPO_REVIEW` 是上轮 RUNBOOK 的明确默认位置，不是本代理在 Linux 验证过的路径。执行 Agent 应用自己保留的真实完成回执核对；若实际采用位置不同，只能显式提供该确切文件，不能自动搜索最新目录。`diagnose-dpo` 要求实际 258/64/16/43 和对应 STOP；输入错误会停止。

容量允许时，可在独立目录按精确 SHA 检出：

```bash
git clone --filter=blob:none --no-checkout --single-branch \
  --branch implementation/20261019-multi-candidate-rd \
  https://github.com/zb581899564-arch/AIC-shipin.git "$AIC_REPO"
git -C "$AIC_REPO" checkout --detach "$AIC_IMPLEMENTATION_SHA"
git -C "$AIC_REPO" merge-base --is-ancestor f343a92da467b0e9f4c2677bd2ab75ff88a09df7 HEAD
test "$(git -C "$AIC_REPO" rev-parse HEAD)" = "$AIC_IMPLEMENTATION_SHA"
```

容量紧时，在审查机的这个精确 Git checkout 生成仅代码交付。`code_manifest.json` 的 `files` 是本目录所有 Python 和配置，`dependencies` 是 repo 相对路径的冻结继承代码/测试依赖；按二者列出的成员保持相对路径传输，再携带本目录 Markdown 与两份清单即可。**config.example.json 和继承 native_preference_v1 的 config/code_manifest 不得漏带**。不把整历史仓库、保护 ZIP、模型或媒体再复制到 Linux。代码目录完整后，不论采用哪种部署，均执行以下公共初始化并核代码成员。`AIC_RUN` 已存在时先核原 claim/状态，不能覆盖。下面的 `code_identity()` 和新 CPU 检查会核每个成员，缺一个即停：

```bash
mkdir "$AIC_RUN"
cp --no-clobber "$AIC_CODE/config.example.json" "$AIC_CONFIG"
cd "$AIC_REPO"
"$AIC_PY" -B - <<'PY'
from improvement.content_choice_v1.contracts import code_identity
print(code_identity())
PY
```

小量部署目录没有 Git 元数据时，另保留审查机 `git rev-parse HEAD` 的回执和传输成员 SHA；不能在非 Git 目录伪造 checkout 成功。`run.py`、`admission.py`、`check_cpu.py` 支持绝对脚本路径；原 GPU wrapper 改 cwd/PYTHONPATH 后，`run.py` 仍导入本次独立 checkout。Torch 门按下文从仓库根用 `-m improvement.content_choice_v1.torch_checks` 运行，不能把它当独立脚本路径调用。

## 3. 采用资产，保护原包和完整历史

优先**只读复用已经完成 DPO 的私有 assets manifest**，即 `--assets "$AIC_OLD_ASSETS"`。本轮配置与运行目录独立，资产 manifest 不加入新结果、critic 权重、DPO final 或正式测试标签。旧 manifest 的 `code_root/code_refs` 仍绑定其原 native_preference Python 部署；本轮新代码另由新 `code_manifest` 绑定，不能把旧 code_root 改指 content_choice_v1。

以下成功资产链已由仓库代码/回执确认其接口，但私有文件存在与 SHA 要在 Linux preflight 核验：

| 数据/模型接口 | 精确历史入口（相对 AIC_WORK） | 本轮用途 |
| --- | --- | --- |
| 外部 25 源/144 窗训练输入 | `bottleneck_24h_20261019_v1/summary_CPU_registration_05.json`；`summary_inputs_05/input_acceptance.json` | 全部 25 SumMe；新 critic 监督/LOSO，采集时不读目标值 |
| 外部 8 源/43 窗输入 | `bottleneck_24h_20261019_v1/summary_dev_CPU_registration_09.json`；`summary_dev_inputs_09/input_acceptance.json` | 全部历史 VideoXum；不使用失败 07 |
| 原始来源身份 | `source_clear_residual_20261018_v1/registration.json` | SHA、来源/用途/原参考；不能冒充归一化 NPZ 登记 |
| 归一化完整监督 | `meaningful_residual_20261018_v1/registration.json` | 完整 native clock、40.47 外部选择、全部评审摘要 membership；未知位不补零 |
| 原 MAT/导出 NPY 证明 | `source_clear_residual_20261018_v1/original_human_label_adoption.json` | 分别绑定原 MAT 历史身份及现有导出证明，不比较两个不同格式的哈希 |
| BASE/TIME/双视图 helper | `bottleneck_24h_20261019_v1/summary_generation_registration_10.json` | 原权重、model_config、成功 09 输入和既有字典/patch；不用 SFT/DPO final |
| 原 43 个 TIME 控制 | `bottleneck_24h_20261019_v1/summary_generation_10/INIT_TIME/completion.json` 与 `first_independent_output_QA.json` | 当前 tokenizer、grammar、native 选择重新核身份后采用，0 次重复模型生成 |
| 正式 426/522 输入 | `five_summary_sprint_20261019_v41/input_registration41.json`；`formal_inputs_41/input_acceptance.json` | 仅独立生产审查后采用；官方 scope 没有 supervision 接口 |
| 原正式 TIME 控制 | `five_summary_sprint_20261019_v41/first_independent_output_QA41.json` | 跟踪其中 TIME role 的 522 个成功 raw；BASE 与停止的五包不是新候选 |
| 冻结空间接口 | `twenty_hour_five_20261014_v1/temporal_family_native_package_v3/package_inputs.json` | 原 field、PTS、composer、独立严格 11 项验证器 |
| 保护包 | `semantic_context_production_20261016_v1/package/candidate_CONTEXT_SEMANTIC_RESIDUAL.zip` | 只读，384630 字节；SHA 见下 |

```text
b37c4a2e6593fc800f54ecce2f860fee5e7d5dc74e17ce280f9ee6722afbccd3
```

首次 preflight 会核原 manifest 的全部引用、模型目录闭合字节、权重/媒体/参考/patch/代码、来源分组和登记链，有真实磁盘读取成本。`source_supervision(sid)` 只在 train/check 读既有 NPZ 的人类摘要与显式 known masks；官方数据不能进入拟合、特征标准化、标签、人工挑选或伪标签。原作者未选不是客观“普通帧”标签。

保留既有的 `rights_declaration_ref/basis_refs` 并核其使用范围涵盖当前的本地外部研究训练/评价。不能用模板文字代替实际依据。若复用 manifest 不满足接口，先保存具体差异；仅在明确的现有来源证据支持下，用**未改动的**旧 assets.py 在本轮目录生成新 manifest，并让本轮所有 stage 始终绑定它；不能覆盖旧 manifest 或在中途换 manifest。

## 4. 必要 CPU 门与明确计划

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  "$AIC_PY" -B "$AIC_CODE/check_cpu.py" --output "$AIC_RUN/linux_synthetic_cpu.json"

"$AIC_PY" -B -m improvement.content_choice_v1.torch_checks \
  --output "$AIC_RUN/torch_cpu_checks.json"

timeout --signal=TERM --kill-after=30s 1800s \
  "$AIC_PY" -B "$AIC_ENTRY" --stage preflight \
  --config "$AIC_CONFIG" --assets "$AIC_OLD_ASSETS"

timeout --signal=TERM --kill-after=30s 1800s \
  "$AIC_PY" -B "$AIC_ENTRY" --stage plan \
  --config "$AIC_CONFIG" --assets "$AIC_OLD_ASSETS"

timeout --signal=TERM --kill-after=30s 1800s \
  "$AIC_PY" -B "$AIC_ENTRY" --stage diagnose-dpo \
  --config "$AIC_CONFIG" --assets "$AIC_OLD_ASSETS" \
  --dpo-completion "$AIC_DPO_COMPLETE" --dpo-review "$AIC_DPO_REVIEW"
```

Torch gate 必须是**这个代码版本的** `AIC_CONTENT_CHOICE_TORCH_CPU_CHECKS_V1/PASS`，30 项 pure 加 13 项真实 CPU Torch，0 skip/0 fail，同一 Torch distribution；代码绑定包含新 runtime、observation、verification 及继承依赖。这里没有 Torch 的本地结果是 **NOT_RUN/退出 77**，旧 DPO 的 11 项 Torch PASS 不能直接当新 gate。真实 Torch 门只创建小合成 CPU 张量，不加载 Qwen/CUDA。

`plan/plan.json` 固定所有 25/144＋8/43 来源、源 SHA、原生窗口和引用；不读目标数值、不自选新来源。`diagnose_dpo/diagnostic.json` 只从已完成原试验读绝对 logp、raw margin、相对差、共同前缀长度与原停止原因，0 新模型调用；不会把原 STOP 改成功。

每阶段有排他 `claim.json`。目录已存在、无 complete、失败或硬超时都保留，禁止删除 claim 重试、覆盖 raw 或将缺失输出补空。科学 `STOP_MECHANISM` 退出 3；执行错误写 `failure.json` 并非零退出。外层硬终止来不及写 failure 时，未完成 claim 也不能采用。

## 5. 共同开发候选采集＋contrast 的第一轮判定

GPU 只能由当前执行 Agent 使用原共享 wrapper 及资源策略/锁/唯一 ledger。下面命令是**一次显式阶段**；本轮编写代码的代理未执行它们。

```bash
CUDA_VISIBLE_DEVICES=0 "$AIC_PY" "$AIC_GPU_WRAPPER" \
  --name content_choice_20261019_v1_collect_check --max-seconds 3600 \
  --planned-output-bytes 1073741824 \
  --capacity-reason "Fixed external8 source pool; adopt43 TIME controls; sample86; no production" \
  --queue-seconds 0 \
  -- "$AIC_PY" -B "$AIC_ENTRY" --stage collect --partition check \
  --config "$AIC_CONFIG" --assets "$AIC_OLD_ASSETS" \
  --plan "$AIC_RUN/plan/plan.json" --torch-checks "$AIC_RUN/torch_cpu_checks.json"

timeout --signal=TERM --kill-after=30s 1800s \
  "$AIC_PY" -B "$AIC_ENTRY" --stage review --candidate contrast \
  --config "$AIC_CONFIG" --assets "$AIC_OLD_ASSETS" \
  --plan "$AIC_RUN/plan/plan.json" --collect-check "$AIC_RUN/collect_check/completion.json"
```

最多 86 新 generate、344 TF；静态反事实若四张量字节完全相同，显式复用真实 TF；同一输入内完全相同 suffix 也复用。原生集合相同但 token 不同不能假称概率/feature 相同。逐窗记录 raw、EOS/grammar、input signature、候选、准确 cache alias 与实际 counts；实际原 BASE/288 TIME 矩阵零变化后才能 complete。

`review_contrast/review.json` 给出原 TIME、40.47 外部代理、同池 raw mean logp、contrast 的完整来源 F1/P/R、逐源增删、所选 slot、oracle/regret、非平局效用对排序与覆盖。先读这个报告，再决定是否值得支付 train 采集。A 科学 STOP 不等于 collection 执行失败，也不自动否定 critic；但池本身上限无空间或所有源排序覆盖门不可达时，停止这个固定池方向。

contrast 的门：实际选择有变化；跨源 F1 同时严格超过原 TIME 和保护代理；没有新增 false-empty source；同池 F1 与来源宏排序均严格超过 raw。概率条件差不等于效用，更不等于官方偏好；不能为过门扫描 shift、温度、slot 数或 token 归一化方式。

## 6. critic：只有候选空间值得继续时才采集训练来源

```bash
CUDA_VISIBLE_DEVICES=0 "$AIC_PY" "$AIC_GPU_WRAPPER" \
  --name content_choice_20261019_v1_collect_train --max-seconds 7200 \
  --planned-output-bytes 1073741824 \
  --capacity-reason "Fixed25 external source candidates and frozen state reads; zero Qwen training updates" \
  --queue-seconds 0 \
  -- "$AIC_PY" -B "$AIC_ENTRY" --stage collect --partition train \
  --config "$AIC_CONFIG" --assets "$AIC_OLD_ASSETS" \
  --plan "$AIC_RUN/plan/plan.json" --collect-check "$AIC_RUN/collect_check/completion.json" \
  --torch-checks "$AIC_RUN/torch_cpu_checks.json"

OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 \
  timeout --signal=TERM --kill-after=30s 1800s \
  "$AIC_PY" -B "$AIC_ENTRY" --stage fit \
  --config "$AIC_CONFIG" --assets "$AIC_OLD_ASSETS" \
  --plan "$AIC_RUN/plan/plan.json" --collect-train "$AIC_RUN/collect_train/completion.json"

timeout --signal=TERM --kill-after=30s 1800s \
  "$AIC_PY" -B "$AIC_ENTRY" --stage review --candidate critic \
  --config "$AIC_CONFIG" --assets "$AIC_OLD_ASSETS" \
  --plan "$AIC_RUN/plan/plan.json" --collect-check "$AIC_RUN/collect_check/completion.json" \
  --fit-run "$AIC_RUN/fit/completion.json"
```

全部 144 窗 greedy＋两个固定 sample 共 432 新生成；最多 1152 TF，同次 TF 既得全 suffix logp 又得预测 EOS 的 hidden，不为特征额外调用模型。25 来源先组成四个整源动作，再读全部评审参考并拟合；不在窗级独立挑选候选或用窗级 F1 求和。

`fit/critic_weights.json` 保存部署用 131 权重；`fit/completion.json` 保存 content、shape-only、permuted-hidden 三臂的最终头、全部 25 个独立留源折、标准化来源、求解残差、权重 SHA、OOF 真实选择和指标。固定 lambda=.01、无 epoch/lr/beta 扫描；3 个最终解＋75 个 LOSO 解，共 78 次 NumPy 线性求解。保存并重读后分数须完全一致。

critic 的门：跨数据集完整源 F1 严格超过原 TIME/保护代理；LOSO F1 超过原 TIME；跨数据集 F1 **以及来源宏候选排序**均超过 shape-only 和 permuted-hidden；LOSO 排序超过 shape-only；实际有非零改动，没有新增 false-empty source。排序比较要求全部来源都有非平局效用对；不通过不能改分母。最终 fit source SHA 与实际 train 完整匹配，train/check 不交叉，所有 collect/observation/production 的 runtime identity 与版本必须一致。

只有某几个历史来源上涨、对照不胜或增加 oracle 但不能选择出更好答案，都不足以宣称内容能力成立。25/8 源全有历史曝光；LOSO 只证明本次拟合留源隔离。

## 7. observation：独立输入机制

```bash
CUDA_VISIBLE_DEVICES=0 "$AIC_PY" "$AIC_GPU_WRAPPER" \
  --name content_choice_20261019_v1_observation --max-seconds 2700 \
  --planned-output-bytes 1073741824 \
  --capacity-reason "At most43 fixed-budget changed observations; original TIME greedy; no model training" \
  --queue-seconds 0 \
  -- "$AIC_PY" -B "$AIC_ENTRY" --stage observation \
  --config "$AIC_CONFIG" --assets "$AIC_OLD_ASSETS" \
  --plan "$AIC_RUN/plan/plan.json" --collect-check "$AIC_RUN/collect_check/completion.json" \
  --torch-checks "$AIC_RUN/torch_cpu_checks.json"

timeout --signal=TERM --kill-after=30s 1800s \
  "$AIC_PY" -B "$AIC_ENTRY" --stage review --candidate observation \
  --config "$AIC_CONFIG" --assets "$AIC_OLD_ASSETS" \
  --plan "$AIC_RUN/plan/plan.json" --collect-check "$AIC_RUN/collect_check/completion.json" \
  --observation-run "$AIC_RUN/observation/completion.json"
```

缓存帧的 12 维描述子每源计算一次；Overview/Excerpt 各自在原均匀 PTS 的固定时间分层内选取，同视觉 token 预算、首尾锁定，真实源 PTS 重建 prefix。新 prefix 保存后实际重载，重建全部四张量并核字节和原生 plan，才调用原 TIME。review/package 再从文件独立重读和重算。

若所选像素没有变化，撤回整份新时间计划、保留旧 prefix/输入并采用旧成功答案；`NO_EFFECT` 是明确没有实际输入干预，不是执行失败降级。不得把只改时间元数据却复用旧答案记成新推理。诊断保存 proposed/discarded plan、同预算证据、实际 changed_input_windows 和采用数量。

observation 的门：实际改变至少一个输入；完整源实际选择改变；F1 严格超过原 TIME/保护代理；没有新增 false-empty source。RGB 变化只是输入分配启发式，不是高光标签。若没有改善，结束这条固定观察规则，不改提示词、采样层、阈值后重称同一机制成功。

## 8. 调用、训练、时间、磁盘与参数预算

所有数字是**固定次数或最大执行预算，不是新候选已实测耗时/质量**。墙钟包括资产核验、模型装载、采用 QA、计算、保存/重载和最后冻结哈希；实际由原 wrapper ledger/resource 和本次 events/completion 对账。wrapper 超时轮询及终止清理会有额外返回延迟。

| 阶段 | 新 generate 上限 | TF 上限 | Qwen backward / 更新 | native.model 顶层 forward 上限 | 执行终止阈值 |
| --- | ---:| ---:| ---:| ---:| ---:|
| check 共用池 | 86；另采用旧43 | 344 | 0 / 0 | 44,376 | 3,600秒 |
| train 共用池 | 432 | 1,152 | 0 / 0 | 222,336 | 7,200秒 |
| critic fit＋75 LOSO 控制折 | 0 | 0 | 0 / 0 | 0；78次线性求解 | 1,800秒 CPU |
| observation check | ≤43；其余采用原回答 | 0 | 0 / 0 | 22,016 | 2,700秒 |
| contrast 426/522，仅独立准入后 | 1,044；另采用旧522 | 4,176 | 0 / 0 | 538,704 | 7,200秒 |
| critic 426/522，仅独立准入后 | 1,044；另采用旧522 | 2,088 | 0 / 0 | 536,616 | 7,200秒 |
| critic 显式复用已通过的 contrast 正式完整池 | 0；采用原池全部候选/特征 | 0 | 0 / 0 | 0；无新拟合 | 1,800秒 CPU |
| observation 426/522，仅独立准入后 | ≤522；其余采用原回答 | 0 | 0 / 0 | 267,264 | 7,200秒 |
| preflight/plan/diagnose/review/package | 0 | 0 | 0 / 0 | 0 | 各1,800秒 CPU |

每个生成最多 512 suffix tokens，TF 是整答案 SUM 且含 EOS。一次 generate 内有多次 top-level forward；不能把 generate 次数说成完整算力。精确相同 suffix/相同反事实输入可减少实际 TF；不得补抽直到达到预算数。critic 正式期不运行 permuted 对照；它在 pilot 已用于检验机制，正式只加载部署 content 权重。

共同开发/训练池合计最多 **518 新 generate＋1496 TF**；三个候选小试 GPU 执行上限合计 3.75 小时。优先让有限 pilot 解释问题；用户可用约20小时/日并不要求耗尽训练时间，更不要求每天凑5包。三路全部生产额外最多6小时，但这是理论预算加法，**不是默认执行计划，也不是承诺能跑完**。只优先生产有完整证据且独立审查通过的一路，保留真实异常修复、独立 QA 和复现时间。

整个新的 `run_root` 累计新输出上限 **1 GiB**，不是每 stage 1GiB；descriptor 只保留当前来源，流式复用现有 patches，不复制模型、不重解码媒体、不导出4096维大 tensor。131 个部署权重只有1048字节的float64数值，另有 JSON 元数据、候选131维特征、prefix、raw/events、折报告和获准的一份或多份候选包。实际磁盘峰值必须由回执测量；任何阶段超过限额停下，不删除原始失败/成功证据腾空间。

| 参数部分 | 元素数 | 依据 |
| --- | ---:| --- |
| 原 BASE | 8,767,123,696 | 原已核模型，载入后 canonical byte/numel 校验 |
| 原 TIME LoRA | 15,335,424 | 原288矩阵 FP32逐字节核验，不更新 |
| 继承语义头 | 98,329 | 保护管线依赖，不能因新阶段使用缓存而漏计 |
| 新 critic | 131 | 实际保存/重载部署的float64权重；无额外可学习bias/scale |
| `observation` / `contrast` 全管线 | **8,782,557,449** | 原完整依赖 |
| `critic` 全管线 | **8,782,557,580** | 原依赖＋131 |

固定 SHA signed-hash 投影没有拟合参数；执行计数器、代码常量不是新模型。shape-only/permuted 是外部对照，不部署；即便审计额外保守合计保存的对照/折小头，距离9B仍有明显余量，但技术报告应逐实际模型列明并按官方口径复核。实际驻留原 Qwen＋TIME 为8,782,459,120，不能拿驻留少计替代完整 pipeline。

## 9. 生产资产与候选独立审查

每路必须先有 `review_<candidate>/review.json = ELIGIBLE_FOR_EXECUTION_REVIEW`；只有工程 PASS 或高于较弱保护代理还不够。执行 Agent 审查候选逐源指标、shape/raw/permuted 控制、既有曝光、完整来源分母、实际参数/费用/冻结结果，才能另立该路生产审查记录。该文件记录执行 Agent 的具体决定，不要求再次询问用户通用代码修改授权。

如果上轮已存在完全同一资产链的生产 manifest，可显式采用并核其 SHA；没有则用旧 assets.py 的已修接口新建，**不启动旧 launcher**。以下读取原 manifest 的实际 rights/code_root，保持旧部署依赖：

```bash
"$AIC_PY" -B - <<'PY'
import os
from improvement.native_preference_v1.assets import read_json, bootstrap
old = read_json(os.environ['AIC_OLD_ASSETS'])
bootstrap(
    workspace_root=os.environ['AIC_WORK'], output=os.environ['AIC_FORMAL_ASSETS'],
    rights_declaration=old['rights_declaration_ref']['path'], code_root=old['code_root'],
    train_registration='bottleneck_24h_20261019_v1/summary_CPU_registration_05.json',
    train_acceptance='bottleneck_24h_20261019_v1/summary_inputs_05/input_acceptance.json',
    check_registration='bottleneck_24h_20261019_v1/summary_dev_CPU_registration_09.json',
    check_acceptance='bottleneck_24h_20261019_v1/summary_dev_inputs_09/input_acceptance.json',
    generation_registration='bottleneck_24h_20261019_v1/summary_generation_registration_10.json',
    protected_registration='semantic_context_production_20261016_v1/production_registration.json',
    protected_zip='semantic_context_production_20261016_v1/package/candidate_CONTEXT_SEMANTIC_RESIDUAL.zip',
    production_registration='five_summary_sprint_20261019_v41/input_registration41.json',
    production_acceptance='five_summary_sprint_20261019_v41/formal_inputs_41/input_acceptance.json',
    package_inputs='twenty_hour_five_20261014_v1/temporal_family_native_package_v3/package_inputs.json',
    reference_completion=old['reference_generation_origin']['completion_ref']['path'],
    reference_output_qa=old['reference_generation_origin']['first_output_qa_ref']['path'])
PY
```

生成审查草稿（以下以推荐的 critic 为例，另两路分别显式设其名字）：

```bash
export AIC_CANDIDATE=critic
"$AIC_PY" -B "$AIC_CODE/admission.py" --action production --candidate "$AIC_CANDIDATE" \
  --config "$AIC_CONFIG" --assets "$AIC_OLD_ASSETS" --production-assets "$AIC_FORMAL_ASSETS" \
  --review-run "$AIC_RUN/review_$AIC_CANDIDATE/review.json" --formal-qa "$AIC_FORMAL_QA" \
  --output "$AIC_RUN/production_$AIC_CANDIDATE.draft.json"
```

该工具只写 `approved:false`，不会执行生产。执行 Agent 审查后另存 `production_<candidate>.admission.json`：保留全部引用，填写真实 `reviewed_by`、带时区 `reviewed_at`、具体 `review_notes`，获准时 `approved:true`。不能给停止方案补一个批准文件绕过 `load_review()`；不能把一条候选的批准用于另一条。正式资产在模型加载前验证全部字节与原 pilot 依赖一致。

## 10. 一个候选的一次正式生成；随后独立封包

只有上一节该候选评审通过后：

```bash
CUDA_VISIBLE_DEVICES=0 "$AIC_PY" "$AIC_GPU_WRAPPER" \
  --name "content_choice_20261019_v1_production_$AIC_CANDIDATE" --max-seconds 7200 \
  --planned-output-bytes 1073741824 \
  --capacity-reason "One reviewed content-choice candidate on426 sources; no automatic package or submission" \
  --queue-seconds 0 \
  -- "$AIC_PY" -B "$AIC_ENTRY" --stage production --candidate "$AIC_CANDIDATE" \
  --config "$AIC_CONFIG" --assets "$AIC_OLD_ASSETS" --production-assets "$AIC_FORMAL_ASSETS" \
  --review-run "$AIC_RUN/review_$AIC_CANDIDATE/review.json" --formal-qa "$AIC_FORMAL_QA" \
  --admission "$AIC_RUN/production_$AIC_CANDIDATE.admission.json" \
  --torch-checks "$AIC_RUN/torch_cpu_checks.json"

"$AIC_PY" -B "$AIC_CODE/admission.py" --action package --candidate "$AIC_CANDIDATE" \
  --config "$AIC_CONFIG" --assets "$AIC_OLD_ASSETS" --production-assets "$AIC_FORMAL_ASSETS" \
  --production-run "$AIC_RUN/production_$AIC_CANDIDATE/completion.json" \
  --output "$AIC_RUN/package_$AIC_CANDIDATE.draft.json"
```

生产 complete 是 `COMPLETE_PRODUCTION_NOT_PACKAGED`，保留全部新 raw、输入/时钟、采用的旧522、runtime/counters、frozen_verification 和 selection；GPU wrapper 的 resource/唯一费用账本另外保留，由执行 Agent 绑定到交付记录，不能把内部 budget 快照当作实际收费证明。执行 Agent 核自然 `completed/exit0`、resource/唯一账本一致、没有无效或缺窗、实际参数≤9B及无未经评价的处理变化，再另存填写 `package_<candidate>.admission.json`。下面是之后的独立 CPU 封包入口：

```bash
timeout --signal=TERM --kill-after=30s 1800s \
  "$AIC_PY" -B "$AIC_ENTRY" --stage package --candidate "$AIC_CANDIDATE" \
  --config "$AIC_CONFIG" --assets "$AIC_OLD_ASSETS" --production-assets "$AIC_FORMAL_ASSETS" \
  --production-run "$AIC_RUN/production_$AIC_CANDIDATE/completion.json" \
  --admission "$AIC_RUN/package_$AIC_CANDIDATE.admission.json"
```

package 独立重读全部522 raw/token/grammar/native选择、冻结回执和 runtime，重新合成426源并重算该候选的决定，与 selection 完全一致后才调用 field/PTS renderer。observation 新 prefix 还要从已有 patches 重建四张量。随后原独立严格验证器实际检查11项、ZIP成员/CRC、目标比例和原包身份。

合法空来源保留；FAILED、缺源、截断、过期身份不变成空。任何所选帧超出冻结 field 定义域先写诊断再停止，不能删掉该帧后假装是相同候选。与保护包 canonical predictions 零差异时不输出新 ZIP。输出分别为：

- `package_critic/rendered/candidate_CONTENT_CHOICE_CRITIC.zip`
- `package_contrast/rendered/candidate_CONTENT_CHOICE_CONTRAST.zip`
- `package_observation/rendered/candidate_CONTENT_CHOICE_OBSERVATION.zip`

这里只描述三个可分别执行的接口，不代表现在有任何新正式 ZIP。没有自动官网提交；不能旧包改名或零差异凑五次。官方 score 只能另附用户/执行 Agent 的真实平台回执，不从外部代理换算。

### 10.1 可选：两个候选均准入时，critic 复用 contrast 正式完整池

如果 contrast 与 critic 都独立通过各自 pilot 和生产审查，可先运行一次 contrast 正式池，再用同一池的全部四槽 real features 计算 critic；无须重复1,044次抽样或2,088次 real TF。不能只把 contrast 选中的答案转交 critic。只有 critic 通过时，直接运行上节的 critic 正式入口更便宜；不能为了这个复用接口启动已停止的 contrast。

复用是另一次明确的 CPU production，不会自动发生，也不需要新的 `--torch-checks`。原池必须是同 config/assets、formal QA、plan、check collection 和 runtime 的完整 contrast426/522成功终态；它自己的 review、独立 admission、全部522输入/seed/raw/token/native/TF/frozen记录会重新核验。只接受 contrast → critic，禁止串联复用。

```bash
"$AIC_PY" -B "$AIC_CODE/admission.py" --action production --candidate critic \
  --config "$AIC_CONFIG" --assets "$AIC_OLD_ASSETS" --production-assets "$AIC_FORMAL_ASSETS" \
  --review-run "$AIC_RUN/review_critic/review.json" --formal-qa "$AIC_FORMAL_QA" \
  --production-pool "$AIC_RUN/production_contrast/completion.json" \
  --output "$AIC_RUN/critic_reuse_production.draft.json"
```

执行 Agent 审查后另存填写 `critic_reuse_production.admission.json`；随后：

```bash
timeout --signal=TERM --kill-after=30s 1800s \
  "$AIC_PY" -B "$AIC_ENTRY" --stage production --candidate critic \
  --config "$AIC_CONFIG" --assets "$AIC_OLD_ASSETS" --production-assets "$AIC_FORMAL_ASSETS" \
  --review-run "$AIC_RUN/review_critic/review.json" --formal-qa "$AIC_FORMAL_QA" \
  --production-pool "$AIC_RUN/production_contrast/completion.json" \
  --admission "$AIC_RUN/critic_reuse_production.admission.json"
```

仍独立输出 `production_critic/selection.json`、`cpu_reuse_verification.json` 和 `completion.json`，不覆盖 contrast。执行模式是 `CPU_CRITIC_FROM_ADMITTED_CONTRAST_POOL`，本轮12项调用计数全部0；原成本只在 `adopted_origin_counts` / `adopted_origin_budget` 及显式 origin 引用中体现，不能重复收费，也没有新的模型加载/冻结校验 PASS。漏传 `--production-pool` 不能把这份 CPU admission 用于新 GPU 调用。

然后设 `AIC_CANDIDATE=critic`，按上节普通 package 草稿、独立审查和封包命令处理新 `production_critic/completion.json`。**package 不传 `--production-pool`**，它沿 completion 的原池引用再次重读所有输出和 critic 决策。该复用分支也计入 run_root 累计1GiB，真实 Linux 运行仍未进行。

## 11. 执行 Agent 需要补充的最小信息

只回传允许公开的聚合短回执，完整私有证据留 Linux：

1. 精确执行 SHA/代码manifest、真实原资产 manifest SHA/用途依据、采用43/522成功链；新 Torch 43项 gate与实际环境。
2. 每作业的自然终态、resource/唯一费用账本、开始/完成的 generation/TF/top-level forward、0 backward/update、峰值MiB、收费秒、累计新磁盘字节；最后冻结参数回执。
3. DPO 16对已收费缓存的绝对概率差、raw/参考差、共同前缀；不请求新增梯度/模型调用来解释旧结果。
4. 新固定池逐源唯一动作数、选择量、含空动作、oracle空间/排序覆盖与regret；区分候选没有更好答案和选择器找不到已有好答案。
5. 三机制完整来源/全部原评审 F1/P/R、逐源胜负/增删/false-empty、shape/permuted/raw 对照和所有冻结停止原因。OOF/test曝光边界完整披露，不只报最好的汇总值。
6. observation 真正改变的图像/PTS/prefix与无效果采用数量；相同视觉 token 预算是否实际成立。没有视频空间GT时，联合构图质量继续 `UNKNOWN`，不以轨迹平滑或时间 F1 代替。

公开规则已于2026-10-19核查，见 RESEARCH 的原文链接与解释界限。执行前再核官网现行版本；若限制变化，记录差异。测试数据不得用于训练、闭源服务、人工补标或按排行榜反构规则。每日五次是提交次数上限；没有特别许可记录可绕过这些限制。
