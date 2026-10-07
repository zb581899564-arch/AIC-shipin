"""Actual fixed processor, native clock and physical non-test source acceptance."""
from common import *
import time


def main():
    bind_helpers()
    import torch
    from transformers import AutoProcessor
    from engine import prompt_for, encode_window, plan_window
    from frame_contract import window_schedule
    from video_contract import encode, identity
    from exact_pts import exact_native_pts, verify_native_encoding
    from native_frames import prepare_native_processor_input
    from native_input import decode_window
    config = settings(); started = time.monotonic()
    processor = AutoProcessor.from_pretrained(config['model_dir'], local_files_only=True, min_pixels=131072,max_pixels=131072)
    require(processor.video_processor.size == config['video_size'], 'B2 processor changed')
    cases = []
    for count in (1,3,63,64):
        import numpy as np
        array = np.zeros((count,72,128,3), dtype=np.uint8)
        ids = list(range(count)); points=[.4*index for index in ids]
        metadata = dict(fps=2, frames_indices=ids, total_num_frames=count, video_backend='synthetic')
        plan = dict(source_frame_ids=ids, source_relative_pts=points, window_start=0)
        array, metadata = prepare_native_processor_input(array,metadata,plan)
        with exact_native_pts(processor,plan,2) as native:
            encoded = encode(processor,text=[prompt_for(processor)],videos=[torch.from_numpy(array).permute(0,3,1,2)],
                video_metadata=[metadata],video_size=config['video_size'],max_input=config['max_input_tokens'])
            verify_native_encoding(processor,encoded,native)
        cases.append(dict(physical_frames=count, processor_frames=len(array), native_identity=native,
                          input_identity=identity(processor,encoded,len(array))))
        del array, encoded
    hd = torch.zeros((64,3,1080,1920),dtype=torch.uint8)
    metadata = dict(fps=30,frames_indices=[14*index for index in range(64)],total_num_frames=900,video_backend='decord')
    text = prompt_for(processor)
    legacy = processor(text=[text],videos=[hd],video_metadata=[dict(metadata)],padding=True,
                       do_sample_frames=False,truncation=False,return_tensors='pt')
    explicit = encode(processor,text=[text],videos=[hd],video_metadata=[dict(metadata)],video_size=config['video_size'])
    for key in ('input_ids','attention_mask','pixel_values_videos','video_grid_thw'):
        require(torch.equal(legacy[key],explicit[key]), 'B2 HD explicit pixels changed: '+key)
    require(8192 < int(explicit['input_ids'].shape[1]) <= 16384, 'real processor did not exercise the old context failure')
    cases.append(dict(hd=True, tensors_equal_to_original_B_defaults=True,input_identity=identity(processor,explicit,64)))
    del hd, legacy, explicit
    _, manifest, clocks = inputs('nontest')
    for item in manifest['records']:
        clock=clocks[item['video_id']]
        start,end = window_schedule(item,manifest['kind'],clock)[0]
        plan = plan_window(item,clock,start,end,0)
        encoded, details = encode_window(processor,plan,config)
        array, _, _, reopened = decode_window(plan)
        require(reopened['frame_pixel_sha256'] == details['frame_pixel_sha256'] and
                reopened['actual_pts_sec'] == details['actual_pts_sec'], 'real reopened native frame identity differs')
        require(len(details['window_source_pts_sec']) == plan['eligible_source_frame_count'],
                'unsampled actual source PTS missing from realizability evidence')
        cases.append(dict(video_id=item['video_id'], clock_branch=clock['branch'], physical_frames=len(details['source_frame_ids']),
            processor_frames=len(array), actual_source_pts_count=len(details['window_source_pts_sec']),
            source_sha256=item['source_sha256'], reopened_64_frame_pixel_sha_equal=True,
            native_processor_identity=details['native_processor_identity'], input_tokens=details['input_tokens']))
        del array, encoded
    write(HERE / 'processor_acceptance.json', dict(status='PASS_B2_REAL_PROCESSOR_AND_NATIVE_SOURCE',
        cases=cases, actual_source_videos=8, HD_defaults_tensor_equal=True, same_encode_function_as_production=True,
        synthetic_cases=5, actual_CUDA_started=False, optimizer_updates=0, confirm_read=False,
        rematch_pixels_read=False, wall_seconds=time.monotonic()-started))
    print('PASS_B2_REAL_PROCESSOR_AND_NATIVE_SOURCE', flush=True)


if __name__ == '__main__':
    main()
