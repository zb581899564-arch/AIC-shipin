"""Copy the already downloaded source for user-requested native MP4 annotation."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import shutil
import av

root = Path(__file__).resolve().parent
project = root.parent / "antigravity_label_probe_20261009"
source = root / "data/tvsum/selected_media/GsAD1KT1xo8.mp4"
destination = project / "input/native_video_tvsum_v1"
destination.mkdir(exist_ok=False)
video = destination / source.name
with source.open("rb") as incoming, video.open("xb") as outgoing:
    shutil.copyfileobj(incoming, outgoing, 1 << 20)
source_sha = hashlib.sha256(source.read_bytes()).hexdigest()
assert source_sha == hashlib.sha256(video.read_bytes()).hexdigest()
with av.open(str(video)) as container:
    stream = container.streams.video[0]
    metadata = {"duration_seconds_metadata": float(stream.duration * stream.time_base) if stream.duration else None,
                "video_time_base": [stream.time_base.numerator, stream.time_base.denominator],
                "video_start_time_ticks": stream.start_time,
                "dimensions": [stream.width, stream.height], "average_rate_metadata": str(stream.average_rate),
                "container_duration_seconds_metadata": container.duration / av.time_base if container.duration else None}
manifest = {"source_id": source.stem, "file": video.name, "bytes": video.stat().st_size,
            "media_sha256": source_sha, "purpose": "USER_REQUESTED_NATIVE_VIDEO_HIGHLIGHT_ANNOTATION",
            "input_mode": "Direct native view_file of original MP4, no prepared image samples",
            "human_scores_provided": False, "frame_crop_labels_provided": False, **metadata}
(destination / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
(root / "native_video_preparation.json").write_text(json.dumps({"utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS_LOCAL_COPY_IDENTITY_ORIGINAL_MP4", "input_directory": str(destination),
    "source": str(source), **manifest}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps(manifest, ensure_ascii=False))
