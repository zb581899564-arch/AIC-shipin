"""Three fixed, label-free trajectory hypotheses on original model anchors."""
from bisect import bisect_right
from fractions import Fraction
import math
import statistics

POLICIES = ('pchip', 'median3', 'shot_representative')


def groups(rows):
    ordered = sorted(rows, key=lambda r: (r['video_id'], r['source_frame']))
    current, previous = [], None
    for row in ordered:
        key = row['video_id'], row['source_frame']
        if current and (row['is_shot_start'] or key[0] != previous[0] or key[1] != previous[1] + 1):
            yield current
            current = []
        current.append(row)
        previous = key
    if current:
        yield current


def _endpoint(h0, h1, d0, d1):
    slope = ((2 * h0 + h1) * d0 - h0 * d1) / (h0 + h1)
    if slope * d0 <= 0:
        return 0.0
    if d0 * d1 < 0 and abs(slope) > 3 * abs(d0):
        return 3 * d0
    return slope


def pchip_slopes(times, values):
    if len(times) != len(values) or not times or any(b <= a for a, b in zip(times, times[1:])):
        raise ValueError('Strict chronological real native knots required')
    if len(times) == 1:
        return [0.0]
    h = [b-a for a, b in zip(times, times[1:])]
    d = [(b-a)/gap for a, b, gap in zip(values, values[1:], h)]
    if len(times) == 2:
        return [d[0], d[0]]
    slopes = [_endpoint(h[0], h[1], d[0], d[1])]
    for i in range(1, len(times)-1):
        if d[i-1] * d[i] <= 0:
            slopes.append(0.0)
        else:
            w1, w2 = 2*h[i] + h[i-1], h[i] + 2*h[i-1]
            slopes.append((w1+w2)/(w1/d[i-1]+w2/d[i]))
    slopes.append(_endpoint(h[-1], h[-2], d[-1], d[-2]))
    return slopes


def sample_curve(times, values, slopes, t):
    if len(times) == 1:
        return values[0]
    i = max(0, min(len(times)-2, bisect_right(times, t)-1))
    h = times[i+1]-times[i]
    u = (t-times[i])/h
    if not -1e-9 <= u <= 1+1e-9:
        raise ValueError('No trajectory extrapolation across shot boundaries')
    value = ((2*u**3-3*u**2+1)*values[i] + (u**3-2*u**2+u)*h*slopes[i]
             + (-2*u**3+3*u**2)*values[i+1] + (u**3-u**2)*h*slopes[i+1])
    lo, hi = sorted((values[i], values[i+1]))
    if value < lo-1e-7 or value > hi+1e-7:
        raise ValueError('Shape-preserving curve overshot its real anchor envelope')
    return min(hi, max(lo, value))


class ShotTrajectory:
    def __init__(self, frames, anchors, pts):
        self.frames = sorted(f for f in frames if f in anchors)
        if not self.frames or self.frames[0] != frames[0] or self.frames[-1] != frames[-1]:
            raise ValueError('Original complete same-shot endpoint anchors required')
        self.boxes = [anchors[f]['box_xyw'] for f in self.frames]
        self.original = dict(zip(self.frames, self.boxes))
        if len({box[2] for box in self.boxes}) != 1:
            raise ValueError('These recipes require the original unchanged same-shot width')
        self.times = [float(pts[f]) for f in self.frames]
        self.xy = [[float(b[k]) for b in self.boxes] for k in (0, 1)]
        self.slopes = [pchip_slopes(self.times, axis) for axis in self.xy]
        self.filtered = [[statistics.median([axis[max(0, i-1)], axis[i], axis[min(len(axis)-1, i+1)]])
                          for i in range(len(axis))] for axis in self.xy]
        median = [statistics.median(axis) for axis in self.xy]
        self.representative = min(range(len(self.frames)),
            key=lambda i: (abs(self.xy[0][i]-median[0])+abs(self.xy[1][i]-median[1]), self.frames[i]))

    def sample(self, policy, frame, t, baseline, source):
        if policy not in POLICIES:
            raise ValueError('Unregistered policy')
        if baseline[2] != self.boxes[0][2]:
            raise ValueError('Protected per-frame crop width cannot change')
        if policy == 'pchip':
            if frame in self.original:
                xy = self.original[frame][:2]
            else:
                xy = [sample_curve(self.times, axis, slope, float(t)) for axis, slope in zip(self.xy, self.slopes)]
        elif policy == 'median3':
            j = max(0, min(len(self.times)-2, bisect_right(self.times, float(t))-1))
            if len(self.times) == 1:
                xy = [axis[0] for axis in self.filtered]
            else:
                u = (float(t)-self.times[j])/(self.times[j+1]-self.times[j])
                if not -1e-9 <= u <= 1+1e-9:
                    raise ValueError('Median interpolation would cross a shot')
                xy = [axis[j]+u*(axis[j+1]-axis[j]) for axis in self.filtered]
        else:
            xy = self.boxes[self.representative][:2]
        width = baseline[2]
        max_x = source['width']-width
        max_y = math.floor(Fraction(source['height'])-Fraction(str(width))*source['targetRatioWH'][1]/source['targetRatioWH'][0])
        # Integer-origin placement, explicitly bounded by the unchanged native crop dimensions.
        return [min(max_x, max(0, int(round(xy[0])))), min(max_y, max(0, int(round(xy[1])))), width]
