"""Write a new Linux handoff and Sources payload without editing the frozen release."""
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ready=json.loads((HERE/'linux_readiness_completion.json').read_text())
upload=json.loads((HERE/'upload_verification.json').read_text())
assert ready['status']=='PASS_LINUX_UPLOAD_SELECTED_HASHES_AND_ALL_REAL_IMAGE_CPU_PREFLIGHTS'
assert ready['zip_sha256']==upload['zip_sha256']
assert not ready['weights_loaded'] and not ready['optimizer_started']
report='''# Linux开训交接：上传与CPU数据预检已通过

本交接对应2026-10-09已批准的Windows经Mac mini跳板上传。训练机数据目录：
`/home/inspur/aic_video_work/datasets/qwen8b_annotation_20261009_v2`

上传包1,269,695,818字节，SHA256为`45af6f8edc267be4a126cd1f86fb99172f11632202da947d9cb3eca2246ff57c`。全部6,353个ZIP条目的CRC读取通过；安全解压后6,352个选定文件的字节和SHA均通过独立核验。没有修改原始标签、原发布包、旧实验或现有生产权重。

|任务|训练样本|验证样本|Linux实际图片CPU预检|
|---|---:|---:|---|
|裁剪框|181|148|全部通过，最大319 tokens|
|时间重要性序列|314|89|全部通过，最大1618 tokens|

预检使用既有`qwen3vl_isolated_20260910`环境和指定Qwen3-VL-8B模型目录中的processor/config，不加载模型权重。图片数量、输入长度、助手监督掩码与非空目标检查全部通过。对应回执：`linux_readiness_completion.json`、`upload_verification.json`、`linux_receipt_copy.json`。

时间数据来自48源、6047个采样帧的TVSum人工重要性分数，固定2秒网格。源帧数/原生PTS与人工标注对齐；20人评分求和目标除以20恢复原均分。网格边缘是采样边缘，不是精确动作语义起止。Gemini600条候选的语义边界尚未全部验收，均未进入训练目标。裁剪仍是经过复核的模型弱标签，不能把验证一致性称为人工金标准质量。

上传早期前缀的缓冲尾段导致首次合并保护检查拒绝，未覆盖数据。随后保留完整旧前缀，仅按已验证长度读取前缀并重新核验所有分片，合并整包SHA与原包完全一致；未重传整包。原尝试和修复记录见`transfer_completion.json`。

此次授权仅上传和校验，没有启动训练、安装环境、GPU推理或优化器。数据传输和实际读入准备已完成；8B权重加载、首步loss/梯度与显存峰值仍需在下一阶段实测，训练效果未知。

后续获得训练授权后，先实时核对共享任务与资源，以独立新output运行原发布脚本并显式添加`--train`。不要复用已完成CPU预检目录。裁剪和时间adapter分别保存，不覆盖现有生产adapter。具体配置、评估入口和CPU/训练调用约束见原包`README.md`。
'''
with (HERE/'README_LINUX_READY.md').open('x',encoding='utf-8') as f:f.write(report)
payload={'schemaVersion':1,'items':[
 {'id':'linux-package-verified','title':'Linux数据包验收','queries':[
  {'id':'upload-integrity','source':{'label':'上传与安全解压回执',
   'files':[{'label':'transfer_completion.json'},{'label':'upload_verification.json'}],
   'evidenceFlow':[{'kind':'validation','title':'字节与完整性核验',
                   'text':'远端包大小与本地相同，完整SHA一致；所有ZIP条目读至EOF并校验CRC，解压后选定文件大小和SHA全部一致。'}]},
   'rows':[{'zip_bytes':upload['zip_bytes'],'archive_files':upload['archive_files'],
            'selected_files_verified':upload['extracted_selected']['files'],'sha256':upload['zip_sha256']}],
   'columns':[{'field':'zip_bytes','label':'包大小（字节）'},{'field':'archive_files','label':'ZIP文件数'},
              {'field':'selected_files_verified','label':'选定文件校验数'},{'field':'sha256','label':'整包SHA256'}]}]},
 {'id':'linux-data-preflight','title':'训练机实际图片读入准备','queries':[
  {'id':'real-image-cpu-checks','source':{'label':'Linux CPU预检与数据审核',
   'files':[{'label':'linux_readiness_completion.json'},{'label':'selected_data_audit.json'}],
   'filters':['裁剪与时间任务分别预检','保持按视频源划分训练与验证集'],
   'caveats':['时间目标是TVSum人工帧重要性，不能证明精确动作起止边界；Gemini600条事件区间均未进入训练目标。',
              '裁剪标签是经过复核的模型弱标签。',
              '此次未加载8B权重、未计算模型loss或启动优化器；训练效果未知。'],
   'evidenceFlow':[{'kind':'validation','title':'实际图片和监督掩码',
                   'text':'训练机现有环境实际处理了全部329条裁剪样本和403条时间序列，输入长度与非空助手监督目标检查通过。'}]},
   'rows':[{'task':'裁剪框','train_rows':181,'validation_rows':148,'max_input_tokens':319},
           {'task':'时间重要性','train_rows':314,'validation_rows':89,'max_input_tokens':1618}],
   'columns':[{'field':'task','label':'任务'},{'field':'train_rows','label':'训练样本'},
              {'field':'validation_rows','label':'验证样本'},{'field':'max_input_tokens','label':'最大输入tokens'}]}]}
]}
with (HERE/'linux_readiness_sources.json').open('x',encoding='utf-8') as f:json.dump(payload,f,ensure_ascii=False,indent=2)
print('Saved Linux handoff and reviewed Sources payload')
