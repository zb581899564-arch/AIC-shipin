"""Fixed bidirectional native-frame transport, with exact original box control.

This checks geometric self-consistency only. Hidden model centers never enter
transport, and neither flow agreement nor a hidden center is human crop truth.
"""
import math


def geometry(width, height):
    assert type(width) is int and type(height) is int and min(width, height) > 0
    cw = min(width, max(1, int(math.floor(height * 9 / 16 + 1e-12))))
    while cw > 1 and cw * 16 > height * 9:
        cw -= 1
    return cw, cw * 16 / 9


def box(center, width, height):
    assert len(center) == 2 and all(math.isfinite(x) and 0 <= x <= 1 for x in center)
    cw, ch = geometry(width, height)
    x = int(round(max(0., min(center[0] * width - cw / 2, float(width - cw)))))
    ymax = max(0, int(math.floor(height - ch + 1e-9)))
    y = int(round(max(0., min(center[1] * height - ch / 2, float(ymax)))))
    return [min(x, width - cw), min(y, ymax), cw]


def linear_control(left, right, width, height):
    """Original p2j_core: interpolate already clamped integer anchor triplets."""
    a, b = box(left, width, height), box(right, width, height)
    return [[int(round(float(a[j]) + (k / 8) * (float(b[j]) - float(a[j]))))
             for j in range(3)] for k in range(9)]


def _track(images, start, crop_normalized):
    import cv2
    import numpy as np
    assert images.dtype == np.uint8 and images.ndim == 3 and len(images) == 9
    h, w = images.shape[1:]
    mask = np.zeros((h, w), np.uint8)
    # Central third of the actual maximum legal crop, centered on raw subject.
    half = np.array(crop_normalized) * np.array([w, h]) / 6
    center = np.array(start) * np.array([w, h])
    low = np.maximum(0, np.floor(center - half).astype(int))
    high = np.minimum([w, h], np.ceil(center + half).astype(int) + 1)
    mask[low[1]:high[1], low[0]:high[0]] = 255
    pts = cv2.goodFeaturesToTrack(images[0], maxCorners=64, qualityLevel=.01,
                                 minDistance=3, mask=mask, blockSize=7)
    if pts is None or len(pts) < 8:
        return None, dict(reason='INSUFFICIENT_START_FEATURES', count=0 if pts is None else len(pts))
    path = [np.array(start, dtype=np.float64)]
    counts = []
    options = dict(winSize=(21, 21), maxLevel=3,
                   criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 30, .01))
    for k in range(8):
        nxt, good, _ = cv2.calcOpticalFlowPyrLK(images[k], images[k + 1], pts, None, **options)
        if nxt is None or good is None:
            return None, dict(reason='FORWARD_LK_FAILED', transition=k)
        back, backgood, _ = cv2.calcOpticalFlowPyrLK(images[k + 1], images[k], nxt, None, **options)
        if back is None or backgood is None:
            return None, dict(reason='BACKWARD_LK_FAILED', transition=k)
        good = (good[:, 0] != 0) & (backgood[:, 0] != 0)
        good &= np.isfinite(nxt).all(axis=(1, 2)) & np.isfinite(back).all(axis=(1, 2))
        good &= np.linalg.norm(back[:, 0] - pts[:, 0], axis=1) <= 1.
        good &= (nxt[:, 0, 0] >= 0) & (nxt[:, 0, 0] < w) & (nxt[:, 0, 1] >= 0) & (nxt[:, 0, 1] < h)
        counts.append(int(good.sum()))
        if good.sum() < 8:
            return None, dict(reason='INSUFFICIENT_BIDIRECTIONAL_FEATURES', transition=k, counts=counts)
        displacement = np.median((nxt[good, 0] - pts[good, 0]).astype(np.float64), axis=0)
        path.append(path[-1] + displacement / np.array([w, h]))
        pts = nxt[good].copy()
    return np.array(path), dict(reason='TRACK_COMPLETE', counts=counts)


def transport(images, left, right, width, height):
    """Endpoints only; no hidden image model output is accepted by this API."""
    import numpy as np
    control = linear_control(left, right, width, height)
    cw, ch = geometry(width, height)
    crop = np.array([cw / width, ch / height])
    forward, forward_report = _track(images, left, crop)
    backward, backward_report = _track(images[::-1].copy(), right, crop)
    report = dict(forward=forward_report, backward=backward_report,
                  hidden_center_used=False, native_interval=8, frame_count=9)
    if forward is None or backward is None:
        return dict(status='EXACT_ORIGINAL_LINEAR_FALLBACK', boxes=control,
                    control_boxes=control, **report)
    backward = backward[::-1].copy()
    residual_f = np.array(right) - forward[-1]
    residual_b = np.array(left) - backward[0]
    residuals = [float(np.linalg.norm(residual_f / crop)), float(np.linalg.norm(residual_b / crop))]
    report['endpoint_residual_crop_norm'] = residuals
    if max(residuals) > .25:
        return dict(status='EXACT_ORIGINAL_LINEAR_FALLBACK', reason='ENDPOINT_RESIDUAL',
                    boxes=control, control_boxes=control, **report)
    output = []
    for k in range(9):
        u = k / 8
        corrected_f = forward[k] + u * residual_f
        corrected_b = backward[k] + (1 - u) * residual_b
        transported_raw = (1 - u) * corrected_f + u * corrected_b
        raw_linear = (1 - u) * np.array(left) + u * np.array(right)
        # Preserve the *original* integer/clamped path when pixels provide no
        # nonlinear motion. Raw-linear-then-clamp is a different old baseline.
        control_center = np.array([(control[k][0] + cw / 2) / width,
                                   (control[k][1] + ch / 2) / height])
        proposed = np.clip(control_center + transported_raw - raw_linear, 0, 1)
        output.append(box(proposed.tolist(), width, height))
    assert output[0] == control[0] and output[-1] == control[-1]
    return dict(status='BIDIRECTIONAL_NATIVE_MOTION_TRANSPORT', boxes=output,
                control_boxes=control, **report)


def normalized_center_error(candidate, reference, height):
    assert candidate[2] == reference[2] > 0
    cw = candidate[2]
    ch = cw * 16 / 9
    return math.hypot((candidate[0] - reference[0]) / cw,
                      (candidate[1] - reference[1]) / ch)
