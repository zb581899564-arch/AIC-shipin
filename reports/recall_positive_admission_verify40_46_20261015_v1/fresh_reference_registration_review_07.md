# 首次新4源确认：开发回执与来源接入审查

日期：2026-10-15。原 `reference_review.md`、`reference_candidates.json`、已部署positive代码和v2协议均未修改。本次只新增 `improvement/recall_positive_media_v1/*` 与本文件；不SSH、不实际HEAD/GET、不运行媒体、clock、CPU输入、模型或launcher。

## 开发回执：原4、原8门实际通过

只读 `dev_completion_receipt_06.json` 与已接收的 `dev_completion_summary_06.json`；后者17,596B，传输绑定SHA `4137b3d8f1b74651db8ed8b2f6acb846cf6f081f2e272be925f73273172ea3b4`，回执记录Windows大小/SHA匹配。实际原4次序为 `v_vfJnUQ9Tax0`、`v_8tlLBffNjf8`、`v__CMIO5R_OGA`、`v_voaGOm-rl9Y`，没有挑选更好来源或删去零变化来源。

本审查者从四源各指标的exact Fraction独立重算等权macro及差值，与回执完全一致：F1增量0.0068243740939798155，recall增量0.02931783730641039，precision增量0.0029801271049039665；两来源共新增90原生帧，逐源最小F1差0。四源完整分母、原macro F1≥0、各源F1≥−0.01、macro recall增量≥0.01、macro precision≥0、全评审baseline recall保留、baseline原生帧保留及至少2来源作用八门均通过，未改变 `protocol_v2.json`。

回执同时绑定10个新实际调用、10个首次输入QA、10个首次输出QA，7 UNKNOWN/3 KEEP；唯一账本exact、GPU completed/exit0，费用293.44747891742736秒。没有新媒体解码或vision processor调用，旧成功未重复。开发源均曝光，结果明确 `source_metrics_exposed_first_time=false`，不是新盲测。fixed40、426和新ZIP仍0。

**开发PASS允许冻结后的首次新4参考接入；不允许直接生产。** 本审查没有独立重新读取远端raw或重放任何成功阶段；精确复算对象是已接收并绑定的开发结果回执。

## 新来源、许可与路线

固定候选继续原盐及source-hash次序，来自开发前冻结的 `reference_candidates.json`；不是按开发分数或错误个例选源。旧16池仅剩2个未用来源，因此延伸既有ID-only前缀而非复用旧确认组：

| 角色 | 来源 | 历史及本次HEAD字节 |
| --- | --- | ---: |
| confirm0 | `v_NNuIaUFYGCE` | 1,673,389 |
| confirm1 | `v_pHZogKGkc9o` | 2,275,440 |
| confirm2 | `v_5FM_xJGb-Tk` | 18,425,235 |
| confirm3 | `v_YW3mCNKVaa4` | 19,389,367 |
| reserve0 | `v_1VDNFR3vQR4` | 4,607,018 |
| reserve1 | `v_SFfB6qvT5FI` | 3,549,249 |

首4共41,763,431B，全部6池49,919,698B。旧64保守登记/预留与实际14媒体合成78身份排除；另核已知692个YouTube IDs与1149个媒体SHA，下载后再加旧14媒体已记录SHA及本次已取得SHA，拒绝整文件重复。来源元数据必须与原候选文档完整字典相等，且候选文档SHA必须出现在已完成dev registration的 `required_files` 中。不得只保留集合而改变备用次序。

本次范围继续既有用户公开来源→Linux直达的私人研究验证许可，49.9MB六池已由主线程确认覆盖。沿已核VideoXum Apache-2.0标注及TornadoLabs academic source terms/原上传者媒体权利；不训练、不再分发媒体、不主张商业授权。未重复同源许可搜索或联系作者。

只读主线程新增的小量回执：`fresh_public_routes_windows_09.json` 六条均为原公开对象的正常CDN重定向，元数据only；`fresh_cdn_linux_route_probe_10.json` 对同六条CDN均HEAD200、长度与表中一致，主机为inspur-NP5570M5。其前Linux初始域名失败保留于08回执，不能抹去；本入口只复用已成功获得的CDN地址，不再次HEAD原域名或CDN，不修改网络、代理、SSH或服务。Windows及Linux HEAD均非媒体载荷，不能把HEAD成功称已收到媒体。短期签名URL不在本报告输出。

原人工任务仍是事件文本引导摘要代理；模型不接收事件文本、字幕或摘要答案，人工未选不叫ORDINARY。known-ID/全文件SHA隔离不能证明隐藏别名、子片段语义或底座全部预训练隔离；这些继续UNKNOWN。

## 独立媒体CPU入口

源码为 `improvement/recall_positive_media_v1/positive_media.py`，部署位置必须为：

`/home/inspur/aic_video_work/recall_positive_admission_verify40_46_20261015_v1/fresh_01/media_code/positive_media.py`

入口 `python -B positive_media.py --root /home/inspur/aic_video_work/recall_positive_admission_verify40_46_20261015_v1/fresh_01`；实际Linux主机必须inspur-NP5570M5、CUDA_VISIBLE_DEVICES必须为空。独立 `media_registration.json` 使用 `POSITIVE_FRESH_MEDIA_REGISTRATION_V1` / `REGISTERED_POSITIVE_FIRST_FRESH_MEDIA_NATIVE`，绑定实际dev结果c7fd…、dev登记7a72…、dev selection815f…与原v2协议8736…，不调用旧consensus注册或准入。

注册必须给出主线程提供的annotation/known-exclusion、14个原 `media_receipt.json`、两个原source-scope、原native_profile_01/04及全部实际新代码的path/SHA闭包；旧媒体只采用原字节绑定receipt内已记录SHA，不重复下载、解码或重新哈希旧媒体本体。主线程已取得的 `fresh_existing_dependency_refs_11.json` 提供这些小量原依赖引用，本审查未远端重复取得。

每源只执行一次固定CDN GET，禁止自动redirect/retry/resume、账号凭据和Windows媒体中转。状态200、原ETag、精确Content-Length、identity编码以及最终HTTPS host/path均须匹配注册；文件完成后核全文件SHA和长度，再一次调用原native_profile_04测clock。使用真实PTS、末帧duration、physical_end及原零origin；原人工秒端点不裁切、不拉伸、不加epsilon，所有实际评审从vsum轴动态读取，baseline及15秒/7.5秒窗均须至少64不同真帧。

只有实际/预登记404，或明确的原生origin/PTS/末duration/geometry/秒端点/native64域拒绝，才依reserve0、reserve1次序替换。未知schema错误、未知ValueError、PyAV解码/I/O异常、403/5xx、超时、ETag/字节/SHA冲突及CPU环境失败停止；不按模型、质量或是否有新增效果换源。失败保留完整文件、partial、已成功clock、reference及accepted槽，不自动恢复或重跑。

完整4源后输出 `fresh_01/reference_01/completion.json`，状态 `PASS_POSITIVE_FRESH_MEDIA_NATIVE_SECONDS_NOT_INPUT_OR_GPU`，group confirm。每accepted含video_id/slot/group、media(path/bytes/SHA/known_ID_and_byte_separation)、clock path/SHA、reference path/SHA；另绑定source_registration_ref/dev_selection_ref/dev_result_ref及原v2。`reference_completion_confirm.json` 仅指向该完成回执。本状态不是CPU输入或GPU准入。

本审查者运行了纯fixture：AST、固定4+2身份/字节/次序、三评审动态schema、精确越域/零origin/native64拒绝、总量cap、路由错误，以及mock单次200/404/503、改变CDN path、整文件SHA重复时partial保留，均PASS。真实已绑定dev结果/protocol/ref元数据与新验证接口兼容性也通过；selection/registration结构用fixture，不冒充远端实际注册验收。

源码冻结：positive_media.py 30,538B，SHA `831f4d3e0da2a9351a172b080157622bcfc5debd12444df60e047ff04f6818eb`；check_pure.py 5,968B，SHA `23eadc78ec2f4fee206889f20c52919b6e7b2c3c56652ceb5240d5e0bcf18ce4`。这两个文件之后不再改动，供主线程实际部署manifest绑定。

## 新fresh CPU/模型链只读接口审查

已只读新 `improvement/recall_positive_fresh_v1/fresh_registration.py`、`source_plan.py`、准备/首次QA入口及chain的来源权限接口。没有修改该代理负责的文件。

`media_files` 已核精确 `fresh_01/media_registration.json` 与 `fresh_01/reference_01/completion.json` 路径、新schema/status/group、完整4源，以及source_registration_ref/dev selection/dev result相等；selection和工程备用与已绑定原候选文档完整相等。再次检查已知ID、旧78身份、旧14及已知媒体SHA、四源之间字节重复，核媒体全文件SHA/大小与clock/reference位置。该检查不会读取人工reference内容，只绑定其字节。

新fresh registration绑定实际devPASS及未变v2门，完整新源码和原runtime/processor/config/CV资产在首个CPU工作前冻结。source plan保留原baseline、15/7.5窗及原native64策略；准备与首次QA只使用媒体/clock/固定输入信息，reference标签不参与采样或模型输入。全原生输入首个独立QA在B0前，全部旧VERIFY新token独立QA在其GPU前；GPU后只做新输出QA，不重复首次输入QA。最终把新完成证据交给已冻结positive合同；四个新人工指标只在链末首次评价，没有途中按分数换源或改门。

本审查建议的source-authority缺口已补上：原实现仅允许candidate集合，新实现同时检查上述精确媒体stage路径/schema及selection/reserve字典顺序，不能误接旧root或变更来源登记。现阶段本审查范围内没有剩余静态致命接口问题。运行器代理报告AST及纯source-plan/native64/clockshift/容量/QA顺序检查通过；本报告将其与本审查者亲自运行的媒体fixture区分。

**可由主线程先独立部署媒体入口，再按真实完成回执和实际资源准入新fresh CPU/模型链。** 不把本静态审查、HEAD200或成功启动视为source/native、输入、模型、八门或固定40通过。新确认失败即保留STOP，不在同4源调参复试；新确认及固定40事实均通过后才允许426生产。实际媒体/clock/CPU/GPU/确认及封包结果由各自后续回执负责，本报告不预判PASS。
