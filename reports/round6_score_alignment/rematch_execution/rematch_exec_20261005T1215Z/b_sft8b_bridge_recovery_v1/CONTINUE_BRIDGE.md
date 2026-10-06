# 8B v3 回传桥接恢复（2026-10-06 18:58 UTC+8）

本次只修复已授权 v3 包生成的容量证据刷新和最终回传，不重启 Linux 控制器、不修改 68 个绑定文件、不启动实验或官网上传。

原 Windows 桥接 PID60636 的直属 SSH 子进程56500 自18:23:57卡在容量 receipt 的远端 mv；命令、父子关系与创建时间保存在 old_stalled_query.json。只结束该直属子进程，原桥接随既有错误门退出，旧 stderr 与注册保留。没有终止训练、推理或外部任务。

独立 bridge_recovery.ps1 保持原容量合同、scp -J macmini、严格主机校验、交付清单和独立 loader。新增 bounded_native.ps1 使用原生参数数组与异步 stdout/stderr 读取，SSH有120秒墙钟界，scp有1800秒墙钟界，ConnectTimeout15/ServerAlive15x3；超时只结束本函数创建的子进程树。任何失败仍 STOP，不绕过 Mac、不更改连接配置。

新单次桥接历史 PID52676，10:57:28Z登记；Mac/Linux真实 hostname 通过，18:57:34 的 Mac live 容量 receipt 已经 Mac 跳板传到 Linux并完成原子注册，18:57:46实查新值。本机 stderr 当时为空，桥接存活。后续必须实时查询 PID/命令、bridge.stderr.log 和注册文件，不重复启动。

源码 SHA256：bridge_recovery.ps1=4afe1ab0df01546a60368d9b8aa956a05c1760d811071adaedddd6e7f0698005；bounded_native.ps1=cc40b4efee7a7d8e3514363f4d1a83c526e114600ac7b496ae4ee5d4155a7778。

Linux v3 时间阶段已 PASS：426视频/521窗口/0无效，14旧成功对象不变，81旧 generate 前 guard 失败窗口各恢复一次；CPU顺序镜头/锚点 PID989427 18:56实查约341%CPU。后续仍需空间、严格ZIP、本机交付。Mac独立训练18:57实查107/227更新、1722/3620有效，failure=null。

唯一交付判定保持 b_sft8b_package_v3/delivery_completion.json=PASS_LOCAL_UPLOADABLE_8B_PACKAGE；ZIP在该目录delivery_01/candidate_B_8B.zip。当前没有完成的8B可提交包，官网未上传，原A包保留。
