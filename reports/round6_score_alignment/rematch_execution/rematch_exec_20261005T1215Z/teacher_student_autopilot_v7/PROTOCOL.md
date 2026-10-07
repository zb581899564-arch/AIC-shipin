# v7 全链修复后的十二窗配方校准

用户授权全面核查、立即修复及原后续自动链。v5 于22:18停止：12/12真实生成均正，0空例、0T更新；原样真实第二次诊断12条中3支持、9拒绝/不确定，若干拒绝理由可证实混用了源PTS和窗口秒数。这不是人工真值，也不能把拒绝直接变空。

继承v6工程验收：92项CPU合同，160个真实元数据窗口的10302端点与12原始目标无损回放、两条完整真实decode/64帧pixel SHA通过，旧四位serializer会拒绝11/12现有目标，新的值完全不变。修复精度helper身份、dev/生产原生实帧合同、增量容量/合法空空间成本、phase服务器历史回执和fresh probe缓存误计。第20更新、最多3epochs、原B LoRA/lr1e-5和最终包门保持；CPU不冒充CUDA训练已完成。

**新科学登记：改变实际生成对象的字段先后顺序。** 原v5高光定义、teacher_prompt字节、固定32B/运行时、源窗/64PNG、采样PTS、端点枚举及原validator均保持。实际grammar先生成decision_reason和uncertain/explicit_no_highlight，再列retained_segments；三种状态仍平等合法，不强制任何比例。这是针对全正现象的一项校准假设，尚不声称字段顺序就是已证实原因或能修好质量。

复查与标注保持同一观察规则：明确窗口本地端点和源PTS的两列数值对应；跨窗事件允许仅保留本窗可见部分，不臆造间隙的边界真值。数值预验证不能证明高光语义正确，审核仍可拒绝或不确定。原schema的all_provided_frames_reviewed=true为grammar常量，不能称为自主确认；第二复查为真实可拒绝boolean。

使用历史同一哈希规则的8train/4dev作为明确的配方校准集，主控已读其v5诊断，不冒充未触碰验证集。v7重新独立真实生成十二条，不复用v5/v6旧配方标签。逐条原validator后复查全部eligible，再评估分布与全部弱复查；未知、排除、拒绝及失败均保留，绝不转为空或删除来过门。

小试仅在有真实正与空、无invalid/整窗偏置且全部eligible真实复查支持时通过，随后自动重输入工程probe→160新配方标签/完整train-dev各正空与全部弱复查→B LoRA续训T/20prefix→弱开发选点→NONTEST8→426/strict ZIP。任何门拒绝STOP，不盲目全量重跑。100confirm不读，不复刻官方分数。

全部留Linux。Mac不参与，无新大模型/素材下载、无自动回传或官网提交。共享GPU锁、追加账本7200历史偏移与真实容量保持。只有426独立strict及ZIP大小/SHA/CRC、根PASS_AUTOPILOT_FINAL_T_ZIP_ON_LINUX才可提交。
