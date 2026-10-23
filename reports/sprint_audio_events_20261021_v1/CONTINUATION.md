# 最新：两种输入A0均已自然完成，固定融合停止

先读RESULT12.md、current_state.json及execution_closeout12.json。初始8PANN/16TIME和native32k10的8PANN/16TIME、全部独立QA/唯一ledger均完成，禁止再次启动controller/remaining06/native_controller10或重做任何成功下载、解码、输入、模型和评价。

原视觉整源F1 .241387，16k缓存音频 .233737，原音轨32k .236078；正确均优于错位但未优于原视觉，不生产。原声片段F1 .262795是局部结果，不能替代整源收益。CONTROL5保持T，GPU已释放，40.47保持，新ZIP0。

本轮S1/S0/T资产门/A0都已到各自止步条件，整体提分目标仍未完成。下一次只能以实际新的匹配监督或不同机制的新支撑登记，不扫提示/事件类别/阈值、不追加旧摘要训练，也不因GPU空闲封失败包。不要把下方过程历史RUNNING作为重启依据。

--- 以下是过程记录 ---

# A0接续入口

Linux唯一根：`/home/inspur/aic_video_work/sprint_audio_events_20261021_v1`。当前按真实最新`completion.json`/`review.json`或`remaining06_failure.json`接续，不用历史PID判断失败。

## 已完成

- 作者仓库固定`d2f4b8c18eab44737fcc0de1248ae21eb43f6aa4`，源码MIT；精确Git树/归档成员验收。
- Zenodo3987831权重`Cnn14_DecisionLevelAtt_mAP=0.425.pth`为CC-BY-4.0，331757477字节，MD5作者一致。实际直连137.138.121.78/eno2，空ProxyHandler。旧raw超时、API限流、错误Accept406、wheel许可成员名错误均原样保留；只恢复缺失阶段，无中继下载。
- PANN严格91张量加载、FFT与原卷积前端/原logmel独立公式通过；实际82917948参数，完整保护基线合计8865475397≤9B。
- `inputs.py`首次把旧ceil采样数写成floor，0新32k成功/0GPU时停止；`code_v6`仅修正此契约并采用原成功模型前端检查。原标签、原生PTS和旧缓存不改。`remaining06_launch.json`为唯一显式剩余恢复启动。
- 8份真实32k输入、8个PANN前向、原coarse→framewise重复/末帧补齐的首次独立输出复核完成。10ms网格不是精确事件时间GT。
- 16份正确/同源半窗固定错位增强输入已通过CPU验收；原视觉张量与TIME不改。`descriptor_control_diagnostic07.json`确认真实全部时间槽都产生不同控制证据且音频内容多重集合相同。

## 当前唯一任务

`pann_audio_correct_shift_TIME16_20261021_v1`，max1800秒。读取Linux`RUN/controller/同名.log`了解首次生成进度；最终resource与唯一gpu_ledger一致才成功。外层controller日志不随生成刷屏并非卡住。不得重复launcher或成功调用。

它自然成功后原链只做首次独立token/grammar/native和整源重叠去重评价，写`review.json`、`completion.json`，**没有自动426或封包**。评价四个历史曝光来源的原TIME控制与正确/错位音频，所有原评审平均；不是40.47精确外部复现、独立盲测或官网联合分。通过也须独立审查全量准入，未通过不扫事件类别/提示/阈值挽救。

40.47原ZIP和依赖保护；CONTROL5同startticks状态T绝不恢复。仅必要小代码/短回执SSH，模型/音轨/输出均留Linux，不创建Goal/定时或官网自动提交。
