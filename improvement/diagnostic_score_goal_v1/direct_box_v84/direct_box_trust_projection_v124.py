"""Fixed GT-free 9/10 Jaccard trust region; no artifact IO or scope actions.

Checks the actual final rectangles, including original XYWH4 height. This
does not establish mean gain, improvement count, controls, or official quality.
"""
from __future__ import annotations
import copy
from fractions import Fraction
import math
from numbers import Integral,Real
import direct_box_math_v84 as frozen84

GRID=1024
RECIPE=dict(grid_denominator=1024,grid_order='1024_DOWN_TO_1',threshold_numerator=9,threshold_denominator=10,
    direction='OBSERVED_B0_NATIVE_XYW_TO_FROZEN105_DIRECT_NATIVE_XYW',rounding='NEAREST_HALF_DOWN_THEN_FROZEN84_LEGAL_CLAMP',
    final_rectangle_checked=True,fallback='EXACT_ORIGINAL_BASELINE_ARRAY',GT_read=False,new_model_calls=0,
    monotonicity_assumed=False,new_fit=False)


def require(value,message):
    if not value:raise ValueError(message)


def _fraction(value):
    require(not isinstance(value,bool),'Boolean is not a rectangle coordinate')
    if isinstance(value,Fraction):return value
    if isinstance(value,Integral):return Fraction(int(value))
    require(isinstance(value,Real) and math.isfinite(float(value)),'Finite real rectangle coordinate')
    # Exact value of the parsed binary float; no decimal rounding or repair.
    return Fraction.from_float(float(value))


def rectangle_xywh(box,format):
    require(isinstance(box,(list,tuple)) and format in ('NATIVE_XYW3','XYWH4')
        and len(box)==(3 if format=='NATIVE_XYW3' else 4),'Explicit rectangle schema, never infer/drop original height')
    values=[_fraction(v) for v in box]
    if format=='NATIVE_XYW3':
        require(all(isinstance(v,Integral) and not isinstance(v,bool) for v in box),'Native3 coordinates are original integers')
        x,y,w=values;h=9*w/16
    else:x,y,w,h=values
    require(w>0 and h>0,'Positive rectangle area')
    return x,y,w,h


def exact_areas(first,second,*,first_format='NATIVE_XYW3',second_format='NATIVE_XYW3'):
    x,y,w,h=rectangle_xywh(first,first_format);u,v,r,s=rectangle_xywh(second,second_format)
    overlap=max(Fraction(0),min(x+w,u+r)-max(x,u))*max(Fraction(0),min(y+h,v+s)-max(y,v))
    union=w*h+r*s-overlap
    require(union>0,'Finite nonempty Jaccard union')
    return overlap,union


def exact_iou(first,second,*,first_format='NATIVE_XYW3',second_format='NATIVE_XYW3'):
    intersection,union=exact_areas(first,second,first_format=first_format,second_format=second_format)
    return intersection/union


def _rational(value):return dict(numerator=int(value.numerator),denominator=int(value.denominator))


def _round_half_down(value):
    whole,remainder=divmod(value.numerator,value.denominator)
    return int(whole+(2*remainder>value.denominator))


def _native_quantize(xyw,W,H):
    w=min(W,16*H//9,max(1,_round_half_down(xyw[2])))
    x=min(W-w,max(0,_round_half_down(xyw[0])))
    y=min((16*H-9*w)//16,max(0,_round_half_down(xyw[1])))
    result=[x,y,w];require(frozen84.legal_native(result,W,H),'Final integer candidate must pass frozen84 native legality')
    return result


def _box4(native):return [int(native[0]),int(native[1]),int(native[2]),float(Fraction(9*int(native[2]),16))]


def _certificate(output,baseline,output_format,baseline_format):
    intersection,union=exact_areas(output,baseline,first_format=output_format,second_format=baseline_format)
    iou=intersection/union;require(10*intersection>=9*union,'Actual final rectangle lies in the fixed exact9/10 trust region')
    return dict(intersection_area=_rational(intersection),union_area=_rational(union),iou=_rational(iou),
        threshold=dict(numerator=9,denominator=10),exact_comparison='10*intersection >= 9*union',
        comparison_left=_rational(10*intersection),comparison_right=_rational(9*union),threshold_passed=True,
        maximum_IoU_drop_for_any_same_measure_GT=_rational(1-iou),floating_IoU=float(iou),
        baseline_format=baseline_format,output_format=output_format,original_baseline_height_preserved_in_anchor=True,
        Jaccard_triangle_guarantee=True,other_quality_gates_established=False)


def project_trust_region(baseline,direct_box3,width,height,*,baseline_format='NATIVE_XYW3'):
    """Return largest admitted fixed grid k, or exact B0; never read targets.

    `box` has baseline_format. `box3` is None for a four-coordinate fallback
    whose original height cannot be represented by implicit9w/16. Use `box`.
    """
    W,H=frozen84.dimensions(width,height)
    require(frozen84.legal_native(direct_box3,W,H),'Only actual legal frozen105 DIRECT native3 proposal')
    x,y,w,h=rectangle_xywh(baseline,baseline_format)
    require(x>=0 and y>=0 and x+w<=W and y+h<=H,'Original baseline must be legal; never clip or repair it')
    if baseline_format=='NATIVE_XYW3':require(frozen84.legal_native(baseline,W,H),'Original native3 baseline strict legality')
    anchor=(x,y,w);direct=tuple(_fraction(v) for v in direct_box3);examined=0
    for k in range(GRID,0,-1):
        examined+=1
        candidate=_native_quantize(tuple((a*(GRID-k)+b*k)/GRID for a,b in zip(anchor,direct)),W,H)
        intersection,union=exact_areas(candidate,baseline,first_format='NATIVE_XYW3',second_format=baseline_format)
        if 10*intersection<9*union:continue
        box3=candidate;box4=_box4(candidate);output=box3 if baseline_format=='NATIVE_XYW3' else box4
        return dict(box=output,box3=box3,box4=box4,output_format=baseline_format,alpha_k=k,alpha_denominator=GRID,
            alpha=k/GRID,fallback=False,candidates_examined=examined,certificate=_certificate(output,baseline,baseline_format,baseline_format))
    output=copy.deepcopy(list(baseline))
    representable=(h==9*w/16 and all(v.denominator==1 for v in (x,y,w))
        and frozen84.legal_native([int(x),int(y),int(w)],W,H))
    box3=[int(x),int(y),int(w)] if representable else None
    box4=copy.deepcopy(output) if baseline_format=='XYWH4' else _box4(output)
    return dict(box=output,box3=box3,box4=box4,output_format=baseline_format,alpha_k=0,alpha_denominator=GRID,
        alpha=0.,fallback=True,candidates_examined=examined,certificate=_certificate(output,baseline,baseline_format,baseline_format))
