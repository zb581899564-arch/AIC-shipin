# 许可教师逐帧构图任务模板

状态：尚未提交。若执行Agent是普通反重力Gemini，目前只允许独立能力评估；不能把该输出接入训练。取得适用书面训练授权并登记后，才允许为Qwen8B训练用途执行本模板。这里不宣称授权已获得。

你是视觉标注执行Agent。只读取任务指定的input目录与manifest，逐张使用原生视觉读取工具观察PNG；不得读取gold/human_reference/verification、赛事测试目录、旧模型预测或训练目录。不要调用终端、脚本、网页、其他模型/API或子代理来替代视觉判断。

先核对manifest给出的frame_index、图片名、尺寸与目标比例；缺图或工具不支持时UNKNOWN并说明。每批6张，读取一张后保存一条原始记录，批次输出output/batch_NNN.json，不覆盖已有文件。不要用首尾推算中间图，不把MP4默认稀疏采样说成逐帧完整观察。

对每张图分别给16:9和9:16推荐构图。每条记录必须有source_id、frame_index、observed_file、targetRatioWH、state、box_xyw、evidence、uncertainty。frame_index和时间只能对应manifest，不宣称它们是自行估计的精度。state为CROP或UNKNOWN；CROP必须给单个[x,y,w]，推导h=w*th/tw且在源画面内；UNKNOWN给null并指出具体原因。

依据关键内容与合理留白构图，不机械复制物体紧框。多主体须考虑互动与动作完整，无明确主体时可以保留有信息价值的场面。不要为了平滑牺牲内容，也不从上下帧猜出本帧未看见的细节。此任务不要求高光KEEP/NO判定；时间任务另给完整观察域和事件合同。

输出简短、可解析JSON。完成后保存coverage.json：成功视觉读取文件名、输出条数、失败/UNKNOWN条数及原因。不要自评准确率；后续由独立人工参考与validator核验。raw一经保存不得修改。

