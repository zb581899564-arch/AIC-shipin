# v3真实教师时间坐标修复

v2真实32B小试已加载GPU并生成首条响应，但该响应混用源PTS139.514375/150和本窗0..30秒，被原strict validator拒绝，0合格标签/0 T更新，旧raw/frames/失败保留。本版同一自然窗口/同一64源帧/同一PNG/同一模型与主提示词，逐帧文本明确窗口内时间；结构化生成的区间端点仅可取实测窗口内采样PTS或0/窗口末端，metadata常量只绑定输入身份，all_provided_frames_reviewed/空/不确定/语义均由模型选择。不得修补旧响应、裁段或制造空标签，validator不改。端点生成粒度属于新教师配方，单独登记。本版同时修复probe.per_window_wall_sec数组的max统计，不把数组当标量。

# 本机32B教师标注接口

入口为 `teacher_label.py`。主控将它放在共享GPU wrapper内执行；本模块不下载、不传输、不访问官网、不启动学生训练。服务器只绑定 `127.0.0.1`，客户端禁用环境代理和HTTP重定向。输入只接受冻结的128train/32dev完整自然窗口，不打开100confirm或复赛媒体。

## 调用

Linux `RUN` 为 `/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z`。下面是接口示例，变量不是额外目录或任务：

```bash
python "$RUN/teacher_student_autopilot_v1/teacher_label.py" \
  --run-dir "$RUN" \
  --out-dir "$RUN/teacher_student_autopilot_v1/teacher_01" \
  --selected-train "$RUN/next_round_v1/supervision_v2/selection_02/selected_train.jsonl" \
  --selected-dev "$RUN/next_round_v1/supervision_v2/selection_02/selected_dev.jsonl" \
  --selection-receipt "$RUN/next_round_v1/supervision_v2/selection_02/selection_receipt.json" \
  --teacher-admission "$RUN/teacher_student_autopilot_v1/teacher_admission.json" \
  --server-url http://127.0.0.1:8080 --start-server --phase probe
```

`--phase probe` 完成真实工程探针后退出；主控按 `teacher_probe_completion.json` 的 `wall_sec`、`per_window_wall_sec` 和实际token计量登记下一作业。将同一命令改为 `--phase all` 接续全部标注、独立验证及二次真实弱审核。`labels` 只到独立验证，`review` 只做已有validated的真实二次审核。单次HTTP超时默认3600秒，可通过 `--request-timeout` 显式调整。完整作业止时由外层wrapper依据实测成本登记。

探针按冻结选择清单的真实ffprobe元数据，从各split选择“实际selected帧数最多→提供的原始RGB footprint最大→稳定window_id最小”的一个窗口。排序不读标签、旧高光或内容。其native源尺寸对host解码内存有解释性，但不是尚未实测的教师token最坏上界；每次请求仍检查真实llama输入长度和像素。`probe_selection.json`保存160个候选的metadata和选择理由。工程探针接受语义不确定或超过5段的完整合法响应作为工程证据，但它们不进入SFT；探针不证明质量或训练准入。

`all`逐字节核验并复用同out已完成的探针，不再次标注它们。每次 `--start-server` 都重新加载本机服务器，Popen不创建独立进程组，继承外层共享GPU wrapper的PGID；正常完成或失败后只停止本次Popen对象。不会信号外部进程。外层wrapper控制并发、GPU账本、动态物理容量及单次止时。

## 初始教师准入JSON

主控负责真实文件下载验收、源码/二进制pin、共享资源和物理容量核验。传入的不可变JSON需要以下字段：

```json
{
  "status": "ADMITTED_PENDING_REAL_TEACHER_PROBE",
  "base_model_id": "Qwen/Qwen3-VL-32B-Instruct",
  "model_id": "Qwen/Qwen3-VL-32B-Instruct-GGUF",
  "model_revision": "e3e1fe0c76de7ee58ea65db420c643adfe2e457c",
  "runtime_revision": "5ad1c5da0ad7f6176256b823925aad19134f0263",
  "job_source_lock_sha256": "主控真实源码锁SHA256",
  "production_test_access": false,
  "weight_files": [{"path":"真实Linux完整权重路径","bytes":0,"sha256":"真实SHA256"}],
  "max_sequence_length": 65536,
  "max_pixels_per_frame": 786432,
  "image_min_tokens": 8,
  "image_max_tokens": 768,
  "max_new_tokens": 8192,
  "server_binary_sha256": "主控已核pin二进制SHA256",
  "server_command": ["真实llama-server绝对路径", "--model", "Q4_K_M绝对路径",
    "--mmproj", "F16投影器绝对路径", "--host", "127.0.0.1", "--port", "8080",
    "--parallel", "1", "--ctx-size", "65536", "--no-context-shift", "--log-verbosity", "10",
    "--image-min-tokens", "8", "--image-max-tokens", "768"]
}
```

示例占位值不可用于实际准入。`weight_files`必须是原validator官方metadata指定的完整Q4_K_M和F16投影器两文件、实际size和SHA；脚本读取实际文件并逐SHA核验，拒绝incomplete文件。教师ctx与像素独立声明；这里768 image tokens对应patch16/merge2的786432像素预算。全部实际尺寸从tensor-copy DEBUG日志获取，禁止把该公式或HF视频processor计算当实际计量。

脚本核服务器command的本机host、single slot、context/no-shift、image token flags与准入一致，核真实 `/v1/models` 的image modality和实际slot ctx。初始JSON不回写。两个真实探针的顺序解码/HTTP/处理日志/strict响应通过后，写 `out/teacher_admission.json` 为 `PASS_REAL_STRONGER_TEACHER_ADMISSION`；该PASS仍不代替语义监督门。

也支持已由主控核验的外部本机server：不传 `--start-server`，初始status须已为PASS，需提供 `server_url`、`server_pid`、`server_log`、`server_parallel=1`、`server_log_verbosity>=5` 和所有身份/限制字段。外部server不由本脚本停止。

## 真实观察合同

先核源SHA与ffprobe完整PTS序列SHA，再从ordinal0使用PyAV完整顺序解码。每个实际frame都必须有PTS并与ffprobe同ordinal相差不超过1e-6秒。仅存原selector已冻结的最多64个ordinal，没有新采样、seek、FPS重建时间或越界补帧。原生RGB为 `np.ascontiguousarray(frame.to_ndarray(format='rgb24'))`，哈希 `image.tobytes(order='C')`。无损PNG保存后重开并核相同RGB哈希。observation额外提供真实 `source_total_frames/fps_num/fps_den/width/height`，学生重新按ordinal解码核同一哈希。

教师使用有显式逐帧ordinal/PTS文本的独立 `image_url` PNG序列。pinned llama `input_video`会按video-fps重采样，因此这里不用该入口。日志 `copying image i/n ... (nx=..., ny=...)`核真实processed空间网格；Qwen单图的两次temporal copies仅在同尺寸时归并为一个实际源帧。测量缺失/额外/顺序异常、pixels超界、实际usage.prompt_tokens缺失/超界、finish_reason非stop、HTTP或JSON失败都STOP并保存原始证据。

教师与学生契约是同源文件、同完整window范围、同floor endpoint选择、同原生PTS、同ordinal和同RGB字节。教师使用独立图像embedding，学生使用64HD视频 temporal-paired embedding，两者不声称输入tensor相等。学生显式 `size={shortest_edge:4096,longest_edge:25165824}` 与16384token保持；本模块不会退到Mac低像素或削帧。教师实际ctx单独是65536，实际像素和token逐调用记录。

`teacher_prompt.txt`为旧 `next_round_v1/supervision/teacher_prompt.txt`的精确字节副本，运行时先核SHA。label提示与原validator完全一致；观察contract展开包含实际送入PTS。额外逐帧文本与完整HTTP request亦单独SHA绑定。unknown/uncertain不转为空；>5段原样排除，不剪裁、合并或删除事件理由。

## 输出与科学边界

每个 `windows/window_id/`保存完整顺序decode receipt、PNG、实际prompt、HTTP request/response原字节、raw answer、server JSON、实际输入contract/log、annotation和局部strict record。仅 `done.json`存在且全部绑定文件与帧RGB/源SHA重新核验通过才复用。中途失败目录保留并STOP，不自动重试或随机重标。

全部160标注后，`annotation_receipts.jsonl`送入新的Python子进程执行未改写的原 `validate_teacher.py`。旧输出helper只允许旧supervision目录；新runner只替换这个fresh输出路径guard，指向唯一owned `out/validated`，不修改响应、观察、身份或清洗逻辑。原validator SHA、依赖SHA、guard适配正文SHA记在 `independent_validator_execution.json`。因此新目录不会改写冻结源码。

结果为 `validated/{validated_records.jsonl,eligible_train.jsonl,eligible_dev.jsonl,validation_receipt.json}`。全部receipt正确且无无效/未标注记录才写 `teacher_completion.json` 的 `PASS_VALIDATED_WEAK_TEACHER_LABELS`。uncertain与>5段排除仍在validated_records审计；这个PASS没有训练准入或官方质量含义。

语义门先检train/dev各至少一个真实可解释positive和显式empty、train数量能在最多3epochs/有效batch16产生20-update前缀，以及systematic全空/全窗全选。不足STOP并报告需独立登记扩展选择，不能强拼空配额。通过后，同一32B再次看每个eligible窗口的完整相同PNG/PTS及原始标签；真实review JSON必须确认all frames、uncertain=false、semantics_consistent=true、issues=[]及非空reason，否则整个review STOP，不移除失败样本来凑门。

`raw_semantic_review_receipts.jsonl`绑定每个eligible canonical teacher record hash、真实raw JSON及SHA、sourceRGB/ordinal/PTS、实际review processor contract和HTTP响应。raw精确keys是 `window_id,observation_scope,semantics_consistent,uncertain,reason,issues`，scope与原label一致。`semantic_review.json`采用 `aic_automated_weak_semantic_review_v1`/`PASS_AUTOMATED_WEAK_SEMANTIC_REVIEW`，记录主控/学生约定字段、真实内容解释、稳定window_id代表例、缺失类别和每窗retained duration fraction。没有出现的多段/边界案例不捏造。

同一32B二次审核不是独立教师、人类审核或真值；mode明确为 `AUTOMATED_WEAK_TEACHER_REVIEW_NOT_HUMAN_GROUND_TRUTH`。所有输出保持 `semantic_training_admitted=false`，主控仍需真实学生工程/资源/源码绑定准入。旧first-workday期限不作为放行依据。官网成绩只由用户实际提交产生。

## 已执行检查

Windows使用现有Python运行 `python teacher_cpu_tests.py`：10项全部PASS。涵盖unknown/伪负、明确空/多段/边界不修补、PTS与RGB缺失、来源泄漏与test路径、真实log计量合同、仅loopback、真实reviewraw矛盾、监督数量/bias停止、HTTP/JSON原字节保留，以及真实独立子进程调用原validator的receipt链。测试均为明确synthetic CPU工程fixture，不宣称真实教师观察或质量通过。真实32B探针/160标注/语义审核需Linux实际运行receipt确认。
