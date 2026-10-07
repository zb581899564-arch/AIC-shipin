# v4严格教师生成约束与接续

v3于2026-10-07 14:03在第11条完整标注因字段缺失STOP，10/160进度；旧成功和失败原字节保留。固定运行时实际读取response_format.json_schema.schema，旧schema同级字段被忽略，真实grammar仅通用object。v4纠正请求嵌套，把原四条if/then语义条件等价展开为三个完整对象分支，所有空/正/不确定分支保留；使用固定运行时真正的grammar解析器校验生成对象及缺字段反例，不放宽原独立validator。

成功v3窗口逐SHA/原validator核验后原样引用，不复制/改写raw/帧/标签。原两条重输入探针和失败窗口在v4各新生成一次，并测试一次真实弱审核请求，再继续160全量。新旧生成约束差异登记，失败回答不補字段、不转空、不作为训练目标；不重开旧入口。原prompt、权重、选窗、学生协议、未知负语义门、官网提交与传输边界保持。

# v3真实教师时间坐标修复

v2真实32B小试已加载GPU并生成首条响应，但该响应混用源PTS139.514375/150和本窗0..30秒，被原strict validator拒绝，0合格标签/0 T更新，旧raw/frames/失败保留。本版同一自然窗口/同一64源帧/同一PNG/同一模型与主提示词，逐帧文本明确窗口内时间；结构化生成的区间端点仅可取实测窗口内采样PTS或0/窗口末端，metadata常量只绑定输入身份，all_provided_frames_reviewed/空/不确定/语义均由模型选择。不得修补旧响应、裁段或制造空标签，validator不改。端点生成粒度属于新教师配方，单独登记。本版同时修复probe.per_window_wall_sec数组的max统计，不把数组当标量。

# v2入口修复登记

v1已于2026-10-07 13:10 UTC+8因裸ffprobe不在PATH而STOP，尚无GPU教师调用、标签或T更新。旧失败/源码保留。本版仅将原选择器使用的既有ffprobe绝对路径及SHA绑定到几何预估、教师CLI和preflight，GPU作业名改v2；标签、训练、输入、模型、采样、提示、停止门均不改。已有Z于13:08因旧冻结51GiB额度STOP，真实磁盘仍有约193GiB可用，T不以Z成功为门，按真实容量运行器接续；本版不重开Z。

# 一次性Linux接续入口

先核Linux主机inspur-NP5570M5；查本目录registration.json与真实PID/命令，不把历史PID当存活。运行时查progress.json、controller.log；最终以completion.json为准。只有PASS_AUTOPILOT_FINAL_T_ZIP_ON_LINUX且rematch_01/independent_validation.json全部checks=true才算Linux提交包完成。

当前teacher32b_linux_download_v1是已获本次流量许可的独立Linux下载；Windows旧下载50872/教师上传等待27724与Z回传61596保持停止。不得自动恢复这些旧入口，不再回传整套产物。新的其他大流量传输必须先说明规模/链路/可能机场流量并取得确认。本次源码部署为小量文件，不是模型主体搬运。

本目录controller.py由一次性后台入口启动，持有controller.lock与registration.json，禁止重开。等待下载、运行时、Z终态后自动真实teacher_probe→teacher_full（含独立validator及真实第二次弱审核）→student_admission→student_train（含同轮20prefix及CPU重载）→NONTEST8→426推理/空间/strict ZIP。机器运行依赖Linux在线，不依赖本地Windows持续运行。

主要回执：teacher_01/teacher_probe_completion.json、teacher_01/teacher_completion.json、teacher_01/semantic_review.json、student_01/student_completion.json、nontest_01/package.stage.json、rematch_01/package.stage.json、completion.json。新模型训练开始只看student_01/progress.json实际optimizer更新，不能把排队/工程probe算开训。

STOP时读completion.reason、phase wrapper日志和RUN/controller/rematch_TAUTO_v4_*.resource.json，不重试失效教师响应、不强造空标签、不扩大科学协议。只注册新独立修复版本后再继续。既有source_lock与失败证据保留，不回写旧B/Z/M实验。最终candidate_T_8B.zip留Linux，用户要取包时先说明大小；官网不自动上传。
