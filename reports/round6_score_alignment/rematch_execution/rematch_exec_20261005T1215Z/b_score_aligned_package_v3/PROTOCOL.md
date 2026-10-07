# B2 v3：显式原生解码修复与仅失败窗恢复

保留已经训练的B最终8B LoRA、v2统一canonical时长、原提示/64帧/16384/greedy/参数。v1/v2所有锁、raw、STOP及成功物保持。

真实provider视频97在送入processor/模型之前，PyAV17.1/libswscale9拒绝yuv420p/unknown primaries/unknown colorspace/log316 transfer，errno95。全434源头元数据仅这一个SHA为此profile，来源SHA8ec893eb5378452de6223f6c8e5878bcea044cb2f9e4feaabf708fa364871722。OpenCV亦打印同转换失败，read的返回不能当合法RGB。

这是独立登记的新像素转换配方：仅此SHA且精确格式/geometry/trc10/space2/prim2/range1匹配时，将用于转换的transfer标记临时设UNSPECIFIED(2)，明确限定范围ITU601 YUV样本映射，完成后恢复原frame元数据。原YUV样本/PTS/尺寸/range/源文件字节不变；不应用或宣称恢复摄影gamma曲线。不按图像内容选颜色参数，没有复赛视觉调参。其他所有来源保持原转换调用，额外未知错误STOP，绝不try/except自动换任意decoder。

source_color_cpu复现真实errno95、合成有限范围参考、真实64帧RGB/BGR通道完全相等/完整native ordinal与PTS/raw YUV不变；processor实际8非测试像素SHA仍通过。全529端点/529越界拒绝/原29错误及12目标无损合同保持。新source_color/recovery及CPU/processor/所有旧必要成功SHA绑定后单次启动。

v1剩余有效GPU生成继续，不重复成功物。v3在provider全426/521时间与wrapper终态完整记账后，仅准入原失败为登记source97的送模型前errno95，逐SHA/原validator核所有成功，保留旧failed raw/stage。原成功记录整行原字节复制，失败窗口在新目录用修复转换实际生成一次，B288张量/基座全SHA/原输入和原validator/CUDA有限分数都须PASS；不补标签、不将失败变空、不减少分母。新recovery stage明确原成功数/新调用数/两个真实wall成本，不修改旧STOP或借失败总stage给成功回执。

时间新完整PASS后，全源CPU镜头/同一source转换空间/恢复合成/独立strict ZIP；8非测试完整门仍先通过。最终唯一426ZIP留Linux，T0/新分未知，B2不是新教师T微调。每15分钟静默核真实provider/controller/回执，自主独立修复，最后真实大小/SHA/CRC/全部strict通过后报告一次并删除监控。共享锁/追加账本/7200offset/真实容量，Mac退出、不回传/官网提交、新大流量许可继续。
