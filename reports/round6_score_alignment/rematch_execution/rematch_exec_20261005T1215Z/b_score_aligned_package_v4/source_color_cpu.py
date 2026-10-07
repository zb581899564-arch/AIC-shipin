"""Reproduce actual failure; validate explicit samples/PTS and RGB/BGR consistency."""
from common import *
import hashlib
import numpy as np


def main():
    bind_helpers()
    from engine import plan_window
    from native_input import decode_window
    from source_color import convert_frame, authorized_source, ColorNativeReader, verify_default_decoder_ast
    from frame_contract import window_schedule
    import av
    config = settings()['source_color_repair']; inventory = {}; special = []; sources = 0
    for scope in ('nontest','rematch'):
        _,manifest,clocks = inputs(scope)
        for item in manifest['records']:
            with av.open(item['source_path']) as container:
                context = container.streams.video[0].codec_context
                profile = tuple(getattr(context,name) for name in ('color_trc','colorspace','color_primaries','color_range'))
                inventory[str(profile)] = inventory.get(str(profile),0)+1
            if profile[0] == 10:
                require(authorized_source(item['source_sha256']), 'additional unsupported source needs independent repair')
                special.append((item,clocks[item['video_id']],manifest['kind']))
            sources += 1
    require(sources == 434 and len(special) == len(config['sources']) == 1, 'registered color-source inventory differs')
    item,clock,kind = special[0]
    require(sha(item['source_path']) == item['source_sha256'], 'registered unsupported source changed')
    with av.open(item['source_path']) as container:
        frame = next(container.decode(container.streams.video[0]))
        try:
            frame.to_ndarray(format='rgb24')
        except OSError as error:
            require(error.errno == 95, 'different original RGB error')
        else:
            raise ValueError('original real unsupported conversion was not reproduced')
        original = frame.to_ndarray(format='yuv420p').copy()
        rgb = convert_frame(frame,item['source_sha256'],'rgb24')
        bgr = convert_frame(frame,item['source_sha256'],'bgr24')
        require(np.array_equal(rgb,bgr[:,:,::-1]) and np.array_equal(original,frame.to_ndarray(format='yuv420p')) and
            frame.color_trc == 10, 'raw sample planes, metadata restoration or RGB/BGR mapping changed')
    # Constant samples exercise the declared limited-range ITU601 mapping.
    tests = 0
    for y,u,v,target in ((16,128,128,(0,0,0)), (235,128,128,(255,255,255)),
                         (128,128,128,(130,130,130)), (81,90,240,(255,0,0))):
        array = np.empty((1280*3//2,720),dtype=np.uint8)
        array[:1280] = y; array[1280:1280+1280//4] = u; array[1280+1280//4:] = v
        frame = av.VideoFrame.from_ndarray(array,format='yuv420p')
        frame.color_trc=10;frame.colorspace=2;frame.color_primaries=2;frame.color_range=1
        value = convert_frame(frame,item['source_sha256'],'rgb24')
        require(int(np.abs(value.astype(int)-np.array(target)).max()) <= 2 and
            np.array_equal(array,frame.to_ndarray(format='yuv420p')), 'declared sample-mapping reference mismatch')
        tests += 1
    schedule=window_schedule(item,kind,clock);require(len(schedule)==1,'declared original failed-window count differs')
    start,end=schedule[0];window=plan_window(item,clock,start,end,0)
    array,metadata,plan,evidence=decode_window(window)
    require(len(array)==64 and evidence['source_frame_ids']==window['planned_source_frame_ordinals'] and
        evidence['actual_pts_sec']==window['planned_actual_pts_sec'],'converted production window actual PTS/frame IDs differ')
    reader=ColorNativeReader(item,clock)
    try:
        for n,index in enumerate(evidence['source_frame_ids']):
            bgr,digest=reader.get(index)
            require(np.array_equal(array[n],bgr[:,:,::-1]) and hashlib.sha256(array[n].tobytes()).hexdigest()==
                evidence['frame_pixel_sha256'][n], 'temporal/field actual source pixel identity differs')
    finally:
        reader.close()
    verify_default_decoder_ast(HERE/'production.py',RUN/'next_round_v1/production.py')
    report=dict(status='PASS_B2_DECLARED_COLOR_CONVERSION_CPU',tests=tests+5,
        source_headers=434,changed_color_sources=1,actual_converted_frames=64,
        original_errno95_reproduced=True,raw_YUV_planes_unchanged=True,original_metadata_restored=True,
        temporal_RGB_field_BGR_exact=True,source_pts_unchanged=True,default_other_sources_unchanged=True,
        gamma_curve_recovered=False,explicit_conversion_recipe=config,source_sha256=item['source_sha256'],
        actual_production_window=window,actual_native_evidence=evidence,
        synthetic_sample_cases=tests,header_profiles=inventory,actual_CUDA_started=False,optimizer_updates=0,
        contest_media_content_visually_inspected=False,source_pixels_used_for_hyperparameter_tuning=False)
    write(HERE/'source_color_acceptance.json',report)
    print(json.dumps({k:v for k,v in report.items() if k not in ('actual_production_window','actual_native_evidence')}))


if __name__ == '__main__':
    main()
