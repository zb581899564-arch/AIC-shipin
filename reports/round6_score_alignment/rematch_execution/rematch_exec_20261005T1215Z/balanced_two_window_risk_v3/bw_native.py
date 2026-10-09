"""Exact midpoint domains and original integer-floor64 physical sampling."""
import copy,hashlib,math,sys
from pathlib import Path
from fractions import Fraction
from bisect import bisect_left
import bw_common as c
require,sha,load=c.require,c.sha,c.load
HERE=c.RUN/'teacher_student_autopilot_v14'
_VERIFIED_SOURCE_STATS={}

def floor_indices(first,stop):
    require(type(first) is int and type(stop) is int and 0<=first<stop,'empty/invalid native domain')
    n=stop-first
    return list(range(first,stop)) if n<=64 else [first+i*(n-1)//63 for i in range(64)]

def balanced_schedule(original):
    pairs=[(Fraction(str(a)),Fraction(str(b))) for a,b in original]
    require(pairs and all(a<b for a,b in pairs),'original domains')
    if len(pairs)==2 and 30<pairs[-1][1]-pairs[0][0]<60:
        a,b=pairs[0][0],pairs[-1][1];m=(a+b)/2
        require(pairs[0][1]==pairs[1][0],'old two windows not contiguous')
        return [(a,m),(m,b)]
    return pairs

def convert_job(job,points,origin=Fraction(0)):
    original=[(p['start_sec'],p['end_sec']) for p in job['windows']]
    schedule=balanced_schedule(original)
    for ix,(part,(a,b)) in enumerate(zip(job['windows'],schedule)):
        part['base_window']=copy.deepcopy(part['window'])
        part['base_start_sec'],part['base_end_sec']=part['start_sec'],part['end_sec']
        if (a,b)==tuple(map(lambda x:Fraction(str(x)),original[ix])):continue
        raw_a,raw_b=origin+a,origin+b
        first,stop=bisect_left(points,raw_a),bisect_left(points,raw_b)
        ids=floor_indices(first,stop);w=copy.deepcopy(part['window'])
        require([i for i,t in enumerate(points) if float(raw_a)<=float(t)<float(raw_b)]==list(range(first,stop)),
            'float processor boundary membership differs from exact rational domain')
        w.update(window_id=w['window_id']+':BW',window_pts_start_sec=float(raw_a),window_pts_end_exclusive_sec=float(raw_b),
            window_duration_sec=float(b-a),planned_source_frame_ordinals=ids,planned_actual_pts_sec=[float(points[i]) for i in ids],
            planned_exact_pts=[str(points[i]) for i in ids],eligible_source_frame_count=stop-first,
            exact_raw_start=str(raw_a),exact_raw_end=str(raw_b),exact_normalized_start=str(a),exact_normalized_end=str(b),
            sampling_recipe='EXACT_BALANCED_TWO_WINDOWS_NATIVE_FLOOR64')
        part.update(start_sec=float(a),end_sec=float(b),window=w)
    return job

def exact_ranges(segments,window):
    # Exact source clock independently checks the original parser's result.
    from contracts import validate_segments
    validate_segments(segments,window['window_duration_sec'])
    pts=[Fraction(x) for x in window['eligible_exact_pts']]
    start=Fraction(window['exact_raw_start']);result=[]
    for a,b in segments:
        require(0<=Fraction(str(a))<Fraction(str(b))<=Fraction(window['exact_raw_end'])-start,'endpoint exceeds exact balanced duration')
        first,stop=bisect_left(pts,start+Fraction(str(a))),bisect_left(pts,start+Fraction(str(b)))
        require(0<=first<stop<=len(pts),'segment has no exact native source frame')
        result.append([first,stop])
    return result

def decode_balanced_window(window, observation=None):
    """Public sequential T decoder, with optional teacher-observation equality.

    Return (numpy THWC RGB, video_metadata, exact_native_pts_plan, evidence).
    This function also handles contest windows when called by the separately
    admitted production job; training never manufactures such a window.
    """
    import av
    import numpy as np
    w = window
    ids, pts = w["planned_source_frame_ordinals"], w["planned_actual_pts_sec"]
    require(ids and len(ids) == len(pts) <= 64 and ids == sorted(set(ids)) and
            all(type(i) is int and i >= 0 for i in ids) and all(math.isfinite(t) for t in pts), "invalid T frame/PTS plan")
    if "eligible_source_frame_count" in w:
        require(ids == floor_indices(ids[0], ids[0] + w["eligible_source_frame_count"]), "T sampling is not registered integer-floor rule")
    require(w.get("sampling_recipe")=="EXACT_BALANCED_TWO_WINDOWS_NATIVE_FLOOR64" and
        len(w["planned_exact_pts"])==len(ids),"unregistered native nearest authority")
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
            require(Fraction(frame.pts)*frame.time_base == Fraction(w['planned_exact_pts'][len(frames)]) and
                    point == pts[len(frames)], "actual decoded ordinal exact PTS differs")
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
