# Mac 128帧内存/索引修复 v7 接续

唯一当前目录：`/Users/choubk/codex-workspace/projects/aic-video/mac_sft8b_128_lowres_mps_20261006T0740Z`。环境复用只读 v1 的 `env/bin/python`；全部命令通过 `/Users/choubk/codex-workspace/bin/run`。不得重复已启动的 `launch_owned_mac.py`，控制器历史启动PID78837须实时查询。

当前源码锁：`fb72b24e524423fc9af585a404eb954c36bcf59eca4df3685ef5211e2c647936`（33个绑定文件）。只读 `status_mac.py`、`controller/pipeline_latest.json`，实际backward/update以 `probe_01/progress.json` 或 `full_01/progress.json` 为准。运行期间不编辑绑定源码或改变任何配置。

v1 首次forward OOM；v2自身resource_tracker辅助进程被误判为外部计算停止；v3和v4在backward的MPS半精度索引累加算子失败，均0完成backward/0update。失败receipt及账本保留。v7使用明确视频像素总预算n_sampled*32768、每帧实际网格<=32768、保持128源序号/6144序列上限。BF16模型与FP32 LoRA保持；仅实例级将DeepStack布尔索引加法转为FP32再转回，CPU BF16/FP16和MPS BF16前向/梯度一致检查是已登记探针耗时的一部分，禁止CPU静默fallback或提高MPS上限。

后台 `finish_mac.py` 单次接续固定3 updates/48 microbatches探针。只有完整有限连通梯度/实际权重变化、基座与视觉逐字节冻结、adapter重载、实际峰值不超过MPS建议内存、共享资源和合计80GiB容量都通过，才从冷基座新LoRA开始5epochs/227updates/3620microbatches。全量时限按实测探针成本登记，不沿用探针adapter。失败STOP，不能通过改配置、重开launcher或丢弃失败样本继续。若真正128帧仍OOM，主控按用户授权另行登记不同方向。

最终收集 `controller/pipeline_completion.json`、`probe_resource.json`、`full_resource.json` 与最终train_report、adapter；复制时双端SHA验收。Linux对应v7 `frozen_mac_package/` 只存源码归档，不运行其中Mac入口。Linux原64帧全量训练持续，源码锁不动、账本7200秒初始偏移不动。Mac累计计算追加其独立账本。固定开发比较、比赛推理、空间封包和上传不由本接续自动启动；训练工程通过不代表质量通过。

额外修复：每microbatch同步释放MPS空闲缓存，测试后恢复登记种子20261006；v5首步工程证据及主动停止记录保留。


额外修复：显式token数与feature行数/hidden维度相等检查，contiguous占位掩码；v6旧广播索引大小误判失败保留。

