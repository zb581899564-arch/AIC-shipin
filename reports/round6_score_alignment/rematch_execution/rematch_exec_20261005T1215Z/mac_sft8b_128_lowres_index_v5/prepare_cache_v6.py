from pathlib import Path
import json,shutil,hashlib,datetime as dt,ast
SRC=Path(__file__).resolve().parent;DST=SRC.parent/'mac_sft8b_128_lowres_index_cache_v6'
DST.mkdir(exist_ok=False);(DST/'controller').mkdir()
old=json.loads((SRC/'source_lock.json').read_text())
for name in old['files']:
    target=DST/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(SRC/name,target)
config=json.loads((DST/'config.json').read_text());config['mps_cache_policy']='SYNCHRONIZE_AND_EMPTY_CACHE_AFTER_EACH_MICROBATCH'
config['seed_restored_after_equivalence_tests']=True
config['scientific_change']+='; release variable-length MPS allocator cache after each backward; restore registered RNG after equivalence tests'
(DST/'config.json').write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
path=DST/'train_mac.py';text=path.read_text()
text=text.replace("cpu_bf16_and_fp16=True,mps_bf16=True,forward_and_gradient_bitwise_equal=True)",
 "cpu_bf16_and_fp16=True,mps_bf16=True,forward_and_gradient_bitwise_equal=True)\n        random.seed(config['seed']); np.random.seed(config['seed']); torch.manual_seed(config['seed'])\n        torch.mps.manual_seed(config['seed'])\n        report['initialization_seed_restored_after_tests']=config['seed']")
text=text.replace("del result,encoded", "del result,encoded\n                    torch.mps.synchronize();torch.mps.empty_cache()\n                    sample_memory(report,torch,'after_microbatch_cache_release')\n                    report['cache_release_count']=report.get('cache_release_count',0)+1\n                    write(output/'progress.json',report)")
assert text.count("after_microbatch_cache_release")==1 and text.count('initialization_seed_restored_after_tests')==1
path.write_text(text)
path=DST/'PROTOCOL.md';path.write_text(path.read_text()+'''

## 缓存与随机种子修正 v6

v5已完成真实反向与首个optimizer更新：288张量梯度连通/有限，首步144个LoRA张量变化，mean_loss3.4471/gradient_norm5.2133。不同长度窗口使MPS缓存保留量持续增长，采样driver峰值达到55920.31MiB，高于当时recommended53084.67MiB；不能据首次forward的低峰值批准全量。主控仅终止本次注册的v5训练子进程组，账本和更新证据保留。另发现一致性测试torch.manual_seed(33)影响后续LoRA初始化，v5不能作为登记seed20261006的训练结果。

v6每次完成backward、持久化证据并删除临时result/encoded后，synchronize并empty_cache，保留训练模型、梯度和优化器状态；每次记录释放后allocated/driver以及释放计数，峰值仍记录释放前样本，不通过只改报告低估峰值。仍用原128帧/显式像素预算/局部FP32索引修复。每个probe/full初始化前，在一致性测试后重新设置random/numpy/torch/MPS为20261006，记录该值。保持完整3updates/48microbatches验收及live recommended memory门；不在同一运行里继续调参数。完整训练从冷基座新LoRA开始，探针不作质量比较。
''')
names=list(old['files'])
for name in names:
    if name.endswith('.py'):ast.parse((DST/name).read_text(),filename=name)
lock=dict(schema='aic_mac_8b128_lowres_index_cache_source_lock_v6',scope=old['scope'],created_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
 files={name:hashlib.sha256((DST/name).read_bytes()).hexdigest() for name in names})
(DST/'source_lock.json').write_text(json.dumps(lock,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
digest=hashlib.sha256((DST/'source_lock.json').read_bytes()).hexdigest();print(digest)
copy=(SRC/'copy_verified_parent.py').read_text().replace('mac_sft8b_128_lowres_index_20261006T0728Z','mac_sft8b_128_lowres_index_cache_20261006T0734Z')
(DST/'copy_verified_parent.py').write_text(copy)
for name in ['CONTINUE_MAC.md','update_repair_status.py','copy_linux_verified_parent.py','verify_archive.py']:
    text=(SRC/name).read_text().replace('mac_sft8b_128_lowres_index_v5','mac_sft8b_128_lowres_index_cache_v6').replace('mac_sft8b_128_lowres_index_20261006T0728Z','mac_sft8b_128_lowres_index_cache_20261006T0734Z').replace('25f7b9df1a0a452c9187043bbc7d9fe2bf4658d232afcfb9f1d7dd4c8cb30fc5',digest).replace('INDEX_V5','INDEX_CACHE_V6').replace('v5','v6')
    if name=='CONTINUE_MAC.md':text+='\n额外修复：每microbatch同步释放MPS空闲缓存，测试后恢复登记种子20261006；v5首步工程证据及主动停止记录保留。\n'
    (DST/name).write_text(text,encoding='utf-8')
