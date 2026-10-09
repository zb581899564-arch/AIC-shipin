"""New PCHIP arithmetic only. No media/model/field I/O and no old-code edits."""
from bisect import bisect_left
from fractions import Fraction


def _integer(value, name):
    if type(value) is not int:
        raise ValueError(name + ' must be an exact integer')
    return value


def _slope(h_before, h_after, d_before, d_after):
    if d_before * d_after <= 0:
        return Fraction(0)
    w1, w2 = 2 * h_after + h_before, h_after + 2 * h_before
    return Fraction(w1 + w2) / (Fraction(w1) / d_before + Fraction(w2) / d_after)


def scalar(q, z, frame):
    """Exact four-support central value. Final integer rounding is caller-owned."""
    if len(q) != 4 or len(z) != 4:
        raise ValueError('exactly four consecutive planned supports required')
    for value in q + z:
        _integer(value, 'support')
    _integer(frame, 'frame')
    h0, h1, h2 = [b-a for a, b in zip(q, q[1:])]
    if not (1 <= h0 <= 8 and h1 == 8 and 1 <= h2 <= 8):
        raise ValueError('invalid four-support gap8 geometry')
    if not q[1] <= frame <= q[2]:
        raise ValueError('extrapolation forbidden')
    d0, d1, d2 = [Fraction(b-a, h) for a, b, h in zip(z, z[1:], [h0, h1, h2])]
    m1, m2 = _slope(h0, h1, d0, d1), _slope(h1, h2, d1, d2)
    u = Fraction(frame-q[1], h1)
    return ((2*u**3-3*u**2+1)*z[1] + (u**3-2*u**2+u)*h1*m1
            + (-2*u**3+3*u**2)*z[2] + (u**3-u**2)*h1*m2)


def legal_box(box, width, height, ratio):
    if len(box) != 3 or any(type(v) is not int for v in box):
        return False
    if any(type(v) is not int or v <= 0 for v in [width, height]):
        return False
    if len(ratio) != 2 or any(type(v) is not int or v <= 0 for v in ratio):
        return False
    x, y, w = box
    return x >= 0 and y >= 0 and w > 0 and x+w <= width and (y*ratio[0]+w*ratio[1] <= height*ratio[0])


def validate_shot(anchors, width, height, ratio):
    if not anchors or any(type(q) is not int or q < 0 for q in anchors):
        raise ValueError('invalid anchor ordinals')
    ordered = sorted(anchors)
    if any(not 1 <= b-a <= 8 for a,b in zip(ordered,ordered[1:])):
        raise ValueError('shot anchor gap outside original1..8 contract')
    if any(not legal_box(b,width,height,ratio) for b in anchors.values()):
        raise ValueError('illegal original anchor')
    widths = {b[2] for b in anchors.values()}
    expected_max_width = min(width, height*ratio[0]//ratio[1])
    if widths != {expected_max_width}:
        raise ValueError('original maximum constant width changed')
    return ordered


def interpolate(frame, anchors, width, height, ratio, old_interpolate):
    """Caller validates complete shot/source/identity first; callback is frozen old code.

    All original anchors and ordinary ineligible intervals call old code unchanged.
    This small primitive is not a source/provenance/strict pipeline acceptance.
    """
    _integer(frame,'frame')
    ordered=validate_shot(anchors,width,height,ratio)
    if frame in anchors:
        return old_interpolate(frame,anchors)
    i=bisect_left(ordered,frame)
    if i==0 or i==len(ordered):
        raise ValueError('frame outside planned anchors')
    if i<2 or i+1>=len(ordered) or ordered[i]-ordered[i-1]!=8:
        return old_interpolate(frame,anchors)
    q=ordered[i-2:i+2]
    xy=[round(scalar(q,[anchors[f][axis] for f in q],frame)) for axis in [0,1]]
    box=xy+[anchors[q[1]][2]]
    if not legal_box(box,width,height,ratio):
        raise ValueError('PCHIP integer result illegal; no clipping')
    return box,{'spatial_source':'SHOT_PCHIP_XY_ORDINAL_GAP8','support_ordinals':q,
                'left_anchor':q[1],'right_anchor':q[2],
                'left_distance':frame-q[1],'right_distance':q[2]-frame,
                'arithmetic':'FRACTION_FINAL_HALF_EVEN', 'algorithm':'spatial_gap8_pchip_slot4_v1'}


def box_iou(a,b,ratio):
    """Exact continuous geometry; target ratio is explicit, never default9:16."""
    if len(ratio)!=2 or any(type(v) is not int or v<=0 for v in ratio):
        raise ValueError('canonical positive integer target ratio required')
    for box in [a,b]:
        if len(box)!=3 or any(type(v) is not int for v in box) or box[2]<=0:
            raise ValueError('invalid box for exact IoU')
    x1,y1,w1=a; x2,y2,w2=b
    h1=Fraction(w1*ratio[1],ratio[0]);h2=Fraction(w2*ratio[1],ratio[0])
    iw=max(0,min(x1+w1,x2+w2)-max(x1,x2))
    ih=max(Fraction(0),min(y1+h1,y2+h2)-max(y1,y2))
    inter=iw*ih
    return inter/(w1*h1+w2*h2-inter)


def numeric_gate(group_deltas):
    """G2 numerical part only; G0/G1/G3 effect/strict/resource remain mandatory."""
    if len(group_deltas)!=8 or any(type(d) is not Fraction for d in group_deltas):
        raise ValueError('eight exact group deltas required')
    conf=group_deltas[2:]
    checks={'confirm_at_least4of6_positive':sum(d>0 for d in conf)>=4,
            'confirm_mean_positive':sum(conf)>0,'all8_mean_positive':sum(group_deltas)>0,
            'all_confirm_leave_one_means_nonnegative':all(sum(conf)-d>=0 for d in conf)}
    return dict(status='PASS_NUMERIC_ONLY' if all(checks.values()) else 'NO_426',checks=checks,
                quality='UNKNOWN',total_GO=False)
