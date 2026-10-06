from pathlib import Path
import json,shutil,hashlib,datetime as dt,ast
SRC=Path(__file__).resolve().parent;DST=SRC.parent/'mac_sft8b_128_lowres_fp16_v4'
DST.mkdir(exist_ok=False);(DST/'controller').mkdir()
old=json.loads((SRC/'source_lock.json').read_text())
for name in old['files']:
    target=DST/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(SRC/name,target)
config=json.loads((DST/'config.json').read_text());config['precision']='fp16'
config['scientific_change']+='; frozen base/activation FP16 instead of BF16 for actual MPS backward compatibility; LoRA FP32 gradients'
config['parent_failed_run']='/Users/choubk/codex-workspace/projects/aic-video/mac_sft8b_128_lowres_20261006T0720Z'
(DST/'config.json').write_text(json.dumps(config,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
path=DST/'train_mac.py';text=path.read_text().replace('torch_dtype=torch.bfloat16','torch_dtype=torch.float16')
assert text.count('torch_dtype=torch.float16')==1
text=text.replace("validate_trainable_names([name for name,_ in trainable])", "validate_trainable_names([name for name,_ in trainable])\n        require(config['precision']=='fp16' and all(p.dtype==torch.float32 for _,p in trainable),\n                'registered FP16 base / FP32 trainable LoRA recipe changed')\n        report['precision_evidence']=dict(base_dtype='torch.float16',trainable_lora_dtype='torch.float32',\n            loss_dtype='float32',implicit_cpu_fallback=False)")
path.write_text(text)
path=DST/'mac_contract.py';text=path.read_text().replace("config['max_frames']==128 and", "config['precision']=='fp16' and config['max_frames']==128 and");path.write_text(text)
path=DST/'finish_mac.py';text=path.read_text().replace("environment['PYTORCH_ENABLE_MPS_FALLBACK']='0'", "environment['PYTORCH_ENABLE_MPS_FALLBACK']='0';environment['TORCH_SHOW_CPP_STACKTRACES']='1'");path.write_text(text)
path=DST/'PROTOCOL.md';path.write_text(path.read_text()+'''

## MPS精度兼容修正 v4

v3 已在真实训练窗口保持128帧、2507token完成forward，MPS采样峰值23842.64MiB（约23.28GiB），随后backward报MPS标量类型错误，0完成backward/0update，27.298秒模型执行证据保留；该失败不是OOM。v4 独立新目录，基座与激活改为FP16，要求PEFT语言LoRA全部FP32，loss采用模型的FP32交叉熵。其余数据、128帧显式视频像素预算、优化设置保持。严格要求所有真实梯度有限、连通、后续更新非零及冻结/重载哈希一致；不把精度变化写成纯输入比较。新失败开启C++堆栈证据，不提高MPS上限，不隐式CPU fallback。通过探针才从相同FP16冷基座重新开始全量训练。
''')
names=list(old['files'])
for name in names:
    if name.endswith('.py'):ast.parse((DST/name).read_text(),filename=name)
lock=dict(schema='aic_mac_8b128_lowres_fp16_source_lock_v4',scope=old['scope'],
 created_utc=dt.datetime.now(dt.timezone.utc).isoformat(),parent_v3_source_lock_sha256=hashlib.sha256((SRC/'source_lock.json').read_bytes()).hexdigest(),
 files={name:hashlib.sha256((DST/name).read_bytes()).hexdigest() for name in names})
(DST/'source_lock.json').write_text(json.dumps(lock,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(hashlib.sha256((DST/'source_lock.json').read_bytes()).hexdigest())
(DST/'copy_verified_parent.py').write_text('''from pathlib import Path
import json,hashlib,shutil
root=Path('/Users/choubk/codex-workspace/projects/aic-video')
src=root/'mac_sft8b_128_lowres_20261006T0720Z';dst=root/'mac_sft8b_128_lowres_fp16_20261006T0724Z'
assert src.is_dir() and not src.is_symlink() and dst.is_dir() and not dst.is_symlink()
lock=src/'source_lock.json'
assert hashlib.sha256(lock.read_bytes()).hexdigest()=='fbb48910afe94eb8ab6aa50db1a2eb3174cab2d4c264be65c8aec6205e46dd0a'
for name,digest in json.loads(lock.read_text())['files'].items():
    source=src/name;assert not source.is_symlink() and hashlib.sha256(source.read_bytes()).hexdigest()==digest
    target=dst/name;assert not target.exists()
    target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,target)
print('PASS_MAC_LOCAL_VERIFIED_ASSET_FREE_SOURCE_FORK')
''')
