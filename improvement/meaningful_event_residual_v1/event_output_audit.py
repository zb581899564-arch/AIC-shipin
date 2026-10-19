"""First independent decision-policy audit, no fit, media or old model calls."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
os.environ.setdefault('OPENBLAS_NUM_THREADS','2')
import sys,zipfile
from pathlib import Path
ROOT=Path('/home/inspur/aic_video_work/meaningful_residual_20261018_v1')
sys.path.insert(0,str(ROOT/'code_v1'))
from event_common import *
import numpy as np


def independent_memory(z,m):
    diff=m['bank']-z
    distance=np.einsum('ij,ij->i',diff,diff)
    reps=[]
    for source in sorted(set(map(int,m['source_codes']))):
        indexes=np.flatnonzero(m['source_codes']==source);idx=int(indexes[np.argmin(distance[indexes])]);reps.append((float(distance[idx]),source,float(m['target'][idx])))
    reps=sorted(reps,key=lambda v:(v[0],v[1]))[:5]
    zero=[v for v in reps if v[0]==0]
    if zero:return sum(v[2]for v in zero)/len(zero)
    weights=[1/(v[0]+1e-8)for v in reps]
    return sum(w*v[2]for w,v in zip(weights,reps))/sum(weights)


def main(name):
    cpu();out=ROOT/'packages'/name;completion=read(out/'completion.json')
    frozen=read(bound(completion['selection_ref']));model=dict(np.load(bound(frozen['weights_ref'])))
    inference=read(out/'inference_completion.json');decisions={v['sid']:v for v in inference['decisions']}
    expected=set();actions=[];chosen_value=0.;chosen_cost=0;queries=0;items=[]
    with zipfile.ZipFile(bound(read(ROOT/'registration.json')['baseline_ref']))as z:base=[json.loads(v)for v in z.read('predictions.jsonl').splitlines()]
    baseline={(r['video_id'],p['frame'])for r in base for p in r['predictions']};expected.update(baseline)
    for receipt in read(ROOT/'formal_inputs_01/completion.json')['sources']:
        r=read(bound(receipt));sid=r['sid'];d=np.load(bound(r['input_ref']));x=d['x'];b=d['baseline'];c=r['candidates'];v=np.load(out/(sid+'_output.npz'));q=v['predicted_quality'];gain=v['estimated_gain'];k=np.asarray([p['added_frames']for p in c],float)
        require(q.shape==gain.shape==(len(c),)and np.isfinite(q).all()and np.isfinite(gain).all(),'Complete finite source outputs, zero actions not execution failure')
        if name=='SEMANTIC_EVENT_RANK':
            require(np.array_equal(q,x[:,96]),'All source semantic scores equal original frozen descriptor')
            expected_gain=1/(1+np.exp(-np.clip(x[:,96],-30,30)));best=None if not len(q)else int(np.argmax(q));queries+=len(q)
        else:
            expected_gain=2*k*q/(int(b.sum())+k+len(b)*float(model['rho_train']));best=None if not len(q)or gain.max()<=0 else int(np.argmax(gain))
            if name=='EVENT_AUDIO_VISUAL':
                a=read(ROOT/'formal_audio_01'/(sid+'.json'));ax=np.load(bound(a['input_ref']))['x'];x=np.concatenate([x,ax],1)
                direct=np.clip(np.einsum('ij,j->i',(x-model['mean'])/model['std'],model['coef'])+float(model['bias']),-.5,1.)
                require(np.allclose(q,direct,atol=2e-11,rtol=2e-11),'All audiovisual head rows independently recomputed');queries+=len(q)
            else:
                indices=sorted({0,len(q)//2,len(q)-1}|({best}if best is not None else set()))if len(q)else[]
                for index in indices:
                    direct=independent_memory((x[index]-model['mean'])/model['std'],model)
                    require(abs(float(q[index])-direct)<2e-11,'Independent2D all-bank source-balanced neighbour numeric check')
                    queries+=1
        require(np.allclose(gain,expected_gain,atol=2e-12,rtol=2e-12),'All estimated gain/value rows match registered policy')
        if best is not None:actions.append((sid,int(k[best]),float(gain[best])))
        chosen=decisions[sid]['chosen']
        if chosen is not None:
            require(best is not None and chosen==c[best],'Published action exactly registered source argmax')
            chosen_value+=float(gain[best]);chosen_cost+=int(k[best]);expected.update((sid,i)for i in range(chosen['left'],chosen['right']))
        items.append(dict(sid=sid,proposal_rows=len(c),source_argmax=best,actually_selected=chosen is not None))
    # Separate two-array DP, no call to production knapsack/backtracking.
    budget=len(baseline)//10;dp=np.zeros(budget+1)
    for sid,cost,value in actions:
        if cost>budget:continue
        old=dp.copy();dp[cost:]=np.maximum(old[cost:],old[:-cost]+value)
    require(abs(chosen_value-float(dp[-1]))<2e-10 and chosen_cost<=budget,'Actual chosen source actions achieve registered0/1 optimum within guard')
    with zipfile.ZipFile(bound(completion['zip']))as z:rows=[json.loads(v)for v in z.read('predictions.jsonl').splitlines()]
    actual={(r['video_id'],p['frame'])for r in rows for p in r['predictions']}
    require(actual==expected and len(actual)-len(baseline)==chosen_cost==completion['added_frames'],'Published ZIP exactly baseline union complete source actions')
    require(8782459120+98329+sum(v.size for v in model.values())==completion['actual_resident_parameters']<=9_000_000_000,'Whole active model/preprocessor inventory')
    report=dict(status='PASS_FIRST_INDEPENDENT426_OUTPUT_POLICY_NATIVE_UNION_AND_PARAMETER_QA',mechanism=name,source_count=len(items),numeric_queries_checked=queries,numeric_check_scope='allsemantic_rows'if name=='SEMANTIC_EVENT_RANK'else'all_audio_visual_rows'if name=='EVENT_AUDIO_VISUAL'else'first_middle_last_and_argmax_each_nonempty_source_independent2D_allbank',all_source_finite_and_gain_mapping=True,independent_global_budget_optimality=True,published_native_set_exact=True,package_completion_ref=ref(out/'completion.json'),code_ref=ref(Path(__file__)),sources=items,utc=utc())
    save(out/'output_qa.json',report);print(json.dumps({k:v for k,v in report.items()if k!='sources'}),flush=True)


if __name__=='__main__':
    try:main(sys.argv[1])
    except BaseException as e:failure('first_event_output_QA_'+sys.argv[1],e);raise
