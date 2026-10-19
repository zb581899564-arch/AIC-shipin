"""One new whole-window TIME prefill; last-layer temporal pooling only."""
import argparse
import sys
import time
from collections import defaultdict
from pathlib import Path

from common import *
from data import source_pixels
from mapping import pair_image_pixels


def infer(scope, phase):
    import numpy as np
    import torch
    require(os.environ.get('CUDA_VISIBLE_DEVICES', '') != '', 'GPU parent must retain its actual CUDA index')
    torch.set_num_threads(2)
    lock = read(ROOT/('source_lock_'+scope+'.json'))
    acceptance = read(checked(lock['acceptance']))
    for filename, digest in lock['code'].items():
        require(sha(ROOT/'code'/filename) == digest, 'Frozen new runtime code changed')
    require(acceptance['status'] == 'PASS_ALL_NEW_VIDEO_INPUTS_AND_FIRST_INDEPENDENT_QA', 'Actual input QA gate')
    cfg = read(checked(lock['model_config']))
    for directory in (RUN/'b_score_aligned_package_v4', RUN/'temporal_sft8b_v1', RUN/'baseline_a_pts_v1'):
        sys.path.insert(0, str(directory))
    from sft_contract import verify_live_gpu_reservation
    import engine
    verify_live_gpu_reservation()
    selected = set(acceptance['pilot_case_ids']) if phase == 'pilot32' else None
    if phase == 'remaining_external':
        selected = {x['case_id'] for x in acceptance['cases']}-set(acceptance['pilot_case_ids'])
        require(read(ROOT/'pilot32_acceptance.json')['status']=='PASS32_REAL_TIME_GROUP_FEATURES_AND_COST', 'Pilot32 must pass')
    if selected is None:
        selected = {x['case_id'] for x in acceptance['cases']}
    require(selected and len(selected)==(32 if phase=='pilot32' else len(selected)), 'Nonempty fixed GPU phase')
    out = ROOT/('features_'+scope);out.mkdir(exist_ok=True)
    # Completion receipts prohibit repeating a successful prefill, even in another phase.
    require(all(not (out/(cid+'.json')).exists() and not (out/(cid+'.pt')).exists() for cid in selected),
            'New phase would repeat a successful feature prefill')
    attempt = ROOT/(phase+'_attempts.jsonl')
    with attempt.open('x'):
        pass
    def record(**row):
        with attempt.open('a') as stream:
            stream.write(json.dumps(dict(utc=utc(), **row))+'\n');stream.flush();os.fsync(stream.fileno())
    started = time.monotonic()
    model, processor, identity = engine.load_model(cfg)
    require(identity['logical_parameters'] == 8782459120 and identity['adapter']['adapter_enabled']
            and model.active_adapter == 'default', 'Actual frozen original TIME identity')
    native = model.get_base_model();core = native.model
    require(all(not p.requires_grad for p in model.parameters()), 'Whole backbone and adapter frozen')
    versions = [(p,p._version) for p in model.parameters()]
    write(ROOT/(phase+'_model_identity.json'),dict(identity=identity,model_parameters=sum(p.numel() for p in model.parameters()),
         selected_cases=sorted(selected),new_optimizer_updates=0,feature_layer='FINAL_TEXT_RMS_NORM_VIDEO_TOKEN_SPATIAL_MEAN_PLUS_LAST_PREFILL_STATE'))
    completed=[];forward_times=[]
    for source in acceptance['sources']:
        windows=[x for x in source['windows'] if x['case_id'] in selected]
        if not windows:
            continue
        frames, grid_hw, ordinals=source_pixels(source,verify=True)
        for row in windows:
            cid=row['case_id'];request=read(checked(row['request']))
            require(request['source_sha256']==source['source_sha256'] and request['clock_sha256']==source['clock']['sha256'],
                    'Actual request/source clock identity')
            tokens=torch.load(checked(request['tokens']),map_location='cpu',weights_only=True)
            start,end=request['source_start_cell'],request['source_end_cell']
            require(ordinals[start:end]==request['source_ordinals'], 'Actual observed native ordinals')
            pixels,grid=pair_image_pixels(frames[start:end],grid_hw)
            encoded=dict(**tokens,pixel_values_videos=pixels,video_grid_thw=grid.unsqueeze(0))
            require(signature(encoded)==request['input_signature'], 'Actual CPU input changed after first QA')
            gpu={key:value.to('cuda') for key,value in encoded.items()}
            positions=torch.tensor(request['text_evidence']['group_token_positions'],device='cuda',dtype=torch.long)
            actual_id=(gpu['input_ids'][0]==processor.tokenizer.convert_tokens_to_ids(processor.video_token)).nonzero().flatten()
            require(torch.equal(actual_id,positions.flatten()), 'Actual video token ownership before forward')
            captured=[]
            def pool(_module,_inputs,output):
                require(output.ndim==3 and output.shape[0]==1, 'One actual window norm state')
                temporal=output[0,positions].float().mean(dim=1)
                context=output[0,-1].float().expand(len(positions),-1)
                captured.append(torch.cat([temporal,context],dim=-1).cpu().contiguous())
            handle=core.language_model.norm.register_forward_hook(pool)
            record(event='BEGIN_NEW_WHOLE_WINDOW_PREFILL',case_id=cid,request_sha256=row['request']['sha256'])
            one=time.monotonic()
            try:
                with torch.inference_mode():
                    result=core(**gpu,use_cache=False,return_dict=True)
                torch.cuda.synchronize()
            finally:
                handle.remove()
            seconds=time.monotonic()-one
            require(len(captured)==1 and captured[0].ndim==2 and
                    len(captured[0])==len(request['global_group_ids']) and bool(torch.isfinite(captured[0]).all()),
                    'Actual finite final-layer temporal groups and context')
            file=out/(cid+'.pt')
            torch.save(dict(features=captured[0],group_ids=torch.tensor(request['global_group_ids']),
                            source_sha256=source['source_sha256'],request_sha256=row['request']['sha256']),file)
            receipt=dict(status='ACCEPTED_NEW_TIME_CONTEXT_FEATURES',case_id=cid,source_id=source['id'],
                         request=row['request'],input_signature=request['input_signature'],features=reference(file),
                         tensor_sha256=tensor_sha(captured[0]),shape=list(captured[0].shape),
                         group_ids=request['global_group_ids'],seconds=seconds,actual_new_forward=True,
                         actual_video_grid=grid.tolist(),model_identity=reference(ROOT/(phase+'_model_identity.json')))
            write(out/(cid+'.json'),receipt);completed.append(reference(out/(cid+'.json')));forward_times.append(seconds)
            record(event='ACCEPTED_NEW_WHOLE_WINDOW_PREFILL',case_id=cid,features_sha256=receipt['features']['sha256'])
            event('NEW_TIME_FEATURES_SAVED',phase=phase,case_id=cid,completed=len(completed),total=len(selected),seconds=seconds)
            del result,gpu,encoded,pixels,captured
        del frames
    require(len(completed)==len(selected) and all(p._version==v and not p.requires_grad for p,v in versions),
            'Complete new forward count or frozen parameter version changed')
    require(engine.frozen_identity(model,cfg)==identity['base'] and engine.adapter_identity(model,cfg)==identity['adapter'],
            'Frozen base/adapter actual identity changed after new feature extraction')
    write(ROOT/(phase+'_feature_completion.json'),dict(status='PASS_ALL_REGISTERED_NEW_TIME_FEATURE_FORWARDS',
         phase=phase,scope=scope,actual_new_forwards=len(completed),entries=completed,
         forward_seconds=sum(forward_times),elapsed_seconds=time.monotonic()-started,
         max_window_seconds=max(forward_times),model_parameters=identity['logical_parameters'],
         new_backbone_optimizer_updates=0,attempts=reference(attempt),labels_read=False))


def independent_output_qa(scope,phase):
    assert_cpu()
    import numpy as np
    import torch
    completion=read(ROOT/(phase+'_feature_completion.json'))
    accepted=read(ROOT/('acceptance_'+scope+'.json'))
    cases={r['case_id']:r for r in accepted['cases']}
    seen=[];dimensions=set()
    for ref in completion['entries']:
        receipt=read(checked(ref));cid=receipt['case_id'];request=read(checked(cases[cid]['request']))
        payload=torch.load(checked(receipt['features']),map_location='cpu',weights_only=True)
        feature=payload['features']
        require(payload['source_sha256']==request['source_sha256'] and
                payload['request_sha256']==cases[cid]['request']['sha256'], 'Independent model output/source byte binding')
        require(feature.dtype==torch.float32 and list(feature.shape)==receipt['shape'] and
                tensor_sha(feature)==receipt['tensor_sha256'] and torch.isfinite(feature).all(), 'Independent persisted feature tensor')
        require(payload['group_ids'].tolist()==request['global_group_ids']==receipt['group_ids'] and
                len(feature)==request['video_grid_thw'][0], 'Independent time token/native mapping')
        require(len(set(payload['group_ids'].tolist()))==len(feature), 'No duplicate group in one window')
        dimensions.add(feature.shape[1]);seen.append(cid)
    require(len(seen)==len(set(seen))==completion['actual_new_forwards'] and len(dimensions)==1, 'Independent all-output denominator')
    write(ROOT/(phase+'_output_QA.json'),dict(status='PASS_ALL_FIRST_OUTPUT_QA_WITHOUT_NEW_FORWARD',
          cases=seen,dimension=dimensions.pop(),completion=reference(ROOT/(phase+'_feature_completion.json')),
          new_forwards=0,source_count=len({cases[c]['source_id'] for c in seen})))
    if phase=='pilot32':
        require(len(seen)==32,'Actual32 pilot count')
        mean=completion['forward_seconds']/32
        write(ROOT/'pilot32_acceptance.json',dict(status='PASS32_REAL_TIME_GROUP_FEATURES_AND_COST',
             actual_new_forwards=32,distinct_sources=len({cases[c]['source_id'] for c in seen}),
             feature_dimension=read(ROOT/(phase+'_output_QA.json'))['dimension'],
             mean_forward_seconds=mean,projected_external_forward_seconds=mean*accepted['window_count'],
             output_QA=reference(ROOT/(phase+'_output_QA.json')),elapsed_seconds=completion['elapsed_seconds'],
             original_media_decodes=0,original_successful_processor_calls_repeated=0,
             scope='Engineering/cost only, no new independent quality confirmation'))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['infer','qa']);p.add_argument('scope',choices=['external','production'])
    p.add_argument('phase',choices=['pilot32','remaining_external','production'])
    a=p.parse_args()
    try:
        (infer if a.mode=='infer' else independent_output_qa)(a.scope,a.phase)
    except BaseException as exc:
        import traceback
        failure=ROOT/(a.phase+'_'+a.mode+'_failure.json')
        if not failure.exists():write(failure,dict(error=repr(exc),traceback=traceback.format_exc(),utc=utc()))
        raise
