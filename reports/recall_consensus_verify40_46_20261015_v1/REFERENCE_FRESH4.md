# 双视角明确KEEP交集：首次fresh4参考接入

唯一实现：`improvement/recall_consensus_verify40_46_v1/prepare_fresh_reference.py`。目标Linux根为 `/home/inspur/aic_video_work/recall_consensus_verify40_46_20261015_v1`，下文记NEW；旧根 `/home/inspur/aic_video_work/recall_expansion_verify40_46_20261014_v1` 记OLD。

本次只交付代码、接口与静态/必要合成检查，不SSH、HEAD、GET、真实解码、clock测量、processor、模型或launcher。7581 B开发代码包与已完成8源CPU开发不是fresh确认。旧单KEEP独立确认失败保持STOP；旧8源全部已曝光，仅作本轮开发，不能重新称盲测。VERIFY40.46包不改。

## 固定来源与预算

按旧 `new8_source_registration_01.json` 的全局预留顺序，排除真实旧10媒体（含A0R3KFXD_BU、zT6ITDwPi0w两原生域拒绝以及8个已曝光来源），剩余6个恰按下列顺序。此处不沿用旧dev/confirm分组：本轮前4均是新确认，后2为全组共用的顺序工程替补。各行保留 `prior_registration_group` 供历史追溯。

| 本轮角色 | video_id | 原登记字节 | 作者duration原值 |
| --- | --- | ---: | --- |
| selected0 | v_rrNJt73BG_8 | 4476707 | 57.1 |
| selected1 | v_17nr8u_ze0o | 8183799 | 57.28 |
| selected2 | v_isUCIXYjOXE | 4851500 | 45.05 |
| selected3 | v_IGamNJ5yIh4 | 2931217 | 39.59 |
| reserve0 | v_NNuIaUFYGCE | 1673389 | 52.08 |
| reserve1 | v_pHZogKGkc9o | 2275440 | 41.63 |

初始4文件20,443,223 B；最坏6池24,392,052 B，仅Linux公开镜像→Linux新载荷，不含已发生旧10费用，也不是旧104,730,788 B池。代码只尝试完成4个slot所需成员；明确404或原生clock/原参考域不合格时按reserve0、reserve1替换，不能按预测、票的质量或分数换源。网络超时、403/5xx、过期/不一致ETag、字节/身份重叠、磁盘或环境故障都停止并保留材料，不触发替补或重试。

所有媒体路由由主代理预先固定在NEW/public_routes.json；源地址严格为旧registry中的公开bucket原URL，目标为其正常HTTPS `.cdn.hf.co` 公共重定向和ETag。代码本身不HEAD、不读凭据、不自动redirect/retry、不另搜许可或联系作者。下载前固定全部6身份/size，下载后计算真实新文件SHA，排除原known hashes、旧10既有receipt记录SHA及本轮已成功文件SHA。原镜像与作者编码字节完全相同仍未证明；hidden alias/语义重叠仍UNKNOWN，不夸大元数据隔离。

## 单注册文件：NEW/fresh_confirm_registration.json

采用主代理和CPU/runtime最终统一的单文件方案；允许加入初始冻结的runtime、gpu_budget、deadline等字段，本文不创建第二注册，不回填已冻结protocol。

必须字段：

```text
schema: RECALL_CONSENSUS_FRESH4_REFERENCE_REGISTRATION_V1
status: REGISTERED_FIRST_FRESH_CONFIRM_MEDIA_NATIVE_REFERENCE
group: confirm
expected_accepted_sources: 4
maximum_media_pool_bytes: 24392052
route_acquisition_method: HEAD
windows_video_body_bytes: 0
expected_prior_media_count: 10
selection: [4条完整canonical source row]
ordered_engineering_reserves: [2条完整canonical source row]
selected_confirm_ids: [上表前4 video_id，原顺序]
ordered_confirm_engineering_reserve_ids: [上表后2 video_id，原顺序]
protocol_ref: {path: NEW/protocol.json, sha256: ...}
development_selection_ref: {path: NEW/selection_before_fresh_confirmation.json, sha256: ...}
development_result_ref: {path: NEW/development_01/result.json, sha256: ...}
authorization_ref: {path: NEW内本轮明确授权回执, sha256: ...}
prior_source_registration_ref: {path: OLD/new8_source_registration_01.json, sha256: ...}
public_routes_ref: {path: NEW/public_routes.json, sha256: ...}
annotation_file_path / annotation_file_sha256: 与原registry完全相同
known_exclusions_path / known_exclusions_sha256: 与原registry完全相同
old_exposed_and_reserved_ids: 原registry旧exclusion集合并集旧10实际ID
prior_media_receipts: [{path,sha256}, ...准确10条]
required_code_files: {绝对实际代码路径: SHA256}
required_files: {绝对既有文件路径: SHA256}
```

原registry SHA为 `2521b9901e9e432d5bdd27f0ef57fae3fec6ccc66f659bed06416f0ff838b1ad`；本轮protocol SHA为 `d71d191c2525402872a866ab513e84c1ee032fdb14858ff9034bdb32f93cb236`。源接入不使用旧单KEEP协议、旧4dev+4confirm门或旧reference_03作为新确认。

生成来源行可安全调用纯函数 `expected_candidate_rows(prior_registry, prior_ids) -> (selected4,reserves2)`；它不联网或读媒体。行格式为原完整registry行，加 `prior_registration_group=原group`、`group='confirm'`。按完整字典匹配，video/youtube ID、provider URL/size、原作者duration和selection_hash不变。

旧10条ref由主代理给定，代码不glob：OLD/dev/reference_02内准确6条与OLD/confirm/reference_03内准确4条 `*/media_receipt.json`；汇总出处为本地 `prior_media_and_routes_02.json:prior_media_receipts`。代码逐条核receipt原文件SHA、原登记ID/URL/bytes、其中已记录的真实媒体SHA和媒体存在/大小，不再次哈希/解码旧媒体。包含原生域失败但已下载成功的2份，旧费用不归零。

required_files至少包含所有ref原件、原作者JSON、known exclusion、10 receipt、全部required_code_files；可按runtime要求再含全部新py、原config、processor/CV资产。源接入强制锁定自己文件与既有 `/home/inspur/aic_video_work/videoxum_reference_iteration_20261013_v1/code/native_profile_01.py`、`native_profile_04.py`，并核本轮protocol中开发代码SHA。该阶段不需要未来新media/clock/reference；它们完成后进入新的CPU/source_lock闭包，避免循环SHA。

## public_routes.json接口

顶层 `windows_video_body_bytes=0`、`routes`准确6条。每条含 `video_id, initial_public_url, bytes, metadata_only=true, status`；status仅 `PINNED_NORMAL_PUBLIC_REDIRECT` 或 `PUBLIC_OBJECT_404`。前者另含 `publisher_redirect_url, etag`。可附带既有HEAD出处/时间字段；代码不靠缓存存在便声称签名持续有效，真实GET严格核HTTP200、ETag、Content-Length、无压缩、目标host。直接CDN实际HTTP404保存不读响应体的404回执后才允许工程替补。其它失败停止，不能把网络失败登记成404。

主代理决定是否使用仍有效既有HEAD或仅刷新必要小元数据；本实现不执行或重复HEAD，Windows媒体body始终0。

## 参考语义与原生域

原JSON固定 `/home/inspur/aic_video_work/videoxum_reference_iteration_20261013_v1/metadata_02/val_videoxum.json`，SHA为 `2832f423ff5fd768a979665e30345a56f1723aacc1821986b5ec042bed30f556`，不重新下载。运行时仅为尝试过的固定来源导出原vsum，保留每个原区间的十进制端点。评审数从实际vsum结构取得，至少2且各事件相同，不硬编码10评审、20来源或旧分组。

scope保持 `EVENT_TEXT_GUIDED_HUMAN_SUMMARY_PROXY_NOT_GENERIC_HIGHLIGHT_OR_ORDINARY_GOLD`：这是事件文本引导的人工摘要代理；事件文本不送模型。未选区间不能称普通，不能把它改称通用高光真值。

未来每个新媒体只调用一次原 `native_profile_04.measure_original_video`：唯一video stream、原零origin、每帧精确PTS、实际末帧duration、真实尺寸/fps必须可证。完整clock不平移，physical_end取真实末PTS+末duration，不取作者名义duration/容器时长/fps猜终点。原人工区间必须满足 `0<=start<end<=physical_end`；不截断、补零、epsilon或拉伸。原baseline纯native64网格及完整原源0起15/7.5 overlap每窗都至少64不同真帧；不足只作为预登记工程域拒绝。此阶段不生成RGB/processor输入。

## CLI、输出与状态

获主代理实际运行准入后，CPU子进程自身设置 `CUDA_VISIBLE_DEVICES=''`，用既有Linux Python执行：

```text
python NEW/code/prepare_fresh_reference.py --root NEW
```

代码要求Linux主机 `inspur-NP5570M5`、唯一NEW根、尚无reference_01或成功pointer；拒绝隐式恢复/重复成功材料。每源输出 `route.json, media_receipt.json, clock.json, reference.json`；工程拒绝另有 `source_rejection.json`，失败和已成功材料全部保留，不覆盖。

完整4个slot成功后：

- NEW/confirm/reference_01/completion.json，`status=PASS_NEW_PROXY_MEDIA_NATIVE_SECONDS_NOT_CPU_INPUT_OR_GPU`、`group=confirm`、accepted准确4条，accepted字段沿旧 `video_id,slot,group,media,clock_path/SHA,reference_path/SHA`。
- `registration_sha256` 和 `source_registration_sha256` 均绑本轮单fresh_confirm_registration实际SHA；原registry另为 `prior_source_registration_sha256`。`development_selection_sha256/development_result_sha256/protocol_sha256`各绑本轮真实原件；统计本轮新payload/reserved bytes和旧10既发bytes，不混池。
- NEW/reference_completion_confirm.json 为 `{path,sha256}` 指向上述completion。未完成则只有failure及既有成功材料，不能生成4源PASS pointer。

receipt保持旧字段 `video_id,path,bytes,sha256,public_url,group='confirm',known_ID_and_byte_separation=true`；还保留 `original_author_byte_identity_verified=false, hidden_alias_or_semantic_overlap='UNKNOWN'`。CPU代理可直接沿此schema锁全部4源media/clock/ref/route及每窗新输入，不引用旧四源ref03。

开发PASS和参考接入PASS都只允许本次独立确认的下一步。此实现输出 `GPU_admitted=false, production_admitted=false`；fresh模型/首次QA、固定科学门和最终426真实逐帧逐框/参数字节验收仍由各自协议独立完成，不把接入成功当确认或线上提分。

本次必要检查已通过：AST/仅stdlib导入；用既有原registry和主代理旧10 receipt元数据验证固定6顺序与24,392,052 B总量；2评审合成schema与严格native域正例；开发precision门失败、人工端点越域、非零origin、overlap不足64帧、预算超限、旧10分母缺项等6个拒绝检查。没有导入requests/av/torch/transformers，没有任何真实网络、decode、processor、模型或新标签读取。
