"""First whole-program versus fixed-B local preference diagnosis; CPU only."""
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys
import time


def ref(path):
    p=Path(path).resolve(strict=True);b=p.read_bytes()
    return dict(path=str(p),bytes=len(b),sha256=hashlib.sha256(b).hexdigest())


def main():
    n=Path(__file__).resolve().parent;w=n.parent.parent;started=time.monotonic()
    reg=json.loads((n/'registration33.json').read_text());assert reg['code_ref']==ref(__file__)
    def read(r):
        p=Path(r['path']).resolve(strict=True);assert p.is_relative_to(w) and ref(p)==r
        return json.loads(p.read_text())
    protocol=read(reg['protocol_ref']);previous=read(reg['completion32_ref'])
    root32=Path(reg['completion32_ref']['path']).parent
    reg32=read(ref(root32/'registration32.json'));assert ref(root32/'acceptable_program32_math.py')==reg32['math_ref']
    sys.path.insert(0,str(root32));from acceptable_program32_math import exact_utility
    # A valid disjoint-context example: remaining truth5, candidate1/1 or4/2.
    low=exact_utility(4,[2],[5])-exact_utility(1,[1],[5])
    high=exact_utility(8,[5],[5])-exact_utility(5,[4],[5])
    assert low==Fraction(1,9) and high==Fraction(-2,65)
    results=[]
    for r in previous['outputs']:
        inferred=read(r)
        if inferred['arm']!='real':continue
        target=read(inferred['target_ref']);gt=target['gt'];windows=target['windows']
        M=inferred['MAP']['choices'];G=inferred['highest_score_acceptable']['choices'];B=target['baseline_program']
        def total(program,skip=None):
            p=0;tp=[0]*len(gt)
            for i,(window,j)in enumerate(zip(windows,program)):
                if i==skip:continue
                group=window['groups'][j];p+=group['native_count'];tp=[a+b for a,b in zip(tp,group['TP'])]
            return p,tp
        def utility(program):
            p,tp=total(program);return exact_utility(p,tp,gt)
        assert str(utility(M))==inferred['MAP']['utility_fraction']
        assert str(utility(G))==inferred['highest_score_acceptable']['utility_fraction']
        def best_tokens(group,uid):
            vv=[]
            for v in group['variants']:
                if v['kind']=='OLD_ACCEPTED_SUFFIX':
                    slot=read(v['window_ref'])['slots'][v['slot']]
                    vv.append((v['original_real_logp'],len(slot['ids']),dict(kind=v['kind'],slot=v['slot'])))
                else:
                    source=read(v['source_noop_ref']);row=next(a for a in source['windows']if a['uid']==uid)
                    root31=Path(previous['completion31_ref']['path']).parent
                    score=read(ref(root31/(uid+'_scores31.json')))
                    vv.append((score['real'],len(row['suffix']),dict(kind=v['kind'])))
            return max(vv,key=lambda q:q[0])
        changed=[]
        for i,(mi,gi)in enumerate(zip(M,G)):
            if mi==gi:continue
            window=windows[i];a=window['groups'][mi];b=window['groups'][gi];deltas={}
            for name,context in [('fixed_B',B),('MAP_others',M),('gold_others',G)]:
                p,tp=total(context,skip=i)
                ua=exact_utility(p+a['native_count'],[u+v for u,v in zip(tp,a['TP'])],gt)
                ub=exact_utility(p+b['native_count'],[u+v for u,v in zip(tp,b['TP'])],gt)
                delta=ub-ua;deltas[name]=dict(delta=float(delta),exact=str(delta),sign=(delta>0)-(delta<0))
            ma=best_tokens(a,window['uid']);gb=best_tokens(b,window['uid'])
            signs={k:v['sign']for k,v in deltas.items()}
            changed.append(dict(uid=window['uid'],MAP_group=mi,gold_group=gi,native_delta_P=b['native_count']-a['native_count'],
                MAP_suffix_tokens=ma[1],gold_suffix_tokens=gb[1],delta_suffix_tokens=gb[1]-ma[1],
                MAP_variant=ma[2],gold_variant=gb[2],deltas=deltas,
                strict_direction_reversal=any(signs['fixed_B']*signs[k]<0 for k in ['MAP_others','gold_others']),
                fixed_B_tie_becomes_nonzero=signs['fixed_B']==0 and any(signs[k]!=0 for k in ['MAP_others','gold_others'])))
        results.append(dict(sid=target['sid'],role=target['cohort'],window_pairs=len(changed),
            strict_reversals=sum(v['strict_direction_reversal']for v in changed),
            fixed_B_ties_become_nonzero=sum(v['fixed_B_tie_becomes_nonzero']for v in changed),
            full_gold_minus_MAP=float(utility(G)-utility(M)),pairs=changed))
        assert time.monotonic()-started<protocol['maximum_CPU_seconds']
    assert len(results)==7
    summary={role:dict(sources=sum(v['role']==role for v in results),
        pair_count=sum(v['window_pairs']for v in results if v['role']==role),
        strict_reversals=sum(v['strict_reversals']for v in results if v['role']==role),
        sources_with_strict_reversal=sum(v['strict_reversals']>0 for v in results if v['role']==role),
        fixed_B_ties_become_nonzero=sum(v['fixed_B_ties_become_nonzero']for v in results if v['role']==role))for role in ['fit','process']}
    out=dict(status='COMPLETE_FULL_PROGRAM_COUPLING_NOVELTY_DIAGNOSTIC_ONLY',rows=results,summary=summary,
        completion32_ref=reg['completion32_ref'],seconds=time.monotonic()-started,analytic_context_fixture='PASS_EXACT_1over9_AND_minus2over65',
        unsupported_source='S23 retained B, zero comparisons, still fixed4 denominator if later metrics',
        interpretation='Strict reversals evidence context-dependent target differences from fixed-B local pairing; no reversal means no such evidence here. Token-length association is not a causal bias proof. Neither outcome admits training.',
        new_model_calls=0,new_updates=0,new_ZIP=0,official_submissions=0,automatic_training=False,production_admitted=False)
    with(n/'completion33.json').open('x')as f:json.dump(out,f,indent=2,allow_nan=False)
    print(json.dumps(dict(completion_ref=ref(n/'completion33.json'),receipt={k:v for k,v in out.items()if k!='rows'})))


if __name__=='__main__':main()
