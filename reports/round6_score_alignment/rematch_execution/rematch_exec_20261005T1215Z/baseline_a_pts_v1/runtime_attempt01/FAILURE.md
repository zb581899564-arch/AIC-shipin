# Revision 01 单帧 processor 限制

总控在 Linux 既有 `qwen3vl_isolated_20260910` 环境运行 actual installed
Qwen3-VL Fast processor，`real_processor_01` 的 3、63、64 帧均通过。
单 physical frame 被 processor 的 spatial/temporal resize 验证拒绝：
`ValueError: t:1 must be larger than temporal_factor:2`。

此结果证明 revision 01 的假 processor 单帧测试没有覆盖实际输入长度限制，
不能将四 case 测试视为通过。总控 receipt 为
`controller/a_pts_processor_01_receipt.json`，SHA-256
`2dd16247a3483b06e1cba96cf09a9189f6e3f16304cc8abe64fce4bb589f6e37`。
本目录保留当时两个待修 runtime 文件、source lock 和 actual processor test。
旧 source lock SHA-256 为
`22db6136f977903530bff43145f1c81669ffc17b671cc400560d6a7aad5e816d`。

Revision 02 仅在 native context 有一个 physical frame 时显式复制该像素输入
一次，processor metadata 只重复同一 source ID，两个时间相同；记录唯一
physical IDs 和 padded processor IDs。其余奇数长度仍由原 processor padding。
这是输入表示修复，不增加 source frame，不增加时间或改变 segment/output。
新的实际验收需在独立 `real_processor_02` 中复现未 padding 单帧失败，并让
padding 后的 1、3、63、64 帧全部通过。旧 attempt 不覆盖、不删除。
