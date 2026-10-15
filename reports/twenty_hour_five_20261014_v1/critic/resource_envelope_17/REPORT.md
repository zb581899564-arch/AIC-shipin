# 既有证据容量包络17

一次Linux纯元数据采集自然exit0：读取37个既有V4 dev CPU proof及其SHA、已保存BASE实际model identity、现存checkpoint index/4个shard stat、实际loader代码和BASE/TIME resource/snapshot。没有读取input tensor/RGB或权重body，没有全权重hash、模型加载、encoder/decoder/GPU或旧pure重跑。11,190B新代码传输SHA/AST通过。

CPU整prepare process已实测最大RSS 2,561,208KiB=2,622,676,992B。它包含imports、已经准备的输入及分配，不是单独import峰值。将其全部作为per-process overhead再与source特定union RGB/tensor/codec上界相加，会保守重复计算一部分输入成本；不把它冒称正式全426实测峰值。37实际最大logical输入为286,482,312B，未重新加载tensor。

GPU cold-load process HWM未记录：现存自然completed BASE/TIME resource和BASE wait snapshot没有RSS/HWM字段。保存的steady RSS、整机used-memory或GPU VRAM不替代cold host HWM。新schema `GPU_HOST_CODE_BOUNDED_RESOURCE_ENVELOPE_V2`，status `OBSERVATION_UNAVAILABLE_WITH_CODE_BOUNDED_ENVELOPE`，cold_load_HWM_observed=false、observed_BASE_host_peak_rss_bytes=null、observed_peak_proof_ref=null。controller须按独立新schema接纳有证据的推导，不要求编造旧字段。

host scheduling包络为27,013,789,672B（约25.16GiB），分量是：

|分量|bytes|证据性质|
|---|---:|---|
|base BF16|17,534,247,392|实际loaded identity参数8,767,123,696×2；loader明确bfloat16；index total_size一致|
|最大checkpoint shard|4,999,831,048|4个原shard当前stat，未读取body|
|CPU整process peak|2,622,676,992|37原CPU proof实测最大，保守作imports/overhead代理|
|单完整prefill code上界|402,916,864|16,384 input-token门、merge2×2、1536 float32 patch列、IDs/mask/grid|
|adapter双copy余量|245,366,784|实际15,335,424参数，显式按每值8B两copy，非实测峰|
|三个prefill缓存/签名copy余量|1,208,750,592|明确3×上项，非实测峰|

同model architecture metadata与37签名核了merge2、patch16、temporal2、float32列1536和patchrows<=4inputtokens。上界仅适用于相同loader/weights/processor与16,384 cap，不是任意未来代码的数学allocator绝对最大值，也不是已观测cold HWM。当前cuda-only/low_cpu_mem_usage/no-offload loader不预留新的checkpoint disk副本；每批实际raw/proof输出和source canonical/staging/transient另行预留，不与此混淆。

Linux驻留 `CAMPAIGN/resource_envelope_17`：CPU envelope1121B SHA `c90a7c7a169d9f4a67e5e78225b829e920d59c1b76df9cf4d787d9af90a52e60`；GPU envelope4869B SHA `4be92aa2abfc8fe548c11daa70ad886e132eba7d27384454b98b97f40124cfc5`；shard manifest3128B SHA `9909dd2f6363c5fb7850c6bade0b85a2eee423f7debfe53288eb79ad74c97a88`。completion SHA `411145a0f787125c3379c77239630f25a272fd5e161264dd0842f866525af2ba`。仅4份10,992B小回执回Windows，ref大小/SHA一致；37逐项观测21,245B保Linux。

第一批仍须由主控冻结完整membership/source消费者与实际资源估计，结合live可用memory/disk/CPU和已经开始任务的reservations判断。此采集没有最终批manifest或真实source prepare，不宣称第一批FIT/实际生产PASS；容量不足等待或STOP retain，不删canonical/旧成功、不降precision。下一次正常首批GPU job可顺带记录其真正process HWM作为后续实证，不为补旧HWM另跑cold-load模型。批membership与算法不能因早期回答改变。
