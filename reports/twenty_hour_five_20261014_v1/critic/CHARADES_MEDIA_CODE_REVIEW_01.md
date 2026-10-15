# Charades 媒体链的轻量只读审查

已读取 `improvement/charades_native_v1/archive_member.py`、`pipeline.py`、`charades_common.py`，并补看 `charades_cpu._windows` 与输入编码段。未改同伴文件，未执行媒体或CPU链。

未发现206、CD偏移、CRC/SHA、替补或标签选窗的核心false-pass：

- body读取前要求HTTP206、冻结If-Match/ETag、精确Content-Range及Content-Length，不接受200整包或替换publisher。local header的名称、flags、method、CRC、压缩/解压尺寸均与冻结CD匹配；数据起点从固定30字节加名称和extra长度计算。raw deflate要求eof且无unused/unconsumed数据，原MP4尺寸/CRC与CD一致，并保留文件SHA。
- 目录/单个来源唯一claim阻止重复启动和成功下载重做。网络、压缩、processor等普通错误进入整个链STOP；只有明确NativeEndpointError或已知/重复字节身份冲突可按既定替补推进，原失败与媒体/完整clock保持。
- reserve按原排序选择首个未使用、无已知别名、worker不跨dev/confirm的来源；不按模型回答或标签质量挑源。允许同一worker在同一role内出现，因此“worker groups disjoint”只代表跨组不相交，不能额外宣称每组十个独立worker或全部可见actor独立，须按实际registry统计描述。
- `_windows`仅依完整物理clock等分<=30秒及floor64原生序号。actions只做未经修改端点的物理域/schema验证，不给窗口中心或prompt答案；请求为原EMPTY_PROMPT且reference_available_to_inference=False。

已向主控与同伴报告一个实际协调风险：`charades_common.CACHE_DEPENDENCIES`、CPU的HELPER_FILES及已写registration绑定了Linux `local_boundary_v1/code/lb_contract.py` 和 `lb_io.py` 的旧SHA。正在讨论的boundary revision03若覆盖同一Linux路径，会在verify_registration或CPU helper检查触发changed，甚至在CPU完成后破坏后续证据绑定。应给revision03使用新不可变版本路径，或在新协议中引用保留的冻结旧helper副本；不能静默修改旧registration01/SHA冒充原锁。目前据同伴回报媒体/CPU仍0，尚有事前修正窗口。

另有有限记账问题：`range_bytes`只在完整成功后写HTTP全局记录；失败请求保留partial和failure，但失败的requested/received字节不进入该成功列表。原链会停止，因此本轮不会自动利用缺失记录继续超预算；后续显式恢复应记录失败partial实际大小和请求区间，不把已消耗流量忘掉，也不能重发成功部分。

原ZIP总量58,807,341,227B不等于成员是ZIP64 local header：本实现对local descriptor/ZIP64成员明确拒绝，不解析修复。若实际CD标志显示这种不支持格式，应在媒体前登记阻断，不能把HTTP或格式错误当质量替补。当前审查没有重新请求任何headers或body来判断它。

本审查不构成模型/媒体结果验收，不修改原metadata01、registry或科学质量门。
