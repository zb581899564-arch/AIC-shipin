"""Explicit core and engineering aggregates only; no private plan/raw export."""
import datetime as dt,hashlib,json,shutil
from pathlib import Path
from register_b2_package_v1 import RUN,REMOTE,remote

def publish():
    import publish_b2_snapshot as original
    PUB,WORKSPACE,REL=original.PUB,original.WORKSPACE,original.REL
    entry='balanced_two_window_risk_v3';here=RUN/entry
    s=json.loads((RUN/'controller/monitor_balanced_two_window_risk_v3/latest.json').read_bytes())
    assert s['all_frozen_sha_pass'] and s['source_lock_sha256'] and s['all_new_done_bound_sha']
    names=('bw_common.py','bw_native.py','bw_engine.py','bw_attempt.py','bw_video.py','bw_prepare.py','bw_cpu.py',
        'bw_prefix_cpu.py','bw_first_replay.py','bw_report.py','bw_alias_nontest.py','controller.py','packager.py',
        'freeze.py','launch.py','final_acceptance.py','engineering_cpu_recover.py','PROTOCOL.md')
    actual=json.loads(remote('''from pathlib import Path
import json,hashlib,socket
assert socket.gethostname()=='inspur-NP5570M5'
r=Path(%r)/%r;lock=json.loads((r/'source_lock.json').read_bytes())
assert hashlib.sha256((r/'source_lock.json').read_bytes()).hexdigest()==%r
result={}
for name in %r:
 p=r/name;s=hashlib.sha256(p.read_bytes()).hexdigest();assert lock['files'][str(p)]==s;result[name]=s
c=json.loads((r/'cpu_acceptance.json').read_bytes())
print(json.dumps(dict(core=result,cpu_status=c['status'],cpu_counts=c['counts'],max_input_tokens=c['max_input_tokens'],
 cpu_receipt_sha256=hashlib.sha256((r/'cpu_acceptance.json').read_bytes()).hexdigest())))
'''%(REMOTE,entry,s['source_lock_sha256'],names),echo=False))
    for n in names:assert hashlib.sha256((here/n).read_bytes()).hexdigest()==actual['core'][n],n
    selected=[here/n for n in names]+[RUN/'controller'/n for n in ('inspect_balanced_two_window_risk_v3.py',
        'checkpoint_balanced_two_window_risk_v3.py','record_balanced_two_window_risk_v3_20261009.py',
        'publish_balanced_two_window_snapshot.py','publish_b2_snapshot.py')]
    for p in selected:
        q=PUB/p.relative_to(WORKSPACE);q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q);assert p.read_bytes()==q.read_bytes()
    scopes={}
    for scope,v in s['scopes'].items():
        scopes[scope]={k:v[k] for k in ('read_utc','fresh_done','recovered_exact_prior_done','accepted_route_done','raw','failures','all_done_bound_sha')}
        if 'replay_acceptance.json' in v:scopes[scope]['accepted_new_CPU_replays']=v['replay_acceptance.json']['accepted_new_requests']
        if 'independent_validation.json' in v:
            val=v['independent_validation.json'];scopes[scope]['independent_status']=val['status'];scopes[scope]['all11_checks']=val['checks']
        scopes[scope]['candidate_archives']=v['candidate_archives']
    final=s['stages'].get('final_acceptance.json');completion=s['stages'].get('completion.json')
    resources={}
    for name,value in s['resources'].items():
        receipt=value.get('receipt') or {}
        resources[name]={key:receipt.get(key) for key in ('status','exit_code','stop_reason','charged_seconds')}
        resources[name].update(receipt_sha256=value.get('sha256'),unique_terminal_match=value.get('unique_terminal_match'))
    aggregate=dict(status='CURATED_BALANCED_TWO_WINDOW_ENGINEERING_SNAPSHOT',snapshot_utc=s['utc'],entry=entry,
        source_lock_sha256=s['source_lock_sha256'],frozen_files=s['frozen_files'],all_frozen_SHA_pass=s['all_frozen_sha_pass'],
        stage=(s['stages'].get('progress.json') or {}).get('stage'),cpu={k:v for k,v in actual.items() if k!='core'},
        exact_planned_new_calls_this_version={'developer':15,'rematch':116},exact_recovered_prior_calls=1,planned_route_actual_calls=132,exact_old_calls={'nontest':8,'developer':96,'rematch':405},
        source_records={'nontest':8,'developer':104,'rematch':426},local_windows={'nontest':8,'developer':112,'rematch':521},
        production_weight='ORIGINAL_B_8B',logical_parameters=8782459120,adapter_saved_equality=288,
        new_optimizer_updates=0,new_teacher_32B_calls=0,new_overview_calls=0,new_spatial_calls=0,
        scopes=scopes,resources=resources,ledger=s['ledger'],user_explicitly_accepted_experiment_risk=True,
        independent_quality_reference='UNKNOWN',official_score=None,old_B_best_score=37.63,
        old_B_best_ZIP_SHA='86bd5301f6f6771a8451b32063781e214cdd70245ae5513f2a767eaecb9ebe54',
        complete_426=bool(completion),final_status=final['status'] if final else None,
        final_candidate={k:final[k] for k in ('candidate','zip_bytes','zip_sha256')} if final else None,
        final_acceptance_sha256=s['component_sha256'].get('final_acceptance.json'),
        completion_sha256=s['component_sha256'].get('completion.json'),
        prior_failed_GPU={k:final['prior_failed_resource'][k] for k in ('sha256','charged_seconds')} if final else None,
        frame_effect_vs_V14=final['output_effect_vs_V14'] if final else None,
        raw_frames_private_plans_weak_labels_full_discussion_model_or_ZIP_exported=False)
    derived=PUB/REL/entry/'aggregate_execution.json';derived.write_text(json.dumps(aggregate,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    if final:
        state=f'完整426候选已独立验收：{final["zip_bytes"]}字节，SHA256 `{final["zip_sha256"]}`，Linux路径 `{final["candidate"]}`。'
        execution='非测试16和复赛116个变化窗口的真实回答及全部132项独立CPU回放已完成，其中本工程版新生成131个、原有效回答exact恢复1个；其余请求按完整身份及SHA引用。'
    else:state=f'实际阶段 `{aggregate["stage"]}`；尚未完成新的426最终包。'
    if not final:execution='计划非测试16和复赛116个变化窗口真实推理，其余请求仅exact引用。'
    body=(f'\n## 当前双窗均衡风险实验（快照UTC {s["utc"]}）\n\n'
        '用户明确接受试验不确定性后，执行网页讨论中的双窗均衡分区候选。仅原30秒主窗加短尾、总长严格30至60秒的两窗改为精确中点等长两窗；'
        '保留原B权重、B0提示/grammar、native时钟/floor64和原完整空间源场。新训练更新0。'
        f'{execution}'
        f'{state} 非测试和最终包工程通过不等于提分，独立质量参考和新官网分未知，可能低于旧最佳37.63。'
        f'见[协议]({REL}/{entry}/PROTOCOL.md)和[工程聚合]({REL}/{entry}/aggregate_execution.json)。包留Linux，不自动回传或官网提交。\n\n'
        '<!-- END_CURRENT_BALANCED_TWO_WINDOW_RISK -->\n')
    def front(t):
        first,rest=t.split('\n',1)
        if '<!-- END_CURRENT_BALANCED_TWO_WINDOW_RISK -->' in rest:rest=rest.split('<!-- END_CURRENT_BALANCED_TWO_WINDOW_RISK -->',1)[1]
        return first+'\n'+body+rest
    original.edit(PUB/'README.md',front)
    for n in ('SOLUTIONS.md','REPRODUCTION.md'):original.edit(PUB/'docs'/n,lambda t:front(t).replace(']('+REL,'](../'+REL))
    mp=PUB/'docs/publication_manifest.json';raw=mp.read_bytes();ending='\r\n' if b'\r\n' in raw else '\n';manifest=json.loads(raw)
    present={r['path'] for r in manifest['files']}
    for p in selected+[derived]:
        derived_flag=p==derived;rel=p.relative_to(PUB if derived_flag else WORKSPACE).as_posix()
        if rel not in present:manifest['files'].append(dict(path=rel,source_relative_path=None if derived_flag else rel,bytes=0,sha256='',
            category='aggregate_acceptance_no_frame_data' if derived_flag else ('project_code_or_configuration' if p.suffix=='.py' else 'experiment_protocol_or_acceptance')))
    for r in manifest['files']:
        data=(PUB/r['path']).read_bytes();r.update(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
    manifest['updated_utc']=dt.datetime.now(dt.timezone.utc).isoformat()
    mp.write_bytes((json.dumps(manifest,ensure_ascii=False,indent=2)+'\n').replace('\n',ending).encode())
    print(json.dumps(dict(status='PASS_CURATED_BALANCED_TWO_WINDOW_CORE_AND_AGGREGATE',selected_files=len(selected),new_ZIP_raw_frame_or_model_exported=False)))

if __name__=='__main__':publish()
