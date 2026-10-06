# Mac低内存64帧实际启动验收

## Mac改低内存64帧方向并真实更新（2026-10-06 15:52，UTC+8）

用户授权修复内存，若128帧支撑不起则换方向。128帧v7虽有真实更新，修复后仍采样56.59GiB，超出当时live MPS建议51.84GiB；主控只停止登记的本任务训练子进程组，旧结果、源码锁与账本保留，未启动其full。新独立 `mac_sft8b_64_lowres_v8/PROTOCOL.md`：同一固定8B、最多64帧、每帧实际视频处理像素<=32768、max_seq6144，704train/724已知正窗口/602组、r16/lr5e-5/seed20261006/5epochs保持。方向为低内存区间JSON SFT，含输入/解码/硬件差异，不能单独归因或承诺提分；C正式BCE未知负语义门仍STOP，不造负例。

真实codec/processor CPU8/8、继续门3/3、进程树归属2/2通过；MPS/CPU DeepStack前向梯度与掩码/错形状拒绝5/5通过。保留显式VIDEO预算和新鲜嵌套kwargs、局部FP32 DeepStack索引后转回BF16、严格token/feature行数与hidden维度检查及contiguous掩码、每microbatch同步释放缓存和测试后恢复登记RNG；不编辑安装库、不隐式CPU fallback、不提高MPS上限。实际参数8,782,459,120。

当前64帧实际探针1/3更新、26/48完成backward，首步288张量梯度连通/有限、144张量变化，采样MPS峰值24.29GiB，当前无失败；最终48microbatches/3updates的冻结与重载仍待运行结束验收，完整Mac训练尚未启动。单次控制器实查存活；全部门通过才自动从冷基座新LoRA开始5epochs/3620microbatches/227updates。源码锁 `6d42f4768e542c13c7c5d72f988c3dc84970e2a5edc0b53f2963cccc4445d9fa`，33文件已Mac核字节并在Linux归档独立核验。Mac目录 `/Users/choubk/codex-workspace/projects/aic-video/mac_sft8b_64_lowres_20261006T0748Z`；查该版本CONTINUE_MAC.md，不重开launcher、不修改运行中绑定文件。

Linux原64帧完整训练保持正常，最新178/227更新、2860/3620有效，未报失败；8B推理封包尚未开始。本Mac接续不自动开发评测、比赛推理、封包或上传。累计GPU不限、追加计费、Linux7200秒偏移、共享锁、唯一Mac工作根和合计80GiB边界不变。当前实证见 `controller/mac_memory_repair_start_01.json`。
