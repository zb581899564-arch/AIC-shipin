"""Single read-only Linux snapshot; no waits, launches, imports of runtime, or writes."""
import collections
import datetime
import json
import pathlib
import subprocess

ROOT = pathlib.Path('/home/inspur/aic_video_work/twenty_hour_five_20261014_v1')
CONTROL = ROOT / 'temporal_production_control_v6'


def rows(path):
    if not path.exists():
        return []
    data = path.read_text()
    # An append still in flight is observation-incomplete, never a job failure.
    if data and not data.endswith('\n'):
        data = data.rsplit('\n', 1)[0] if '\n' in data else ''
    return [json.loads(line) for line in data.splitlines() if line.strip()]


def process(pid):
    base = pathlib.Path('/proc') / str(pid)
    try:
        stat = (base / 'stat').read_text()
        fields = stat[stat.rfind(')') + 2:].split()
        argv = [part.decode() for part in (base / 'cmdline').read_bytes().split(b'\0') if part]
        return dict(pid=int(pid), state=fields[0], ppid=int(fields[1]),
                    start_ticks=int(fields[19]), argv=argv)
    except (FileNotFoundError, ProcessLookupError):
        return None


def snapshot():
    launch = json.loads((CONTROL / 'chain_launch.json').read_text())
    parent = process(launch['pid'])
    parent_verified = bool(parent and parent['state'] != 'Z'
                           and parent['start_ticks'] == launch['start_ticks']
                           and parent['argv'] == launch['argv'])
    journal = rows(CONTROL / 'run_01/journal.jsonl')
    complete = [row for row in journal if row['event'] in ('COMPLETE', 'REUSE')
                and row.get('exit_code') == 0]
    counts = collections.Counter(row['phase'] for row in complete)
    open_ops = {}
    for row in journal:
        key = (row['phase'], row['item'])
        if row['event'] == 'BEGIN':
            open_ops[key] = row
        elif row['event'] in ('COMPLETE', 'REUSE', 'FAILED'):
            open_ops.pop(key, None)
    accepted = begun = 0
    latest_attempt = None
    for file in sorted((ROOT / 'production_stream_v5/permanent/proofs/runtime_v5').glob('B*/gpu/attempts.jsonl')):
        for row in rows(file):
            begun += row['event'] == 'BEGIN_MODEL_CALL'
            accepted += row['event'] == 'ACCEPTED_MODEL_CALL'
            if row.get('utc') and (latest_attempt is None or row['utc'] > latest_attempt):
                latest_attempt = row['utc']
    output_qa = 0
    for row in complete:
        if row['phase'] == 'OUTPUT_REPLAY':
            batch = json.loads((ROOT / 'temporal_production_runtime_v5/batches' / (row['item'] + '.json')).read_text())
            output_qa += len(batch['request_ids'])
    children = set()
    if parent_verified:
        for thread in (pathlib.Path('/proc') / str(parent['pid']) / 'task').iterdir():
            try:
                children.update((thread / 'children').read_text().split())
            except FileNotFoundError:
                pass
    live = [p for pid in children if (p := process(pid)) and p['state'] != 'Z']
    verified_children = [p for p in live if p['ppid'] == launch['pid']
                         and any(p['argv'] == operation['argv'] for operation in open_ops.values())]
    return dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                parent_verified_live=parent_verified,
                parent_identity=dict(pid=launch['pid'], start_ticks=launch['start_ticks']),
                controller_completion=(CONTROL / 'run_01/completion.json').exists(),
                controller_failure=(CONTROL / 'run_01/failure.json').exists(),
                failed_operations=[dict(phase=r['phase'], item=r['item'], exit_code=r.get('exit_code'))
                                   for r in journal if r['event'] == 'FAILED'],
                source_complete=counts['SOURCE_PREPARE'], natural_gpu_batches=counts['GPU_WRAPPER'],
                model_begun=begun, model_accepted=accepted, frozen_model_budget=1992,
                first_input_qa=counts['FIRST_INPUT_REPLAY'], first_output_qa=output_qa,
                closed_batches=counts['LEASE_CLOSE'], latest_model_attempt_utc=latest_attempt,
                active_batch_phases=[dict(phase=r['phase'], batch_id=r['item']) for r in open_ops.values()
                                     if r['phase'] not in ('SOURCE_PREPARE', 'FIRST_INPUT_REPLAY')],
                actual_verified_live_children=[dict(pid=p['pid'], start_ticks=p['start_ticks'],
                                                   state=p['state'], kind='GPU' if 'gpu_run.py' in ' '.join(p['argv']) else 'CPU')
                                              for p in verified_children],
                gpu=subprocess.check_output(['nvidia-smi', '--query-gpu=index,memory.used,utilization.gpu',
                                             '--format=csv,noheader'], text=True).strip(),
                observation_only=True)


print(json.dumps(snapshot(), ensure_ascii=False))
