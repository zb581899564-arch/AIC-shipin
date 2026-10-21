"""Explicit CPU prepare -> one BASE GPU judgment -> independent CPU review.

New nonlinear visual comparison uses the same cached native actions. No
reference is read in prepare/GPU; reference-assisted oracle choices are absent.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from fractions import Fraction
import gzip
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import random
import sys
import time
import traceback
from unittest.mock import patch


def require(value, message):
    if not value: raise ValueError(message)


def save(path, value):
    with Path(path).open('x', encoding='utf8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)


def ref(path):
    blob=Path(path).read_bytes()
    return dict(path=str(Path(path).resolve()), bytes=len(blob), sha256=hashlib.sha256(blob).hexdigest())


def checked(reference, workspace):
    p=Path(reference['path']).resolve(strict=True)
    require(p.is_relative_to(workspace) and ref(p)==reference, 'Bound file identity/path changed')
    return p


def loadref(reference, workspace):
    return json.loads(checked(reference,workspace).read_text())


def signature(values):
    import torch
    return {k:dict(shape=list(v.shape),dtype=str(v.dtype),sha256=hashlib.sha256(
        v.detach().cpu().contiguous().view(torch.uint8).numpy().tobytes()).hexdigest()) for k,v in values.items()}


def original_candidates(row):
    require(row['status']=='ACCEPTED' and row['labels_read'] is False, 'Actual reference-free successful pool required')
    result=[];seen=set()
    for slot in row['slots']:
        key=tuple(slot['selected_ordinals'])
        require(slot['status']=='ACCEPTED' and list(key)==sorted(set(key)), 'Successful native action required')
        if key not in seen:
            result.append(dict(slot=slot['slot'],text=slot['text'],selected_ordinals=list(key)))
            seen.add(key)
    require(any(not v['selected_ordinals'] for v in result), 'Keep the legitimate empty choice')
    return result


def shuffled_options(row):
    options=original_candidates(row)
    seed=int.from_bytes(hashlib.sha256(('AIC_WINDOW_JUDGE03:'+row['source_sha256']+':'+row['uid']).encode()).digest()[:8],'big')
    random.Random(seed).shuffle(options)
    return options


class ChoiceTrie:
    def __init__(self, prefix_length, suffixes):
        self.prefix_length=prefix_length
        self.suffixes={int(k):tuple(v) for k,v in suffixes.items()}
        require(self.suffixes and all(v for v in self.suffixes.values()),'Nonempty actual answer suffixes required')

    def allowed(self, suffix):
        suffix=tuple(suffix)
        choices=sorted({ids[len(suffix)] for ids in self.suffixes.values()
                        if len(ids)>len(suffix) and ids[:len(suffix)]==suffix})
        require(choices,'Generated token prefix escaped finite choice grammar')
        return choices

    def __call__(self, batch_id, input_ids):
        return self.allowed(input_ids.tolist()[self.prefix_length:])

    def complete(self, ids):
        matching=[k for k,v in self.suffixes.items() if tuple(ids)==v]
        require(len(matching)==1,'Missing EOS/ambiguous/incomplete output is execution failure, not empty')
        return matching[0]


def context(root):
    root=Path(root).resolve(strict=True);workspace=root.parent.parent
    reg=json.loads((root/'registration03.json').read_text())
    checked(reg['code_ref'],workspace)
    protocol=loadref(reg['protocol_ref'],workspace)
    require(protocol['maximum_new_generations']==86 and protocol['arms']==['real','shifted'], 'Fixed86 real/shifted pilot only')
    sys.path.insert(0,reg['prior_code_root'])
    complete=loadref(reg['prior_collection_ref'],workspace)
    require((complete['scope'],complete['source_count'],complete['window_count'])==('check',8,43),'Exact external8/43 only')
    manifest=loadref(complete['asset_manifest_ref'],workspace)
    from improvement.native_preference_v1 import inputs as inputs_module
    from improvement.content_choice_v1.runtime import permute_visual
    from improvement.native_preference_v1.runtime import tokenize_answer,canonical_frozen_hash
    # Same decoded tensors, but decompress each gzip once before torch ZIP seeks.
    # All original tensor signatures are still checked by the inherited store.
    class FastStore(inputs_module.NativeInputStore):
        def _source_pixels(self,sid):
            def once(path,mode='rb',*args,**kwargs):
                require(mode=='rb','Read-only gzip adoption')
                return io.BytesIO(gzip.decompress(Path(path).read_bytes()))
            with patch.object(inputs_module.gzip,'open',once):
                return super()._source_pixels(sid)
    return root,workspace,reg,protocol,complete,manifest,FastStore,permute_visual,tokenize_answer,canonical_frozen_hash


def build_text(processor, request, clock, grid, options, protocol):
    from types import SimpleNamespace
    plan=request['plan']
    duration=float(Fraction(plan['window_end_exact'])-Fraction(plan['window_start_exact']))
    prompt=protocol['prompt']+'\nSource duration %.6fs; Excerpt global interval [%.6f, %.6f), local [0, %.6f).\n'%(
        float(Fraction(clock['physical_end_exact'])),float(Fraction(plan['window_start_exact'])),
        float(Fraction(plan['window_end_exact'])),duration)
    prompt+='Fixed alternatives:\n'+'\n'.join('Choice %d: %s'%(i,v['text']) for i,v in enumerate(options))
    prompt+='\nReturn exactly {"choice":i}, with integer i from0 to%d.\n'%(len(options)-1)
    raw=processor.apply_chat_template([dict(role='user',content=[dict(type='text',text=prompt+'Overview:\n'),
        dict(type='video'),dict(type='text',text='\nExcerpt:\n'),dict(type='video')])],
        tokenize=False,add_generation_prompt=True,enable_thinking=False)
    marker=processor.vision_start_token+processor.video_token+processor.vision_end_token
    parts=raw.split(marker);require(len(parts)==3,'Exactly2 source-owned views')
    text=parts[0]
    for i,(video,(_,h,w)) in enumerate(zip(plan['videos'],grid.tolist())):
        text+=''.join('<%.1f seconds>'%float(Fraction(t))+processor.vision_start_token+
            processor.video_token*(h*w//4)+processor.vision_end_token for t in video['group_timestamps_exact'])+parts[i+1]
    encoded=processor.tokenizer(text,return_tensors='pt',add_special_tokens=False,truncation=False)
    prefix={k:encoded[k].contiguous() for k in ['input_ids','attention_mask']}
    require(prefix['input_ids'].shape[1]+protocol['maximum_new_answer_tokens']<=12288,'No truncation or token budget widening')
    vid=processor.tokenizer.convert_tokens_to_ids(processor.video_token)
    require(int((prefix['input_ids']==vid).sum())==sum(t*h*w//4 for t,h,w in grid.tolist()),'Exact video-token placement')
    return prefix,dict(raw_template=raw,expanded_text=text,prompt=prompt,video_token_id=vid)


def prepare(root):
    started=time.monotonic()
    root,W,reg,protocol,complete,manifest,Store,permute,tokenize,_=context(root)
    import torch
    from transformers import AutoProcessor
    model=manifest['model_spec']
    processor=AutoProcessor.from_pretrained(model['model_dir'],revision=model['revision'],local_files_only=True,trust_remote_code=False)
    store=Store(manifest,'check');out=root/'inputs03';out.mkdir()
    case_refs=[]
    for sid in sorted(store.source_ids):
        for uid in complete['sources'][sid]['window_ids']:
            require(time.monotonic()-started<protocol['cpu_prepare_seconds'],'Finite input preparation budget')
            row=loadref(complete['window_refs'][uid],W)
            request,values,clock=store.case(uid)
            options=shuffled_options(row)
            prefix,metadata=build_text(processor,request,clock,values['video_grid_thw'],options,protocol)
            newvalues=dict(values,**prefix)
            # First independent text/processor expansion with actual adopted pixels.
            store._helpers().independent_text(processor,request['plan'],newvalues,metadata)
            suffixes={i:tokenize(processor.tokenizer,newvalues,json.dumps(dict(choice=i),separators=(',',':')),
                               request_text=metadata['expanded_text']) for i in range(len(options))}
            eos=processor.tokenizer.convert_tokens_to_ids('<|im_end|>')
            require(all(v[-1]==eos and eos not in v[:-1] and len(v)<=32 for v in suffixes.values()),'Actual finite EOS grammar')
            shifted=permute(newvalues)
            sig,shift_sig=signature(newvalues),signature(shifted)
            require(sig['pixel_values_videos']==row['input_signature']['pixel_values_videos'] and
                shift_sig['pixel_values_videos']==row['counterfactual_input_signature']['pixel_values_videos'],
                'Adopted real/shifted pixel signatures changed')
            path=out/(uid+'.prefix.pt');torch.save(prefix,path)
            loaded=torch.load(path,map_location='cpu',weights_only=True)
            require(all(torch.equal(loaded[k],prefix[k]) for k in prefix),'Prefix save/reload exact')
            case=dict(uid=uid,sid=sid,source_sha256=row['source_sha256'],original_request_ref=row['request_ref'],
                original_window_ref=complete['window_refs'][uid],prefix_ref=ref(path),options=options,
                suffixes=suffixes,signatures=dict(real=sig,shifted=shift_sig),text=metadata,
                original_input_QA='ADOPTED_ORIGINAL_ACCEPTED_PIXELS; new text independently checked',labels_read=False)
            dst=out/(uid+'.json');save(dst,case);case_refs.append(ref(dst))
            del values,newvalues,shifted
        store.close()
    require(len(case_refs)==43,'All43 real CPU inputs required before any GPU')
    result=dict(status='PASS_FIRST_NEW_VISUAL_CHOICE_INPUTS_43',case_refs=case_refs,source_count=8,window_count=43,
                new_decode=0,new_image_processor=0,new_model_calls=0,seconds=time.monotonic()-started,
                registration_ref=ref(root/'registration03.json'),protocol_ref=reg['protocol_ref'])
    save(root/'input_acceptance03.json',result);print(json.dumps({k:v for k,v in result.items() if k!='case_refs'}))


def gpu(root):
    started=time.monotonic()
    root,W,reg,protocol,complete,manifest,Store,permute,_,canonical=context(root)
    require(os.environ.get('CUDA_VISIBLE_DEVICES') not in (None,'','-1'),'Shared GPU wrapper must expose CUDA')
    sys.path.insert(0,str(W/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/temporal_sft8b_v1'))
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    admission=json.loads((root/'gpu_admission03.json').read_text())
    require(admission['registration_ref']==ref(root/'registration03.json') and admission['approved'] is True,
            'Separate input-bound GPU admission required')
    accepted=loadref(admission['input_acceptance_ref'],W)
    require(accepted['status']=='PASS_FIRST_NEW_VISUAL_CHOICE_INPUTS_43','No GPU before all input acceptance')
    import torch,transformers
    from transformers import Qwen3VLForConditionalGeneration,AutoTokenizer
    require(transformers.__version__=='4.57.1' and torch.cuda.is_available(),'Pinned local Qwen CUDA runtime')
    spec=manifest['model_spec']
    base=Qwen3VLForConditionalGeneration.from_pretrained(spec['model_dir'],revision=spec['revision'],
        local_files_only=True,trust_remote_code=False,torch_dtype=torch.bfloat16,device_map={'':'cuda:0'},
        low_cpu_mem_usage=True,attn_implementation='sdpa').eval()
    for p in base.parameters():p.requires_grad_(False)
    before=canonical(base,torch)
    require(before['parameters']==8767123696 and before['sha256']==spec['base_sha256'],'Actual original unadaptedBASE bytes')
    require(not any('lora_' in n for n,_ in base.named_parameters()),'New judgment uses pureBASE; no hidden activeTIME')
    tokenizer=AutoTokenizer.from_pretrained(spec['model_dir'],local_files_only=True,revision=spec['revision'])
    eos=tokenizer.convert_tokens_to_ids('<|im_end|>');require(eos==151645,'Pinned EOS')
    out=root/'outputs03';out.mkdir();events=root/'model_events03.jsonl'
    count=[0];current=['NO_CASE']
    def hook(module,args):
        require(time.monotonic()-started<protocol['max_gpu_seconds'],'Actual model phase budget')
        require(not base.training and all(not p.requires_grad for p in base.parameters()),'Every actual forward must be frozenBASE')
        require(current[0]!='NO_CASE','Forward outside registered case')
        count[0]+=1
    handle=base.model.register_forward_pre_hook(hook)
    def event(name,**values):
        with events.open('a') as f:f.write(json.dumps(dict(event=name,**values),allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())
    store=Store(manifest,'check');outputs=[];generations=0;adopted=0
    cases=[loadref(r,W) for r in accepted['case_refs']]
    cases.sort(key=lambda x:(x['sid'],x['uid']))
    for case in cases:
        request,original,clock=store.case(case['uid'])
        prefix=torch.load(checked(case['prefix_ref'],W),map_location='cpu',weights_only=True)
        values=dict(original,**prefix)
        for arm in protocol['arms']:
            actual=values if arm=='real' else permute(values)
            require(signature(actual)==case['signatures'][arm],'Actual four tensors differ from first acceptance')
            if arm=='shifted' and case['signatures']['real']==case['signatures']['shifted']:
                prior=outputs[-1];require(prior['arm']=='real' and prior['uid']==case['uid'],'Identical-input adoption needs real output')
                adopted+=1
                record=dict(prior,arm=arm,actual_model_call=False,adopted_exact_input_ref=ref(out/(case['uid']+'.real.json')))
            else:
                require(generations<86,'Registered generation cap')
                current[0]=case['uid']+':'+arm;start_count=count[0]
                trie=ChoiceTrie(actual['input_ids'].shape[1],case['suffixes'])
                event('BEGIN_GENERATION',uid=case['uid'],arm=arm,case_ref=ref(root/'inputs03'/(case['uid']+'.json')))
                placed={k:v.to('cuda:0') for k,v in actual.items()}
                generations+=1
                with torch.inference_mode():
                    generated=base.generate(**placed,do_sample=False,num_beams=1,num_return_sequences=1,
                        max_new_tokens=max(len(v) for v in case['suffixes'].values()),
                        prefix_allowed_tokens_fn=trie,eos_token_id=eos,pad_token_id=eos,
                        repetition_penalty=1.0,use_cache=True)
                ids=generated[0,actual['input_ids'].shape[1]:].detach().cpu().tolist()
                raw=dict(uid=case['uid'],arm=arm,ids=ids,text=tokenizer.decode(ids,skip_special_tokens=False,
                    clean_up_tokenization_spaces=False),forward_calls=count[0]-start_count,actual_model_call=True)
                save(out/(case['uid']+'.'+arm+'.raw.json'),raw)
                require(torch.equal(generated[0,:actual['input_ids'].shape[1]].cpu(),actual['input_ids'][0]),'Generation altered prefix')
                choice=trie.complete(ids)
                require(ids[-1]==eos and eos not in ids[:-1] and count[0]>start_count,'Incomplete answer is not empty')
                decoded=tokenizer.decode(ids[:-1],skip_special_tokens=False,clean_up_tokenization_spaces=False)
                require(json.loads(decoded)==dict(choice=choice),'JSON/trie decode mismatch')
                option=case['options'][choice]
                record=dict(uid=case['uid'],sid=case['sid'],arm=arm,choice=choice,original_slot=option['slot'],
                    selected_ordinals=option['selected_ordinals'],ids=ids,input_signature=signature(actual),
                    source_sha256=case['source_sha256'],raw_ref=ref(out/(case['uid']+'.'+arm+'.raw.json')),
                    actual_model_call=True,forward_calls=count[0]-start_count,labels_read=False)
                del placed,generated
            save(out/(case['uid']+'.'+arm+'.json'),record);outputs.append(record)
            event('ACCEPTED',uid=case['uid'],arm=arm,actual_model_call=record['actual_model_call'])
        del original,values,actual
    store.close();handle.remove();current[0]='NO_CASE'
    after=canonical(base,torch);require(after==before,'BASE changed during frozen inference')
    require(len(outputs)==86 and generations+adopted==86 and count[0]>0,'Complete86 logical outputs required')
    result=dict(status='COMPLETE_VISUAL_CHOICE_MODEL_NOT_QUALITY',new_generations=generations,
        identical_input_adoptions=adopted,logical_outputs=86,top_level_forward_calls=count[0],
        output_refs=[ref(out/(x['uid']+'.'+x['arm']+'.json')) for x in outputs],
        base_before=before,base_after=after,actual_resident_parameters=8767123696,
        conservative_pipeline_parameters=8782557449,new_updates=0,labels_read=False,
        seconds=time.monotonic()-started,automatic_production=False)
    save(root/'gpu_completion03.json',result);print(json.dumps({k:v for k,v in result.items() if k!='output_refs'}))


def review(root):
    root,W,reg,protocol,complete,manifest,Store,_,_,_=context(root)
    admission=json.loads((root/'review_admission03.json').read_text())
    require(admission['registration_ref']==ref(root/'registration03.json'),'Review registration changed')
    model=loadref(admission['gpu_completion_ref'],W)
    require(model['status']=='COMPLETE_VISUAL_CHOICE_MODEL_NOT_QUALITY','Natural complete model phase required')
    # Independent: reconstruct selection from recorded token IDs and frozen trie,
    # never trust only the GPU's selected_ordinals field.
    accepted=loadref(admission['input_acceptance_ref'],W)
    cases={c['uid']:c for c in [loadref(r,W) for r in accepted['case_refs']]}
    selected={arm:{s:set() for s in complete['sources']} for arm in protocol['arms']}
    seen=set()
    for reference in model['output_refs']:
        row=loadref(reference,W);case=cases[row['uid']];key=(row['uid'],row['arm'])
        require(key not in seen,'Duplicate output');seen.add(key)
        trie=ChoiceTrie(case['signatures']['real']['input_ids']['shape'][1],case['suffixes'])
        index=trie.complete(row['ids']);option=case['options'][index]
        require(index==row['choice'] and option['slot']==row['original_slot'] and
                option['selected_ordinals']==row['selected_ordinals'] and
                row['input_signature']==case['signatures'][row['arm']], 'Independent token/action/native replay mismatch')
        selected[row['arm']][case['sid']].update(option['selected_ordinals'])
    require(len(seen)==86,'Missing real/shifted window')
    spec=importlib.util.spec_from_file_location('oracle_api03',root.parent/'diagnostic.py')
    api=importlib.util.module_from_spec(spec);spec.loader.exec_module(api)
    import numpy as np
    store=Store(manifest,'check');metrics={}
    for arm in protocol['arms']:
        rows=[]
        for sid in sorted(store.source_ids):
            human=store.source_supervision(sid);n=len(human['clock']['normalized_exact_pts'])
            require(all(len(m)==n and all(m) for m in human['known_masks']),'UNKNOWN is not negative')
            labels=np.zeros((n,len(human['raters'])),dtype=bool)
            for i,g in enumerate(human['raters']):labels[sorted(g),i]=True
            current=selected[arm][sid];old=set(complete['sources'][sid]['candidates'][0]['selected_ordinals'])
            rows.append(dict(source_id=sid,f1=api.utility(current,labels),selected=len(current),
                original_TIME_f1=api.utility(old,labels),added=len(current-old),deleted=len(old-current),
                false_empty=not current and bool(old) and bool(labels.any())))
        metrics[arm]=dict(macro_f1=sum(v['f1'] for v in rows)/8,selected=sum(v['selected'] for v in rows),
            added=sum(v['added'] for v in rows),deleted=sum(v['deleted'] for v in rows),
            wins=sum(v['f1']>v['original_TIME_f1'] for v in rows),losses=sum(v['f1']<v['original_TIME_f1'] for v in rows),
            false_empty_sources=[v['source_id'] for v in rows if v['false_empty']],per_source=rows)
    prior=loadref(reg['prior_local_choice_ref'],W)
    TIME=prior['original_TIME_f1_adopted'];shape=prior['metrics']['shape']['macro_f1']
    reasons=[]
    for name,bound in [('TIME',TIME),('PRIOR_SHAPE',shape),('SHIFTED',metrics['shifted']['macro_f1'])]:
        if not metrics['real']['macro_f1']>bound:reasons.append('REAL_NOT_BETTER_THAN_'+name)
    if metrics['real']['false_empty_sources']:reasons.append('NEW_FALSE_EMPTY_SOURCE')
    result=dict(status='STOP_VISUAL_CHOICE_MECHANISM' if reasons else 'ELIGIBLE_FOR_SEPARATE_MAIN_REVIEW',
        stop_reasons=reasons,metrics=metrics,old_TIME=TIME,prior_shape=shape,
        independent_all86_token_native_output_QA='PASS',historical_exposed=True,official_score='UNKNOWN',
        automatic_production=False,automatic_submission=False)
    save(root/'review03.json',result);print(json.dumps({k:v for k,v in result.items() if k!='metrics'},ensure_ascii=False))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--run-root',required=True);p.add_argument('--phase',choices=['prepare','gpu','review'],required=True)
    args=p.parse_args()
    try:globals()[args.phase](args.run_root)
    except BaseException:
        save(Path(args.run_root)/('failure_'+args.phase+'03.json'),dict(status='FAILED_EXECUTION_NOT_EMPTY',traceback=traceback.format_exc()))
        raise
