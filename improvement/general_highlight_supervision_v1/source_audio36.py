"""First native clocks and observed16k speech inputs for four unused publishers."""
from fractions import Fraction
import importlib.util
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
from pathlib import Path
import sys
import time
import numpy as np

from common import ROOT,WORK,read,ref,save
from pilot_common28 import checked

TARGET=ROOT/'speech36'
OLD=WORK/'bottleneck_24h_20261019_v1/audio_semantic23'
sys.path.append(str(WORK/'highlight_source_control_20261021_v1'))
from native_audit12 import native_clock,known_isolation


def old_helpers():
    record=read(OLD/'registration.json')['code_ref'];path=checked(record)
    spec=importlib.util.spec_from_file_location('author_asr_tensor_and_audio_helpers36',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module,record


def audio_frames(media,origin,out):
    import av
    pieces=[];starts=[]
    with av.open(media['path']) as container:
        streams=list(container.streams.audio)
        if not streams:raise ValueError('No actual source audio stream; never invent transcript')
        stream=min(streams,key=lambda s:s.index);stream.codec_context.thread_count=1
        resampler=av.AudioResampler(format='fltp',layout='mono',rate=16000)
        def consume(frames):
            for frame in frames:
                if frame.pts is None or frame.time_base is None or frame.sample_rate!=16000:
                    raise ValueError('Native audio time unavailable')
                values=np.asarray(frame.to_ndarray(),dtype=np.float32).reshape(-1)
                if len(values)!=frame.samples or not np.isfinite(values).all():raise ValueError('Invalid observed waveform')
                stamp=Fraction(frame.pts)*frame.time_base-origin
                if starts and stamp<starts[-1]:raise ValueError('Audio presentation order changed')
                starts.append(stamp);pieces.append(values.copy())
        for packet in container.demux(stream):
            for frame in packet.decode():consume(resampler.resample(frame))
        consume(resampler.resample(None))
    if not pieces:raise ValueError('No observed audio samples')
    offsets=np.r_[0,np.cumsum([len(x) for x in pieces])].astype(np.int64);values=np.concatenate(pieces)
    path=out/'original_resampled_frames.npz'
    np.savez_compressed(path,values=values,offsets=offsets,starts_exact=np.asarray(list(map(str,starts))))
    with np.load(path,allow_pickle=False) as data:
        if not np.array_equal(data['values'],values) or not np.array_equal(data['offsets'],offsets):
            raise ValueError('First waveform serialization differs')
    return values,offsets,starts,ref(path)


def prepare_source(row,helpers,annotations):
    sid=row['sid'];out=TARGET/sid;out.mkdir()
    checked(row['media']);isolation=known_isolation(row['media'])
    clock=native_clock(Path(row['media']['path']));save(out/'clock.json',clock)
    origin=Fraction(clock['first_PTS_exact']);end=Fraction(clock['physical_end_exact'])-origin
    labels=[a for a in annotations if a['video_path']==row['source']['url']]
    if len(labels)!=row['source']['annotators']:raise ValueError('Original reviewer denominator changed')
    for reviewer in labels:
        for s in reviewer['summary_timestamps']:
            if not 0<=Fraction(str(s['start_time']))/1000<Fraction(str(s['end_time']))/1000<=end:
                raise ValueError('Unmodified human endpoint outside original media; exclude whole source')
    save(out/'original_annotations.json',labels)
    values,offsets,starts,full=audio_frames(row['media'],origin,out)
    chunks=[]
    for index,first in enumerate(range(0,int(__import__('math').ceil(float(end))),30)):
        start=Fraction(first);stop=min(start+30,end)
        wave,observed,mapping=helpers.clip_from_frames(values,offsets,starts,start,stop)
        path=out/(f'chunk_{index:03d}.npz');np.savez_compressed(path,wave=wave,observed=observed)
        with np.load(path,allow_pickle=False) as restored:
            if not np.array_equal(restored['wave'],wave) or not np.array_equal(restored['observed'],observed):
                raise ValueError('First chunk waveform serialization differs')
        visited=np.zeros(len(wave),dtype=bool)
        for item in mapping:
            frame=item['frame'];lo=item['frame_first'];hi=item['frame_stop']
            positions=np.arange(item['grid_first'],item['grid_first']+hi-lo);fresh=~visited[positions]
            if not np.array_equal(wave[positions[fresh]],values[offsets[frame]+lo:offsets[frame]+hi][fresh]):
                raise ValueError('Independent native source-frame-to-wave mapping differs')
            visited[positions[fresh]]=True
        if not np.array_equal(visited,observed) or wave[~observed].any():raise ValueError('Unknown audio mask differs')
        chunks.append(dict(index=index,wave=ref(path),start_exact=str(start),end_exact=str(stop),
            samples=len(wave),observed_samples=int(observed.sum()),observed_fraction=float(observed.mean()),
            observed_silence_distinct_from_missing=True,max_grid_error_seconds='1/16000'))
    result=dict(sid=sid,media=row['media'],source=row['source'],isolation=isolation,
        clock=ref(out/'clock.json'),annotations=ref(out/'original_annotations.json'),
        original_audio_frames=full,chunks=chunks,native_frames=clock['native_frames'],
        physical_duration_exact=str(end),all_reviewers=len(labels),no_reference_labels_in_ASR=True,
        waveform_independent_native_mapping_pass=True,unselected_summary_not_explicit_NHL=True)
    save(out/'acceptance.json',result)
    print('NATIVE_AUDIO_ACCEPTED',sid,len(chunks),result['native_frames'],flush=True)
    return ref(out/'acceptance.json')


def main():
    TARGET.mkdir();helpers,code=old_helpers()
    save(TARGET/'preparation_registration.json',dict(
        media_selection=ref(ROOT/'media35/registration.json'),unchanged_audio_helpers=code,
        mode='First native speech inputs only; no visual processor/I3D or old ASR excerpts repeated',
        interval_seconds=30,all_reference_reviewers=True,source_isolation='Known704train/426test bytes; global content/pretraining UNKNOWN'))
    while not (ROOT/'media35/completion.json').exists():time.sleep(2)
    sources=read(ROOT/'media35/completion.json')['accepted']
    annotations=read(ROOT/'lvsum20/annotations__lvsum_72_dataset.json')
    accepted=[];failures=[]
    for row in sources:
        try:accepted.append(prepare_source(row,helpers,annotations))
        except Exception as error:
            failure=dict(sid=row['sid'],error=repr(error),traceback=__import__('traceback').format_exc())
            save(TARGET/(row['sid']+'_failure.json'),failure);failures.append(failure)
            print('NATIVE_AUDIO_FAILED',row['sid'],repr(error),flush=True)
    save(TARGET/'input_acceptance.json',dict(state='NEW_NATIVE_SPEECH_INPUT_TERMINAL',
        accepted=accepted,failures=failures,new_model_calls=0,no_padding_or_stretch_of_labels=True))


if __name__=='__main__':main()
