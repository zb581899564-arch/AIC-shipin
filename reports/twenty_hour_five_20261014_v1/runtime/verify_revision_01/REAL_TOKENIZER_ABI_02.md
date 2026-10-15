一次真实 Qwen tokenizer-only VERIFY retarget ABI 已通过，不是候选质量/科学输入/CPU 或 GPU 准入。

读取且只读取旧成功 `CH_7FQ5Q_W000` 的 input/proof/full gzip tensor cache，核 cache SHA 和原 tensor signature。未读源视频、RGB NPZ、参考 action 或 coarse 回答。候选 ID 为 `ABI_ONLY_SYNTHETIC_CANDIDATE`，区间取原窗内 1/3..2/3，仅供接口检查，不能登记为真实模型候选。

实际 Qwen2TokenizerFast / Qwen3VLProcessor：旧 12075 tokens 全文 roundtrip 完全一致，EMPTY_PROMPT 出现且替换唯一；新 12194 tokens，原完整 vision token prefix/时间文字不变；grid `[32,28,52]`、原 float32 pixel 与 int64 grid/token/mask 保持，独立 partition+encode 的 token/combined tensor signature 完全一致。原缓存没有复制或改写，新 token cache 也未另保存。实测接口检查 20.062773682177067 秒，进程峰值 RSS 1270192 KiB；解码、vision processor encode、模型调用、optimizer、CUDA 初始化均为 0。

Linux 完整回执位于 `/home/inspur/aic_video_work/twenty_hour_five_20261014_v1/candidate_verify_v1/tokenizer_abi_check_01/receipt.json`，9821 B，SHA `bdbf6b54988da9fbcbeb64d4ea79381f9744f4dafd45dc4ec6e3425e8a84c7c8`。ABI raw 161427 B 留在同目录 Linux，未回传。Windows `real_tokenizer_abi_01.json` 是 stdout 的结构化回执副本，文件序列化不同，不能拿 Linux 文件 SHA 当 Windows 副本 SHA。

原 8py/README 与 `code_manifest_01.json` 绑定全部一致，无 ABI 修补，无新 02 业务代码；pure01 和原 manifest 历史不改。外部真实 coarse 仍未提供，端点/VERIFY 效果和 grammar 在真实生成中的行为尚未验收。原 production 缺缓存时 MissingOriginalCacheError 仍阻断，不增 fallback，不把本次接口通过叫 production processor/decode 0。
