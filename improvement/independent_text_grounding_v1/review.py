"""Native-frame AP and structural query/temporal correspondence controls."""
import numpy as np
from common import ROOT,checked,grouped_ap,read,ref,write


def normalize(values):
    values=values.astype(np.float64)
    norms=np.linalg.norm(values,axis=-1,keepdims=True)
    assert np.all(norms>0)
    return values/norms


def source_scores(source,text):
    primary=read(ROOT/'outputs'/source['sid']/'acceptance.json')
    image=np.concatenate([np.load(checked(f),allow_pickle=False) for f in primary['files']])
    assert len(image)==source['native_cells']*8
    pooled=normalize(normalize(image).reshape(-1,8,512).mean(axis=1))
    scores=pooled@text.T
    assert np.isfinite(scores).all() and np.max(np.abs(scores))<=1.000001
    np.save(ROOT/'outputs'/source['sid']/'scores.npy',scores,allow_pickle=False)
    return scores


def main():
    inputs=read(ROOT/'input_acceptance.json')
    success=read(ROOT/'inference_completion.json')
    text=normalize(np.load(checked(success['text']),allow_pickle=False))
    rows=[]
    for i,source in enumerate(inputs['sources']):
        scores=source_scores(source,text)
        target=np.load(checked(source['target']),allow_pickle=False)
        counts=target['counts'];events=[]
        other=inputs['sources'][(i+1)%len(inputs['sources'])]['query_ids']
        ids=source['query_ids']
        for j,qid in enumerate(ids):
            values=dict(correct=scores[:,qid],within_query_swap=scores[:,ids[(j+1)%len(ids)]],
                        cross_video_query_swap=scores[:,other[j%len(other)]],
                        temporal_shift=np.roll(scores[:,qid],len(counts)//2))
            ap={key:grouped_ap(v,target['positive'][j],counts) for key,v in values.items()}
            assert all(v is not None for v in ap.values())
            ap['constant']=float(target['positive'][j].sum()/counts.sum())
            events.append(dict(query_id=qid,AP=ap))
        means={k:float(np.mean([e['AP'][k] for e in events])) for k in events[0]['AP']}
        rows.append(dict(sid=source['sid'],event_count=len(events),AP=means,events=events))
    macro={k:float(np.mean([r['AP'][k] for r in rows])) for k in rows[0]['AP']}
    gate=read(ROOT/'protocol.json')['gate']
    tests=dict(within=macro['correct']-macro['within_query_swap']>=gate['within_gain'],
               cross=macro['correct']-macro['cross_video_query_swap']>=gate['cross_gain'],
               content=macro['correct']-macro['temporal_shift']>=gate['shift_gain'],
               constant=macro['correct']-macro['constant']>=gate['constant_gain'],
               sources=sum(r['AP']['correct']>r['AP']['within_query_swap'] for r in rows)>=gate['sources'])
    write(ROOT/'review.json',dict(status='ELIGIBLE_FOR_SEPARATE_AUTOMATIC_QUERY_PILOT' if all(tests.values()) else 'STOP_FROZEN_SEMANTIC_GROUNDING',
              tests=tests,source_macro_AP=macro,sources=rows,
              human_query_positive_control_only=True,generic_highlight_quality_claim=False,
              wrong_text_semantically_false_claim=False,all_sources_historical_exposure=True,
              training_updates=0,automatic_query_test_run=False,production_allowed=False))


if __name__=='__main__':
    main()
