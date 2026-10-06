# protocol_audit.md — 作者跟踪协议直读审计

- 审计对象：`HVision-NKU/OraRL` @ commit `e1ec91ff00f59ee0da04d285938c1f7247daa69c`
- 本地路径：`/home/inspur/aic_video_work/orarl_round1/src/OraRL`（只读使用）
- 关键源码：`eval/task/tracking/eval_tracking_vllm.py`、`eval/task/eval_vllm.py`、`eval/task/eval.sh`、`eval/task/eval_prompt.py`、`data/eval/datasets.jsonl`、`eval/task/qwenvl_decord_patch.py`
- 审计方式：直接读固定 commit 的代码，行号即该 commit 的行号。**未为迎合当前模型输出而改动协议解释。**
- 重要限制：真正的 GOT-10k 标注文件（`annotations/tracking/got10k.jsonl`）与媒体属于 `OraRL/OraRL-Data` 数据集，**本轮未下载**（不在授权范围内）。因此凡涉及标注原文的地方，本审计只依据评测代码中出现的**字面证据**，并明确标注哪些内容无法从仓库确证。

---

## 0. 结论速览

| 问题 | 结论 | 主要证据 |
|---|---|---|
| 首帧框如何提供 | **提示词文本里的整数坐标字面量** `[x1,y1,x2,y2]`，不是单独图片、不是画框图片 | `eval_tracking_vllm.py:343-347`、`:380-381`、`:513-518` |
| 是否还给自然语言描述 | 仓库内**没有**第二个描述字段；只把 `problem`/`question` 字符串整段送进模板。示例措辞里也没有类别名 | `eval_tracking_vllm.py:238-242`、`:343-344` |
| 输出键语义 | GT 键是**源视频的真实秒**，1..32；**不是**采样帧序号 | `eval_tracking_vllm.py:15`、`:529-530`、`:161-163` |
| 首帧/采样/输出键/GT 如何对应 | 首帧框 = GT 的第 1 秒框；`fps=1, max_frames=32` 在整段视频上均匀取 32 帧；键 N 与 GT 的键 N 对齐；**代码从不校验第 N 个采样帧是否真的落在第 N 秒** | `eval_tracking_vllm.py:507-520`、`:760-763`、`:161-163`、`:529-535` |
| 是否要求目标始终存在 / 支持 absent/null | **不支持**。schema 只有 `boxes`；缺帧记 0 分；没有 absent/null 分支 | `eval_tracking_vllm.py:14-16`、`:151-164`、`:186-202`；全文无 absent 相关分支 |
| 长视频 / 切镜 / 不足 32 秒 | 长视频：默认路径整段送，fps=1 会把 32 帧摊到整段（另有明确标注为**诊断**的 chunked_reprompt 用真实秒切窗）。切镜：**无任何处理**。不足 32 秒：按 `round(duration*fps)` 少取帧，但提示词仍要 32 个键 | `eval_tracking_vllm.py:305-336`、`:760`、`:881-885`、`:907-925`；`qwenvl_decord_patch.py:40-59,167-168` |
| 与上一轮输入的差异 | 上一轮**完全没给首帧框**，只给了自然语言描述 —— 这在作者协议下是**缺输入的**；另有 2/32 秒槽的时基偏差 | 见 §7 |

---

## 1. 作者如何提供首帧框？

**答：作为提示词文本中的整数坐标字面量。**

```python
# eval_tracking_vllm.py:343-347
# Match an [x1,y1,x2,y2] bbox literal — the canonical pattern in GOT-10k
# prompts: 'Given the bounding box [537,403,768,703] of the target object'.
# We capture the FIRST 4-int bracket group in the prompt; tolerate spaces.
_BBOX_4INT_RE = re.compile(
    r"\[\s*(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)\s*\]")
```

- 注释直接给出了 GOT-10k 提示词的措辞：`Given the bounding box [537,403,768,703] of the target object`。框是**纯文本整数**，写在问句里。
- `eval_tracking_vllm.py:350-357` 的 `_replace_first_bbox_literal()` 说明首帧框就"在 question 里"，替换时把坐标取整后写回文本。
- `eval_tracking_vllm.py:380-381` 明确写 "1) replace first-frame bbox in question"。
- 不是单独图片、不是画框图片：`_build_video_content()`（`:322-336`）只构造 `{"type":"video", ...}`，没有第二张图；`build_prompt_text()`（`:238-242`）只由字符串拼提示词。

**坐标制**：`_replace_first_bbox_literal` 只做 `int(round(float(v)))`，不缩放；而 GT 框在评测里与预测框直接做 IoU、不做任何重缩放（`:139-148`、`:161-163`），且预测框是 norm1000（`:16`）。`eval_tracking_vllm.py:518` 又把"提示词里的首帧框"与 `gt[1]` 当作可互相替换的回退关系 —— 所以**提示词里的框与 GT 同为 norm1000**。

> 不确定性（如实标注）：GOT-10k 标注原文在未下载的 `OraRL-Data` 中。上述"norm1000"是由代码中的等价性推出的，不是从标注文件直接确认的。

---

## 2. 是否还提供自然语言描述？

**答：仓库证据里没有第二个描述字段。**

```python
# eval_tracking_vllm.py:238-242
def build_prompt_text(example, enable_thinking=False, prompt_mode="default"):
    question = _strip_leading_tags(
        example.get("problem") or example.get("question") or "")
    return QUESTION_TEMPLATE_NO_THINK.format(Question=question) + TRACKING_TAIL
```

- 只有 `problem` / `question` 一个字符串进入模板；`:232-235` 的 `_strip_leading_tags` 只去掉开头的 `<video>` 标签。
- GOT-10k 提示词示例（`:344`）只含框，**不含类别名或外观描述**。
- 模板本体（`eval/task/eval_prompt.py:93-106`）中 `Question` 之外没有任何补充描述字段：

```
GROUNDING_QUESTION_TEMPLATE_NO_THINK = "{Question}\nPlease answer this question based on the visual content. "
TRACKING_TAIL = "Please track the target object throughout the video and provide one bounding box per second, ONLY up to 32 seconds, ..."
```

> 不确定性：若 `OraRL-Data` 里的 GOT-10k `problem` 字段实际拼接了类别名（如 "person"），本仓库无法证伪。仓库能确证的是：**评测代码本身只提供框**，不存在独立的描述输入通道。

**这直接推翻上一轮的做法**：上一轮只给了自然语言描述、没给框，属于**缺必需输入**，而不是"协议的另一种写法"。

---

## 3. 输出键是实际秒、采样序号，还是其他？

**答：字面规定是"源视频的真实秒"，1..32；不是采样帧序号。**

```python
# eval_tracking_vllm.py:13-16
# Schema notes (mirrors OneThinker's `eval_bench.py` 'tracking'):
#     - Answer is a JSON dict with key `boxes` only (NO `time` field).
#     - `boxes` is a dict keyed by integer second 1..32 (max 32 seconds).
#     - Each value is a 4-number bbox [x1,y1,x2,y2] in norm1000 coords.
```

```python
# eval_tracking_vllm.py:529-535
# IMPORTANT: GOT-10k GT-second labels (1, 2, ..., 32) are REAL seconds
# in the source video, NOT sampled-frame indices. So the temporal cut
# passed to qwen_vl_utils must be in real seconds too. ...
v_start = max(0.0, float(win_first) - 1.0 - 0.5)  # in seconds
v_end = float(win_last) + 0.5
```

键是整数秒；`:186-202` 的 `_normalize_boxes` 用 `int(float(k))` 归一（注意：`"1.5"` 会被截成 `1`，与键 `"1"` 冲突，见 §6）。

---

## 4. 首帧、采样时间、输出键与真值如何对应？

链路如下（默认路径，即论文使用的路径）：

1. **首帧框**：`eval_tracking_vllm.py:507-520` 从 `problem` 里正则取出框；取不到就回退到 `gt[1]`：
   ```python
   # Try to read first-frame box from prompt; fallback to gt[1].
   m = _BBOX_4INT_RE.search(prompt)
   init = [float(x) for x in m.groups()] if m else gt_b.get("1", [])
   ```
   → **首帧框 = GT 的第 1 秒框**。
2. **视频输入**：默认路径 `eval_tracking_vllm.py:760` 调 `_build_video_content(vp, args)`，`video_start`/`video_end` 均为 `None`（`:305-307`）→ **整段视频**；`fps`/`max_frames` 来自 canonical profile（见 §6）。
3. **采样**：`qwenvl_decord_patch.py:167-168`
   ```python
   nframes = _smart_nframes(ele, total_frames=total_frames, video_fps=video_fps)
   idx = torch.linspace(0, total_frames - 1, nframes).round().long().tolist()
   ```
   `_smart_nframes`（`:40-59`）：`n = clamp(round(duration*FPS), MIN_FRAMES=4, MAX_FRAMES=32)`。
4. **对齐**：`mean_iou_over_gt_frames`（`:151-164`）逐 GT 键取值比对，预测缺键记 0：
   ```python
   for k, gbox in gt_boxes.items():
       total += iou_2d(pred_dict.get(k, []), gbox)
   ```
   即**键对键**比较：预测键 N ↔ GT 键 N。

**关键观察：评测代码从不校验第 N 个采样帧是否真的落在第 N 秒。** 它默认视频长约 32 秒，于是 `linspace` 的 32 个点每点落进一个秒格。这个假设在 canonical GOT-10k 上成立；一旦视频长度不是 ~32 秒就不成立，而代码里没有任何断言或警告。

**实测（`no_gpu_tests/known_time_mapping.json`，见 §4.1）**：只有在视频正好 32.000 秒时，槽位 N 才落在第 N−1 个秒格（0-based），32/32 正确。

### 4.1 已知时间视频实测

构造 32.000 s / 30 fps / 960 帧、每帧用黑白位块编码"真实秒"的视频（容器 ffv1 无损），用作者 canonical 采样参数跑 `process_vision_info`（decord），再从**解码后的像素**读回真实秒：

| 配置 | n_sampled | 采样帧号（前 6） | 解码真实秒（前 6） | 槽位=真实秒+1 |
|---|---|---|---|---|
| canonical `fps=1, max_frames=32` | 32 | 0, 31, 62, 93, 124, 155 | 0, 1, 2, 3, 4, 5 | **True（0/32 错）** |
| 脚本 argparse 默认 `fps=2, max_frames=64` | 64 | 0, 15, 30, 46, 61, 76 | 0, 0, 1, 1, 2, 2 | False（63/64 错） |

结论：canonical 配置在**正好 32.000 s** 的视频上，槽位 N ↔ 第 N 个一秒格，语义自洽。而脚本自身的 argparse 默认（`fps=2, max_frames=64`）与"每秒一个键"完全不匹配 —— 这也说明 **canonical profile（`eval.sh`）才是协议**，脚本默认值不是。

### 4.2 上一轮片段的时基偏差（量化）

`orarl_round1/clips/src_wk2CeU_DcBo_60_210_off0_len32.mp4` 实际时长 **32.200 s / 962 帧**。32 槽 linspace 后：

- 均匀间隔 **1.0333 s**（而非 1.000 s）
- 槽 1 → t=0.000 s；槽 32 → t=32.033 s（相对 32 s 漂移 +0.033 s）
- **落入错误秒格的槽位：2/32（第 31、32 槽）**

即：上一轮确实存在时基偏差，但幅度小且集中在末尾。

---

## 5. 原始任务是否要求目标始终存在？是否支持 absent/null？

**答：协议要求目标全程存在；不支持 absent/null。**

- 答案 schema 只有 `boxes`，注释明确 "NO `time` field"（`:14-15`），没有任何表示"目标不可见"的字段或取值约定。
- 缺帧的处理是**记 0 分**而不是"标记缺席"（`:151-164`）：
  ```python
  """Mean IoU over EVERY gt frame; missing pred frames score 0."""
  ```
- `_normalize_boxes`（`:186-202`）对坏条目是 `continue` **静默丢弃**，不产生"缺席"语义。
- 全文件检索 `absent` / `null` / `disappear` / `not visible` / `occlu`：**没有任何相关分支**（仅命中 `None` 用作 Python 空值、`last_box is not None` 等无关处）。
- GT 方面，注释称 "got10k always = 32"（`:22`），即每个样本都有 32 个 GT 帧 → 目标被假定全程可见。

**因此：** 目标消失、遮挡到不可见、切镜换主体，都不是该协议能表达的情况。评测里这类情况只会表现为 IoU 变低，而不会记为"应当缺席"。

---

## 6. 作者如何处理长视频、切镜、不足 32 秒的视频？

### 6.1 长视频

- **默认路径不处理**：整段视频送进采样，`n = clamp(round(duration*1), 4, 32)`。对 100 秒的视频，32 帧被摊到整段（间隔 ≈3.2 s），而提示词仍然说"每秒一个框、最多 32 秒"，输出键 N 与真实秒 N 的对齐**失效**。代码对此没有断言也没有警告。
- 作者另有一条**明确标注为诊断**的路径：`--chunked_reprompt`（`:907-925`），注释写 "USE ONLY for diagnostics: this is NOT the default GOT-10k protocol."（`:913`）。它按真实秒切窗（`:529-535` 的 `v_start`/`v_end`，含 ±0.5 s 余量），并**替换示例中的键序列**，因为 "Models tend to mimic the example's key set rather than follow instructions"（`:372-376`）—— 这条注释本身说明作者知道模型有照抄示例键的倾向。
- 解码侧有 `DECORD_EOF_RETRY_MAX=20480`（`:58`）用于长视频。

### 6.2 切镜

**没有任何处理。** 没有镜头检测、没有重定位、没有 absent 分支。切镜后目标不存在时，协议的合法输出仍然是一个框（因为 schema 不表达缺席），而 GT 若在切镜后仍有框，模型只能靠视觉匹配；若 GT 也没有，评测会把它当普通帧记分。

### 6.3 不足 32 秒

- 采样侧：`n = clamp(round(duration*fps), MIN_FRAMES=4, MAX_FRAMES=32)` → 10 秒视频只取 10 帧。
- 提示词侧：**仍然要求 1..32 个键**（`TRACKING_TAIL`，`eval_prompt.py:98-106`）。
- 评测侧：`mean_iou_over_gt_frames` 只遍历 **GT 的键**，所以多出来的预测键被忽略；缺失的 GT 键记 0。
- 结论：不足 32 秒时，"键 N = 第 N 秒"依然字面成立（只要 fps=1 且 `duration ≥ n`），但提示词与视频长度不一致这件事**代码不做校验**。

### 6.4 其他影响输入的开关

- `EVAL_VIDEO_ITEM_ONETHINKER=1`（`:313-321`）会构造**只含** `{video, max_pixels, max_frames, fps}` 的 video item，去掉 `min_pixels`/`total_pixels`；注释说 OneThinker 的 `eval_bench.py` 就是这么构造的，且"extra keys can subtly shift the per-frame pixel layout in qwen_vl_utils"。**默认关闭**（`:321` 取 `"0"`）。
- `--prompt_mode`：`default`（= joint-SFT 对齐模板）或 `bare`（`:899-902`）；canonical 用 `default`。
- `--enable_thinking` 默认 false（`:897-898`）。
- 采样温度 0.0、top_p 1.0（`eval_vllm.py:2584-2588`）→ 贪心解码。

---

## 7. canonical 参数：脚本默认值 vs 论文 canonical profile

两者不同，必须区分。**canonical profile（`eval.sh` + `datasets.jsonl`）才是评测协议**。

| 参数 | 脚本 argparse 默认 | canonical（`eval.sh`/`datasets.jsonl`） |
|---|---|---|
| fps | 2（`:885`） | **1**（`eval.sh:514`） |
| max_frames | 64（`:884`） | **32**（`eval.sh:513`） |
| video_min_pixels | 4·32·32 = 4096（`:875`） | 4096（`eval.sh:510`） |
| video_max_pixels | 64·32·32 = 65536（`:876`） | **786432**（`eval.sh:511`） |
| video_total_pixels | 256·64·32·32 = 16777216（`:877-880`） | **8388608**（`eval.sh:512`） |
| max_new_tokens | 1024（`:891`） | **8192**（`eval.sh:516`） |
| enable_thinking | False（`:897-898`） | false（`eval.sh:520`） |
| prompt_mode | default（`:899`） | default（`eval.sh:521`） |
| chunked_reprompt | 0（`:914`） | 0（`eval.sh:522`） |

`eval_vllm.py:709-732` 是 canonical 值进入 worker 的地方（`TRACKING_FPS` 默认 1、`TRACKING_MAX_FRAMES` 默认 32、`TRACKING_VIDEO_MAX_PIXELS` 默认 786432、`TRACKING_MAX_NEW_TOKENS` 默认 8192）。
`datasets.jsonl` 的 tracking 行把同一组值写在 `legacy_environment` 与 `preprocessing` 里，`expected_count=180`（GOT-10k 180 条）。

**上一轮使用的正是 canonical 值**（fps=1, max_frames=32, min=4096, max=786432, total=8388608, max_new_tokens=8192），这一点上一轮是对的。

---

## 8. 上一轮输入与作者协议的具体差异

| # | 项 | 作者协议 | 上一轮实际 | 影响 |
|---|---|---|---|---|
| **D-a** | **首帧框** | question 内含 `[x1,y1,x2,y2]` 字面量 | **完全没有框**，只有自然语言描述 | **致命：缺必需输入。** 协议下模型无法知道要跟踪哪一个目标 |
| D-b | 视频时长 | canonical GOT-10k ≈32 s | 32.200 s / 962 帧 | 32 槽 linspace 后间隔 1.0333 s，**2/32 槽落入错误秒格** |
| D-c | 提示词模板 | `GROUNDING_QUESTION_TEMPLATE_NO_THINK` + `TRACKING_TAIL` | 相同 | 一致 |
| D-d | 采样参数 | fps=1, max_frames=32, min/max/total | 相同 | 一致 |
| D-e | 视频窗口 | 默认整段（无 video_start/end） | 整段 | 一致 |
| D-f | 解码后端 | decord（+patch） | decord（env 开关） | 一致 |
| D-g | 推理引擎 | vLLM 0.19.1 | HF Transformers `generate()` | 已知偏差，round1 已记录 |
| D-h | attention | flash_attention_2 | sdpa | 已知偏差，round1 已记录 |
| D-i | 目标存在性 | 假定全程存在 | 片段含切镜、目标后段离开 | 协议无法表达，属能力边界 |
| D-j | 真值 | GOT-10k GT 每样本 32 帧 | 无真值 | 不能算任何指标 |

**根本结论（回答"上一轮静止框是否与初始化或时间映射有关"）：**
主因是 **D-a 缺首帧框**，不是时间映射。依据：
1. 时间映射偏差只有 2/32 槽，且集中在末尾两槽；不可能让**全部 32 槽**退化成同一个框。
2. 作者评测代码与模型输入都不含时基校验；模型收到的只是"32 个均匀采样 + 每帧一个框"的任务，键语义靠提示词维持。
3. 因此"静态框"更可能是**缺少目标锚点**导致的：没有框，模型只能从描述里猜目标，最省力的解是给一个覆盖显著前景的大框并保持不变。
   → 这一点由 round2 的 A/B/C 对照直接检验（见 `REPORT.md` §A/B/C）。

---

## 9. 附：作者解析器与 round2 严格解析器的差异（均为硬化的真实理由）

作者 `eval_tracking_vllm.py` 的解析器有意宽松；round2 的入口刻意更严。差异与理由：

| 项 | 作者 | round2 | 理由 |
|---|---|---|---|
| 数字校验 | `_is_list_of_numbers`（`:122-132`）用 `float(v)` | 拒绝 bool / 字符串 | `float(True)==1.0`、`float("1")==1.0`，会把布尔和字符串当成坐标 |
| 未闭合/多余文本 | `_load_json_relaxed`（`:91-119`）取第一个平衡 `{...}` | 要求整段为合法 JSON | 宽松回退会把"解释文字里碰巧出现的 JSON"当答案 |
| 重复键 | Python `json` 默认后者覆盖 | **报错** | 重复键语义有歧义（`{"1":[..],"1":[..]}`） |
| 秒键 | `int(float(k))`（`:196-197`） | 仅接受整数字面量 | `"1.5"`→1 会与 `"1"` 冲突并静默合并 |
| 多个 `<answer>` | `extract_answer` 取**第一个**（`:84-88`） | **报错** | 多个答案是歧义输出，不应静默取首 |
| 缺失键 | 记 0 分（不报错） | 记为 `protocol_complete=False` | 记分与"协议完整"是两件事，round2 分开表达 |
| 时序解析 | `parse_query` / `extract_time`（`temporal_grounding`） | 要求恰为两个数字 | 避免"取前两个数字、忽略后续" |
