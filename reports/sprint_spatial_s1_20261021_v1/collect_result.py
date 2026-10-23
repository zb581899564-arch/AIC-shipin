"""Read natural S1 terminals and return only a small result receipt."""
import base64
import hashlib
import json
from pathlib import Path

ROOT = Path('/home/inspur/aic_video_work/sprint_spatial_s1_20261021_v1')
RESOURCE = ROOT.parent / 'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/controller'
LEDGER = ROOT.parent / 'improvement_round1/gpu_ledger.jsonl'


def read(path):
    return json.loads(path.read_text())


def main():
    final = read(ROOT / 'completion.json')
    ledger = [json.loads(s) for s in LEDGER.read_text().splitlines()]
    jobs = ['s1_centers_20261021_v1', 's1_three_arms_20261021_v1']
    if final['new_confirm_generations']:
        jobs.append('s1_first_confirm_20261021_v1')
    records = []
    for job in jobs:
        record = read(RESOURCE / (job + '.resource.json'))
        if record['status'] != 'completed' or record['exit_code'] != 0:
            raise ValueError('S1 GPU terminal is not natural completed/exit0')
        if [r for r in ledger if r.get('name') == job] != [record]:
            raise ValueError('S1 unique GPU ledger does not match terminal')
        records.append(dict(job=job, charged_seconds=record['charged_seconds'],
            peak_gpu_memory_mib=record.get('peak_gpu_memory_mib'), status=record['status']))
    if final['new_updates'] != 150 or final['new_dev_generations'] != 240:
        raise ValueError('S1 final denominators differ from frozen protocol')
    print(json.dumps(dict(completion=final, unique_GPU_records=records,
        short_receipt_bytes=(ROOT / 'short_result.json').stat().st_size,
        short_receipt_sha256=hashlib.sha256((ROOT / 'short_result.json').read_bytes()).hexdigest())))


if __name__ == '__main__':
    main()
