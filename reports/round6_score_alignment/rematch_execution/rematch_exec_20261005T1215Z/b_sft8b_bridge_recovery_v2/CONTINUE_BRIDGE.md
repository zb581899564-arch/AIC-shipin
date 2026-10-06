# 8B v3 桥接当前入口（2026-10-06 20:57 UTC+8）

旧 bridge_recovery_v1 因一次 bounded SSH 超时退出，原注册 PID52676 已查不存活，旧 stderr 与注册/receipt 全部保留。Linux8B空间与Mac训练均继续；截至20:57，空间9850/13947、0失败，Mac20:55为177/227、failure=null。

用户原包生成授权下独立恢复接续，不重启Linux训练/推理，不修改原68绑定文件。新v2历史PID48800，20:56:56登记；当前检查新桥接自己的bridge_registration、stderr、transport_retries和Linux容量receipt时间，不能只按PID历史记录认定成功。

v2保留v1原生参数数组、异步双流读取、SSH120秒/scp1800秒墙钟界和task-owned超时子树结束；连接错误在原三天外层界内等待30秒重试，逐次追加UNKNOWN_TRANSPORT_RETRY_NO_BYPASS。只有身份/容量查询、Mac跳板容量传输、receipt原子注册和远端状态查询五类传输失败可重试，模型/合同/完成STOP、交付字节或strict loader错误仍STOP。失败不冒充容量PASS、不绕过Mac、不更改SSH配置。部分交付错误不静默覆盖或重开。

source SHA见recovery_audit.json。官网未上传，Mac独立训练授权不扩展。唯一交付合同仍为b_sft8b_package_v3/delivery_completion.json=PASS_LOCAL_UPLOADABLE_8B_PACKAGE与本机delivery_01/candidate_B_8B.zip完整独立验收。
