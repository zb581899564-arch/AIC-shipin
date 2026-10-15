# 首次 metadata 投影失败的最小恢复范围

结论：现有接口允许在 INPUT_v4 内新增不可变 `registration_02.json`，不因注册文件改名而必须复制 input/runtime/control 全版本。这个判断仅适用于修复已有证据的字段适配或错误断言实现、并保持原 64 个真实原帧、像素身份、source 身份、算法、请求表及模型角色不变的情况。实际 visual64 失败原因由 source agent 独立定位，本审查没有重读预测、像素、媒体或重跑投影。

静态依据：

- `tp_io.registration()` 约束注册路径在 INPUT_v4 根内，没有固定 basename；注册中的全部依赖 SHA 和原 caller 目录每个 Python 文件仍必须匹配。
- `prepare_source.load_plan()`、`initialize()`、`consumer_api` 和 `pr_io` 按实际注册 path + SHA 闭合引用。controller 将这个真实路径传给 source 准备；因此新注册路径本身没有 ABI 阻塞。
- `project_legacy.main()` 先完成整个 `project(reg)`，随后才 create-x `plan_01`。主控本次回执为 plan/cache/formal 全零，不能将此次失败前的检查当作已接受 plan。
- 原 `build()` 会 create-x 原 bootstrap_run_01、重复 retain 三个 bindings，再写原 registration.json；它不是恢复入口，禁止再次调用整条原 build。

最小合法实现是新的独立 metadata recovery helper 和 continuation，放在旧 code 目录之外，不热改旧 125 个依赖文件。新注册需冻结全部原依赖与新 helper 的实际 SHA，并绑定旧失败回执、旧注册和具体修复范围。三个已成功 retained leaf 的原路径、大小和 SHA 直接复用，不重新复制、不覆盖。continuation 仅执行尚未成功的 projection、cache initialization 和后续 budget/protocol/batch/control 元数据；每阶段仍唯一 create-x，保留新的 launch/terminal。

恢复输出位置仍受现有根约束：首次未生成的 plan_01 与 cache_initialization 可留在 INPUT_v4；新 recovery 运行目录和 actual_GPU_budget 必须在 `temporal_production_bootstrap_v1` 根内，因为 runtime 对预算引用明确只准该根。不要为了另建 bootstrap_v2 而静默扩大 runtime whitelist。未来 source permission 与 controller permission 必须仍缺失，后续由 root 分别按新注册 SHA 首次签发。

若定位证明必须改变采样、raw/source ordinal 的含义、视觉身份标准、输入/输出 schema 或下游算法，则上述局部恢复不成立：需要独立新 input 版本及显式联动 runtime/control 根与协议。不能将 visual64 失败改为 UNKNOWN、跳过、用预测替换旧证明，或仅降低身份断言而继续。

本次只读审查没有执行 metadata、pure checks、解码、processor、cache 初始化或模型。旧 bootstrap FAILED 和旧注册继续保留；这份说明不是生产准入或科学通过。
