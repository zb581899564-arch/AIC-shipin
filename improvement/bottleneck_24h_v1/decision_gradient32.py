"""Four fixed training windows, all original raters; derivatives only, zero updates."""
from datetime import datetime, timezone
import argparse
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import time
import traceback

from diagnose_underselection28 import read, ref, bound, save


def main(root):
    import torch
    reg = read(root/'registration32.json')
    assert os.environ.get('CUDA_VISIBLE_DEVICES') not in (None,'')
    for name,r in reg['code'].items():
        assert bound(r) == Path(__file__).resolve().parent/name
    save(root/'claim32.json',dict(pid=os.getpid(),registration_ref=ref(root/'registration32.json')))
    W = Path('/home/inspur/aic_video_work')
    P = W/'bottleneck_24h_20261019_v1'
    N = P/'summary_objective_v20'
    RUN = W/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
    sys.path.insert(0,str(N/'code'))
    from summary_runtime import build_training_tokens, source_pixels, atomic_torch
    from summary_contract import build_pixels, signature
    sys.path.insert(0,str(RUN/'temporal_sft8b_v1'))
    from sft_contract import verify_live_gpu_reservation
    from verify_saved_smoke import canonical_frozen_hash
    verify_live_gpu_reservation()
    from transformers import Qwen3VLForConditionalGeneration
    from peft import PeftModel, get_peft_model_state_dict
    from safetensors.torch import load_file
    cfg = read(bound(reg['model_config_ref']))
    weights = bound(reg['trained_weights_ref'])
    prepared = read(bound(reg['training_prepared_ref']))
    rows = [json.loads(l) for l in bound(prepared['training_targets']).read_text().splitlines() if l]
    fixed = read(bound(reg['CPU28_result_ref']))['fixed_next_probe_selection']
    fixed = [x for x in fixed if x['domain']=='training']
    selected = {x['uid']:[r for r in rows if r['uid']==x['uid']] for x in fixed}
    assert sum(len(v) for v in selected.values()) == reg['actual_original_rater_forward_count']
    catalog = {s['id']:s for s in read(bound(prepared['source_catalog']))['sources']}
    started = time.monotonic()
    def deadline():
        assert datetime.now(timezone.utc) < datetime.fromisoformat(reg['main_cutoff_utc'].replace('Z','+00:00'))
        assert time.monotonic()-started < reg['max_gpu_seconds']
    torch.manual_seed(20261019)
    torch.cuda.manual_seed_all(20261019)
    base = Qwen3VLForConditionalGeneration.from_pretrained(cfg['model_dir'],revision=cfg['model_revision'],
        local_files_only=True,torch_dtype=torch.bfloat16,device_map={'':'cuda:0'},low_cpu_mem_usage=True,
        attn_implementation='sdpa')
    for p in base.parameters():
        p.requires_grad_(False)
    before = canonical_frozen_hash(base,torch)
    assert before['sha256']==cfg['expected_base_sha256']
    model = PeftModel.from_pretrained(base,str(weights.parent),adapter_name='summary',is_trainable=True)
    trainable = re.compile(r'language_model\.layers\.(\d+)\.self_attn\.(q_proj|k_proj|v_proj|o_proj)\.lora_(A|B)\.summary\.weight$')
    for name,p in model.named_parameters():
        p.requires_grad_(trainable.search(name) is not None)
    parameters = [(n,p) for n,p in model.named_parameters() if p.requires_grad]
    assert len(parameters)==288 and sum(p.numel() for _,p in parameters)==15335424
    saved = load_file(str(weights),device='cpu')
    state = get_peft_model_state_dict(model,adapter_name='summary')
    assert set(state)==set(saved) and all(torch.equal(state[k].detach().cpu(),saved[k]) for k in saved)
    del state
    model.config.use_cache=False
    model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant':False})
    model.train()
    disabled_dropouts = []
    for name,m in model.named_modules():
        if isinstance(m,torch.nn.Dropout):
            m.eval()
            disabled_dropouts.append(dict(name=name,p=m.p))
        if name.endswith('.visual'):
            m.eval()
    save(root/'first_runtime_acceptance32.json',dict(status='PASS_EXACT_SINGLE_ADAPTER_GRADIENT_ONLY_RUNTIME',
        active_parameters=15335424,matrices=288,base_parameters=8767123696,optimizer_created=False,
        source_weights_ref=reg['trained_weights_ref'],all_saved_weights_exact=True,
        deterministic_dropout_disabled=disabled_dropouts,not_historical_stochastic_training_replay=True))
    results = []
    forward_count = 0
    C = reg['fixed_normalizer']
    from fractions import Fraction
    for sample in fixed:
        deadline()
        request = read(bound(sample['input_ref']))
        source = catalog[sample['sid']]
        frames,grid,ordinals = source_pixels(source)
        clock = read(bound(source['clock']))
        plan = request['plan']
        values,actual = build_pixels(frames,grid,ordinals,clock['normalized_exact_pts'],
            plan['window_start_exact'],plan['window_end_exact'],
            dict(source_id=sample['sid'],source_sha256=request['source_sha256']))
        assert actual==plan
        prefix = torch.load(bound(request['prefix_ref']),map_location='cpu',weights_only=True)
        values.update(prefix)
        assert signature(values)==request['input_signature']
        data = selected[sample['uid']]
        params = [p for _,p in parameters]
        total = torch.zeros(15335424,device='cuda:0',dtype=torch.float32)
        branch = torch.zeros_like(total)
        row_details = []
        progress = root/('gradient_progress32_'+sample['uid']+'.pt')
        for row in sorted(data,key=lambda x:x['reviewer']):
            deadline()
            suffix = row['suffix_ids']
            assert suffix[:2]==[4913,56829] and suffix[2] in (788,8899)
            tokens = build_training_tokens(prefix,suffix)
            gpu = {k:v.to('cuda:0') for k,v in values.items() if k not in ('input_ids','attention_mask')}
            gpu.update(input_ids=tokens['full_input_ids'].to('cuda:0'),attention_mask=tokens['attention_mask'].to('cuda:0'))
            with (root/'journal32.jsonl').open('a') as log:
                log.write(json.dumps(dict(event='BEGIN_NEW_GRADIENT_FORWARD',uid=row['uid'],reviewer=row['reviewer']))+'\n')
                log.flush();os.fsync(log.fileno())
            hidden = model.get_base_model().model(**gpu,use_cache=False,return_dict=True).last_hidden_state
            logits = model.get_base_model().lm_head(hidden.index_select(1,tokens['causal_logits_indices'].to('cuda:0'))).float()[0]
            ce = torch.nn.functional.cross_entropy(logits,tokens['targets'][0].to('cuda:0'),reduction='none')
            scale = row['weight']/C
            gb = torch.autograd.grad(ce[2]*scale,params,retain_graph=True)
            flat_branch = torch.cat([g.detach().flatten().float() for g in gb])
            del gb
            gt = torch.autograd.grad(ce.sum()*scale,params)
            flat_total = torch.cat([g.detach().flatten().float() for g in gt])
            del gt
            assert bool(torch.isfinite(flat_branch).all()) and bool(torch.isfinite(flat_total).all())
            total.add_(flat_total);branch.add_(flat_branch)
            row_record = dict(uid=row['uid'],reviewer=row['reviewer'],empty=not json.loads(row['target_json'])['segments'],
                source_weight=row['weight'],token_count=len(suffix),total_CE=float(ce.sum().detach().cpu()),
                third_token_CE=float(ce[2].detach().cpu()))
            row_details.append(row_record)
            checkpoint = dict(uid=sample['uid'],completed_reviewers=[x['reviewer'] for x in row_details],
                total_gradient=total.detach().cpu(),branch_gradient=branch.detach().cpu(),rows=row_details,
                parameter_order=[dict(name=n,shape=list(p.shape),numel=p.numel()) for n,p in parameters],
                actual_loss_constant=C,optimizer_updates=0,gradients_not_model_updates=True)
            atomic_torch(progress,checkpoint,replace=progress.exists())
            save(root/('row32_%s_%03d.json'%(row['uid'],row['reviewer'])),row_record)
            forward_count+=1
            del checkpoint,flat_branch,flat_total,hidden,logits,ce,tokens,gpu
            assert all(p.grad is None for p in params)
        assert len(row_details)==len(data)
        results.append(dict(uid=sample['uid'],sid=sample['sid'],stratum=sample['stratum'],
                            reviewers=len(data),gradient_ref=ref(progress)))
        del total,branch,frames,values,prefix
        print(json.dumps(dict(event='ALL_RATER_GRADIENT_WINDOW_COMPLETE',uid=sample['uid'],forwards=forward_count)),flush=True)
    assert forward_count==reg['actual_original_rater_forward_count']
    state = get_peft_model_state_dict(model,adapter_name='summary')
    assert all(torch.equal(state[k].detach().cpu(),saved[k]) for k in saved)
    assert canonical_frozen_hash(model,torch)==before and ref(weights)==reg['trained_weights_ref']
    save(root/'gradient_completion32.json',dict(status='COMPLETE_FOUR_ALL_RATER_GRADIENT_DECOMPOSITION_NO_UPDATES',
        windows=results,actual_new_forwards=forward_count,backward_components_per_forward=2,
        optimizer_created=False,optimizer_updates=0,base_and_adapter_unchanged=True,
        deterministic_dropout_disabled=True,not_historical_update_replay=True,
        media_decode_or_processor_calls=0,elapsed_seconds=time.monotonic()-started))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,required=True)
    args=parser.parse_args()
    try:
        main(args.root)
    except BaseException as error:
        save(args.root/('failure32_%s.json'%os.getpid()),dict(error=repr(error),traceback=traceback.format_exc(),
            no_automatic_retry=True,successful_rows_progress_preserved=True))
        raise
