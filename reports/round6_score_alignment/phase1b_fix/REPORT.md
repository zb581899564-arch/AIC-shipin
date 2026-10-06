# P1b 标注工具定向修复报告

- run_id：`round6_p1b_fix_20260917T1630Z`
- 执行时间：2026-09-17 16:30Z–17:40Z
- 依据：`reports/round6_score_alignment/SUPERVISOR_P1B_REVIEW.md`（判定 `P1B_PARTIAL_MEDIA_VERIFIED_TOOL_CHANGES_REQUIRED`）
- 范围：**只修标注工具、导出边界与使用说明**；未进入正式标注、未扩集、未训练、未推理、未提交
- 资源：GPU 0；未 SSH、未下载、未安装；本轮新增 **1,287,175 B ≈ 1.23 MiB**（预算 500 MiB）；CPU 验证合计约 1 分钟（预算 20 分钟）
- 历史保护：8 条媒体、`pilot_manifest.json`、phase1b 全部报告、P1a 代码与 vendor 副本、AGENTS/ROADMAP 共 **50 个受保护文件哈希前后完全一致**

---

## 0. 结论摘要

1. **六项阻塞全部修复，并且都用真实页面闭环证明**：真实浏览器（Chrome headless）打开页面 → 取精确解码帧 → **拖动/缩放可见框** → 存区间与关键帧 → 切样本（状态重置）→ 导出草稿 → 刷新后恢复 → 导出参考 → Python 校验 → **P1a 接口消费**。
2. **两条失败路径在真实页面上被正确拒绝**：负宽度框（从被篡改的草稿导入）与“无高光 + 残留区间/框”都**拒绝导出并列出问题**，不再静默丢弃用户工作。
3. **JS 与 Python 同源**：页面加载的 `annotation_core.js` 与 Python 校验器在**同一组 28 条手写边界样例**上各自 28/28 通过，且**逐例结论完全一致（divergences = 0）**。
4. **帧精度可核对**：关键帧使用本机 CPU 解码的静态图，链路为
   请求帧 64 → 服务器解码 index 64（pts 6.4）→ 图像 sha256 `1dc8f25a…` = 导出中的 `image_sha256` = 浏览器收到的字节 → **从图像里解出的机器可读编号 = 64**。
5. **端点语义统一为半开区间** `[start_frame, end_frame_exclusive)`，允许 `end = N` 覆盖最后一帧；
   旧闭区间文件**拒绝导入**，不猜测转换。
6. **恢复能力可用**：自动草稿 + 文件导出/导入 + 离开提示；刷新后恢复出 2 条标注（状态/标注者/区间/框/溯源齐全）并再次成功导出参考。
7. **P1a 消费结果符合预期**：稀疏参考 → `SPARSE_DIAGNOSTIC`（score=null）；参考不含未标注样本时 → `NOT_COMPUTABLE`（score=null），**未标注不会被当成空真值，也不会产生联合分**。

---

## 1. 逐条对应总控问题

### 阻塞 1：画框功能未实现（含关键帧行错表）

| 修复前（本机实测） | 修复后 |
|---|---|
| `has_showBox_handler = false`、`drag_listener_count = 0`（按钮存在但无处理） | `showBox` 有 onclick；`mousedown/mousemove/mouseup` 共 4 处监听；拖动移动、右下角手柄按比例缩放 |
| 关键帧行被追加到**时间区间表**：`intervalTable` 2 行 / `kfTable` 0 行 | 区间 → `#intervalTable`、关键帧 → `#kfTable`（各自 1 行，E2E 断言 `table_counts_after_add = {intervals:1, keyframes:1}`） |
| 切样本沿用上一条的帧号与框 | 切样本重置帧号=0、隐藏框、清空精确帧、表格按样本重绘（E2E：切到 S02 后 `frame=0, overlay=none, tables=0/0`） |
| 显示缩放与源坐标关系未声明 | 中栏显示“显示比例 0.xxx（显示 1px = 源 N px）”；坐标始终存**源像素**；框经 `clampBox` 强制满足目标比例与边界 |

E2E 实测：拖动后框 `[14,9,120]`、缩放后 `[14,9,126.97]`，`overlay_moved=true`、`overlay_resized=true`、
`box_within_frame=true`、`box_ratio_ok=true`；越界请求 `[9999,9999,9999]` 被夹到合法范围。

### 阻塞 2：实际网页导出缺少统一校验

修复前（对真实页面 JS 的复现）：`box=[0,0,-10]`、`box=[NaN,0,100]`、越界框都仍然
`exportable_as_reference=true` 且模式 `SPARSE_KEYFRAME_GT`；“无高光 + 残留区间/框”直接导出空参考。

修复后：
- 导出前统一走 `validateAnnotation`（与 Python 同一套规则）；失败 → **拒绝导出、不产生参考、逐条列出问题**；
- 无高光与残留区间/框冲突 → `BLOCKED_BY_VALIDATION`，提示“清除或改回状态，不做静默丢弃”；
- E2E 实测：`invalid_export_returned_empty=true`（没有产生下载）、`invalid_export_notice` 含
  `keyframe 0: w must be > 0`；`conflict_export_returned_empty=true`，提示含
  `NO_HIGHLIGHT conflicts with the remaining intervals/keyframes`。

### 阻塞 3：Python 校验漏非有限值

修复前复现（归档的旧校验器）：`box=[NaN,0,100]` → `valid=True`、`problems=[]`、**并且产出了参考**。

修复后（新校验器，10 项探针全部拒绝且不产出参考）：

| 探针 | 结果 |
|---|---|
| `NaN` / `Infinity` / `bool` / `string` 框值 | 全部 `valid=false`、`reference=None` |
| 负宽度 / 越界框 | 拒绝 |
| 重复关键帧 / 重复区间 | 拒绝（`duplicate keyframe for frame 12` / `duplicate interval [10, 20)`） |
| 旧闭区间字段（无语义） | 拒绝（`refusing to convert`） |
| 无高光 + 残留区间/框 | 拒绝并报告冲突 |

另：身份必填、帧号范围、秒数与帧号一致性（>0.5 帧即拒绝）都在同一套规则中。

### 阻塞 4：帧精度证据不足

| 修复前 | 修复后 |
|---|---|
| 设置 `currentTime` 后直接记误差 0 | 只有 `decoded_frame` / `pts_sample` 可记 0；`browser_seek` / `manual_frame_input` 记 `null`（未知），并写入说明 |
| 单一全局 `frame_source` | **每个区间起点、终点、每个关键帧各自带溯源**（`start_provenance` / `end_provenance` / `provenance`） |
| 无解码核对 | 新增本机回环精确帧服务（PyAV 按需解码，只监听 127.0.0.1），页面显示静态图 + `index/pts/time_base/sha256`，并核对浏览器收到的字节一致 |
| 手工改帧号与视频不同步 | 帧号输入同步视频位置与提示；`timeupdate`/`seeked` 绑定时间显示 |

E2E 帧链证据（`ui_e2e/e2e_record.json` → `frame_chain`）：
`frame=64`、`server_index=64`、`server_pts_sec=6.4`、
`exported_image_sha256 = server_image_sha256 = 1dc8f25a651a79f7b039e8ade55d5c82b6c6ce2b8d0e1309f5b1254dbf561207`、
`hash_match=true`、**`marker_decoded_from_served_image=64`、`marker_matches_frame=true`**
（合成视频每帧内嵌机器可读的帧编号，由独立的 Python 校验器从服务返回的图像里解出）。

### 阻塞 5：区间端点不明确

- 全链路统一为 **`start_frame` / `end_frame_exclusive`（半开 `[start, end)`）**，合法范围
  `0 ≤ start < end ≤ N`，**允许 `end = N`** 覆盖最后一帧；导出中写入
  `interval_semantics = "half_open_end_exclusive"`。
- 相邻区间合法（B20）；空区间、越界、重复区间拒绝（B17/B18/B16）。
- 旧 `end_frame`（闭区间）字段在草稿或导出中一律**拒绝并给出理由**，不猜测转换。
- 与 P1a 一致：P1a 的选择策略本身就是 `a ≤ t < b` 的半开语义（`aic6/timebase.py`）。

### 阻塞 6：恢复能力缺失

- 自动草稿（浏览器本地）+ `导出草稿` / `导入草稿` / `恢复自动草稿`；
- 导入校验：协议版本、区间语义、媒体身份（`sample_digest` + 每样本媒体 SHA-256）、未知样本、旧字段；
- 覆盖未保存工作前二次确认；有未保存改动时关闭页面触发离开提示；
- **E2E 真实刷新恢复**：step2 为新页面加载 → `草稿已恢复：2 条标注` → 恢复出
  `status=HAS_HIGHLIGHT`、`annotator=E2E_SYNTHETIC_ANNOTATOR`、区间 `[60,120)`、关键帧 64/`[30,20,200]`，
  `restored_valid=true`，并再次成功导出参考。

---

## 2. 真实页面闭环（`ui_e2e/`）

**方式**：无头 Chrome（`--headless=new`，`file://` 页面 + 对本机回环服务的真实 HTTP），
驱动脚本通过**真实 UI 事件**操作（点击真实按钮、在遮罩层上派发 `mousedown/mousemove/mouseup`、
拖动手柄），并用页面暴露的只读调试钩子读取状态。合成媒体 `synthetic_marked.mp4`
（120 帧 / 10 fps / 320×240，每帧内嵌可机器解码的帧编号）。

**闭环步骤（step1，实际顺序）**

打开样本 S01 → 取精确解码帧 37（index/hash 双核对）→ `显示/编辑框` → 拖动 → 缩放 →
越界请求被夹紧 → 取精确帧 64 → 添加关键帧 → 添加区间 `[60, 120)`（覆盖最后一帧 119）→
切到 S02（状态重置）→ 切回 S01 → 导出参考（valid）→ 导出草稿 → 导入被篡改草稿（-10 宽）→
**导出被拒** → 重新导入好草稿（valid）→ 设“无高光+确认” → **冲突被拒** → 改回有高光（valid）→
再次导出参考 + 草稿。

**step2（刷新恢复）**：新页面加载 → 恢复自动草稿 → 状态与标注完整 → 再次导出参考。

**产物**：`ui_e2e/step1_page.png`（186,815 B）、`ui_e2e/step2_page.png`（178,445 B）、
真实导出 JSON：`step1_reference.json`、`step2_restored_reference.json`、`step1_draft.json`、
`refusal_invalid_draft.json`、`refusal_no_highlight_conflict.json`、`e2e_record.json`。

**诚实声明（保留）**

- 交互由脚本派发真实 DOM 事件完成，**不是人手操作**；这能证明页面逻辑与界面元素可用，
  不能替代人工手感验收。
- 本执行模型**无图像输入能力**，因此没有做像素级目视验收；截图已保存供总控/人工查看。
- 页面下载在自动化运行中被跳过（`__E2E_NO_DOWNLOAD`），因为无头下载需要 CDP 客户端；
  保存下来的 JSON 是页面交给下载器的**同一载荷**（来自同一函数、同一证据钩子）。
- 8 条真实试点视频的语义标签**仍未填写**；本闭环只用合成媒体。

---

## 3. 自动边界测试（`test_results.json`）

| 项 | 结果 |
|---|---|
| 共享边界样例（手写期望，JS 引擎 = 页面加载的 `annotation_core.js`） | **28/28 通过** |
| 同一批样例（Python 校验器） | **28/28 通过** |
| JS ↔ Python 逐例结论比对 | **完全一致，divergences = 0** |
| 修复前回归（旧页面 JS + 旧 Python 校验器） | 5 类边界全错（见 §1） |
| 非法输入探针（NaN/Inf/bool/string/负宽/越界/重复/旧字段/冲突） | **10/10 拒绝且不产出参考** |
| E2E 产物校验（2 个正样本 + 1 个拒绝样本） | 3/3 符合预期 |
| 草稿导入校验（含媒体身份与协议版本） | 通过 |
| 命令退出码 | 5 条命令全部 exit 0 |

样例集 `boundary_cases.json` 中每条期望值都是**手写**的（新增样例含“相邻区间合法”“末帧覆盖”
“估算定位允许但不能声称精确”“解码帧号与记录不一致要拒绝”等），不从被测实现生成。

**本轮由测试自己抓到并修掉的实现缺陷**（均留痕）：
1. JS 里的链式比较 `0 <= frame < n` 恒真 → 越界关键帧未被拦截（B21 暴露）；
2. 页面“显示框”开关状态与自动绘制互相冲突，首次点击反而隐藏（E2E 暴露）；
3. 添加区间时端点溯源误用“当前播放帧”，而不是区间端点自身（E2E 暴露）；
4. 关键帧字段名 `box` 与 P1a 参考 schema 的 `box_xyw` 不一致（P1a 消费时暴露，已统一）。

---

## 4. 接口与语义

| 项 | 值 |
|---|---|
| 核心版本 | `p1b_core_v2`（`annotation_core.js`，页面与 Node/Python 共用） |
| 导出 schema | `p1b_annotation_export_v2`；草稿 `p1b_annotation_draft_v2` |
| 区间语义 | `half_open_end_exclusive` |
| 稀疏框字段 | `box_xyw = [x, y, w]`（高度推导 `h = w·th/tw`） |
| 参考覆盖 | 稀疏关键帧 → `coverage="sparse"`；确认无高光 → `coverage="full", frames=[]`；其余不产出参考 |
| P1a 消费 | 稀疏参考 + 对应评分全集 → `SPARSE_DIAGNOSTIC`（score=null）；全集含未标注样本 → `NOT_COMPUTABLE`（score=null） |

---

## 5. 修改范围与保护

- 修改/新增均在 `round6_score_alignment/p1b/`（工具、测试、说明）与
  `reports/round6_score_alignment/phase1b_fix/`（报告）内；清单见 `changed_files.json`。
- **未修改**：8 条媒体、`pilot_manifest.json`、`fingerprints.json`、`inventory_raw.json`、
  phase1b 全部报告与截图、P1a 全部代码与 vendor 副本、AGENTS.md、ROADMAP.md、提交包与历史数据。
  50 个受保护文件哈希前后一致（`protected_hashes.json`）。
- `README_annotation.md`（v1）按总控“保留历史”的要求**保持字节不变**，由
  `README_annotation_v2.md` 说明其已被取代。
- `build_pilot_package.py`（历史清单构建脚本，会重写受保护清单）保留但已在 v2 说明中标注**不要重跑**。

---

## 6. 未完成项与限制

1. **真实语义标注 0 条、人工复核 0 条**：本轮只修工具；8 条真实视频仍未标注（`UNANNOTATED`）。
2. **8 条仍是 `pilot_dev`**：不是盲测留出集；扩到 80 组时试点及其同源视频不得进入新 holdout。
3. **像素级目视验收未做**：执行模型无图像输入；截图与 DOM/状态证据已提供，需人工或总控抽查。
4. **下载路径未走浏览器真实下载**：自动化运行跳过下载点击（需 CDP），保存的是交给下载器的同一载荷。
5. **合成测试数据单独登记**：`synthetic/synthetic_marked.mp4`（53,607 B，带机器可读帧编号）
   与 `synthetic_pilot.mp4` 仅用于工具验证，**不计入真实人工标注数**，也不作为诊断样本。
6. **协议证据解释（沿用总控意见，未据此重做媒体）**：
   - 哈希固定媒体身份，**不证明标签正确**；
   - 缩略图近重复筛查与分辨率/时长差异**不证明与测试素材无共同来源**；
   - 先前报告的 CFR 结论基于**排序后的 packet PTS**，与逐帧 `frame.pts` 不完全等价；
     本轮精确帧服务会独立核对 `frame.pts`，但仅覆盖被请求的少数帧；
   - 项目拟定用途**不等于逐视频许可证据**；
   - P1b 的 10/10 是 Python 镜像/集成用例，**不是网页交互验证**；本轮已补真实页面闭环。

---

## 7. 是否具备进入人工试标的条件

**工程条件已具备**：可见框编辑、精确帧核对、严格导出校验、草稿恢复、真实页面闭环与
JS/Python 一致规则都已通过验证。**但工具通过验收不等于可以开始标注**：
是否启动人工试标（先 2 条：横/竖各 1，完整复核后再做 8 条）由总控决定；本轮不自行开始。
