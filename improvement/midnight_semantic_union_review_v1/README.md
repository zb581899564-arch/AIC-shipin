# SEMANTIC_UNION 工程预览（尚未执行）

`preview_union.py` 仅供 Linux CPU 工程预览，不授权发布，不计第五份交付。源是本轮已经交付的 ACTION、REACTION、INFORMATION 三包；按 `(video_id, frame/source_frame)` 做无权重并集，重叠 prediction/selected/provenance 完整行必须逐值相同。保留 40.46 原 122002 帧及原框，保留 426 非空源、原 native 帧号/PTS 语义和实际 8782459120 参数。

部署位置固定为 `ROOT/semantic_union_review_code_v1/preview_union.py`，其中 ROOT 为 `/home/inspur/aic_video_work/midnight_five_verify40_46_20261015_v1`。独立输入为 `ROOT/semantic_union_review_inputs_27.json`：

- `code_files`：恰三项 path→sha256，新 preview 文件及原 `package_code_v2/production_evidence.py`、`package_math.py`，后两项必须仍等于原冻结输入中的 SHA。
- `source_package_completion_refs`：三元素 `{path, sha256}` 列表，由真实 completion 的 `arm` 识别三风险源包。
- `current_four_package_refs`：四元素同格式列表，必须涵盖已交付 ORDINARY 及三风险包。
- `original_package_inputs_ref`、`protected_baseline_zip_ref`、`history_ref`：各为实际 `{path, sha256}`；history 保留 25 条真实记录与 23 个 canonical，不删除原有重复，且包含当前四包。
- `publication_authorized`：省略或明确 `false`；本入口拒绝 `true`。

各源组件路径从原 completion 目录导出，并以原 ZIP/member SHA、CRC、原 11strict report 与 provenance SHA 验真。三包 metadata 字节及各源 header 必须相同。原 518 次实际调用、1 个 identical-input alias 和首次 QA proof 链仅做只读 JSON/SHA 绑定；不重复模型、输入处理、媒体解码、首次 QA 或源包格式验证。人工参考指标、测试媒体、PAIR/guard 失败方向均不读取。

只创建此前不存在的 `ROOT/semantic_union_review_27`，既存目录或失败草稿均拒绝覆盖和自动重试。仅新组合执行一次既有 independent11strict，要求其相对基线、25 历史记录和当前四包实际预测均不同，再输出该目录的 `candidate_MIDNIGHT_SEMANTIC_UNION_RISK.zip` 与 `review_receipt.json`。不写 `ROOT/packages`、不回传 Windows、不自动提交。

回执包含新增帧数、426 源/总帧数、ZIP 大小/SHA/member SHA/canonical、相对四包的增删帧数及实际 proof refs；固定 `publication_authorized=false`、`maximum_previous_risk_count=3`、`proposed_risk_count=4`、`original4unchanged=true`、`no_new_modelcalls=true`、`quality_pass_claimed=false`、`counted_as_fifth_delivery=false`。工程预览通过不代表人工质量通过或官方提分，原四交付和旧科学失败结论保持。

本地仅做 AST/空白轻量静态检查；未部署或运行本入口，未运行新组合 11strict，未生成任何预览 ZIP。主代理审阅后负责小量部署、真实输入绑定和唯一 CPU 执行。
