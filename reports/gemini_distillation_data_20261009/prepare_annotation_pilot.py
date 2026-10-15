"""Fixed 48 consecutive native decoded TVSum frames for annotation-only pilot."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import shutil
import zipfile

import av
import cv2

ROOT = Path(__file__).resolve().parent
SOURCE_ID = "GsAD1KT1xo8"
VIDEO_ZIP = ROOT / "data/tvsum/ydata-tvsum50-v1_1/ydata-tvsum50-video.zip"
PILOT = ROOT / "annotation_pilot_01"
INPUT = PILOT / "input"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if PILOT.exists():
        raise FileExistsError("Pilot exists; preserve successful extraction")
    INPUT.mkdir(parents=True)
    media_root = ROOT / "data/tvsum/selected_media"
    media_root.mkdir(exist_ok=True)
    video = media_root / (SOURCE_ID + ".mp4")
    if video.exists():
        raise FileExistsError("Selected video exists; inspect rather than overwrite")
    with zipfile.ZipFile(VIDEO_ZIP) as archive:
        names = [name for name in archive.namelist()
                 if Path(name).stem == SOURCE_ID and name.lower().endswith(".mp4")]
        if len(names) != 1:
            raise ValueError("Selected source is not unique")
        with archive.open(names[0]) as incoming, video.open("xb") as outgoing:
            shutil.copyfileobj(incoming, outgoing, 1 << 20)
    records = []
    first_pts = None
    with av.open(str(video)) as container:
        stream = container.streams.video[0]
        rate = str(stream.average_rate)
        for ordinal, frame in enumerate(container.decode(stream)):
            if frame.pts is None or frame.time_base is None:
                raise ValueError("Native frame clock missing")
            pts = frame.pts * frame.time_base
            if first_pts is None:
                first_pts = pts
            relative = pts - first_pts
            if relative < 10:
                continue
            rgb = frame.to_ndarray(format="rgb24")
            filename = f"f{len(records):03d}.png"
            success, encoded = cv2.imencode(".png", cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
            if not success:
                raise ValueError("PNG encoding failed")
            image = INPUT / filename
            with image.open("xb") as output:
                output.write(encoded.tobytes())
            records.append({"local_index": len(records), "frame_index": ordinal,
                            "file": filename, "pts": frame.pts,
                            "time_base": [frame.time_base.numerator, frame.time_base.denominator],
                            "pts_seconds": float(pts), "relative_pts_seconds": float(relative),
                            "width": frame.width, "height": frame.height,
                            "png_sha256": sha(image),
                            "rgb24_sha256": hashlib.sha256(rgb.tobytes()).hexdigest()})
            if len(records) == 48:
                break
    if len(records) != 48 or any(b["frame_index"] != a["frame_index"] + 1
                                 for a, b in zip(records, records[1:])):
        raise ValueError("Expected exactly 48 consecutive native frames")
    manifest = {"purpose": "USER_AUTHORIZED_ANNOTATION_ONLY_NOT_TRAINING",
                "source_id": SOURCE_ID, "source_group": "youtube:" + SOURCE_ID,
                "media_sha256": sha(video), "average_rate_metadata": rate,
                "selection_policy": "First 48 consecutive decoded frames at source-relative PTS >= 10 seconds; fixed before pixels reviewed",
                "count": len(records), "target_ratios": [[16, 9], [9, 16]], "frames": records,
                "audio_provided": False, "human_scores_provided": False}
    (INPUT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (PILOT / "preparation_receipt.json").write_text(json.dumps({
        "status": "PASS_FIXED_REAL_SOURCE_48_NATIVE_CONSECUTIVE_FRAMES",
        "utc": datetime.now(timezone.utc).isoformat(), "source_id": SOURCE_ID,
        "source_video": str(video), "source_video_bytes": video.stat().st_size,
        "source_video_sha256": sha(video), "manifest_sha256": sha(INPUT / "manifest.json"),
        "frames": 48, "crop_tasks": 96, "dimensions": [records[0]["width"], records[0]["height"]],
        "first_source_frame": records[0]["frame_index"], "last_source_frame": records[-1]["frame_index"],
        "first_relative_pts": records[0]["relative_pts_seconds"], "last_relative_pts": records[-1]["relative_pts_seconds"],
        "no_training": True, "no_test_media": True,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "PREPARED_ANNOTATION_ONLY", "frames": 48,
                      "dimensions": [records[0]["width"], records[0]["height"]],
                      "source_frame_range": [records[0]["frame_index"], records[-1]["frame_index"]],
                      "manifest": str(INPUT / "manifest.json")}))


if __name__ == "__main__":
    main()
