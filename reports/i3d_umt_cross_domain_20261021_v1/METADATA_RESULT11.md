# 两条元数据查询：实际结果及训练阻塞

2026-10-21。用户先回复“只允许直连，暂不查这两条”，后明确更正“允许查这两条，刚说错了”；按最新答复执行，仅固定skating/surfing两个原YouTube来源的元数据。未修改代理，未在Windows或Linux下载视频/音频。

| 来源 | 真实返回 | 目前可得结论 |
| --- | --- | --- |
| skating / AUAsfZtcB4E | zac lipslide，public；uploader matt boroughs，2012-09-24；显示10秒，30fps 360p及60fps 720p；license=null；30fps视频流标称510105B | 来源仍有公开媒体，未取得明确使用字段或原帧序；不能因有格式就准入训练 |
| surfing / KKjovY6uXFY | 上游提示This video is unavailable；duration/fps/owner缺失、formats为空 | 当前来源报告不可用，不能把返回的占位标题当有效元数据，更不能转成空训练目标 |

原始查询回执保留。首脚本对surfing返回了宽松的METADATA_RECEIVED状态，但实际只是yt-dlp在ignore_no_formats_error下的占位对象；本记录按字段与上游警告明确判未通过，脚本已修正，不重新查询来覆盖原事实。

两个原作者clip.json已通过Linux直连GitHub读取，只读帧端点，不读取留出域人工票用于选参。skating为6个片段，首[1,100]、末[210,310]；surfing为44个片段，末[2150,2230]。页面10秒及30/60fps不足以证明实际原生总帧数或索引/末端约定。不能按视频时长比例拉伸标签、把310截到300、猜测一基/零基或直接挑60fps。

还完成了两个有限、全新问题的直连检查：

- Linux无代理直连官方youtubei.googleapis.com API端点失败，OSError101/Network is unreachable，约8.09秒；没有改DNS/路由/服务。
- 原成功元数据未保存媒体地址，因此只对同一个已授权skating来源取得一次剩余临时locator，用于Linux的无代理CDN **HEAD**。rr2---sn-ouu2j-puhl.googlevideo.com连接同样失败，约9.15秒。没有发起媒体GET，没有将该临时地址打印或保存到公开材料。

这些只证明当前实际测试的入口未成功，不推广为全部原视频已经失效或任何直连办法都不可能。不会因此扩大到未获许可的非直连批量元数据/媒体，不向作者或其他聊天发消息，不循环探测同一失败URL。

## 当前下一步边界

I3D权重、原视频工程闭环、参数和成本均已成功，不重复。留域skating不变，训练媒体准入仍0；还需要一个**可实际取得且来源/使用/原生帧约定齐全的原视频入口**。已核原作者README提供YouTube原ID及替代ID机制，当前没有取得符合这些条件的直连原视频副本。不能借此换用原UMT自动match、摘要标签、不同骨干的预提取特征或随机UMT分数来凑一次训练。

这是素材接入阻塞，尚无留域训练或质量结果；40.47保持，新训练/ZIP/官方提交均0。当前两条非直连元数据查询授权已执行完，不自动扩展范围。后续若使用新的非直连访问，仍须先按最新长期规则明确询问。

准确文件：metadata_windows09/registration.json及两个*_result.json；Linux source_metadata09/clip_metadata_receipt.json、official_api_direct10.json、direct_media_head11.json，和本地对应短控制回执。
