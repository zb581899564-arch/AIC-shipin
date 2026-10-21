"""First all-alternative native MAP-boundary diagnostic of existing20/23."""
import hashlib
import json
from pathlib import Path
import time


def ref(p):
    p=Path(p).resolve(strict=True);b=p.read_bytes();return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())


def main():
    import numpy as np
    from boundary_margin26_math import diagnose
    N=Path(__file__).resolve().parent;R=N.parent;W=R.parent;started=time.monotonic()
    reg=json.loads((N/'registration26.json').read_text());assert reg['code_ref']==ref(__file__)
    def read(r):
        p=Path(r['path']).resolve(strict=True);assert p.is_relative_to(W)and ref(p)==r;return json.loads(p.read_text())
    protocol=read(reg['protocol_ref']);done20=read(reg['gpu20_ref']);a20=read(reg['acceptance20_ref']);targets20=read(a20['target_ref'])
    done23=read(reg['gpu23_ref']);a23=read(reg['acceptance23_ref']);cases23=read(a23['cases_ref']);targets23=read(a23['targets_ref'])
    scores23={r['uid']:r for v in done23['score_refs']for r in [read(v)]}
    reports20={r['sid']:r for r in done20['source_reports']};rows=[]
    for group,targets in [('fit',targets20['sources']),('process',targets23)]:
        for t in targets:
            sid=t['sid'];windows=t['windows'];actions=[]
            for w in windows:
                c=w if group=='fit'else cases23[w['uid']];old=read(c['window_ref'])
                assert old['source_sha256']==t['source_sha256']and old['labels_read']is False
                actions.append([old['slots'][j]['selected_ordinals']for j in c['slots']])
            metrics={}
            for arm in (['real']if group=='fit'else['real','shifted']):
                if group=='fit':before=reports20[sid]['logits0'];after=reports20[sid]['logits1']
                else:before=[cases23[w['uid']]['original_'+arm]for w in windows];after=[scores23[w['uid']][arm]for w in windows]
                metrics[arm]=diagnose(actions,[w['lengths']for w in windows],[w['overlap']for w in windows],before,after,t['gt'])
            rows.append(dict(sid=sid,group=group,metrics=metrics))
    held=[r for r in rows if r['group']=='process'];assert{r['sid']for r in held}=={'S02','S06','S08','S23'}
    macro={arm:dict(alignment=float(np.mean([r['metrics'][arm]['mean_utility_weighted_margin_alignment']for r in held])),
        positive_sources=sum(r['metrics'][arm]['mean_utility_weighted_margin_alignment']>1e-6 for r in held),
        beneficial_source_count=sum(r['metrics'][arm]['beneficial_swaps']>0 for r in held),
        beneficial_closer=sum(r['metrics'][arm]['beneficial_closer']for r in held),beneficial_farther=sum(r['metrics'][arm]['beneficial_farther']for r in held))for arm in ['real','shifted']}
    real=macro['real'];reasons=[]
    if real['alignment']<=1e-6:reasons.append('NO_POSITIVE_REAL_MAP_BOUNDARY_ALIGNMENT')
    if real['positive_sources']<3:reasons.append('FEWER_THAN3_POSITIVE_REAL_SOURCES')
    if real['alignment']<=macro['shifted']['alignment']+1e-6:reasons.append('NO_REAL_OVER_SHIFTED_BOUNDARY_ADVANTAGE')
    if real['beneficial_source_count']<3:reasons.append('FEWER_THAN3_SOURCES_WITH_BENEFICIAL_ALTERNATIVES')
    summary=dict(status='STOP_EXISTING_SINGLE_STEP_RISK_CONTINUATION_MARGIN_DIRECTION'if reasons else'ELIGIBLE_FOR_SEPARATE_SAME_PROGRAM_MAP_CONTINUATION_REVIEW_ONLY',
        stop_reasons=reasons,process_macro=macro,rows=rows,seconds=time.monotonic()-started,new_model_calls=0,new_updates=0,new_fits=0,new_ZIP=0,official_submissions=0,
        no_GPU_admission=True,actual_changed_selection_not_measured_again=True)
    assert summary['seconds']<protocol['maximum_CPU_seconds']
    with(N/'completion26.json').open('x')as f:json.dump(summary,f,indent=2,allow_nan=False)
    short={k:v for k,v in summary.items()if k!='rows'};short['per_source']=[dict(sid=r['sid'],group=r['group'],metrics={a:{k:v for k,v in m.items()if k!='rows'}for a,m in r['metrics'].items()})for r in rows]
    print(json.dumps(dict(completion_ref=ref(N/'completion26.json'),summary=short)))


if __name__=='__main__':main()
