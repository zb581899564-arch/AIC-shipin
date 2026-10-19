# Summary双video合同05独立只读审查

范围仅为本地`summary_contract.py`和`prepare_summary.py`，为理解继承目标另读`target_contract_feasibility_v3.py`的序列化代码；不读取目标记录/标签值，不执行数据统计、测试、processor、模型、QA或远端命令。代码由其他代理继续开发，本报告不修改任何代码或旧产物。

**结论：未发现当前patch拼接、Overview/Excerpt时间原点或全epoch权重公式的确定数值错误。新empty语义已与原B0区分。两个必须区分的边界是：现parser若将来用于模型raw可把重复键静默转空；CPU05从未构造训练labels，不能声称assistant label-mask/causal shift已验收。** 这不否定由已绑定target03生成器产生的可信人工JSON目标初验，也不要求重复已成功pixel/text/native/EOS检查。新GPU训练与模型raw权威parser不在本次已审范围，CPU05成功不能自行准入训练。

## 必须修正或补齐的具体问题

### 1. 重复JSON键可把非法输出静默转成空摘要

位置：[summary_contract.py:170](G:/ai/AIC视频/improvement/bottleneck_24h_v1/summary_contract.py:170)，特别是172行`json.loads(text)`。

无需运行即可按Python解析语义推导的反例：

```json
{"segments":[[0,1]],"segments":[]}
```

默认`json.loads`保留最后一个同名键；173行检查得到`{'segments': []}`，随后返回空结果，违背171行“非法输出不转合法空”的合同。应由新版本权威parser拒绝重复键。若新生成grammar本身已排除此文本，必须同时证明该grammar与最终raw parser同一范围，不能把格式受限推断为当前parser已拒绝重复。

**当前CPU05与未来raw的区别：** 当前传入`parse_answer`的是已绑定target03生成器以单一`json.dumps({'segments': intervals})`创建的人工目标，生成路径没有重复键，本次没有发现旧人工目标因该漏洞被转空；不重做其成功初验。缺陷针对把这个函数直接提升为未来模型raw权威parser。主代理已明确以独立`summary_output.py`新版本拒重复键/NaN并用Decimal保留生成小数；本次尚未审该新文件，不将计划修复称已验收。

同位置还会先将生成的JSON小数解析成binary float，再用179行`F(str(v))`重建。若合法生成`0.100000000000000001`，会先变成`0.1`；对于位于这两个值之间或等于`0.1`的native PTS，半开区间成员可能变化。当前继承目标是作者脚本已序列化的float文本，未发现其发生此问题；但生成raw并不自动继承该限制。原[contracts.py:49](G:/ai/AIC视频/reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/b_score_aligned_package_v4/contracts.py:49)已有拒重复键和`parse_float=Decimal`范例。需要新parser保持raw十进制精度，再做native映射，不能对预测端点默默舍入。

### 2. CPU05没有实际构造/复核训练label mask，159行声明超出证据

位置：[prepare_summary.py:133](G:/ai/AIC视频/improvement/bottleneck_24h_v1/prepare_summary.py:133)到138、[同文件:159](G:/ai/AIC视频/improvement/bottleneck_24h_v1/prepare_summary.py:159)；[training_suffix:156](G:/ai/AIC视频/improvement/bottleneck_24h_v1/summary_contract.py:156)。

代码实际完成：`expanded_text + answer + <|im_end|>`的token边界、suffix末尾EOS、512 token上限及answer解码往返，保存`prefix_ref`和`suffix_ids`。它没有产生训练`input_ids/attention_mask/labels`，也没有验证prompt/video位置为`-100`、assistant预测shift、`logits_to_keep`范围或EOS恰被监督一次。因而`first_independent_actual_pixel_text_native_label_mask_EOS_QA=True`不能作为mask QA完成依据。

这是训练准入的具体缺项，不要求重复成功pixel/text/native/EOS检查。新GPU代码应在首次前向前，对其实际训练张量独立检查：prefix原样、拼接suffix原样、prompt/vision/pad全mask、JSON/EOS受监督、causal next-token对齐及tail-logits索引。构造时不能先把完整answer喂入，再在同位置无shift预测该answer。若仅另存labels“形状正确”仍不能消除这个反例。

主代理已明确：保留冻结CPU05代码与原接受回执，在新训练admission中不采信该宽泛boolean，并于GPU前新增全部2236条首次实际masked teacher-forcing/causal shift QA。这是针对缺失训练合同的新检查，不是重跑旧已成功输入QA；本次未执行或核验其结果。

## 已核正确的关键实现与适用边界

| 核查项 | 结论与证据 |
|---|---|
| image→video temporal配对 | [build_pixels:53](G:/ai/AIC视频/improvement/bottleneck_24h_v1/summary_contract.py:53)将各静态image patch拆为`[patch,3,2,16,16]`，先核两temporal副本逐bit相同，再取每张第一副本，按时间维stack为真实相邻采样观察的temporal2；flat排列为channel→time→patch，与已有合同一致。两个role的blocks顺序与`video_grid_thw`顺序一致。 |
| 独立pixel检查 | [independent_pixels:75](G:/ai/AIC视频/improvement/bottleneck_24h_v1/summary_contract.py:75)使用flat channel片段复制，未重复builder的reshape/stack表达式，逐bit检查实际拼接张量。验证的是继承image patches的组合，不是新RGB resize/normalize；后者依赖原accepted chunks，代码没有重跑processor。 |
| 抽样与时钟 | [sample_even:30](G:/ai/AIC视频/improvement/bottleneck_24h_v1/summary_contract.py:30)取实际偶数观察、最多64、含两端且拒重号；Excerpt先按`start <= nativePTS < end`选已有2Hz观察，Overview覆盖全源观察清单。Overview origin=0，Excerpt origin=原window_start，时间group为两观测PTS均值减对应origin。既不是把稀疏帧重编号为连续2fps，也没有假造新帧。 |
| token/video顺序 | [build_text:113](G:/ai/AIC视频/improvement/bottleneck_24h_v1/summary_contract.py:113)以Overview/Excerpt两marker逐组展开，核video token总数与两grid一致；[independent_text:138](G:/ai/AIC视频/improvement/bottleneck_24h_v1/summary_contract.py:138)用已安装processor的text expansion路径消费各自时间序列两次并比较四个实际输入键。 |
| 目标语义与标签泄漏 | [question:94](G:/ai/AIC视频/improvement/bottleneck_24h_v1/summary_contract.py:94)明确整源摘要与empty未入摘要，不声称无高光；prompt只含实际时长/窗口、无评审标签或目标内容。`target_json/reviewer`仅进入监督表，不进入prefix。输入source ID/hash只为owner与绑定，不写入模型文字。 |
| 源/评审/窗权重 | [prepare_summary.py:135](G:/ai/AIC视频/improvement/bottleneck_24h_v1/prepare_summary.py:135)为`N/(25*W_s*R_sw)`。在完整N=2236条按`(1/N) sum(weight_i * sequence_loss_i)`汇总时，每源1/25、每窗1/W_s、每评审1/R_sw，公式正确。147–148行核各源总质量N/25。 |

当前独立pixels/time检查采用builder保存的plan再查原ordinal/PTS，未独立重算`sample_even`、Excerpt所属窗及origin。builder本身本次逐行未发现错误，但报告不把这一点包装为第二套独立采样算法验收。它也不证明稀疏观察看到了每条人工摘要动作；这是能力局限，不是将未观察动作补成普通的许可。

## 给正在实现的训练/推理入口的确定接口要求

- **保持实际权重意义。** 上述权重不是可在每4micro组内任意重新归一化的比例。若每组除`sum(weights_this_group)`，不同组权重会被冲掉；应按固定样本/注册的累计分母应用。序列CE是token均值还是token总和必须预先固定，不能让长摘要隐式获得更多评审权重。最后不足4条的累计归一化也须明确，不能丢弃或重复补齐。
- **训练与推理必须加载同一个新合同。** 双role顺序、source_end、窗口、sample_even、timestamps、MAX_SEGMENTS=6、MAX_ANSWER_TOKENS=512、MAX_SEQUENCE_TOKENS=12288及相同prefix不能训练一套推理另一套。旧原B0最多5段/256token parser不能直接用于这条新模型，旧EMPTY_PROMPT也不能替换新summary prompt。
- **不要把CPU模块导入GPU。** `prepare_summary.py:7`会将当前进程CUDA清空。GPU可以只导入无CUDA masking的`summary_contract.py`，自行使用其纯函数；不要为复用`source_pixels`直接import整个prepare模块。
- **继承目标，不重统计。** CPU05绑定target03文件与原source registration；本次未重跑144窗/2236targets或往返验证。现代码按UID取目标，未再次核每行sid、start/end、clock_ref与窗口逐项相等；这一一致性继承已绑定target03生成器，而非独立CPU05目标重算。若后续target输入不是同一已绑定文件，必须阻断而非只保持总2236即可。
- 新GPU代码的初始化、实际LoRA trainability、加权CE、checkpoint/RNG接续和同输入frozen-TIME对照尚不在本次审查范围。不能由本报告或CPU05的`training_or_GPU_admitted=False`产物推断它们已通过。原40.47/旧TIME权重应保持不可变。

未执行任何测试/目标统计/QA或远端操作；唯一写入本报告。
