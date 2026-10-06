#!/usr/bin/env python3
"""P1b-fix: local, loopback-only frame server for exact keyframe annotation.

Why: the browser's ``video.currentTime`` cannot prove *which* frame is on screen.
This helper decodes one requested frame with PyAV on demand (CPU only, no model,
no frame export to disk beyond a single JPEG response) and reports the decoded
index, PTS and time base next to the image bytes.

Endpoints (all read-only):
  GET /health                       -> {"ok": true, "samples": [...], "decoder": "..."}
  GET /frameinfo?sample=&frame=     -> {"index","pts_sec","time_base_sec","sha256","width","height"}
  GET /frame?sample=&frame=         -> image/jpeg bytes (identical bytes to the reported sha256)
  GET /shutdown                     -> graceful stop (loopback only)

Start:  python round6_score_alignment/p1b/frame_server.py [--port 8765]
Stop:   Ctrl+C in that terminal, or GET /shutdown
Binding: 127.0.0.1 only; it serves the pilot media listed in the manifest plus any
         extra manifest given with --extra-manifest (used for the synthetic sample).
Nothing is uploaded and the server never writes to the media directories.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[2]
P1B = ROOT / "round6_score_alignment/p1b"
DEFAULT_MANIFEST = P1B / "pilot_manifest.json"
JPEG_QUALITY = 92
MAX_INDEX_FRAMES = 10000

SAMPLES: dict[str, dict] = {}
CACHE: dict[tuple, dict] = {}
INDEX: dict[tuple, list[int]] = {}
LOCK = threading.Lock()


def load_samples(manifests: list[Path]) -> None:
    for path in manifests:
        if not path.is_file():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        for sample in payload.get("samples", []):
            if sample["sample_id"] in SAMPLES:
                raise ValueError(f"duplicate sample_id in server manifests: {sample['sample_id']}")
            media = (P1B / sample["media_rel_path"]).resolve()
            SAMPLES[sample["sample_id"]] = {
                "sample_id": sample["sample_id"], "media": media,
                "fps": float(sample["fps"]), "n_frames": int(sample["n_frames"]),
                "sha256": sample.get("sha256_local"),
                "width": int(sample["source_width"]), "height": int(sample["source_height"]),
            }


def decode_frame(sample: dict, index: int) -> dict:
    """Use decoded order as the frame number; reject cadence/manifest mismatch."""
    import av
    from PIL import Image

    path = sample["media"]
    if not path.is_file():
        raise FileNotFoundError(f"media missing for {sample['sample_id']}: {path}")
    n = sample["n_frames"]
    if not 0 < n <= MAX_INDEX_FRAMES:
        raise ValueError(f"manifest frame count must be within 1..{MAX_INDEX_FRAMES}")
    if not 0 <= index < n:
        raise ValueError(f"frame {index} outside 0..{n - 1}")

    # The complete, bounded PTS index is built by one sequential decode. Its list
    # position is the only frame-number authority. No image files are exported.
    stat = path.stat()
    identity = (str(path.resolve()), stat.st_size, stat.st_mtime_ns,
                sample.get("sha256"), sample["fps"], n, sample["width"], sample["height"])
    key = (sample["sample_id"], identity, index)
    with LOCK:
        if key in CACHE:
            return CACHE[key]
        if identity not in INDEX:
            expected_hash = sample.get("sha256")
            if expected_hash:
                h = hashlib.sha256()
                with path.open("rb") as fh:
                    for chunk in iter(lambda: fh.read(1 << 20), b""):
                        h.update(chunk)
                if h.hexdigest() != expected_hash:
                    raise RuntimeError("media sha256 differs from manifest")
            pts = []
            with av.open(str(path)) as container:
                stream = container.streams.video[0]
                for frame in container.decode(stream):
                    if frame.pts is None:
                        raise RuntimeError("decoded frame has no PTS")
                    if (frame.width, frame.height) != (sample["width"], sample["height"]):
                        raise RuntimeError("decoded dimensions differ from manifest")
                    pts.append(int(frame.pts))
                    if len(pts) > n:
                        raise RuntimeError("decoded frame count exceeds manifest")
                tb = float(stream.time_base)
            if len(pts) != n:
                raise RuntimeError(f"decoded frame count {len(pts)} differs from manifest {n}")
            if not (sample["fps"] > 0 and tb > 0):
                raise RuntimeError("invalid fps or time base")
            # Nonzero starting PTS is fine. VFR is explicitly rejected for this
            # annotation workflow, whose nominal seconds use frame/fps.
            for a, b in zip(pts, pts[1:]):
                cadence_frames = (b - a) * tb * sample["fps"]
                if abs(cadence_frames - 1.0) > 0.02:
                    raise RuntimeError("PTS cadence differs from manifest fps (VFR or wrong fps)")
            if len(pts) > 1:
                span_error = abs((pts[-1] - pts[0]) * tb - (n - 1) / sample["fps"])
                if span_error > max(2 * tb, 0.02 / sample["fps"]):
                    raise RuntimeError("cumulative PTS span differs from manifest fps")
            if len(set(pts)) != len(pts):
                raise RuntimeError("duplicate decoded PTS")
            INDEX[identity] = pts
        target_pts = INDEX[identity][index]
        # Seeking by an indexed PTS keeps subsequent requests bounded. Validate
        # the returned PTS against the independently built decode-order index.
        with av.open(str(path)) as container:
            stream = container.streams.video[0]
            tb = float(stream.time_base)
            container.seek(target_pts, stream=stream, backward=True)
            chosen = next((f for f in container.decode(stream) if f.pts == target_pts), None)
        if chosen is None:
            raise RuntimeError(f"indexed decoded PTS {target_pts} could not be retrieved")
    img = chosen.to_image()
    if img.size != (sample["width"], sample["height"]):
        raise RuntimeError("decoded dimensions changed during retrieval")
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=JPEG_QUALITY)
    jpeg = buf.getvalue()
    info = {"sample_id": sample["sample_id"], "media_sha256": sample.get("sha256"),
            "index": index, "pts": target_pts,
            "pts_sec": round(float(chosen.pts * tb), 6),
            "time_base_sec": tb,
            "sha256": hashlib.sha256(jpeg).hexdigest(),
            "width": sample["width"], "height": sample["height"],
            "format": "jpeg", "decoder": "PyAV (CPU)",
            "frame_is_keyframe": bool(getattr(chosen, "key_frame", False)),
            "index_derivation": "zero-based sequential decoded order; indexed PTS retrieval",
            "nominal_sec": index / sample["fps"]}
    with LOCK:
        CACHE[key] = {"info": info, "jpeg": jpeg}
        if len(CACHE) > 64:
            CACHE.pop(next(iter(CACHE)))
    return CACHE[key]


class Handler(BaseHTTPRequestHandler):
    server_version = "P1bFrameServer/1.0"

    def log_message(self, fmt, *args):  # keep the terminal quiet but auditable
        if self.server.verbose:
            print(f"[frame_server] {self.address_string()} {fmt % args}", flush=True)

    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code: int, payload: dict) -> None:
        self._send(code, json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                   "application/json; charset=utf-8")

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        if parsed.path == "/health":
            return self._json(200, {"ok": True, "loopback_only": True,
                                    "samples": sorted(SAMPLES), "decoder": "PyAV (CPU)",
                                    "cached": len(CACHE)})
        if parsed.path == "/shutdown":
            self._json(200, {"ok": True, "stopping": True})
            threading.Thread(target=self.server.shutdown, daemon=True).start()
            return
        if parsed.path in ("/frame", "/frameinfo"):
            sample_id = (query.get("sample") or [""])[0]
            try:
                index = int((query.get("frame") or ["-1"])[0])
            except ValueError:
                return self._json(400, {"error": "frame must be an integer"})
            sample = SAMPLES.get(sample_id)
            if sample is None:
                return self._json(404, {"error": f"unknown sample {sample_id!r}"})
            try:
                entry = decode_frame(sample, index)
            except Exception as exc:                     # noqa: BLE001 - report, do not hide
                return self._json(500, {"error": f"{type(exc).__name__}: {exc}"})
            if parsed.path == "/frameinfo":
                return self._json(200, entry["info"])
            return self._send(200, entry["jpeg"], "image/jpeg")
        return self._json(404, {"error": "unknown endpoint"})


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--manifest", action="append", default=[str(DEFAULT_MANIFEST)])
    parser.add_argument("--extra-manifest", action="append", default=[])
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args()
    manifests = [Path(m) for m in args.manifest + args.extra_manifest]
    load_samples(manifests)
    if args.host not in ("127.0.0.1", "localhost", "::1"):
        raise SystemExit("refusing to bind a non-loopback address")
    httpd = ThreadingHTTPServer((args.host, args.port), Handler)
    httpd.verbose = args.verbose
    print(json.dumps({"listening": f"http://{args.host}:{args.port}",
                      "samples": len(SAMPLES), "manifests": [str(m) for m in manifests],
                      "stop": "Ctrl+C here, or GET /shutdown"}, ensure_ascii=False), flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        httpd.server_close()
    print("[frame_server] stopped", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
