"""One-to-one temporal event matching; threshold is local diagnostic, not official."""
from fractions import Fraction as F
from quality_contract import duration,measure,normalize

def event_iou(a,b):
    x=measure(a,b);u=duration(a)+duration(b)-x
    if not u:raise ValueError('Empty event cannot be matched')
    return x/u

def match_events(reference_events,predicted_events,threshold=F('0.5')):
    """Max cardinality, then total exact IoU, then lexicographic stable assignment.

    Each event is an interval list restricted to the two declared source domains.
    Diagnostic references retain difficult supported events, even if not trainable.
    """
    refs=[normalize(x) for x in reference_events];preds=[normalize(x) for x in predicted_events]
    if any(not x for x in refs+preds):raise ValueError('Empty event')
    # The fixed grammar supplies at most ten predicted events across two windows.
    if len(preds)>10:raise ValueError('Two-window prediction grammar violated')
    dp={0:(F(0),())}
    for r,ref in enumerate(refs):
        nxt=dict(dp)
        for used,(score,pairs) in dp.items():
            for p,pred in enumerate(preds):
                if used>>p&1:continue
                iou=event_iou(ref,pred)
                if iou<threshold:continue
                key=used|(1<<p);candidate=(score+iou,pairs+((r,p),))
                old=nxt.get(key)
                if old is None or candidate[0]>old[0] or (candidate[0]==old[0] and candidate[1]<old[1]):nxt[key]=candidate
        dp=nxt
    used,(score,pairs)=min(dp.items(),key=lambda item:(-item[0].bit_count(),-item[1][0],item[1][1]))
    details=[]
    for r,p in pairs:
        ref,pred=refs[r],preds[p]
        details.append(dict(reference_index=r,prediction_index=p,iou=event_iou(ref,pred),
            signed_start_error=pred[0][0]-ref[0][0],signed_end_error=pred[-1][1]-ref[-1][1]))
    return dict(reference_events=len(refs),predicted_events=len(preds),matched_events=len(pairs),
        event_recall=F(len(pairs),len(refs)) if refs else None,matches=details,
        local_diagnostic_threshold=threshold,official_threshold_claimed=False,
        unmatched_reference_indices=[i for i in range(len(refs)) if i not in {r for r,p in pairs}])

if __name__=='__main__':
    import json
    # Two overlapping predictions need a reassignment to achieve two matches.
    r=match_events([[(0,2)],[(1,3)]],[[(0,3)],[(0,2)]])
    assert r['matched_events']==2 and [(x['reference_index'],x['prediction_index']) for x in r['matches']]==[(0,1),(1,0)]
    assert match_events([[(0,1)],[(2,3)]],[[(0,3)]])['matched_events']==0
    assert match_events([],[])['event_recall'] is None
    print(json.dumps(dict(status='PASS_ONE_TO_ONE_REASSIGNMENT_AND_EMPTY_DENOMINATOR',new_model_calls=0,new_optimizer_updates=0)))
