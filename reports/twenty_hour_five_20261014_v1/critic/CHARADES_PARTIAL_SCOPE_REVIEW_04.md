## 独立结论

`charades_partial_native_scope_02.json` 可用于有界的内部动作时间诊断。旧 whole-domain 标注门仍保留 FAILED；新范围完整保留作者原区间，只把完全落入实测原生域的区间列为可评分。越域区间记为 censored UNKNOWN，不裁截、拉伸、加 epsilon，也不作普通内容负标签。无有效区间的来源留在原来源及 coverage 分母中，不据标注数量换源。

当前作者证据只支持动作 start/end 为秒数时间区间，不支持官方越域容忍或官方 censoring 约定。作者 ZIP 内 `Charades/README.txt` 的 `actions` 字段及小数示例，和论文 §2.3 的动作起止标注说明一致。论文、README 未发现整数粒度保证、原生帧精度保证、越域误差容忍或 clip-edge ongoing/censoring 定义。新 UNKNOWN 口径是本研究的保守测量约定；不是作者批准域外 GT 合法。[作者原说明](https://prior.allenai.org/projects/data/charades/README.txt)、[第一方论文](https://ai2-website.s3.amazonaws.com/publications/hollywood-homes.pdf)

冻结的 coarse 候选先与参考建立对应，再看 refiner 回答。只在能确定同一动作且不与 censored/不可区分动作重叠的边界上做局部定位统计；对应失败或语义不清也要报 UNKNOWN 与覆盖率。不得用有效区间并集算整源 precision/F1，因为剩余区域缺少合法负标签。该数据仍是动作时间代理，不是高光选择真值、密集原帧真值或空间框真值。原 40 KEEP/ORDINARY 风险证据另行保留。

本审查没有新增网络、媒体、处理器或模型调用，没有改任何运行链、协议或原标注。
