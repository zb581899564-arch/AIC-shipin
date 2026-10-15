本轮原作者GNMC人工16:9静态构图监督小试验，200训练图、20开发文件、20尚未评分确认文件。仅非商业学生科研，不分发原图；原拍摄来源独立性、预训练重叠和视频外推均UNKNOWN，不自动等于生产通过。

固定原作者train拆分SHA候选顺序、全保护曝光ID/字节及dHash<=6排除；原标注保留，量化目标须与原框IoU>=0.95。一次最终50更新、r8/alpha16/1e-4/grad8，只语言attention qkvo LoRA，助手JSON交叉熵，base/vision冻结并逐字节前后核、adapter保存重载。真实240CPU输入全部通过、冻结源码输入后，唯一共享GPU任务。开发基线20真实回答复用，不重跑；确认只有开发固定门通过后冻结最终adapter再独立执行。

开发及确认固定门：平均配对IoU提高至少0.05、至少75%文件提高、任一文件下降不超过0.05、至少3个文件实际变化、非法输出0、全部20计分；不得因失败调整原门。评价由独立CPU输入/token/raw/grammar/geometry重放实现，全部Linux驻留。旧宽度提示词失败、旧科学门、旧40源FAILED/UNKNOWN及费用全部保持。

原准备HTTP429在131成功训练tensor/40eval后自然失败，GPU0；独立recovery_01只补剩余，引用成功JPEG/range/RGB/tensor，不解码/编码/下载第二次，单网络线程并尊重服务端429等待。唯一入口current_state.json/CONTINUATION.md中的recovery_01，不重启原父链。
