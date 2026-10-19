"""Non-running original geometry helper; not used by the602 exploration pipeline.

The original20 screen zero-box helper remains available for a future separately
authorized geometry audit. No screen data or score is read by current stages.
"""
import math
from width_common import require


def strict_geometry(width_value,W,H,center):
    require(type(width_value) is int and 1 <= width_value <= 1000,'width grammar')
    require(type(W) is int and type(H) is int and min(W,H)>0,'Original source dimensions')
    require(len(center) == 2 and all(type(v) in (float,int) and math.isfinite(v) and 0<=v<=1 for v in center),'Accepted normalized center')
    width = max(1,min(W,H*16//9)*width_value//1000)
    left = round(min(max(center[0]*W-width/2,0),W-width))
    top = round(min(max(center[1]*H-width*9/32,0),max(0,math.floor(H-width*9/16+1e-9))))
    result = [int(left),int(top),width]
    require(legal(result,W,H),'Illegal crop geometry')
    return result


def legal(box,W,H):
    return (isinstance(box,(list,tuple)) and len(box)==3 and all(type(x) is int for x in box) and
            box[0]>=0 and box[1]>=0 and box[2]>=1 and box[0]+box[2]<=W and box[1]+box[2]*9/16<=H+1e-9)


def overlap(candidate,reference):
    x,y,w = candidate; h = w*9/16; u,v,p,q = reference
    require(all(type(z) in (float,int) and math.isfinite(z) for z in reference) and p>0 and q>0,'Original reference XYWH')
    area = max(0,min(x+w,u+p)-max(x,u))*max(0,min(y+h,v+q)-max(y,v))
    return area/(w*h+p*q-area)


def zero_geometry_rows(items,old_predictions):
    old = {row['item_id']:row for row in old_predictions}
    screen = [row for row in items if row['role']=='screen']
    require(len(screen)==20 and len(old)==len(old_predictions)==20 and set(old)=={x['item_id'] for x in screen},'Exact20 successful original screen baselines')
    rows = []
    for item in screen:
        base = old[item['item_id']]
        actual = strict_geometry(1000,item['width'],item['height'],base['center'])
        rows.append(dict(item_id=item['item_id'],expected=base['baseline_box'],actual=actual,equal=actual==base['baseline_box']))
    return rows
