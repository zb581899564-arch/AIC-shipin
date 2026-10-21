"""Small, exclusive receipts and bounded source downloads."""
import hashlib
import json
from pathlib import Path
import urllib.request


def digest(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def reference(path):
    path = Path(path).resolve()
    return dict(path=str(path), bytes=path.stat().st_size, sha256=digest(path))


def write_new(path, value):
    with Path(path).open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)


def download_source(url, path, max_bytes):
    """Code/metadata only; model acquisition has a separate authorization gate."""
    path = Path(path)
    if path.exists() or path.with_suffix(path.suffix + ".partial").exists():
        raise FileExistsError(path)
    partial = path.with_suffix(path.suffix + ".partial")
    total = 0
    request = urllib.request.Request(url, headers={"User-Agent": "AIC-research-asset-audit"})
    with urllib.request.urlopen(request, timeout=40) as response, partial.open("xb") as stream:
        while chunk := response.read(256 * 1024):
            total += len(chunk)
            if total > max_bytes:
                raise RuntimeError(f"Source exceeds registered bound: {url}")
            stream.write(chunk)
    partial.rename(path)
    return dict(url=url, **reference(path))
