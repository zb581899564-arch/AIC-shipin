Charades v2 CPU 代码已完成，真实准备与 GPU 准入仍为 0。

唯一新业务文件是 `improvement/charades_native_v2/charades_cpu.py`。公共接口保持 `prepare_source(source, media_receipt, reference, source_out, bindings)`。新 common 使用 `charades_v2_common`，冻结的 LB v1 两份 gzip helper 和 Charades v1 CPU 文件均未修改。

继承源必须通过 `existing_native_clock_path/sha256` 绑定旧完整包装中的 `clock`，同时核原媒体、源身份、原作者参考元数据 SHA；直接返回旧 clock 路径，绝不解码。带 `existing_CPU_completion_path/sha256` 的两个源检查旧 completion、每份 proof/input/tensor/NPZ 的 SHA、完整窗口和原生帧身份；在新 scope 只保存 launch、clock reuse、reference validation、windows 和 completion 小文件，保留旧 case ID 与所有大缓存路径，不重新 torch load、processor encode 或 RGB decode。

逐条 action 保留原始 class/start/end 文本及完整 original_action。完全位于实际物理时钟且含原生帧的 action 为 FULLY_IN_DOMAIN；越域、无帧、非正区间或不可解释端点为 CENSORED_UNKNOWN，unscored，不能当普通或官方 ongoing。空动作/零 eligible 源照常保留。非法参考容器/文本类型是 metadata STOP，不是 NativeEndpointError；物理 clock/native64 工程门仍严格，内部窗口和原 B EMPTY_PROMPT 不使用作者 action。partial union 明确不允许当完整整源 GT 计算 P/R/F1。

一次 Linux 纯合成检查通过：AST；1 eligible+5 censored；原端点文字不变；空/零 eligible 保留；3 个物理 clock 拒绝；metadata 错误不转可替补工程失败；模拟旧 CPU completion 引用保持、decoder/processor/runtime 调用均被禁止且没有触发；重复成功 completion 直接复用；破坏合成 tensor 字节后拒绝。未读取真实媒体或缓存，未部署此业务文件，模型调用为 0。真实旧 proof schema 与资源时长/RSS 尚待主控批准的登记/准备过程核实，纯合成检查不证明真实 CPU 输入或模型质量。
