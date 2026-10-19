"""Read saved final Adam moments; analytic directions only, never an update."""
import argparse
import json
import math
import os
from pathlib import Path

from diagnose_underselection28 import read,ref,bound,save


def main(root):
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
    import torch
    reg=read(root/'registration35.json')
    assert ref(__file__)==reg['code_ref']
    gradient_review=read(bound(reg['gradient_review33_ref']))
    cp=torch.load(bound(reg['final_training_checkpoint_ref']),map_location='cpu',weights_only=True)
    assert cp['completed_updates']==559 and cp['successful_micro']==2236
    opt=cp['optimizer_state_dict']
    assert len(opt['param_groups'])==1
    group=opt['param_groups'][0]
    assert group['lr']==1e-5 and group['betas']==(.9,.999) and group['eps']==1e-8 and group['weight_decay']==0
    ids=group['params']
    assert len(ids)==288 and len(set(ids))==288
    first=torch.load(bound(gradient_review['details'][0]['gradient_ref']),map_location='cpu',weights_only=True)
    parameter_order=first['parameter_order']
    stripped=[x['name'].replace('.summary.weight','.weight') for x in parameter_order]
    assert stripped==list(cp['adapter_state_dict']), 'Cannot prove optimizer/gradient name order; no positional guessing'
    direction=[];denominator=[]
    for pid,item,key in zip(ids,parameter_order,stripped):
        value=opt['state'][pid]
        step=int(value['step'].item())
        assert step==559 and list(value['exp_avg'].shape)==item['shape']
        assert value['exp_avg'].shape==value['exp_avg_sq'].shape==cp['adapter_state_dict'][key].shape
        m=value['exp_avg'].double()/(1-group['betas'][0]**step)
        den=(value['exp_avg_sq'].double()/(1-group['betas'][1]**step)).sqrt()+group['eps']
        assert bool(torch.isfinite(m).all()) and bool(torch.isfinite(den).all()) and bool((den>0).all())
        direction.append((m/den).flatten());denominator.append(den.flatten())
    direction=torch.cat(direction);denominator=torch.cat(denominator)
    assert direction.numel()==denominator.numel()==15335424
    results=[]
    for item in gradient_review['details']:
        data=torch.load(bound(item['gradient_ref']),map_location='cpu',weights_only=True)
        assert data['parameter_order']==parameter_order
        branch=data['branch_gradient'].double();full=data['total_gradient'].double()
        moment_dot=float(branch.dot(direction))
        preconditioned=full/denominator
        pre_dot=float(branch.dot(preconditioned))
        def cosine(x,y):return float(x.dot(y)/(x.norm()*y.norm()))
        results.append(dict(uid=item['uid'],stratum=item['stratum'],
            gradient_total_branch_cosine=item['total_branch_cosine'],
            saved_final_Adam_direction_dot_branch=moment_dot,
            saved_final_Adam_direction_branch_cosine=cosine(branch,direction),
            saved_final_Adam_direction_locally_worsens_branch=moment_dot<0,
            hypothetical_current_gradient_preconditioned_dot_branch=pre_dot,
            hypothetical_current_gradient_preconditioned_branch_cosine=cosine(branch,preconditioned),
            hypothetical_preconditioning_flips_local_direction=pre_dot<0,
            predicted_branch_loss_linear_change_if_reusing_saved_final_direction=-group['lr']*moment_dot))
    result=dict(status='COMPLETE_CPU_SAVED_ADAM_DIRECTION_ANALYSIS_NO_UPDATES',
        registration_ref=ref(root/'registration35.json'),parameter_order_proved_by_saved_adapter_keys=True,
        optimizer_states=288,saved_step=559,actual_optimizer_updates_in_this_audit=0,model_calls=0,
        details=results,
        windows_saved_direction_opposes_branch=sum(x['saved_final_Adam_direction_locally_worsens_branch'] for x in results),
        windows_hypothetical_preconditioning_flips_direction=sum(x['hypothetical_preconditioning_flips_local_direction'] for x in results),
        interpretation_limits=['The saved moment direction is the final-step direction evaluated against final-weight deterministic gradients, not the full training history or an observed next step.',
            'Each window gradient includes all its original raters; the saved Adam moment came from the actual preceding shuffled microbatches and cannot be treated as that same window gradient.',
            'Preconditioned-current-gradient direction is an analytic counterfactual with saved v, not an executed optimizer step.',
            'No cause is promoted to unique proof and no optimizer/loss/production change is automatically admitted.'])
    save(root/'result35.json',result)
    print(json.dumps(dict(status=result['status'],details=results,
        windows_saved_direction_opposes_branch=result['windows_saved_direction_opposes_branch'],
        windows_hypothetical_preconditioning_flips_direction=result['windows_hypothetical_preconditioning_flips_direction'],
        model_calls=0,optimizer_updates=0,result_ref=ref(root/'result35.json')),ensure_ascii=False))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True)
    main(p.parse_args().root)
