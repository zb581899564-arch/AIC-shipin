"""New physical local observations, with exact ordinal/PTS evidence.

This module does not load a model or start a job on import.  Every decoded
frame is checked against the locked native clock; neither FPS arithmetic nor
approximate seeks are used to recover frame numbers.  The optional color
conversion is an explicitly bound *existing* codec repair, never a fallback.
"""
from __future__ import annotations

from bisect import bisect_left
from fractions import Fraction
import hashlib
import math
from pathlib import Path


def _require(value, message):
    if not value:
        raise ValueError(message)


def sha256_file(path):
    result = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def exact_clock(source):
    """Return normalized Fraction PTS and physical end from a bound source."""
    points = [Fraction(str(value)) for value in source["normalized_exact_pts"]]
    end = Fraction(str(source["physical_end_exact"]))
    _require(points and len(points) == source["n_frames"] and points[0] == 0,
             "Full normalized native PTS beginning at zero required")
    _require(all(a < b for a, b in zip(points, points[1:])) and end > points[-1],
             "Native clock must be strictly increasing with a physical endpoint")
    return points, end


def plan_clips(source, *, clip_seconds=8, samples_per_clip=32):
    """Partition actual source time; select native frames at exact time targets.

    At least four time partitions, limited by available native frames, keep
    nominal clip lengths within the registered 25% source budget.  Uneven PTS
    or a source with fewer than four frames can still make a whole native atom
    exceed that budget; no forced selection repairs such a legal empty result.
    One-frame observations are padded only by the model processor; the unique
    physical observation remains one.
    """
    points, end = exact_clock(source)
    duration = Fraction(str(clip_seconds))
    _require(duration > 0 and type(samples_per_clip) is int and samples_per_clip >= 2,
             "Positive clip length and >=2 sample budget required")
    count = min(len(points), max(4, math.ceil(end / duration)))
    boundaries = [end * index / count for index in range(count + 1)]
    output = []
    for index, (start, stop) in enumerate(zip(boundaries, boundaries[1:])):
        first, last = bisect_left(points, start), bisect_left(points, stop)
        if first == last:
            continue
        sample_count = min(samples_per_clip, last - first)
        # Native time targets, with ordinal ties deterministically resolved.
        if sample_count == 1:
            sampled = [first]
        else:
            chosen = set()
            for sample in range(sample_count):
                target = points[first] + (points[last - 1] - points[first]) * sample / (sample_count - 1)
                right = bisect_left(points, target, first, last)
                options = [candidate for candidate in (right - 1, right)
                           if first <= candidate < last]
                chosen.add(min(options, key=lambda value: (abs(points[value] - target), value)))
            sampled = sorted(chosen)
        groups = [sampled[offset:offset + 2] for offset in range(0, len(sampled), 2)]
        centers = [sum((points[value] for value in group), Fraction(0)) / len(group)
                   for group in groups]
        cell_edges = [start] + [(a + b) / 2 for a, b in zip(centers, centers[1:])] + [stop]
        cells = []
        for lo, hi, group, center in zip(cell_edges, cell_edges[1:], groups, centers):
            cell_first, cell_stop = bisect_left(points, lo), bisect_left(points, hi)
            cells.append(dict(first=cell_first, stop=cell_stop,
                              start_exact=str(points[cell_first]),
                              end_exact=str(points[cell_stop] if cell_stop < len(points) else end),
                              nominal_start_exact=str(lo), nominal_end_exact=str(hi),
                              observed_ordinals=list(group), center_exact=str(center)))
        _require(all(cell["first"] < cell["stop"] for cell in cells),
                 "Every physical temporal group must support native output frames")
        output.append(dict(clip_id=f"clip_{index:05d}", first=first, stop=last,
                           start_exact=str(start), end_exact=str(stop),
                           sample_ordinals=sampled,
                           sample_pts_exact=[str(points[value]) for value in sampled],
                           cells=cells, physical_observations=len(sampled),
                           implicit_last_frame_padding=len(sampled) % 2))
    _require(output and output[0]["first"] == 0 and output[-1]["stop"] == len(points),
             "Local observations do not cover the complete source")
    _require(all(left["stop"] == right["first"] for left, right in zip(output, output[1:])),
             "Local clip native support must partition the complete source")
    return output


def _convert(frame, source):
    recipe = source.get("color_conversion")
    if recipe is None:
        return frame.to_ndarray(format="rgb24")
    _require(recipe["source_sha256"] == source["media"]["sha256"],
             "Existing color recipe is not bound to this media SHA")
    _require(frame.format.name == recipe["format"] and frame.width == recipe["width"]
             and frame.height == recipe["height"] and all(
                 getattr(frame, key) == recipe[key]
                 for key in ("color_trc", "colorspace", "color_primaries", "color_range")),
             "Existing registered source color profile changed")
    previous = frame.color_trc
    try:
        frame.color_trc = recipe["transfer_tag_for_conversion"]
        return frame.reformat(format="rgb24", src_colorspace=recipe["matrix"],
                              dst_colorspace=recipe["matrix"]).to_ndarray()
    finally:
        frame.color_trc = previous


def decode_native_frames(source, *, ordinals=None):
    """Yield exact decoded RGB frames; consume the iterator to verify EOF.

    The complete source is decoded once, even for sparse selections, so a
    changed frame count or a PTS mismatch cannot hide outside sampled frames.
    A caller stopping early has not obtained a complete-source verification.
    """
    import av
    points, _ = exact_clock(source)
    from .contracts import checked
    path = checked(source["media"])
    before = path.stat()
    wanted = None if ordinals is None else set(ordinals)
    if wanted is not None:
        _require(all(type(value) is int and 0 <= value < len(points) for value in wanted),
                 "Requested native ordinal is outside the source")
    actual_count = 0
    with av.open(str(path)) as container:
        _require(len(container.streams.video) == 1, "Exactly one physical video stream required")
        stream = container.streams.video[0]
        stream.thread_type = "NONE"
        stream.codec_context.thread_count = 1
        origin = None
        for ordinal, frame in enumerate(container.decode(stream)):
            _require(ordinal < len(points) and frame.pts is not None and frame.time_base is not None,
                     "Extra decoded frame or missing native PTS")
            raw = Fraction(frame.pts) * Fraction(frame.time_base)
            if origin is None:
                origin = raw
            point = raw - origin
            _require(point == points[ordinal], f"Native PTS mismatch at ordinal {ordinal}")
            actual_count += 1
            if wanted is not None and ordinal not in wanted:
                continue
            rgb = _convert(frame, source)
            _require(rgb.shape == (source["height"], source["width"], 3)
                     and str(rgb.dtype) == "uint8", "Decoded RGB geometry/dtype differs")
            yield dict(frame=ordinal, pts=str(point), rgb=rgb,
                       source_id=source["video_id"],
                       pixel_sha256=hashlib.sha256(rgb.tobytes(order="C")).hexdigest())
    after = path.stat()
    _require(actual_count == len(points), "Decoded native frame count differs")
    _require((before.st_size, before.st_mtime_ns, before.st_ino)
             == (after.st_size, after.st_mtime_ns, after.st_ino),
             "Media changed during native decoding")


def iter_decoded_clips(source, clips):
    """Stream one local clip in RAM; no all-source RGB/tensor cache is created."""
    import numpy as np
    wanted = [value for clip in clips for value in clip["sample_ordinals"]]
    _require(len(set(wanted)) == len(wanted), "Clip samples overlap unexpectedly")
    cursor = 0
    collected = []
    for item in decode_native_frames(source, ordinals=wanted):
        collected.append(item)
        clip = clips[cursor]
        if item["frame"] == clip["sample_ordinals"][-1]:
            _require([row["frame"] for row in collected] == clip["sample_ordinals"],
                     "Decoded local sample inventory differs")
            yield dict(clip=clip, rgb=np.stack([row["rgb"] for row in collected]),
                       pixel_sha256=[row["pixel_sha256"] for row in collected],
                       source_id=source["video_id"], source_sha256=source["media"]["sha256"],
                       source_n_frames=source["n_frames"])
            cursor += 1
            collected = []
    _require(cursor == len(clips) and not collected, "Incomplete local physical observations")
