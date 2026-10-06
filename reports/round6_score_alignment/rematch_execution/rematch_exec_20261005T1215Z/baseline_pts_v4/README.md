# 原生时钟 v4：仅 metadata 重审

生产代码仅stdlib；不导入numpy/decord/torch，不调用ffprobe、解码器或模型，不读取像素/语义标签。输入是绑定SHA256的既有v3完整426 receipt、原M0 manifest、每源numeric，以及非CFR源的独立raw ffprobe endpoint addendum。原数据、源码、报告、manifest均只读。输出不授予旧A或新A推理准入。

v3完整分母426、414pass/12fail。80/161 的timebase一tick就是一帧，把一整tick当浮点误差会导致错误的半帧不可分辨判定。v4改为原native时钟的正确float32表示比较、逐帧唯一性及真实表示误差半帧门；旧CFR `1/fps+1e-6`门不放宽。另10源真实不具CFR资格，只能在新增原native整数/packet duration与逐Decord end共同证明后用native分支。

v3没有保存原整数数组与packet duration：整数仅在冻结parser下作唯一重建并明确标注，nonCFR还需新raw整数交叉验证。尾端以实际最后frame的正packet duration和同帧Decord end为依据；container header duration不同另记诊断，不伪报一致。任何身份、尾证据或哈希失败保留完整分母并STOP，不生成新clean manifest。

本地已执行 `python test_native_clock_cpu.py`，**11/11 PASS**；覆盖coarse80/161、原10个非CFR无尾证据STOP、半帧错配、float32 alias、细tick诊断、源/整数/endpoint篡改、非零origin、header discrepancy、426完整分母、8源短scope保留与源码锁拒绝。`python -m py_compile native_clock_core.py registry_io.py scan_native_clock.py build_nontest_registry.py test_native_clock_cpu.py`通过。测试读取12个已绑定numeric，未执行完整426重审、媒体解码、GPU或推理。

4个production文件绑定于`source_lock.json`，两个CLI运行前核验。以新output-root运行，任何既有目录均拒绝覆盖。stdout仅打印小receipt及路径/hash，不输出逐帧数组。

完整426重审，由主控部署并运行：

```bash
$PY "$RUN/baseline_pts_v4/scan_native_clock.py" \
  --manifest "$RUN/baseline_a/m0_finalize_01/clean_manifest_426.json" \
  --v3-receipt "$RUN/controller/pts_origin_v3_01_receipt.json" \
  --endpoint-addendum "$RUN/baseline_pts_v4/endpoint_addendum_01/addendum_receipt.json" \
  --expected-addendum-sha256 "$BOUND_ADDENDUM_SHA256" \
  --output-root "$RUN/baseline_pts_v4/reaudit_01"
```

固定原manifest SHA为`57a6985ad8248ae9ee64d24adc1f84eea1ac9f1b19f90da3c6647d8befa15d32`，v3 receipt为`efcb86a8435523e53c17e86eedc9506e134b9571a84acdd0ebf5e8af8d17bff5`。默认读取各receipt登记的原numeric路径；`--numeric-root`仅用于SHA一致的metadata镜像，缺任意源仍留在426失败分母。`--addendum-json-root`同样只用于raw JSON镜像，不修改绑定内容。

历史非测试8源使用独立collector，仅CFR分支且保持原短scope：

```bash
$PY "$RUN/baseline_pts_v4/build_nontest_registry.py" \
  --manifest "$RUN/baseline_a/inputs/non_test_frozen8.json" \
  --collector-receipt "$RUN/controller/nontest_clock_numeric_01/nontest_numeric_receipt.json" \
  --output-root "$RUN/baseline_pts_v4/nontest_registry_01"
```

固定8源manifest SHA为`7b3e187451eb15f80647b4441a4a41f030f4be1438a95ef5b7982a53554f153a`，collector SHA为`612da27ff7a1c360557d80ce5f0aa3ae9c00d1346fb88c04d3ca02964da3f2cc`，原worker SHA为`0ab8632ded07c7b3c13c362845d7e46d68f67d721ccd2bd74eff58bb0bd81638`。8源结果与426结果独立。

输出为`clock_arrays/*.clock.json`、`clock_registry.json`、`reaudit_receipt.json`，完整通过才有`clean_manifest_v2.json`。字段与分支约定见[SCHEMA.md](SCHEMA.md)。成功只表示时钟/身份metadata工程证据，不表示推理成功、模型质量或官方成绩。
