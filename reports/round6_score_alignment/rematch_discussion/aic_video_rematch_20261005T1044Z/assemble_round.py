"""Assemble immutable local discussion packets. No browser/model access."""
from pathlib import Path
import argparse
import hashlib
import json
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent

def metadata(path):
    data = path.read_bytes()
    return {"path": str(path), "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--version", required=True)
    p.add_argument("--base", default="context-r00.md")
    p.add_argument("--addition", action="append", required=True)
    args = p.parse_args()
    if not args.version.replace("-", "").isalnum():
        raise ValueError("Invalid version")
    files = [ROOT / args.base] + [ROOT / name for name in args.addition]
    for path in files:
        if path.resolve().parent != ROOT.resolve() or not path.is_file():
            raise ValueError(f"Missing or out-of-scope input: {path}")
    target = ROOT / f"context-{args.version}.md"
    introduction = (
        f"# 当前完整信息包版本 {args.version}\n\n"
        "任务 AIC-VIDEO-REMATCH-NEXT-20261005。以下完整保留基础包与累计原始意见；"
        "旧正文中的轮次状态和待发送用语属于制作时快照，以本版本及账本为准。"
        "Gemini因上传失败由用户明确允许口述；其资料传递/生成异常逐项保留，"
        "不假称上传或逐字阅读已得到证明。Pro只在普通两轮完成后的独立节点发送。\n\n"
    )
    content = introduction
    for path in files:
        content += f"\n\n---\n\n# 完整保留：{path.name}\n\n"
        content += path.read_text(encoding="utf-8-sig")
    with target.open("x", encoding="utf-8", newline="\n") as f:
        f.write(content)
    info = metadata(target)
    ledger_path = ROOT / "ledger.json"
    ledger = json.loads(ledger_path.read_text(encoding="utf-8"))
    ledger["packets"][args.version] = info | {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "inputs": [metadata(path) for path in files],
        "read_status": "AWAITING_MAIN_COMPLETE_ADDITIONS_READ",
    }
    ledger_path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(info | {"lines": len(content.splitlines())}, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
