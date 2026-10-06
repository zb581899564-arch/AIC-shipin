# P1a 总控验收

日期：2026-09-17；状态：`P1A_CHANGES_REQUIRED`，暂不进入P1b/P2。

## 实际核验

总控独立执行 `python -B -m unittest discover -s round6_score_alignment/p1a/tests -t round6_score_alignment/p1a`，83/83通过。另检查scoring.py、compose.py、timebase.py和数据试点建议。未运行会覆盖原报告的run_p1a.py；174/174历史重放本次仅核对执行报告，未独立重跑。不访问远端，不使用GPU或测试媒体内容。

## 阻塞问题（已用合成输入复现）

1. `scoring.load_reference` 使用 `record.get('frames') or []`，把缺失字段和null与明确空数组混同。单视频、合法空预测、full参考只有 `{'video_id':'0'}` 时返回OK、100分。违反缺参考不能当空真值的要求。
2. 同一函数没有拒绝重复video_id，`videos[vid]=frames`静默覆盖。先声明一条frame=0真值，再重复同ID写空frames，配合空预测也返回OK、100分。必须在载入时失败，不能选首条或末条。
3. sparse分支在计算完整per_video之后才返回，仍含precision/recall/f1/time_f1、unmatched_predictions、both_empty等全视频语义字段。总score=null并不足够：稀疏标注不能把未标注帧当负例，也不能据此判断整视频空。

## 其他必要修正

- `SOURCE_SHOT_INTERPOLATION`实际执行同镜头最近框复制，没有两端线性插值。建议准确改名为 `SOURCE_SHOT_NEAREST`，保留距离限制；本轮不要趁机实现新算法。
- 新compose遇INVALID只记录后continue，顶层无失败状态；必须提供明确失败/不可交付状态，调用入口非零退出或阻止下游交付。合法空应继续是成功，缺空间应明确不可交付，不与空混淆。
- `DEVIATIONS_FROM_VENDORED`中“duplicates ... through the first valid record only”的描述与实际所有重复均计分母矛盾，修正文案与协议。
- 报告“只差1帧”须准确为1条视频、移除1帧且新增1帧，对称差2帧；不是只改变一条帧记录。

## 数据路线裁决

不接受“没有人工就只能交空表”的绝对结论：可以先盘点远端既有非测试媒体、许可证据，准备标注工具/清单，或建立明确标为弱标签的辅助诊断；不能据此宣称可信全视频联合分或通过质量门槛。计算媒体哈希能固定身份，不证明标签与媒体已对齐。P1b实际任务待本轮修复验收后再委派，避免现在消耗GPU。

## 下一步

仅修复上述既有模块边界，原始报告与首次83项结果保留。交付路径与验收要求见 `prompts/round6_p1a_fix_handoff.md`。这次修复不扩大成重写评分器、下载数据或训练任务。
