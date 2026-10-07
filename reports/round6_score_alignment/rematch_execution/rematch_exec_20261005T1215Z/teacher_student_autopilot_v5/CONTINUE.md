# Linux v5 一次性自动接续

先读项目 AGENTS.md、STATUS_AUTOPILOT_20261007.md、PROTOCOL.md，核主机 inspur-NP5570M5、实时进程命令及资源。当前入口 teacher_student_autopilot_v5；历史v4已STOP，不能重开旧入口。registration/PID只作为核验线索，运行冻结 source_lock，不改绑定源码、不重复launcher。

自动顺序：准备已固定教师→12窗真实小试/原validator/同32B弱复查→重输入工程探针→完整160新配方标签/完整弱复查→学生准入→B LoRA续训T/20更新重载/开发选点→NONTEST8→426推理/空间/独立strict ZIP。小试或任何科学门拒绝保留并STOP；不能逼空例、排除困难样本或删门强行继续。

关键回执：pilot_01/progress.json、pilot_01/distribution.json、pilot_01/completion.json；teacher_01/progress.json、teacher_completion.json、semantic_review.json；student_01/progress.json、student_completion.json；nontest_01与rematch_01/package.stage.json、independent_validation.json；根 progress.json、completion.json、controller.log。只有实际 optimizer_steps 才代表T训练。

最终只有 completion.status=PASS_AUTOPILOT_FINAL_T_ZIP_ON_LINUX 且426 strict所有检查true、ZIP大小/SHA/CRC验证，才交付一个 candidate_T_8B.zip；路径留Linux，大小告知并获许可后才回传，官网用户上传。正常机器计算可退出，不依赖Windows在线。监控只对异常、修复、重要阶段/最终完成或需用户操作通知。
