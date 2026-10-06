#!/usr/bin/env python3
"""P1b-fix: render annotate.html from the template + a media manifest.

The delivered page is a rendered artifact so that it can be opened directly
(file://) with the real pilot manifest already embedded; the annotation *logic*
lives in annotation_core.js, which is not templated.

  python p1b/build_page.py                       # -> p1b/annotate.html (8 real pilot samples)
  python p1b/build_page.py --manifest <m> --media-prefix ../synthetic/ --out <o>
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

P1B = Path(__file__).resolve().parent
TEMPLATE = P1B / "annotate_template.html"
DEFAULT_MANIFEST = P1B / "pilot_manifest.json"
DEFAULT_OUT = P1B / "annotate.html"
DEFAULT_SERVER = "http://127.0.0.1:8765"


def render(manifest_path: Path, out_path: Path, server: str | None,
           media_prefix: str | None = None, asset_prefix: str = "") -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if media_prefix:
        for sample in manifest["samples"]:
            sample["media_rel_path"] = media_prefix + sample["file_name"]
    manifest["server_hint"] = server
    template = TEMPLATE.read_text(encoding="utf-8")
    page = template.replace("__MANIFEST__", json.dumps(manifest, ensure_ascii=False))
    page = page.replace("__SERVER__", json.dumps(server))
    if asset_prefix:
        page = page.replace('src="annotation_core.js"', f'src="{asset_prefix}annotation_core.js"')
    out_path.write_text(page, encoding="utf-8")
    return {"out": str(out_path), "manifest": str(manifest_path),
            "samples": len(manifest["samples"]), "server": server,
            "bytes": out_path.stat().st_size}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default=str(DEFAULT_MANIFEST))
    parser.add_argument("--out", default=str(DEFAULT_OUT))
    parser.add_argument("--server", default=DEFAULT_SERVER,
                        help="frame server base URL, or 'none' to disable exact frames")
    parser.add_argument("--media-prefix", default=None)
    parser.add_argument("--asset-prefix", default="",
                        help="prefix for annotation_core.js when the page is rendered into a "
                             "different directory (e.g. ../)")
    args = parser.parse_args()
    server = None if args.server.lower() in ("none", "", "null") else args.server
    info = render(Path(args.manifest), Path(args.out), server, args.media_prefix,
                  args.asset_prefix)
    print(json.dumps(info, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
