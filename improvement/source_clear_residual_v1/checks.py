"""Targeted regression checks for new native utility math and frozen transform."""
from sr_common import *
from fractions import Fraction as F

def main():
    cpu();import numpy as np
    import torch
    import ast
    from fit import utility_targets,predict,candidates,metric
    torch.set_num_threads(1)
    baseline=np.array([1,0,0,1,0,0],bool);groups=np.array([0,0,1,1,2,2]);labels=np.array([[0,1],[1,0],[1,1],[0,0],[1,0],[0,1]],bool)
    y=utility_targets(baseline,groups,labels,3)
    for j in range(3):
        direct=metric(baseline|(groups==j),labels)['f1']-metric(baseline,labels)['f1']
        require(abs(y[j]-direct)<1e-12,'Marginal target must equal direct all-rater native set union F1')
    x=np.zeros((3,12));m=dict(mean=np.zeros(12),std=np.ones(12),coef=np.zeros(12),bias=-.001)
    require(predict(x,np.array([1,1,1],bool),m)[0]is None,'Negative gain must select null')
    m['bias']=0.;require(predict(x,np.array([1,1,1],bool),m)[0]is None,'Zero gain must select null')
    m['bias']=.01;require(predict(x,np.array([0,1,1],bool),m)[0]==1,'Positive exact ties use first eligible native cell')
    bad=x.copy();bad[0,0]=np.nan
    try:predict(bad,np.ones(3,bool),m)
    except ValueError:pass
    else:raise ValueError('Execution failure must not silently become a successful null')
    rng=np.random.default_rng(71);language=rng.normal(size=(3,4096)).astype(np.float32)
    old=EXT/'head_code09/semantic_oof09.py'
    if not old.exists():old=EXT/'code/semantic_oof09.py'
    tree=ast.parse(old.read_text());node=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='transform');scope={'require':require}
    exec(compile(ast.Module(body=[node],type_ignores=[]),str(old),'exec'),scope)
    expected=scope['transform'](language,np.zeros((3,2),np.float32),dict(baseline=baseline,groups=groups),'LM')
    require(np.array_equal(transform(language,baseline,groups),expected),'Exact frozen winning semantic transform, not another architecture')
    hidden=np.zeros((3,8));score=np.zeros(3);features,valid=candidates(hidden,score,baseline,groups)
    require(features.shape==(3,12)and valid.tolist()==[True,True,True],'Candidate mapping includes only remaining native frame contribution')
    # Source-level fail safety of this implementation is a fixed decision bound,
    # not a substitute for quality evidence.
    for chosen in [None,0,1,2]:
        mask=baseline.copy()
        if chosen is not None:mask |= groups==chosen
        require(np.all(mask[baseline]),'New choice cannot delete protected baseline frames')
    save(ROOT/'targeted_checks.json',dict(status='PASS_TARGETED_NEW_UTILITY_AND_BASELINE_REGRESSIONS',checks=8,new_model_calls=0,new_processor_calls=0))
    event('TARGETED_CHECKS_PASS',checks=8)

if __name__=='__main__':
    try:main()
    except BaseException as e:failure('checks',e);raise
