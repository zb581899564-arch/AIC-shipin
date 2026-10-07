# v5：用户授权的高光价值定义修正

用户在 2026-10-07 明确要求“那你去修正，然后完成后续”，采纳 controller/TEACHER_RECIPE_DECISION_20261007.md 的提示词修正小试路线。旧 v4 的 160 个回答、全正例偏置、科学门 STOP 保留，不修补、不混入本版本训练。

本次唯一科学改动：高光从“可解释的活动”明确为“值得保留的可见关键内容”。普通活动可以不选；关键动作结果、反应、显著有意义变化或新信息须解释保留价值及边界；无充分观察证据则不确定。teacher_prompt.txt 和 review_prompt.txt 同时绑定新定义，没有固定正负比例或段数要求。

128train/32dev 自然窗口、来源隔离、64nativePTS采样、固定32B Q4_K_M与F16投影器、运行时、实际grammar、原独立validator规则不变。supervision 内 validator/select_windows/schema/教师身份文件与原文件逐字节相等，仅 teacher_prompt.txt 变更。显式绑定新提示词目录，防止 Python 模块缓存引用旧 HERE；输出 guard 只允许新版本确切输出目录。

小试在读取任何新标签前登记：各 split 按 SHA256(window_id) 升序，取8train/4dev，旧标签和测试内容不参与选窗。12条全部原样留档，经原独立validator。工程错误、全正/全空、各split没有有效观察、系统性整窗全选或真实弱复查拒绝都 STOP。小试只要求观察到可解释正例和真实空例各至少一条，不要求两split都出现空例，不删不确定/超段回答凑通过。每条可训练观察都由同32B真实第二次复查；这些是弱证据，不能视为独立共识或人工真值。

小试通过只授权全量新配方标签，不能开训。12条同提示词成功字节在该版本原样复用，另有两条实际重输入工程探针，最后160条逐SHA与原validator复验。完整 train/dev 各有真实正与空、非全空/非整窗全选、3epochs内至少20更新、全部eligible第二次审核等原科学门保持。失败、UNKNOWN、未观察间隙不转空；超5段原样排除，不剪裁。

工程改动：学生输出/20更新checkpoint重载所有权从写死v1改成本版本目录，真实路径合同验收；重输入probe的admission父引用不再被后续cache检查覆盖。模型、优化器、学习率与训练协议保持：从37.63的B最终LoRA继续，r16/alpha32/dropout0.05/lr1e-5/batch16/最多3epochs/seed20261007，20更新真实CPU重载→固定弱开发选checkpoint→NONTEST8→426推理/空间→独立strict ZIP。

使用实际容量与共享GPU锁/追加账本，不设人为磁盘/RAM/VRAM额度、不抢占外部任务；不读100confirm、不手看测试调参、不重新使用Mac。中间及最终ZIP留Linux，没有自动回传、额外权重下载或官网提交。只有 PASS_AUTOPILOT_FINAL_T_ZIP_ON_LINUX 加426独立strict全部通过、大小/SHA/CRC核验后才能宣称可提交。
