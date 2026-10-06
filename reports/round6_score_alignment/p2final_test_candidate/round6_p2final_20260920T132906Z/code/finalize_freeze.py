"""Create a hash manifest for the locally synchronized P2-Final evidence set."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    output = args.output.resolve()
    if output.exists():
        raise FileExistsError("refusing to overwrite final freeze")
    files = []
    for path in sorted(root.rglob("*")):
        if (not path.is_file() or path.resolve() == output or
                "__pycache__" in path.parts or path.suffix == ".pyc"):
            continue
        files.append({"path": path.relative_to(root).as_posix(),
                      "bytes": path.stat().st_size, "sha256": sha256(path)})
    payload = {
        "schema": "aic_round6_p2final_freeze_v1",
        "status": "PACKAGED_NOT_UPLOADED",
        "run_id": root.name,
        "official_score": "NOT_AVAILABLE",
        "uploaded": False,
        "locally_synced_files": len(files),
        "files": files,
        "remote_only_reproducibility_caches": ["inputs/retry_frames/", "inputs/decord97_frames/"],
        "package_relpath": "package/round6_p2t2_qwen_sparse_candidate.zip",
        "package_sha256": "31a3739c243303f3a3cf121f219c0092eae54ebe47084078e44a0070f65b3e8d",
        "predictions_sha256": "7b65d3f65ad9a75819e1b181fdd0bb297ca9c63970f519919bb31882e3396bc3",
    }
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": payload["status"], "files": len(files),
                      "output_sha256": sha256(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
