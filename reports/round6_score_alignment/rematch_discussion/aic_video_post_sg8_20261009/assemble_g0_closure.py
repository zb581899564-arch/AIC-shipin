"""Assemble evidence from performed read-only checks, without rerunning them."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
H=Path(__file__).resolve().parent
def read(n):return json.loads((H/n).read_text(encoding='utf-8-sig'))
def sha(n):return hashlib.sha256((H/n).read_bytes()).hexdigest()
def write(n,d):
    with (H/n).open('x',encoding='utf-8',newline='\n') as f:json.dump(d,f,ensure_ascii=False,indent=2);f.write('\n')
refs=read('reference-qualification-report.json');p=read('plan-metadata-g0-readonly.json');v=read('independent-g0-verification.json');f=read('fallback-registration-readonly.json')
assert p['plan_sha256']==v['plan_sha256']
for row in p['rows']:
    q=next(x for x in v['rows'] if x['record_sha']==row['record_sha'])
    for name,ids in [('old_ordinal_sha',q['old_ordinals']),('proposed_ordinal_sha',q['new_ordinals'])]:
        assert row[name]==hashlib.sha256(json.dumps(ids,separators=(',',':')).encode()).hexdigest()
    assert all(row[k]==q[k] for k in ['group_sha','source_sha','old_tail_kept','old_tail_removed'])
assert v['affected_groups']==p['affected_groups']==8
assert not f['registered_authority_exists']
assert all(t['status']=='PASS' for t in v['tests'])
scope=dict(status='FIXED_INPUT_SCOPE_CLOSED',local_document_bindings=refs['bindings'],remote_metadata_bindings=v['bindings'],additional_registration=f,media_pixels_read=False,weak_answers_read=False,test_predictions_read=False,full_disk_scan=False,new_model_decoder_processor_optimizer=0)
write('input_scope.json',scope)
with (H/'reference_qualification.jsonl').open('x',encoding='utf-8') as out:
    for r in refs['rows']:
        # Existing registration evidence is not a newly byte-verified media asset.
        x=dict(r,field_status={
            'registration_document_identity':'PASS_BOUND_DOCUMENT',
            'actual_media_or_label_export_identity':'UNKNOWN_NOT_OPENED_IN_THIS_SCOPE',
            'independent_task_matched_semantic_reference':'FAIL_NOT_ESTABLISHED',
            'complete_coverage_or_negative_meaning':'UNKNOWN_UNANNOTATED_AND_UNSELECTED_NOT_NEGATIVE',
            'source_mapping_for_new_experiment':'UNKNOWN_NO_QUALIFIED_NEW_REFERENCE',
            'training_permission':'FAIL_NOT_ESTABLISHED_BY_THIS_REVIEW',
            'competition_permission':'FAIL_NOT_ESTABLISHED_BY_THIS_REVIEW',
            'external_sharing_permission':'UNKNOWN_NOT_GRANTED',
            'pretraining_exposure':'UNKNOWN',
            'independent_semantic_review':'NOT_RUN'})
        if r['entry']=='GNMC':x['field_status'].update(training_permission='FAIL_EXPLICIT_PROJECT_DIAGNOSTIC_LIMIT',competition_permission='FAIL_EXPLICIT_PROJECT_DIAGNOSTIC_LIMIT',native_target_match='FAIL_NO_NATIVE_9_16_IN_REVIEWED_README',declared_local_diagnostic_scope='PASS_RECORDED_PROTOCOL_ONLY')
        if r['entry']=='ROUND3_987':x['field_status']['label_generator_independence']='FAIL_MODEL_GENERATED_DOUBAO'
        if r['entry']=='P1B_PILOT':x['field_status']['annotation_completed']='FAIL_DEFAULT_UNANNOTATED_NO_NEW_EXPORT_FOUND'
        out.write(json.dumps(x,ensure_ascii=False)+'\n')
write('source_exposure.json',dict(status='SOURCE_GROUP_METADATA_ESTABLISHED_INDEPENDENT_LABEL_EXPOSURE_NOT_ESTABLISHED',developer_records=104,developer_source_groups=96,affected_records=8,affected_groups=8,affected_group_hashes=[r['group_sha'] for r in v['rows']],developer_prior_exposure='OBSERVED_BY_C_B1_D_Q_EXPLORATIONS_NOT_NEW_HOLDOUT',reference_rows=[dict(entry=r['entry'],registered_exposure=r['exposure'],new_experiment_independence='UNKNOWN_NOT_QUALIFIED') for r in refs['rows']],global_pretraining_exposure='UNKNOWN',no_confirm100_access=True,evidence=['reference-qualification-report.json','independent-g0-verification.json']))
write('two_window_plan.json',dict(status='PASS_TWO_WINDOW_METADATA_PLAN_ONLY',plan_sha256=v['plan_sha256'],records=104,unchanged_records=96,affected_records=8,affected_groups=8,planned_changed_requests=16,rows=v['rows'],consumer_fraction_boundary_admission='NOT_RUN',rgb_processor_token_model='NOT_RUN',quality='UNKNOWN'))
write('cpu_acceptance.json',dict(status='PASS_INDEPENDENT_PLAN_RECOMPUTATION_AND_15_METADATA_CONTRACTS',tests=v['tests'],all_8_old_and_new_ordinal_hashes_equal=True,independent_method='linear Fraction membership and divmod floor64; original planner uses bisect; no planner import',verification_sha256=sha('independent-g0-verification.json'),consumer_boundary='NOT_RUN_FLOAT_ROUNDTRIP_COUNTEREXAMPLE_RECORDED',scope='metadata and synthetic mathematics, not full production admission',measured_verifier_cpu_seconds=v['cpu_seconds'],measured_verifier_wall_seconds=v['wall_seconds'],measured_verifier_peak_rss_kib=v['peak_rss_kib'],measured_verifier_bytes_read=v['bytes_read'],earlier_checks_CPU_peak='NOT_INSTRUMENTED_NOT_ASSUMED_ZERO',new_model_calls=0,new_decoder_calls=0,new_processor_calls=0,new_optimizer_updates=0))
decision='''# 本轮最终决策与实际执行：有界G0结束，NO_426

用户授权主控在一锅炖讨论后直接执行。本轮四普通网页席位完成两轮；Chrome研究项目GPT-6 Pro slot5正式答复完整保存。本轮消耗1次、连续预算5/8，余3次。主控采纳一次有界的已有参考资格审计＋开发双窗精确CPU计划，现已执行并封存。没有新训练、新GPU任务或新426包；“完成”只指本工作包。

## 决策依据与异议

SG8原工程成功而固定科学门失败，确认3/6为正、确认及全组均值负，保留原NO_426，不换组/改公式/降门。均衡二分属于新的输入划分，不能被SG8结果直接证伪；但更多左上下文同时交换掉旧尾部采样并新增中点边界，现有行为指标不足以判定高光质量方向。主控同意本轮不购买16窗推理或426风险包。

Gemini第二轮仍支持有限均衡风险实验；其异议是严格停止可能错过实际涨分机会。完整原文保留。本决策承认机会成本，不声称NO_426在真实官网分数上必然最优，不冒充全席共识。Tibo/Grok支持短有界G0。Sol真实第二轮撤回纯行为门、支持参考资格先行并提出条件实验，较Pro“所有本轮出口均NO_426”略宽；本轮采用Pro更窄工作范围。

## 原文保存补正

核对时发现sol-r01.md误保存了上一轮复制内容。原文件、已发送context-p01.md与Pro回答均保持，不回写历史；现从已完成网页回复重新复制真实第二轮至sol-r01-corrected.md，并完整追加最终卷宗。主控此前摘要已正确记录其撤回，Pro也明确指出附件正文未同步；该补正不改变当前NO_426决定，不再消耗Pro知会额度。

## 已实际执行

1. 固定8份既有登记文档、p1b顶层已登记export文件名及原C fallback/authority/NONTEST登记只读核验。未出现新的可审、任务匹配独立参考入口；未全盘扫描，未登记其他资产仍UNKNOWN。987豆包参考保持模型弱标签，p1b默认UNANNOTATED不转负；GNMC项目协议仅本地诊断，不能批准训练/比赛测试/打包/提交，原生9:16参考未成立。逐字段表保留身份、用途、覆盖和曝光UNKNOWN。
2. Linux原developer_plan.json SHA10a3f4cf6aadc00c7394537323af8ab8b6ea80ab670c5dcaf8523e7ed97aca6d及已保存native时钟表：104记录/96来源组/112原窗；实际8双窗记录来自8个来源组。精确二分会改变16请求，其余96记录计划恒等。原尾长0.3–2.134秒，新窗15.15–16.067秒；新右窗保留65个旧尾观测，移除343个，新增447个旧尾之前的上下文观测。8个精确中点均非真实PTS，保持Fraction，不吸附。
3. 新独立验证器用线性Fraction半开归属/divmod采样重算，8记录全部旧/新ordinal SHA与先前bisect计划相等；15项元数据/合成合同PASS，含非零起点、单窗/恰60秒/三窗恒等、中点有无PTS、空窗/非法值/旧缺口拒绝、同组去重、路径限制、诊断不授权训练比赛、完整区间平移和浮点往返反例。主尾区域采样间隔及新旧边界邻帧均保留。

不是解码、RGB、processor、token、真实模型或11strict验收。消费者能否保留有理数边界语义尚NOT_RUN，浮点往返反例仅作为需阻塞的接口风险，不能称实际消费者已失败或通过。没有读取弱答案/测试预测来挑记录；没有媒体像素/100confirm访问，没有新远端写入或launcher。

## 终态和下一步缺口

本工作包所有出口固定NO_426，按已有范围证据耗尽结束，不自动重复参考审计、均分风险包或旧C/B1/D/Q/65CE。旧最佳B37.63及原ZIP86bd5301f6f6771a8451b32063781e214cdd70245ae5513f2a767eaecb9ebe54保持；旧GPU费用/7200offset不改，新GPU任务不存在，不伪造completed回执。独立验证器实测CPU/读字节/峰RSS见cpu_acceptance.json，其余未仪器化开销不写0。

可行动缺口是具体任务参考：完成标注与生成来源、时间或空间目标、query和原生比例、源/时钟映射、完整覆盖及未选语义、用途许可、source_group隔离和本任务曝光史。现在没有成立的新资产，不能把模型缓存或几何合法性充作真值。本轮没有达到“更好提交包”的最终目标，新官网分UNKNOWN。
'''
with (H/'final-decision.md').open('x',encoding='utf-8') as z:z.write(decision)
ledger=read('ledger.json');ledger['pro_status']='COMPLETE_SLOT5_REMAINING3';ledger['pro_reply']={'file':'pro-p01.md','sha256':sha('pro-p01.md'),'bytes':(H/'pro-p01.md').stat().st_size};ledger['sol_r01_correction']={'old_file_preserved':'sol-r01.md','corrected_file':'sol-r01-corrected.md','sha256':sha('sol-r01-corrected.md'),'reason':'stale clipboard original r00; true r01 recaptured from completed visible UI'};ledger['implementation_status']='COMPLETE_BOUNDED_G0_NO_426';ledger['final_decision']={'file':'final-decision.md','sha256':sha('final-decision.md')};ledger['updated_utc']=datetime.now(timezone.utc).isoformat();(H/'ledger.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'status':'ASSEMBLED_ACTUAL_G0_EVIDENCE','plan_rows':len(v['rows']),'tests':len(v['tests']),'new_model_calls':0},ensure_ascii=False))
