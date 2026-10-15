"""Supplement only the missing video; three new windows with corrected media paths."""
from pathlib import Path
import json, os, subprocess, hashlib
from datetime import datetime, timezone

HERE=Path(__file__).resolve().parent
ROOT=HERE/'native_event_pilot_v1'
AGY='C:/Users/33056/AppData/Local/agy/bin/agy.exe'
MODEL='gemini-3.8-flash-high'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,obj):
    with p.open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2)
def invoke(folder,prompt):
    assert not folder.exists(), 'Preserve existing attempt; never repeat'
    folder.mkdir()
    (folder/'prompt.txt').write_text(prompt,encoding='utf-8')
    env=os.environ.copy();env['HTTP_PROXY']=env['HTTPS_PROXY']='http://127.0.0.1:7892'
    started=datetime.now(timezone.utc).isoformat()
    cmd=[AGY,'--model',MODEL,'--mode','accept-edits','--sandbox','--print-timeout','10m','--output-format','stream-json','--log-file',str(folder/'agy.log'),'-p',prompt]
    with (folder/'stream.jsonl').open('xb') as out,(folder/'stderr.txt').open('xb') as err:
        proc=subprocess.run(cmd,cwd=folder,env=env,stdout=out,stderr=err)
    events=[json.loads(x) for x in (folder/'stream.jsonl').read_text(encoding='utf-8-sig').splitlines() if x.strip()]
    result=next((x['result'] for x in reversed(events) if x.get('event')=='result'),None)
    save(folder/'terminal.json',dict(started_utc=started,finished_utc=datetime.now(timezone.utc).isoformat(),exit_code=proc.returncode,result=result,stream_sha256=sha(folder/'stream.jsonl')))
    print(json.dumps(dict(folder=str(folder),exit_code=proc.returncode,status=result and result.get('status')),ensure_ascii=False),flush=True)

if __name__=='__main__':
    jobs=[Path(x) for x in json.loads((ROOT/'jobs.json').read_text())['jobs']]
    media=jobs[0]; dest=media/'video_supplement_v3';output=dest/'video_observation.json'
    invoke(dest,f'''仅补充读取之前路径错误导致未见的视频。不得重复64原图观察/读取main_blind_initial或其他标签。用户已授权视频标注。
只允许view_file读取真实存在的 {media.as_posix()}/clip.mp4 一次及 {media.as_posix()}/manifest.json（最多3段），write_to_file保存 {output.as_posix()}。
禁止终端、代码、网络、API、子代理、其它模型。输出工具实际视频可见范围/时间映射/所见事实/工具限制，若工具不支持则明确写不能读取；不能仅从manifest推演内容。full_native_frames_observed=false、training_admitted=false。不读取旧提案，不作最终标签。''')
    template=(HERE/'run_native_event_pilot.py').read_text(encoding='utf-8')
    # Reuse the exact original scientific instructions, correcting only output isolation.
    for media in jobs[1:]:
        dest=media/'attempt03_correct_path';m=json.loads((media/'manifest.json').read_text())
        paths='\n'.join(r['frame_id']+' '+Path(r['path']).as_posix() for r in m['frames'])
        prompt=f'''用户已授权视频高光标注。只读取本窗 {media.as_posix()}/manifest.json 全部64帧清单/PTS/clip偏移（最多3段）、真实视频 {media.as_posix()}/clip.mp4（1次）和下列64张原始PNG（按序逐项8批，不能只看overview）。禁止读取main_blind_initial、任何旧标签/评分/预测/其他文件。禁止终端、代码、网络、API、其他模型或子代理。仅允许view_file与write_to_file。
无音频不能推断说话内容；静态但有信息的展示/特写可保留；明确冗余过渡可NO，具体未清疑问UNKNOWN。不要求非空、比例或固定事件数。不将品种/物品存在编造成动作，不以未提及自动判NO。
写 {dest.as_posix()}/teacher_proposal.json：window_id/source_sha256/clip_sha256/model/native_video_actual_scope/full_native_frames_observed(false)/student_processor_visibility_verified(false)/training_admitted(false)；frame_observations64条(frame_id/source_ordinal/local_seconds_exact/observed/visible_fact)；events0..5条(event_id/visible_facts/highlight_reason/evidence_frame_ids/proposed_local_seconds/start_uncertainty_range/end_uncertainty_range/boundary_evidence_frame_ids/limitations)；window_coverage分KEEP/NO/UNKNOWN含依据；explicit_no_highlight/consequential_unknowns/limitations。clip0需加manifest.clip_pts_offset_exact；粗边界须保留不确定范围。候选超过5条不强行跨镜头合并。只是提案不授予训练资格。工具读取失败仍如实记录，不能声称连续逐帧已见。
64原图：
{paths}'''
        invoke(dest,prompt)
