"""Declared new127-frame decoder; original V14 remains immutable."""
import hashlib,math,sys
from pathlib import Path
import nd_common as c
require,sha,load=c.require,c.sha,c.load
HERE=c.RUN/'teacher_student_autopilot_v14'
_VERIFIED_SOURCE_STATS={}

def floor_indices(first,stop):
    require(type(first) is int and type(stop) is int and 0<=first<stop,'bad original ordinal range')
    n=stop-first
    return list(range(first,stop)) if n<=64 else [first+i*(n-1)//63 for i in range(64)]

def nested_indices(base):
    require(base and base==sorted(set(base)) and len(base)<=64 and all(type(i) is int and i>=0 for i in base),'bad preserved floor64 ordinals')
    return sorted(set(base)|{(a+b)//2 for a,b in zip(base,base[1:]) if b-a>1})

def dense_window(original,points):
    import copy
    value=copy.deepcopy(original);base=original['planned_source_frame_ordinals'];ids=nested_indices(base)
    require(base==floor_indices(base[0],base[0]+original['eligible_source_frame_count']),'original floor64 contract differs')
    require(set(base)<=set(ids) and ids[0]==base[0] and ids[-1]==base[-1] and len(ids)<=127,'dense plan dropped or expanded physical endpoints')
    require([points[i] for i in base]==original['planned_actual_pts_sec'],'preserved source PTS differs')
    value.update(planned_source_frame_ordinals=ids,planned_actual_pts_sec=[points[i] for i in ids],
        sampling_recipe='BASE_FLOOR64_PLUS_ALL_ADJACENT_NATIVE_ORDINAL_MIDPOINTS',
        baseline_floor64_ordinals=base,physical_frames_added=len(ids)-len(base))
    return value

def decode_nested_window(window, observation=None):
    """Public sequential T decoder, with optional teacher-observation equality.

    Return (numpy THWC RGB, video_metadata, exact_native_pts_plan, evidence).
    This function also handles contest windows when called by the separately
    admitted production job; training never manufactures such a window.
    """
    import av
    import numpy as np
    w = window
    ids, pts = w["planned_source_frame_ordinals"], w["planned_actual_pts_sec"]
    require(ids and len(ids) == len(pts) <= 127 and ids == sorted(set(ids)) and
            all(type(i) is int and i >= 0 for i in ids) and all(math.isfinite(t) for t in pts), "invalid T frame/PTS plan")
    if "eligible_source_frame_count" in w:
        require(ids == nested_indices(floor_indices(ids[0], ids[0] + w["eligible_source_frame_count"])), "T sampling is not registered integer-floor rule")
    require(w.get("sampling_recipe")=="BASE_FLOOR64_PLUS_ALL_ADJACENT_NATIVE_ORDINAL_MIDPOINTS" and set(w["baseline_floor64_ordinals"])<=set(ids),"unregistered nested-density authority")
    before = Path(w["source_path"]).stat()
    key = str(Path(w["source_path"]).resolve(strict=True))
    signature = (w["source_sha256"], before.st_size, before.st_mtime_ns)
    if _VERIFIED_SOURCE_STATS.get(key) != signature:
        require(sha(w["source_path"]) == w["source_sha256"], "T source byte identity changed")
        _VERIFIED_SOURCE_STATS[key] = signature
    frames, actual_pts, pixels, window_source_pts = [], [], [], []
    with av.open(w["source_path"]) as container:
        require(len(container.streams.video) == 1, "ambiguous source video stream")
        stream = container.streams.video[0]
        rate = stream.average_rate
        require(rate is not None and float(rate) > 0, "actual source FPS unavailable")
        if observation is not None:
            require(observation["fps_num"] == rate.numerator and observation["fps_den"] == rate.denominator,
                    "student/teacher source average FPS metadata differs")
        wanted = iter(ids); current = next(wanted, None)
        for ordinal, frame in enumerate(container.decode(stream)):
            if current is None:
                break
            if ids[0] <= ordinal <= ids[-1]:
                require(frame.pts is not None and frame.time_base is not None, "actual unsampled source frame PTS missing")
                window_source_pts.append(float(frame.pts * frame.time_base))
            if ordinal != current:
                continue
            require(frame.pts is not None and frame.time_base is not None, "actual source frame PTS missing")
            point = float(frame.pts * frame.time_base)
            require(abs(point - pts[len(frames)]) <= 1e-6, "actual decoded ordinal PTS differs from teacher observation")
            color_path = HERE / "source_color.py"
            color = sys.modules.get("t_registered_source_color")
            if color is None or Path(color.__file__).resolve() != color_path.resolve():
                color = load(color_path, "t_registered_source_color")
            require(Path(color.__file__).resolve() == color_path.resolve(), "source color helper identity differs")
            image = color.convert_frame(frame, w["source_sha256"], "rgb24")
            require(image.ndim == 3 and image.shape[-1] == 3, "source RGB geometry changed")
            if "height" in w and "width" in w:
                require(image.shape[:2] == (w["height"], w["width"]), "registered source geometry changed")
            digest = hashlib.sha256(image.tobytes(order="C")).hexdigest()
            if observation is not None:
                require(digest == observation["frame_pixel_sha256"][len(frames)], "student/teacher frame pixel SHA differs")
            frames.append(image); actual_pts.append(point); pixels.append(digest)
            current = next(wanted, None)
    after = Path(w["source_path"]).stat()
    require(len(frames) == len(ids) and (before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns),
            "source changed or a planned frame was not decoded")
    arr = np.stack(frames)
    plan = dict(source_frame_ids=ids, source_relative_pts=actual_pts, window_start=w["window_pts_start_sec"])
    total = observation["source_total_frames"] if observation is not None else w.get("source_total_frames", w.get("n_frames"))
    require(type(total) is int and total > ids[-1], "actual full-source frame count must be declared")
    metadata = dict(fps=float(rate), frames_indices=ids, total_num_frames=total, video_backend="pyav")
    from native_frames import prepare_native_processor_input
    arr, metadata = prepare_native_processor_input(arr, metadata, plan)
    return arr, metadata, plan, dict(window_id=w["window_id"], source_sha256=w["source_sha256"],
        source_frame_ids=ids, actual_pts_sec=actual_pts, frame_pixel_sha256=pixels,
        window_source_pts_sec=window_source_pts,
        native_source_clock=True, explicit_lone_frame_copy=len(ids) == 1,
        teacher_pixel_identity_checked=observation is not None, source_fps_num=rate.numerator, source_fps_den=rate.denominator)

