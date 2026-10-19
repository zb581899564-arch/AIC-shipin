"""Targeted exact-time, marginal-quality, budget, and persistence checks."""
from event_common import *
from event_features import *
import io


def clock(n=80,step=F(1,8)):
    return dict(normalized_exact_pts=[str(i*step) for i in range(n)],physical_end_exact=str(n*step))


def run():
    cpu();passed=[]
    c=clock();b=np.zeros(80,bool);p=proposals(c,b)
    require(len(p)>0 and all(F(x['added_duration_exact'])>=2 for x in p),'True multi-second actions')
    require(any(x['start_exact']=='8' and x['end_exact']=='10' for x in p),'Physical tail covered without padding')
    passed.append('exact_native_proposals_and_tail')
    holes=np.ones(80,bool);holes[20:22]=False
    require(proposals(c,holes)==[],'Tiny holes do not become multi-second events')
    passed.append('tiny_action_exclusion')
    mask=np.ones(80,bool);mask[16:32]=False;p=proposals(c,mask)
    require(len(p)==1 and p[0]['start_exact']=='2' and p[0]['duration_exact']=='2','Stable shortest envelope dedup')
    passed.append('membership_dedup_representative')
    inside=np.ones(80,bool);inside[20]=False
    require(proposals(c,mask,inside)==[],'One unavailable new frame rejects entire action')
    passed.append('whole_proposal_field_eligibility')
    rng=np.random.default_rng(7);labels=rng.random((80,3))<.3;labels[:,2]=False
    quality,gain=targets(mask,labels,p)
    union=mask.copy();union[p[0]['left']:p[0]['right']]=True
    delta=metric(union,labels)['f1']-metric(mask,labels)['f1']
    require(abs(gain[0]-delta)<1e-12 and -.5<=quality[0]<=1,'Full all-rater non-linear set gain')
    passed.append('exact_marginal_quality_with_empty_reviewer')
    components=np.zeros((32,4096));components[np.arange(32),np.arange(32)]=1
    pca=dict(pca_components=components,pca_mean=np.zeros(4096))
    language=rng.normal(size=(20,4096));groups=np.repeat(np.arange(20),4);score=rng.normal(size=20)
    x=descriptors(language,score,groups,c,mask,pca,p)
    raw=projected(language,pca)[groups[16:32]]
    require(x.shape==(1,102)and np.allclose(x[0,:32],raw.mean(0))and np.allclose(x[0,64:96],raw.std(0)),'Actual native-weighted descriptor')
    passed.append('weighted_descriptor_independent_scalar_check')
    actions=[dict(sid='a',added_frames=4,predicted_gain=5.),dict(sid='b',added_frames=3,predicted_gain=4.),dict(sid='c',added_frames=2,predicted_gain=3.)]
    require(knapsack(actions,5)=={'b','c'} and knapsack(actions,0)==set(),'Indivisible true-frame budget')
    passed.append('native_budget_backtracking')
    model=dict(pca_mean=np.zeros(4096),pca_components=components,mean=np.zeros(102),std=np.ones(102),coef=np.zeros(102),bias=np.asarray(-.1),rho_train=np.asarray(.2))
    best,q,g=rank(x,p,mask,model);require(best is None,'Successful explicit null selection')
    stream=io.BytesIO();np.savez(stream,**model);stream.seek(0);restored=dict(np.load(stream));require(all(np.array_equal(v,restored[k])for k,v in model.items()),'Model tensor persistence')
    passed.append('null_and_tensor_persistence')
    try:event('NO_WRITE_TEST',utc='duplicate')
    except ValueError:pass
    else:raise ValueError('Post-completion timestamp collision not rejected')
    passed.append('duplicate_timestamp_rejected_before_journal')
    save(ROOT/'targeted_checks.json',dict(status='PASS_EVENT_LEVEL_TARGETED_CHECKS',checks=passed,utc=utc()))
    print(json.dumps(dict(status='PASS',checks=len(passed))))


if __name__=='__main__':
    try:run()
    except BaseException as error:failure('event_checks',error);raise
