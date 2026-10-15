# 家族 renderer 有界静态审查09

仅实读本地 `improvement/temporal_family_v1/package_family.py`、`combine_events.py` 及 Linux 原 `field_contract.py`、`package_contract.py`、`pts_contract.py`、vendor `p2j_core.py`、`independent_validate.py`。未读测试媒体/GT、未执行封包/processor/模型。Linux身份为 `inspur-NP5570M5`；只读资源/活动任务核查后读取小代码，未干预现有 VERIFY GPU任务。Windows不存在对应 field contract 本地副本，所以实际接口以 Linux 原代码为准。

已核正确：`compose_from_field` 首参是完整 manifest dict，`legacy_manifest` 的显式投影满足历史空间 schema；返回三键预测后添加 `model_params_b=8.78245912` 是必要且正确的次序。原 spatial contract 会校验整个冻结场的 shots/anchor SHA、固定 max-gap-8 日程、同帧像素身份、合法 anchor/interpolation，再取 selected，未选 anchor 失败也阻断。renderer逐保留 D8 frame 核原框相等；新增帧也必须来自原自动 full field。原整数 bbox 类型与排序由真实 `p2j_core`/contract约束，canonical去掉参数/名称且包含帧与框，能拒绝基线及家族实际重复，不能靠改ZIP名凑包。

空 source 事前格式 guard 自动恢复该 source 原D8，逐source披露，不能把工程失败转空。combine完整 endpoint/VERIFY集合、原事件长度决定D8 pad、冲突保原、保留事件区间 union 的处理正确。实际11 strict 是独立 subprocess 调冻结 loader，外加单成员 CRC/字节 SHA 再发布；它是工程格式检查，不证明时间/高光质量。

主控已根据前次反馈加入 renderer 依赖根和原production accepted_export_refs四投影的强绑定、实际 endpoint/event/source IDs 对齐。随后初读指出的三个具体缺口也已由主控修复并实读确认：

1. 实际 `package_contract` 把 `baseline_a_pts_v1/vendor` 插到 import path 首位，真实 `p2j_core.py` 位于 vendor；bscore目录没有该文件。最终 required 已包括 vendor/*.py 和strict-loader递归py，补齐原来漏掉的vendor实际依赖。
2. 最终renderer新增每源完整PTS数量与metadata n_frames/sourceSHA/path/videoID一致的断言，并要求新 `LAST_NATIVE_FRAME_PTS_PLUS_POSITIVE_DURATION` witness 与production端点witness逐source一致，不能拿legacy CFR n/fps作新实测证明。实际 witness 的正duration/clock数学和原完整PTS对齐仍须由生产独立验收完成，而不是该字符串断言自行证明。
3. 最终renderer新增 production.frozen_development_selection_ref 与inputs.development_selection严格相等，并读选择文件核 global_refiner_role/global_VERIFY_role 与production一致，冻结全局角色文件不再仅作为无作用附件。

最终只读快照 renderer SHA `a985790c7db0e88af054c756917405e9ced5ade275b91cf50cba7723067aeb51`，combine SHA `0b9ce6f9a0dad339a50d4c7ab199bce0c0c5b14cce9b41f5062ced3283f44108`。没有发现上述接口范围内尚未修复的代码阻断；没有执行实际metadata或证明新生产schema已真实生成。准入时应核提供给strict-loader的metadata与source_manifest同源同尺寸/帧数/比例，不能只靠ID集合一致；这是同一来源合同核对，不是新媒体/模型实验。

时钟范围需要事前协议精确说明：真实 `pts_contract.legacy_manifest` 对 NATIVE_PTS 将scope投影回n/fps，只是空间旧validator兼容；它不控制新时间映射。新的 combine 对全部source用 exact native PTS半开 `[a,b)`，历史旧 `pts_contract.select_frames` 对 CFR 分支用float ceil算术。合成 KEEP→D8全122050 frame重建是有效必要拒绝门，但只证明原端点保持，不能宣称所有新端点下两种算术恒等。新生产应固定实际native cut/末duration语义及原clock对齐，不为了重建失败调整映射、epsilon或逐source规则。

本回执不是包准入或质量PASS。实际生产完整自然终态、唯一账本、首次独立输入/输出重放、完整源clock/field、风险与已知严重劣化否决、当前规则核对、正式11 strict及最终实际差异仍由主控在真实数据上完成。旧失败门与所有成功证据不改，不把5个组合名当5个交付。
