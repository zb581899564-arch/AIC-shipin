"""Close the actual bounded experiment, preserving gaps and root-review errors."""
import zipfile
import runner as r

def main():
    student=r.read(r.ROOT/'student_sealed_v2.json')
    initial_sha=r.sha(r.ROOT/'student_sealed.json')
    assert r.read(r.ROOT/'native_admission.json')['student_seal_sha256']==initial_sha
    assert student['supersedes_sha256']==initial_sha
    native=[];audits=[];terminals=[];views=[]
    for path in sorted(r.ROOT.glob('*/audit.json')):
        doc=r.read(path);audits.append(dict(path=str(path.relative_to(r.ROOT)),sha256=r.sha(path),status=doc['status'],errors=doc['errors']))
        for tool in doc['tools']:
            if tool['name']=='view_file':views.append(tool['parameters']['AbsolutePath'])
        if path.parent.name.startswith('native_block_'):native.extend(doc['records'])
    native.sort(key=lambda x:x['frame_id'])
    assert len(native)==32
    native_index,native_index_sha=r.index('native')
    reference={x['frame_id']:x for x in r.read(r.ROOT/'root_native_observed_reference.json')['records']}
    fixes={x['frame_id']:x for x in r.read(r.ROOT/'root_native_subject_decisions.json')['corrections']}
    corrections=[]
    for record in native:
        fid=record['frame_id'];target=reference[fid]
        changes=[]
        if record['subtitle_text']!=target['subtitle_text']:
            changes.append(dict(frame_id=fid,field='subtitle_text',corrected=target['subtitle_text'],reason='Actual individually reopened native PNG subtitle differs from raw AGY answer; retain original'))
            leg='absent' if target['subtitle_text'] is None else 'clear'
            if record['subtitle_legibility']!=leg:
                changes.append(dict(frame_id=fid,field='subtitle_legibility',corrected=leg,reason='Actual subtitle visibility'))
        if fid in fixes:
            changes.append(dict(frame_id=fid,field='visible_subject',corrected=fixes[fid]['corrected'],reason=fixes[fid]['reason']))
        for change in changes:
            record.setdefault('model_original_fields',{})[change['field']]=record[change['field']]
            record[change['field']]=change['corrected']
            record.setdefault('root_corrections',[]).append(change)
        corrections.extend(changes)
    present={x['frame_id'] for x in native}
    missing=[x['frame_id'] for x in native_index['frames'] if x['frame_id'] not in present]
    assert missing==[f'F{i:02}' for i in list(range(16,32))+list(range(48,64))]
    for phase,records in [('student',student['records']),('native',native)]:
        idx,_=r.index(phase);lookup={x['frame_id']:x for x in idx['frames']}
        assert len({x['frame_id'] for x in records})==len(records)
        for row in records:
            ref=lookup[row['frame_id']]
            assert row['source_ordinal']==ref['source_ordinal'] and row['local_seconds_exact']==ref['local_seconds_exact']
            assert row['png_sha256']==ref['png_sha256'] and row['raw_sha256']==r.sha(row['raw_file'])
            assert row['actual_image_read'] is True
    # Guard specifically against reintroducing the four root false positives.
    assert all(x['subtitle_text'] is None for x in student['records'] if x['frame_id'] in {'F11','F30','F49','F50'})
    assert all(x['subtitle_text'] is None for x in native if x['frame_id']=='F11')
    for path in sorted(r.ROOT.glob('*/terminal.json')):
        doc=r.read(path);assert doc['stream_sha256']==r.sha(path.parent/'stream.jsonl')
        terminals.append(dict(path=str(path.relative_to(r.ROOT)),sha256=r.sha(path),**doc))
    assert len(terminals)==10 and sum(t['exit_code']!=0 for t in terminals)==3
    assert all(t['elapsed_seconds']<=420 for t in terminals)
    assert len(views)==96 and len(set(views))==96
    protocol=r.read(r.ROOT/'protocol.json')
    assert protocol['historical_cli_count']==11
    baseline=r.ROOT.parents[2]/'deliveries/ANNOTATION_ITERATION_20261010/SAFE_37_66/candidate_SAFE_37_66.zip'
    expected='07730c9e02e68d1a1ce54e7ef5a8aa616346cf8f2f8d78426ed36bc3eb481496'
    assert r.sha(baseline)==expected and baseline.stat().st_size==306167
    with zipfile.ZipFile(baseline) as z:assert z.testzip() is None and z.namelist()==['predictions.jsonl']
    r.save(r.ROOT/'native_partial_semantic_review.json',dict(utc=r.utc(),accepted_scope='32_ACTUAL_GEMINI_ROWS_MAIN_AGENT_REVIEWED_NOT_FULL_PHASE',
        reviewed_frame_ids=[x['frame_id'] for x in native],missing_frame_ids=missing,corrections=corrections,
        reference_sha256=r.sha(r.ROOT/'root_native_observed_reference.json'),training_admitted=False))
    r.save(r.ROOT/'native_partial_sealed.json',dict(utc=r.utc(),phase='native',records=native,missing_frame_ids=missing,
        complete=False,training_admitted=False,semantic_review_sha256=r.sha(r.ROOT/'native_partial_semantic_review.json')))
    by_student={x['frame_id']:x for x in student['records']}
    diffs=[]
    for b in native:
        a=by_student[b['frame_id']]
        diffs.append(dict(frame_id=b['frame_id'],student_subtitle=a['subtitle_text'],native_subtitle=b['subtitle_text'],
            corrected_subtitles_equal=a['subtitle_text']==b['subtitle_text'],
            student_subject=a['visible_subject'],native_subject=b['visible_subject'],
            wording_difference_is_not_automatically_fact_error=True))
    assert all(x['corrected_subtitles_equal'] for x in diffs)
    r.save(r.ROOT/'native_partial_differences.json',dict(utc=r.utc(),common_frames=32,missing_native_frames=missing,
        student_seal_sha256=r.sha(r.ROOT/'student_sealed_v2.json'),native_partial_seal_sha256=r.sha(r.ROOT/'native_partial_sealed.json'),
        comparisons=diffs))
    completion=dict(utc=r.utc(),status='BOUNDED_STAGE_CLOSED_PARTIAL_NATIVE_EOF_NOT_TRAIN_READY',
        implementation_complete=True,full_annotation_acceptance_pass=False,student_records=64,native_records=32,
        unique_Gemini_png_reads=96,expected_png_reads=128,missing_native_frame_ids=missing,
        new_cli_count=10,successful_cli_count=7,pre_inference_EOF_failures=3,historical_cli_count=11,cumulative_cli_count=21,cumulative_cli_cap=36,
        recovery_count=1,recovery_cap=1,all_cli_within_420_seconds=True,terminals=terminals,audits=audits,
        original_successes_not_repeated=True,old_stop_preserved=True,original_raw_files_preserved=True,
        root_subtitle_false_positive_frames=['F11','F30','F49','F50'],root_erratum_sha256=r.sha(r.ROOT/'ROOT_QA_ERRATUM.json'),
        corrected_student_seal_created_after_native_admission=True,original_student_seal_before_native=True,
        raw_student_subtitle_disagreement_frames_after_corrected_review=[],raw_native_subtitle_disagreement_frames=['F11'],
        student_subject_precision_correction_frames=11,native_semantic_corrections=corrections,
        main_agent_native_images_reviewed=64,main_reference_not_substituted_for_Gemini_outputs=True,
        native_video_delivered=False,old_silver_contract_pass=False,training_admitted=False,
        new_optimizer_updates=0,new_426_calls=0,new_gpu_jobs=0,pro_used=6,pro_cap=8,cash_cost='UNKNOWN_NOT_ZERO',
        baseline_zip=dict(path=str(baseline),bytes=306167,sha256=expected,crc_ok=True),
        current_student_facts='student_sealed_v2.json',current_native_facts='native_partial_sealed.json',
        output_sha256s={p:r.sha(r.ROOT/p) for p in ['student_sealed_v2.json','native_partial_sealed.json','ROOT_QA_ERRATUM.json']})
    r.save(r.ROOT/'completion.json',completion)
    report='''# W01 四图标注实际结果

当前终态：BOUNDED_STAGE_CLOSED_PARTIAL_NATIVE_EOF_NOT_TRAIN_READY。程序和验收流程已实现并实际执行；全量标注未通过。

- 学生视图：Gemini 实际读图并输出64/64条，当前有效复核版为 student_sealed_v2.json。
- 原图：Gemini 实际完成32/64条；缺 F16—F31、F48—F63。native_partial_sealed.json 显式保留缺口，未造空标签。主控看过原图64张的参考记录不冒充Gemini输出。
- 实际10次CLI，7次完成、3次在推理前Google资格检查EOF失败；唯一恢复用于学生最后16图并成功，不重复已成功读图。本阶段96次唯一Gemini PNG读取，历史11次继续累计为21/36；当前阶段10次上限用完。
- 每四图先落盘、每会话最多16图、源身份由程序绑定，实际成功输出通过结构和公共读取记录检查。六个正反例验收器测试通过。

## 质量与纠错

F37四图回归及原图F37均正确识别人物与字幕，切到F38狗镜头没有串位。学生64帧字幕与纠正后的主控观察一致；这是已曝光单窗诊断，不能作为总体准确率。

主控初次拼图复核把邻帧字幕错误延续到F11/F30/F49/F50，误称四处漏标并写入初版复核。逐张重开后确认这四图确实无字幕，Gemini学生原答正确。ROOT_QA_ERRATUM.json撤销四处误改；错误初版、原封存、原native准入绑定全部保留，当前学生事实使用v2。纠正后的语义封存发生在原图准入之后，不能冒称原科学封存顺序完全通过。

学生侧11帧收紧站姿、动作或持续性表述，原答保留。原图F11的Gemini原答确实多写不存在的“Abrazarte.”，已根据单图删去并记录原值。四图方法仍需逐图复核，不能无人验收扩量。

## 后续入口与边界

本阶段不得重开已成功CLI或补写完成状态。先解决AGY资格检查EOF与剩余原图准入，再单独建立高光取舍目标；事实覆盖不等于高光。未生成KEEP/NO、事件边界或裁剪框，不满足旧银标合同，不能开训。

原37.66包306167字节、SHA及CRC再核通过，权重不变。新增GPU训练、optimizer更新、426推理、下载、上传、公开发布、官网提交均0；没有新提交ZIP或新成绩。Pro保持6/8，现金费用UNKNOWN非0。
'''
    with (r.ROOT/'RESULT.md').open('x',encoding='utf-8') as f:f.write(report)
    print(completion['status'], 'student=64 native=32 CLI=10 unique_Gemini_PNG=96')

if __name__=='__main__':main()
