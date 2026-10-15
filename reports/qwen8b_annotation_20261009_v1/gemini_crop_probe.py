"""Bounded native-image crop annotation probe, separate from temporal and Doubao output."""
from pathlib import Path
from datetime import datetime,timezone
import json,subprocess,hashlib,sys,time
from spatial_prepare import ROOT,load,sha,save,validate
AGY=Path('C:/Users/33056/AppData/Local/agy/bin/agy.exe')
MODEL='gemini-3.8-flash-high'
def accept(sid,job,model=MODEL):
    manifest,doc,rows=validate(sid,job/'draft_01.json')
    es=[json.loads(s) for s in (job/'stream.jsonl').read_text(encoding='utf-8-sig').splitlines() if s.strip()]
    init=next(e['init'] for e in es if e.get('event')=='init')
    final=next(e['result'] for e in reversed(es) if e.get('event')=='result')
    assert init['model']==model and final['status']=='SUCCESS' and load(job/'cli_terminal.json')['exit_code']==0
    observed=set()
    calls=[]
    for e in es:
        s=e.get('step_update',{})
        if s.get('state')!='DONE' or s.get('tool_name') not in ('view_file','view_image'):continue
        p=s.get('tool_info',{}).get('parameters',{})
        for v in p.values():
            if isinstance(v,str):
                for f in manifest['frames']:
                    if v.replace('\\','/').endswith('/input/'+sid+'/'+f['file']):
                        observed.add(f['file']);calls.append(dict(tool=s['tool_name'],path=v))
    assert observed=={f['file'] for f in manifest['frames']},f'Actual image tool calls missing: {observed}'
    receipt=dict(status='PASS_IMAGE_TOOL_CALLS_FRAME_IDENTITY_AND_GEOMETRY',source_id=sid,model=model,frames=12,ratio_targets=24,
        crop_count=sum(r['state']=='CROP' for r in rows),unknown_count=sum(r['state']=='UNKNOWN' for r in rows),
        raw_sha256=sha(job/'draft_01.json'),stream_sha256=sha(job/'stream.jsonl'),media_sha256=manifest['media_sha256'],
        image_tool_calls=calls,duration_seconds=final.get('duration_seconds'),usage=final.get('usage'),
        actual_crops_visually_reviewed=False,utc=datetime.now(timezone.utc).isoformat())
    save(job/'acceptance.json',receipt);return receipt
def prompt(sid,job):
    dest=ROOT/'input'/sid
    return f'''为Qwen8B标注视频构图，只处理源{sid}的12张原始PNG，不标高光。
先原生view_file读取{(dest/'manifest.json').as_posix()}，然后实际逐张用原生图像工具view_file或view_image查看其中frames列出的12张PNG。文件名、帧号、PTS、原图尺寸照manifest，不读MP4、豆包/其他教师结果、人类评分或其它源。不调用终端/脚本/代码、浏览器、联网、外部API或子代理，不训练。
给每帧16:9和9:16的裁剪框，坐标是原图整数像素。尽量保留主角完整头脸、当前关键动作及手中的操作物体；无法同时保留核心内容就UNKNOWN，不编造不存在的合法裁框。群像可选择一位主角，但理由说明舍弃内容。主角左右位置必须根据实际像素识别，不能默认居中。原图内容固有裁断与新增裁断分别如实判断。
box_xyw使用[x,y,w,h]，h=w*ratioH/ratioW必须为整数（16:9的w为16倍数，9:16的w为9倍数），x>=0,y>=0,x+w<=sourceWidth,y+h<=sourceHeight。宽度尽量保留足够上下文，别缩小框导致更严重截断。
只用write_to_file写新文件{(job/'draft_01.json').as_posix()}，不覆盖。
JSON顶层source_id、annotator_ui="gemini-3.8-flash-high-cli"、observed_files（真实查看成功的12文件名）、frames。
每帧sample_index、frame_index、pts_seconds、observed_file、visible_content（实际可见内容短句）、focus_bounds_xyxy（核心主体估计边界或null）和crops两条。每框targetRatioWH[16,9]/[9,16]、state CROP/UNKNOWN、box_xyw（UNKNOWN为null）、reason（简短明确主要保留/舍弃内容）。只写实际看过帧，读失败写{(job/'failure.json').as_posix()}并停止，不能猜。
写完回读校验12帧24比例，聊天只简报数量。不要在未看到实际裁图前声称视觉质量验收通过。'''
def run(sid,model=MODEL,attempt='attempt_01',concise=False):
    job=ROOT/'raw/gemini_crop'/sid/attempt;job.mkdir(parents=True,exist_ok=True)
    if (job/'acceptance.json').exists():return load(job/'acceptance.json')
    if any(job.iterdir()):raise RuntimeError('Partial job preserved; needs separate recovery attempt')
    task=prompt(sid,job).replace('gemini-3.8-flash-high-cli',model+'-cli')
    if concise:task+='\n为减少延迟，visible_content和reason每条各不超过15个中文字。无需输出长篇分析，先实际看完12张图，然后一次写紧凑JSON。'
    (job/'prompt.txt').write_text(task,encoding='utf-8')
    started=datetime.now(timezone.utc).isoformat();before=time.perf_counter()
    cmd=[str(AGY),'--model',model,'--mode','accept-edits','--sandbox','--output-format','stream-json','--log-file',str(job/'agy.log'),'-p',task]
    with (job/'stream.jsonl').open('wb') as out,(job/'stderr.txt').open('wb') as err:
        p=subprocess.run(cmd,cwd=ROOT,stdout=out,stderr=err,check=False)
    save(job/'cli_terminal.json',dict(exit_code=p.returncode,started_utc=started,finished_utc=datetime.now(timezone.utc).isoformat(),wall_seconds=time.perf_counter()-before))
    receipt=accept(sid,job,model);print(json.dumps(receipt,ensure_ascii=False),flush=True);return receipt
if __name__=='__main__':
    if '--low' in sys.argv:
        for sid in [s for s in sys.argv[1:] if s!='--low'] or ['PJrm840pAUI']:run(sid,'gemini-3.8-flash-low','attempt_low_01',True)
    else:
        for sid in sys.argv[1:] or ['PJrm840pAUI']:run(sid)
