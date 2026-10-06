# Revision 02 分数终点表示冲突

Revision 02 source lock SHA-256 为
`deacc114488c6412c33420a7a15bf3301c2461536960fdf7ca9881de9be3bb48`，
本目录保存其七个生产文件、source lock、processor test 和 27-case CPU receipt。
保存后逐文件字节 SHA 已与该 lock 校验一致。

总控以不涉及比赛内容的 synthetic case 独立复现：
verified duration 为 `739/60 = 12.316666666666666`，原冻结 parser 对
`{"segments":[[0,12.3167]]}` 返回 `[[0.0,12.3167]]`，errors 为空；
parser 先按原 `1e-3` 输入容差接受并限制到 duration，随后 round4 又使末端
大于真实 duration。新 native selector 按真实 endpoint 阻断，产生
`INVALID_NATIVE_PARSED_SEGMENT`。

Revision 03 只在 native 分支对原 parser 已接受、末端等于
`round(clip_duration,4)` 且大于真实 duration 的表示恢复精确 float duration，
保存 `LEGACY_ROUND4_NATIVE_ENDPOINT_RESTORED` 事件和 raw output。
所有其他 parser 失败、空结果、超过 5 段、明显超时、无 source-frame 段继续
阻断；CFR 使用原 parser 原返回值。本次问题不涉及质量、标签或模型选择。
