# Revision 03 shots CLI 入口失败

主控实际 NONTEST8 revision 03 temporal/select 通过，选中 396 帧；进入 shots
CLI 时，第 42 行 `sha(args.manifest)` 产生
`UnboundLocalError: local variable 'sha' referenced before assignment`。
Python 将 main 尾部 `sha=lambda` 定义为整个函数的 local，导致先于赋值的
manifest SHA 检查无法使用模块级已导入 `a_contract.sha`。未解码 shots 像素，
未完成联合 E2E。此真实失败保留，不以 temporal/selection 通过替代验收。

Revision 03 source lock SHA-256：
`94938aca8c47ad02068bebe9c8bfdb34e3219872bfe83d418fb3f48fc55eb0ee`。
本目录保存完整 source/snapshot/vendor/additional dependency 四锁，以及四锁
指向的全部 runtime 文件和原 CPU receipt。文件逐项与这些原 lock 校验一致。

本地 `cpu_cli_regression_attempt03_reproduction.json` 在真实脚本子进程中
复现同一 UnboundLocalError。首次 fixture 写入错误和后续测试错误消息断言
不匹配也保留在 attempt receipts，不能把这些测试开发失败写成生产失败。

Revision 04 仅删除重复局部 lambda 一行；summary 和入口都使用原已导入的
SHA-256 文件函数。shot 算法、阈值、源 frame ordinal 与 pixels 均不改。
`infer_anchors_pts.py` 不存在同类赋值/导入遮蔽，源字节保持不变。

新的完整 CLI 回归执行 CFR 和 mixed native main、比较冻结 vendor 的输出
字节，并验证异常 manifest/hash 在 decoder/model 之前阻断。其 decoder I/O
为可区分帧 controlled synthetic 替身，不替代 main 的独立 lossless actual
codec 验收；正式 NONTEST8 仍须主控在新 run 中全部重验。
