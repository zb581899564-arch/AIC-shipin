# 第三方依赖与恢复

- Qwen3-VL：使用 `Qwen/Qwen3-VL-8B-Instruct` 固定 revision；模型、processor、tokenizer 与使用许可按上游模型说明执行。本仓库不分发其权重。
- PyTorch、Transformers、PEFT、Accelerate、Qwen VL utils、OpenCV、PyAV、Decord、Pillow、NumPy：环境版本以各实验 freeze 和协议为准。
- 历史 OraRL / TempSamp-R1 复现实验的项目适配、验证与账本代码保留；完整第三方 checkout、数据包、模型下载与临时镜像未重复纳入本次发布。相关固定来源/revision及原说明仍在历史报告中。
- 项目内 `vendor` 目录包含实验已绑定的辅助源码快照，保留已有来源注释；文件哈希可在原 source_lock 和发布 manifest 对照。
- 官方比赛数据、公开视频、公开参考与弱教师派生标签各有独立许可/语义边界。仓库中的论文或数据来源记录不构成再分发许可。

本次上传没有创建新的项目开源许可证，也不覆盖第三方原许可。
