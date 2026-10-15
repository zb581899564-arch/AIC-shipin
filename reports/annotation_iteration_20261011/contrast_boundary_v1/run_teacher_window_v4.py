"""One fresh, bounded AGY sheet annotation; preserves original bytes and terminal cost."""
import argparse, datetime, hashlib, json, os, subprocess, time
from pathlib import Path

ROOT=Path(__file__).resolve().parent
AGY=Path(r'C:\Users\33056\AppData\Local\agy\bin\agy.exe')
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):
    with Path(p).open('x',encoding='utf-8') as f: json.dump(x,f,ensure_ascii=False,indent=2)
def now(): return datetime.datetime.now(datetime.timezone.utc).isoformat()

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--index',type=int,required=True);ap.add_argument('--attempt',type=int,required=True);args=ap.parse_args();assert args.index in (0,1,4) and args.attempt in (1,2)
    obs=ROOT/'observations'/f'{args.index:03d}'
    manifest=json.loads((obs/'contact_sheet_manifest.json').read_text(encoding='utf-8'))
    blind=json.loads((obs/'blind_initial.json').read_text(encoding='utf-8'))
    assert blind['blind_attestation']=={'teacher_content_received':False,'candidate_prediction_received':False}
    assert blind['independent_semantic_review_complete'] is True
    assert blind['window_id']==manifest['window_id'] and blind['source_sha256']==manifest['source_sha256']
    authorization=json.loads((ROOT/'user_authorization_v1.json').read_text(encoding='utf-8'))
    calls=ROOT/'teacher_calls';calls.mkdir(exist_ok=True)
    existing=list(calls.glob('*/launch.json'));probe=json.loads((ROOT/'agy_diagnostics/text_probe_v1/terminal.json').read_text(encoding='utf-8'));assert probe['status']=='PASS_ACTUAL_NEW_TEXT_CONNECTIVITY_PROBE_NOT_ANNOTATION';prior_probe_calls=1;assert len(existing)+prior_probe_calls<authorization['teacher_new_call_budget']
    assert all((p.parent/'terminal.json').exists() for p in existing),'unfinished prior call; no concurrent/retry hidden calls'
    out=calls/f'{args.index:03d}_attempt_{args.attempt:02d}';out.mkdir(exist_ok=False)
    ranges={'type':'array','items':{'type':'array','minItems':2,'maxItems':2,'items':{'type':'string'}}}
    schema={'type':'object','required':['window_id','source_sha256','frame_facts','keep_local_exact','no_local_exact','unknown_local_exact','events','boundaries','explicit_no_highlight','limitations'],
      'properties':{'window_id':{'type':'string'},'source_sha256':{'type':'string'},'frame_facts':{'type':'array','minItems':64,'maxItems':64,'items':{'type':'object','required':['frame_id','visible_fact'],'properties':{'frame_id':{'type':'string'},'visible_fact':{'type':'string'}}}},
        'keep_local_exact':ranges,'no_local_exact':ranges,'unknown_local_exact':ranges,'events':{'type':'array','maxItems':5,'items':{'type':'object','required':['event_id','local','visible_reason'],'properties':{'event_id':{'type':'string'},'local':ranges['items'],'visible_reason':{'type':'string'}}}},
        'boundaries':{'type':'array','items':{'type':'object','required':['event_id','side','local_exact','uncertainty_local_exact','inside_frame_id','outside_frame_id_or_domain','reason'],'properties':{'event_id':{'type':'string'},'side':{'enum':['start','end']},'local_exact':{'type':'string'},'uncertainty_local_exact':ranges['items'],'inside_frame_id':{'type':'string'},'outside_frame_id_or_domain':{'type':'string'},'reason':{'type':'string'}}}},
        'explicit_no_highlight':{'type':'boolean'},'limitations':{'type':'array','items':{'type':'string'}}}}
    save(out/'schema.json',schema)
    sheets=[r['image']['path'] for r in manifest['sheets']]
    for row in manifest['sheets']:assert sha(row['image']['path'])==row['image']['sha256']
    frames=[{k:r[k] for k in ('frame_id','ordinal','pts_exact','local_seconds_exact')} for r in manifest['frames']]
    prompt='''你是视频高光片段标注员。本任务仅标注一个窗口，不修改或运行训练。必须用 view_file 图像工具逐一实际打开下列8张PNG联系表（每张8帧，原始RGB未缩放），共64个原生采样帧。不得用read_file/终端文本代替看图，不读取任何其他目录、旧标注、主控初稿、模型预测、论文或成绩。不要调用终端，不创建文件。8次图像工具完成后直接返回符合JSON schema的完整JSON，不要ACK，不使用markdown。若看不到某张图或图片工具失败，诚实说明并把受影响范围UNKNOWN；禁止虚构读取成功。
高光标准：独立有价值的可见动作、关键变化、技法展示及明确结果，保留必要准备和完成，不把普通持续讲话、重复姿势、logo、无动作过渡当高光。不要强行每窗选高光：纯普通窗可以keep=[]、no全域。禁止为了凑负样本削短动作；禁止把所有动作/普通宠物抚摸均判高光。没有声音，不能编造台词、因果、身份或意图。不能用官方importance分数推导标签。本任务是有限64帧建议，不声称观看完整视频。
时间全部用下面明确的local_seconds_exact（字符串整数或分数秒），不是帧号、截图排布序号或绝对时间。域为[0,D)，KEEP/NO/UNKNOWN必须非重叠完整覆盖整个域。边界不确定、隐藏动作、需要音频判断则UNKNOWN，禁止把UNKNOWN当NO；explicit_no_highlight仅完整纯NO可true。最多5个彼此独立事件，事件local区间并集必须恰好KEEP。每个KEEP起止必须单独边界，引用边界内外实际Fxx图像和<=1/2秒不确定括号（包含边界），不要用不存在的帧。全域NO也要逐帧事实和原因支持。每个F00..F63写短而具体可见事实，不能统一填'同前'。事实与边界必须服从实际图片。
'''+json.dumps({'window_id':manifest['window_id'],'source_sha256':manifest['source_sha256'],'D':manifest['domain_local_seconds_exact'][1],'images_in_order':sheets,'frame_time_map':frames},ensure_ascii=False)
    (out/'prompt.txt').write_text(prompt,encoding='utf-8')
    cmd=[str(AGY),'--model','gemini-3.8-flash-high','--mode','accept-edits','--sandbox','--print-timeout','20m','--output-format','stream-json','--json-schema',str(out/'schema.json'),'--log-file',str(out/'agy.log'),'-p',prompt]
    started=now();start=time.monotonic();status='FAILED';exit_code=None;timed_out=False
    with (out/'stdout.jsonl').open('xb') as stdout,(out/'stderr.log').open('xb') as stderr:
      process=subprocess.Popen(cmd,cwd=obs,stdout=stdout,stderr=stderr,creationflags=subprocess.CREATE_NEW_PROCESS_GROUP|subprocess.CREATE_NO_WINDOW)
      save(out/'launch.json',{'status':'ACTUAL_NEW_TEACHER_CALL_STARTED','started_utc':started,'pid':process.pid,'model':'gemini-3.8-flash-high','window_id':manifest['window_id'],'new_experiment_call_ordinal':len(existing)+prior_probe_calls+1,'prior_text_probe_calls':prior_probe_calls,'explicit_attempt_after_successful_text_probe':args.attempt,'prior_closed_project_teacher_calls':40,'prompt_sha256':sha(out/'prompt.txt'),'schema_sha256':sha(out/'schema.json'),'blind_initial_sha256':sha(obs/'blind_initial.json'),'teacher_cash':'UNKNOWN_NOT_ZERO'})
      try:exit_code=process.wait(timeout=authorization['teacher_per_call_seconds']+30)
      except subprocess.TimeoutExpired:
        timed_out=True;subprocess.run(['taskkill','/PID',str(process.pid),'/T','/F'],stdout=stderr,stderr=stderr,check=False);exit_code=process.wait(timeout=20)
    events=[];issues=[];result=None;observed={}
    for line in (out/'stdout.jsonl').read_text(encoding='utf-8-sig').splitlines():
      try: event=json.loads(line)
      except json.JSONDecodeError:issues.append('NON_JSON_STDOUT');continue
      events.append(event)
      if event.get('event')=='result':result=event.get('result')
    save(out/'terminal.json',{'status':'TIMEOUT' if timed_out else 'EXIT_RECORDED','started_utc':started,'finished_utc':now(),'wall_seconds':time.monotonic()-start,'exit_code':exit_code,'timed_out':timed_out,'stdout_sha256':sha(out/'stdout.jsonl'),'stderr_sha256':sha(out/'stderr.log'),'teacher_cash':'UNKNOWN_NOT_ZERO','result_status':result.get('status') if isinstance(result,dict) else None,'usage':result.get('usage') if isinstance(result,dict) else None,'new_optimizer_updates':0})
    if exit_code!=0 or not isinstance(result,dict) or result.get('status')!='SUCCESS' or issues:
      save(out/'failure.json',{'status':'STOP_TEACHER_ORIGINAL_STREAM_OR_RESULT','issues':issues,'result_status':result.get('status') if isinstance(result,dict) else None});raise RuntimeError('Teacher failed; original bytes/terminal retained; no automatic retry')
    response=result.get('response');proposal=json.loads(response) if isinstance(response,str) else response
    assert isinstance(proposal,dict) and proposal['window_id']==manifest['window_id'] and proposal['source_sha256']==manifest['source_sha256']
    assert [r['frame_id'] for r in proposal['frame_facts']]==[f'F{i:02d}' for i in range(64)]
    save(out/'proposal.json',proposal)
    print(json.dumps({'status':'ACTUAL_TEACHER_RESULT_PRESERVED_NOT_YET_IMAGE_AUDITED_OR_ADMITTED','index':args.index,'window_id':manifest['window_id'],'original_stream_sha256':sha(out/'stdout.jsonl'),'proposal_sha256':sha(out/'proposal.json')}),flush=True)

if __name__=='__main__':main()
