# 新局部 refiner 激活消融的有界独立评议

结论：这是不同于已停止 base-only coarse selection 的新问题，不是复活旧失败方案。旧 12 源实验取消 TIME LoRA 做全窗事件选择，已经观察到 F1 劣化，STOP 和全部结果保持。新比较固定原 TIME-enabled B0 的粗事件、同一个短窗、原生 64 帧、文字和 finite-index grammar，仅改变局部 refiner 是否激活 TIME LoRA；B0 与 VERIFY 仍保持原 TIME-enabled。这能检验 coarse SFT 到新定位 schema 的迁移是否妨碍通用指令，但目前只是待检假说。

旧 smoke 的两个 KEEP 不是 adapter 妨碍定位的证明：原边界可能受画面支持，也可能缺清晰同事件转折。BASE 出现变化、更多 REFINE 或更少 UNKNOWN 都不是质量标准，不能据此选 BASE 或凑五包。

## 对照边界

- 原两个成功 native64 canonical 输入及首次独立输入证明直接引用；不重 decode、processor、原模型回答或原独立输入重放。新回答前核原 canonical SHA 与 CPU→GPU 完整输入签名。每次生成独立 prefill，不继承另一角色的 KV 状态。
- 唯一因素是 TIME adapter 激活状态。相同 actual loaded base/adapter SHA、prompt、采样、输入 tokens、grammar 可选值、确定性生成配置、输出上限、native conversion、KEEP/UNKNOWN/冲突规则和解析失败分母；不能只给 BASE 扩大选择范围或修复坏输出。
- physically loaded 8,782,459,120 参数，BASE activated 8,767,123,696；不是卸载 adapter，也不是新 base checkpoint。`disable_adapter` 范围内实核 144 LoRA 模块全部 disabled；结束后核恢复 enabled。VERIFY 与后续 coarse 的激活状态不能被泄漏改变。optimizer 为 0。
- 新 2 次激活消融调用独立登记、真实 raw/token/native output 重放，绑定旧已接受 input proof；不能重启旧 enabled smoke 两个成功回答，也不能把相同输入两角色答案当独立确认来源。

## 外部选择和确认

Charades dev 成对比较使用冻结的同一粗事件、native64 输入和同事件边界对应，最多 40+40 次真实请求。候选与参考对应、clear/ambiguous/censored 标准在 refiner 结果前冻结，不能挑“恰好 BASE 改了”的样本。报告逐角色和成对 clear-boundary 定位误差、方向错误、工程失败、UNKNOWN/KEEP/REFINE 分母及参考覆盖；多动作、越域参考或同事件不清仍 UNKNOWN，不当负标签。

dev 上冻结统一 refiner 角色后再用 worker-disjoint confirm 检验；这是 worker 角色隔离，不是所有人物/场景/household 或预训练独立。若要 START/END 不同角色或条件切换，须作为明确的新候选规则在 dev 中事先登记、全局冻结再确认，不能逐条参考选择角色或取两角色“最好”端点。

局部动作时间代理不能证明高光选择提分。原 40 KEEP/ORDINARY 风险证据、严重已知劣化 veto 和工程门继续生效；旧 coarse base-only 的失败不改写，新确认来源也不重新声称旧曝光 dev 是盲测。

这里只做评议，不授权 GPU 或角色切换，不读取新媒体/GT，也不增加数据或模型。
