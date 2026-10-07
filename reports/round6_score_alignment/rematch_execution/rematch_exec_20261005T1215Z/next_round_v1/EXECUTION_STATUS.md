# 修复与实际执行状态

## 下一轮v1已实际启动（2026-10-07 11:00 UTC+8）

用户采纳新结论，授权先修代码、制定路线并执行。新独立入口`next_round_v1/CONTINUE.md`、协议`PROTOCOL.md`；旧37.63 Linux B及Mac包/冻结运行文件不改。Linux103文件源锁SHA`9a4159496083dfa36cbcae703644aea1a44d1e31c6ac0f3c29627e5fd0f9e8e2`，主控历史启动PID2234812、Windows独立交付等待PID60188，须实时核活，不重复launcher。

145项Windows/Linux CPU合同通过；真实processor1/63/64帧及HD和旧默认逐张量相同（旧B提示64HD=12048token、实际372736像素/帧），显式视频size4096/25165824和统一16384界，无截断。全空426通过独立strict的11检查；真实CUDA合成空兼容生成为LEGAL_EMPTY，空assistant CE loss=1.6668949有限，head/full各自原生PTS context通过，峰值20312.43MiB，0optimizer更新。这里只验工程，不宣称新监督/质量通过。

代码修复覆盖严格0..1000整数中心、空/失败分离、空assistant目标、CFR/native选帧、完整源镜头/空间场先插值后筛时间；B/Z开发同production解码及同encoded窗口。Z保留B的1..5段提示做原生8B对照；T取得真实完整观察监督后才用0..5段与lr1e-5/最多3epochs，不重复旧LoRA延长训练。Z相对旧B同时改变坐标与镜头边界，官网比较应按整套配方解释。

Mac占用预留28GiB、共享临时1GiB、Linux当前实占+当次产物<=51GiB，80GiB合计不变；Linux无Mac心跳TTL等待，传输仍实时验证Mac并经跳板。按一次性控制器自动合成探针→开放104/96 B/Z诊断→NONTEST8完整门→426 Z时间/全源空间/strict封包/经Mac回传；没有delivery_completion PASS前不能宣称Z包已交付，不自动官网上传。当前已实际通过合成GPU探针，后续以progress/completion为准。

监督原128/32选择v1实际遇到duration-only尾格而STOP，保留证据，独立supervision_v2只修最后真实非空PTS格选择并保留不可采样时间格；实际提供帧、教师响应前无新标签。32B教师需20958945472字节（19.52GiB），现行余6.46GiB，T仍STOP_32B_TEACHER_CAPACITY，未下载/训练、未用8B替代。S缺已绑定双比例人工构图参考，登记STOP，不用弱ROI冒充构图真值。C正式BCE未知负语义STOP保持。

用户问本地评分：不需要本地复刻AIC总分，官网每日最多5次、最终取复赛阶段最高有效分；仍保留非测试机制/弱教师实验比较、格式、源帧身份和失败检查。内部F1不是官网分，不以其CI>0作为新Z工程门。100confirm不读，不按手看测试内容改参数。

