"""One small control deployment followed by CPU-only source/model checks."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile

LOCAL = Path(__file__).resolve().parent
REPORT = LOCAL.parents[1] / "reports/i3d_umt_cross_domain_20261021_v1"
REMOTE = "/home/inspur/aic_video_work/i3d_umt_cross_domain_20261021_v1"
PYTHON = "/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python"
SSH = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15", "-o", "StrictHostKeyChecking=yes", "aic-inspur-home"]


def remote_code(code, timeout=60):
    result = subprocess.run(SSH + ["python3 -B -"], input=code, text=True,
                            encoding="utf-8", capture_output=True, timeout=timeout)
    print(result.stdout, flush=True)
    if result.stderr:
        print(result.stderr, file=sys.stderr, flush=True)
    result.check_returncode()
    return result.stdout


def main():
    REPORT.mkdir(exist_ok=False)
    files = [p for p in LOCAL.glob("*.py") if p.name != "deploy_cpu.py"]
    manifest = {p.name: dict(bytes=p.stat().st_size, sha256=hashlib.sha256(p.read_bytes()).hexdigest())
                for p in files}
    payload = REPORT / "code01.zip"
    with zipfile.ZipFile(payload, "x", zipfile.ZIP_DEFLATED) as package:
        for p in files:
            package.write(p, p.name)
        package.writestr("manifest.json", json.dumps(manifest))
    expected = hashlib.sha256(payload.read_bytes()).hexdigest()
    registration = dict(scope="BOOTSTRAP_SOURCE_AND_CPU_ONLY", root=REMOTE,
                        payload_bytes=payload.stat().st_size, payload_sha256=expected,
                        code=manifest, model_download_allowed=False,
                        protected_score=40.47, automatic_GPU=False, automatic_training=False,
                        human_label_correction="UMT default match is not original mturk; no weak labels admitted")
    (REPORT / "registration01.json").write_text(json.dumps(registration, indent=2), encoding="utf-8")
    remote_code(f"""from pathlib import Path
import socket,json
assert socket.gethostname()=='inspur-NP5570M5'
r=Path({REMOTE!r});assert r.parent==Path('/home/inspur/aic_video_work')
r.mkdir(exist_ok=False)
(r/'deployment_claim.json').write_text({json.dumps(registration)!r})
print('NEW_CPU_ROOT_CLAIMED')
""")
    subprocess.run(["scp", "-o", "BatchMode=yes", "-o", "ConnectTimeout=15",
                    "-o", "StrictHostKeyChecking=yes", str(payload), f"aic-inspur-home:{REMOTE}/code01.zip"],
                   check=True, timeout=90)
    remote_code(f"""from pathlib import Path
import hashlib,json,zipfile
r=Path({REMOTE!r});p=r/'code01.zip'
assert hashlib.sha256(p.read_bytes()).hexdigest()=={expected!r}
with zipfile.ZipFile(p)as z:
 assert z.testzip() is None
 m=json.loads(z.read('manifest.json'))
 for name,ref in m.items():
  assert Path(name).name==name
  b=z.read(name);assert len(b)==ref['bytes']and hashlib.sha256(b).hexdigest()==ref['sha256']
  with(r/name).open('xb')as f:f.write(b)
with(r/'code_acceptance.json').open('x')as f:json.dump(dict(status='PASS',sha256={expected!r}),f)
print('CODE_SHA_CRC_MEMBERS_PASS')
""")
    command = f"env CUDA_VISIBLE_DEVICES= {PYTHON} -B {REMOTE}/bootstrap.py --root {REMOTE}"
    result = subprocess.run(SSH + [command], text=True, encoding="utf-8", capture_output=True, timeout=240)
    (REPORT / "bootstrap_control.json").write_text(json.dumps(dict(exit_code=result.returncode,
        stdout=result.stdout, stderr=result.stderr), indent=2), encoding="utf-8")
    print(result.stdout, flush=True)
    if result.stderr:
        print(result.stderr, file=sys.stderr, flush=True)
    result.check_returncode()
    command = f"env CUDA_VISIBLE_DEVICES= {PYTHON} -B {REMOTE}/cpu_gate.py --root {REMOTE}"
    result = subprocess.run(SSH + [command], text=True, encoding="utf-8", capture_output=True, timeout=90)
    (REPORT / "cpu_control.json").write_text(json.dumps(dict(exit_code=result.returncode,
        stdout=result.stdout, stderr=result.stderr), indent=2), encoding="utf-8")
    print(result.stdout, result.stderr, flush=True)
    result.check_returncode()


if __name__ == "__main__":
    main()
