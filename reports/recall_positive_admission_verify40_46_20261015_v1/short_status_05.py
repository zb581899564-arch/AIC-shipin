"""One bounded read-only status; run this source with existing SSH python3 stdin."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import socket
import subprocess

ROOT = Path('/home/inspur/aic_video_work/recall_positive_admission_verify40_46_20261015_v1')
HOME = ROOT.parent
RUN = HOME/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
JOB = 'recall_positive_novelparts_dev10_20261015_v1'
assert socket.gethostname() == 'inspur-NP5570M5'
out = dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(), host=socket.gethostname(), processes=[], stages={})
for p in Path('/proc').iterdir():
    if not p.name.isdigit():
        continue
    try:
        cmd = (p/'cmdline').read_bytes().replace(b'\0', b' ').decode(errors='replace')
        if str(ROOT) not in cmd:
            continue
        stat = (p/'stat').read_text().rsplit(')', 1)[1].split()
        out['processes'].append(dict(pid=int(p.name), ppid=int(stat[1]), state=stat[0], start_ticks=stat[19],
                                    argv=cmd, io=(p/'io').read_text()))
    except (FileNotFoundError, PermissionError, ProcessLookupError):
        pass
for rel in ['dev/chain_01', 'dev/POSITIVE/cpu_01', 'dev/POSITIVE/input_qa_01',
            'dev/POSITIVE/gpu_01', 'dev/POSITIVE/output_qa_01', 'dev/comparison_01']:
    p = ROOT/rel
    if not p.exists():
        continue
    data = {}
    for name in ['started.json', 'completion.json', 'failure.json', 'result.json']:
        f = p/name
        if f.is_file():
            v = json.loads(f.read_text())
            data[name] = {k:v[k] for k in ['status','stage','utc','calls','actual_new_calls','expected_input_count',
                'error','conditions','macro','resource_terminal_sha256'] if k in v}
            if name == 'failure.json':
                data[name]['traceback_tail'] = v.get('traceback', '')[-2400:]
    if rel.endswith('gpu_01') and (p/'attempts.jsonl').exists():
        rows = [json.loads(x) for x in (p/'attempts.jsonl').read_text().splitlines() if x.strip()]
        data['BEGIN'] = sum(x.get('event') == 'BEGIN' for x in rows)
        data['ACCEPTED'] = sum(x.get('event') == 'ACCEPTED' for x in rows)
    data['direct_json_files'] = len(list(p.glob('*.json')))
    data['child_directories'] = sum(x.is_dir() for x in p.iterdir())
    out['stages'][rel] = data
resource = RUN/'controller'/(JOB+'.resource.json')
if resource.is_file():
    raw = resource.read_bytes(); v = json.loads(raw)
    matches = [json.loads(x) for x in (HOME/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines()
               if x.strip() and json.loads(x).get('name') == JOB]
    out['resource'] = v
    out['resource_sha256'] = hashlib.sha256(raw).hexdigest()
    out['unique_ledger_exact'] = matches == [v]
out['gpu'] = subprocess.run(['nvidia-smi','--query-gpu=index,memory.used,utilization.gpu',
    '--format=csv,noheader,nounits'], capture_output=True, text=True, check=True).stdout
print(json.dumps(out, ensure_ascii=False))
