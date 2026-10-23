"""Read-only Linux snapshot for this one S1 root; no launch or retry actions."""
import json
from pathlib import Path
import shutil
import socket
import subprocess

ROOT = Path('/home/inspur/aic_video_work/sprint_spatial_s1_20261021_v1')


def load(name):
    path = ROOT / name
    return json.loads(path.read_text()) if path.exists() else None


def lines(name):
    path = ROOT / name
    return sum(1 for _ in path.open()) if path.exists() else 0


def owned_processes():
    found = []
    for process in Path('/proc').iterdir():
        if not process.name.isdigit():
            continue
        try:
            argv = (process / 'cmdline').read_bytes().replace(b'\0', b' ').decode(errors='replace')
            if str(ROOT / 'code') not in argv:
                continue
            stat = (process / 'stat').read_text().rsplit(')', 1)[1].split()
            found.append(dict(pid=int(process.name), parent=int(stat[1]), state=stat[0],
                start_ticks=stat[19], argv=argv, IO=(process / 'io').read_text().splitlines()[:7]))
        except (FileNotFoundError, ProcessLookupError, PermissionError):
            continue
    return found


def main():
    result = dict(host=socket.gethostname(), disk_free=shutil.disk_usage(ROOT).free,
        GPU=subprocess.check_output(['nvidia-smi', '--query-gpu=memory.used,utilization.gpu',
                                     '--format=csv,noheader,nounits'], text=True).strip(),
        owned=owned_processes(), arms=[])
    for arm in ['W10', 'W01', 'W11']:
        completion = load(f'arms/{arm}/completion.json')
        result['arms'].append(dict(arm=arm, updates=lines(f'arms/{arm}/updates.jsonl'),
            dev_outputs=lines(f'dev_{arm}_raw.jsonl'), confirm_outputs=lines(f'confirm_{arm}_raw.jsonl'),
            completed=completion is not None, seconds=completion['wall_seconds'] if completion else None))
    for name in ['training_failure.json', 'completion.json', 'selected.json', 'three_arms_terminal.json',
                 'dev_audit_review_terminal.json', 'first_confirm_terminal.json', 'confirm_audit_review_terminal.json']:
        value = load(name)
        if value is not None:
            result[name] = value
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
