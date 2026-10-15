编码缓存已改为 `encoded_tensors.pt.gz`，原CPU encoding仍一次。`gzip.GzipFile` level1包裹原 `torch.save`；GPU和独立CPU重放均使用gzip+`torch.load(weights_only=True,map_location='cpu')`，并消费gzip末尾核CRC。未修改dtype、像素、归一化、原tensor signature或frames NPZ。

本次实际Linux小型合成检查通过：6个tensor包含int64、fp32非连续stride、fp16、bf16，`torch.equal`、dtype、stride和连续原字节signature全部一致；原逻辑payload12712B，gzip文件12091B，压缩/读回0.006987秒，进程peak RSS374652KiB。该压缩率/RSS只描述小合成检查，不能推算真实native64输入。processor0、模型0、媒体0、真实input0、CUDA未初始化；原成功准备未重跑。

原7个脚本已在LinuxAST语法检查通过；随后新增真实CPU统计与VERIFY有限grammar的两个文件另做更新语法检查，未重复成功gzip检查。证据为 `gzip_synthetic_check_01.json`、`syntax_update_02.json`。Linux合成原回执保留于 `BASE/gzip_synthetic_check_01/receipt.json`。

首个真实CPU input proof会报告实际compressed tensor字节、RGB NPZ字节、逻辑tensor payload、processor/压缩/请求耗时和进程peak RSS。主代理必须根据实测冻结生产输入数量与容量预算，不能用部分prepare提前启动GPU。

plan现在支持明确 `validation_scope=ONE_EVENT_INTERFACE_SMOKE` 的1event/2requests最小接口检查；10–20events开发诊断使用独立 `EXTERNAL_DEVELOPMENT_DIAGNOSTIC` scope。两个scope完整分母均须先冻结。README有实际Linux CLI示例；plan只读旧JSON/完整clock，不重decode、不读媒体或processor。

VERIFY代码草案已增加KEEP/UNKNOWN/DROP prompt/parser/resolver及 `VerificationConstraint`。只在清晰普通/冗余/无支持时DROP；未知景观、讲话无音频、不完整活动或稀疏覆盖不足保留，不要求完整动作。它尚未进入plan/CPU/GPU driver或任何准入。DROP仅给候选状态，未删除帧；integrator须对其他KEEP候选求并集后再处理覆盖。

最终7py加README共90831B，逐文件SHA与bytes见 `code_manifest_02.json`。真实请求代码仍未部署运行；没有真实CPU/GPU、训练、模型调用、媒体下载、独立新模型重放或新封包结果。
