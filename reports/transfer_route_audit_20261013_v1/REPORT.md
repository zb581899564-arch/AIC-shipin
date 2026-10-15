# 2026-10-13 传输流程与国内中继只读核查

用户要求本轮先处理传输问题，没有启动任何新模型、训练或候选任务，没有改网络/SSH/代理/服务，也没有购买或部署中继。

## 实际结果

Linux数据准备、推理、评价、验收和打包可以完整在远端完成。此前Windows评价需要回传原始回答和proof，是工作流拆分导致，不是科学验证必须跨机器。后续本地编辑代码、传小量变更，远端计算并保留全部证据，只回最终ZIP和简短回执；原成功、原失败和质量门保持，不为迁移重跑成功工作。已写进AGENTS顶部。

本轮抽查最近四个已完成导出回执，不重新下载：SumMe20为532178字节，SumMe新5为163271字节，VideoXum20为3663836字节，VideoXum新8为1537407字节，总5896692字节（5.90MB十进制）。包含原始模型回答、原生时钟、CPU检查及来源清单等，不包含完整视频和模型权重。此数不是全项目历史流量、SSH总流量或机场账单，不据此否认用户观察的总耗量。更早的大数据上传属于另一阶段。

16:48–16:54 Asia/Taipei实际核查：ssh -G显示aic-inspur-home直指100.127.244.47:22、无ProxyJump/ProxyCommand、严格主机检查；它仍依赖Tailscale外层通道。三次tailscale ping均为DERP(hkg)，315/349/370ms，direct connection not established。Linux看到Windows侧relay sfo。两端Tailscale均1.102.2；Windows UDP=true、MappingVariesByDestIP=false，Linux UDP=true、MappingVariesByDestIP=true，均无可用公网IPv6。这支持当前未直连、Linux侧存在困难NAT；本轮未抓包或改NAT，不将其升级为已定位具体校园网设备。

FlClash TUN实际在线，系统代理ProxyEnable=0。只提取配置的非敏感设置：mode=rule；derp20b/20c/20d.tailscale.com明确走“自动选择”；仅tailscaled.exe的UDP被定向DIRECT；100.64.0.0/10为DIRECT；境内baidu/qq/qcloud/aliyun/aliyuncs/myqcloud和GEOIP CN为DIRECT；其他流量有机场策略兜底。外层DERP是TCP/HTTPS，内层100.x及UDP直连规则不覆盖所有DERP流量。已有tailscaled TCP连接出现198.18.* TUN/Fake-IP地址，存在代理接管证据。未取得实时规则命中/机场账单，不声称全部历史SSH载荷都已测量确认经过机场；目前不能保证零消耗。

Linux当前SSH环境未设置http_proxy/https_proxy/all_proxy/no_proxy，当前进程仅发现tailscaled，没有发现Clash/frp类代理进程；默认出口为物理eno2及校园网私网网关。这是当前快照，不能证明过去每个下载进程未单独设置代理。

两端只做境内阿里云文档站HEAD可达性检查，各响应302、约0.5KB头；Linux连接203.119.145.38，Windows连接198.18.1.33(Fake-IP)。--noproxy只关闭应用层代理，不能绕过现有TUN，此测试不等于完成国内中继或机场零计费验收。

## 可实施选择与证据

1. 已有百度网盘可继续用于必要大文件的国内存取；国内OSS/COS私有桶也可以双向存取，不必让双方同时在线。双方实际DIRECT时文件载荷不经过机场。国内云存储仍有自己的存储/请求/外网下行费用，不等于完全免费。阿里云[流量计费](https://help.aliyun.com/zh/oss/traffic-fees)明示普通上传流入不收费、外网下载流出收费。
2. 若需要稳定SSH和双向自动传输，优先评估一台用户自有中国大陆公网节点作Tailscale Peer Relay。两端实际版本满足1.86+要求且均支持UDP；仍要核到具体节点的UDP可达性、带宽和tailnet授权，不把netcheck成功当部署完成。[官方Peer Relay说明](https://tailscale.com/docs/features/peer-relay)
3. UDP不能通到所选国内节点时，自建HTTPS DERP或TCP型frp STCP可作备选。DERP有公网、证书及端口要求，不照搬跳过证书验证的教程；frp STCP需要两端访客/服务客户端。中继两端须直接连到大陆节点，且文件传输不能静默回落到境外DERP。[官方DERP说明](https://tailscale.com/docs/reference/derp-servers/custom-derp-servers)、[frp STCP](https://gofrp.org/zh-cn/docs/examples/stcp/)

## 验收与限制

先减少不必要传输，国内中继作为独立网络部署处理。有具体节点后以小量已知字节文件双向核验：实际peer-relay/自建DERP节点、节点域名和IP的DIRECT命中、两端接口字节、机场对应连接无该载荷增长、收到文件大小/SHA一致。机场全局总流量可能被Codex/浏览器等其他连接改变，不能用全局计数单独归因。中继仍消耗普通宽带和节点带宽/流量；大文件数据面与Tailscale认证/控制面的少量外网请求分开计算。

当前没有用户国内节点信息、没有新中继部署和端到端文件测试，因此只确认方案技术可行及当前存在耗机场路径，未声明已实现零机场传输。
