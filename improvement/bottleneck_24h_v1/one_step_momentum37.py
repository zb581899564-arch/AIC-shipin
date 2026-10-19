"""Two actual single-step candidates using adopted gradients; no model forward."""
import argparse
import copy
import json
import math
import os
from pathlib import Path
import shutil
import traceback

from diagnose_underselection28 import read, ref, bound, save


def main(root):
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
    import torch
    from safetensors.torch import load_file, save_file
    reg = read(root/'registration37.json')
    assert ref(__file__) == reg['code_ref']
    save(root/'claim37.json',dict(registration_ref=ref(root/'registration37.json'),pid=os.getpid()))
    cp = torch.load(bound(reg['final_checkpoint_ref']),map_location='cpu',weights_only=True)
    assert cp['completed_updates']==559 and cp['successful_micro']==2236
    source_weights = bound(reg['source_adapter_ref'])
    disk_state = load_file(str(source_weights),device='cpu')
    state = cp['adapter_state_dict']
    assert list(state)==list(reg['parameter_keys']) and set(state)==set(disk_state)
    assert all(torch.equal(state[k],disk_state[k]) for k in state)
    old_opt = cp['optimizer_state_dict']
    group = old_opt['param_groups'][0]
    assert len(old_opt['param_groups'])==1 and group['lr']==1e-5 and group['weight_decay']==0
    assert group['betas']==(.9,.999) and group['eps']==1e-8
    assert len(group['params'])==288
    gradient = torch.zeros(15335424,dtype=torch.float32)
    total_raters = 0
    order = None
    for r in reg['adopted_gradient_refs']:
        data = torch.load(bound(r),map_location='cpu',weights_only=True)
        if order is None:
            order = data['parameter_order']
        assert data['parameter_order']==order
        gradient.add_(data['total_gradient'])
        total_raters += len(data['completed_reviewers'])
    assert total_raters == 62 == reg['gradient_divisor']
    assert [x['name'].replace('.summary.weight','.weight') for x in order] == list(state)
    gradient.div_(total_raters)
    raw_norm = float(gradient.norm())
    scale = min(1.,1./(raw_norm+1e-6))
    gradient.mul_(scale)
    assert bool(torch.isfinite(gradient).all()) and raw_norm > 0
    gradient_file = root/'fixed_adopted_gradient37.pt'
    torch.save(dict(gradient=gradient,parameter_order=order,divisor=total_raters,
                    pre_clip_norm=raw_norm,clip_factor=scale,new_backward_calls=0),gradient_file)
    common_v = None
    candidates = {}
    for arm in ('KEEP_M','RESET_M'):
        output = root/arm
        output.mkdir()
        parameters = [torch.nn.Parameter(v.clone()) for v in state.values()]
        opt = torch.optim.AdamW(parameters,lr=group['lr'],betas=group['betas'],eps=group['eps'],
                                weight_decay=0,foreach=False)
        opt.load_state_dict(copy.deepcopy(old_opt))
        offset = 0
        for (key,old),p in zip(state.items(),parameters):
            assert torch.equal(old,p.detach()) and int(opt.state[p]['step'])==559
            assert opt.state[p]['exp_avg'].dtype==opt.state[p]['exp_avg_sq'].dtype==torch.float32
            if arm=='RESET_M':
                opt.state[p]['exp_avg'].zero_()
            p.grad = gradient[offset:offset+p.numel()].reshape_as(p).clone()
            offset += p.numel()
        assert offset==len(gradient)
        # This is an actual parameter update and is counted as such, despite CPU execution.
        opt.step()
        candidate = {k:p.detach().clone() for k,p in zip(state,parameters)}
        next_state = opt.state_dict()
        max_error = 0.
        offset = 0
        changed = 0
        squared_delta = 0.
        next_v = []
        for (key,w),p,pid in zip(state.items(),parameters,group['params']):
            old = old_opt['state'][pid]
            actual = opt.state[p]
            assert int(actual['step'])==560
            g = gradient[offset:offset+w.numel()].reshape_as(w).double()
            m0 = old['exp_avg'].double() if arm=='KEEP_M' else torch.zeros_like(g)
            expected_m = .9*m0 + .1*g
            expected_v = .999*old['exp_avg_sq'].double() + .001*g.square()
            expected = w.double() - (1e-5/(1-.9**560))*expected_m/(expected_v.sqrt()/math.sqrt(1-.999**560)+1e-8)
            err = (candidate[key].double()-expected).abs()
            tolerance = 8*torch.finfo(torch.float32).eps*(w.double().abs()+(expected-w.double()).abs()+1e-8)
            assert bool((err<=tolerance).all()), 'Independent float64 Adam formula differs beyond FP32 rounding'
            max_error = max(max_error,float(err.max()))
            delta = candidate[key].double()-w.double()
            squared_delta += float(delta.square().sum())
            changed += not torch.equal(candidate[key],w)
            assert bool(torch.isfinite(candidate[key]).all())
            next_v.append(actual['exp_avg_sq'].detach().clone())
            offset += w.numel()
        assert changed>0 and squared_delta>0
        if common_v is None:
            common_v = next_v
        else:
            assert all(torch.equal(x,y) for x,y in zip(common_v,next_v)), 'Only first moment may differ'
        config = source_weights.parent/'adapter_config.json'
        shutil.copyfile(config,output/'adapter_config.json')
        out_weights = output/'adapter_model.safetensors'
        save_file(candidate,str(out_weights),metadata={'format':'pt'})
        reloaded = load_file(str(out_weights),device='cpu')
        assert set(reloaded)==set(candidate) and all(torch.equal(reloaded[k],candidate[k]) for k in candidate)
        opt_path = output/'one_step_state37.pt'
        torch.save(dict(completed_updates=560,new_candidate_updates=1,arm=arm,
                        optimizer_state_dict=next_state,adapter_state_dict=candidate,
                        adopted_gradient_ref=ref(gradient_file)),opt_path)
        info = dict(weights_ref=ref(out_weights),optimizer_checkpoint_ref=ref(opt_path),
                    new_candidate_updates=1,saved_optimizer_step=560,changed_matrices=changed,
                    l2_parameter_delta=math.sqrt(squared_delta),independent_float64_max_error=max_error,
                    save_reload_all288_bit_equal=True,all_second_moments_equal_between_arms=True)
        save(output/'candidate_acceptance37.json',info)
        candidates[arm] = info
        del parameters,opt,candidate,next_state,reloaded,next_v
    keep = load_file(candidates['KEEP_M']['weights_ref']['path'],device='cpu')
    reset = load_file(candidates['RESET_M']['weights_ref']['path'],device='cpu')
    different = sum(not torch.equal(keep[k],reset[k]) for k in keep)
    assert different>0 and ref(source_weights)==reg['source_adapter_ref']
    result = dict(status='PASS_TWO_FIXED_ONE_STEP_CANDIDATES_ONLY_FIRST_MOMENT_DIFFERS',
                  registration_ref=ref(root/'registration37.json'),candidates=candidates,
                  adopted_gradient_ref=ref(gradient_file),gradient_divisor=62,pre_clip_norm=raw_norm,
                  clip_factor=scale,arms_differing_matrices=different,total_new_candidate_optimizer_steps=2,
                  new_backward_or_model_calls=0,source_weights_and_checkpoint_unchanged=True,
                  not_final_pipeline_quality_or_production_admission=True)
    save(root/'completion37.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('registration_ref','adopted_gradient_ref')},ensure_ascii=False))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True)
    args=p.parse_args()
    try:
        main(args.root)
    except BaseException as error:
        save(args.root/('failure37_%s.json'%os.getpid()),dict(error=repr(error),traceback=traceback.format_exc(),
             successful_candidates_preserved=True,automatic_retry=False))
        raise
