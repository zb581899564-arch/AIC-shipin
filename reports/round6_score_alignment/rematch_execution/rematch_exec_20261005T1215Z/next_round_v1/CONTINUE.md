# 接续与验收

唯一 Linux 目录 `/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/next_round_v1`。

实时状态读 `progress.json`、`controller.log`，最终读 `completion.json`。PID仅为历史登记，须实际核活。`launch.py` 已注册后禁止重复；source_lock绑定代码不得修改。

阶段输出为 `probe_01`、`dev_01`、`nontest_01`、`rematch_01`。`PASS_COMPLETE_426_Z8B_READY_FOR_DELIVERY` 只是远端包完成，Windows `delivery_completion.json` 才是实际交付。官网上传由用户操作，官方分目前未知。

监督 `supervision/selection_01` 为真实源身份/PTS选择；没有实际教师响应前仍无训练标签。T容量STOP；保持80GiB直到用户明确修改。不要重训旧B/M或把UNKNOWN改空。

新的代码/标签/容量变更应另开版本，保留本轮失败记录。不会修改旧37.63包或Mac包。
