"""External-only EM diagnostic; never fit a prior on official inputs."""
import sys
from pathlib import Path
sys.path.insert(0,'/home/inspur/aic_video_work/calibrated_event_20261018_v1/code_v1')
from calibrate import *


def adjust_prior(p,source_prior,iterations=100):
    p=np.asarray(p,np.float64);rho=float(source_prior)
    require(p.ndim==1 and len(p)>0 and np.isfinite(p).all()and np.all((p>=0)&(p<=1))and 0<rho<1,'A calibrated binary field and nondegenerate source prior required')
    prior=rho;eps=np.finfo(np.float64).eps;likelihood=[]
    for _ in range(iterations):
        positive=p*prior/rho;negative=(1-p)*(1-prior)/(1-rho);den=positive+negative
        require((den>0).all(),'Finite nonzero likelihood denominator')
        posterior=positive/den
        likelihood.append(float(np.log(den).mean()))
        prior=float(np.clip(posterior.mean(),eps,1-eps))
    positive=p*prior/rho;negative=(1-p)*(1-prior)/(1-rho);posterior=positive/(positive+negative)
    require(np.isfinite(posterior).all()and np.all((posterior>=0)&(posterior<=1))and all(b>=a-1e-12 for a,b in zip(likelihood,likelihood[1:])),'Bounded posterior and nondecreasing registered EM likelihood')
    return posterior,dict(source_prior=rho,estimated_target_prior=prior,iterations=iterations,likelihood_initial=likelihood[0],likelihood_final=likelihood[-1],assumption='classconditional score distributions fixed; not proven for videos',target_labels_used=False)


def checks():
    p=np.array([.9,.9,.1,.1]);v,s=adjust_prior(p,.5);require(np.allclose(v,p),'Equal prior mixture fixed point')
    v,s=adjust_prior(np.full(8,.3),.3);require(np.allclose(v,.3),'Uninformative field must not invent density shift')
    v,s=adjust_prior(np.zeros(8),.3);require(np.array_equal(v,np.zeros(8)),'Actual zero field is legal zero posterior, not model failure')
    v,s=adjust_prior(np.ones(8),.3);require(np.array_equal(v,np.ones(8)),'Actual one field is legal posterior')
    v,s=adjust_prior(np.array([.05,.1,.2,.3]),.4);require(np.all(np.diff(v)>=0),'Prior adaptation preserves score ordering')
    save(ROOT/'prior_checks_02.json',dict(status='PASS5_TARGETED_EM_PRIOR_AND_NULL_CHECKS',utc=utc()))


def main():
    deadline();require(not(ROOT/'prior_adapted_02').exists(),'One fixed prior diagnostic only');checks()
    frozen=read(ROOT/'frozen_selection.json');m=dict(np.load(bound(frozen['weights_ref'])));reg=read(EVENT/'registration.json')
    # Source prior is the source-equal mean predicted posterior, matching its
    # calibration convention; PAVA preserves the same weighted empirical mean.
    means=[]
    for s in reg['sources']:
        if s['group']!='train':continue
        d=load_source(s,False);means.append(float(probability(d['score'],m)[d['groups']].mean()))
    rho=float(np.mean(means));require(abs(rho-float(m['rho_train']))<1e-12,'Training prior must mirror calibrated prediction mean')
    out=ROOT/'prior_adapted_02';out.mkdir()
    save(out/'frozen_selection.json',dict(status='FROZEN_EXTERNAL_ONLY_PRIOR_DIAGNOSTIC_ON_ONE_EXISTING_PAVA',production_admitted=False,official_input_prior_fit_allowed=False,lookup_weights_ref=frozen['weights_ref'],source_prior=rho,iterations=100,new_learned_parameters=0,protocol_ref=ref(ROOT/'prior_adaptation_protocol_02.json'),code_ref=ref(Path(__file__)),target_labels_used_by_adjustment=False,utc=utc()))
    items=[]
    for s in reg['sources']:
        if s['group']!='check':continue
        d=load_source(s);initial=probability(d['score'],m)[d['groups']];p,adaptation=adjust_prior(initial,rho);gain,stats=gains(d['baseline'],p,d['candidates'])
        idx=None if not len(gain)or gain.max()<=0 else int(gain.argmax())
        action=None if idx is None else dict(sid=s['sid'],candidate_index=idx,added_frames=d['candidates'][idx]['added_frames'],predicted_gain=float(gain[idx]))
        items.append(dict(d=d,p=p,adaptation=adaptation,action=action,gain=gain,stats=stats))
    budget=sum(int(v['d']['baseline'].sum())for v in items)//10;chosen=knapsack([v['action']for v in items if v['action']],budget);rows=[]
    for v in items:
        d=v['d'];mask=d['baseline'].copy();idx=None
        if d['sid']in chosen:idx=v['action']['candidate_index'];c=d['candidates'][idx];mask[c['left']:c['right']]=True
        b,n=metric(d['baseline'],d['labels']),metric(mask,d['labels']);vote=d['labels'].mean(1);added=mask&~d['baseline']
        rows.append(dict(sid=d['sid'],baseline=b,candidate=n,delta=n['f1']-b['f1'],added_frames=int(added.sum()),newframe_reviewer_precision=None if not added.any()else float(vote[added].mean()),chosen=None if idx is None else d['candidates'][idx],successful_source_null=v['action']is None,adaptation=v['adaptation'],true_selected_fraction_diagnostic_only=float(vote.mean()),brier=float(np.mean((v['p']-vote)**2)),historically_exposed=True))
        np.savez(out/(d['sid']+'_output.npz'),probability=v['p'],selected=mask,estimated_gain=v['gain'])
    summary=dict(sources=len(rows),macro_delta=float(np.mean([r['delta']for r in rows])),improved_sources=sum(v['delta']>0 for v in rows),decreased_sources=sum(v['delta']<0 for v in rows),successful_source_nulls=sum(v['successful_source_null']for v in rows),changed_sources=sum(v['added_frames']>0 for v in rows),added_frames=sum(v['added_frames']for v in rows),worst_delta=min(v['delta']for v in rows),macro_brier=float(np.mean([v['brier']for v in rows])))
    save(out/'evaluation.json',dict(status='ONE_FROZEN_PRIOR_SHIFT_DEVELOPMENT_DIAGNOSTIC',summary=summary,sources=rows,assumption_verified=False,no_new_blind_claim=True,no_parameter_search=True,utc=utc()))
    save(out/'completion.json',dict(status='COMPLETED_ONE_LABEL_FREE_PRIOR_ADAPTATION_DIAGNOSTIC',new_fit=0,new_GPU=0,evaluation_ref=ref(out/'evaluation.json'),utc=utc()))
    print(json.dumps(clean(summary)),flush=True)


if __name__=='__main__':
    try:main()
    except BaseException as e:save(ROOT/('prior_adaptation_failure_'+str(os.getpid())+'.json'),dict(error=repr(e),traceback=traceback.format_exc(),successes_preserved=True,utc=utc()));raise
