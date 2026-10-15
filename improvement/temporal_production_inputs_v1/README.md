# 正式时间输入准备层原型 v1

本目录只提供自动输入准备与读取接口。当前仅代码和纯合成检查；未部署，正式426媒体读取/解码、processor、GPU调用均0。总控冻结开发阶段统一 endpoint adapter角色、官方规则回执、完整生产请求表和新缓存许可后，才可启动实际准备。

`project_legacy.py` 从原B已接受521窗/665段与426旧完整clock自动投影身份；不读取视频内容、GT或空间框内容。全部1995逻辑请求事前固定：每段 START/END 原端点±3秒 native64、VERIFY原始完整≤30秒窗64帧。不足64的端点预登记UNKNOWN原点，不扩大窗口。LEGAL_EMPTY窗口和全部426源覆盖保留。批量大小只允许按实测容量改变，不按结果改变来源、请求或consumer。

`prepare_source.py initialize` 创建独立 `production_stream_vN` 永久缓存根与事前RGB lease依赖图。`source --source-id ID` 串行一次新AV遍历：取得全部真实PTS/原origin/正末duration，同时收集该源冻结请求的ordinal并集；另存完整测量，再核对旧clock。416个 `LEGACY_CFR_N_DIV_FPS` 末端仅是旧计划见证；不能自称实测原生duration。差异或缺duration明确STOP，不修改旧clock、时间标签或空间场。VERIFY新的原窗RGB必须与旧pixel evidence逐帧一致；不一致不自动换decoder。此严格门尚未在正式媒体检验。

每个实际consumer独立生成完整prompt/token输入并真实普通processor一次，使用冻结原B native时钟接口与实际grid/pixel/token预算，16384输入token上限。131072是processor配置项，不称每帧pixel预算。每个完整CPU tensor dict永久保留，经critics所有 `production_stream_cache_v1` exact bit-LUT+gzip恢复核对；不支持或unique>256由库保留原gzip，dtype/stride/storage offset/alias、NaN位型均不变。视觉仅实际字节和完整7字段context identity相同才dedup，不能宣称665 VERIFY必然压到521输入。当前正式旧RGB/tensor为缺失，新操作明确记为 `new_native_RGB_materialization`。

`consumer_api.load_consumer(reg,id)` 返回永久完整CPU dict、请求metadata、manifest/CPU proof ref与冻结角色；`gpu_input(reg,id,device)` 通过 `tp_device.transfer_exact` 复制完整底层storage并还原原view，核实际CPU/GPU全签名。此接口不加载模型、不开job、不证明实际weights角色；模型driver仍须绑定原8.78245912B、144层activation、288adapter身份、prompt/grammar/raw与唯一账本，并独立prefill。

`replay_input.first_input_replay(reg,id,resource_ref,ledger_ref)` 在真实自然completed/exit0唯一GPU终态后，以不同PID首次从仍存在的新RGB走普通processor；核完整dict实际位型、token/grid、native/runtime evidence相同，写INPUT-ONLY证明。它不把input-only证明当作输出token/parser/native/实际weights验收，不调用 `accept_consumer` 或 `release_rgb`。总控独立输出重放需与此证明合并，按库 `CACHE_FIRST_INDEPENDENT_REPLAY_ACCEPTANCE_V1` 完整schema及其冻结 `independent_replay_code_sha256` 登记，全部consumer首次完整验收后才可释放对应新RGB。旧RGB/proofs/clocks/raw与新canonical永久保留；本目录不实现清理runner。

新控制根固定 `/home/inspur/aic_video_work/twenty_hour_five_20261014_v1/temporal_production_inputs_v1`。registration字段由总控冻结：schema `TEMPORAL_PRODUCTION_INPUTS_V1`；scope `FORMAL426_AUTOMATIC_NEW_INFERENCE_INPUTS_ONLY`；`training/test_GT_read/old_successful_outputs_modified=false`；`request_algorithm_frozen_before_any_new_model_results=true`；原plan/accepted_temporal/clock_registry/空间场refs；`required_code_files`全部自身及hashbound v3、VERIFY、cache库文件路径→SHA；三library目录；official_rules_ref；selected_uniform_development_role_ref；endpoint角色TIME_ENABLED或BASE_DISABLED、VERIFY TIME_ENABLED；`main_agent_actual_production_preparation_approved`；cache_root/cache_policy。cache_policy另按critic库完整PRODUCTION新root/永久exact/事前ephemeral/first replay SHA门冻结。

未来获准Linux CPU命令（不是此次执行）：

```text
python project_legacy.py --registration ROOT/registration.json
python prepare_source.py initialize --registration ROOT/registration.json
python prepare_source.py source --registration ROOT/registration.json --source-id FIXED_ID
```

容量按当时available bytes、该source实际RGB并集、实际processor size、下一批永久和临时完整tensor上界核对；不使用固定GB门或压缩比许诺。容量不足保留全部产物，禁止量化、删除canonical或按结果换请求。完整源尝试/编码/首次重放不能自动重复；失败需总控独立恢复范围，已成功操作继续引用。
