#!/usr/bin/env python3
"""Check what LFS metadata the previously-saved HF API response contains, and
re-fetch with a browser-like User-Agent (the plain urllib UA gets 403)."""
import json
import subprocess
from pathlib import Path

R = Path("/home/inspur/aic_video_work/orarl_round1")
p = R / "evidence/hf_model_api.json"
if p.exists():
    d = json.loads(p.read_text())
    print("saved api top-level keys:", list(d.keys()))
    print("sha:", d.get("sha"))
    sibs = d.get("siblings", [])
    print("siblings:", len(sibs))
    withlfs = [s for s in sibs if s.get("lfs")]
    print("siblings with lfs block:", len(withlfs))
    for s in sibs[:3]:
        print("  sample:", json.dumps(s)[:300])
    for s in sibs:
        if s["rfilename"].endswith(".safetensors"):
            print("  shard:", json.dumps(s)[:300])
else:
    print("no saved api json")

print("\n--- refetch with User-Agent via curl ---")
url = "https://hf-mirror.com/api/models/OraRL/Video-ORA-4B?blobs=true"
out = subprocess.run(["curl", "-sS", "--max-time", "60", "-H",
                      "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
                      url], capture_output=True, text=True)
print("curl rc:", out.returncode, "bytes:", len(out.stdout))
try:
    d2 = json.loads(out.stdout)
    withlfs = [s for s in d2.get("siblings", []) if s.get("lfs")]
    print("fetched sha:", d2.get("sha"), "siblings:", len(d2.get("siblings", [])),
          "with lfs:", len(withlfs))
    for s in d2.get("siblings", []):
        if s["rfilename"].endswith((".safetensors", ".json", ".jinja")):
            print("  ", s["rfilename"], json.dumps(s.get("lfs")))
    (R / "evidence/hf_model_api_blobs.json").write_text(
        json.dumps(d2, indent=2)[:200000])
    print("saved evidence/hf_model_api_blobs.json")
except Exception as e:
    print("parse failed:", e, out.stdout[:500], out.stderr[:300])
