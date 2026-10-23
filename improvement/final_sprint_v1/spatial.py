"""Semantic subject extent and measured image-motion crops for the final sprint.

This is a new production exploration.  It does not load the failed S0 scorer,
S1 width adapter, historical launchers, or any labels.  A successful *semantic*
whole-scene answer is an explicit instruction to retain the accepted baseline
box.  A malformed answer, missing image, or failed model call raises instead.

The only learned component is the caller's existing Qwen3-VL base model.
Tracking uses current image pixels and OpenCV Lucas--Kanade optical flow; it
adds zero learned parameters.  Every changed box has either a same-frame
grounding witness or a forward/backward-checked tracking witness.

History deliberately retained: direct_box_v84 learned final crop deltas from
GNMC using a rank-8 adapter plus a 4096->3 head; motion_transport43 transported
only original centers, at unchanged maximum width, between fixed endpoints.
Both have recorded STOP outcomes.  LK is not a new mechanism here.  The new
hypothesis is raw semantic *subject extent*, same-frame foreground support,
and explicit subject-containment geometry with content-dependent scale.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from fractions import Fraction
import hashlib
import json
import math
import re
from typing import Any, Callable, Iterable, Mapping, Sequence

from .visible_geometry import polygon_bounds, visible_polygon


@dataclass(frozen=True)
class SpatialConfig:
    """One fixed recipe, not a threshold-search surface."""

    context_fraction: float = 0.20
    minimum_width_fraction: float = 0.55
    ground_interval_seconds: str = "2"
    tracker_long_edge: int = 480
    max_subjects: int = 3
    foreground_iterations: int = 2
    foreground_expansion: float = 0.15
    minimum_foreground_support: float = 0.08
    min_track_points: int = 8
    forward_backward_error: float = 1.5
    minimum_inlier_fraction: float = 0.65
    maximum_step_scale: float = 1.20
    cut_mean_absolute_difference: float = 0.22
    max_ground_calls: int = 5000

    def validate(self) -> None:
        if not (0 <= self.context_fraction <= 0.5):
            raise ValueError("Context fraction outside fixed safe geometry range")
        if not (0 < self.minimum_width_fraction <= 1):
            raise ValueError("Minimum legal width fraction must be in (0,1]")
        if Fraction(self.ground_interval_seconds) <= 0:
            raise ValueError("Ground interval must be positive exact seconds")
        if self.tracker_long_edge < 64 or self.min_track_points < 4:
            raise ValueError("Insufficient image tracking configuration")
        if not (0 < self.minimum_inlier_fraction <= 1):
            raise ValueError("Invalid inlier fraction")
        if self.maximum_step_scale <= 1 or self.max_ground_calls <= 0:
            raise ValueError("Invalid tracking scale or grounding call budget")
        if not 1 <= self.foreground_iterations <= 4 or not 0 <= self.foreground_expansion <= .5:
            raise ValueError("Invalid bounded foreground refinement configuration")
        if not 0 < self.minimum_foreground_support <= 1:
            raise ValueError("Invalid minimum observed foreground support")


GROUNDING_PROMPT = """Identify the visual subject or small group of subjects that is
most important to retain when reframing this single real video frame. Locate
their complete visible extent, including hands, equipment, or objects essential
to the visible action. Do not output a crop rectangle or a preferred zoom level.
If the information is distributed across the whole scene and no compact subject
or group should be isolated, use whole_scene. Do not invent an off-screen extent.
Coordinates are integer normalized full-image coordinates from 0 to 1000;
each box is [left, top, right, bottom]. Return at most three subject boxes.
Output only one JSON object with exactly these keys:
{"mode":"subject","boxes":[[left,top,right,bottom]]}
or {"mode":"whole_scene","boxes":[]}.
"""


def _number(value: Any) -> bool:
    return type(value) in (int, float) and math.isfinite(value)


def parse_grounding(raw: str, max_subjects: int = 3) -> dict[str, Any]:
    """Parse a complete model answer; never salvage partial coordinates."""
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError("Empty grounding answer is an execution failure")
    text = raw.strip()
    if text.startswith("```json\n") and text.endswith("\n```"):
        text = text[len("```json\n"):-len("\n```")]
    def reject_constant(value: str) -> None:
        raise ValueError("Non-finite JSON constant: " + value)
    def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result = {}
        for key, item in pairs:
            if key in result:
                raise ValueError("Duplicate grounding key: " + key)
            result[key] = item
        return result
    value = json.loads(text, parse_constant=reject_constant, object_pairs_hook=unique_object)
    if not isinstance(value, dict) or set(value) != {"mode", "boxes"}:
        raise ValueError("Grounding requires exactly mode and boxes")
    boxes = value["boxes"]
    if value["mode"] == "whole_scene":
        if boxes != []:
            raise ValueError("Whole-scene grounding must have no boxes")
        return value
    if value["mode"] != "subject" or not isinstance(boxes, list):
        raise ValueError("Unknown grounding mode")
    if not 1 <= len(boxes) <= max_subjects:
        raise ValueError("A subject answer requires one to three real boxes")
    for box in boxes:
        if (not isinstance(box, list) or len(box) != 4
                or any(type(v) is not int or not 0 <= v <= 1000 for v in box)
                or box[0] >= box[2] or box[1] >= box[3]):
            raise ValueError("Invalid normalized subject extent")
    if len({tuple(box) for box in boxes}) != len(boxes):
        raise ValueError("Duplicate subject extent")
    return value


def validate_box(box: Sequence[float], width: int, height: int,
                 ratio: Sequence[int]) -> None:
    if (type(width) is not int or type(height) is not int or min(width, height) <= 0
            or len(ratio) != 2 or any(type(v) is not int or v <= 0 for v in ratio)):
        raise ValueError("Native integer image geometry and ratio required")
    if len(box) != 3 or any(not _number(v) for v in box):
        raise ValueError("Invalid [x,y,width] crop")
    x, y, crop_width = [Fraction(str(v)) for v in box]
    crop_height = crop_width * ratio[1] / ratio[0]
    if min(x, y) < 0 or crop_width <= 0 or x + crop_width > width or y + crop_height > height:
        raise ValueError("Crop exceeds exact native frame geometry")


def pixel_subjects(grounding: Mapping[str, Any], width: int,
                   height: int) -> list[list[float]]:
    if grounding["mode"] != "subject":
        return []
    # Multiply integers before division.  A legal normalized edge at 1000
    # must become exactly width/height: (2007 / 1000.) * 1000 otherwise gives
    # 2007.0000000000002 and falsely rejects a valid border-touching subject.
    sizes = (width, height, width, height)
    return [[float(Fraction(v * sizes[i], 1000)) for i, v in enumerate(box)]
            for box in grounding["boxes"]]


def crop_from_subjects(subjects: Sequence[Sequence[float]], width: int,
                       height: int, ratio: Sequence[int], baseline: Sequence[float] | None,
                       config: SpatialConfig) -> tuple[list[float], dict[str, Any]]:
    """Keep measured subject union with context in a legal target-ratio crop.

    If the union cannot fit even the largest target-ratio crop, preserve the
    exact accepted box rather than arbitrarily drop one of several subjects.
    This is an explicit composition decision, not error handling.
    """
    config.validate()
    if (type(width) is not int or type(height) is not int or min(width, height) <= 0
            or len(ratio) != 2 or any(type(v) is not int or v <= 0 for v in ratio)):
        raise ValueError("Native integer image geometry and ratio required")
    scene_new = baseline is None
    if baseline is not None:
        validate_box(baseline, width, height, ratio)
    else:
        # New temporal selections have no accepted prior box.  A valid model
        # whole_scene/distributed judgment supplies the semantic reason for
        # this deterministic maximum-field scene crop; it is never used when
        # the model/image/clock fails.  Parent evidence names the seen frame.
        maximum = min(width, height * ratio[0] // ratio[1])
        baseline = [int((width - maximum) // 2),
                    int(math.floor((height - Fraction(maximum * ratio[1], ratio[0])) / 2)), maximum]
        validate_box(baseline, width, height, ratio)
    if not subjects:
        return list(baseline), {"decision": "MODEL_WHOLE_SCENE_NEW_FRAME_MAX_FIELD" if scene_new else "WHOLE_SCENE_KEEP_EXACT_BASELINE"}
    for box in subjects:
        if (len(box) != 4 or any(not _number(v) for v in box)
                or not (0 <= box[0] < box[2] <= width and 0 <= box[1] < box[3] <= height)):
            raise ValueError("Measured subject extent outside native image")
    left = min(b[0] for b in subjects)
    top = min(b[1] for b in subjects)
    right = max(b[2] for b in subjects)
    bottom = max(b[3] for b in subjects)
    tw, th = ratio
    maximum = min(width, height * tw // th)
    if maximum < 1:
        raise ValueError("No positive integer target-ratio crop fits this source")
    union_width, union_height = right - left, bottom - top
    required = max(union_width, union_height * tw / th)
    witness = {"subject_union_xyxy": [left, top, right, bottom],
               "maximum_legal_width": maximum,
               "minimum_subject_containment_width": required}
    if required > maximum:
        witness["decision"] = "MODEL_DISTRIBUTED_SUBJECTS_NEW_FRAME_MAX_FIELD" if scene_new else "DISTRIBUTED_SUBJECTS_KEEP_EXACT_BASELINE"
        return list(baseline), witness
    wanted = required * (1.0 + 2.0 * config.context_fraction)
    crop_width = min(maximum, max(math.ceil(wanted), math.ceil(maximum * config.minimum_width_fraction)))
    crop_height = Fraction(crop_width * th, tw)
    center_x, center_y = (left + right) / 2.0, (top + bottom) / 2.0
    # Subject containment can require fractional placement.  Choose integer
    # origin inside the feasible interval; enlarge by one pixel if rounding
    # otherwise destroys containment at an exact boundary.
    while True:
        x_low = max(0, math.ceil(right - crop_width - 1e-9))
        x_high = min(width - crop_width, math.floor(left + 1e-9))
        y_low = max(0, math.ceil(bottom - float(crop_height) - 1e-9))
        y_high = min(math.floor(height - crop_height), math.floor(top + 1e-9))
        if x_low <= x_high and y_low <= y_high:
            break
        if crop_width >= maximum:
            witness["decision"] = "NO_INTEGER_CONTAINMENT_NEW_FRAME_MAX_FIELD" if scene_new else "NO_INTEGER_CONTAINMENT_KEEP_EXACT_BASELINE"
            return list(baseline), witness
        crop_width += 1
        crop_height = Fraction(crop_width * th, tw)
    x = min(x_high, max(x_low, round(center_x - crop_width / 2)))
    y = min(y_high, max(y_low, round(center_y - float(crop_height) / 2)))
    result = [int(x), int(y), int(crop_width)]
    validate_box(result, width, height, ratio)
    witness.update(decision="SEMANTIC_SUBJECT_CONTAINMENT", requested_context_width=wanted,
                   actual_width=crop_width, contains_all_subjects=True,
                   context_fraction=config.context_fraction)
    return result, witness


def pixel_sha256(rgb: Any) -> str:
    import numpy as np
    data = np.asarray(rgb)
    if data.dtype != np.uint8 or data.ndim != 3 or data.shape[2] != 3:
        raise ValueError("Actual HxWx3 uint8 RGB pixels required")
    return hashlib.sha256(data.tobytes(order="C")).hexdigest()


def transport_polygon(polygon: Sequence[Sequence[float]], affine: Sequence[Sequence[float]],
                      native_wh: Sequence[int], thumbnail_wh: Sequence[int]) -> list[list[float]]:
    """Move the persistent subject quadrilateral in the measured thumbnail.

    Replacing a rotated polygon with its axis-aligned bounding box *before*
    the next transport inflates its area at every frame.  Only the final
    composition may take an axis-aligned bound; tracking retains all four
    transformed vertices, including their orientation, until regrounding.
    """
    if (len(polygon) != 4 or any(len(point) != 2 or any(not _number(v) for v in point) for point in polygon)
            or len(affine) != 2 or any(len(row) != 3 or any(not _number(v) for v in row) for row in affine)
            or len(native_wh) != 2 or len(thumbnail_wh) != 2
            or any(type(v) is not int or v <= 0 for v in (*native_wh, *thumbnail_wh))):
        raise ValueError("Finite subject quadrilateral and actual image transform required")
    sx, sy = thumbnail_wh[0] / native_wh[0], thumbnail_wh[1] / native_wh[1]
    return [[(affine[0][0] * x * sx + affine[0][1] * y * sy + affine[0][2]) / sx,
             (affine[1][0] * x * sx + affine[1][1] * y * sy + affine[1][2]) / sy]
            for x, y in polygon]


class SubjectTracker:
    """Bounded, deterministic measured transport; uncertainty requests a model.

    An uncertain tracker never supplies a crop.  The caller must perform a new
    same-frame grounding, or fail the candidate when its call budget is spent.
    """

    def __init__(self, config: SpatialConfig):
        config.validate()
        import cv2
        import numpy as np
        # Bound this process's OpenCV worker pool; the existing Java task is
        # not part of the sprint and must retain its shared CPU allocation.
        cv2.setNumThreads(1)
        self.cv2, self.np, self.config = cv2, np, config
        self.previous = None
        self.previous_shape = None
        self.boxes: list[list[float]] = []
        self.polygons: list[list[list[float]]] = []

    def foreground_support(self, rgb: Any, boxes: Sequence[Sequence[float]]) -> tuple[list[list[float]], list[dict[str, Any]]]:
        """Measure same-frame foreground support inside semantic extents.

        GrabCut is image segmentation during inference, without persisted or
        trained weights.  Only the containing extent of *all* foreground is
        used; this is not an aesthetic score or supervised crop regressor.
        Low/degenerate foreground support explicitly retains the model's real
        extent, while a library/decode exception propagates as execution failure.
        """
        np, cv2, cfg = self.np, self.cv2, self.config
        height, width = rgb.shape[:2]
        scale = min(1., cfg.tracker_long_edge / max(width, height))
        small = cv2.resize(rgb, (max(2, round(width * scale)), max(2, round(height * scale))), interpolation=cv2.INTER_AREA)
        sh, sw = small.shape[:2]
        sx, sy = sw / width, sh / height
        output, evidence = [], []
        for box in boxes:
            x0, y0, x1, y1 = box
            bw, bh = x1 - x0, y1 - y0
            exterior = [max(0, math.floor((x0 - bw * cfg.foreground_expansion) * sx)),
                        max(0, math.floor((y0 - bh * cfg.foreground_expansion) * sy)),
                        min(sw, math.ceil((x1 + bw * cfg.foreground_expansion) * sx)),
                        min(sh, math.ceil((y1 + bh * cfg.foreground_expansion) * sy))]
            mask = np.full((sh, sw), cv2.GC_BGD, dtype=np.uint8)
            ex0, ey0, ex1, ey1 = exterior
            mask[ey0:ey1, ex0:ex1] = cv2.GC_PR_BGD
            ix0, iy0, ix1, iy1 = max(0, math.floor(x0 * sx)), max(0, math.floor(y0 * sy)), min(sw, math.ceil(x1 * sx)), min(sh, math.ceil(y1 * sy))
            mask[iy0:iy1, ix0:ix1] = cv2.GC_PR_FGD
            entry = {"method": "SAME_FRAME_GRABCUT_SUPPORT", "semantic_box_xyxy": list(box),
                     "thumbnail_wh": [sw, sh], "iterations": cfg.foreground_iterations,
                     "new_trained_weights": 0}
            if int((mask == cv2.GC_BGD).sum()) < 8 or int((mask == cv2.GC_PR_FGD).sum()) < 8:
                output.append(list(box))
                evidence.append(dict(entry, status="SEMANTIC_EXTENT_RETAINED_INSUFFICIENT_BACKGROUND"))
                continue
            background = np.zeros((1, 65), dtype=np.float64)
            foreground = np.zeros((1, 65), dtype=np.float64)
            cv2.setRNGSeed(0)
            cv2.grabCut(cv2.cvtColor(small, cv2.COLOR_RGB2BGR), mask, None, background, foreground,
                        cfg.foreground_iterations, cv2.GC_INIT_WITH_MASK)
            support = (mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD)
            ys, xs = np.nonzero(support)
            denominator = max(1, (ix1 - ix0) * (iy1 - iy0))
            support_fraction = len(xs) / denominator
            entry.update(support_pixels=len(xs), support_fraction_of_semantic_box=support_fraction,
                         support_mask_sha256=hashlib.sha256(support.tobytes()).hexdigest())
            if len(xs) < 8 or support_fraction < cfg.minimum_foreground_support:
                output.append(list(box))
                evidence.append(dict(entry, status="SEMANTIC_EXTENT_RETAINED_LOW_PIXEL_SUPPORT"))
                continue
            refined = [float(Fraction(int(xs.min()) * width, sw)),
                       float(Fraction(int(ys.min()) * height, sh)),
                       float(Fraction(int(xs.max() + 1) * width, sw)),
                       float(Fraction(int(ys.max() + 1) * height, sh))]
            output.append(refined)
            evidence.append(dict(entry, status="MEASURED_FOREGROUND_EXTENT", foreground_box_xyxy=refined))
        return output, evidence

    def gray(self, rgb: Any) -> Any:
        cv2 = self.cv2
        height, width = rgb.shape[:2]
        scale = min(1.0, self.config.tracker_long_edge / max(width, height))
        small = cv2.resize(rgb, (max(1, round(width * scale)), max(1, round(height * scale))),
                           interpolation=cv2.INTER_AREA)
        return cv2.cvtColor(small, cv2.COLOR_RGB2GRAY)

    def reset(self, rgb: Any, boxes: Sequence[Sequence[float]]) -> None:
        self.previous = self.gray(rgb)
        self.previous_shape = rgb.shape[:2]
        self.boxes = [list(map(float, box)) for box in boxes]
        self.polygons = [[[left, top], [right, top], [right, bottom], [left, bottom]]
                         for left, top, right, bottom in self.boxes]

    def transport(self, rgb: Any) -> tuple[list[list[float]] | None, dict[str, Any]]:
        np, cv2, cfg = self.np, self.cv2, self.config
        current = self.gray(rgb)
        if self.previous is None or self.previous_shape != rgb.shape[:2] or current.shape != self.previous.shape:
            return None, {"tracking_status": "NEED_SAME_FRAME_GROUNDING", "reason": "NO_COMPATIBLE_PREVIOUS_IMAGE"}
        mad = float(np.abs(current.astype(np.float32) - self.previous.astype(np.float32)).mean() / 255)
        if mad > cfg.cut_mean_absolute_difference:
            return None, {"tracking_status": "NEED_SAME_FRAME_GROUNDING", "reason": "IMAGE_CUT_OR_LARGE_CHANGE", "image_mad": mad}
        if not self.boxes:
            self.previous = current
            return [], {"tracking_status": "WHOLE_SCENE_CONTINUATION", "image_mad": mad}
        height, width = rgb.shape[:2]
        sy, sx = current.shape[0] / height, current.shape[1] / width
        results, polygons, witnesses = [], [], []
        if len(self.polygons) != len(self.boxes):
            raise ValueError("Subject tracker polygon state does not match grounding")
        for subject, polygon in zip(self.boxes, self.polygons):
            mask = np.zeros_like(self.previous, dtype=np.uint8)
            left, top, right, bottom = subject
            x0, y0 = max(0, math.floor(left * sx)), max(0, math.floor(top * sy))
            x1, y1 = min(mask.shape[1], math.ceil(right * sx)), min(mask.shape[0], math.ceil(bottom * sy))
            mask[y0:y1, x0:x1] = 255
            previous_points = cv2.goodFeaturesToTrack(self.previous, maxCorners=64, qualityLevel=.01,
                                                     minDistance=4, mask=mask, blockSize=5)
            if previous_points is None or len(previous_points) < cfg.min_track_points:
                return None, {"tracking_status": "NEED_SAME_FRAME_GROUNDING", "reason": "TOO_FEW_SUBJECT_FEATURES"}
            next_points, status, _ = cv2.calcOpticalFlowPyrLK(self.previous, current, previous_points, None,
                winSize=(21, 21), maxLevel=3,
                criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, .01))
            if next_points is None or status is None:
                return None, {"tracking_status": "NEED_SAME_FRAME_GROUNDING", "reason": "FORWARD_FLOW_UNAVAILABLE"}
            returned, reverse_status, _ = cv2.calcOpticalFlowPyrLK(current, self.previous, next_points, None,
                winSize=(21, 21), maxLevel=3,
                criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, .01))
            if returned is None or reverse_status is None:
                return None, {"tracking_status": "NEED_SAME_FRAME_GROUNDING", "reason": "REVERSE_FLOW_UNAVAILABLE"}
            fb_error = np.linalg.norm(returned.reshape(-1, 2) - previous_points.reshape(-1, 2), axis=1)
            valid = (status.ravel() == 1) & (reverse_status.ravel() == 1) & np.isfinite(fb_error) & (fb_error <= cfg.forward_backward_error)
            before, after = previous_points.reshape(-1, 2)[valid], next_points.reshape(-1, 2)[valid]
            if len(before) < cfg.min_track_points or not np.isfinite(after).all():
                return None, {"tracking_status": "NEED_SAME_FRAME_GROUNDING", "reason": "FLOW_CONSISTENCY_LOST"}
            cv2.setRNGSeed(0)
            affine, inliers = cv2.estimateAffinePartial2D(before, after, method=cv2.RANSAC,
                ransacReprojThreshold=2.0, maxIters=1000, confidence=.99, refineIters=10)
            if affine is None or inliers is None or not np.isfinite(affine).all():
                return None, {"tracking_status": "NEED_SAME_FRAME_GROUNDING", "reason": "SUBJECT_TRANSFORM_UNAVAILABLE"}
            inlier_fraction = float(inliers.mean())
            scale = float(math.hypot(affine[0, 0], affine[1, 0]))
            if inlier_fraction < cfg.minimum_inlier_fraction or not 1 / cfg.maximum_step_scale <= scale <= cfg.maximum_step_scale:
                return None, {"tracking_status": "NEED_SAME_FRAME_GROUNDING", "reason": "UNTRUSTED_SUBJECT_TRANSFORM", "scale": scale, "inlier_fraction": inlier_fraction}
            transformed = transport_polygon(polygon, affine.tolist(), [width, height],
                                            [current.shape[1], current.shape[0]])
            visible = visible_polygon(transformed, width, height)
            if not visible:
                return None, {"tracking_status": "NEED_SAME_FRAME_GROUNDING", "reason": "SUBJECT_HAS_NO_VISIBLE_AREA"}
            moved = polygon_bounds(visible)
            results.append(moved)
            # Preserve the full transported quad, including off-image vertices.
            # Only composition and next-frame feature selection use visibility.
            polygons.append(transformed)
            witnesses.append({"affine_thumbnail": affine.tolist(), "thumbnail_wh": [current.shape[1], current.shape[0]],
                              "subject_polygon_xy": transformed, "geometry": "PERSISTENT_GROUNDED_QUADRILATERAL",
                              "visible_polygon_xy": visible, "visible_subject_xyxy": moved,
                              "visibility_geometry": "POSITIVE_AREA_POLYGON_IMAGE_INTERSECTION",
                              "accepted_points": len(before), "inlier_fraction": inlier_fraction,
                              "forward_backward_error_max": float(fb_error[valid].max()), "step_scale": scale})
        self.previous, self.boxes, self.polygons = current, results, polygons
        return results, {"tracking_status": "MEASURED_FORWARD_BACKWARD_FLOW", "subjects": witnesses, "image_mad": mad}


def compose_source(observations: Iterable[Mapping[str, Any]], baseline_boxes: Mapping[int, Sequence[float] | None],
                   ratio: Sequence[int], ground: Callable[[Any, Mapping[str, Any]], Mapping[str, Any]],
                   config: SpatialConfig | None = None, *, initial_ground_calls: int = 0,
                   on_record: Callable[[dict[str, Any]], None] | None = None) -> list[dict[str, Any]]:
    """Compose selected native frames from an exact decoded-image iterator.

    Each observation contains ``frame`` (native ordinal), ``pts`` (an exact
    rational string), ``rgb`` (uint8), and optional ``source_id``.  ``ground``
    returns the actual runtime dictionary with at least ``raw_text`` and
    ``input_sha256``.  It is normally a wrapper around QwenRuntime's generic
    ``generate_images``.  The iterator must contain exactly selected frames.
    The enclosing run journal owns durable per-source completion and resumption.
    """
    config = config or SpatialConfig()
    config.validate()
    if type(initial_ground_calls) is not int or initial_ground_calls < 0:
        raise ValueError("Previously completed grounding call count must be a nonnegative integer")
    tracker = SubjectTracker(config)
    expected = sorted(baseline_boxes)
    if any(type(frame) is not int or frame < 0 for frame in expected):
        raise ValueError("Native frame ordinals must be nonnegative integers")
    records, count, previous_frame, previous_pts = [], 0, None, None
    last_ground_pts, anchor, subjects = None, None, []
    ground_calls = initial_ground_calls
    for observation in observations:
        frame = observation["frame"]
        if count >= len(expected) or frame != expected[count]:
            raise ValueError("Decoded observation membership differs from selected native frames")
        raw_pts = observation["pts"]
        if isinstance(raw_pts, (float, bool)):
            raise ValueError("Exact native PTS required; nominal-FPS time is prohibited")
        pts = Fraction(raw_pts)
        if pts < 0:
            raise ValueError("Normalized native PTS must be nonnegative")
        if previous_pts is not None and pts <= previous_pts:
            raise ValueError("Native PTS not strictly increasing")
        rgb = observation["rgb"]
        pixels = pixel_sha256(rgb)
        if "pixel_sha256" in observation and observation["pixel_sha256"] != pixels:
            raise ValueError("Decoded pixel witness differs from actual RGB bytes")
        height, width = rgb.shape[:2]
        baseline = baseline_boxes[frame]
        if baseline is not None:
            validate_box(baseline, width, height, ratio)
        reground = (previous_frame is None or frame != previous_frame + 1 or last_ground_pts is None
                    or observation.get("is_shot_start", False) is True
                    or pts - last_ground_pts >= Fraction(config.ground_interval_seconds))
        flow_witness: dict[str, Any] = {"tracking_status": "ANCHOR_DUE"}
        if not reground:
            transported, flow_witness = tracker.transport(rgb)
            reground = transported is None
            if transported is not None:
                subjects = transported
        if reground:
            if ground_calls >= config.max_ground_calls:
                raise RuntimeError("Grounding call budget reached; no baseline-as-failure substitution")
            ground_calls += 1
            request = {"prompt": GROUNDING_PROMPT, "max_new_tokens": 192, "frame": frame,
                       "native_pts": str(pts), "pixel_sha256": pixels, "role": "base",
                       "source_id": str(observation.get("source_id", ""))}
            reply = dict(ground(rgb, request))
            if not isinstance(reply.get("input_sha256"), str) or not re.fullmatch(r"[0-9a-f]{64}", reply["input_sha256"]):
                raise ValueError("Grounding lacks actual processor input SHA witness")
            parsed = parse_grounding(reply.get("raw_text", ""), config.max_subjects)
            subjects = pixel_subjects(parsed, width, height)
            subjects, foreground_evidence = tracker.foreground_support(rgb, subjects)
            tracker.reset(rgb, subjects)
            anchor = {"frame": frame, "native_pts": str(pts), "pixel_sha256": pixels,
                      "input_sha256": reply["input_sha256"], "raw_text": reply["raw_text"],
                      "raw_sha256": hashlib.sha256(reply["raw_text"].encode()).hexdigest(),
                      "mode": parsed["mode"], "subjects_normalized": parsed["boxes"],
                      "foreground_support": foreground_evidence,
                      "runtime": {k: reply[k] for k in ("output_tokens", "gpu_seconds") if k in reply},
                      "parameter_inventory_sha256": hashlib.sha256(json.dumps(reply.get("parameter_inventory"),
                          sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()}
            last_ground_pts = pts
        box, composition = crop_from_subjects(subjects, width, height, ratio, baseline, config)
        record = {"frame": frame, "native_pts": str(pts), "bboxes": box,
                  "spatial_source": ("QWEN_SEMANTIC_EXTENT_MEASURED_LK" if subjects else
                                     ("ACCEPTED_BASELINE_WHOLE_SCENE" if baseline is not None else "QWEN_OBSERVED_WHOLE_SCENE_MAX_FIELD")),
                  "pixel_sha256": pixels, "ground_anchor": dict(anchor),
                  "same_frame_grounding": reground, "subjects_xyxy": subjects,
                  "composition": composition, "tracking": flow_witness,
                  "ground_calls_cumulative": ground_calls}
        if "source_id" in observation:
            record["video_id"] = str(observation["source_id"])
        if previous_frame is not None:
            record["previous_observed_frame"] = previous_frame
            record["previous_pixel_sha256"] = records[-1]["pixel_sha256"]
        records.append(record)
        if on_record is not None:
            on_record(record)
        previous_frame, previous_pts = frame, pts
        count += 1
    if count != len(expected):
        raise ValueError("Source decoding ended before all selected native frames")
    return records


def process_source(observations: Iterable[Mapping[str, Any]], selected_frames: Sequence[int],
                   baseline_boxes: Mapping[int, Sequence[float]], ratio: Sequence[int],
                   ground_image: Callable[[Any, Mapping[str, Any]], Mapping[str, Any]],
                   config: SpatialConfig | None = None, *, initial_ground_calls: int = 0,
                   on_record: Callable[[dict[str, Any]], None] | None = None) -> dict[str, Any]:
    """Production API with one compact evidence object per source.

    A previously successful source result is adopted by the enclosing immutable
    source journal, not by this pure orchestration function.  ``on_record`` is
    available to checkpoint a source in progress; callers must validate its
    binding before adopting it.  No PID/timeout is interpreted as completion.
    """
    config = config or SpatialConfig()
    frames = list(selected_frames)
    if any(type(frame) is not int or frame < 0 for frame in frames) or frames != sorted(set(frames)):
        raise ValueError("Selected native frames must be unique sorted ordinals")
    selected_baselines = {frame: baseline_boxes.get(frame) for frame in frames}
    records = compose_source(observations, selected_baselines, ratio, ground_image, config,
                             initial_ground_calls=initial_ground_calls, on_record=on_record)
    anchors: dict[int, dict[str, Any]] = {}
    evidence = []
    decisions: dict[str, int] = {}
    changed, new, tracking, reground = 0, 0, 0, 0
    for record in records:
        anchor = record["ground_anchor"]
        anchor_frame = anchor["frame"]
        if anchor_frame in anchors and anchors[anchor_frame] != anchor:
            raise ValueError("Grounding anchor identity changed during source rendering")
        anchors[anchor_frame] = anchor
        current = dict({key: value for key, value in record.items() if key != "ground_anchor"}, ground_anchor_frame=anchor_frame,
                       ground_anchor_raw_sha256=anchor["raw_sha256"],
                       source_frame=record["frame"], box_xyw=list(record["bboxes"]))
        evidence.append(current)
        frame = record["frame"]
        if frame not in baseline_boxes:
            new += 1
        elif list(baseline_boxes[frame]) != record["bboxes"]:
            changed += 1
        decision = record["composition"]["decision"]
        decisions[decision] = decisions.get(decision, 0) + 1
        reground += int(record["same_frame_grounding"])
        tracking += int(record["tracking"]["tracking_status"] == "MEASURED_FORWARD_BACKWARD_FLOW")
    return {"predictions": [{"frame": row["frame"], "bboxes": row["bboxes"]} for row in records],
            "spatial_evidence": evidence, "groundings": [anchors[frame] for frame in sorted(anchors)],
            "diagnostics": {"selected_frames": len(frames), "new_frames": new,
                            "changed_existing_boxes": changed, "same_frame_groundings": reground,
                            "tracked_frames": tracking, "composition_decisions": decisions,
                            "ground_calls_cumulative": initial_ground_calls + reground,
                            "additional_learned_parameters": 0, "config": asdict(config),
                            "offline_quality_validation": "NOT_RUN",
                            "official_quality": "UNKNOWN"}}


def _rectangle_polygons(boxes: Sequence[Sequence[float]]) -> list[list[list[float]]]:
    return [[[left, top], [right, top], [right, bottom], [left, bottom]]
            for left, top, right, bottom in boxes]


def _visible_polygon_boxes(polygons: Sequence[Sequence[Sequence[float]]], width: int,
                           height: int) -> list[list[float]]:
    """Intersect transported *visible* extents with the current image domain."""
    boxes = []
    for polygon in polygons:
        visible = visible_polygon(polygon, width, height)
        if not visible:
            raise ValueError("Transported semantic extent has no visible support; control cannot invent a box")
        boxes.append(polygon_bounds(visible))
    return boxes


def _control_anchor(anchor: Mapping[str, Any], row: Mapping[str, Any], width: int,
                    height: int) -> list[list[list[float]]]:
    raw = anchor["raw_text"]
    if (not isinstance(raw, str) or hashlib.sha256(raw.encode()).hexdigest() != anchor["raw_sha256"]
            or row["ground_anchor_raw_sha256"] != anchor["raw_sha256"]
            or anchor["frame"] != row["frame"] or anchor["native_pts"] != row["native_pts"]
            or anchor["pixel_sha256"] != row["pixel_sha256"]
            or not re.fullmatch(r"[0-9a-f]{64}", anchor["input_sha256"])):
        raise ValueError("Semantic control anchor does not match the actual parent observation")
    parsed = parse_grounding(raw)
    if parsed["mode"] != anchor["mode"] or parsed["boxes"] != anchor["subjects_normalized"]:
        raise ValueError("Semantic control anchor differs from its complete raw answer")
    boxes = pixel_subjects(parsed, width, height)
    if len(boxes) != len(row["subjects_xyxy"]):
        raise ValueError("Semantic control and parent subject identities differ")
    return _rectangle_polygons(boxes)


def semantic_extent_control(source: Mapping[str, Any], parent_proof: Mapping[str, Any],
                            baseline_boxes: Mapping[int, Sequence[float]],
                            config: SpatialConfig | None = None) -> dict[str, Any]:
    """Remove GrabCut tightening using the exact successful parent's observations.

    Qwen answers, frame membership and measured LK affines are reused.  These
    affines were measured inside the parent's refined extents, so this is a
    *geometry* control, not an independently tracked or newly inferred model.
    It uses no image decoding, parameter loading or additional neural calls.
    The caller must verify the parent file SHA and durable SUCCESS binding.
    """
    config = config or SpatialConfig()
    config.validate()
    width, height, ratio = source["width"], source["height"], source["targetRatioWH"]
    if (parent_proof.get("schema") != "AIC_FINAL_SPATIAL_EVIDENCE_V1"
            or parent_proof.get("video_id") != source["video_id"]
            or parent_proof.get("source_sha256") != source["media"]["sha256"]):
        raise ValueError("Semantic control requires the exact parent source proof")
    detail = parent_proof["observed_pixel_evidence"]
    rows, anchors = detail["frame_evidence"], detail["groundings"]
    frame_ids = sorted(baseline_boxes)
    parent_predictions = parent_proof["frames"]
    if ([row["frame"] for row in rows] != frame_ids
            or [row["frame"] for row in parent_predictions] != frame_ids
            or any(type(frame) is not int or not 0 <= frame < source["n_frames"] for frame in frame_ids)):
        raise ValueError("Semantic control must preserve the complete protected frame membership")
    anchor_map = {anchor["frame"]: anchor for anchor in anchors}
    if len(anchor_map) != len(anchors):
        raise ValueError("Duplicate semantic control anchor")
    predictions, evidence = [], []
    polygons, pixel_polygons, previous, active_anchor = [], [], None, None
    used_anchors = set()
    for row, parent_prediction in zip(rows, parent_predictions):
        frame = row["frame"]
        if (row["native_pts"] != source["normalized_exact_pts"][frame]
                or row["bboxes"] != parent_prediction["bboxes"]
                or row.get("box_xyw") != parent_prediction["bboxes"]
                or type(row["same_frame_grounding"]) is not bool
                or not re.fullmatch(r"[0-9a-f]{64}", row["pixel_sha256"])):
            raise ValueError("Semantic control parent frame/PTS/box/pixel witness differs")
        anchor_id = row["ground_anchor_frame"]
        if row["same_frame_grounding"]:
            if anchor_id != frame or anchor_id not in anchor_map:
                raise ValueError("Missing same-frame semantic control anchor")
            polygons = _control_anchor(anchor_map[anchor_id], row, width, height)
            pixel_polygons = _rectangle_polygons(row["subjects_xyxy"])
            active_anchor = anchor_id
            used_anchors.add(anchor_id)
        else:
            if (previous is None or frame != previous["frame"] + 1 or anchor_id != active_anchor
                    or row.get("previous_observed_frame") != previous["frame"]
                    or row.get("previous_pixel_sha256") != previous["pixel_sha256"]
                    or row["ground_anchor_raw_sha256"] != anchor_map[anchor_id]["raw_sha256"]):
                raise ValueError("Broken semantic control native tracking chain")
            tracking = row["tracking"]
            if not polygons:
                if tracking["tracking_status"] != "WHOLE_SCENE_CONTINUATION" or row["subjects_xyxy"]:
                    raise ValueError("Whole-scene control has unexpected subject transport")
            else:
                transforms = tracking.get("subjects", [])
                if tracking["tracking_status"] != "MEASURED_FORWARD_BACKWARD_FLOW" or len(transforms) != len(polygons):
                    raise ValueError("Semantic control lacks actual parent measured affines")
                for index, transform in enumerate(transforms):
                    if transform.get("geometry") != "PERSISTENT_GROUNDED_QUADRILATERAL":
                        raise ValueError("Old re-bounded tracker geometry cannot enter this control")
                    args = (transform["affine_thumbnail"], [width, height], transform["thumbnail_wh"])
                    pixel_polygons[index] = transport_polygon(pixel_polygons[index], *args)
                    if pixel_polygons[index] != transform["subject_polygon_xy"]:
                        raise ValueError("Parent affine does not reproduce its measured subject polygon")
                    polygons[index] = transport_polygon(polygons[index], *args)
        subjects = _visible_polygon_boxes(polygons, width, height)
        box, composition = crop_from_subjects(subjects, width, height, ratio, baseline_boxes[frame], config)
        predictions.append({"frame": frame, "bboxes": box})
        evidence.append({"frame": frame, "native_pts": row["native_pts"], "bboxes": box,
            "pixel_sha256": row["pixel_sha256"], "ground_anchor_frame": anchor_id,
            "ground_anchor_raw_sha256": row["ground_anchor_raw_sha256"],
            "semantic_polygon_xy": polygons, "visible_semantic_extents": subjects,
            "composition": composition, "parent_bbox": parent_prediction["bboxes"],
            "tracking_origin": "EXACT_PARENT_GRABCUT_SUBJECT_MEASURED_AFFINES",
            "new_neural_calls": 0, "new_independent_tracking": False})
        # Snapshot the nested polygon lists: later transport updates must not
        # mutate an already emitted frame's witness.
        polygons = [[list(point) for point in polygon] for polygon in polygons]
        previous = row
    if used_anchors != set(anchor_map):
        raise ValueError("Unused or foreign parent anchor in semantic control")
    return {"predictions": predictions, "spatial_evidence": evidence,
            "diagnostics": {"control": "RAW_SEMANTIC_EXTENT_WITH_PARENT_MEASURED_MOTION",
                "selected_frames": len(predictions), "changed_parent_boxes": sum(
                    a["bboxes"] != b["bboxes"] for a, b in zip(predictions, parent_predictions)),
                "new_neural_calls": 0, "new_independent_tracking": False,
                "config": asdict(config), "offline_quality_validation": "NOT_RUN", "official_quality": "UNKNOWN"}}
