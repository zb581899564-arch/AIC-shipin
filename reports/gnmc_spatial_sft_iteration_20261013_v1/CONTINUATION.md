最新终态：50真实optimizer更新、adapter冻结/保存重载及20开发真实预测/独立CPU重放已完成，373.178秒唯一completed/exit0。15/20改善但两文件大退化，宏IoU下降0.007653，原质量门FAILED；确认0、生产0、ZIP0，不重新执行该链。诊断显示预测width997..1000且中心退至约500；训练200图有114>950宽、35<=750宽。下一项证据支持的任务是单独学习宽度并保护原中心、平衡训练宽度，而不是重跑原联合配方或调原质量门。

最新实际：原父链在131成功训练tensor/40成功eval后HTTP429失败，GPU0；旧父链不重启。独立recovery_01于14:38:06Z启动一次，仅补剩余输入，所有已有JPEG/range/RGB/tensor/proof原地复用，原50更新/质量门/固定顺序不改，单网络线程1.25秒间隔并尊重429 Retry-After。准确入口 recovery_01/launch.json、started.json、chain.log、failure.json、completion.json；原始失败保留。CPU全部完成后原唯一GPUjob尚可首次启动。

唯一Linux入口 /home/inspur/aic_video_work/gnmc_spatial_sft_iteration_20261013_v1/chain_launch.json。70,127字节代码/控制包已SHA/CRC/逐成员核验部署，2026-10-13T14:34:07Z父链启动一次。先新200作者train图、复用40原RGB并生成新输入；全部CPU通过后自动唯一共享GPU任务gnmc_native16_sft200_screen20_20261013_v1，50实际更新/最终adapter重载/20新预测，再独立CPU验证固定门。只有通过才另登记冻结adapter的20文件确认，原基线开发答案复用不重跑。现在生产未准入，不能声称有新ZIP。不得重复launcher/成功媒体/编码/模型/重放，真实失败显式新版本恢复，保留所有证据。评价与产物驻留Linux，本地只小回执和最终ZIP。
