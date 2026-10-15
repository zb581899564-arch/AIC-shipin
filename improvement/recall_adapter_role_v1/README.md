# Adapter role development ablation

独立开发对照，不是旧 positive 科学失败的恢复。原四开发来源、10个原候选、原视觉和提示token、首次独立输入QA全部引用；不重复准备、模型或输入QA。唯一新因素是strict positive新增准入的每次生成内关闭全部144 TIME LoRA，前后均启用恢复并冻结梯度，base/adapter权重不变。B0/旧VERIFY和40.46保护基线不变；实际载入总8782459120参数，关闭LoRA不减报参数。

首次子进程`role_runtime.py admit`引用完整原10输入及已成功firstQA、控制组10回答/输出QA；只建立新输入来源锁。唯一共享GPU新job执行10个BASE角色回答，完整原prefill，无之前输出/KV输入，原有限KEEP/UNKNOWN/DROP grammar与newpart可见门保持。GPU后独立output-only QA核实际token/grammar/native/input/activationbefore-inside-after及权重终态，不再encode。固定开发八门及全评审平均duration-F1沿用原protocol_v2；通过后仅冻结下一次新确认，不自动新媒体或生产。

新reg绑定原root/code、protocol、当前官方回执、prior inputQA/outputQA/result、model/runtime/processor依赖与原source lock完整files，以及已验证PEFT激活语义的原`local_boundary_base_dev_v1/code/bd_contract.py`路径与SHA（只引用纯合同，不执行旧边界工作）。`role_chain.py --root NEW_ROOT`父CUDA0，CPU子仅隐藏自身。所有文件exclusive create，唯一新GPU自然账本，不重复launcher。新任务仍仅开发10calls/max1200秒，无新下载、训练、解码、封包、Goal或心跳。

`check_pure.py`验证输出/激活错误拒绝与输入QA/GPU/outputQA顺序；不冒称真实模型通过。旧4开发曝光、旧另外12来源也曝光，不当新盲测；新dev过后需另一份未曝光确认登记。关闭TIME是否改善拒选只是待测假设，不能把旧无负例训练事实直接当因果结论。
