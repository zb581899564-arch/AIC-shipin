## 只读审查结论

审查对象为 `improvement/charades_coarse_v1/coarse.py` 的首次草案；本审查未部署、准备输入或启动模型。

实际 blocker：生成的 `request.json` 没有 `case_id`，而 `local_boundary_v2/plan_local_inputs.py::accepted_event` 强制核 `request['case_id']`。须写入原 case 身份，否则所有非空 coarse 候选进入边界计划都会失败。

另外两处准入依赖需要闭合：coarse 的允许输入路径含 `charades_boundary_v2`，当前边界 v2 的 `EXTERNAL_ROOTS` 只含 `charades_boundary_v1`，未来需要独立新版本显式加入第二根；不能覆盖旧 v1。coarse 的必需文件集只强制自身、输入表、协议、规则和配置；主控 source lock 还须实际冻结 runtime、缓存 helper、模型 engine/contracts、grammar/GPU reservation 代码及 processor assets，否则省略依赖也能通过当前必需集合检查。仅有文件被列入并实际 SHA 核验时，才称锁定。

循环只在 infer 开始核截止时间。主控已澄清本 Goal 的截止语义为截止后不启动新实验，截止前合法启动的同一冻结 job 可自然完成。因此不要求逐 micro-call 截断；主控须在 protocol/admission 明示该语义，并据剩余时间及 wrapper max-seconds 预算准入。

已覆盖的关键行为：每次生成前核 144 个 LoRA 模块全部 enabled；核实际 base/adapter SHA 和 8,782,459,120 参数；真实 token decode、有限 score 分母、完整 grammar、允许合法空结果、半开原生帧成员均有实际断言。GPU 复用已接受无损缓存且核 CPU/GPU tensor signature。独立 CPU 重放重新从保存的真实 RGB 编码核同证据，并核 token/parser/native；不加载模型。重放需唯一自然完成 ledger/resource，按顺序核每窗一个 BEGIN/ACCEPTED。合法空结果不转为工程失败，不用于凑候选数。

这些是代码审查发现和已覆盖条件，不是模型质量、运行终态或封包通过证明。

## 主控修复回执

主控已修复 request 的 case/source 字段，并增加实际 dependency roots 和 processor assets 的必需锁；GPU admission 还会核解析器、预约函数的实际 module path。Charades 第二根 whitelist 在当前 smoke 完成后用独立 v3 支持，不覆盖正在运行的 v2 smoke 锁。
