# TVSum本地下载验收

2026-10-09。用户已明确批准下载到本地，完整官方包下载完成。

- 实际大小：671779858 bytes。
- SHA256：407d340bcd06fdc6d17374ebe6760b4a96816bcace228559c8283d9fb2520dea。
- gzip完整读取/CRC及全部tar路径检查通过；外层6个普通文件完整落盘。
- 内含4个ZIP，全部成员路径与CRC通过；50个视频文件、50条信息、1000条人工评分记录，三者ID集合完全一致。
- 每视频20条人工评分；10类别各5视频。
- TSV与MATLAB v7.3/HDF5的全部评分、帧长度及平均值交叉核对一致。7047060个评分数值是展开后的向量元素，不是同数量的独立人类判断。
- 原视频native时钟尚未全量解码验证；没有把完整数据集准入为训练真值。

原包保留于downloads/tvsum50_ver_1_1.tgz。外层解压位置为data/tvsum；50视频仍完整保留于ydata-tvsum50-video.zip，只为用户要求的标注小试额外提取一个源。

包内WebscopeReadMe.txt及README仍声明签署Yahoo协议、获批非商业研究及禁止再分发；作者现行网页记录2019年转为直接下载。该差异已登记为UNRESOLVED，没有推定新网页自动覆盖旧协议，也未联系第三方或转传Linux。

用户随后明确将当前工作限定为视觉标注。现在执行一个公开视频短片段的原始逐帧标签保存，训练与完整数据集外部上传均未启动。小试记录独立保存，不改变历史训练协议。

验收细节见[tvsum_delivery_acceptance.json](tvsum_delivery_acceptance.json)、[完整原包检查](archive_preflight.json)、[来源清单](tvsum_catalog.json)。
