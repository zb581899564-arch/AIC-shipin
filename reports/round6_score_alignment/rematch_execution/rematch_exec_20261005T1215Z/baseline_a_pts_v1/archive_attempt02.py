"""One-time reconstruction of the preserved, frozen pre-terminal-fix snapshot."""
from pathlib import Path
import hashlib

root=Path(__file__).resolve().parent/"runtime_attempt02_preterminalfix"
path=root/"pts_contract.py"
text=(root.parent/path.name).read_text(encoding="utf-8")
a=text.index("def parse_native_segments(")
b=text.index("def native_segment_frames(",a)
text=text[:a]+text[b:]
path.write_bytes(text.encode())
path=root/"infer_temporal_pts.py"
text=(root.parent/path.name).read_text(encoding="utf-8")
text=text.replace("window_schedule, native_clip_plan, parse_native_segments)","window_schedule, native_clip_plan)")
a=text.index('                    if clock["branch"] == BRANCH_CFR:\n                        parsed, errors, warnings')
b=text.index('                    row.update(raw_output=raw',a)
text=text[:a]+"                    parsed, errors, warnings = tc.parse_segments(raw, end-start)\n"+text[b:]
path.write_bytes(text.encode())
import json
lock=json.loads((root/"source_lock.json").read_text())
for item in lock["files"]:
    assert hashlib.sha256((root/item["path"]).read_bytes()).hexdigest()==item["sha256"],item["path"]
assert hashlib.sha256((root/"source_lock.json").read_bytes()).hexdigest()=="deacc114488c6412c33420a7a15bf3301c2461536960fdf7ca9881de9be3bb48"
print("preserved revision 02 byte hashes verified")
