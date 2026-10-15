# 同输入 BASE 局部角色静态审查

只读审查 `bd_contract.py`、`bd_io.py`、`driver.py` 及 BASE37 controller 的 closure；没有执行 source gate、旧 pure checks、processor、cache replay 或模型。driver `77a184dddc9e1efe2250e6f8e7087e8af9aade56862339596568129652cce26f`、contract `c96d1f4c1005544bb5ed670dc29650b534c642cf2dd44547fab384b2993f31bd`、含新 controller root 白名单的 io revision02 `bc1590ef72837e6592d22b2a674589e180f6184e527e23851ec84428887fc6c8`。实际部署和在跑任务状态由主控负责。

在当前审查范围未发现阻断 driver 问题：source_bundle 绑定 TIME 自然 completed 与首次 37 input/output replay，保留 20事件/40名义端点/37实际/3预登记短侧。BASE 使用原成功 canonical 输入及同 prompt/grammar/采样/native 语义，CPU→GPU 完整签名相同；新 generation 独立 prefill，不带 TIME 答案或 KV。真实 144 层激活状态逐次 False→True→False；物理参数 8,782,459,120，BASE activated 8,767,123,696，adapter 留存未卸载。PEFT context 退出后显式 `requires_grad_(False)` 并核所有梯度冻结；全 base 与 288 adapter tensor 值 hash 在 job 前后核查。raw 在解析之前保存，坏输出不转 UNKNOWN。新独立输出 replay 仅 tokenizer/token/grammar/parser/native 元数据，复用首次 input proof，不再次 encode/load RGB/cache。3个 short skip 保留原点和独立几何 proof，不伪造模型调用。

controller 顺序为 TIME 自然终态→完整 source_bundle→首次注册/锁→独立 consumer 检查→唯一 1500s/8MiB shared wrapper→新 output-only replay；动态资源快照不写死 RAM/GPU GiB，parent CUDA=0、CPU child CUDA 空。其静态 event-wait 有一个未来竞态：`controller.py:58–62` 任意 GPU/replay completion CLOSE 都令 `closed_terminal=True`，随后严格读取 chain completion；若 chain 此时刚 create-x 但未 close，可能将 partial JSON 判作失败。应只在实际 chain completion CLOSE/MOVED 时严格读取，其他 wake 保持 tolerate_incomplete。这一项已反馈作者；当前已跨过 TIME gate 的任务不因潜在竞态改锁、重启或重复成功阶段。

固定 prompt 要求同一原候选、内侧锚点、明确窗内前后转换；更激烈阶段、镜头切换和不清身份不能当边界。因此 KEEP/UNKNOWN 可能是正确保守响应。原 B0 interval 没有唯一人物/视觉实体描述，角色无法保证同事件；finite grammar 中 KEEP 比 REFINE/index 更短以及 coarse 秒区间 SFT→native-index 迁移是可检验的偏置假说，不是已经证明的 adapter 机制。BASE 更多 REFINE 不构成质量证据，不能催促模型改变、按变化率选角色或用正式测试/排行榜调整 prompt。

metric08 固定可达 paired geometry 为 0，默认 TIME；本 BASE37 只能声明同输入 activation 行为对照，不能科学角色优胜或高光质量 PASS。旧 base-only coarse12 的严重失败不改变。未来独立全局 BASE 局部风险范围必须预登记，B0/VERIFY 仍 TIME，工程和已知严重反证 veto 保持。
