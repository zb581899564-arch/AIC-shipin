# 三条 worst-ID 派生规则与本次确认绑定

这是原 relative `redundant` 的 CPU 派生规则。原模型 parsed/raw/first QA 与普通臂失败均保留，不追加模型调用。只登记以下三条离散规则，不扫描其他比例或阈值：

- `ALL_WINDOW_WORST`：每个多候选窗采用实际 `redundant` 所指的最弱 ID；开发指标直接采用已经完成的原 redundant 比较，不重跑该成功比较。
- `BUDGET_TWO_THIRDS`：仅候选数 `n>=3` 时采用同一实际最弱 ID，因此每窗至少保留 2/3 候选。
- `PAIR_ONLY`：仅 `n==2` 时采用同一实际最弱 ID；其余视窗不删。

`n<2` 必须实际返回空最弱列表。任何实际 response 含多个 worst ID 直接失败，不推测哪一个最弱。三个风险字段与原 ordinary 结果不参与本次参考指标筛选。

主链在比较前新建并冻结 `policy_protocol_07.json`，字段为：

```python
{
  "policies": ["ALL_WINDOW_WORST", "BUDGET_TWO_THIRDS", "PAIR_ONLY"],
  "selection_order": ["ALL_WINDOW_WORST", "BUDGET_TWO_THIRDS", "PAIR_ONLY"],
  "max_selected_policies": 2,
  "source_manifest_ref": ORIGINAL_RELATIVE_RESULT["bindings"]["manifest_ref"],
  "source_completion_ref": ORIGINAL_RELATIVE_RESULT["bindings"]["decisions_ref"],
  "prior_all_window_result_ref": ref(MAIN/"relative_dev_comparison_04.json"),
  "source_protocol_ref": ref(MAIN/"relative_protocol_03.json"),
  "deletion_quality_gates": ORIGINAL_FIXED_DELETION_GATES
}
```

`selection_order` 可由主链预先固定为三名的任一排列，比较后不得改。脚本按该顺序从通过者中选最多两个，直接比较完整原生帧集合排除相同预测。三名的 `passed_arms` 始终保留全部真实 bool；实际最多两条准入记录在独立的 `selected_policies`，不会为了两条而改写第三条的 PASS。

```text
python -B reference_code/policy_evaluate.py --protocol MAIN/policy_protocol_07.json --output MAIN/policy_comparison_08.json
```

结果包括 `passed_policies` 和完全相同的 `passed_arms`、每策略宏指标/逐源/固定门、原生帧集合与签名，以及真正不同的 `selected_policies`。不足两个通过且不同的策略时 status 为 `INSUFFICIENT_TWO_DISTINCT_PASSING_POLICIES`、exit 5。原全部来源及全部评审保留，召回列出但不要求绝对不降。

有通过策略时 selection 输出名精确为 `policy_comparison_08_selection.json`，兼容 schema `MIDNIGHT_DELETE_DEV_SELECTION_V1`。它的 `passed_arms` 与对应 result 的 map 相同，并新增 `selected_policies`。`confirm_mapping.select`（外层和新 CPU code 副本）、`confirm_media.registration`、`confirm_runtime/fresh_registration.py` 均消费这两个文件中相同的 `passed_arms` 字段；不会在下载前因新旧字段名差异报 KeyError。

**本次真正采用 policy 后，CONFIRM_README 中原 relative development refs 必须改用以下新绑定：**

```text
protocol_ref                 MAIN/policy_protocol_07.json
development/dev_result_ref   MAIN/policy_comparison_08.json
development/dev_selection_ref MAIN/policy_comparison_08_selection.json
```

`relative_protocol_03.json` 仍以 policy protocol 的 `source_protocol_ref` 保留，原 relative prompt/实际模型字段不变；新 protocol 只冻结 CPU 应用规则及选择。新 confirmation source/media/input 根仍为 `MAIN/relative_confirm`，使用 CONFIRM_README 的相同小 metadata、media 注册与 12 文件 CPU 接口。`map_confirm_completed.py` 会把 `selected_policies` 而非所有 passing policies 写入实际 fresh admission 的 `admitted_arms`。

完整新 4 源、原 B0/VERIFY/首次 QA 与新实际 relative classifier 输出全部成功后，确认入口改用本脚本，不能用仅识别 ordinary/redundant 的旧 `evaluate.py`：

```text
python -B reference_code/policy_evaluate.py --protocol MAIN/policy_protocol_07.json --manifest MAIN/relative_confirm/rank_mapping_01/first_fresh_evaluation_manifest.json --decisions NEW_CLASSIFIER_STAGE/completion.json --development-selection MAIN/policy_comparison_08_selection.json --output MAIN/relative_confirm/policy_fresh_comparison.json
```

首次确认只计算已冻结且开发通过的 `selected_policies`；不观察其他派生策略的确认指标，也不据新源结果重新选策略。任何旧 STOP、旧门与旧原始回答都不改写。参考仍是人类摘要区间代理，人工未选不是 ORDINARY gold，官方效果保持 UNKNOWN。
