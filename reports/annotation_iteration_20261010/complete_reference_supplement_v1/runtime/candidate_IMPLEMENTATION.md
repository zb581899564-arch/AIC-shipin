# 条件候选三个入口

实现仅新增 `candidate_` 文件，不改主控、common、训练、评价或历史科学模块。当前交付为本地源码与纯逻辑测试；未启动模型、processor、视频 decoder 或传输，也未生成真实候选包。

`candidate_static_preflight.py --config --lock --expected-lock --output` 在任何训练GPU启动前由主控调用。它以common phase=`train` admission后仅执行`candidate_support.prepare(contract)`，实际核验全部426/521 plan、registry/clock、source/space/科学依赖静态字节绑定，不需要尚未生成的final或quality，不创建candidate_output。成功status=`PASS_ACTUAL_CPU_STATIC_FIXED_426_521_CANDIDATE_INPUT_BINDINGS`只证明当前实际Linux静态输入通过，不代表模型、decoder、processor或ZIP运行验收。它不按CUDA_VISIBLE_DEVICES非空拒绝，当前CPU执行路径不导入相关库；异常原证据保留。

本地实际静态科学helper导入已检查9模块全部加载而torch/transformers/av/numpy/peft均未导入；本地synthetic preflight测试只检验入口逻辑，没有冒充Linux原文件验证。原v1验证历史保留，修订验证由`candidate_validate_implementation.py --version v2`另存。

`candidate_engine.py` 在 common admission、实际 final 288 tensor 训练回执及独立全24质量回执通过后，读取原 BW v3 固定426/521计划。116窗口使用历史 BW native decoder、精确 Fraction domain 与 BW video processor；405窗口使用原 V14 decoder/next_round video processor，grammar/parser 的 duration 保持原 `window_duration_sec` float。所有521回答新调用 final adapter，无旧时间 raw 入口。原B0、0..5段、greedy、input16384、output256与原像素预算保持。

raw中的`overview_adapter_disabled=true`声明本候选overview路线禁用；生成仍明确`final_adapter_enabled=true`，实际sole active adapter必须为`default`且生成前后全部288 tensor等于新final safetensors。独立CPU回放要求相同声明，不把该字段解释成关闭final adapter。

每个请求在生成前保存实际 native/processor/tensor SHA 输入回执，116还与历史已接受纯输入proof比较。raw 先独占落盘，再验证分数、grammar、原parser与物理帧范围。首真实回答之后，启动独立 `candidate_replay.py --first-only` CPU进程；通过才继续第2..521请求。

两支帧映射保持原协议：116使用原BW `exact_ranges`与原`native_segment_ranges`一致检查；405仅以原`native_segment_ranges`的float绝对PTS、原float窗口start及原parser endpoint映射为选择权威，独立CPU重建同一映射，不增加rational选集相等科学门。精确clock仍绑定输入ordinal/原PTS/像素与processor身份。主控实时只读示例video388/index2为60..66.72、CFR_LEGACY、duration=6.719999999999999，不能改成Fraction6.72。测试另覆盖精确5/6渲染为float0.8333333333333334时原float包含源帧的映射，防止新增rational检查改变旧规则。

`candidate_replay.py` 仅加载 CPU processor/tokenizer，不加载模型。原native decoder重新提取原生帧、processor重新编码，核对全部tensor SHA、精确PTS/像素身份、生成token解码、逐token原prefix grammar、原parser与native range。完整521回放引用已成功首请求CPU证明，不重复该成功decoder/processor，重新构建其余520。目标回执与逐请求CPU回执必须全新；失败保留，不自动恢复或重复已有成功。

`candidate_package.py` 只使用独立521回放的native frame范围选择帧；原31295时间独立空间源场四文件及stages必须固定SHA。重新按原全域shot/max-gap8验证requests，使用原field_contract全域插值后取新时间选择，不调用空间模型。原package_contract验证全部426行（合法空行保留），ZIP唯一`predictions.jsonl`并核CRC。原独立strict脚本另进程执行11项验收，再由独立`--verify-final-only` CPU进程复核实际新adapter SHA、全部绑定、全域空间组合、最终ZIP/CRC/内容，成功才保存completion。

## 需要主控投影的config字段

在既有config新增 `candidate_contract={"path": "<实际Linux候选contract JSON绝对路径>", "sha256": "<实际SHA>"}`。该文件遵守 `candidate_contract_schema.json`：

- `plan`：原 `balanced_two_window_risk_v3/input_01/rematch_plan.json`；固定426/521/116/405。
- `manifest`、`clock_registry`：原 `baseline_pts_v4/scan_01/clean_manifest_v2.json` 与registry。
- `changed_cpu_acceptance`：原 BW v3 `cpu_acceptance.json`，仅116 rematch纯输入proof，无旧时间raw。
- `space`：原 `b_score_aligned_package_v4/rematch_01/field_frames.jsonl`、`field_shots.jsonl`、`anchor_requests.jsonl`、`anchor_output.jsonl`、`schedule.stage.json`、`spatial.stage.json`。
- `strict_loader_root`：原 `baseline_a_pts_v1/vendor/frozen_strict_loader`。

所有ref严格为`path/sha256`，这些实际输入固定SHA见support的FIXED_INPUT_SHAS/FIXED_SPACE_SHAS。plan.input_ref原四平铺键必须对应manifest/registry。registry每个clock_arrays与manifest每个source media必须实际SHA入lock，保持历史CFR/native branch与原packet-end判断，不重新更改clock批准。

除common已要求依赖外，lock还须冻结support的DEPENDENCIES列表：BW common/native、V14 native_segment_contract、原space package/frame/field_contract、原independent_validate脚本及strict_loader_root全部文件。runtime所有`*.py`（含candidate测试）原字节必须冻结；schema/本说明/实现验收manifest可供主控归档，不作为模型输入。

## CLI与回执

三个入口共用 `--config --lock --expected-lock --final-receipt --expected-final-receipt --quality-receipt --expected-quality-receipt`。replay另需`--output <candidate_output_dir>/independent_temporal_replay.json`；package另需`--replay-receipt --expected-replay-receipt`。内部首请求/最终ZIP子进程由入口串行启动；主控调用参数不用改变。所有入口以 `python -B` 调用。

quality必须为本轮evaluation目录的 `independent_quality_receipt.json`，status=`PASS_INDEPENDENT_CPU_FINAL_ONLY_EVALUATION_RECONSTRUCTION`、24实际重构、质量PASS，严格绑定本config/lock/final/eval及每个实际raw/done/CPUinput。evaluate摘要不代替独立质量回执。

最终completion status=`PASS_COMPLETE_FIXED_SILVER_426_CANDIDATE_ON_LINUX`，包含records426、fresh_temporal_model_calls521、当前final_adapter_sha256、all_11_strict_checks_passed=true及actual candidate/zip_bytes/zip_sha256。线上成绩仍UNKNOWN，uploaded=false。

`estimate_output_bytes(contract)`仅标准库CPU读取实际plan窗口大小/64输入数量、116 proof实际字节、48个24eval raw/done实际大小、全部原空间文件字节与输出256token预算，返回正整数输出占用估计。它不加载decoder/model，不提出固定容量准入线。资源/费用终态与总控保留由pipeline_controller负责。

## 已验证与尚未验证

`python -B candidate_test.py`仅验证纯逻辑：双窗边界/不适用域/floor64、原parser空段与异常、精确半开native membership、source ordinal映射、float/Fraction两种原duration语义、SHA/回执防覆盖与动态字节估计。synthetic测试不等于真实521 GPU/CPU/11strict或质量验收。完整Linux输入合同、真实训练final及独立质量回执尚未在本机配置，因此入口仅实现，未经真实模型运行；任何后续运行都须主控在新freeze后按授权单次执行。
