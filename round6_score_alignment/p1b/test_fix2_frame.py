#!/usr/bin/env python3
"""Small synthetic frame-identity regression; CPU only, no pilot media access."""
from __future__ import annotations

import hashlib
import io
import json
from fractions import Fraction
from pathlib import Path

import av
import numpy as np
from PIL import Image

from frame_server import CACHE, INDEX, decode_frame
from make_marked_synthetic import draw_frame, frame_index_from_marker

ROOT = Path(__file__).resolve().parents[2]
P1B = Path(__file__).resolve().parent
OUT = ROOT / "reports/round6_score_alignment/phase1b_fix2"
SYN = OUT / "synthetic"


def create(name: str, fps: Fraction, nonzero: bool = False, vfr: bool = False) -> Path:
    SYN.mkdir(parents=True, exist_ok=True)
    path = SYN / name
    with av.open(str(path), "w") as container:
        stream = container.add_stream("mpeg4", rate=fps)
        stream.width, stream.height, stream.pix_fmt = 320, 240, "yuv420p"
        stream.time_base = Fraction(1, 1000) if fps == 10 else 1 / fps
        for i in range(12):
            image = draw_frame(i, (320, 240), 12)
            frame = av.VideoFrame.from_ndarray(np.asarray(image), format="rgb24")
            if fps == 10:
                frame.pts = (5000 if nonzero else 0) + 100 * i + (100 if vfr and i >= 6 else 0)
                frame.time_base = Fraction(1, 1000)
            else:
                frame.pts, frame.time_base = i, 1 / fps
            for packet in stream.encode(frame):
                container.mux(packet)
        for packet in stream.encode():
            container.mux(packet)
    return path


def sample(path: Path, fps: float, count: int = 12) -> dict:
    return {"sample_id": path.stem, "media": path, "fps": fps, "n_frames": count,
            "width": 320, "height": 240,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def observed(entry: dict) -> dict:
    return {"claimed_index": entry["info"]["index"],
            "machine_marker": frame_index_from_marker(Image.open(io.BytesIO(entry["jpeg"]))),
            "pts_sec": entry["info"]["pts_sec"],
            "nominal_sec": entry["info"]["nominal_sec"],
            "index_derivation": entry["info"]["index_derivation"]}


def main() -> int:
    CACHE.clear(); INDEX.clear()
    marked = P1B / "synthetic/synthetic_marked.mp4"
    cases = []
    base = sample(marked, 10.0, 120)
    for i in (64, 65, 0, 119):
        actual = observed(decode_frame(base, i))
        cases.append({"case": f"ordered_{i}", "pass": actual["claimed_index"] == i == actual["machine_marker"],
                      "observed": actual})
    for name, spec in (("nonzero_pts.mkv", (Fraction(10), True, False)),
                       ("vfr.mkv", (Fraction(10), True, True)),
                       ("fractional.mkv", (Fraction(30000, 1001), False, False))):
        path = create(name, *spec)
        s = sample(path, float(spec[0]))
        try:
            actual = observed(decode_frame(s, 7))
            accepted = True
        except Exception as exc:
            actual, accepted = {"error": str(exc)}, False
        want = name != "vfr.mkv"
        cases.append({"case": name, "pass": accepted == want and
                      (not accepted or actual["machine_marker"] == actual["claimed_index"] == 7),
                      "observed": actual})
    for name, s in (("wrong_fps", dict(base, fps=20.0)),
                    ("wrong_hash", dict(base, sha256="0" * 64)),
                    ("wrong_count", dict(base, n_frames=119))):
        try:
            actual = observed(decode_frame(s, 64))
            rejected = False
        except Exception as exc:
            actual, rejected = {"error": str(exc)}, True
        cases.append({"case": name, "pass": rejected, "observed": actual})
    result = {"run_id": "round6_p1b_fix2_20260917T0951Z", "cases": cases,
              "passed": sum(c["pass"] for c in cases), "total": len(cases)}
    (OUT / "frame_tests.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                                          encoding="utf-8")
    print(json.dumps({"passed": result["passed"], "total": result["total"]}))
    return 0 if result["passed"] == result["total"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
