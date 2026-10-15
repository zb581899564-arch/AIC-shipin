首入口在登记后、读取视频前失败：ModuleNotFoundError: No module named 'source_color'。原因是历史运行根路径漏写 reports。该次没有打开视频或生成图像，没有模型调用。原登记保留，独立 v2 引用同一预先登记 ordinal；仅修正历史根与输出目录，不改变采样请求。
