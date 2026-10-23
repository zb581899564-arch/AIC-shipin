# GPT-6.1-sol Linux RUNBOOK：固定提交、真实冒烟、完整426、独立封包

## 0. 先读结论与边界

执行的是本轮**新的生产风险探索**，不是恢复122/123、CONTROL5或旧训练协议。首先读根目录 [FINAL_SPRINT_PLAN_20261023.md](../../FINAL_SPRINT_PLAN_20261023.md)、[candidates.json](candidates.json)、[VALIDATION.md](VALIDATION.md)，再读最新 [START_HERE](../../reports/github_status_20261023_v1/START_HERE.md) 和 [RESULT122_123](../../reports/t_branch_execution_20261022_v1/RESULT122_123.md)。本轮代码主流程已经实现，缺少的是本机现存私有资产的精确绑定和真实首次运行。

目标：先交 `g_subject` 的一个工程完整且真正不同的ZIP和小交付清单，然后按实际共享GPU吞吐选择R/M。没有任何新包被证明超过40.48。新候选不新增F1/五折/人工标注门；首个真实工程冒烟必须执行，模型/映射/全空崩塌故障先修。官方视频不外发、不训练、不转为伪标签；不人工改选片或框，不自动官网提交。

时间：用户消息提供剩余24小时和两天各5次；具体账户余额及日界在执行端查看。保守预算终点先按本轮接单时刻约 `2026-10-23 04:05 UTC` 加24小时，即 `2026-10-24T04:05:00+00:00`。这是本轮预算锚点，**不是独立核实的官方延期**；若用户实际窗口或账户显示更早，以更早为准，不能每次恢复都改成“现在+24h”。累计全部模型命令墙时≤18h，至少4h收尾；共享GPU等待也消耗实际日历窗口。

## 1. 第一条命令：只读真实资源

```bash
df -hT /home/inspur/aic_video_work /dev/shm
```

继续只读核查，不结束/暂停外部任务：

```bash
free -h
nvidia-smi --query-gpu=index,uuid,memory.total,memory.free,utilization.gpu --format=csv
nvidia-smi --query-compute-apps=gpu_uuid,pid,used_memory --format=csv
ps -eo pid,comm,pcpu,pmem --sort=-pcpu
```

根盘0.22GB、tmpfs10GB只是旧快照。这里必须复核实际值。代码checkout约207MiB（本公开checkout测量，训练机fetch增量以实际为准）；不要在余量相近的根盘再完整clone。优先采用现有Git对象并在已有获准的数据文件系统建立独立worktree。原模型/视频不复制。若只有tmpfs可用，必须同时满足MemAvailable与Java保护余量，明确它不是跨重启永久盘，完整证明和最终包需有Linux内持久保存去向；没有合格容量就报告具体缺口，不能删除旧基线/证据来腾空间。

GPU有外部任务时，等待其自然完成，或使用现有调度器对本run_root/GPU UUID的真实有效共享授权；不得伪造授权文件或抢显存。程序不会发信号给Java、CONTROL5或其他任务。CPU计算≤2线程，不安装新的服务/代理/路由，不改SSH，不买计算资源。

## 2. 固定源码，使用现有解释器

从本次交付消息复制**完整40位最终commit**到 `FSV1_COMMIT`。不要自行用最新branch head替代它。PR目标分支是 `sync/20261023-t-branch-results`，精确基点必须为 `e8224c4339007790a1be383be19fdb200cc817bc`；main不够新。

下面变量中，现存私有工作根和Python采用已发布代码记录的真实接口。`FSV1_OUTPUT_PARENT` 是步骤1确认有容量的现成获准目录；可以与原工作根不同。`FSV1_GIT_SOURCE` 是本机已存在的该仓库Git checkout，执行者只需填实际路径，不必改主流程。没有Linux checkout时，可从Windows部署这次必要的小代码及固定Git对象到现有获准工作目录；不反向搬媒体/raw/tensor来方便审计。

```bash
set -euo pipefail
export FSV1_WORK=/home/inspur/aic_video_work
export FSV1_PYTHON="$FSV1_WORK/env/qwen3vl_isolated_20260910/bin/python"
: "${FSV1_COMMIT:?从本次PR交付消息复制完整40位SHA}"
: "${FSV1_GIT_SOURCE:?填入Linux现存AIC-shipin Git checkout绝对路径}"
: "${FSV1_OUTPUT_PARENT:?填入已核实容量的现成获准输出父目录}"
test "${#FSV1_COMMIT}" -eq 40
test -x "$FSV1_PYTHON"
export FSV1_REPO="$FSV1_OUTPUT_PARENT/final_sprint_checkout_20261023"
export FSV1_RUN="$FSV1_OUTPUT_PARENT/final_sprint_production_20261023_v1"
export FSV1_BIND="${FSV1_RUN}_binding"
export FSV1_MAPPING="$FSV1_BIND/mapping.json"
export FSV1_ASSETS="$FSV1_RUN/assets.json"
export FSV1_SCRATCH=/dev/shm
export FSV1_DEADLINE=2026-10-24T04:05:00+00:00
```

只有本机已确认合法直连GitHub时才执行fetch；已有精确对象可直接采用，不必下载。代理/未知中转先询问用户，不修改配置来绕过限制。安全的checkout操作：

```bash
if ! git -C "$FSV1_GIT_SOURCE" cat-file -e "$FSV1_COMMIT^{commit}"; then
  GIT_TERMINAL_PROMPT=0 git -C "$FSV1_GIT_SOURCE" fetch --no-tags origin "$FSV1_COMMIT"
fi
if [ ! -e "$FSV1_REPO" ]; then
  git -C "$FSV1_GIT_SOURCE" worktree add --detach "$FSV1_REPO" "$FSV1_COMMIT"
fi
test "$(git -C "$FSV1_REPO" rev-parse HEAD)" = "$FSV1_COMMIT"
git -C "$FSV1_REPO" merge-base --is-ancestor e8224c4339007790a1be383be19fdb200cc817bc HEAD
test -z "$(git -C "$FSV1_REPO" status --porcelain --untracked-files=no)"
cd "$FSV1_REPO"
"$FSV1_PYTHON" -m improvement.final_sprint_v1.cli --help
```

存在但不匹配的worktree必须保留并检查，不能reset或覆盖。`assets.bind`还会核查本目录每个Python/JSON文件均已被该commit跟踪；不会把未提交小改动当成可复现生产。

## 3. 从现存注册自动生成全部资产接口

本轮不靠扫描latest/vN寻找模型。以下精确路径来自当前仓库实际旧注册入口，bootstrap会逐项核对原SHA和真实文件。某路径被管理员整体迁移时，执行者按原完整注册/原SHA定位现存对应对象；不能换数据、重建基线或忽略不匹配。

```bash
export FSV1_OLD_RUN="$FSV1_WORK/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z"
export FSV1_CONFIG="$FSV1_OLD_RUN/b_score_aligned_package_v4/config.json"
export FSV1_INPUTS="$FSV1_WORK/twenty_hour_five_20261014_v1/temporal_family_native_package_v3/package_inputs.json"
export FSV1_SEM_REG="$FSV1_WORK/semantic_context_production_20261016_v1/production_registration.json"
export FSV1_I3D_ACCEPT="$FSV1_WORK/i3d_umt_cross_domain_20261021_v1/weight_acceptance.json"
export FSV1_UMT_REG="$FSV1_WORK/general_highlight_supervision_20261021_v1/routing_production60/registration.json"
export FSV1_ZIP48="$FSV1_WORK/general_highlight_supervision_20261021_v1/routing_package63/source_remove/candidate_SPORT_ROUTE_REMOVE_8B.zip"
export FSV1_ZIP47="$FSV1_WORK/semantic_context_production_20261016_v1/package/candidate_CONTEXT_SEMANTIC_RESIDUAL.zip"
CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 \
"$FSV1_PYTHON" -m improvement.final_sprint_v1.bootstrap prepare \
  --config "$FSV1_CONFIG" --package-inputs "$FSV1_INPUTS" \
  --semantic-registration "$FSV1_SEM_REG" --i3d-acceptance "$FSV1_I3D_ACCEPT" \
  --umt-registration "$FSV1_UMT_REG" --baseline-40-48 "$FSV1_ZIP48" --baseline-40-47 "$FSV1_ZIP47" \
  --workspace-root "$FSV1_OUTPUT_PARENT" --run-root "$FSV1_RUN" --output-dir "$FSV1_BIND" \
  --deadline "$FSV1_DEADLINE" --scratch-dir "$FSV1_SCRATCH" --gpu-index 0 --inventory
```

若GPU index不是0，在绑定前改成已有调度器分配的实际index。bootstrap的空CUDA环境是**单命令前缀**，不要全局export空CUDA后再跑生产。

该命令会自动生成4份完整factory specs，实际在CPU加载并严格清点：

| 组件 | 精确资产接口 | 实际加载方式 |
|---|---|---|
| 原TIME | config `b_adapter`/adapter_model.safetensors，原SHA必须为 `8e2cca463d8aac39f7a709bdf562373e3e47a3a8da490991c303d5e03b803b23` | materialize实际LoRA A/B参数，15,335,424；不是量化后磁盘数 |
| semantic | 原 `production_registration.selected_head`；`SEM/code/monotone_head06.py` | `ResidualHead(12289,8)`，严格state，98,329 |
| I3D | 原weight_acceptance引用的实际文件 | 原SHA锁定 `ENGINEERING/runtime.py:make_models(...)[0]`，`model_state` |
| SportUMT | 原routing_production60注册 `expert_checkpoint`及source_input_lock | 同一原factory `[1]`，`model`；I3D+UMT合计34,252,497 |

代码不import旧launcher、不恢复旧训练、不执行历史质量门。成功库存存在时只核验采用。四个实际辅助参数总数应为49,686,250，完整原8B仍在后续GPU加载中实际清点。原BASE canonical冻结SHA必须为 `74bcce81cfcb0893cf4b4c25ae36ec908d6ea669583aedd0f3940063080b8b59`，真实8,767,123,696个参数；仅同架构同参数量不算身份一致。

预期终态 `ALL_FOUR_ACTUAL_CPU_DEPENDENCIES_COMPLETE_BASE_GPU_INVENTORY_PENDING`。文件在 `$FSV1_BIND/specs/`、`inventories/`、`inventory_completion.json`、`mapping.json`。这些都是本机新产物，不能上传公开Git。中断后用：

```bash
CUDA_VISIBLE_DEVICES='' OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 \
"$FSV1_PYTHON" -m improvement.final_sprint_v1.bootstrap inventory \
  --preparation "$FSV1_BIND/preparation.json"
```

### 可选M资产决定必须在首次bind之前

如已有原始CLIP文件和作者CG权重，直接绑定；若缺失，按 [OPTIONAL_SPECIALIST.md](OPTIONAL_SPECIALIST.md)执行真实直连检查及固定版本小资产准备。它会创建另一个 `mapping_with_specialist.json`，保留基础mapping。现有clip环境或直连不满足时跳过M，继续G/R。不要让可选资产耗尽首包时间。

M特征采用无损float32原字节base64，按 `8192 × sum(ceil(每源实际秒数/2)) + 300000×427` 字节估算双份可恢复图像/文本缓存，此外留1GiB给其他路线和证据。binder根据全量真实时钟自动提高计划持久输出容量，绝不把143MB权重大小当作全部存储成本；权重/源码的新增空间在可选手册单独核算。前5源查看实际增长，保守预算不足则停路线，不静默删除共享成功。

## 4. 绑定、预检和首个真实冒烟

```bash
"$FSV1_PYTHON" -m improvement.final_sprint_v1.cli bind \
  --mapping "$FSV1_MAPPING" --output "$FSV1_ASSETS" --expected-commit "$FSV1_COMMIT"
CUDA_VISIBLE_DEVICES=0 "$FSV1_PYTHON" -m improvement.final_sprint_v1.cli preflight \
  --assets "$FSV1_ASSETS" --expected-commit "$FSV1_COMMIT" --candidate g_subject --gpu
CUDA_VISIBLE_DEVICES=0 "$FSV1_PYTHON" -m improvement.final_sprint_v1.supervise \
  --assets "$FSV1_ASSETS" --expected-commit "$FSV1_COMMIT" --action smoke --candidate g_subject
```

实际index不是0时同步替换上述前缀。bind会核验426媒体SHA、原生时钟、两原ZIP、当前模型完整文件树和原色彩修复配置；不复制媒体、不自动找目录。现有log316输入修复按原SHA和完整policy保留，这是已采用的工程转换，不是新加测试来源特例。

preflight检查当前磁盘、tmpfs/物理RAM、GPU空闲/外部任务、实际Python依赖；要求现有Transformers4.57.1。不要为可选路线大规模重装环境。新推理使用本机原Qwen BF16/sdpa，禁自动Hub下载、禁外部推理。真实空间冒烟在仅按媒体元数据选择的一源上执行16个相邻原生帧，验证decode→Qwen主体→GrabCut/LK→合法框；不是质量筛选，不看官方标签。

预期 `smoke/grounding/completion.json: REAL_ENGINEERING_SMOKE_PASS`，带实际参数清单/真实输入证据/耗时、`quality_evaluated:false`。公开CPU检查不能代替此状态。模型身份、EOS/JSON、native PTS、真实图片/空间证据或参数数错误都停止，不转为空或默认框。

wrapper输出自己的精确目录，例如 `$FSV1_RUN/wrappers/<随机ID>/`，不要靠“最新目录”定位。该目录 `command.log`、`claim.json`、`completion.json` 和 `terminated_claims/`是本次实际终态。正常或失败均以实际wait结果为准，不以pid不存在或tmux断线判断。

## 5. 首个全426与独立CPU验收

```bash
"$FSV1_PYTHON" -m improvement.final_sprint_v1.cli forecast \
  --assets "$FSV1_ASSETS" --expected-commit "$FSV1_COMMIT"
CUDA_VISIBLE_DEVICES=0 "$FSV1_PYTHON" -m improvement.final_sprint_v1.supervise \
  --assets "$FSV1_ASSETS" --expected-commit "$FSV1_COMMIT" --action run --candidate g_subject
"$FSV1_PYTHON" -m improvement.final_sprint_v1.cli package \
  --assets "$FSV1_ASSETS" --expected-commit "$FSV1_COMMIT" --candidate g_subject
```

`supervise`是所有smoke/run的生产入口，直接CLI会拒绝没有wrapper的GPU执行。它严格拥有一个新子进程组，累计预算或阶段超时时只终止本组并wait，绝不按旧PID终止外部任务。自然完成不额外发信号。CPU派生也用同一有界入口，但不会加载GPU。

G最大3h命令墙时。`forecast`按真实全量时钟估算，冷加载分开；R/M估计包含新空间开销。正常生产先完成5个来源，用实际墙时/物理时长推算剩余×1.2；预计无法在阶段或最终预留前完成就STOP，已成功调用全部保留。该规则是成本控制，不是效果挑选。不要因成本STOP改口“模型质量失败”。

首个交付里程碑：

```text
$FSV1_RUN/candidates/g_subject/package/candidate_FINAL_G_SUBJECT.zip
$FSV1_RUN/candidates/g_subject/package/delivery.json
$FSV1_RUN/candidates/g_subject/package/package_receipt.json  （完整内部回执留Linux）
```

预期完整source状态为 `SUCCESS_NONEMPTY` 或 `SUCCESS_EMPTY`，失败没有source成功文件。封包终态 `ENGINEERING_ACCEPTED_QUALITY_UNVALIDATED`，每包完整426条、单JSONL、CRC/memberSHA通过、对40.48/40.47的加帧/删帧/改框/改变来源数明确。G必须加帧0/删帧0，实际框差异若为0会按重复基线拒绝，不能仅改ZIP名。

独立 `package` 命令在新进程重新读取全部source成功账本和原生证据，0新模型调用。426有一条缺失/失败、全空/全选、非法框、参数超9B或与任何已封新包同预测都会拒绝。它可在最后4h收尾期运行，不要求再次抢GPU。

## 6. 后续候选：先看真实吞吐，再用预登记配置

G父包完成后，几何对照不需要新GPU：

```bash
CUDA_VISIBLE_DEVICES=0 "$FSV1_PYTHON" -m improvement.final_sprint_v1.supervise \
  --assets "$FSV1_ASSETS" --expected-commit "$FSV1_COMMIT" --action run --candidate g_center_control
```

R一次冒烟包含真实物理局部输入和缓存分支/完整无padding参考比较；常规32帧片约17物理forward，冒烟额外8参考。容差固定，失败不能绕过或用参考结果替换原分支。

```bash
CUDA_VISIBLE_DEVICES=0 "$FSV1_PYTHON" -m improvement.final_sprint_v1.supervise \
  --assets "$FSV1_ASSETS" --expected-commit "$FSV1_COMMIT" --action smoke --candidate r_phase_event
"$FSV1_PYTHON" -m improvement.final_sprint_v1.cli forecast \
  --assets "$FSV1_ASSETS" --expected-commit "$FSV1_COMMIT"
CUDA_VISIBLE_DEVICES=0 "$FSV1_PYTHON" -m improvement.final_sprint_v1.supervise \
  --assets "$FSV1_ASSETS" --expected-commit "$FSV1_COMMIT" --action run --candidate r_phase_event
CUDA_VISIBLE_DEVICES=0 "$FSV1_PYTHON" -m improvement.final_sprint_v1.supervise \
  --assets "$FSV1_ASSETS" --expected-commit "$FSV1_COMMIT" --action run --candidate r_phase_apex
```

若一次R冒烟预测超过可用8h或剩余日历时间，停止R，切已绑定M；不继续生成半套426。R 1ms保守DP成本量化可能舍弃恰好占满25%上限的事件，尤其VFR/短源；这是固定规则风险，不临时改比例或强制填满。apex只采用父包选中的相同事件和已存在空间子集，缺父成功时会拒绝启动新模型。

M只有在首次bind已包含合法资产时执行。先主包后通用查询对照：

```bash
CUDA_VISIBLE_DEVICES=0 "$FSV1_PYTHON" -m improvement.final_sprint_v1.supervise \
  --assets "$FSV1_ASSETS" --expected-commit "$FSV1_COMMIT" --action smoke --candidate m_specialist
"$FSV1_PYTHON" -m improvement.final_sprint_v1.cli forecast \
  --assets "$FSV1_ASSETS" --expected-commit "$FSV1_COMMIT"
CUDA_VISIBLE_DEVICES=0 "$FSV1_PYTHON" -m improvement.final_sprint_v1.supervise \
  --assets "$FSV1_ASSETS" --expected-commit "$FSV1_COMMIT" --action run --candidate m_specialist
CUDA_VISIBLE_DEVICES=0 "$FSV1_PYTHON" -m improvement.final_sprint_v1.supervise \
  --assets "$FSV1_ASSETS" --expected-commit "$FSV1_COMMIT" --action run --candidate m_generic_control
```

上述命令是候选入口，不是无条件全顺序执行清单。资源不够时按计划只完成高优先级主包；对照的每个新source仍通过同样全426封包门。M基于共享CLIP图像特征，但新查询/CG前向、新选中帧的空间定位确实另计，不称零推理或独立模型证据。

## 7. 恢复：精确终态优先，禁止成功重启

只读短状态：

```bash
"$FSV1_PYTHON" -m improvement.final_sprint_v1.cli status \
  --assets "$FSV1_ASSETS" --expected-commit "$FSV1_COMMIT"
```

| 状态 | 动作 |
|---|---|
| `success.json`存在、terminal丢失 | 同一命令会验证并采用成功、补终态，0新模型 |
| `returned_result.json`完整，写success前中断 | 自动采用原始完整返回值，0新模型 |
| 完整返回值与后续failure共存 | 用本次精确wrapper终态reconcile；原failure保留，另写adoption，0新模型 |
| claim未完成、显式failure、旧PID/超时 | 不自动重试；先读本次wrapper的实际completion和失败位置 |
| 前N源成功、N+1失败 | 解决N+1工程故障后，仅继续未完成部分；前N源与已成功子调用不重跑 |
| 426全成功、封包失败/中断 | 单独 `cli package`；不重启GPU或完整推理 |
| 包已完整成功 | `run`也会先采用完整包并独立复核，不重新申请GPU |

在真实wrapper完成后才执行：

```bash
: "${FSV1_TERMINAL:?填本次supervise实际打印的completion.json完整路径，禁止自动找latest}"
"$FSV1_PYTHON" -m improvement.final_sprint_v1.cli reconcile \
  --assets "$FSV1_ASSETS" --expected-commit "$FSV1_COMMIT" --wrapper-terminal "$FSV1_TERMINAL"
```

这不是重跑命令。它核对每个claim SHA、任务ID、owned-wrapper身份和实际terminated证据，采纳可恢复成功或明确释放未完成claim；之后才显式重发相同supervise命令。没有wrapper终态时，先取得现有调度器的确切本任务终态，不造“pid不存在所以成功/可重跑”的证明。wrapper自身遭SIGKILL或主机重启可能无法写终态，这种情况下保持未决，不自动重启成功或未知调用。

失败位置：`wrappers/<exact>/command.log`；`journal/tasks/<task_id>/attempts/<n>/failure.json`与claim；`command_budget/<command_id>/completion.json`；各source `spatial_evidence.json/result.json`；包 `package_receipt.json`。完整证据留Linux，只读取必要短状态，禁止把官方媒体/raw/tensor/完整输入锁传回聊天或Windows。

如果代码必须修复，先形成新Git提交并明确受影响机制/输入，保留原失败与成功。不能在原asset lock下面悄改代码；不得因此从零重跑旧成功实验。当前固定代码的常规中断恢复已完整实现，不要求执行者补写主流程。

## 8. 最终传输、人工提交及费用

只把最终ZIP、小 `delivery.json` 和独立接收脚本 `verify_received.py` 送Windows；完整package_receipt及来源证明留Linux。接收端不解包重压、不修改JSONL，运行：

```powershell
python verify_received.py --manifest delivery.json --zip candidate_FINAL_G_SUBJECT.zip
```

预期 `TRANSFER_IDENTICAL`，检查最终ZIP大小/SHA256、仅一个predictions.jsonl、CRC、memberSHA及426 ID集合。其他candidate替换实际ZIP文件名即可。只有这一步通过的原字节文件才能交用户手动官网提交；不自动点击提交。

执行Agent汇报每包：candidate_id、完整Git SHA、实际模型全部参数、改变范围、实际工程终态、ZIP bytes/SHA/memberSHA、预测identity、相对两原包差异、真实运行墙时/physicalforward、失败费用、共享GPU等待、质量是否验证。`command_budget`统计完整子进程加载/核验/解码/推理/失败/封包墙时，和`journal`里的逻辑任务数分开；嵌套任务墙时不重复求和。这里没有购买外部资源的货币账单，不把墙时叫独立测得的GPU内核时间。

保留两原包SHA复核结果。新风险包分数低就放弃该固定路线；不能用平台总分恢复测试标签、为某源改规则或扫同阈值。最多六个有差异的注册包，不要求耗尽十次；最后4h停止新GPU路线，预留验收、传输及平台算分。
