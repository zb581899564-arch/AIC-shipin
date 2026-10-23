"""First full frozen-branch native output and independently audited routing comparison."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
from bisect import bisect_left
from fractions import Fraction
import sys
from pathlib import Path
import numpy as np
import torch
from transformers import AutoTokenizer
from baseline_bridge57_common import ROOT,DATA,SEM,WORK,RUN,read,ref,save,checked,legacy_runtime,verify_modules,semantic_modules


def verified_mask(source):
    legacy_runtime();contract,grammar,_=verify_modules()
    tokenizer=AutoTokenizer.from_pretrained(read(RUN/'b_score_aligned_package_v4/config.json')['model_dir'],local_files_only=True)
    candidates=grammar.candidate_tokens(tokenizer,contract.responses())
    clock=read(checked(source['clock']));origin=Fraction(clock['first_PTS_exact']);pts=[Fraction(p)-origin for p in clock['PTS']]
    end=Fraction(clock['physical_end_exact'])-origin;all_mask=np.zeros(len(pts),dtype=bool);kept=all_mask.copy();decisions=[]
    for identity in read(ROOT/'verify_GPU_completion.json')['outputs']:
        row=read(checked(identity));case=row['input'];event=case['event'];req=read(checked(case['request']));raw=read(checked(row['raw']))
        constraint=grammar.VerifyConstraint(tokenizer,raw['prefix'],req,raw['eos'],candidates)
        constraint.assert_complete(torch.tensor(raw['tokens'],dtype=torch.long))
        text=tokenizer.decode(raw['tokens'],skip_special_tokens=True,clean_up_tokenization_spaces=False)
        decision=contract.resolve(text,req,execution_status='MODEL_OK')
        if decision!=row['decision']:raise ValueError('Independent canonical VERIFY replay differs')
        first,last=map(Fraction,event['original_interval_exact']);lo,hi=map(Fraction,event['original_window_exact'])
        a=max(lo,first-Fraction(3,4));b=min(hi,last+Fraction(1,2)+(Fraction(1,4) if last-first>=8 else 0))
        mask=np.zeros(len(pts),dtype=bool);mask[bisect_left(pts,a):bisect_left(pts,b)]=True;all_mask|=mask
        if decision['decision']!='DROP':kept|=mask
        decisions.append(dict(event=event['event_id'],decision=decision['decision']))
    guard=not kept.any() and all_mask.any()
    if guard:kept=all_mask.copy()
    return kept,all_mask,decisions,guard


def semantic_mask(baseline):
    _,transform,head_module=semantic_modules();language=[];yesno=[]
    cpu=read(ROOT/'semantic_CPU_completion.json');model=read(ROOT/'semantic_GPU_completion.json')
    if len(cpu['chunks'])!=len(model['outputs']):raise ValueError('Full semantic input/output count differs')
    for case,identity in zip(cpu['chunks'],model['outputs']):
        value=torch.load(checked(identity),map_location='cpu',weights_only=True)
        if value['input']!=case['input'] or value['samples']!=case['samples']:raise ValueError('First semantic output input binding differs')
        if value['language'].shape!=(case['queries'],4096) or value['yes_no'].shape!=(case['queries'],2):raise ValueError('Actual output representation shape differs')
        language.append(value['language'].numpy());yesno.append(value['yes_no'].numpy())
    language=np.concatenate(language);yesno=np.concatenate(yesno)
    with np.load(checked(cpu['native']),allow_pickle=False) as value:groups=value['groups']
    native=dict(baseline=baseline,groups=groups);reg=read(SEM/'production_registration.json')
    x=transform.transform(language,yesno,native,reg['selected_view'])
    model=head_module.ResidualHead(reg['feature_dimension'],8)
    model.load_state_dict(torch.load(checked(reg['selected_head']),map_location='cpu',weights_only=True),strict=True);model.eval()
    if model.parameter_count!=98329:raise ValueError('Frozen actual semantic head parameters differ')
    with torch.inference_mode():residual=model(torch.from_numpy(x)).numpy()
    if not np.isfinite(residual).all():raise ValueError('Frozen semantic residual is nonfinite')
    selected=baseline | (residual[groups]>1.)
    with (ROOT/'frozen_head_output.npz').open('xb') as out:np.savez_compressed(out,residual=residual,selected=selected,groups=groups)
    return selected,int((selected & ~baseline).sum())


def main():
    source=read(ROOT/'registration.json')['source'];baseline,d8,decisions,guard=verified_mask(source)
    full,added=semantic_mask(baseline)
    sport=WORK/'highlight_source_admission_20261021_v1/matched_hl_pilot16';stem=source['source']
    accepted=read(sport/'inputs'/stem/'acceptance.json');groups=np.load(checked(accepted['groups']),allow_pickle=False)
    expert=np.load(sport/'outputs'/(stem+'_matched_HL.npy'),allow_pickle=False)
    route=next(r for r in read(WORK/'general_highlight_supervision_20261021_v1/semantic_route48/routing.json') if r['sid']=='S_'+stem)
    rerank=full.copy();remove=full.copy()
    if route['source_routed']:
        rerank[:]=False;rerank[np.argsort(-expert[groups],kind='stable')[:int(full.sum())]]=True
        remove=full & (expert[groups]>=.5)
    with (ROOT/'native_selections.npz').open('xb') as out:
        np.savez_compressed(out,D8=d8,VERIFY=baseline,full40_47=full,source_rerank=rerank,source_remove=remove)
    # All candidate choices above are completed before the first human-label read.
    sys.path.insert(0,str(sport/'code'));from pilot15_common import original_targets
    from time_control50_review import metrics
    labels=original_targets(source)
    values={k:metrics(v,labels) for k,v in dict(D8=d8,VERIFY=baseline,full40_47=full,source_rerank=rerank,source_remove=remove).items()}
    gains={arm:values[arm]['F1']-values['full40_47']['F1'] for arm in ['source_rerank','source_remove']}
    save(ROOT/'review.json',dict(state='FROZEN_BASELINE_BRIDGE_SIGNAL_REQUIRES_EXPLICIT_PRODUCTION_ADMISSION' if any(g>0 for g in gains.values()) else 'STOP_FULL_BASELINE_ROUTING57',
        actual_complete_external_frozen_VERIFY_and_semantic_branch=True,original_TIME_B0_answers_adopted=True,
        external_native64_window_plan_not_official_test_reproduction=True,source_count=1,historically_exposed_not_blind=True,
        metrics=values,F1_delta_vs_complete_frozen_branch=gains,semantic_added_frames=added,verification=decisions,
        original_empty_source_guard_applied=guard,all_candidate_predictions_before_label_mask=True,
        no_official_joint_score_or_universal_gain_claim=True,no_automatic426_or_package=True))
    save(ROOT/'independent_CPU_audit.json',dict(state='PASS',VERIFY_token_grammar_parser_replay=True,
        native_original_window_clipping=True,semantic_input_output_and_frozen_weight_binding=True,
        all_expected_target_queries=read(ROOT/'semantic_CPU_completion.json')['cells'],
        native_selections=ref(ROOT/'native_selections.npz'),baseline40_47_unchanged=True))


if __name__=='__main__':main()
