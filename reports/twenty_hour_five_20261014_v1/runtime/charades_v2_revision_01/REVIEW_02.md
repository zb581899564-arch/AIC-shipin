主控已裁决按 `reports/twenty_hour_five_20261014_v1/charades_partial_native_scope_02.json` 的作者秒级端点 proxy：资格仅为严格 `0 <= original_start < original_end <= actual_physical_end`，不能额外要求 PTS 落入短区间。

02 只修改 `_validate_reference` 的这个额外门。无 PTS 的落域 action 仍 FULLY_IN_DOMAIN/scored，`contains_native_frame=False`、空 `native_range` 和单独 count 是诊断；不称可见高光核心或 dense native-frame GT，不准把 partial union 当完整整源 GT。原作者文本和所有旧引用逻辑保持。

01 原代码已原样保存为 `charades_cpu_draft_01.py`（SHA 4782975311156f400d5a4b3f80166745e0b87431986e8b7d2ccd06cc07b6ad98），01 manifest/purecheck/review 均保留为被本裁决修正的草稿。没有重复运行成功的 01 合成检查。

02 仅对新增两个短 action 案例做 Linux 纯检查：前帧间隙 [.0100,.0200) 和实际末帧 duration 内 [3.1700,3.1900) 都落域但 PTS membership 为空，保持 FULLY_IN_DOMAIN，原文字不变；AST 通过。真实媒体/cache/processor/model 全为 0，业务文件尚未由本代理部署。独占文件和所有物理 native64 工程门不变，由 temporal 代理部署/登记、主控审查后才运行。
