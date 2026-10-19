"""One explicit INIT_TIME or final559 matched-input role; no training/labels."""
import argparse
from datetime import datetime, timezone
from fractions import Fraction as F
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import time
import traceback
import torch
from summary_contract import build_pixels, signature, require
from summary_context_pixels import load_context_frames
from summary_grammar6 import PrefixConstraint, ascii_token_candidates
from summary_output import parse_summary

W = Path('/home/inspur/aic_video_work')
ROOT = W/'bottleneck_24h_20261019_v1/summary_objective_v20'
RUN = W/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'


def read(p):
    return json.loads(Path(p).read_text())


def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda:f.read(8<<20),b''):
            h.update(b)
    return h.hexdigest()


def ref(p):
    return dict(path=str(Path(p).resolve()), bytes=Path(p).stat().st_size, sha256=sha(p))


def bound(r):
    p = Path(r['path']).resolve()
    require(p.is_relative_to(W) and p.is_file() and sha(p) == r['sha256'], 'Explicit bound file changed/outside work root')
    return p


def save(p,value):
    with Path(p).open('x') as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.flush(); os.fsync(f.fileno())


def event(p, name, **values):
    with Path(p).open('a') as f:
        f.write(json.dumps(dict(utc=datetime.now(timezone.utc).isoformat(),event=name,**values))+'\n')
        f.flush(); os.fsync(f.fileno())


class DevInputs:
    def __init__(self, reg):
        gate = read(bound(reg['first_dev_input_acceptance_ref']))
        require(gate['status'] == 'PASS_ALL43_FIRST_MATCHED_DEV8_TWO_VIEW_INPUTS' and gate['sources'] == 8
                and gate['windows'] == 43, 'Actual full8/43 first new input acceptance required')
        self.prepared = read(bound(gate['prepared']))
        sources = read(bound(self.prepared['source_catalog']))['sources']
        self.sources = {s['id']:s for s in sources}
        require(len(self.sources) == 8 and len(self.prepared['inputs']) == 43, 'Exact matched development denominator')
        dictionary = bound(reg['pixel_dictionary_ref']); codec = bound(reg['pixel_codec_ref'])
        if 'codec' in sys.modules:
            require(Path(sys.modules['codec'].__file__).resolve() == codec, 'Unrelated codec module already imported')
        else:
            spec = importlib.util.spec_from_file_location('codec', codec)
            module = importlib.util.module_from_spec(spec); sys.modules['codec'] = module; spec.loader.exec_module(module)
        spec = importlib.util.spec_from_file_location('summary10_dictionary', dictionary)
        module = importlib.util.module_from_spec(spec); sys.modules['summary10_dictionary'] = module; spec.loader.exec_module(module)
        exposed = os.environ.get('CUDA_VISIBLE_DEVICES')
        require(exposed not in (None,''), 'Pure cached reader imports may not hide GPU')
        self.frames = {sid:load_context_frames(s,module) for sid,s in self.sources.items()}
        self.clocks = {sid:read(bound(s['clock'])) for sid,s in self.sources.items()}
        require(os.environ.get('CUDA_VISIBLE_DEVICES') == exposed, 'Cached reader changed parent CUDA')

    def get(self, reference):
        request = read(bound(reference)); source = self.sources[request['sid']]
        require(request['source_sha256'] == source['source_sha256'] and request['first_new_pixel_text_native_QA'],
                'Adopt actual original development source identity')
        frames,grid,ordinals = self.frames[request['sid']]; plan = request['plan']
        values, actual = build_pixels(frames,grid,ordinals,self.clocks[request['sid']]['normalized_exact_pts'],
            plan['window_start_exact'],plan['window_end_exact'],dict(source_id=request['sid'],source_sha256=source['source_sha256']))
        require(actual == plan, 'Actual new two-role source/time sampling changed')
        prefix = torch.load(bound(request['prefix_ref']),map_location='cpu',weights_only=True)
        values.update(prefix)
        require(signature(values) == request['input_signature'], 'Runtime input differs from first accepted actual input')
        return request,values


def inventory(model):
    counts = dict(base=0,summary=0); matrices = 0
    for name,p in model.named_parameters():
        require(not p.requires_grad, 'Every inference parameter must be frozen')
        key = 'summary' if 'lora_' in name else 'base'; counts[key] += p.numel()
        if key == 'summary':
            require('.summary.weight' in name, 'Only registered summary adapter may be resident')
            matrices += 1
    layers = [m for m in model.modules() if hasattr(m,'lora_A')]
    require(counts == dict(base=8767123696,summary=15335424) and matrices == 288 and len(layers) == 144
        and all(set(m.lora_A) == {'summary'} and list(m.active_adapters) == ['summary']
                and not m.disable_adapters for m in layers), 'Actual TIME role/flags/inventory differs')
    return dict(**counts,conservative_pipeline_parameters=8797892873,all_frozen=True,active_adapter='summary',matrices=matrices)


def run(role):
    require(role=='TRAINED','Original same-input INIT43 must be adopted, never repeated')
    require(os.environ.get('CUDA_VISIBLE_DEVICES') not in (None,''), 'Shared wrapper must expose actual GPU')
    reg = read(ROOT/'summary_generation_registration_10.json')
    require(reg['schema'] == 'FIXED_TWO_VIEW_SUMMARY_MATCHED_DEV43_GENERATION_V10', 'Explicit generation registration')
    for name,r in reg['code'].items():
        require(bound(r) == Path(__file__).resolve().parent/name, 'Executed generation component differs')
    cfg = read(bound(reg['model_config_ref']))
    original = bound(reg['initial_TIME_ref'])
    require(original == Path(cfg['b_adapter'])/'adapter_model.safetensors' and sha(original) == cfg['b_adapter_sha256'],
            'Original TIME file identity')
    repair = read(bound(reg['scientific_repair_registration_ref']))
    require(repair['only_loss_reduction_changed'] is True,'Explicit registered single-factor comparison')
    if role == 'INIT_TIME':
        weights = original; frozen_selection = None
    else:
        frozen_selection = ROOT/'summary_final_weights_frozen_10.json'
        selected = read(frozen_selection)
        require(selected['status'] == 'FINAL559_WEIGHTS_FROZEN_BEFORE_DEV_METRICS', 'Only fixed final559 checkpoint')
        trained = read(bound(selected['training_completion_ref']))
        require(trained['status'] == 'PASS_SUMMARY_FINAL559_SINGLE_EPOCH' and trained['completed_updates'] == 559
                and trained['successful_micro'] == 2236, 'Full registered single epoch, no checkpoint choice')
        weights = bound(selected['final_adapter_ref'])
        require(ref(weights) == trained['adapter_weights_ref'], 'Frozen final weights differ from actual training terminal')
    weight_reference = ref(weights)
    out = ROOT/'summary_generation_10'/role; out.mkdir(parents=True,exist_ok=False)
    save(out/'claim.json',dict(model_role=role,registration=ref(ROOT/'summary_generation_registration_10.json'),
         weights=weight_reference,pid=os.getpid()))
    started = time.monotonic(); outputs = []; tokens_saved = []
    def deadline():
        require(datetime.now(timezone.utc) < datetime.fromisoformat(reg['deadline_utc'].replace('Z','+00:00'))
            and time.monotonic()-started < reg['max_gpu_seconds_by_role'][role], 'No new call beyond actual registered budget')
    try:
        sys.path.insert(0,str(RUN/'temporal_sft8b_v1'))
        from sft_contract import verify_live_gpu_reservation
        from verify_saved_smoke import canonical_frozen_hash
        verify_live_gpu_reservation(); deadline()
        import transformers,peft
        from transformers import Qwen3VLForConditionalGeneration,AutoTokenizer
        from peft import PeftModel,get_peft_model_state_dict
        from safetensors.torch import load_file
        require(transformers.__version__ == '4.57.1' and peft.__version__ == '0.17.1', 'Pinned actual runtime')
        inputs = DevInputs(reg)
        base = Qwen3VLForConditionalGeneration.from_pretrained(cfg['model_dir'],revision=cfg['model_revision'],
            local_files_only=True,torch_dtype=torch.bfloat16,device_map={'':'cuda:0'},low_cpu_mem_usage=True,attn_implementation='sdpa')
        for p in base.parameters():p.requires_grad_(False)
        before = canonical_frozen_hash(base,torch)
        require(before['parameters'] == 8767123696 and before['sha256'] == cfg['expected_base_sha256'], 'Actual shared BASE bytes')
        model = PeftModel.from_pretrained(base,str(weights.parent),adapter_name='summary',is_trainable=False).eval()
        for p in model.parameters():p.requires_grad_(False)
        inv = inventory(model)
        state = get_peft_model_state_dict(model,adapter_name='summary'); saved = load_file(str(weights),device='cpu')
        require(set(state) == set(saved) and all(torch.equal(state[k].detach().cpu(),saved[k].to(state[k].dtype)) for k in state),
                'Actual role model equals its bound saved weights')
        del state,saved
        tokenizer = AutoTokenizer.from_pretrained(cfg['model_dir'],local_files_only=True)
        eos = tokenizer.convert_tokens_to_ids('<|im_end|>'); require(eos == 151645, 'Same trained terminal EOS')
        candidates = ascii_token_candidates(tokenizer)
        for request_ref in inputs.prepared['inputs']:
            deadline(); request,values = inputs.get(request_ref); uid = request['uid']
            duration = F(request['plan']['window_end_exact'])-F(request['plan']['window_start_exact'])
            prefix = values['input_ids'].shape[1]
            constraint = PrefixConstraint(tokenizer,prefix,duration,max_segments=6,candidate_token_ids=candidates,
                                          eos_token_ids=[eos],allow_empty=True)
            gpu = {k:v.to('cuda:0') for k,v in values.items()}
            event(out/'journal.jsonl','BEGIN_GENERATION',uid=uid,model_role=role,request_ref=request_ref)
            with torch.inference_mode():
                generated = model.generate(**gpu,max_new_tokens=512,do_sample=False,num_beams=1,use_cache=True,
                    eos_token_id=eos,pad_token_id=eos,prefix_allowed_tokens_fn=constraint)
            torch.cuda.synchronize()
            ids = generated[0,prefix:].detach().cpu().tolist()
            raw_tokens = out/(uid+'.tokens.json')
            save(raw_tokens,dict(uid=uid,sid=request['sid'],request_ref=request_ref,generated_ids=ids,
                                model_role=role,model_weights_ref=weight_reference))
            tokens_saved.append(ref(raw_tokens))
            require(torch.equal(generated[0,:prefix].detach().cpu(),values['input_ids'][0]), 'Actual generated prefix identity')
            constraint.assert_complete(ids)  # Syntax-only return value is never used for numeric mapping.
            require(ids and ids[-1] == eos, 'Natural complete EOS required')
            text = tokenizer.decode(ids[:-1],skip_special_tokens=False,clean_up_tokenization_spaces=False)
            segments = parse_summary(text,duration)
            path = out/(uid+'.output.json')
            save(path,dict(uid=uid,sid=request['sid'],raw_text=text,generated_ids=ids,raw_token_ref=ref(raw_tokens),
                 request_ref=request_ref,model_role=role,model_weights_ref=weight_reference,
                 parsed_exact_segments=[[str(a),str(b)] for a,b in segments],grammar_stats=constraint.stats))
            outputs.append(ref(path)); event(out/'journal.jsonl','RAW_ACCEPTED',uid=uid,output_ref=outputs[-1])
            del gpu,generated
        require(len(outputs) == 43, 'All registered43 outputs exactly once')
        require(canonical_frozen_hash(model,torch) == before and sha(original) == cfg['b_adapter_sha256']
                and sha(weights) == weight_reference['sha256'], 'Frozen base/role weights/old TIME changed')
        inventory(model)
        save(out/'completion.json',dict(status='PASS_ALL43_MATCHED_SUMMARY_GENERATIONS',model_role=role,outputs=outputs,
            model_weights_ref=weight_reference,input_acceptance_ref=reg['first_dev_input_acceptance_ref'],
            base_fingerprint=before,inventory=inv,old_TIME_unchanged=True,optimizer_updates=0,
            frozen_selection_ref=ref(frozen_selection) if frozen_selection else None,elapsed_seconds=time.monotonic()-started))
    except BaseException as error:
        save(out/'failure.json',dict(error=repr(error),traceback=traceback.format_exc(),outputs=outputs,
            first_raw_token_generations=tokens_saved,model_role=role,automatic_retry=False,failure_to_empty=False))
        raise


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--role',choices=['INIT_TIME','TRAINED'],required=True)
    run(p.parse_args().role)
