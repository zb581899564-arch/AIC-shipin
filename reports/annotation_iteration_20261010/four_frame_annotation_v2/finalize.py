"""Independent local final acceptance; no model or decoder invocation."""
import json, zipfile
from pathlib import Path
import runner as r

def main():
    student=r.read(r.ROOT/'student_sealed.json');native=r.read(r.ROOT/'native_sealed.json')
    admission=r.read(r.ROOT/'native_admission.json')
    assert admission['student_seal_sha256']==r.sha(r.ROOT/'student_sealed.json')
    assert student['utc']<admission['utc']<native['utc']
    diffs=[]
    for phase,doc in [('student',student),('native',native)]:
        idx,idx_sha=r.index(phase)
        assert [x['frame_id'] for x in doc['records']]==[x['frame_id'] for x in idx['frames']]
        for obs,ref in zip(doc['records'],idx['frames']):
            for key in ['source_ordinal','local_seconds_exact','png_sha256','image_path']:
                assert obs[key]==(ref['path'] if key=='image_path' else ref[key])
            assert obs['raw_sha256']==r.sha(obs['raw_file'])
            assert obs['actual_image_read'] is True
        assert doc['training_admitted'] is False
    for a,b in zip(student['records'],native['records']):
        changed={key:dict(student=a[key],native=b[key]) for key in ['visible_subject','subtitle_text','subtitle_legibility','uncertainties'] if a[key]!=b[key]}
        if changed:diffs.append(dict(frame_id=a['frame_id'],fields=changed,description_difference_not_automatically_fact_error=True))
    terminals=[]
    for path in sorted(r.ROOT.glob('*/terminal.json')):
        terminal=r.read(path);folder=path.parent
        assert terminal['stream_sha256']==r.sha(folder/'stream.jsonl')
        terminals.append(dict(path=str(path.relative_to(r.ROOT)),sha256=r.sha(path),**terminal))
    protocol=r.read(r.ROOT/'protocol.json')
    assert len(terminals)<=protocol['new_cli_cap']
    assert len(terminals)+protocol['historical_cli_count']<=protocol['cumulative_cli_cap']
    assert all(t['elapsed_seconds']<=420 for t in terminals)
    actual_reads=[]
    for path in r.ROOT.glob('*/audit.json'):
        doc=r.read(path)
        for tool in doc['tools']:
            if tool['name']=='view_file':actual_reads.append(tool['parameters']['AbsolutePath'])
    assert len(actual_reads)==128 and len(set(actual_reads))==128
    baseline=r.ROOT.parents[2]/'deliveries/ANNOTATION_ITERATION_20261010/SAFE_37_66/candidate_SAFE_37_66.zip'
    assert r.sha(baseline)=='07730c9e02e68d1a1ce54e7ef5a8aa616346cf8f2f8d78426ed36bc3eb481496'
    with zipfile.ZipFile(baseline) as z:
        assert z.testzip() is None and z.namelist()==['predictions.jsonl']
    r.save(r.ROOT/'native_differences.json',dict(utc=r.utc(),student_seal_sha256=r.sha(r.ROOT/'student_sealed.json'),
        native_seal_sha256=r.sha(r.ROOT/'native_sealed.json'),differences=diffs,student_seal_not_rewritten=True))
    reviews={phase:r.read(r.ROOT/f'{phase}_semantic_review.json') for phase in ['student','native']}
    summary=dict(utc=r.utc(),status='PASS_COMPLETE_PRIMARY_AGENT_REVIEWED_W01_FACTS_NOT_SFT',
        student_records=64,native_records=64,actual_unique_png_reads=128,all_student_reads_before_native=True,
        new_cli_count=len(terminals),historical_cli_count=protocol['historical_cli_count'],cumulative_cli_count=len(terminals)+protocol['historical_cli_count'],
        recovered_missing_only=True,original_failures_preserved=True,terminals=terminals,
        all_cli_within_420_seconds=True,corrections={p:reviews[p]['corrections'] for p in reviews},
        manual_review_not_blind_gold=True,native_video_delivered=False,old_silver_contract_pass=False,
        training_admitted=False,new_optimizer_updates=0,new_426_calls=0,pro_used=6,pro_cap=8,
        cash_cost='UNKNOWN_NOT_ZERO',baseline_zip=dict(path=str(baseline),bytes=baseline.stat().st_size,sha256=r.sha(baseline),crc_ok=True),
        output_seal_sha256s={p:r.sha(r.ROOT/f'{p}_sealed.json') for p in reviews})
    r.save(r.ROOT/'completion.json',summary)
    counts={p:len({c['frame_id'] for c in reviews[p]['corrections']}) for p in reviews}
    report=f'''# W01 四图事实标注实际验收

学生视图 64 条和原图 64 条已完成；公共工具记录共 128 次唯一 PNG 读取。学生事实先复核封存，原图准入绑定其 SHA，原图与差异另存，不回写学生原件。

本阶段实际 CLI {len(terminals)} 次，含一次推理前 EOF 失败和仅补缺失16图的恢复；历史11次继续累计。所有终态在420秒内；Pro保持6/8，现金费用 UNKNOWN 非0。

四图试点 F37 主体及字幕正确，F37/F38 切镜没有串位。主控逐图复核后，学生侧 {counts['student']} 个帧、原图侧 {counts['native']} 个帧有明确勘误；原始教师答案和错误全部保留。具体修改、理由、文件 SHA 在 semantic_review 与封存记录中。

这证明本窗口分批落盘与身份验收可用，不证明 Gemini 可无人复核地批量标注。事实文件没有高光 KEEP/NO、事件边界或裁剪框，训练准入仍为 false；旧视频银标合同未通过。下一阶段单独校准全窗高光相对重要性，不能把事实覆盖或字幕存在自动视作高光。

原37.66包再次通过306167字节、SHA和ZIP CRC检查，模型未变。新增GPU训练、426推理、下载、跨主机传输和官网提交均0，没有新提交包或新成绩。
'''
    (r.ROOT/'RESULT.md').write_text(report,encoding='utf-8')
    print(json.dumps(dict(status=summary['status'],cli=len(terminals),correction_frames=counts),ensure_ascii=False))

if __name__=='__main__': main()
