# EasyTier常驻与文件直连独立核验

2026-10-13 Asia/Taipei，本次按用户要求验证另一AI完成的配置。没有改动SSH、EasyTier、Tailscale、代理、路由、hosts或服务，没有终止服务/断网/重启。仅创建临时SSH诊断转发和一个1MiB随机测试文件，上传、下载各一次，测试文件随后清理，保留回执。

## 实际通过

- `ssh -G aic-inspur-home`实际为127.0.0.1:22022，HostKeyAlias=100.127.244.47，StrictHostKeyChecking=true。原别名通过EasyTier端口转发连接原Linux SSH，主机实际inspur-NP5570M5。严格指纹没有关闭。
- Windows main peer与Linux main peer相互cost=1、next_hop_peer_id等于对端peer_id、tunnel_type=udp。Windows外层连接Linux真实公网202.196.17.232:6026；Linux外层连接Windows真实公网36.113.35.220:58718。Windows最佳路由为202.196.17.232/32→WLAN→192.168.0.1，未走FlClash接口。两端数据路径不是Tailscale虚拟地址。
- 原别名scp上传1048576字节约1.922秒，下载1048576字节约2.266秒（含SSH/SFTP建立，不是长期吞吐基准）。本地、Linux和下载副本SHA256均为4a2caeb54acc1ce625369041ed4a707930a9f0aae129ce018442c03576ccb47f。
- Windows直连UDP计数增加tx=2800895/rx=1685500字节；Linux对应UDP计数增加tx=1704376/rx=1970431字节，均涵盖传输及协议/重传/诊断开销。协调节点的计数增加约1KB；同期Tailscale到Linux的计数仅增加tx=4472/rx=4720字节、合计9192字节。计数采样非原子，也有背景心跳，不能把差值全部说成文件开销。
- 上述证据支持本次文件载荷通过真实UDP P2P与物理网卡传输，未通过机场中继。没有读取机场账单/实时机场接口计费，不能声称所有应用和控制面的总机场流量为零。

## 常驻机制

Windows任务Codex-EasyTier-Direct当前Running，Logon触发，无执行时限；启动G:/vpn/EasyTier/resident-windows.ps1。脚本5秒检查两core进程并补启动，wrapper本身由任务计划3次、一分钟间隔重启。实际resident-state不断更新；已有resident-recovery-result.json记录上一个core恢复测试成功，只作为该AI先前测试记录，不冒充本次故障注入。

Linux用户服务codex-easytier-direct.service实际enabled/active、Restart=always、RestartSec=5、StartLimitIntervalSec=0，用户Linger=yes，支持无人登录时启动用户服务。当前NRestarts=0，本次没有重启机器或故意结束进程验证恢复。

## 必须保留的限制

两端main配置均p2p_only=true，官方说明这种模式丢弃无法直连目标的数据，不通过relay转发。因此Tailscale当前用于协调/bootstrap，不能宣称本别名在P2P失败后会自动通过Tailscale搬文件；这个失败边界正好避免大文件静默耗机场。[官方P2P模式](https://easytier.cn/guide/network/p2p-optimize.html)

Windows监听/路由保护脚本依赖当前Wi-Fi地址192.168.0.2、网关192.168.0.1；更换网络、DHCP地址或对端公网映射变化需要复核，不能用本次在线样本保证永久直连或所有断线自动恢复。后续日常无需手动运行脚本，但大文件之前仍检查实际peer和物理路由；失败先诊断，不擅自恢复旧Tailscale文件通路。

原始单次证明verification.json及代码verify_live.py保留，不为下次心跳重复此传输。此次成功不是比赛实验/质量准入，不启动任何旧模型、训练、数据或候选链；Linux驻留计算约束保持。
