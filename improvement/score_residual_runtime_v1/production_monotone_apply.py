"""Frozen new head, no labels and no outcome-based production selection."""
import sys
from common_runtime import *

def main():
    import numpy as np
    import torch
    sys.path.insert(0,str(ROOT))
    from score_residual_head_v1.contracts import build_contract
    from monotone_head06 import ResidualHead,native_prediction
    torch.set_num_threads(2)
    reg=read(ROOT/'production_registration.json');feature=read(ROOT/'feature_completion.json')
    require(len(feature['sources'])==426,'Incomplete actual feature generation')
    selected=reg['selected_head']
    require(sha(selected['path'])==selected['sha256'],'Frozen selected head changed')
    model=ResidualHead(reg['feature_dimension'],8);model.load_state_dict(torch.load(selected['path'],map_location='cpu',weights_only=True));model.eval()
    require(8782459120+model.parameter_count==reg['actual_resident_parameters']<=9000000000,'Actual parameter limit')
    outputs=[]
    for s in feature['sources']:
        sid=s['id'];vpath=ROOT/'features'/sid/'vision.npy';require(sha(vpath)==s['feature_sha256'],'Frozen feature changed')
        v=np.load(vpath).astype(np.float32);n=np.load(ROOT/'inputs'/sid/'native.npz')
        center=v.mean(axis=0,dtype=np.float64).astype(np.float32)
        scale=max(1e-6,float(np.sqrt(np.mean((v-center).astype(np.float64)**2))))
        local=np.stack([v[max(0,j-4):min(len(v),j+5)].mean(0) for j in range(len(v))])
        delta=np.abs(v-np.vstack([v[:1],v[:-1]]));ds=max(1e-6,float(np.sqrt(np.mean(delta.astype(np.float64)**2))))
        prior=np.array([n['baseline'][n['groups']==j].mean() for j in range(len(v))],np.float32)[:,None]
        x=torch.from_numpy(np.concatenate([(v-center)/scale,(local-center)/scale,delta/ds,prior-prior.mean()],axis=1).copy())
        c=build_contract(n['groups'].tolist(),n['baseline'].tolist(),[None]*len(n['baseline']),len(v),read(ROOT/'inputs'/sid/'clock.json')['normalized_exact_pts'])
        with torch.no_grad():residual=model(x).detach()
        mask=np.array(native_prediction(residual,c),dtype=np.bool_)
        # Independent direct native prior+feature residual predicate, no unit expansion.
        direct=n['baseline'].copy();z=(2*n['baseline'].astype(np.int8)-1).astype(np.float32)+residual.numpy()[n['groups']]
        direct = n['baseline'] | (z>0)
        require(np.array_equal(mask,direct) and bool((mask | ~n['baseline']).all()),'First independent native head replay or baseline retention failed')
        out=ROOT/'head_outputs'/sid;out.mkdir(parents=True,exist_ok=False)
        np.savez(out/'output.npz',residual=residual.numpy(),selected_native=mask)
        rec=dict(id=sid,frames=len(mask),selected=int(mask.sum()),baseline=int(n['baseline'].sum()),added=int((mask&~n['baseline']).sum()),removed=int((~mask&n['baseline']).sum()),sha256=sha(out/'output.npz'),independent_direct_native_equal=True)
        write(out/'acceptance.json',rec);outputs.append(rec)
    write(ROOT/'head_output_acceptance.json',dict(status='PASS_FROZEN_HEAD_ALL426_FIRST_NATIVE_OUTPUT_REPLAY',sources=outputs,actual_resident_parameters=reg['actual_resident_parameters'],new_training_updates=0,new_language_generations=0))

if __name__=='__main__':main()
