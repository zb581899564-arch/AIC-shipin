"""New base-only ablation on previously accepted, unchanged external inputs.

Admission reuses successful CPU tensor proofs. GPU encoding is still performed
and checked; independent output replay does not redundantly encode the inputs.
"""
import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import math
import os
import sys
import time
import traceback
from bisect import bisect_left
from fractions import Fraction as F
from pathlib import Path

RUN = Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
LEGACY_CODE = Path('/home/inspur/aic_video_work/videoxum_reference_iteration_20261013_v1/code')
PY = '/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(8 << 20), b''):
            h.update(b)
    return h.hexdigest()


def save(path, value):
    with Path(path).open('x', encoding='utf-8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.flush()
        os.fsync(f.fileno())


def append(path, value):
    with Path(path).open('a', encoding='utf-8') as f:
        f.write(json.dumps(value, ensure_ascii=False, allow_nan=False) + '\n')
        f.flush()
        os.fsync(f.fileno())


def require(ok, why):
    if not ok:
        raise ValueError(why)


def runtime():
    # Single frozen legacy implementation in a fresh process, no new common.py.
    sys.path.insert(0, str(LEGACY_CODE))
    import cohort_run_common_07 as old
    return old.runtime()


def inputs(root):
    p = read(root / 'protocol.json')
    registration = read(root / 'registration_input_01.json')
    entries = [{**e, 'proof_path':e['entry']['proof_path'], 'proof_sha256':e['entry']['proof_sha256'],
                'prior_independent_replay_path':e['old_independent_replay_path'],
                'prior_independent_replay_sha256':e['old_independent_replay_sha256']} for e in registration['rows']]
    require(len(entries) == p['calls'] == 12, 'fixed pilot denominator')
    require(len({e['case_id'] for e in entries}) == 12, 'duplicate pilot case')
    require(len({e['source_name'] for e in entries}) == 12 and all(e['original_group'] == 'screen' and e['case_id'].endswith('_W000') for e in entries), '12 distinct registered screen first windows')
    result = []
    for e in entries:
        require(sha(e['proof_path']) == e['proof_sha256'], 'old CPU proof changed')
        cpu = read(e['proof_path'])
        require(cpu['status'] == 'PASS_CPU_ORIGINAL_B_NATIVE64_PROCESSOR_INPUT' and cpu['CPU_only'], 'real prior CPU proof')
        require(sha(cpu['input_path']) == cpu['input_sha256'], 'old input changed')
        meta = read(cpu['input_path'])
        require(sha(meta['frame_array_path']) == meta['frame_array_sha256'], 'old RGB changed')
        require(cpu['case_id'] == meta['case_id'] == e['case_id'] and meta['source_name'] == e['source_name'], 'pilot identity')
        require(cpu['input_tokens'] <= 16384 and len(set(meta['source_frame_ordinals'])) == 64, 'old native64 budget')
        require(not meta['reference_available_to_inference'] and not meta['audio_observed'], 'reference/audio not input')
        require(sha(e['original_done_path']) == e['original_done_sha256'], 'paired old model answer changed')
        result.append((e, cpu, meta))
    return p, result


def verify_lock(root):
    value = read(root / 'source_lock.json')
    for path, digest in value['files'].items():
        require(sha(path) == digest, 'frozen input/code changed: ' + path)
    return value


def admit(root):
    require(not (root / 'source_lock.json').exists(), 'already admitted: do not repeat')
    p, values = inputs(root)
    require(p['hypothesis'] == 'TIME_ADAPTER_SELECTION_BIAS' and p['optimizer_updates'] == 0, 'fixed base-only scope')
    require(p['old_scientific_gates_changed'] is False and p['official_test_input'] is False, 'authority scope')
    files = {str(q): sha(q) for q in [root/'protocol.json', root/'registration_input_01.json', Path(__file__).resolve()]}
    # Bind accepted tensor proof and all successful native RGB, no re-decoding or CPU encoding.
    for e, cpu, meta in values:
        for q in [e['proof_path'], cpu['input_path'], meta['frame_array_path'], e['original_done_path']]:
            files[str(q)] = sha(q)
        require(e.get('prior_independent_replay_path') and e.get('prior_independent_replay_sha256'), 'prior independent input replay required')
        q = e['prior_independent_replay_path']
        require(sha(q) == e['prior_independent_replay_sha256'], 'prior independent replay changed')
        replay = read(q)
        require(replay['status'] == 'PASS_INDEPENDENT_CPU_TENSOR_TOKEN_PARSER_NATIVE_REPLAY' and replay['CPU_only'] and replay['case_id'] == e['case_id'] and replay['source_name'] == meta['source_name'] and replay['input_evidence'] == cpu['input_evidence'], 'prior independent successful tensor evidence')
        files[str(q)] = sha(q)
    config_path = RUN/'b_score_aligned_package_v4/config.json'
    files[str(config_path)] = sha(config_path)
    rt = runtime()
    require(all(cpu['input_evidence'].get('physical_frames') == 64 for _, cpu, _ in values), 'native frame denominator')
    require(hashlib.sha256(rt.EMPTY_PROMPT.encode()).hexdigest() == p['prompt_sha256'], 'unchanged B0 prompt')
    for q in LEGACY_CODE.glob('*.py'):
        files[str(q)] = sha(q)
    legacy = Path('/home/inspur/aic_video_work/temporal_refinement_pilot_20261011/dev_01')
    for q in legacy.glob('*.py'):
        files[str(q)] = sha(q)
    for q in (RUN/'b_score_aligned_package_v4').glob('*.py'):
        files[str(q)] = sha(q)
    save(root/'source_lock.json', {'files': files, 'calls':12, 'new_CPU_encodes':0,
         'reused_real_CPU_proofs':12,'reuse_does_not_claim_no_GPU_encoding':True,
         'pipeline_parameter_upper_bound':8782459120, 'unique_gpu_name':p['gpu_name']})
    save(root/'admission.json', {'status':'PASS_12_UNCHANGED_PRIOR_REAL_CPU_INPUTS_AND_INDEPENDENT_PROOFS',
         'source_lock_sha256':sha(root/'source_lock.json'), 'new_model_calls':0, 'new_CPU_encoding':0})


def ranges(segments, meta):
    points = [F(x) for x in meta['all_source_exact_pts']]
    origin = F(meta['window_start'])
    result = []
    for a, b in segments:
        lo, hi = bisect_left(points, origin+F(str(a))), bisect_left(points, origin+F(str(b)))
        require(0 <= lo < hi <= len(points), 'nonempty interval must contain real native frames')
        require(list(range(lo, hi)) == [i for i,x in enumerate(points) if origin+F(str(a)) <= x < origin+F(str(b))], 'independent direct native predicate')
        result.append([lo, hi])
    return result


def infer(root):
    verify_lock(root)
    p, values = inputs(root)
    require(dt.datetime.now(dt.timezone.utc) < dt.datetime.fromisoformat(p['deadline']), 'new GPU job after deadline')
    require(read(root/'admission.json')['source_lock_sha256'] == sha(root/'source_lock.json'), 'admission binding')
    rt = runtime()
    from sft_contract import verify_live_gpu_reservation
    from constrained_json import ascii_token_candidates, make_prefix_constraint
    import torch
    verify_live_gpu_reservation()
    out = root/'gpu_01'
    out.mkdir(exist_ok=False)
    save(out/'claim.json', {'source_lock_sha256':sha(root/'source_lock.json'), 'calls':12, 'pid':os.getpid()})
    entries, begun, current = [], 0, None
    try:
        config = read(RUN/'b_score_aligned_package_v4/config.json')
        model, processor, identity = rt.b_engine.load_model(config)
        require(identity['logical_parameters'] == 8782459120 and identity['base']['parameters'] == 8767123696,
                'actual original B identity')
        require(identity['base']['sha256'] == '74bcce81cfcb0893cf4b4c25ae36ec908d6ea669583aedd0f3940063080b8b59', 'frozen base')
        require(identity['adapter']['sha256'] == '8e2cca463d8aac39f7a709bdf562373e3e47a3a8da490991c303d5e03b803b23', 'loaded old adapter')
        save(out/'model_identity.json', {'loaded_identity':identity,'actual_physical_parameters':8782459120,
             'activated_base_parameters':8767123696,'adapter_disabled_for_all_calls':True,'optimizer_updates':0})
        candidates = ascii_token_candidates(processor.tokenizer)
        eos = model.generation_config.eos_token_id
        eos = [eos] if isinstance(eos, int) else list(eos)
        for e, cpu, meta in values:
            current = e['case_id']
            folder = out/current
            folder.mkdir(exist_ok=False)
            lo, hi = F(meta['window_start']), F(meta['window_end'])
            frames = rt.baseline_frames(meta)
            encoded, evidence = rt.encode(processor, meta, frames, lo, rt.EMPTY_PROMPT)
            require(evidence == cpu['input_evidence'], 'actual GPU request vs prior accepted CPU tensor')
            prefix = int(encoded['input_ids'].shape[1])
            require(prefix == cpu['input_tokens'], 'original actual input tokens')
            grammar = make_prefix_constraint(processor.tokenizer, prefix, hi-lo,
                candidate_token_ids=candidates, eos_token_ids=eos, allow_empty=True)
            gpu = encoded.to('cuda')
            require(rt.tensor_signature(gpu) == evidence['tensor_signature'], 'actual CPU/GPU tensors')
            save(folder/'request.json', {'input_path':cpu['input_path'],'input_sha256':cpu['input_sha256'],
                'CPU_proof_sha256':e['proof_sha256'],'input_evidence':evidence,'prompt':rt.EMPTY_PROMPT,
                'adapter_disabled':True,'reference_supplied_to_model':False})
            append(out/'attempts.jsonl', {'event':'BEGIN','case_id':current,'call_id':begun+1})
            begun += 1
            started = time.monotonic()
            with model.disable_adapter():
                disabled = [bool(m.disable_adapters) for m in model.modules() if hasattr(m,'disable_adapters') and hasattr(m,'lora_A')]
                require(len(disabled) == 144 and all(disabled), 'all actual LoRA layers must be disabled')
                with torch.inference_mode():
                    result = model.generate(**gpu,do_sample=False,max_new_tokens=256,
                        prefix_allowed_tokens_fn=grammar,return_dict_in_generate=True,output_scores=True)
            torch.cuda.synchronize()
            ids = result.sequences[0,prefix:]
            raw = processor.tokenizer.decode(ids,skip_special_tokens=True,clean_up_tokenization_spaces=False)
            scores = [float(s[0,int(t)]) for s,t in zip(result.scores,ids)]
            save(folder/'raw.json', {'raw_output':raw,'output_token_ids':ids.tolist(),
                'selected_token_scores':[s if math.isfinite(s) else str(s) for s in scores],
                'generated_score_count':len(result.scores),'input_tokens':prefix,'output_tokens':len(ids),
                'generation_seconds':time.monotonic()-started,'eos_token_ids':eos,'adapter_disabled_layers':disabled,
                'actual_model_call':True,'input_evidence':evidence})
            require(0 < len(ids) <= 256 and len(scores) == len(ids) and all(math.isfinite(s) for s in scores), 'finite generated token scores')
            grammar.assert_complete(ids)
            segments, errors, warnings = rt.parse_segments(raw,hi-lo,allow_empty=True)
            require(segments is not None and not errors, 'original strict parser rejects raw')
            done = {'status':'MODEL_OK' if segments else 'LEGAL_EMPTY','case_id':current,'source_name':meta['source_name'],
                'segments':segments,'parse_warnings':warnings,'native_ranges':ranges(segments,meta),
                'raw_sha256':sha(folder/'raw.json'),'request_sha256':sha(folder/'request.json'),'input_evidence':evidence}
            save(folder/'done.json',done)
            entries.append({'case_id':current,'done_path':str(folder/'done.json'),'done_sha256':sha(folder/'done.json')})
            append(out/'attempts.jsonl',{'event':'ACCEPTED','case_id':current,'call_id':begun,**entries[-1]})
            print(json.dumps({'accepted':len(entries),'budget':12,'case_id':current}),flush=True)
            del gpu,encoded,frames,result,ids
        require(begun == len(entries) == 12, 'unique complete calls')
        require(rt.b_engine.frozen_identity(model,config) == identity['base'], 'frozen base after inference')
        save(out/'completion.json', {'status':'PASS_12_NEW_BASE_ONLY_CALLS_NOT_QUALITY','entries':entries,
             'calls':begun,'attempts_sha256':sha(out/'attempts.jsonl'),'source_lock_sha256':sha(root/'source_lock.json')})
    except BaseException as err:
        save(out/'failure.json', {'error':repr(err),'traceback':traceback.format_exc(),'begun':begun,
             'successful_entries':entries,'current':current,'successful_calls_not_repeated':True})
        raise


def replay(root):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU output replay only')
    verify_lock(root)
    p, values = inputs(root)
    terminal = read(root/'gpu_01/completion.json')
    resource = read(RUN/('controller/'+p['gpu_name']+'.resource.json'))
    ledger = [json.loads(x) for x in Path('/home/inspur/aic_video_work/improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if x.strip()]
    require([x for x in ledger if x['name'] == p['gpu_name']] == [resource] and resource['status'] == 'completed' and resource['exit_code'] == 0, 'unique GPU terminal')
    require(terminal['calls'] == 12 and terminal['source_lock_sha256'] == sha(root/'source_lock.json'), 'GPU complete binding')
    events = [json.loads(x) for x in (root/'gpu_01/attempts.jsonl').read_text().splitlines()]
    require(len(events) == 24, 'actual attempt denominator')
    rt = runtime()
    from transformers import AutoProcessor
    from constrained_json import ascii_token_candidates, make_prefix_constraint
    processor = AutoProcessor.from_pretrained(read(RUN/'b_score_aligned_package_v4/config.json')['model_dir'],local_files_only=True,min_pixels=131072,max_pixels=131072)
    candidates = ascii_token_candidates(processor.tokenizer)
    out = root/'replay_01'
    out.mkdir(exist_ok=False)
    accepted = {e['case_id']:e for e in terminal['entries']}
    checks = []
    for index,(e,cpu,meta) in enumerate(values):
        case = e['case_id'];folder=root/'gpu_01'/case
        require(events[2*index]['event'] == 'BEGIN' and events[2*index+1]['event'] == 'ACCEPTED' and all(x['case_id'] == case for x in events[2*index:2*index+2]), 'attempt order')
        require(sha(folder/'done.json') == accepted[case]['done_sha256'], 'new done changed')
        done,raw,request=read(folder/'done.json'),read(folder/'raw.json'),read(folder/'request.json')
        require(done['raw_sha256'] == sha(folder/'raw.json') and done['request_sha256'] == sha(folder/'request.json'), 'raw/request bytes')
        require(cpu['input_evidence'] == request['input_evidence'] == raw['input_evidence'] == done['input_evidence'], 'new input vs independently accepted old tensor proof')
        require(request['CPU_proof_sha256'] == e['proof_sha256'] and request['input_sha256'] == cpu['input_sha256'] and request['prompt'] == rt.EMPTY_PROMPT and not request['reference_supplied_to_model'], 'unchanged accepted request')
        ids,scores=raw['output_token_ids'],raw['selected_token_scores']
        require(0 < len(ids) == len(scores) == raw['generated_score_count'] == raw['output_tokens'] <= 256 and all(type(s) in (float,int) and math.isfinite(s) for s in scores), 'finite token scores')
        require(raw['adapter_disabled_layers'] == [True]*144 and raw['actual_model_call'], 'real base-only call')
        require(raw['input_tokens'] == cpu['input_tokens'], 'actual input token bound')
        require(processor.tokenizer.decode(ids,skip_special_tokens=True,clean_up_tokenization_spaces=False) == raw['raw_output'], 'new output token decode')
        grammar=make_prefix_constraint(processor.tokenizer,raw['input_tokens'],F(meta['window_end'])-F(meta['window_start']),candidate_token_ids=candidates,eos_token_ids=raw['eos_token_ids'],allow_empty=True)
        grammar.assert_complete(ids)
        segments,errors,warnings=rt.parse_segments(raw['raw_output'],F(meta['window_end'])-F(meta['window_start']),allow_empty=True)
        require(not errors and segments == done['segments'] and warnings == done['parse_warnings'] and ranges(segments,meta) == done['native_ranges'], 'independent strict parser/native replay')
        q=out/(case+'.json');save(q,{'status':'PASS_NEW_CPU_TOKEN_GRAMMAR_PARSER_NATIVE_WITH_PRIOR_INDEPENDENT_TENSOR_PROOF','case_id':case,'CPU_only':True,'new_CPU_encoding':0,'new_model_calls':0,'segments':segments,'done_sha256':sha(folder/'done.json'),'prior_tensor_replay_sha256':e['prior_independent_replay_sha256']})
        checks.append({'case_id':case,'path':str(q),'sha256':sha(q)})
    import torch
    require(not torch.cuda.is_initialized(), 'CPU replay initialized CUDA')
    save(out/'completion.json',{'status':'PASS_ALL12_NEW_OUTPUT_REPLAYS','proofs':checks,'new_CPU_encoding':0,'prior_independent_input_proofs_reused':12,'resource_terminal_sha256':sha(RUN/('controller/'+p['gpu_name']+'.resource.json')),'gpu_completion_sha256':sha(root/'gpu_01/completion.json')})


if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['admit','infer','replay']);parser.add_argument('root',type=Path)
    a=parser.parse_args();globals()[a.stage](a.root)
