本轮外部补召回固定协议保持：4开发/4确认，15秒视图、7.5秒步长，新增仅KEEP。

媒体初次主站HEAD网络失败保留，随后仅Windows取得12KB正常公共CDN元数据，视频正文仍Linux直达；actual下载6媒体38129391B，其中4通过原生参考端点、2越界按事前同组替补。

CPU inputs_01的首个primary encode已真实成功并保存22,191,038B lossless cache，但后续过窄dict检查拒绝BatchFeature，原encode_evidence未保存，CPUproof0/GPU0。旧cache、PNGunion、NPZ/meta、失败全部保留。

显式input_recovery_registration_02绑定十项继承产物与实际已成功primary1/RGBunion1/firstQA0。新first-input QA在独立进程按已登记原处理器从NPZ复核，与旧cache逐bit一致才形成真实新evidence；它是第一次独立QA前移，不覆盖旧cache，也不声称旧receipt存在。GPU后该view直接引用已通过QA，只做输出token/grammar/parser/native复核；其他视图仍第一次QA。

新prepare_inputs_recovery_v2只引用首源全部PNG、首view缓存，其他3源首次decode、其他唯一views首次primary encode。新primary返回立即保存evidence；新inputs_02/admission_02/chain_02及v2 unique GPU jobs保留旧inputs_01/chain_01。所有门、源序、quality协议不改；未过开发/独立确认/固定40事实否决，不进入426生产。

2026-10-14T14:28:06Z 一次稍后严格SSH重试仍为TCP22连接超时，远端未执行读取或改动，SCP结果仍未确认。connection_retry_result_01.json保留具体错误；本次临时aic已由App实际deleted，不再重复轮询。GPU/新模型/新ZIP仍0，恢复代码及全部成功缓存保留。
