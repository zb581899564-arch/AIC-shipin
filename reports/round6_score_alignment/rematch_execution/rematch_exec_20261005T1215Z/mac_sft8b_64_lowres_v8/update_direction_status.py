from pathlib import Path
import json,datetime as dt,hashlib
HERE=Path(__file__).resolve().parent;RUN=HERE.parent;PROJECT=RUN.parents[3]
assert PROJECT.name=='AIC视频'
probe=json.loads((HERE/'controller/progress_snapshot_01.json').read_text())
status=json.loads((HERE/'controller/status_snapshot_01.json').read_text())
linux=json.loads((HERE/'controller/linux_status_snapshot_01.json').read_text())
assert probe['optimizer_steps']>=1 and probe['effective_batches']>=16 and status['controller_alive']
assert probe['initialization_seed_restored_after_tests']==20261006 and probe['cache_release_count']>=16
assert probe['deepstack_equivalence_tests']['tests']==5
assert probe['peak_mps_driver_mib']*2**20<=probe['mps_recommended_max_memory_bytes']
first=probe['updates'][0];assert first['changed_lora_tensors']>0
assert all(item['connected']==item['finite']==144 for item in first['lora_gradient_evidence'].values())
utc=dt.datetime.now(dt.timezone.utc);local=utc.astimezone(dt.timezone(dt.timedelta(hours=8)))
peak=probe['peak_mps_driver_mib']/1024
block=f'''\n## Mac改低内存64帧方向并真实更新（{local:%Y-%m-%d %H:%M}，UTC+8）

用户授权修复内存，若128帧支撑不起则换方向。128帧v7虽有真实更新，修复后仍采样56.59GiB，超出当时live MPS建议51.84GiB；主控只停止登记的本任务训练子进程组，旧结果、源码锁与账本保留，未启动其full。新独立 `mac_sft8b_64_lowres_v8/PROTOCOL.md`：同一固定8B、最多64帧、每帧实际视频处理像素<=32768、max_seq6144，704train/724已知正窗口/602组、r16/lr5e-5/seed20261006/5epochs保持。方向为低内存区间JSON SFT，含输入/解码/硬件差异，不能单独归因或承诺提分；C正式BCE未知负语义门仍STOP，不造负例。

真实codec/processor CPU8/8、继续门3/3、进程树归属2/2通过；MPS/CPU DeepStack前向梯度与掩码/错形状拒绝5/5通过。保留显式VIDEO预算和新鲜嵌套kwargs、局部FP32 DeepStack索引后转回BF16、严格token/feature行数与hidden维度检查及contiguous掩码、每microbatch同步释放缓存和测试后恢复登记RNG；不编辑安装库、不隐式CPU fallback、不提高MPS上限。实际参数8,782,459,120。

当前64帧实际探针{probe['optimizer_steps']}/3更新、{probe['effective_batches']}/48完成backward，首步288张量梯度连通/有限、{first['changed_lora_tensors']}张量变化，采样MPS峰值{peak:.2f}GiB，当前无失败；最终48microbatches/3updates的冻结与重载仍待运行结束验收，完整Mac训练尚未启动。单次控制器实查存活；全部门通过才自动从冷基座新LoRA开始5epochs/3620microbatches/227updates。源码锁 `6d42f4768e542c13c7c5d72f988c3dc84970e2a5edc0b53f2963cccc4445d9fa`，33文件已Mac核字节并在Linux归档独立核验。Mac目录 `/Users/choubk/codex-workspace/projects/aic-video/mac_sft8b_64_lowres_20261006T0748Z`；查该版本CONTINUE_MAC.md，不重开launcher、不修改运行中绑定文件。

Linux原64帧完整训练保持正常，最新{linux['optimizer_steps']}/227更新、{linux['effective_batches']}/3620有效，未报失败；8B推理封包尚未开始。本Mac接续不自动开发评测、比赛推理、封包或上传。累计GPU不限、追加计费、Linux7200秒偏移、共享锁、唯一Mac工作根和合计80GiB边界不变。当前实证见 `controller/mac_memory_repair_start_01.json`。
'''
for path in [PROJECT/'AGENTS.md',PROJECT/'ROADMAP.md',RUN/'REPORT.md',RUN/'CONTINUE.md']:
    text=path.read_text(encoding='utf-8');head,sep,tail=text.partition('\n')
    path.write_text(head+'\n'+block+'\n'+tail,encoding='utf-8')
receipt=dict(status='PASS_MAC_ALTERNATIVE_64_FRAME_REAL_BACKWARD_AND_FIRST_UPDATE',checked_utc=utc.isoformat(),
    scope=probe['scope'],source_lock_sha256=probe['source_lock_sha256'],controller_alive=True,
    optimizer_steps=probe['optimizer_steps'],effective_batches=probe['effective_batches'],first_update=first,
    peak_mps_driver_gib=peak,full_probe_completed=False,full_training_started=False,quality_claim=False,
    abandoned128_reason='working set exceeds live MPS recommended memory',
    linux_optimizer_steps=linux['optimizer_steps'],linux_effective_batches=linux['effective_batches'],
    snapshots={name:hashlib.sha256((HERE/'controller'/name).read_bytes()).hexdigest() for name in
       ['progress_snapshot_01.json','status_snapshot_01.json','linux_status_snapshot_01.json']})
with (RUN/'controller/mac_memory_repair_start_01.json').open('x',encoding='utf-8') as f:f.write(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n')
(HERE/'STATUS_REPAIR_START.md').write_text('# Mac低内存64帧实际启动验收\n'+block,encoding='utf-8')
print(json.dumps(receipt,ensure_ascii=False))
