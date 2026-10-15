"""Four bounded AGY observation calls, preserving partial and successful work."""
from pathlib import Path
from datetime import datetime,timezone
import json,subprocess,hashlib,traceback
HERE=Path(__file__).resolve().parent/'native_event_pilot_v1'
AGY='C:/Users/33056/AppData/Local/agy/bin/agy.exe'
MODEL='gemini-3.8-flash-high'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):
    with p.open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2)
def main():
    jobs=json.loads((HERE/'jobs.json').read_text())['jobs']
    binding=HERE/'blind_initial_binding.json'
    if not binding.exists():save(binding,dict(utc=datetime.now(timezone.utc).isoformat(),
        files=[dict(path=str(Path(d)/'main_blind_initial.md'),sha256=sha(Path(d)/'main_blind_initial.md')) for d in jobs],
        teacher_calls_before_binding=0,scope='initial independent observations only; no complete silver target qualification'))
    records=[]
    for d in jobs:
        folder=Path(d);out=folder/'teacher_proposal.json';accepted=folder/'teacher_tool_receipt.json'
        if accepted.exists():
            r=json.loads(accepted.read_text());assert sha(out)==r['proposal_sha256'];records.append(r);continue
        assert not out.exists() and not (folder/'stream.jsonl').exists(),'Preserve prior attempt; no automatic replay'
        m=json.loads((folder/'manifest.json').read_text());assert len(m['frames'])==64
        frame_paths='\n'.join(r['frame_id']+' '+Path(r['path']).as_posix() for r in m['frames'])
        prompt=f'''用户已明确授权高光视频标注。这是新四窗可观察性先导的一窗，仅编辑建议，不是训练金标。
只读取本窗manifest.json、clip.mp4以及下面列出的64个原始PNG。禁止读取main_blind_initial、任何旧标签/人类评分/模型预测/其他源文件；禁止terminal、代码、联网、外部API、其他模型、子代理。仅允许view_file读取、write_to_file保存本窗teacher_proposal.json或失败记录。
先view_file读取{(folder/'manifest.json').as_posix()}的全部frames清单、PTS、clip偏移；长文件可分段。再view_file原生读{(folder/'clip.mp4').as_posix()}，记录工具实际可见范围，不能声称逐帧连续播放。再按F00..F63每批8帧view_file直接读取全部64个下面列出的PNG（8批，单图逐项读取，不只读contact sheet），总视频读取1次/原图64次/manifest最多3段；不能以自报读完替代实际工具调用。如某图失败保留未读状态，不编造该图事实。
窗口局部PTS以manifest为准，clip的0还需加clip_pts_offset_exact。标注视觉query-free高光的编辑建议：重要/有趣动作、结果、互动、清楚主题展示、静态但有信息的特写都可能保留；明确冗余/纯过渡可NO；未看清/语义/边界疑问为UNKNOWN。不要求非空，不要求固定保留比例，不强制只大运动，不把字幕/物品存在编成未见动作。不将未提及内容自动当NO。无音频，不能推断说话内容。
输出JSON：window_id、source_sha256、clip_sha256、model、native_video_actual_scope、full_native_frames_observed(false)、student_processor_visibility_verified(false)、frame_observations(64条按序，每条frame_id/source_ordinal/local_seconds_exact/observed/visible_fact；不可见则明确原因)、events(0..5条：event_id/visible_facts/highlight_reason/evidence_frame_ids/proposed_local_seconds/[start_uncertainty_range,end_uncertainty_range]/boundary_evidence_frame_ids/limitations)、window_coverage(KEEP/NO/UNKNOWN区间及具体观察依据；未解决边界可UNKNOWN，不强行填满)、explicit_no_highlight、consequential_unknowns、limitations、training_admitted(false)。
时间提案可粗略，但必须声明边界不确定范围，不伪精确。事件超过5不合并凑数而记不可表达。只提案，不授予最终训练资格；主控独立审查后才考虑。仅写{out.as_posix()}，不能覆盖已存在文件。工具/读取不能完成则写{(folder/'teacher_failure.json').as_posix()}并停止。
64原始PNG清单：
{frame_paths}'''
        (folder/'teacher_prompt.txt').write_text(prompt,encoding='utf-8')
        started=datetime.now(timezone.utc).isoformat()
        cmd=[AGY,'--model',MODEL,'--mode','accept-edits','--sandbox','--print-timeout','10m','--output-format','stream-json','--log-file',str(folder/'agy_teacher.log'),'-p',prompt]
        with (folder/'stream.jsonl').open('xb') as stdout,(folder/'stderr.txt').open('xb') as stderr:
            p=subprocess.run(cmd,cwd=folder,stdout=stdout,stderr=stderr)
        save(folder/'teacher_terminal.json',dict(started_utc=started,finished_utc=datetime.now(timezone.utc).isoformat(),exit_code=p.returncode))
        events=[json.loads(s) for s in (folder/'stream.jsonl').read_text(encoding='utf-8-sig').splitlines() if s.strip()]
        init=next(e['init'] for e in events if e.get('event')=='init');assert init['model']==MODEL
        assert p.returncode==0 and out.exists(),'Actual call did not complete; preserved, no replay'
        result=next(e['result'] for e in reversed(events) if e.get('event')=='result');assert result['status']=='SUCCESS'
        done=[e['step_update'] for e in events if e.get('step_update',{}).get('state')=='DONE' and e['step_update'].get('tool_name')=='view_file']
        supplied=set()
        for c in done:
            value=c.get('tool_info',{}).get('parameters',{}).get('AbsolutePath')
            if value:supplied.add(str(Path(value).resolve()))
        required={str(Path(r['path']).resolve()) for r in m['frames']}
        doc=json.loads(out.read_text(encoding='utf-8-sig'))
        assert doc['window_id']==m['window_id'] and doc['source_sha256']==m['source_sha256'] and doc['clip_sha256']==m['clip_sha256']
        assert [x['frame_id'] for x in doc['frame_observations']]==[x['frame_id'] for x in m['frames']]
        assert doc['training_admitted'] is False
        missing=sorted(required-supplied);video=str(Path(m['clip_path']).resolve()) in supplied
        receipt=dict(status='TEACHER_PROPOSAL_TOOL_DELIVERY_PASS_SEMANTIC_REVIEW_PENDING' if not missing and video else 'INCOMPLETE_EXPLICIT_MEDIA_DELIVERY',
            window_id=m['window_id'],model_actual=init['model'],proposal_sha256=sha(out),stream_sha256=sha(folder/'stream.jsonl'),
            source_frame_pngs_expected=64,source_frame_pngs_done=64-len(missing),missing=missing,native_video_done=video,
            full_native_frames_observed=False,training_admitted=False,conversation_id=result['conversation_id'],
            tool_receipts_not_attention_proof=True)
        save(accepted,receipt);records.append(receipt)
        print(json.dumps(receipt,ensure_ascii=False),flush=True)
        if missing or not video:raise ValueError('Explicit media delivery incomplete; do not expand')
    save(HERE/'teacher_completion.json',dict(status='FOUR_OBSERVATION_PROPOSALS_COMPLETE_NOT_TRAINING_ADMISSION',receipts=records,training_admitted=False))
if __name__=='__main__':
    try:main()
    except Exception:
        p=HERE/'teacher_controller_failure.txt'
        with p.open('x',encoding='utf-8') as f:f.write(traceback.format_exc())
        raise
