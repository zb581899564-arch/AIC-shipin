# Linux旧失败缓存清理

用户于2026-10-15明确授权：容量不足时清理以前失败方向的包和数据，保留当前最高40.46包的数据。清理先核主机、实时容量、精确路径、当前注册和最佳包依赖，以及活动进程的命令、工作目录、打开文件和映射；未对进程发送信号。

实际于2026-10-15T00:55:48Z删除1,560个旧GNMC失败方向及原A/B/C被拒方向的二进制帧/张量缓存，释放9,814,941,696字节可用空间（约9.81GB）。可用空间从70,301,339,648增至80,116,281,344字节。完整逐文件清单保留在Linux独立清理目录，Windows仅保存简短回执。

保留40.46原ZIP及复现来源、当前独立确认、共享模型和环境、原始媒体/比赛数据。40.46 ZIP复核SHA仍为86593725c6bad919dc0d342fe98ad65e489a13a6e492da5de3afd247a3226543；当前注册及最佳封包元数据在删除前后保持。旧源码、协议、QA/失败/成功终态、费用和119个缓存目录内小量元数据未删除，旧失败门不改。

删除的旧二进制缓存已不可直接完整重放，不能再声称其仍然保留；这不撤销此前真实执行及科学失败结论。没有为清理重跑下载、解码、编码、模型或QA。

具体范围：gnmc_width_sft1000_iteration_20261013_v1的tensors/rgb、gnmc_spatial_sft_iteration_20261013_v1的tensors/rgb、gnmc_width_sft_iteration_20261013_v1的tensors、human_reference_iteration_20261013_v1的rgb_02，仅删除登记的二进制载荷。未删除整个实验根。

Linux审计目录：/home/inspur/aic_video_work/storage_cleanup_best40_46_20261015_v1；deletion_plan_03.json及deletion_completion_04.json为实际清单和终态。本地deletion_completion_04.json为简短回执。
