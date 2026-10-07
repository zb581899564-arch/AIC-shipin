"""Generate only proven pre-model decode failures; preserve all valid old raw lines."""
from common import *
import copy
import time


def recover(scope, out):
    config=verify();out=Path(out)
    from sft_contract import verify_live_gpu_reservation
    from temporal_reuse import verify_model
    from engine import load_model,plan_window,encode_window,generate_window,frozen_identity,adapter_identity
    from constrained_json import ascii_token_candidates
    from production import select_frames
    verify_live_gpu_reservation()
    receipt=read(out/'recovery_manifest.json')
    require(receipt['status']=='PASS_DECLARED_PROVIDER_RECOVERY_MANIFEST' and receipt['failed_windows'] and
        sha(out/'provider_temporal.jsonl')==receipt['provider_temporal_sha256'] and
        sha(out/'provider_temporal.stage.json')==receipt['provider_stage_sha256'], 'recovery input binding changed')
    old_stage=read(out/'provider_temporal.stage.json')
    _,manifest,clocks=inputs(scope)
    metadata={r['video_id']:r for r in manifest['records']}
    failed={(r['video_id'],r['index']):r for r in receipt['failed_windows']}
    original_lines=(out/'provider_temporal.jsonl').read_bytes().splitlines(keepends=True)
    model,processor,identity=load_model(config);verify_model(identity)
    write(out/'model_identity.json',identity)
    candidates=ascii_token_candidates(processor.tokenizer)
    started=time.monotonic();recovered=[];unchanged_records=0;unchanged_windows=0;results=[]
    with (out/'temporal.jsonl').open('xb') as stream:
        for line in original_lines:
            original=json.loads(line);record=copy.deepcopy(original);modified=False
            item=metadata[record['video_id']];clock=clocks[item['video_id']]
            for index,window in enumerate(record['windows']):
                key=(item['video_id'],index)
                if key not in failed:
                    require(window['output_valid'] is True,'unregistered failure must not be copied')
                    unchanged_windows+=1
                    continue
                target=failed[key]
                require(hashlib.sha256(json.dumps(window,sort_keys=True).encode()).hexdigest()==
                    target['original_window_sha256'],'original failed-window evidence changed')
                one=time.monotonic();start,end=target['start_sec'],target['end_sec']
                plan=plan_window(item,clock,start,end,index)
                encoded,details=encode_window(processor,plan,config)
                color=read(HERE/'source_color_acceptance.json')
                require(details['frame_pixel_sha256']==color['actual_native_evidence']['frame_pixel_sha256'] and
                    details['source_frame_ids']==color['actual_native_evidence']['source_frame_ids'] and
                    details['actual_pts_sec']==color['actual_native_evidence']['actual_pts_sec'],
                    'actual GPU recovered window differs from registered real conversion CPU evidence')
                result=generate_window(model,processor,encoded,details,plan['window_duration_sec'],candidates)
                del encoded
                result.update(start_sec=start,end_sec=end,index=index,seconds=time.monotonic()-one,
                    clock_branch=clock['branch'],clock_record_sha256=clock['clock_record_sha256'],
                    declared_color_conversion=config['source_color_repair'],original_failure_preserved=True)
                require(result['output_valid'] is True,'real recovery generation failed; do not convert to empty')
                record['windows'][index]=result;modified=True
                recovered.append(dict(video_id=item['video_id'],index=index,status=result['status'],
                    original_window_sha256=target['original_window_sha256'],seconds=result['seconds']))
            for index,window in enumerate(record['windows']):
                if (record['video_id'],index) not in failed:
                    require(window==original['windows'][index],'a previously successful output changed')
            if modified:
                stream.write((json.dumps(record,ensure_ascii=False,allow_nan=False)+'\n').encode('utf-8'))
            else:
                stream.write(line);unchanged_records+=1
            stream.flush();results.append(record)
            progress(out,dict(stage='B2_DECLARED_DECODE_RECOVERY',videos=len(results),total=len(original_lines),
                recovered_windows=len(recovered),original_valid_windows_copied=unchanged_windows,
                original_failure_to_empty_conversions=0))
    require(len(recovered)==len(failed) and unchanged_windows+len(recovered)==521 and len(results)==426,
            'recovery denominator or original successful-window denominator changed')
    require(frozen_identity(model,config)==identity['base'],'base changed during one-window recovery')
    adapter_identity(model,config);select_frames(manifest,results,clocks)
    elapsed=time.monotonic()-started
    write(out/'temporal.stage.json',dict(status='PASS_TEMPORAL_EXECUTION',videos=426,windows=521,invalid_windows=0,
        output_sha256=sha(out/'temporal.jsonl'),logical_parameters=config['complete_parameters'],adapter_enabled=True,
        selected_adapter_sha256=config['b_adapter_sha256'],allow_empty=False,input_contract=config['b2_input_contract'],
        source_lock_sha256=sha(HERE/'source_lock.json'),wall_seconds=old_stage['wall_seconds']+elapsed,
        original_provider_wall_seconds=old_stage['wall_seconds'],actual_recovery_wall_seconds=elapsed,
        original_successful_windows_reused=unchanged_windows,original_record_raw_lines_exact=unchanged_records,
        new_generation_calls=len(recovered),original_failed_windows=len(failed),failures_to_empty_conversions=0,
        original_failure_stage_sha256=sha(out/'provider_temporal.stage.json'),recovery=recovered,
        optimizer_updates=0,official_score=None))


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=('recover',));parser.add_argument('scope');parser.add_argument('out')
    args=parser.parse_args();recover(args.scope,args.out)
