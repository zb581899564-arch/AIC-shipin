# Agent C 评估器与训练门只读审查

审查日期：2026-09-09  
范围：`tmp_agent_c/evaluation/`、`tmp_agent_c/training/`。未修改 C 文件，未加载 GPU 框架。

## 已复核且自洽的部分

- `python3 -m evaluation.tests.run_boundary_tests --report <临时文件>` 通过 9/9。
- 诊断 metric 的公式实现与代码声明一致：逐视频 `F=2*S/(Npred+Ngt)`，视频等权平均再乘 100；同视频同帧才匹配。双空为 1、单空为 0。见 `evaluation/internal_metric.py:142-147`、`:181-242`。
- 合法重复帧在 validator 中给 warning、保留；metric 只让第一次对该帧贡献 IoU，重复行仍进入 `Npred`。合成重复样例端到端返回 66.6666666667，`n_pred=2`。
- 非法帧越界、NaN、越界框和未知 `video_id` 都使 validator 产生 error；CLI 不计算 metric 并以退出码 2 结束。合成越界样例验证了 `metric=null`。
- 当前 A 的 gate 文件在 C gate 中得到 `candidate_splits_ignored=true`、`ok=false`；缺 `accepted_splits`、`passed=false`、`alignment_verified=false` 均被拒绝。candidate 行带 `candidate_only` 或 `do_not_use_as_training` 时也会被拒绝；缺媒体文件和相同字符串的来源组交叠均会被拒绝。

## 可复现问题

### 1. 来源组只做字面相交，后缀别名可绕过跨 split 泄漏检查

`training/gate.py:238-249` 直接对每个 JSONL 行的 `source_group` 字符串做 set intersection，没有使用 A 的“去掉末尾 `_start_end`”规范化。合成 gate 满足 `training_authorized=true`、`passed=true`、`alignment_verified=true`、200/50/50 计数，训练组使用 `train-g-0`、dev 组使用 `train-g-0_60.0_210.0`，所有媒体文件存在且无 candidate 标志；C 返回 `ok=true`、`cross_split.zero_overlap=true`。

这是条件性中等风险：当前 A 生成的候选文件已经使用规范化来源组，当前 gate 仍是 FAIL；但任何 accepted split 若混入 raw `source_vid` 与 canonical group 两种写法，C 不会发现同源泄漏。接受前应复用同一规范化函数，或要求带可验证的 canonical source-group/manifest。

### 2. accepted split 的可信身份和媒体类型没有逐行重验

`training/gate.py:217-223` 把 `counts[*].trusted_identity` 当作 gate 文件中的声明；`training/gate.py:139-145` 只检查支持的路径字段能解析到 `os.path.isfile`，没有检查每行 `trusted_identity`、来源哈希、JSON 标签 schema、允许的训练媒体根或 MP4 类型。合成 1 字节文本文件命名为 `media.mp4`，生成无 trusted/hash 字段的 200/50/50 行，C 返回 `ok=true`。

这依赖“accepted split 与 gate 文件均由可信 A 产出”的上游信任假设；在该假设成立时不是当前 gate 的绕过。但若 gate 文件或 accepted split 可被误写/替换，任意已有文件和伪造计数即可进入下一阶段。当前 candidate 行因标志和缺少 accepted_splits 被挡住，缺媒体也被挡住。

### 3. 诊断 GT parser 会静默截断非整数帧号

`evaluation/internal_metric.py:103-106` 对列表形式的 GT 使用 `int(value["frame"])`；因此 `1.9` 和 `True` 都被接受并变为帧 1。预测 validator 在 `evaluation/schema.py:316-320` 严格要求整数并拒绝 bool。合成 parser 样例实际得到 `frames=[1]`。

这只影响合成/开发 GT，当前没有官方封存 GT，且该包明确标记为 `internal_diagnostic`；它不会改变当前测试提交路径，但可能让错误的本地诊断标签得到错误分数。建议 GT parser 采用与预测相同的整数且非 bool 检查。

## 结论

metric 的已声明重复/非法预测策略在现有边界测试下内部一致，且明确没有冒充官方 evaluator。当前训练门能挡住 A 的 candidate 文件、缺媒体和字面相同的跨 split 来源组交叠；已发现的实际结构性缺口是来源组别名未规范化，以及 accepted 行的可信身份/媒体根没有逐行重验。未执行训练、未写 C 文件、未读取或上传视频内容。

复核命令与证据：

```powershell
python3 -m evaluation.tests.run_boundary_tests --report <临时 JSON 路径>
python3 -m py_compile evaluation\schema.py evaluation\internal_metric.py training\gate.py training\train_lora.py
```
