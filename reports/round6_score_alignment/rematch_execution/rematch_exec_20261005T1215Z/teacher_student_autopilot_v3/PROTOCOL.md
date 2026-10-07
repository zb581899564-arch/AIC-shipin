# v3真实教师时间坐标修复

v2真实32B小试已加载GPU并生成首条响应，但该响应混用源PTS139.514375/150和本窗0..30秒，被原strict validator拒绝，0合格标签/0 T更新，旧raw/frames/失败保留。本版同一自然窗口/同一64源帧/同一PNG/同一模型与主提示词，逐帧文本明确窗口内时间；结构化生成的区间端点仅可取实测窗口内采样PTS或0/窗口末端，metadata常量只绑定输入身份，all_provided_frames_reviewed/空/不确定/语义均由模型选择。不得修补旧响应、裁段或制造空标签，validator不改。端点生成粒度属于新教师配方，单独登记。本版同时修复probe.per_window_wall_sec数组的max统计，不把数组当标量。

# v2入口修复登记

v1已于2026-10-07 13:10 UTC+8因裸ffprobe不在PATH而STOP，尚无GPU教师调用、标签或T更新。旧失败/源码保留。本版仅将原选择器使用的既有ffprobe绝对路径及SHA绑定到几何预估、教师CLI和preflight，GPU作业名改v2；标签、训练、输入、模型、采样、提示、停止门均不改。已有Z于13:08因旧冻结51GiB额度STOP，真实磁盘仍有约193GiB可用，T不以Z成功为门，按真实容量运行器接续；本版不重开Z。

# Linux一次性教师与T学生接续

用户2026-10-07离开前授权布置全部任务，并明确批准本次Linux原地下载固定32B教师权重约19.52GiB（20.96GB，已说明重试可能增加），以及自动标注、8B微调、推理封包。Windows不继续大文件下载/上传；仅部署本目录约数百KB以内的源码/元数据。最终一个选定T ZIP留Linux，不自动回传、不上传官网。Mac退出。磁盘/RAM/VRAM无项目人为额度，按实际容量与外部任务冲突准入；共享GPU锁、追加账本和7200秒历史偏移保持。

固定离线教师Qwen3-VL-32B-Instruct官方GGUF Q4_K_M+F16 projector、revision e3e1fe0c76de7ee58ea65db420c643adfe2e457c；llama.cpp 5ad1c5da0ad7f6176256b823925aad19134f0263。全部模型主体从官方CDN到Linux，临时signed URL仅作下载授权并留私有文件，不进入公开仓库。下载两个完整size/SHA通过才加载。Linux本地模型server127.0.0.1，禁止第三方上传视频。

总控一次注册：等下载与CUDA运行时完成，并等已注册Z终态释放GPU；Z的官方质量或包成功不是T训练前置条件。Z全源空间场合格时冻结原字节SHA并复用，同一8B基座无时间adapter，避免重复空间GPU计算；缓存缺失/失败/源域不一致时由T独立重算。Z103冻结文件、旧B37.63包与历史记录不改。

教师真实输入为已固定128train/32dev自然窗口、YouTube组隔离、最多64floor端点采样、实际native PTS与PyAV RGB24。独立PNG图像embedding与学生video embedding有差异，不能宣称tensor相等。教师显式ctx65536、image tokens8..768、真实每帧pixels<=786432；实际grid从llama DEBUG日志取，实际prompt长度由usage取，缺失或溢出STOP。先每split一窗的真实工程探针，再按实测成本登记完整标注与第二次32B真实弱语义审核。全部提供帧、原prompt、原HTTP响应、原始答案和PNG/帧SHA保留。不确定/失败/未知不转为空，超过5段排除但保留。

审核明确是同32B第二次观察的弱监督审核，不是独立模型、人类审核或真值。train/dev自然出现的正例与显式空例都必须存在；有效train须能在3epochs有效batch16内产生20更新；来源污染、缺观察、全空/系统性全选或审核不一致STOP。多段、边界与缺失类别按真实记录审核，不造定额或实例。CPU格式通过不能代替这些真实门。

学生继续旧B最终LoRA（不重置），固定r16/alpha32/dropout.05/lr1e-5/batch16/micro1/最多3epochs/seed20261007。基座与视觉全字节冻结；assistant interval JSON CE接受真正[]，提示、视频和padding mask。前20更新属于同一次3epochs计划，实际保存/加载比对optimizer、RNG、数据位置和pending epoch状态；独立CPU子进程重载prefix adapter，不额外更新、不重置父optimizer/RNG。任一失败STOP保留。

学生train/dev/production统一64floor真实PTS、PyAV RGB24、显式video size4096/25165824、16384token、0..5可空约束greedy。T生产对全部CFR/native分支均按真实PTS half-open bisect映射帧，并保留raw origin，以Fraction相加后单次转float避免边界误差。这是与旧B/Z不同的新整套配方，不纯归因微调。

epoch1/2/3各保存并在同一新dev评一次。初始B只对该新dev评一次作为崩溃参照；弱video macro temporal F1最大者选中，精确并列选较早epoch。预声明崩溃门：全空、每窗选择>=99%，或>=75%组下降且macro F1下降>=0.05时STOP。内部弱F1不是AIC总分，不实现本地官方评分，不以CI>0作为质量门。100confirm不读，正式C BCE仍STOP，空间S缺构图真值不偷偷启动。

选定adapter实际重载通过后：NONTEST8完整链→426复赛时间推理→同源空间场→compose→SHA/CRC/独立strict全部11项→candidate_T_8B.zip。部署推理链总参数8782459120，共享8B只计一次，离线32B教师不进部署链。成功只写PASS_AUTOPILOT_FINAL_T_ZIP_ON_LINUX；官网分待用户上传所得，不承诺提分。

运行中禁止修改source_lock绑定代码或重复launcher。网络、容量、模型、数据、输入或工程错误保留现场STOP，不静默降低帧数/像素、不使用8B教师替代、不杀外部任务、不自动改SSH/Tailscale/代理。
