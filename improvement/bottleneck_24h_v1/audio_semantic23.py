"""Fixed eight external audio excerpts: first waveform/ASR use, no training.

Uses unchanged original-author Whisper tensor core and mel functions. Optional
transcription wrappers are omitted because their dependencies are not installed.
The fixed greedy decoder is explicitly a local pilot, not Whisper's full CLI.
"""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
import ast
import base64
from bisect import bisect_left
from collections import defaultdict
from datetime import datetime, timezone
from fractions import Fraction as F
from functools import lru_cache
import hashlib
import json
import math
from pathlib import Path
import sys
import time
import traceback
import types
from typing import Optional, Union
import zlib
import numpy as np
import torch

W = Path('/home/inspur/aic_video_work')
R = W/'bottleneck_24h_20261019_v1/audio_semantic23'
RATE = 16000


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''):
            h.update(block)
    return h.hexdigest()


def ref(path):
    path = Path(path).resolve(strict=True)
    return dict(path=str(path), bytes=path.stat().st_size, sha256=sha(path))


def bound(value):
    path = Path(value['path']).resolve(strict=True)
    assert path.is_relative_to(W) and path.is_file() and sha(path) == value['sha256']
    return path


def save(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.flush(); os.fsync(stream.fileno())


def event(stage, **values):
    with (R/'journal.jsonl').open('a') as stream:
        stream.write(json.dumps(dict(utc=datetime.now(timezone.utc).isoformat(), stage=stage, **values))+'\n')
        stream.flush(); os.fsync(stream.fileno())


def clip_from_frames(values, offsets, starts, start, end):
    """Observed sample -> fixed16k grid; holes are separately masked, never audio."""
    size = math.ceil((end-start)*RATE)
    output = np.zeros(size, np.float32); observed = np.zeros(size, bool)
    mapping = []
    for index, origin in enumerate(starts):
        data = values[offsets[index]:offsets[index+1]]
        lo = max(0, math.ceil((start-origin)*RATE))
        hi = min(len(data), math.ceil((end-origin)*RATE))
        if hi <= lo:
            continue
        relative = (origin-start)*RATE
        first = math.floor(relative)+lo
        positions = first+np.arange(hi-lo)
        assert positions[0] >= 0 and positions[-1] < size
        keep = ~observed[positions]
        output[positions[keep]] = data[lo:hi][keep]
        observed[positions[keep]] = True
        mapping.append(dict(frame=index, frame_first=lo, frame_stop=hi,
            actual_first_sample_time_exact=str(origin+F(lo,RATE)),
            grid_first=first, kept=int(keep.sum()), overlap_discarded=int((~keep).sum()),
            sub_sample_grid_residual_exact=str(relative-math.floor(relative))))
    return output, observed, mapping


def prepare(reg):
    import av
    assert not (R/'first_audio_inputs.json').exists()
    out = R/'inputs'; out.mkdir()
    selected = reg['selected']; by_source = defaultdict(list)
    for item in selected:
        by_source[item['sid']].append(item)
    receipts = []
    for sid, items in by_source.items():
        manifest = read(bound(items[0]['old_audio_manifest_ref']))
        assert manifest['status'] == 'COMPLETE' and manifest['audio_observed'] and not manifest['no_audio']
        media = bound(manifest['media_ref']); clock = read(bound(items[0]['source_clock_ref']))
        origin = F(clock['original_exact_pts'][0]); physical_end = F(clock['physical_end_exact'])
        assert clock['source_sha256'] == manifest['media_ref']['sha256']
        pieces, starts = [], []
        frame_count = 0
        with av.open(str(media)) as container:
            streams = [stream for stream in container.streams if stream.type == 'audio']
            assert streams, 'Previously accepted observed audio stream disappeared'
            stream = min(streams, key=lambda value: value.index)
            resampler = av.AudioResampler(format='fltp', layout='mono', rate=RATE)
            def consume(frames):
                for frame in frames:
                    assert frame.pts is not None and frame.time_base is not None and frame.sample_rate == RATE
                    data = np.asarray(frame.to_ndarray(), np.float32).reshape(-1)
                    assert len(data) == frame.samples and np.isfinite(data).all()
                    stamp = F(frame.pts)*F(frame.time_base)-origin
                    assert not starts or stamp >= starts[-1]
                    starts.append(stamp); pieces.append(data.copy())
            for packet in container.demux(stream):
                for frame in packet.decode():
                    assert frame.pts is not None and frame.time_base is not None
                    frame_count += 1; consume(resampler.resample(frame))
            consume(resampler.resample(None))
            stream_index = stream.index
        assert pieces
        offsets = np.r_[0, np.cumsum([len(part) for part in pieces])].astype(np.int64)
        values = np.concatenate(pieces)
        source_path = out/(sid+'_resampled_frames.npz')
        np.savez_compressed(source_path, values=values, offsets=offsets,
            starts_exact=np.asarray(list(map(str, starts))))
        source_ref = ref(source_path)
        # This is a first ASR-waveform purpose; old DSP had no retained PCM.
        # Old accepted DSP/decoder/QA stages are not repeated as the same stage.
        for item in items:
            request = read(bound(item['request_ref']))
            start = F(request['plan']['window_start_exact']); end = F(request['plan']['window_end_exact'])
            assert 0 <= start < end <= physical_end and end-start <= 30
            wave, observed, mapping = clip_from_frames(values, offsets, starts, start, end)
            assert observed.any() and observed.mean() >= .95, 'Fixed first-input coverage gate; no source replacement'
            path = out/(item['uid']+'.npz'); np.savez_compressed(path, wave=wave, observed=observed)
            # Independent exact sample identity by the written frame -> clip map.
            with np.load(path, allow_pickle=False) as saved:
                assert np.array_equal(saved['wave'], wave) and np.array_equal(saved['observed'], observed)
            visited = np.zeros(len(wave), bool)
            for row in mapping:
                lo, hi = row['frame_first'], row['frame_stop']; frame = row['frame']
                positions = np.arange(row['grid_first'], row['grid_first']+hi-lo)
                fresh = ~visited[positions]
                assert np.array_equal(wave[positions[fresh]], values[offsets[frame]+lo:offsets[frame]+hi][fresh])
                visited[positions[fresh]] = True
                stamp = F(row['actual_first_sample_time_exact'])
                assert start <= stamp < end and 0 <= F(row['sub_sample_grid_residual_exact']) < 1
            assert np.array_equal(visited, observed) and not wave[~observed].any()
            receipt = dict(uid=item['uid'], sid=sid, waveform_ref=ref(path), source_audio_frames_ref=source_ref,
                request_ref=item['request_ref'], original_clock_ref=item['source_clock_ref'],
                media_ref=manifest['media_ref'], old_DSP_manifest_ref=item['old_audio_manifest_ref'],
                source_start_exact=str(start), source_end_exact=str(end), sample_rate=RATE,
                actual_stream_index=stream_index, decoded_audio_frames=frame_count,
                video_decode_calls=0, ASR_first_new_waveform_use=True, no_old_DSP_reexecution=True,
                samples=len(wave), observed_samples=int(observed.sum()), missing_samples=int((~observed).sum()),
                missing_zeros_explicit_mask_not_observed_silence=True, max_grid_error_seconds='1/16000',
                first_independent_sample_mapping_QA=True, mappings=mapping)
            q=out/(item['uid']+'.json'); save(q, receipt); receipts.append(ref(q))
            event('FIRST_ASR_AUDIO_INPUT_ACCEPTED', uid=item['uid'], samples=len(wave), observed_samples=int(observed.sum()))
    assert len(receipts) == 8 and len(by_source) == 4
    save(R/'first_audio_inputs.json', dict(status='PASS_FIRST8_ASR_WAVEFORMS_FOUR_FIXED_EXTERNAL_SOURCES',
        receipts=receipts, source_count=4, excerpts=8, labels_in_preparation=False,
        new_audio_decode_sources=4, new_video_decode=0, old_DSP_not_rerun=True))


def original_modules(author):
    """Keep all author tensor operations, remove only unused optional wrappers."""
    path = author/'whisper/model.py'; tree = ast.parse(path.read_text())
    removed = []
    nodes = []
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.level and node.module in ('decoding','transcribe'):
            removed.append('import:'+node.module); continue
        if isinstance(node, ast.ClassDef) and node.name == 'Whisper':
            keep=[]
            for item in node.body:
                if isinstance(item, ast.Assign) and any(isinstance(target, ast.Name) and target.id in
                    ('detect_language','transcribe','decode') for target in item.targets):
                    removed.extend('alias:'+target.id for target in item.targets); continue
                keep.append(item)
            node.body=keep
        nodes.append(node)
    assert sorted(removed) == sorted(['import:decoding','import:decoding','import:transcribe',
                                     'alias:detect_language','alias:transcribe','alias:decode'])
    tree.body=nodes; module=types.ModuleType('audio23_original_whisper_core')
    module.__file__=str(path); sys.modules[module.__name__]=module
    exec(compile(tree,str(path),'exec'),module.__dict__)
    audio_path=author/'whisper/audio.py'; audio_tree=ast.parse(audio_path.read_text())
    wanted={'mel_filters','log_mel_spectrogram','pad_or_trim'}
    functions=[node for node in audio_tree.body if isinstance(node,ast.FunctionDef) and node.name in wanted]
    assert len(functions)==3
    utils=ast.parse((author/'whisper/utils.py').read_text())
    div=next(node for node in utils.body if isinstance(node,ast.FunctionDef) and node.name=='exact_div')
    namespace=dict(__file__=str(audio_path),os=os,np=np,torch=torch,F=torch.nn.functional,
        lru_cache=lru_cache,Optional=Optional,Union=Union,SAMPLE_RATE=16000,N_FFT=400,
        HOP_LENGTH=160,CHUNK_LENGTH=30,N_SAMPLES=480000,N_FRAMES=3000)
    exec(compile(ast.Module(body=[div,*functions],type_ignores=[]),str(audio_path),'exec'),namespace)
    proof=dict(removed_optional_imports_and_aliases=removed,
        original_tensor_core_AST_sha256=hashlib.sha256(ast.dump(tree).encode()).hexdigest(),
        original_mel_function_AST_sha256={node.name:hashlib.sha256(ast.dump(node).encode()).hexdigest()for node in functions},
        model_tensor_arithmetic_changed=False, new_global_dependencies=0)
    return module, namespace, proof


def vocabulary(author, model):
    tree=ast.parse((author/'whisper/tokenizer.py').read_text())
    node=next(node for node in tree.body if isinstance(node,ast.Assign)
        and any(isinstance(target,ast.Name)and target.id=='LANGUAGES'for target in node.targets))
    languages=ast.literal_eval(node.value)
    ranks={}
    for line in (author/'whisper/assets/multilingual.tiktoken').read_bytes().splitlines():
        token,index=line.split();ranks[int(index)]=base64.b64decode(token)
    assert set(ranks)==set(range(len(ranks)))
    specials=['<|endoftext|>','<|startoftranscript|>',
        *['<|%s|>'%lang for lang in list(languages)[:model.num_languages]],
        '<|translate|>','<|transcribe|>','<|startoflm|>','<|startofprev|>',
        '<|nospeech|>','<|notimestamps|>',*['<|%.2f|>'%(index*.02)for index in range(1501)]]
    tokens={text:len(ranks)+index for index,text in enumerate(specials)}
    assert max(tokens.values())+1==model.dims.n_vocab
    lang_ids=[tokens['<|%s|>'%lang]for lang in list(languages)[:model.num_languages]]
    return ranks,tokens,dict(zip(lang_ids,list(languages))),languages


def transcribe(model, mel, ranks, special, languages):
    sot=special['<|startoftranscript|>']; eot=special['<|endoftext|>']
    with torch.inference_mode():
        features=model.encoder(mel[None])
        first=model.decoder(torch.tensor([[sot]]),features)[0,-1].float()
        language_ids=list(languages);lang_logits=first[language_ids]
        lang=language_ids[int(lang_logits.argmax())]
        language_probability=float(lang_logits.softmax(-1).max())
        no_speech=float(first.softmax(-1)[special['<|nospeech|>']])
        generated=[];scores=[];ended=False
        if no_speech<=.6:
            prefix=[sot,lang,special['<|transcribe|>'],special['<|notimestamps|>']]
            cache,hooks=model.install_kv_cache_hooks()
            try:
                current=torch.tensor([prefix])
                for step in range(128):
                    logits=model.decoder(current,features,kv_cache=cache)[0,-1].float()
                    allowed=logits.clone();allowed[len(ranks):]=-torch.inf;allowed[eot]=logits[eot]
                    if step==0:allowed[eot]=-torch.inf;allowed[220]=-torch.inf
                    token=int(allowed.argmax());scores.append(float(logits.log_softmax(-1)[token]))
                    generated.append(token)
                    if token==eot:ended=True;break
                    current=torch.tensor([[token]])
            finally:
                for hook in hooks:hook.remove()
    raw=b''.join(ranks[token]for token in generated if token in ranks).decode('utf8',errors='replace')
    average=float(np.mean(scores))if scores else None
    ratio=len(raw.encode())/max(1,len(zlib.compress(raw.encode())))
    if no_speech>.6:status='VALID_ASR_ABSTAIN_NO_SPEECH_EVIDENCE'
    elif not ended:status='VALID_ASR_ABSTAIN_TOKEN_LIMIT_UNCERTAIN'
    elif not raw.strip()or average < -1.0 or ratio>2.4:status='VALID_ASR_ABSTAIN_UNCERTAIN_TRANSCRIPTION'
    else:status='ASR_TRANSCRIPT_AVAILABLE_UNVERIFIED_TEXT_NOT_GROUND_TRUTH'
    return dict(status=status,raw_text=raw,generated_ids=generated,EOT_observed=ended,
        no_speech_probability=no_speech,conditional_language_probability=language_probability,
        detected_language=languages[lang],mean_original_token_logprob=average,compression_ratio=ratio,
        greedy_decoder='fixedtemperature0 normalBPE+EOT only,128token cap; no best-of/fallback/retune',
        utterance_word_times_available=False,execution_failure_to_empty=False)


def run_asr(reg):
    gate=read(R/'first_audio_inputs.json');assert len(gate['receipts'])==8
    lock=read(R/'download_completion.json');author=R/'author';module,audio,proof=original_modules(author)
    weights=bound(lock['model_ref'])
    assert sha(weights)=='65147644a518d12f04e32d6f3b26facc3f8dd46e5390956a9424a650c0ce22b9'
    state=torch.load(weights,map_location='cpu',weights_only=True)
    model=module.Whisper(module.ModelDimensions(**state['dims']));model.load_state_dict(state['model_state_dict'],strict=True)
    model=model.float().eval()
    loaded=model.state_dict()
    assert set(loaded)==set(state['model_state_dict']) and all(torch.equal(loaded[key],
        value.to(loaded[key].dtype))for key,value in state['model_state_dict'].items())
    for parameter in model.parameters():parameter.requires_grad_(False)
    count=sum(parameter.numel()for parameter in model.parameters());assert 8782459120+count<=9000000000
    assert not torch.cuda.is_initialized()
    before={name:hashlib.sha256(value.detach().contiguous().numpy().tobytes()).hexdigest()
            for name,value in model.state_dict().items()}
    ranks,special,languages,_=vocabulary(author,model)
    save(R/'ASR_model_acceptance.json',dict(status='PASS_AUTHOR_TINY_STRICT_TENSOR_LOAD_CPU_AND_FIXED_CORE',
        model_ref=lock['model_ref'],actual_parameters=count,combined_TIME_and_ASR_parameters=8782459120+count,
        all_frozen=True,all_loaded_tensors_equal_original=True,new_global_packages=0,source_code_proof=proof,training_updates=0))
    out=R/'asr';out.mkdir();outputs=[];started=time.monotonic()
    for reference in gate['receipts']:
        assert time.monotonic()-started<1800,'Fixed8 CPU ASR budget; do not restart successes'
        receipt=read(bound(reference))
        with np.load(bound(receipt['waveform_ref']),allow_pickle=False)as data:wave=torch.from_numpy(data['wave'].copy())
        mel=audio['log_mel_spectrogram'](audio['pad_or_trim'](wave))
        assert list(mel.shape)==[80,3000] and torch.isfinite(mel).all()
        event('BEGIN_FIRST_ASR',uid=receipt['uid'])
        result=transcribe(model,mel,ranks,special,languages)
        result.update(uid=receipt['uid'],sid=receipt['sid'],waveform_acceptance_ref=reference,
            model_acceptance_ref=ref(R/'ASR_model_acceptance.json'),source_start_exact=receipt['source_start_exact'],
            source_end_exact=receipt['source_end_exact'],new_decoder_model_call=True,
            original_human_labels_used=False,submittable_labels=False)
        path=out/(receipt['uid']+'.json');save(path,result);outputs.append(ref(path))
        event('COMPLETE_FIRST_ASR',uid=receipt['uid'],status=result['status'],generated_tokens=len(result['generated_ids']))
    after={name:hashlib.sha256(value.detach().contiguous().numpy().tobytes()).hexdigest()
           for name,value in model.state_dict().items()}
    assert before==after and not torch.cuda.is_initialized()
    usable=sum(read(bound(reference))['status']=='ASR_TRANSCRIPT_AVAILABLE_UNVERIFIED_TEXT_NOT_GROUND_TRUTH'for reference in outputs)
    save(R/'ASR_completion.json',dict(status='COMPLETE_FIXED8_FIRST_CPU_ASR_NOT_HIGHLIGHT_QUALITY_PROOF',
        outputs=outputs,usable_transcripts=usable,successful_abstentions=8-usable,elapsed_seconds=time.monotonic()-started,
        model_unchanged=True,actual_ASR_parameters=count,combined_parameters=8782459120+count,
        new_GPU_calls=0,fit=0,new_human_or_official_labels=0,automatic_formal_production=False))


def main():
    assert os.uname().nodename=='inspur-NP5570M5' and not torch.cuda.is_initialized()
    reg=read(R/'registration.json');assert bound(reg['code_ref'])==Path(__file__).resolve()
    torch.set_num_threads(reg['CPU_threads']);torch.set_num_interop_threads(1)
    save(R/'CPU_claim.json',dict(pid=os.getpid(),registration_ref=ref(R/'registration.json'),automatic_retry=False))
    prepare(reg);run_asr(reg)


if __name__=='__main__':
    try:main()
    except BaseException as error:
        failure=R/('CPU_failure_%s.json'%os.getpid())
        if not failure.exists():save(failure,dict(error=repr(error),traceback=traceback.format_exc(),
            successes_preserved=True,automatic_retry=False,execution_failure_to_empty=False))
        raise
