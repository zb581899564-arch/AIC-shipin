PAIR_ONLY补充短源确认：STOP，不能准入第五包。

2026-10-15T11:58:44.494813Z唯一controller自然完成。4B0+5VERIFY+4rank=13真实调用，13首次输入QA/13首次输出QA全部成功；3唯一GPU作业自然completed/exit0、逐条共享账本完全一致，实际费用430.978899208829秒。controller进程已消失，shared active GPU为null。

|指标|基线|候选|差值|
|---|---:|---:|---:|
|macro F1|0.3059141578|0.2781580829|-0.0277560749|
|macro precision|0.3073878225|0.2802625180|-0.0271253046|
|macro recall|0.4229718528|0.3939914552|-0.0289803976|

完整4源、各10原评审。PAIR适用1窗，v_nEOpfvJ7g_g实际删130原生帧，该源F1 .1110242995→0；其余3源精确不变。宏F1不降、precision不降、逐源loss<=.01三门失败；其余5门通过。未改门/端点/标签，不重跑或扩大来源。

旧4源neutral-but-no-applicability PAIR失败保持；两次预登记reference/native-domain工程替补拒绝及部署包装器解析失败07均保留。所有媒体、原始模型回答、QA和计算证据驻Linux，Windows只存metadata与短回执。40.46包和旧失败根未修改。

最终Linux比较：`/home/inspur/aic_video_work/midnight_pair_applicability_20261015_v1/policy_fresh_comparison.json` SHA `876f2cf98e307cf5644d1ef1634888983e4908840c45a1884e2855a9a1e23d10`。

控制完成：`/home/inspur/aic_video_work/midnight_pair_applicability_20261015_v1/control_01/completion.json` SHA `8b87f323913ac04d2f80bffd71e14623b895891c2a50a83d0c2ac5a0b0a1e474`。科学STOP短回执：同级`scientific_stop_receipt_18.json`；Windows副本见本目录同名JSON。工程自然完成与科学质量失败分别记录，官方提分UNKNOWN。
