"""One CPU-only Qwen tokenizer ABI check; synthetic event, no candidate run."""
import ast
import base64
import hashlib
import json
import os
from pathlib import Path
import resource
import socket
import sys
import time
import traceback
import types

payload = json.loads(base64.b64decode(sys.stdin.buffer.readline()))
os.environ['CUDA_VISIBLE_DEVICES'] = ''
if socket.gethostname() != 'inspur-NP5570M5' or sys.platform != 'linux':
    raise ValueError('Unexpected ABI check host')
for name in ('cv_contract', 'cv_io', 'cv_tokens', 'cv_grammar', 'replay_verify'):
    source = payload['code'][name+'.py']
    ast.parse(source)
    module = types.ModuleType(name)
    module.__file__ = '/memory_only_candidate_verify_abi/'+name+'.py'
    sys.modules[name] = module
    exec(compile(source, module.__file__, 'exec'), module.__dict__)
c, io, tokens, replay = (sys.modules[name] for name in ('cv_contract', 'cv_io', 'cv_tokens', 'replay_verify'))
root = Path('/home/inspur/aic_video_work/twenty_hour_five_20261014_v1/candidate_verify_v1/tokenizer_abi_check_01')
root.mkdir(parents=True, exist_ok=False)
oldfolder = Path('/home/inspur/aic_video_work/twenty_hour_five_20261014_v1/charades_boundary_v1/native_01/7FQ5Q')
complete = io.read(oldfolder/'completion.json')
entry = complete['proofs'][0]
if entry['case_id'] != 'CH_7FQ5Q_W000':
    raise ValueError('Expected exact already-successful original CPU case')
proofpath = io.checked(dict(path=entry['proof_path'], sha256=entry['proof_sha256']))
inputpath = io.checked(dict(path=entry['input_path'], sha256=entry['input_sha256']))
proof, meta = io.read(proofpath), io.read(inputpath)
cachepath = io.checked(dict(path=entry['encoded_tensor_path'], sha256=entry['encoded_tensor_sha256']))
memavailable = next(int(row.split()[1])*1024 for row in Path('/proc/meminfo').read_text().splitlines()
                    if row.startswith('MemAvailable:'))
memoryestimate = 2*proof['logical_tensor_payload_bytes']+2*cachepath.stat().st_size
if memavailable <= memoryestimate:
    raise ValueError('Current memory cannot cover one existing tensor cache and token-only check')
bindings = dict(source_case=entry['case_id'], old_input_path=str(inputpath), old_input_sha256=entry['input_sha256'],
    old_proof_path=str(proofpath), old_proof_sha256=entry['proof_sha256'],
    old_cache_path=str(cachepath), old_cache_sha256=entry['encoded_tensor_sha256'],
    old_cache_bytes=cachepath.stat().st_size,
    code_files={name:dict(bytes=len(source.encode()), sha256=hashlib.sha256(source.encode()).hexdigest())
                for name, source in payload['code'].items()},
    candidate_metadata='EXPLICIT_SYNTHETIC_ABI_ONLY_NOT_ORIGINAL_COARSE_PREDICTION',
    source_media_and_RGB_not_read=True, reference_metadata_not_read=True)
io.save(root/'launch.json', dict(bindings=bindings, pid=os.getpid(), CPU_only=True, utc=io.utc(),
    memory_available_bytes=memavailable, memory_estimate_from_old_actual_proof_bytes=memoryestimate,
    new_processor_encodes=0, media_decodes=0, model_calls=0, actual_CPU_or_GPU_admitted=False))
started, stage = time.monotonic(), 'LOCAL_ORIGINAL_TOKENIZER_ASSETS'
try:
    import torch
    runtime, processor, identity = io.cpu_processor()
    for key, value in proof['original_b_processor_runtime'].items():
        if identity[key] != value:
            raise ValueError('Original processor/tokenizer/runtime identity differs: '+key)
    if hashlib.sha256(runtime.EMPTY_PROMPT.encode()).hexdigest() != c.EMPTY_PROMPT_SHA256:
        raise ValueError('Original B EMPTY_PROMPT changed')
    def forbidden(*args, **kwargs):
        raise ValueError('ABI check attempted forbidden media/vision/model work')
    runtime.encode = forbidden
    # No runtime encode or processor call is needed. Block either visual
    # preprocessing entry explicitly while using the already-loaded tokenizer.
    processor.video_processor.preprocess = forbidden
    processor.image_processor.preprocess = forbidden
    stage = 'READ_ALREADY_ACCEPTED_LOSSLESS_CPU_CACHE_ONCE'
    original = io.load_tensor_cache(cachepath)
    oldsignature = runtime.tensor_signature(original)
    if oldsignature != proof['input_evidence']['tensor_signature']:
        raise ValueError('Already successful CPU cache signature differs')
    oldtext = processor.tokenizer.decode(original['input_ids'][0].tolist(), skip_special_tokens=False,
                                        clean_up_tokenization_spaces=False)
    lo, hi = c.exact(meta['window_start']), c.exact(meta['window_end'])
    event = dict(event_id='ABI_ONLY_SYNTHETIC_CANDIDATE', original_segment_index=0,
                 original_interval_exact=[str(lo+(hi-lo)/3), str(lo+2*(hi-lo)/3)])
    req = c.request(event, meta)
    req['prompt'] = c.prompt(req)
    io.save(root/'abi_raw.json', dict(original_expanded_text=oldtext, new_prompt=req['prompt'],
        synthetic_request=req, actual_coarse_candidate=False, actual_model_raw=False,
        original_prompt_occurrences=oldtext.count(runtime.EMPTY_PROMPT), bindings=bindings))
    stage = 'ACTUAL_ORIGINAL_TOKENIZER_RETARGET'
    newtokens, combined, evidence = tokens.retarget(original, processor.tokenizer,
        runtime.EMPTY_PROMPT, req['prompt'], runtime.tensor_signature)
    stage = 'INDEPENDENT_PARTITION_ENCODE'
    independently_encoded, independent_combined, independent_evidence = replay.independent_tokens(
        original, processor.tokenizer, runtime.EMPTY_PROMPT, req['prompt'], runtime.tensor_signature)
    if runtime.tensor_signature(newtokens) != runtime.tensor_signature(independently_encoded):
        raise ValueError('Actual Qwen independent new text tokens differ')
    if runtime.tensor_signature(combined) != runtime.tensor_signature(independent_combined):
        raise ValueError('Actual Qwen independent combined tensor signature differs')
    for key, value in independent_evidence.items():
        if evidence[key] != value:
            raise ValueError('Independent prompt-only ABI evidence differs: '+key)
    newtext = processor.tokenizer.decode(newtokens['input_ids'][0].tolist(), skip_special_tokens=False,
                                        clean_up_tokenization_spaces=False)
    if newtext != oldtext.replace(runtime.EMPTY_PROMPT, req['prompt'], 1):
        raise ValueError('Actual new expanded token text is not the exact prompt replacement')
    if runtime.tensor_signature(original) != oldsignature or torch.cuda.is_initialized():
        raise ValueError('Original CPU tensors changed or CUDA initialized')
    receipt = dict(status='PASS_REAL_QWEN_TOKENIZER_ONLY_VERIFY_RETARGET_ABI_NOT_CANDIDATE_QUALITY',
        bindings=bindings, identity=identity, tokenizer_class=type(processor.tokenizer).__name__,
        processor_class=type(processor).__name__, original_prompt_occurrences=1,
        original_input_tokens=int(original['input_ids'].shape[1]), new_input_tokens=evidence['input_tokens'],
        original_cache_signature_equal_to_accepted_proof=True, original_full_token_roundtrip_equal=True,
        unique_EMPTY_PROMPT_replacement=True, new_expanded_text_exact=True,
        unchanged_original_vision_prefix=evidence['vision_prefix'],
        unchanged_pixel_grid_signature=evidence['unchanged_vision_tensor_signature'],
        independent_partition_token_and_combined_signature_equal=True,
        original_tensors_unchanged=True, retarget_evidence=evidence,
        grid_thw=original['video_grid_thw'].tolist(), dtypes={key:str(t.dtype) for key,t in original.items()},
        candidate_metadata_is_synthetic=True, actual_coarse_predictions_read=0,
        source_media_reads=0, RGB_cache_reads=0, vision_processor_calls=0,
        new_vision_encodes=0, model_calls=0, optimizer_updates=0, CUDA_initialized=False,
        original_large_cache_copies=0, token_only_cache_saved=False,
        actual_CPU_or_GPU_admitted=False, candidate_quality_tested=False,
        wall_seconds=time.monotonic()-started, process_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        utc=io.utc())
    io.save(root/'receipt.json', receipt)
    print(json.dumps(receipt, ensure_ascii=False))
except BaseException as error:
    io.save(root/'failure.json', dict(status='FAILED_ABI_CHECK_KEEP_RAW_NO_UNKNOWN_FALLBACK', stage=stage,
        error_type=type(error).__name__, error=str(error), traceback=traceback.format_exc(), bindings=bindings,
        raw_path=str(root/'abi_raw.json') if (root/'abi_raw.json').exists() else None,
        vision_processor_calls=0, source_media_reads=0, model_calls=0, actual_CPU_or_GPU_admitted=False))
    raise
