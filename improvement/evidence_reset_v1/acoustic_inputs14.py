"""First exact8s acoustic inputs from retained media/PCM; no new video decode."""
import argparse
from fractions import Fraction as F
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import time
import traceback


def module(path, name):
    spec=importlib.util.spec_from_file_location(name,path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


def read(p): return json.loads(Path(p).read_text())


def save(p, value):
    with Path(p).open('x') as f:json.dump(value,f,indent=2,allow_nan=False)


def ref(p):
    p=Path(p).resolve(strict=True);h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''):h.update(b)
    return dict(path=str(p),bytes=p.stat().st_size,sha256=h.hexdigest())


def check(r):
    assert ref(r['path'])==r,'Bound original bytes';return Path(r['path'])


def verify_mapping(np, wave, observed, rows, values, offsets, starts, start, end):
    visited=np.zeros(len(wave),bool)
    for r in rows:
        i=r['frame'];lo=r['frame_first'];hi=r['frame_stop']
        pos=np.arange(r['grid_first'],r['grid_first']+hi-lo)
        fresh=~visited[pos];expected=values[offsets[i]+lo:offsets[i]+hi]
        assert np.array_equal(wave[pos[fresh]],expected[fresh])
        actual=starts[i]+F(lo,16000)
        assert start<=actual<end
        residual=(starts[i]-start)*16000-math.floor((starts[i]-start)*16000)
        assert str(residual)==r['sub_sample_grid_residual_exact'] and 0<=residual<1
        visited[pos]=True
    assert np.array_equal(visited,observed) and not wave[~observed].any()
    missing=~observed
    assert int(missing.sum())<=16,'Only submillisecond grid holes admitted; no physical audio gaps'
    assert not np.any(missing[1:]&missing[:-1]),'No consecutive missing audio samples'
    assert len(wave)==128000 and observed[0] and observed[-1]


def prepare(root):
    import av,numpy as np,torch
    torch.set_num_threads(2)
    N=Path(root);R=N.parent;W=R.parent;t=time.monotonic()
    reg=read(N/'registration14.json');inv=read(check(reg['inventory_ref']))
    old=module(check(inv['original_author_code_ref']),'accepted_audio_functions14')
    _,audio,proof=old.original_modules(W/'bottleneck_24h_20261019_v1/audio_semantic23/author')
    out=N/'inputs14';out.mkdir();receipts={};new_decodes=[];adopted=[]
    for sha,s in inv['sources'].items():
        clock=read(check(s['original_clock_ref']));origin=F(clock['original_exact_pts'][0]);assert origin==0
        if s['retained_PCM_ref'] is not None:
            with np.load(check(s['retained_PCM_ref']),allow_pickle=False)as z:
                values=z['values'];offsets=z['offsets'];starts=list(map(F,z['starts_exact'].tolist()))
            source_ref=s['retained_PCM_ref'];adopted.append(sha)
        else:
            media=Path(s['media_path']);assert ref(media)==dict(path=str(media),bytes=s['media_bytes'],sha256=sha)
            parts=[];starts=[];count=0
            with av.open(str(media))as c:
                stream=c.streams[s['audio_streams'][0]['index']]
                assert stream.type=='audio'
                resample=av.AudioResampler(format='fltp',layout='mono',rate=16000)
                def consume(frames):
                    for frame in frames:
                        assert frame.pts is not None and frame.time_base is not None and frame.sample_rate==16000
                        v=np.asarray(frame.to_ndarray(),dtype=np.float32).reshape(-1)
                        stamp=F(frame.pts)*F(frame.time_base)-origin
                        assert len(v)==frame.samples and np.isfinite(v).all() and (not starts or stamp>=starts[-1])
                        starts.append(stamp);parts.append(v.copy())
                for packet in c.demux(stream):
                    for frame in packet.decode():
                        count+=1;consume(resample.resample(frame))
                consume(resample.resample(None))
            assert parts
            offsets=np.r_[0,np.cumsum([len(v)for v in parts])].astype(np.int64);values=np.concatenate(parts)
            source_ref=dict(media_sha256=sha,decoded_audio_frames=count,source_PCM_in_RAM_only=True,
                raw_values_sha256=hashlib.sha256(values.tobytes()).hexdigest(),
                original_starts_exact=list(map(str,starts)),original_offsets=offsets.tolist())
            # Explicit registered ephemeral full-source buffer; all requested excerpts durable.
            new_decodes.append(sha)
        for uid,c in inv['cases'].items():
            if c['source_sha256']!=sha:continue
            start,end=F(c['start_exact']),F(c['end_exact']);assert end-start==8
            wave,observed,mappings=old.clip_from_frames(values,offsets,starts,start,end)
            verify_mapping(np,wave,observed,mappings,values,offsets,starts,start,end)
            p=out/(uid+'.npz');np.savez_compressed(p,wave=wave,observed=observed)
            with np.load(p,allow_pickle=False)as z:
                assert np.array_equal(z['wave'],wave) and np.array_equal(z['observed'],observed)
            mel=audio['log_mel_spectrogram'](audio['pad_or_trim'](torch.from_numpy(wave.copy())))
            assert mel.dtype==torch.float32 and tuple(mel.shape)==(80,3000) and torch.isfinite(mel).all()
            mp=out/(uid+'.mel.npz');np.savez_compressed(mp,mel=mel.numpy())
            with np.load(mp,allow_pickle=False)as z:assert np.array_equal(z['mel'],mel.numpy())
            receipt=dict(uid=uid,source_sha256=sha,start_exact=str(start),end_exact=str(end),
                waveform_ref=ref(p),mel_ref=ref(mp),original_clock_ref=s['original_clock_ref'],
                original_media_path=s['media_path'],sample_rate=16000,samples=128000,
                observed_samples=int(observed.sum()),missing_samples=int((~observed).sum()),
                missing_not_observed_silence=True,source_PCM_ref=source_ref,mapping=mappings,
                original_mel_AST_proof=proof,right_padding_samples=352000,padding_is_input_only_not_label=True,
                independent_native_sample_QA=True,lossless_mel_roundtrip=True)
            rp=out/(uid+'.json');save(rp,receipt);receipts[uid]=ref(rp)
        with (N/'preparation_events14.jsonl').open('a')as f:
            f.write(json.dumps(dict(event='SOURCE_FIRST_AUDIO_INPUTS_ACCEPTED',source_sha256=sha,accepted=len(receipts)))+'\n');f.flush();os.fsync(f.fileno())
        assert time.monotonic()-t<reg['max_prepare_seconds']
        assert sum(p.stat().st_size for p in N.rglob('*')if p.is_file())<reg['max_total_bytes']
    assert len(receipts)==100 and len(new_decodes)==22 and len(adopted)==4
    result=dict(status='PASS_FIRST100_EXACT8S_ACOUSTIC_INPUTS',case_refs=receipts,inventory_ref=reg['inventory_ref'],
        first_new_audio_source_decodes=len(new_decodes),retained_PCM_sources_adopted=len(adopted),
        video_decode=0,new_model_calls=0,new_download=0,new_fit=0,
        seconds=time.monotonic()-t,stage_bytes=sum(p.stat().st_size for p in N.rglob('*')if p.is_file()))
    save(N/'input_acceptance14.json',result)
    print(json.dumps({k:v for k,v in result.items()if k!='case_refs'}))


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--run-root',required=True);args=a.parse_args()
    try:prepare(args.run_root)
    except BaseException:
        save(Path(args.run_root)/'failure_prepare14.json',dict(status='ACTUAL_FAILURE_NO_AUTOMATIC_RETRY',traceback=traceback.format_exc()))
        raise
