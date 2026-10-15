"""Finalize bounded factual probes and append actual execution to the discussion ledger."""
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import json,hashlib
BASE=Path(__file__).resolve().parent;ROOT=BASE/'w01_editorial_diagnostic_v1'
DISC=BASE.parent/'round6_score_alignment/rematch_discussion/aic_video_empty407_20261010'
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,d):
    with p.open('x',encoding='utf-8') as f:json.dump(d,f,ensure_ascii=False,indent=2)
def probe(folder,refs,output_name,extra_reads):
    assert (folder/'terminal.json').exists(),'Owned probe is still running; do not relaunch.'
    lines=[json.loads(s) for s in (folder/'stream.jsonl').read_text(encoding='utf-8-sig').splitlines() if s.strip()]
    calls=[r['step_update'] for r in lines if r.get('step_update',{}).get('step_type')=='tool' and r['step_update'].get('state')=='DONE']
    readmap={str(Path(r['path']).resolve()):r['frame_id'] for r in refs};allowed=set(readmap)|{str(p.resolve()) for p in extra_reads}
    writes={str((folder/output_name).resolve())};counts=Counter();issues=[]
    for c in calls:
        pars=c.get('tool_info',{}).get('parameters',{});pars=json.loads(pars) if isinstance(pars,str) else pars
        raw=pars.get('AbsolutePath') or pars.get('TargetFile');p=str(Path(raw).resolve()) if raw else None
        name=c.get('tool_name')
        if name=='view_file':
            counts[p]+=1
            if p not in allowed:issues.append('OUTSIDE_READ_WHITELIST')
        elif name=='write_to_file':
            if p not in writes:issues.append('OUTSIDE_WRITE_WHITELIST')
        else:issues.append('UNEXPECTED_TOOL:'+str(name))
    if any(counts[p]!=1 for p in readmap):issues.append('MISSING_OR_REPEATED_PNG')
    init=next((r['init'] for r in lines if r.get('event')=='init'),{})
    result=next((r['result'] for r in reversed(lines) if r.get('event')=='result'),None)
    exists=(folder/output_name).exists();doc=load(folder/output_name) if exists else None
    terminal=load(folder/'terminal.json');request=load(folder/'request.json')
    return dict(actual_model=init.get('model'),stream_sha256=sha(folder/'stream.jsonl'),terminal=terminal,
        declared_max_seconds=request['max_seconds'],actual_wall_seconds_with_startup_and_shutdown=terminal['elapsed_seconds'],
        strict_wall_budget_met=terminal['elapsed_seconds']<=request['max_seconds'],print_timeout_not_a_hard_wall_deadline=True,
        actual_PNG_read_count=sum(counts[p]==1 for p in readmap),tool_issues=sorted(set(issues)),actual_result_status=result and result.get('status'),
        actual_result_usage=result and result.get('usage'),output_sha256=sha(folder/output_name) if exists else None,output=doc,
        cash_cost='UNKNOWN_NOT_ZERO',semantic_correctness='NOT_CERTIFIED_BY_TOOL_COMPLETION')

if __name__=='__main__':
    refs=load(ROOT/'student_index.json')['frames'];one=next(r for r in refs if r['frame_id']=='F37');half=refs[32:]
    p2=ROOT/'h2_f37_single_frame_v1';p3=ROOT/'h3_second_half32_factual_v1'
    a=probe(p2,[one],'observation.json',[]);b=probe(p3,half,'facts.json',[p3/'input_index.json'])
    expected='siempre puedes ignorar a esas personas'
    a['root_previously_observed_subject_and_subtitle_match']=bool(a['output'] and a['output'].get('actual_image_read') is True and a['output'].get('subtitle_text')==expected and '男子' in a['output'].get('visible_subject',''))
    obs=b['output'].get('frame_observations',[]) if b['output'] else []
    geometry=[]
    if len(obs)!=32:geometry.append('EXPECTED_32_FACTS_MISSING')
    for o,r in zip(obs,half):
        if any(o.get(k)!=r[k] for k in ('frame_id','source_ordinal','local_seconds_exact')):geometry.append('FACT_IDENTITY_MISMATCH')
        if o.get('actual_image_read') is not True:geometry.append('READ_NOT_ATTESTED')
    b['fact_geometry_issues']=sorted(set(geometry))
    f37=next((o for o in obs if o.get('frame_id')=='F37'),None)
    b['F37_root_previously_observed_subtitle_match']=bool(f37 and f37.get('subtitle_text')==expected)
    b['F37_observation']=f37
    independent=load(ROOT/'independent/student_sealed.json')['frame_observations'][32:]
    def clean(x):return None if x in (None,'无字幕','none') else str(x).strip()
    differences=[]
    for o,r in zip(obs,independent):
        if o.get('frame_id')==r['frame_id'] and clean(o.get('subtitle_text'))!=clean(r.get('subtitle_text')):
            differences.append(dict(frame_id=r['frame_id'],fresh_32=o.get('subtitle_text'),independent=r.get('subtitle_text')))
    b['subtitle_literal_disagreements_with_independent']=differences
    b['agreement_is_not_gold']=True
    diagnostic=load(ROOT/'final_diagnostic_audit_v1.json')
    report=dict(status='CLOSED_BOUNDED_W01_DIAGNOSTICS_NOT_TRAINING_ADMISSION',utc=datetime.now(timezone.utc).isoformat(),
        full_diagnostic_sha256=sha(ROOT/'final_diagnostic_audit_v1.json'),single_frame=a,fixed_second_half32=b,
        original_preregistration_deviation_preserved=True,post_stop_distinct_windows=1,conservative_new_model_task_count=3,
        new_independent_full_review_records=1,new_optimizer_updates=0,new_426_calls=0,
        actual_new_CLI_invocations=6,pre_inference_connection_failures=2,model_turns_with_inference_including_original_interruption=4,
        original_STOP_sha256=sha(BASE/'slot6_silver24_v1/pilot_final_adjudication_v1.json'),
        original_STOP_unchanged=sha(BASE/'slot6_silver24_v1/pilot_final_adjudication_v1.json')==diagnostic['original_STOP_sha256'],
        current_37_66_zip_sha256=diagnostic['safe_baseline']['sha256'],new_official_score=None,pro_used_or_reserved=6,pro_remaining=2,
        interpretation='Single-frame success is evidence of this fresh-context recognition only. Fixed-half results require actual geometry and factual review, and neither establishes unique causation or dataset gold.',training_admitted=False)
    save(ROOT/'final_post_stop_execution_receipt_v1.json',report)
    ok32=not b['tool_issues'] and not b['fact_geometry_issues'] and b['F37_root_previously_observed_subtitle_match'] and b['strict_wall_budget_met']
    text=f'''# W01实际诊断结果与下一步

本轮继续执行一锅炖r04/r05决定，完成一份Gemini提案和一份新独立审阅；两边实际学生64张、原生64张，学生封存字节保持。新GPU训练、optimizer、426推理均0。原0/4 STOP和37.66交付包保持。

两份封存提案：Gemini保留22.83秒/7连续区间，独立者保留23.62秒/6连续区间；叙事单元为10对5，取舍分歧3.55秒。原B0 parser实际拒绝两份，不截去KEEP或填NO缝隙。它们是完整覆盖提案，不是通过语义验收的训练参考。

明确事实错误：F37主体是人物、字幕为siempre puedes ignorar a esas personas；长序列Gemini误写成下一镜头狗及y esconderte,，原生阶段仍错误。首次CLI十分钟打印超时、两次连接失败及同提案恢复均保留，一会话预注册未满足；教师seal错误ordinal范围另存纠错侧车。没有把这些失败洗成原科学协议PASS。

随后新增有界事实探针：fresh单图一次实际读图，{a['terminal']['elapsed_seconds']:.2f}秒完成，主体和字幕答对。固定F32..F63的32图fresh事实探针：实际读图{b['actual_PNG_read_count']}，终态{b['actual_result_status']}，输出身份问题{b['fact_geometry_issues']}，F37字幕匹配{b['F37_root_previously_observed_subtitle_match']}，与独立审阅字幕逐字差异{len(differences)}处。32图读取/身份/F37初步检查{'通过' if ok32 else '未全通过'}；这是诊断，不证明32图全部事实正确，也不能唯一归因长上下文。

已有当前训练源20人重要性评分的试探统计，KEEP不比NO明显高；精确native映射与AIC等价尚未验收。该源已经曝光，不能变成盲测，不能按本次统计选择阈值或造训练目标。

主控建议按三步推进：先采用短上下文事实提取并逐批检查帧号/主体/字幕，再在事实稳定后校准相对高光选择，最后判断完整目标是否需要新表达合同。优先修标签质量，暂不扩大数据或直接放宽五段。下一版必须前置固定准则，不事后按五段配额删标签；再取得足够合格来源与窗口后，才在原B8B上做小规模时间LoRA比较，空间框先沿用基线。

详细可执行草案见next_label_protocol_draft_v1.md；本文件是实际执行后的主控建议，未冒称Pro新裁决。Pro连续6/8，剩2。本次新增CLI共6次（含2次推理前连接失败），4个实际模型turn（含同提案恢复），人民币费用UNKNOWN非0；未新增付费服务、充值、下载或上传。
'''
    with (ROOT/'RESULT_AND_NEXT_STEP.md').open('x',encoding='utf-8') as f:f.write(text)
    ledger=DISC/'ledger.json';old=ledger.read_bytes();backup=DISC/'ledger-before-w01-execution-append.json'
    backup.open('xb').write(old);d=json.loads(old.decode('utf-8-sig'))
    d.setdefault('execution_followups',[]).append(dict(utc=report['utc'],status=report['status'],receipt_path=str(ROOT/'final_post_stop_execution_receipt_v1.json'),
        receipt_sha256=sha(ROOT/'final_post_stop_execution_receipt_v1.json'),result_path=str(ROOT/'RESULT_AND_NEXT_STEP.md'),
        result_sha256=sha(ROOT/'RESULT_AND_NEXT_STEP.md'),previous_ledger_sha256=hashlib.sha256(old).hexdigest(),
        original_STOP_unchanged=report['original_STOP_unchanged'],pro_used_or_reserved=6,pro_remaining=2,new_optimizer_updates=0,new_426_calls=0,
        discussion_rounds_r04_r05_and_prior_final_knowledge_preserved=True,new_execution_result_not_yet_sent_to_external_sites=True))
    ledger.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'result':str(ROOT/'RESULT_AND_NEXT_STEP.md'),'single_frame_correct':a['root_previously_observed_subject_and_subtitle_match'],
        'half32_initial_check':ok32,'subtitle_literal_differences':differences,'old_STOP_unchanged':report['original_STOP_unchanged'],'training_admitted':False},ensure_ascii=False))
