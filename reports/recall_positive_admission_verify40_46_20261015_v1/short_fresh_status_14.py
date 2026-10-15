"""One bounded first-confirmation snapshot; no launcher or quality recomputation."""
import datetime as dt
import json
from pathlib import Path
import socket
import subprocess

MAIN = Path('/home/inspur/aic_video_work/recall_positive_admission_verify40_46_20261015_v1')
ROOT = MAIN/'fresh_01'
assert socket.gethostname() == 'inspur-NP5570M5'
out=dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(),host=socket.gethostname(),processes=[],stages={})
for p in Path('/proc').iterdir():
    if not p.name.isdigit():continue
    try:
        cmd=(p/'cmdline').read_bytes().replace(b'\0',b' ').decode(errors='replace')
        if str(MAIN) not in cmd:continue
        stat=(p/'stat').read_text().rsplit(')',1)[1].split()
        out['processes'].append(dict(pid=int(p.name),ppid=int(stat[1]),state=stat[0],start_ticks=stat[19],argv=cmd,io=(p/'io').read_text()))
    except (FileNotFoundError,PermissionError,ProcessLookupError):pass
for rel in ['reference_01','confirm/chain_01','confirm/chain_02','confirm/inputs_01','confirm/B0/input_qa_01','confirm/B0/gpu_01',
            'confirm/B0/replay_01','confirm/VERIFY/cpu_01','confirm/VERIFY/input_qa_01','confirm/VERIFY/gpu_01','confirm/VERIFY/replay_01']:
    p=ROOT/rel
    if not p.exists():continue
    data={}
    for name in ['completion.json','failure.json']:
        f=p/name
        if f.is_file():
            v=json.loads(f.read_text());data[name]={k:v[k] for k in ['status','stage','utc','calls','expected_input_count','actual_input_count','error','actual_new_media_payload_bytes'] if k in v}
            if name=='failure.json':data[name]['traceback_tail']=v.get('traceback','')[-2500:]
    if rel=='reference_01':
        data['accepted_sources']=len(list(p.glob('accepted_slot_*.json')))
        data['media_receipts']=len(list(p.glob('*/media_receipt.json')))
        data['native_clock_files']=len(list(p.glob('*/clock.json')))
        data['native_rejections']=len(list(p.glob('*/source_rejection.json')))
    if (p/'attempts.jsonl').is_file():
        rows=[json.loads(x) for x in (p/'attempts.jsonl').read_text().splitlines() if x.strip()]
        data['BEGIN']=sum(x.get('event')=='BEGIN' for x in rows);data['ACCEPTED']=sum(x.get('event')=='ACCEPTED' for x in rows)
    if rel=='confirm/B0/input_qa_01':
        data['first_actual_encode_evidence']=len(list(p.glob('*.encode_evidence.json')))
        data['accepted_first_QA']=len(list(p.glob('*.accepted_input.json')))
    data['direct_json_files']=len(list(p.glob('*.json')));data['child_directories']=sum(x.is_dir() for x in p.iterdir())
    out['stages'][rel]=data
for rel in ['confirm/POSITIVE/cpu_01','confirm/POSITIVE/input_qa_01','confirm/POSITIVE/gpu_01','confirm/POSITIVE/output_qa_01','confirm/comparison_01']:
    p=MAIN/rel
    if not p.exists():continue
    data={}
    for name in ['completion.json','failure.json','result.json']:
        f=p/name
        if f.is_file():
            v=json.loads(f.read_text());data[name]={k:v[k] for k in ['status','stage','utc','calls','expected_input_count','error','conditions','macro'] if k in v}
            if name=='failure.json':data[name]['traceback_tail']=v.get('traceback','')[-2500:]
    if (p/'attempts.jsonl').is_file():
        rows=[json.loads(x) for x in (p/'attempts.jsonl').read_text().splitlines() if x.strip()]
        data['BEGIN']=sum(x.get('event')=='BEGIN' for x in rows);data['ACCEPTED']=sum(x.get('event')=='ACCEPTED' for x in rows)
    data['direct_json_files']=len(list(p.glob('*.json')));data['child_directories']=sum(x.is_dir() for x in p.iterdir())
    out['stages']['MAIN/'+rel]=data
out['gpu']=subprocess.run(['nvidia-smi','--query-gpu=index,memory.used,utilization.gpu','--format=csv,noheader,nounits'],capture_output=True,text=True,check=True).stdout
print(json.dumps(out,ensure_ascii=False))
