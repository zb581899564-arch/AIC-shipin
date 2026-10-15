"""Small control-only deployment; no media, weights, labels or ZIP transfer.

Existing project authorization explicitly permits direct SSH for small control
code and excludes Mac involvement. Mac was observed online 20261008T1705Z;
this scoped exception is recorded rather than claiming it remains offline.
"""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import subprocess

LOCAL = Path(__file__).resolve().parent.parent
REMOTE = "/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z"
PY = "/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--entry", default="context_advisory_v1")
    args = parser.parse_args()
    entry = args.entry
    assert entry.startswith("context_advisory_v") and entry.replace("_", "").isalnum()
    files = {p.name: base64.b64encode(p.read_bytes()).decode() for p in (LOCAL / entry).iterdir()
        if p.suffix in (".py", ".md", ".json") and p.is_file() and p.name not in ("source_lock.json", "preflight.json", "draft_preflight.json")}
    payload = json.dumps(dict(entry=entry, files=files))
    code = '''import base64,hashlib,json,pathlib,socket
data=json.loads(PAYLOAD)
assert socket.gethostname()=='inspur-NP5570M5'
root=pathlib.Path(REMOTE)/data['entry']
root.mkdir(exist_ok=True)
assert not (root/'source_lock.json').exists(), 'frozen source: deployment prohibited'
total=0
for name,value in data['files'].items():
 assert pathlib.Path(name).name==name
 b=base64.b64decode(value); p=root/name
 p.write_bytes(b); assert hashlib.sha256(p.read_bytes()).digest()==hashlib.sha256(b).digest()
 if p.suffix=='.py':compile(b,str(p),'exec')
 total+=len(b)
print(json.dumps(dict(status='PASS_SMALL_DRAFT_CODE_DEPLOYMENT_NO_MODEL_CALLS',files=len(data['files']),bytes=total)))
'''.replace("PAYLOAD", repr(payload)).replace("REMOTE", repr(REMOTE))
    result = subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", "aic-inspur-home", PY, "-B", "-"],
        input=code, text=True, encoding="utf-8", capture_output=True)
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    raise SystemExit(result.returncode)


if __name__ == "__main__":
    main()
