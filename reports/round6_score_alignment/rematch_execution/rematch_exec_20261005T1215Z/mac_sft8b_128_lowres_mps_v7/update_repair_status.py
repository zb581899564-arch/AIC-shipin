from pathlib import Path
import json,hashlib,datetime as dt
HERE=Path(__file__).resolve().parent;RUN=HERE.parent;PROJECT=RUN.parents[3]
assert PROJECT.name=='AIC视频'
probe=json.loads((HERE/'controller/progress_snapshot_01.json').read_text())
status=json.loads((HERE/'controller/status_snapshot_01.json').read_text())
linux=json.loads((HERE/'controller/linux_status_snapshot_01.json').read_text())
assert probe['optimizer_steps']>=1 and probe['effective_batches']>=16 and status['controller_alive']
assert probe['deepstack_equivalence_tests']['tests']==5
assert probe['initialization_seed_restored_after_tests']==20261006 and probe['cache_release_count']>=16
assert probe['peak_mps_driver_mib']*2**20<=probe['mps_recommended_max_memory_bytes']
first=probe['updates'][0];assert first['changed_lora_tensors']>0
assert all(item['connected']==item['finite']==144 for item in first['lora_gradient_evidence'].values())
utc=dt.datetime.now(dt.timezone.utc);local=utc.astimezone(dt.timezone(dt.timedelta(hours=8)))
peak=probe['peak_mps_driver_mib']/1024
block=f'''\n## Mac内存修复已真实更新（{local:%Y-%m-%d %H:%M}，UTC+8）

用户授权修复内存及必要时改变方向。当前独立v7 `mac_sft8b_128_lowres_mps_v7/PROTOCOL.md`，Mac目录 `/Users/choubk/codex-workspace/projects/aic-video/mac_sft8b_128_lowres_mps_20261006T0740Z`，保留128帧，以显式VIDEO总像素预算限制每帧实际处理像素<=32768、序列<=6144。旧AutoProcessor image max_pixels没有约束视频，新调用固定metadata/no-resampling并每次重新建立嵌套参数字典。MPS2.5.1的半精度IndexBackward不支持index_put累加，现仅实例级DeepStack索引加法转FP32再转回BF16；每microbatch同步释放空闲MPS缓存，测试后恢复登记种子20261006。模型/视觉参数保持冻结，无库全局修改、隐式CPU fallback或MPS上限提高。

真实codec/processor CPU8/8、阶段继续门3/3、进程树归属2/2、CPU BF16/FP16和MPS BF16前向/梯度逐元素一致与掩码校验5/5通过。当前实际探针{probe['optimizer_steps']}/3更新、{probe['effective_batches']}/48完成backward，首步梯度有限/288张量连通、{first['changed_lora_tensors']}张量变化，采样MPS峰值{peak:.2f}GiB，当前无失败；最终全探针冻结/重载仍待运行结束验收，完整Mac训练尚未启动。单次后台控制器实查存活；3更新探针全部验收通过才自动从冷基座新LoRA开始同一704train/724窗口/5epochs/227更新，保持lr5e-5和r16；不自动开发评测、测试推理、封包或上传。源码锁 `fb72b24e524423fc9af585a404eb954c36bcf59eca4df3685ef5211e2c647936`，33文件已双端字节核验，运行期间不编辑或重复launcher。查询见该版本CONTINUE_MAC.md。

v1 OOM、v2辅助进程误判STOP、v3/v4索引类型STOP完整保留并分别计费；v5首步可更新，但缓存峰值超过live recommended且测试改变初始化RNG，主控仅停止已登记的本任务训练子进程组，更新证据与失败receipt保留。不能用旧等待快照判断当前状态。Linux冻结64帧全量保持正常，最新{linux['optimizer_steps']}/227更新、{linux['effective_batches']}/3620有效，未报失败；8B推理封包尚未开始。C正式BCE未知负语义门保持STOP。实际快照与首步验证见 `controller/mac_memory_repair_start_01.json`。
'''
for path in [PROJECT/'AGENTS.md',PROJECT/'ROADMAP.md',RUN/'REPORT.md',RUN/'CONTINUE.md']:
    text=path.read_text(encoding='utf-8');head,sep,tail=text.partition('\n')
    path.write_text(head+'\n'+block+'\n'+tail,encoding='utf-8')
receipt=dict(status='PASS_MAC_128_LOWRES_REAL_BACKWARD_AND_FIRST_UPDATE',checked_utc=utc.isoformat(),
    scope=probe['scope'],source_lock_sha256=probe['source_lock_sha256'],controller_alive=status['controller_alive'],
    optimizer_steps=probe['optimizer_steps'],effective_batches=probe['effective_batches'],first_update=first,
    peak_mps_driver_gib=peak,full_probe_completed=False,full_training_started=False,quality_claim=False,
    linux_optimizer_steps=linux['optimizer_steps'],linux_effective_batches=linux['effective_batches'],
    snapshots={name:hashlib.sha256((HERE/'controller'/name).read_bytes()).hexdigest() for name in
       ['progress_snapshot_01.json','status_snapshot_01.json','linux_status_snapshot_01.json']})
with (RUN/'controller/mac_memory_repair_start_01.json').open('x',encoding='utf-8') as f:f.write(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
(HERE/'STATUS_REPAIR_START.md').write_text('# Mac内存修复实际启动验收\n'+block,encoding='utf-8')
print(json.dumps(receipt,ensure_ascii=False))
