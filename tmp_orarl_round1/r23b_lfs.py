#!/usr/bin/env python3
import json, subprocess
from pathlib import Path
R = Path("/home/inspur/aic_video_work/orarl_round1")
p = R / "evidence/hf_model_api.json"
print("=== saved api json ===")
if p.exists():
    d = json.loads(p.read_text())
    print("top keys:", list(d.keys()))
    print("sha:", d.get("sha"))
    sibs = d.get("siblings", [])
    print("siblings:", len(sibs), "with lfs:", len([s for s in sibs if s.get("lfs")]))
    for s in sibs:
        if s["rfilename"].endswith((".safetensors", ".json", ".jinja")):
            print("  ", s["rfilename"], json.dumps(s.get("lfs")), "size=", s.get("size"))
else:
    print("missing")

print()
print("=== refetch with browser User-Agent ===")
url = "https://hf-mirror.com/api/models/OraRL/Video-ORA-4B?blobs=true"
o = subprocess.run(["curl", "-sS", "--max-time", "60", "-H",
                    "User-Agent: Mozilla/5.0 (X11; Linux x86_64)", url],
                   capture_output=True, text=True)
print("rc:", o.returncode, "stdout bytes:", len(o.stdout), "stderr:", o.stderr[:200])
try:
    d2 = json.loads(o.stdout)
    sibs = d2.get("siblings", [])
    withlfs = [s for s in sibs if s.get("lfs")]
    print("sha:", d2.get("sha"), "siblings:", len(sibs), "with lfs:", len(withlfs))
    for s in sibs:
        if s["rfilename"].endswith((".safetensors", ".json", ".jinja")):
            print("  ", s["rfilename"], json.dumps(s.get("lfs")))
    (R / "evidence/hf_model_api_blobs.json").write_text(json.dumps(d2, indent=2))
    print("saved")
except Exception as e:
    print("parse failed:", e)
    print(o.stdout[:400])
