# 浏览器电脑操作故障排查（2026-10-10）

状态：未修复；已确认两个接口的不同故障，不把它们合并为已证实的单一根因。

用户目标：恢复Chrome真实电脑操作，然后继续一锅炖讨论；授权不允许绕过工具安全检查。

## 现场证据

1. 原Windows电脑操作能列出Chrome/Edge窗口、打开Chrome；get_window_state在研究项目页和新标签页均返回：
   `Computer Use has been stopped for this turn because it could not determine the current browser URL on Windows with enough confidence to enforce policy.`
   这是URL识别无法完成后的拒绝，不是网站已经被判为禁止访问。更底层失败原因尚未得到日志证明。
2. Codex启动日志记录：computer-use native pipe startup ready；辅助进程正在运行。未发现辅助进程未启动的证据。
3. 官方Chrome扩展接口可以列出Chrome及完整标签URL。只读inventory成功并不证明页面控制可用。
4. 对ChatGPT导航实际超时：`Timed out after 10000ms waiting for CDP command Page.navigate.`；之后标签显示about:blank。
5. Chrome页面状态读取实际超时：`Timed out after 10000ms waiting for CDP command Emulation.setFocusEmulationEnabled.`
6. 创建新的临时Chrome标签成功，但导航到官方Computer Use文档也同样Page.navigate超时；排除仅旧标签绑定失效的简单解释。
7. 通过官方js_reset重置浏览器控制JavaScript会话，随后inventory仍成功，两个测试标签仍about:blank；没有恢复完成的证据。
8. 当前桌面应用日志出现：`No ChatGPT browser route is available for browser session ...`。此记录来自browser-use-iab-api，是当前聊天内置浏览器路由异常；不能直接证明它是Chrome命令超时或WindowsURL识别失败的根因。
9. 注册的ChatGPT Chrome native messaging manifest存在，指向既有Chrome插件latest/extension-host/windows/x64/extension-host.exe；没有因此改注册表、扩展权限或安全策略。

## 版本与资源

- Windows包：OpenAI.Codex 26.1002.7124.0；应用日志release 26.1002.52244。
- @oai/sky包：0.7.6；cua_node运行时目录3dd31cfff853001c。
- Chrome：154.0.8037.99。
- Chrome及电脑操作辅助进程在运行。未杀任何用户进程，未安装或卸载插件，未重置浏览器用户数据。
- 相关桌面日志：LocalCache/Local/Codex/Logs/2026/10/10中的b5906fd0本次启动文件。

## 后续恢复与验收

官方Chrome扩展排障顺序包括重启浏览器、核验当前profile安装扩展、重新建立聊天连接、重启ChatGPT桌面应用；仍失败则通过/feedback向官方反馈聊天ID。

下一步应完整退出并重新启动ChatGPT桌面应用，同时保留本聊天和Chrome用户配置；在Chrome手动打开https://chatgpt.com/，从本聊天继续。完整重启将中断当前执行，不能在同一活跃连接内证明修复；需重启后的新实测。

重启后验收：Chrome元数据精确URL可读、页面DOM/截图可读、可导航官方页面并正常返回；全部通过才恢复发送讨论消息。仍失败则保存新启动日志与本报告，检查版本更新/官方反馈；不得关闭URL检查、改guard代码、走隐藏接口或冒称讨论已完成。

官方资料：
- https://learn.chatgpt.com/docs/chrome-extension （Troubleshooting）
- https://learn.chatgpt.com/docs/computer-use

本轮未发送任何模型讨论消息；Pro预算未消耗。
