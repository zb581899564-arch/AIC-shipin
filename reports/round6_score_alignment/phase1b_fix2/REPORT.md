# P1b 精确帧身份链定向修复

- run_id：`round6_p1b_fix2_20260917T0951Z`
- 执行：2026-09-17 09:51–10:05 UTC；纯本地 CPU，未 SSH、下载、加载模型、训练、标注真实语义或访问竞赛测试视频。
- 状态：**代码与离线回归完成；`UI_E2E_NOT_VERIFIED`。** 总控Agent告知当前浏览器的 URL policy 拒绝本地 `file://` 交付页，且禁止以 localhost、其他浏览器或 CDP 绕过。因此本轮没有真实页面截图，也没有浏览器真实下载文件；不能据此宣布 P1b 工程验收通过。
- 修改边界：仅 `round6_score_alignment/p1b/` 的工具、测试、说明；证据仅写本目录。未改旧报告、媒体、manifest、P1a、AGENTS/ROADMAP、生产代码或提交。

## 修复前复现与同输入修复后结果

详见 `repro_before.json`、`repro_after.json`。修复前将已有 10 fps 机器编号合成视频仅在请求元数据中改为 20 fps，取 64 返回了**实际编号 32**的图像，却报告 index=64、PTS=3.2 s。修复后同输入明确拒绝：`PTS cadence differs from manifest fps (VFR or wrong fps)`。P01 对 `[500,0,533.3333]` 夹框原得 `[1,0,533.33]` 且越界；现得合法框。重复 `sample_id` 草稿原被接受，现明确拒绝。前端旧图、异步覆盖和失败仍可留下精确溯源的问题，修复前依据实际代码路径留档；修复后通过交付页脚本的离线状态测试逐条验证，未冒充浏览器复现。

## 实现

1. `frame_server.py` 首次读取有界媒体时顺序解码全部帧，只保留最多 10000 个 PTS 的小索引，不导出帧文件。**索引位置即实际解码帧号**；后续按索引 PTS seek，并核对返回 PTS。校验媒体 SHA-256、帧数、尺寸、逐帧 cadence 与累计跨度。非零起始 PTS 和非整数 fps 已验证支持；VFR、错误 fps、缺 PTS、重复 PTS 等不符合当前协议的输入拒绝。8 条保留的 `pilot_dev` 媒体均只读取帧 64 做解码顺序检查，8/8 通过（`pilot_decode_checks.json`）。图像信息同时给实际 `pts_sec` 与 `nominal_sec`。
2. `annotate_template.html` 及重新生成的实际交付页 `annotate.html` 使用样本 ID、媒体 SHA-256、请求版本和帧号检查异步响应。切帧/切样本先清除旧图及精确状态。服务返回和图像使用同一份字节计算哈希；独立 Image 预加载成功后才替换可见图。HTTP、图像加载、哈希或媒体身份失败均不产生 `state.still`。端点按钮点击时即复制各自的溯源；手填端点按误差未知记录。实际下载函数已去掉旧 E2E 跳过下载的开关，并延迟撤销 Blob URL；本轮未能通过浏览器验证落盘。
3. `annotation_core.js` 在宽度量化后再次夹 x/y，四边和 16:9、9:16 的结果均满足最终边界。草稿先核对顶层结构、版本、manifest 身份、数组/对象类型、样本 ID 唯一性与媒体哈希，再原子替换状态；语义尚未完成的草稿仍可恢复。`validate_exports.py` 独立实现相应草稿结构校验。`pts_sample` 不再能声明误差 0；仅成功显示并核对过的 `decoded_frame` 可声明精确。
4. 导出增加 `seconds_semantics="nominal_frame_over_manifest_fps_not_decoded_pts"`。`start_sec/end_sec` 是帧号除以 manifest fps 的**名义秒数**，不是实际 PTS；Python 校验要求该标识。关键帧与区间仍以帧号为主键。

## 本轮独立验证

所有最终测试命令、退出码、耗时和尾部输出在 `test_results.json`，11 条命令均退出 0。

| 验证 | 结果 | 证据 |
|---|---:|---|
| 机器编号合成视频：顺序 64/65、错误 fps、非零 PTS、非整数 fps、VFR 拒绝、错误哈希/帧数 | 10/10 | `frame_tests.json`，`synthetic/` |
| **实际交付页脚本**的 Node VM 离线状态测试：64→65、切样本、响应逆序、加载中切样本、服务/图像/哈希/身份失败、四边夹框、草稿原子拒绝 | 30/30 | `page_vm_tests.json`；这是 DOM 模拟，不是浏览器 E2E |
| 既有共同边界样例：JS 与 Python 各自执行 | 28/28、28/28；逐例差异 0 | `boundary_js.json`、`boundary_python.json`、`boundary_compare.json` |
| 新共同草稿样例：JS 与 Python 两份独立实现核对 | 13/13 一致 | `draft_common_cases.json`、`draft_common_compare.json` |
| 8 条保留媒体的只读解码序号检查 | 8/8 | `pilot_decode_checks.json` |
| 离线合成接口样例经 Python 校验和 P1a 消费 | `valid=true`；稀疏仅 S01 为 `SPARSE_DIAGNOSTIC`，含未标注 S02 为 `NOT_COMPUTABLE`，两者 score=null | `offline_synthetic_export.json`、`offline_consumer_result.json`；**程序构造接口样例，非浏览器下载或人工标注** |

前述 28 例是本轮**重新运行**，但不能单独覆盖本轮发现的失败；新增 10+30+13 项针对性回归才覆盖关键链路。旧报告中的截图、下载 hook 和浏览器记录仅作历史背景，未计入本轮 UI 证据。

## 未完成的验收环节

`UI_E2E_NOT_VERIFIED`：无法在真实浏览器确认可见框移动/缩放、精确帧图像显示、切帧/切样本交互、两个端点设置后的真实保存、草稿刷新恢复、浏览器下载到磁盘及回读。因此 `ui_e2e/` 下无本轮截图与下载文件，**不能用离线 VM 或旧下载 hook 替代**。代码已为该流程准备好；浏览器门禁解除后由总控Agent按本轮提示词完成实际页面闭环。无真实语义标注，未进入 P2 或训练。

## 保护与资源

`protected_before.json` 和 `protected_after.json` 对 108 个保护文件逐字节 SHA-256 核对，路径集合和哈希均一致。`changed_files.json` 列出本轮 10 个修改/新增工具文件及当前哈希。`resource_record.json` 记录 GPU 0、8 条试点媒体只读、最终测试批次约 2 秒、8 条媒体顺序扫描合计 12.647 秒；本轮新增远低于 500 MiB，CPU 测试累计远低于 20 分钟。辅助服务未启动，无需停止共享服务。

工具使用说明已更新于 `round6_score_alignment/p1b/README_annotation_v2.md`。本轮执行到此停止，交总控Agent验收。
