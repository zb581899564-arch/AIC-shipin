# P1b 用户实际页面冒烟验收

日期：2026-09-17。状态：`USER_UI_SMOKE_PASS_REFERENCE_E2E_PENDING`。

用户在本地浏览器打开 `round6_score_alignment/p1b/annotate.html`，截图显示 P01 视频可播放、页面渲染正常；用户随后报告画框、切样本、精确取帧 64→65 和草稿下载均成功。以上交互结论来自用户报告，本轮无法由代理读取受策略限制的本地浏览器页面，不能称代理独立重演。

本轮独立检查：本机 127.0.0.1:8765 监听；`/health` 返回 ok=true、loopback_only=true、8 样本、PyAV CPU。读取 P01 的 frameinfo，64/65 请求分别返回 index 64/65，PTS 2.669333/2.711042 秒，带媒体和图像哈希。

Chrome 下载 `C:\Users\33056\Downloads\p1b_draft (1).json` 存在，SHA-256 `052c6635e38692e9531f49863e83d94a3791de6e0cb5c5402028d09326b`。按当前 pilot_manifest 和 `validate_exports.draft_problems` 校验无问题，schema=`p1b_annotation_draft_v2`、core=`p1b_core_v2`、8 样本。其中 P01 标注者字段是 `UI-test`，8 条状态均 `UNANNOTATED`，因此这是工具测试草稿，**不是高光真值或训练数据**。

仍未完成：实际浏览器导出有效参考文件、下载回读、P1a 消费；真实语义标注及复核均 0。进入 P1b 人工试标前，需要明确标注任务与复核人，先 2 条来源组（目标16:9和9:16各一），再决定剩余6条。稀疏构图框只能用于稀疏诊断，不生成全视频联合分。不得据本轮工具冒烟结果声称提分或进入训练。
