"""Refresh only unbound V12 handoffs from a current live snapshot."""
import base64,datetime as dt,hashlib,json
from pathlib import Path
from register_b2_package_v1 import remote,REMOTE,RUN
ENTRY='teacher_student_autopilot_v12'
MARKER='<!-- END_CURRENT_TEACHER_V12 -->'

def main():
    value=json.loads((RUN/'controller/monitor_teacher_v12/latest.json').read_bytes());snap=value['snapshot']
    raw=json.loads(remote("""from pathlib import Path
import base64,hashlib,json
h=Path(%r)/%r
out={n:base64.b64encode((h/n).read_bytes()).decode() for n in ('start_receipt.json','registration.json','resume_cpu_acceptance.json','resume_handoff.json') if (h/n).is_file()}
p=h/'source_lock.json';v=json.loads(p.read_bytes());out['lock_summary']={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'files':len(v['files']),'schema':v['schema']}
print(json.dumps(out))
"""%(REMOTE,ENTRY),echo=False))
    for name,data in raw.items():
        if name=='lock_summary':continue
        target=RUN/ENTRY/name;data=base64.b64decode(data)
        if target.exists():assert target.read_bytes()==data
        else:target.write_bytes(data)
    start=json.loads((RUN/ENTRY/'start_receipt.json').read_bytes());ls=raw['lock_summary']
    assert ls['sha256']==snap['source_lock_sha256']==start['source_lock_sha256']
    stage=(snap.get('completion') or snap.get('progress') or {}).get('status',(snap.get('progress') or {}).get('stage','SOURCE_PREFLIGHT_CPU'))
    parts=snap.get('v8_stage_receipts') or {};rp=parts.get('review_progress') or {};first=parts.get('first_review_generation')
    steps=(snap.get('student_progress') or {}).get('optimizer_steps',0)
    receipt=dict(status='REGISTERED_V12_EXACT_REVIEW_CONTINUATION_NOT_FINAL_QUALITY',utc=dt.datetime.now(dt.timezone.utc).isoformat(),
        entry=ENTRY,source_lock_sha256=ls['sha256'],frozen_files=ls['files'],launch_utc=start['utc'],launch_historical_pid=start['pid'],
        snapshot_utc=snap['utc'],actual_stage=stage,owned_commands=snap.get('processes',[]),owned_servers=snap.get('owned_servers',[]),
        original_labels=160,original_reviews=28,remaining_registered_review_calls=132,actual_new_review_progress=rp,
        first_review_generation=first,original_V11_STOP_and_successes_preserved=True,new_label_calls=0,new_T_optimizer_updates=steps,
        new_ZIP_complete=False,large_transfer_bytes=0,per_frame_or_teacher_raw_published=False)
    rpath=RUN/'controller/autonomy_v12_registration_20261008.json';rpath.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    top=f"""## 2026-10-08：V12修复canonical键顺序衔接，原160标签与28盲复查保留

当前唯一入口 `{ENTRY}/CONTINUE.md` 与 `PROTOCOL.md`。原V11完整160标注已自然成功（本阶段新134/逐SHA复用26）；全量第二选择第五条后在09:15:44 UTC工程STOP。已复现：旧V10成功原JSON文件验证通过，排序JSONL读出对象与原对象完全相等，但parsed对象键顺序不同，再序列化得到不同canonical SHA而误拒绝。原回答、canonical字串、窗口端点、标签对象、原STOP均保持。

V12仅从exact SHA和隔离原validator批准的原文件读取canonical投影顺序。Linux原地原validator/全部输入及PNG/RGB核160/28，2真实旧排序失败回放与13拒绝合同通过，CPU/复用新调用0。冻 `{ls['files']}` 文件，锁 `{ls['sha256']}`；单次launcher `{start['utc']}`，历史PID/PGID `{start['pid']}`。实际 `{snap['utc']}` 所属完整命令进程{len(snap.get('processes',[]))}、server{len(snap.get('owned_servers',[]))}，阶段 `{stage}`。历史PID、GPU闲或旧progress均不代表持续存活/卡死。

原160标签/28盲选择只按完整exact manifest/SHA/原validator复用，剩132独立第二选择；新label调用0。原full失败wrapper自然exit1/stop_reason null，真实charge6748.806357712485秒已追加账本，未发送任何旧/外部进程信号。新/旧review锁只准入原160记录与28原reviewexact授权，不泛化旧回答。固定160/24/语义prompt/BF grammar/输入/原validator/学生和生产配方保持。首个阻塞窗真实新review状态 `{(first or {}).get('status','PENDING_REAL_GENERATION')}`；实际新review进度 `{rp}`。原支持/UNKNOWN不改，同教师一致性不是人工真值。

自动接续剩复查→原监督科学门→可靠完整窗口路线A学生2–4真实更新同optimizer/RNG、旧B candidate0开发→NONTEST8→426/11独立strict ZIP。边界可靠仅准入独立路线B；观察仍不可靠按授权登记C同8B全源粗览/局部非测试匹配。B/C以实际协议/回执为准，不假称运行；新T实际更新 `{steps}`，当前没有新最终ZIP。禁止改冻结源码或重复launcher/成功生成；CPU SHA与顺序解码/共享等待可能合法。

B2用户37.32/DONE（317401字节SHA0f8c95f01222a28a053e6f80b76b3d4d7ac3dc82077f4dd533605337bc6883a3），旧B37.63绑定旧包SHA86bd5301f6f6771a8451b32063781e214cdd70245ae5513f2a767eaecb9ebe54，各旧成绩原样保留。每15分钟aic-linux静默入口controller/checkpoint_teacher_v12.py，只记录实时实际命令/PGID/IO、原provider终态、新复查/学生/strict/resource/queue与artifact bytes/mtime。新大流量先许可，小量控制直SSH、Mac退出，100confirm不读、复赛不手看调参，共享锁/账本7200与外部任务/连接/服务保持。仅最终ZIP全部真实验收后一次通知、删除监控、不归档；最终包留Linux，新官网分未知。

{MARKER}

"""
    targets=[RUN.parents[3]/'AGENTS.md',RUN/'STATUS_AUTOPILOT_20261007.md',RUN/'controller/AUTONOMOUS_EXECUTION_20261008.md',RUN/'controller/V8_REPAIR_AND_EXECUTION_20261008.md']
    payload={}
    for path in targets:
        old=path.read_bytes().decode('utf-8')
        if MARKER in old:
            head,tail=old.split(MARKER,1);global_prefix=head.split('## 2026-10-08：V12',1)[0] if path.name=='AGENTS.md' else ''
            content=global_prefix+top+tail.lstrip('\r\n')
        else:
            anchor='## 2026-10-08：V11证据编号'
            assert anchor in old
            idx=old.index(anchor)
            prefix=old[:idx] if path.name=='AGENTS.md' else ''
            content=prefix+top+old[idx:]
        path.write_text(content,encoding='utf-8',newline='\n')
        if path.name!='AGENTS.md':payload[path.relative_to(RUN).as_posix()]=base64.b64encode(path.read_bytes()).decode()
    for path in (rpath,RUN/'controller/V12_CANONICAL_HANDOFF_REPRODUCTION_20261008.json'):
        payload[path.relative_to(RUN).as_posix()]=base64.b64encode(path.read_bytes()).decode()
    remote("""import base64,json,hashlib
from pathlib import Path
r=Path(%r);items=json.loads(base64.b64decode(%r));bound=set()
for lock in r.glob('*/source_lock.json'):
 v=json.loads(lock.read_bytes());entries=v.get('files',v.get('production_files'))
 if isinstance(entries,dict):names=list(entries)
 elif isinstance(entries,list) and all(isinstance(x,dict) and isinstance(x.get('path'),str) for x in entries):names=[x['path'] for x in entries]
 else:raise RuntimeError('unknown source lock schema')
 bound.update(str((lock.parent/n).resolve()) for n in names)
for name,data in items.items():
 p=r/name;assert p.resolve().is_relative_to(r.resolve()) and str(p) not in bound
 new=base64.b64decode(data)
 if p.exists() and p.read_bytes()!=new:
  previous=p.read_bytes();a=r/'controller/handoff_history_v12';a.mkdir(exist_ok=True);q=a/(p.name+'.'+hashlib.sha256(previous).hexdigest())
  if not q.exists():q.write_bytes(previous)
 p.parent.mkdir(exist_ok=True,parents=True);p.write_bytes(new)
print(json.dumps({'status':'PASS_UNBOUND_V12_HANDOFF_ONLY','files':len(items)}))
"""%(REMOTE,base64.b64encode(json.dumps(payload).encode()).decode()))
    print(json.dumps({k:receipt[k] for k in ('actual_stage','source_lock_sha256','frozen_files','new_T_optimizer_updates')},ensure_ascii=False))

if __name__=='__main__':main()
