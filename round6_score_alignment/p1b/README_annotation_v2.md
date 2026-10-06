# P1b 标注工具使用说明 v2（当前版本）

- 版本：`p1b_core_v2`；适用文件：`G:\ai\AIC视频\round6_score_alignment\p1b\annotate.html`
- 本文件**取代** `README_annotation.md`（v1）：v1 描述的是已被修复的旧行为（无框编辑、闭区间端点、无草稿）。
  v1 文件按总控要求保留不改，仅作历史记录。

---

## 1. 打开方式

1. （可选，推荐）启动本机精确帧服务，用于**逐帧精确**标注：
   ```
   python round6_score_alignment\p1b\frame_server.py
   ```
   - 只监听 `127.0.0.1:8765`（回环），不联网、不上传；可加 `--port` 换端口。
   - 停止：在该终端按 `Ctrl+C`，或浏览器访问 `http://127.0.0.1:8765/shutdown`。
   - 可用样本：8 个试点样本 + 合成测试样本（`--extra-manifest`）。
2. 双击 `annotate.html` 打开（纯 `file://`，无需服务器）。
   - 若用非默认端口：`python round6_score_alignment\p1b\build_page.py --server http://127.0.0.1:<port>`
   重新生成页面。
   - 不启动服务也能用：此时只能“估算定位”，误差字段记为 `null`（未知），工具会明确提示。

## 2. 标注流程

1. 左栏选样本 → 中栏粗定位视频（`currentTime` 只用于粗定位）。
2. 在“精确帧”区输入帧号 → `取精确帧`：页面用本机 CPU 解码该帧并显示静态图，同时打印
   `解码帧 index / pts / time_base / sha256`。服务先按真实解码顺序建立有界 PTS 索引，逐帧核对
   manifest 帧数、尺寸、媒体 SHA-256 和帧率，再以索引 PTS 取图。非零起始 PTS 与非整数 fps 可用；
   VFR、错误 fps、缺失/重复 PTS、帧数或尺寸不符均拒绝。仅接收 manifest 帧数 1–10000 的媒体；
   首次取每条媒体需要顺序扫描，后续按索引取图。
   帧号是标注主键；`pts_sec` 是实际解码 PTS，导出的 `start_sec/end_sec` 只是 `frame/fps` 的
   名义秒数，`seconds_semantics` 明示此区别。
   页面用取回的**同一份图像字节**算 SHA-256、加载图像，均成功后才显示并启用精确溯源。
   改帧号、切样本、请求逆序、HTTP 失败、图像失败或哈希不符会使旧精确帧失效。
3. 点 `显示/编辑框` → 画面上出现蓝框：**拖动框移动，拖右下角方块改变宽度**；框始终满足
   `h = w·th/tw` 且不越界。中栏显示显示比例（显示 1px = 源 N px），坐标存的是**源像素**。
4. 精确定位每个端点后分别点 `起点=当前帧` / `末帧=当前帧`，当时保存各自的定位溯源；
   也可手填端点，手填按误差未知记录。之后点 `添加区间`。导出写入
   `start_frame` 与 `end_frame_exclusive`（= 最后保留帧 + 1），**半开区间 [start, end)**，
   允许 `end = N` 覆盖最后一帧。
5. `以当前帧添加关键帧` → 存稀疏构图框 `box_xyw = [x, y, w]`（与 P1a 参考 schema 同名字段）。
6. 选状态：`有高光` / `确认无高光`（需勾选确认）/ `不确定` / `未标注`（默认）。
7. 填标注者；复核者**未复核就留空**。`导出参考 JSON` 或 `导出全部已标注参考`。
8. 草稿：改动会自动存到浏览器本地草稿；`导出草稿` 存成文件，`导入草稿` 读回文件，
   `恢复自动草稿` 从本地恢复。有未保存改动时关闭页面会提示。导入前会校验媒体身份与协议版本，
   不一致直接报错；覆盖未保存工作前会二次确认。

## 3. 状态 → 导出规则

| 状态 | 模式 | 可作参考？ |
|---|---|---|
| 未标注（默认） | `NOT_EXPORTABLE` | 否（`intervals/keyframes = null`，未标注 ≠ 空） |
| 不确定 | `NOT_EXPORTABLE` | 否 |
| 确认无高光（须勾选） | `NO_HIGHLIGHT_EMPTY_GT` | 是：`coverage=full, frames=[]` |
| 有高光 + 区间 + 关键帧 | `SPARSE_KEYFRAME_GT` | 是：`coverage=sparse` |
| 有高光 + 只有区间 | `TEMPORAL_ONLY` | 否（仅时间诊断） |
| 任一项校验失败 | `BLOCKED_BY_VALIDATION` | 否，且**列出具体问题**（不会静默清除用户工作） |

校验项包括：数值有限性（NaN/Infinity/字符串/bool 一律拒绝）、框在帧内且满足目标比例、
关键帧帧号唯一且在范围内、区间唯一且 `0 ≤ start < end_exclusive ≤ N`、
秒数与帧号一致（半帧容差）、端点/关键帧**各自**带定位溯源、
`NO_HIGHLIGHT` 与残留区间/框冲突时报错、标注者必填。

## 4. 定位溯源（每个端点独立）

| `method` | 含义 | 误差字段 |
|---|---|---|
| `decoded_frame` | 用本机解码的指定帧（含 index/pts/time_base/图像 sha256） | `0` |
| `pts_sample` | 历史 PTS 采样记录；没有完整解码顺序与显示哈希链 | `null`（未知） |
| `browser_seek` | 浏览器 `currentTime` 定位，未与解码帧核对 | `null`（未知） |
| `manual_frame_input` | 手工输入帧号 | `null`（未知） |

只有 `decoded_frame` 可以声称精确（误差 0）；其余必须记 `null`。区间终点额外记录
`derived: "end_frame_exclusive = last_kept_frame + 1"`。

## 5. 相关工具

| 文件 | 用途 |
|---|---|
| `annotation_core.js` | 页面与 Node 测试共用的 JS 实现；Python 是独立实现，使用共同样例核对 |
| `boundary_cases.json` | 28 条固定边界样例（JS 与 Python 交叉验证） |
| `frame_server.py` | 本机回环精确帧服务（PyAV 按需解码） |
| `validate_exports.py` | 导出/草稿校验与参考派生（`cases` / `export` / `compare`） |
| `run_ui_e2e.py` | 上一轮浏览器脚本；其下载 hook 不构成本轮真实落盘证据 |
| `test_fix2_frame.py` / `test_fix2_page.js` | 合成视频顺序取帧及实际页面脚本的离线状态回归；不替代真实浏览器验收 |
| `make_marked_synthetic.py` | 生成带机器可读帧编号的合成测试视频 |
| `build_page.py` | 用清单渲染 `annotate.html`（改端口/换样本时用） |
| `build_pilot_package.py` | **历史**清单构建脚本：会重写受保护的 `pilot_manifest.json`，**不要重跑** |

## 6. 禁止

- 不上传任何视频/帧到外部服务；不调用外部模型生成标注。
- 不用官方测试视频做标注。
- 不伪造“无高光”或构图语义；未标注就必须保持未标注。
- 8 条仍是 `pilot_dev`，不得当作盲测留出集。
