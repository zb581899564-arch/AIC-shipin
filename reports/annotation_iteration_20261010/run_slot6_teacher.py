"""A single new fixed-window proposal. Transport changes affect this process only."""
from pathlib import Path
from datetime import datetime, timezone
import json, os, subprocess, sys, hashlib, time
HERE=Path(__file__).resolve().parent/'slot6_silver24_v1'
AGY='C:/Users/33056/AppData/Local/agy/bin/agy.exe'
MODEL='gemini-3.8-flash-high'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):
    with Path(p).open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2)
index=int(sys.argv[1])
folder=Path(json.loads((HERE/'observations/jobs.json').read_text())['jobs'][index])
m=json.loads((folder/'manifest.json').read_text());sv=json.loads((folder/'student_views/receipt.json').read_text())
assert sv['status']=='PASS_ACTUAL_LOCAL_CPU_NATIVE_PROCESSOR_TENSOR_VIEWS' and sv['patch_inverse_exact']
attempt=folder/'teacher_attempt01_http1';attempt.mkdir(exist_ok=False)
out=attempt/'proposal.json'
raw_paths='\n'.join(r['frame_id']+' '+Path(r['path']).as_posix() for r in m['frames'])
effective_paths='\n'.join(r['frame_id']+' '+Path(r['path']).as_posix() for r in sv['frames'][::8])
prompt=f'''用户授权进行视频高光编辑标注。此任务只产生有限观察下完整窗口银标提案，绝非金标，不授予训练资格。
严格白名单：本窗 {(folder/'manifest.json').as_posix()}、{(folder/'student_views/receipt.json').as_posix()}、{(folder/'clip.mp4').as_posix()}、下列64个原始PNG与8个学生有效视图，以及输出 {out.as_posix()}。禁止读旧标签/分数/候选预测/其他来源/盲审记录。禁止terminal/代码/联网/其他模型/子代理。只用view_file与write_to_file；不得修改已有文件。
先读取完整manifest的frames/PTS及实际CPU学生视图回执（各最多4段）；读取一次上述正确clip.mp4，记录工具实际观察范围与不透明内部采样，不能说逐帧全片已看。然后F00..F63按序8批，每批8图，view_file逐项原始PNG共64次；再8个有效视图逐项8次。contact sheet不能替代单图实际供给。全窗原始64帧和实际有效画面另有一位未见你答案的独立盲审者；你不得读取其记录。工具失败应如实记录，不能编造可见事实。
实际学生输入64帧，patch反排后归一化逆转换的显示PNG，tensor SHA另绑定，原始PNG仍是真实native RGB。本地CPU与Linux实际processor文件SHA相同，尚未Linux执行。不要把高分辨可见而有效视图不可辨认的细节假称可学。
任务是query-free短视频高光编辑建议。清楚的主题展示、互动、关键动作/结果、静态但有信息的特写皆可KEEP；运动不是自动KEEP，静态不是自动NO。保留必要准备/结果，不跨无关镜头强并。只描述直接可见事实，不猜音频讲述/隐含动机/身份。一般稀疏采样残余风险写limitations，不把所有间隙机械UNKNOWN；实际识别且会改变选择的动作、边界、语义疑问必须UNKNOWN。未列时间不自动NO。原始事件超过5保留完整事件参考并标不可表达，不合并凑5。
窗口local时间来自manifest，clip时间要加clip_pts_offset_exact。时间是编辑决策提案，不伪装无限精确动作真值。每个KEEP/NO要观察依据，边界内外帧ID及不确定区间。没有足够依据不要用精确小数消除未知。不要求非空、保留比例或NO配额。
输出JSON对象：window_id、source_sha256、clip_sha256、model、native_video_actual_scope、full_native_frames_observed(false)、frame_observations（64条按F00..F63：frame_id/source_ordinal/local_seconds_exact/observed/visible_fact）、effective_view_observations（8条）、events（所有事件：event_id/visible_facts/highlight_reason/evidence_frame_ids/proposed_local_seconds[start,end]/start_uncertainty_range/end_uncertainty_range/boundary_inside_frame_ids/boundary_outside_frame_ids/limitations）、window_coverage（覆盖整个local域的互斥区间，每条start/end/label KEEP或NO或UNKNOWN、visible_basis/evidence_frame_ids；有未决疑问保留U而非凑完整监督）、consequential_unknowns、explicit_no_highlight、student_visibility_limitations、limitations、training_admitted(false)。没有提案不能写空segments冒充成功。只保存到{out.as_posix()}。即使有UNKNOWN也保留完整初稿，不自行重试或补查。末条短答仅确认产物与范围。
64原始PNG：
{raw_paths}
8个实际学生有效视图：
{effective_paths}'''
(attempt/'prompt.txt').write_text(prompt,encoding='utf-8')
save(attempt/'request.json',dict(window_id=m['window_id'],model=MODEL,manifest_sha256=sha(folder/'manifest.json'),
    student_receipt_sha256=sha(folder/'student_views/receipt.json'),prompt_sha256=sha(attempt/'prompt.txt'),
    max_native_video_reads=1,max_original_png_reads=64,max_effective_png_reads=8,max_metadata_segments=8,
    independent_blind_review_not_revealed=True,new_protocol_proposal_number=index+1,
    process_only_proxy='existing localhost:7892',process_only_GODEBUG='http2client=0',global_changes=False))
env=os.environ.copy();env.update(HTTP_PROXY='http://127.0.0.1:7892',HTTPS_PROXY='http://127.0.0.1:7892',GODEBUG='http2client=0')
cmd=[AGY,'--model',MODEL,'--mode','accept-edits','--sandbox','--print-timeout','10m','--output-format','stream-json','--log-file',str(attempt/'agy.log'),'-p',prompt]
started=datetime.now(timezone.utc).isoformat();tic=time.monotonic()
with (attempt/'stream.jsonl').open('xb') as stdout,(attempt/'stderr.txt').open('xb') as stderr:
    p=subprocess.run(cmd,cwd=folder,stdout=stdout,stderr=stderr,env=env)
save(attempt/'terminal.json',dict(started_utc=started,finished_utc=datetime.now(timezone.utc).isoformat(),
    exit_code=p.returncode,elapsed_seconds=time.monotonic()-tic,proposal_exists=out.exists(),
    exit_zero_not_success=True,new_optimizer_updates=0))
print(json.dumps(dict(window=m['window_id'],exit_code=p.returncode,proposal_exists=out.exists(),path=str(attempt))),flush=True)
