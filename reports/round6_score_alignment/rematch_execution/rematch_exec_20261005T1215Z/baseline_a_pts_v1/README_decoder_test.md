# 独立真实 CPU 合成解码验收

`test_decoder_synthetic.py` 由独立验收 worker 编写，只调用已冻结的生产 `VerifiedNativeReader/build_native_clip/native_clip_plan/descriptors/validate_frame_request`。不改生产文件或source锁，不调用模型/GPU，不读比赛媒体或语义标签。

主控在最终生产锁部署后运行：

```bash
$PY -B "$RUN/baseline_a_pts_v1/test_decoder_synthetic.py" \
  --ffmpeg /home/inspur/anaconda3/envs/Andy/bin/ffmpeg \
  --ffprobe /home/inspur/anaconda3/envs/Andy/bin/ffprobe \
  --output-root "$RUN/baseline_a_pts_v1/real_decoder_01"
```

必须使用不存在的绝对output-root，Linux限`/home/inspur/aic_video_work`内。raw RGB、FFmpeg argv/log、lossless MP4、原始ffprobe JSON、native整数/packet duration、Decord numeric、marker与RGB/BGR哈希、descriptor/重开/采样/失败证据及cache/tmp均限定该新目录。保留失败，不覆盖或自动回退codec/颜色容差。

两个80帧96×64 fixture：CFR零原点，以及有gap且非零原点的VFR。每帧包含ordinal颜色stripe和不同RGB ramp，编码使用既有`libx264rgb -crf 0`。编码是否实际无损必须由全部帧RGB/BGR逐像素比较证明，不能依据codec名字宣称。fixture clock只在实际ffprobe原整数PTS、正packet duration、stream start、数目/几何与**所有**Decord start/end精确float32表示、邻帧唯一性及半帧表示误差核验后构造，禁止从猜测fps制造时钟。

验收包括顺序全部80帧、同帧重复读取、最后帧；与冻结vendor shot descriptor和shot BGR SHA一致；独立spatial重开像素SHA相同；native max64时序采样的源ordinal与marker一致；最后单physical frame的显式双输入padding仍是同一帧。错误index、倒退ordinal、source SHA、native start/last packet end篡改必须STOP。

成功：`PASS_REAL_CPU_SYNTHETIC_NATIVE_DECODER_IDENTITY`、退出0；失败：`FAIL_REAL_CPU_SYNTHETIC_NATIVE_DECODER_IDENTITY`、退出1。`decoder_test_receipt.json` 保留生产锁、测试源码、FFmpeg/FFprobe及实际生成source SHA，stdout只打印小摘要。

本机已核语法、80个唯一marker和最终revision03生产锁；**实际Linux FFmpeg/Decord尚待主控运行**。此测试直接验native解码API（包括实际CFR fixture），没有伪造生产registry或推理准入；完整shot CLI的426/8源manifest准入与空间模型入口不在本验收范围。
