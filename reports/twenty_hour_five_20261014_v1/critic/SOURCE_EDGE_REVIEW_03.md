# 源边缘 inward 精炼的独立批判

已实际读取 `lb_contract.plan_endpoint/resolve_endpoint`、`prepare_local_inputs.continuity` 及独立 `replay_local_boundaries.independent_endpoint`。当前实现将原start=0或end=physical_end的缺原点外侧画面和cut0/len连续性判据统一转UNKNOWN，这会否决一些本来有完整窗内新切点对照的inward修正。

根任务提出的revision03在数学上成立：源起止的合法性应由已验完整源clock及规范化映射、首PTS/正末duration确定；可否修正则依据所选新切点两侧的实际可见上下文、相邻native duration连续性、内侧锚点与同事件语义。源边界之外没有画面，不意味着源域内部的新切点也缺少外侧对照。

纯contract合成例已运行，见 `source_edge_contract_review.py`。它不读取媒体，不调用processor或模型，也不改同伴文件及已成功gzip检查。

| 例子 | 源/原候选 | 内侧锚点 | 选中样本及新端点 | 窗内对照 | 原实现 |
| --- | --- | --- | --- | --- | --- |
| start源边缘 | 合成25fps源[0,10)，原候选[0,4)，短窗[0,3) | 1秒 | index14，ordinal16，首纳入PTS=16/25=0.64 | 前样本0.60、后样本0.68；cut前相邻duration=1/25 | UNKNOWN_NO_ORIGINAL_OUTSIDE_CONTEXT |
| end源边缘 | 同源，原候选[6,10)，短窗[7,10) | 9秒 | index49，最后纳入ordinal232/25=9.28；半开end=下一PTS233/25=9.32 | 下一可见样本从9.32开始，后面还有9.96；所选末纳入帧duration=1/25 | UNKNOWN_NO_ORIGINAL_OUTSIDE_CONTEXT |

两例的原sourceedge合法、1..62非边缘index、chosen cut的外侧可见、native连续、只向内移动且锚点处于保留侧。若假设同一候选内容在该新切点转入/转出，几何上不需要原source0之前或10之后的未知画面。此数值例证明原guard太强，没有证明模型在真实画面上会正确识别该转换。

重要反例：录制从0开始时同一动作已经持续，0.64只是更强烈的一段；或者同一动作持续至10，9.32以后仍有同一动作。此时几何可通过，窗内外侧仍属于同候选，语义并未支持开始/结束，因此仍应UNKNOWN。修正不能称恢复了源域之外的真实动作起止，也不能把观测窗、镜头切换或采样密度当语义边界。

建议冻结的具体约束：

- 只为已认定的精确源首0或物理末端设一侧合法性分支；内部原点仍需旧strict bracket/duration证明，不泛化撤去原点连续性检查。
- chosen index只准1..62。源首start修正须严格向内；源末end修正须严格向内。原点外移、超源域、内侧锚点错误、chosen continuity未证或同事件/转换不清，均保原并记录UNKNOWN原因。
- end index指最后纳入帧，应映射到下一nativePTS。外侧对照可以从这个exclusive point恰好开始，因此不能要求新end严格小于下一可见samplePTS而错误挡住第二例。
- 源首0按已验normalized clock与原origin映射认定；不能额外用literal rawPTS=0否定已有合法非零raw origin规范化。源末继续用已验正last duration，不使用容器名义duration或epsilon。
- prompt、实际meta、解算和独立CPU replay应同时改成chosen-point语义；旧 `has_original_outside_context` 可以保留为诊断描述，但不能单独作为所有REFINE的否决项。

这属于尚未真实CPU/model之前的数学语义修正，应先冻结revision03再执行，不以第五包数量、原actionGT或任何测试内容决定规则。工程解析失败仍阻断；UNKNOWN必须是有效生成或事前明确的语义保护决定，不能掩盖模型/输入失败。
