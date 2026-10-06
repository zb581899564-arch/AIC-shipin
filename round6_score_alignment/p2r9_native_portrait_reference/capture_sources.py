from __future__ import annotations

import argparse
import hashlib
import json
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


MAX_BYTES = 100 * 1024 * 1024

SOURCES = [
    ("live_yt_readme.md", "https://raw.githubusercontent.com/steven413d/LIVE-YT-VideoCropping/2a91e9492c092c966b10fdc9b369b057d92e8ffb/README.md"),
    ("live_yt_repo.json", "https://api.github.com/repos/steven413d/LIVE-YT-VideoCropping"),
    ("live_yt_contents.json", "https://api.github.com/repos/steven413d/LIVE-YT-VideoCropping/contents?ref=2a91e9492c092c966b10fdc9b369b057d92e8ffb"),
    ("live_yt_releases.json", "https://api.github.com/repos/steven413d/LIVE-YT-VideoCropping/releases"),
    ("live_yt_box_page.md", "https://r.jina.ai/https://utexas.app.box.com/s/hylumfu8akjhdgdd4teynsyc6ickwv1j/folder/407721578256"),
    ("youtube_ugc_official.md", "https://r.jina.ai/https://media.withyoutube.com/ugc-dataset"),
    ("lsvq_official.md", "https://r.jina.ai/https://www.colorado.edu/lab/live/live-fb-large-scale-social-video-quality-lsvq-database"),
    ("gaicd_readme.md", "https://raw.githubusercontent.com/HuiZeng/Grid-Anchor-based-Image-Cropping/d3262a1bc840cd998cdff4bee0c712b4ad0787b7/README.md"),
    ("gaicd_repo.json", "https://api.github.com/repos/HuiZeng/Grid-Anchor-based-Image-Cropping"),
    ("gaicd_tree.json", "https://api.github.com/repos/HuiZeng/Grid-Anchor-based-Image-Cropping/git/trees/d3262a1bc840cd998cdff4bee0c712b4ad0787b7?recursive=1"),
    ("gaicd_arxiv.xml", "https://export.arxiv.org/api/query?id_list=1909.08989"),
    ("mir_thumb_cropnet_crossref.json", "https://api.crossref.org/works/10.1145/3240508.3240517"),
    ("mir_thumb_cropnet_acm.md", "https://r.jina.ai/https://dl.acm.org/doi/10.1145/3240508.3240517"),
    ("gencrop_readme.md", "https://raw.githubusercontent.com/jhong93/gencrop/763da99334ec8c2ec10466af538d81878b7c7a2f/README.md"),
    ("gencrop_license.md", "https://raw.githubusercontent.com/jhong93/gencrop/763da99334ec8c2ec10466af538d81878b7c7a2f/LICENSE.md"),
    ("gencrop_arxiv.xml", "https://export.arxiv.org/api/query?id_list=2312.12080"),
    ("unsplash_license.md", "https://r.jina.ai/https://unsplash.com/license"),
    ("unsplash_data.md", "https://r.jina.ai/https://unsplash.com/data"),
    ("s2cnet_readme.md", "https://raw.githubusercontent.com/suyukun666/S2CNet/6c92712c85e73c2c22b7cbcb17338485b0dc56dd/README.md"),
    ("s2cnet_repo.json", "https://api.github.com/repos/suyukun666/S2CNet"),
    ("s2cnet_arxiv.xml", "https://export.arxiv.org/api/query?id_list=2401.08086"),
    ("h2v_arxiv.xml", "https://export.arxiv.org/api/query?id_list=2101.04051"),
]


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fetch(url: str) -> tuple[bytes, str | None]:
    request = urllib.request.Request(url, headers={"User-Agent": "p2r9-evidence-audit/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        declared = response.headers.get("Content-Length")
        if declared is not None and int(declared) > MAX_BYTES:
            raise RuntimeError("declared content length exceeds metadata gate")
        data = response.read(MAX_BYTES + 1)
        if len(data) > MAX_BYTES:
            raise RuntimeError("response exceeds metadata gate")
        return data, response.headers.get("Content-Type")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, required=True)
    args = parser.parse_args()
    snapshots = args.run_dir.resolve() / "snapshots"
    snapshots.mkdir(parents=True, exist_ok=True)
    rows = []
    for name, url in SOURCES:
        target = snapshots / name
        try:
            data, content_type = fetch(url)
            target.write_bytes(data)
            rows.append({
                "name": name,
                "url": url,
                "accessed_utc": datetime.now(timezone.utc).isoformat(),
                "status": "CAPTURED",
                "bytes": len(data),
                "sha256": sha256_bytes(data),
                "content_type": content_type,
            })
        except (urllib.error.URLError, TimeoutError, RuntimeError) as exc:
            rows.append({
                "name": name,
                "url": url,
                "accessed_utc": datetime.now(timezone.utc).isoformat(),
                "status": "CAPTURE_FAILED",
                "error_type": type(exc).__name__,
            })
    for existing_name, url in [
        ("live_yt_arxiv_2604.24947.pdf", "https://arxiv.org/pdf/2604.24947"),
        ("gencrop_portrait_testeval_sha256.json.gz", "https://raw.githubusercontent.com/jhong93/gencrop/763da99334ec8c2ec10466af538d81878b7c7a2f/data/portrait/testeval_sha256.json.gz"),
    ]:
        path = snapshots / existing_name
        if path.is_file():
            rows.append({
                "name": existing_name,
                "url": url,
                "accessed_utc": datetime.now(timezone.utc).isoformat(),
                "status": "CAPTURED_EARLIER_IN_RUN",
                "bytes": path.stat().st_size,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "content_type": "application/pdf" if path.suffix == ".pdf" else "application/gzip",
            })
    index = {
        "schema": "p2r9_source_snapshot_index_v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "per_candidate_metadata_limit_bytes": MAX_BYTES,
        "snapshots": rows,
        "counts": {
            "captured": sum(row["status"].startswith("CAPTURED") for row in rows),
            "failed": sum(row["status"] == "CAPTURE_FAILED" for row in rows),
        },
    }
    (args.run_dir / "source_snapshot_index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(index["counts"], ensure_ascii=False))
    return 0 if index["counts"]["failed"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
