"""Independent CPU float64 review of persisted gradients, no model or replay."""
import argparse
import json
import math
import os
from pathlib import Path

from diagnose_underselection28 import read, ref, bound, save


def main(root):
    assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
    import torch
    W = Path('/home/inspur/aic_video_work')
    RUN = W/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
    reg = read(root/'registration32.json')
    done = read(root/'gradient_completion32.json')
    assert done['status']=='COMPLETE_FOUR_ALL_RATER_GRADIENT_DECOMPOSITION_NO_UPDATES'
    assert done['optimizer_updates']==0 and done['base_and_adapter_unchanged']
    resource_path = RUN/'controller'/(reg['job_name']+'.resource.json')
    resource = read(resource_path)
    ledger = [json.loads(l) for l in (W/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if l]
    matching = [x for x in ledger if x.get('name')==reg['job_name']]
    assert len(matching)==1 and matching[0]==resource and resource['status']=='completed' and resource['exit_code']==0
    input_reg = read(bound(reg['training_prepared_ref']))
    original = [json.loads(l) for l in bound(input_reg['training_targets']).read_text().splitlines() if l]
    originals = {(x['uid'],x['reviewer']):x for x in original}
    details=[]
    for item in done['windows']:
        p=bound(item['gradient_ref'])
        value=torch.load(p,map_location='cpu',weights_only=True)
        g,b=value['total_gradient'],value['branch_gradient']
        assert g.dtype==b.dtype==torch.float32 and g.shape==b.shape==(15335424,)
        assert bool(torch.isfinite(g).all()) and bool(torch.isfinite(b).all())
        assert len(value['parameter_order'])==288 and sum(x['numel'] for x in value['parameter_order'])==15335424
        assert all(math.prod(x['shape'])==x['numel'] for x in value['parameter_order'])
        assert len(value['rows'])==reg['rater_counts'][item['uid']]
        assert len({x['reviewer'] for x in value['rows']})==len(value['rows'])
        assert len(list(root.glob('row32_'+item['uid']+'_*.json')))==len(value['rows'])
        for row in value['rows']:
            old=originals[(row['uid'],row['reviewer'])]
            assert row['source_weight']==old['weight']
            assert row['token_count']==len(old['suffix_ids'])
            assert row['empty']==(not json.loads(old['target_json'])['segments'])
        gd,bd=g.double(),b.double()
        rest=gd-bd
        gg=float(torch.dot(gd,gd));bb=float(torch.dot(bd,bd));rr=float(torch.dot(rest,rest))
        gb=float(torch.dot(gd,bd));rb=float(torch.dot(rest,bd))
        assert gg>0 and bb>0 and math.isclose(gb,bb+rb,rel_tol=1e-10,abs_tol=1e-10)
        details.append(dict(uid=item['uid'],sid=item['sid'],stratum=item['stratum'],reviewers=len(value['rows']),
            empty_reviewers=sum(x['empty'] for x in value['rows']),total_gradient_norm=math.sqrt(gg),
            branch_gradient_norm=math.sqrt(bb),rest_gradient_norm=math.sqrt(rr),
            total_dot_branch=gb,rest_dot_branch=rb,total_branch_cosine=gb/math.sqrt(gg*bb),
            rest_branch_cosine=rb/math.sqrt(rr*bb) if rr else None,
            total_SGD_direction_locally_worsens_branch_loss=gb<0,
            other_tokens_oppose_branch_gradient=rb<0,
            gradient_ref=item['gradient_ref']))
    assert sum(x['reviewers'] for x in details)==done['actual_new_forwards']==reg['actual_original_rater_forward_count']
    result=dict(status='PASS_FIRST_ALL_RATER_GRADIENT_CPU_QA_AND_COMPONENT_REVIEW',
        QA_code_ref=ref(__file__),registration_ref=ref(root/'registration32.json'),
        gradient_completion_ref=ref(root/'gradient_completion32.json'),resource_ref=ref(resource_path),
        unique_ledger_equal=True,details=details,
        windows_total_gradient_opposes_decision=sum(x['total_SGD_direction_locally_worsens_branch_loss'] for x in details),
        windows_rest_gradient_opposes_decision=sum(x['other_tokens_oppose_branch_gradient'] for x in details),
        actual_new_forward_graphs=done['actual_new_forwards'],optimizer_updates=0,
        model_replay_in_this_CPU_QA=0,protected40_47_unchanged=True,
        interpretation_limits=['A local deterministic gradient at final weights does not reconstruct historical Adam/dropout updates.',
            'Rest means every answer token other than the third; it is not a timestamp-only gradient.',
            'Four historically exposed training windows cannot establish generalization or official-score gain.',
            'If total dot branch is positive, this small test does not support local gradient conflict as the cause of the empty decision.'],
        automatic_training_or_production=False)
    save(root/'first_gradient_output_review33.json',result)
    print(json.dumps(dict(status=result['status'],details=[{k:v for k,v in x.items() if k!='gradient_ref'} for x in details],
        windows_total_gradient_opposes_decision=result['windows_total_gradient_opposes_decision'],
        windows_rest_gradient_opposes_decision=result['windows_rest_gradient_opposes_decision'],
        forwards=done['actual_new_forwards'],optimizer_updates=0,charged_seconds=resource['charged_seconds'],
        peak_gpu_mib=resource['sampled_peak_memory_mib'],review_ref=ref(root/'first_gradient_output_review33.json')),
        ensure_ascii=False))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True)
    main(p.parse_args().root)
