# Mac最终8B开发与提交包接续

用户明确授权“mac的开发测评和提交包尽早完成”。Mac v8最终adapter已结束3620有效/227更新/5轮，SHA1baa14a96d30d3836478295752c0b932f40f811863c28db99b56102fcfa1d5b5。为尽快交付，新接续在Linux CUDA上执行Mac最终模型，复用既有固定同8B基座，不重训或下载模型。

唯一远端目录：`/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/mac8b_delivery_v1`。独立85文件锁SHA4625ec88e222d2faa79c74830af8ae703425d71000828592165071c8e2d67e49。CPU 4真实native/低分辨率processor、12新合同和30回归均PASS。开发原104/96/112窗口及来源隔离已绑定，confirm100不读。

2026-10-06 23:19:49 UTC+8启动单次Linux控制器，历史PID1289898；Windows隐藏容量/交付桥接历史PID64592，二者须实时核PID和命令，不可只看注册。23:19:56控制器实查存活，启动阶段逐字节复核中，尚不能声称开发评测完成。桥接23:18:24的Mac live容量receipt已经Mac跳板注册到Linux。

顺序：CUDA合成64帧1080p低分辨率实际生成与288 LoRA/144语言模块重载精确一致、同全字节冻结基座 → 同低分辨率/PyAV输入BASE8B与Mac最终SFT8B各一次固定开发 → 完整NONTEST8时间/CPU镜头/锚点/空间/strict ZIP → 426/521完整复赛时间 → CPU镜头/实际锚点 → 按本次同8B实际非测试空间成本另准入 → 空间/合成/严格ZIP → Mac跳板回传并Windows独立复核。

输入为64帧上限、每帧实际<=32768像素、输入6144界与Mac训练保持。开发PyAV、生产既有CFR Decord/native验证解码及CUDA与MPS数值差异登记在DEV_PROTOCOL.md；不宣称逐logit或跨后端像素相等。空间仍同8B无时间adapter原生图像接口，共享参数只计一次，全链8782459120。C/BCE UNKNOWN负语义STOP保持。没有官网上传授权。

源码运行中禁止编辑，不重复launcher或各stage。查latest.json、completion.json、dev/progress.json与dev/decision.json、long_probe_01/probe.stage.json、nontest/rematch stage/progress与controller/gpu_run对应resource。任一科学/模型/完整合同/strict门失败STOP；传输容量及状态查询失败在登记三天界内有界重试，transport_retries.jsonl保留UNKNOWN证据，不绕过Mac。GPU共享锁/追加账本/7200秒偏移/累计不限/合计80GiB保持，Mac训练结束后剩余训练产物预留为0。

未来本机包在`delivery_01/candidate_MAC_8B.zip`，只有delivery_completion.json=PASS_LOCAL_UPLOADABLE_8B_PACKAGE且全部strict检查通过才算交付。原4B33.81和已交付Linux8B包保留，不能将注册或正在评测当成包已生成。若只剩机器计算可结束对话，由已登记控制器/桥接接续。
