# 首批代码验收边界（2026-10-23，公开审计环境）

## 已实际执行

本轮在 `e8224c4339007790a1be383be19fdb200cc817bc` 新建独立分支实现。没有采用旧工作区快照覆盖当前源码，没有运行旧训练/推理来刷新历史结果。

| 检查 | 实际结果 | 能说明什么 |
|---|---|---|
| `python -m unittest discover -s tests -p 'test_final_sprint_*.py' -v` | 最终72项通过（其中最后新增的2项wrapper故障注入单独执行通过） | 原生时钟、模型参数逻辑/身份、失败与合法空、source/调用恢复、资源/资产绑定、确定性收据、完整性/封包契约、SIGTERM只清理本次子进程与累计预算拒绝 |
| `python -m unittest improvement.final_sprint_v1.test_spatial improvement.final_sprint_v1.test_specialist -v` | 28项中24通过、4跳过 | 精确几何、语义JSON解析、原生单元、模型失败不转空、无损float32缓存、token契约、参数收据与source返回接口 |
| 新目录与tests `compileall` | 通过 | Python语法可解析，不证明CUDA/API实际可运行 |
| CLI、bootstrap help | 通过 | 命令入口与参数解析可调用 |
| RUNBOOK的13个bash块、OPTIONAL_SPECIALIST的8个bash块；全部Python heredoc | `bash -n` / AST通过 | 命令文本语法成立；没有执行下载或私有资产调用 |
| Lighthouse公开源码固定checkout | commit `3e841d3d662c8440afed514908566fed2d5e82a7`，tree `271085c23c2619f0336186304e7eeb5be328e4cd`真实核验 | 只核验公开源码，不证明checkpoint、训练机依赖或质量 |

合计 **100项新CPU契约测试：96通过、4明确跳过**。这些全部是合成CPU工程检查，包含有意注入的失败，不是100次真实模型/来源验证，不是F1、IoU、Linux训练或官方成绩。

## 明确未运行

- 两份私有原ZIP/其真实依赖、426媒体、完整时钟/输入锁的现场SHA校验。
- 原TIME、monotone_head06、I3D、UMT实际CPU权重加载和库存；公开测试只验证规格及采用逻辑。
- 原Qwen3-VL8B模型加载、canonical冻结张量哈希、实际safetensors键对应、显存峰值。
- 实际PyAV codec/PTS与原色彩修复链；公共环境缺PyAV。
- 真实GrabCut/LK与完整空间链；公共环境缺OpenCV，4项检查因该原因跳过。
- 真实Qwen tokenizer前缀round-trip、native video timestamp callback、四候选缓存分支与完整无padding参考；公共环境无Torch/Transformers/CUDA。
- CLIP/CG-DETR实际权重加载、完整参数预算、GPU forward、模型质量；没有下载这些权重。
- 自有Linux当前可用GPU/磁盘/RAM、直连路由、全426推理和封包、最终传输、平台提交或成绩。

这些检查已落入Linux bootstrap/preflight/smoke/production/package/receiver入口，执行Agent无需重新实现主体。工程冒烟结果不用于F1筛选，不恢复旧科学门。

## 联审修复的具体生产故障

1. 参数/来源证据首写父目录缺失，已补不可覆盖写入前建目录。
2. 原颜色配置层级与全局转换字段丢失，现绑定原config并完整规范化；没有给新测试来源添加人工特例。
3. 同盘output+scratch峰值未合并、tmpfs被误当物理RAM、过期共享GPU授权可误用，现严格检查。
4. raw BASE只有形状/数量身份不足，现实际canonical冻结哈希；四辅助必须绑定原注册/原权重/完成收据。
5. 参数收据包含每次load不同耗时导致跨候选误判，已剔除非确定字段，运行耗时仍计账。
6. 不同语义词长造成右padding KV残留，现选中分支后crop，强制cache/逻辑token长度一致，真实数值QA仍待Linux。
7. CPU派生可因缺缓存意外启动GPU，现cached_only硬拒绝；父source文件必须等于持久成功调用，不能重新绑定被修改文件。
8. 完整返回值与后续failure共存时无法采用，现精确wrapper终态后另建adoption、保留原failure，不重新推理。
9. 模型加载被逐片放大、R/M缺新空间成本，现冷启动单列、全链成本估算，并在正常生产前5源后执行成本止损。
10. wrapper收到SIGTERM或写claim失败可能留下子进程，现只处理自己实际启动的进程组、wait后发布终态；超时受累计剩余额与最后4h预留约束。
11. normalized1000坐标浮点误越界，现用精确Fraction映射；不靠epsilon放过非法框。
12. 专家特征大JSON、重复源码manifest与每源完整参数清单浪费磁盘，现无损float32字节缓存、完整参数清单只存一次、全局asset lock固定完整spec，调用引用其SHA。

## 仍有实际风险

G主体语义与比赛构图偏好可能不同；GrabCut不足时保留已观测的语义范围，不编造像素支持；主体分散/无法包容时会采用有真实语义证据的场景策略，不能把这种策略当已证明更优。R词平均似然与阶段语法是固定解码先验，不是训练或校准后的高光后验；1ms保守DP有极短/VFR舍入风险。M作者任务域和自动查询可能不适合本赛题。任何路线都可能大幅掉分。

完整质量比较只来自未来人工正式整包提交，目标约43.5没有保证。保留/放弃算法仅用总分，不逐测试源反构规则。公共代码检查通过后，应直接完成一次真实工程冒烟和有界生产，不再花数小时新增一个不出包的本地质量评估闭环。
