"""One independent crop-r8 BASE-screen/pilot4/remaining496 experiment.

No TIME or old PAIR adapter is loaded. Only the frozen CPU train schedule carries
supervision. Screen inputs have no evaluation targets. No implicit retry/resume.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import random
import re
import sys
import time
import traceback
_support = Path(__file__).resolve().parents[1]/'pair_code_17'
if _support.is_dir(): sys.path.insert(0, str(_support))
from pair_common import WORK, read, save, sha, ref, bound, require, utc, signature, paths, append_event
ADAPTER='crop'
BASE_PARAMETERS=8767123696
CROP_PARAMETERS=7667712
OLD_PAIR_PARAMETERS=7667712
OLD_TIME_PARAMETERS=15335424
SEMANTIC_PARAMETERS=98329
RECIPE=dict(updates=500,grad_accum=4,rank=8,alpha=16,dropout=0,lr=5e-5,weight_decay=0,grad_clip=1,seed=20261018)
TARGET=re.compile(r'language_model\.layers\.(\d+)\.self_attn\.(q_proj|k_proj|v_proj|o_proj)$')
TRAINABLE=re.compile(r'language_model\.layers\.(\d+)\.self_attn\.(q_proj|k_proj|v_proj|o_proj)\.lora_(A|B)\.crop\.weight$')

def _sync_directory(path):
    descriptor = os.open(str(path), os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _tensor_file(path, value, torch):
    """Persist a first raw result before any post-forward acceptance checks."""
    with Path(path).open('xb') as stream:
        torch.save(value, stream); stream.flush(); os.fsync(stream.fileno())
    _sync_directory(Path(path).parent)


def _atomic_progress(path, value, torch):
    temporary = path.with_name(path.name+'.pending')
    _tensor_file(temporary, value, torch)
    os.replace(temporary, path)
    _sync_directory(path.parent)


def _copy_exclusive(source, destination):
    with source.open('rb') as src, destination.open('xb') as dst:
        for block in iter(lambda: src.read(8 << 20), b''):
            dst.write(block)
        dst.flush(); os.fsync(dst.fileno())
    _sync_directory(destination.parent)


def _cpu_tree(value, torch):
    if isinstance(value, torch.Tensor):
        return value.detach().cpu().contiguous().clone()
    if isinstance(value, dict):
        return {k: _cpu_tree(v, torch) for k, v in value.items()}
    if isinstance(value, list):
        return [_cpu_tree(v, torch) for v in value]
    if isinstance(value, tuple):
        return tuple(_cpu_tree(v, torch) for v in value)
    return value


def _adapter_state(model, torch):
    from peft import get_peft_model_state_dict
    state = _cpu_tree(get_peft_model_state_dict(model, adapter_name=ADAPTER), torch)
    require(len(state) == 288 and all('lora_' in k for k in state), 'Only288 new CROP matrices may be saved')
    return state


def _inventory(model, training, torch):
    trainable = []
    base_count = crop_count = 0
    for name, parameter in model.named_parameters():
        if 'lora_' in name:
            match = TRAINABLE.search(name)
            require(match is not None, 'Unexpected adapter tensor: '+name)
            require(parameter.ndim == 2 and (parameter.shape[0] if match[3] == 'A' else parameter.shape[1]) == 8,
                    'Actual CROP rank differs')
            require(parameter.requires_grad == training, 'Actual CROP trainability differs')
            crop_count += parameter.numel(); trainable.append((name, parameter))
        else:
            require(not parameter.requires_grad, 'BASE/vision/embedding/head became trainable')
            base_count += parameter.numel()
    layers = [(n, m) for n, m in model.named_modules() if hasattr(m, 'lora_A')]
    require(len(layers) == 144 and all(set(m.lora_A) == {ADAPTER} and not bool(m.disable_adapters)
              and list(m.active_adapters) == [ADAPTER] for _, m in layers), 'Exact144 active CROP-only layers required')
    require(model.active_adapter == ADAPTER and len(trainable) == 288
            and base_count == BASE_PARAMETERS and crop_count == CROP_PARAMETERS,
            'Actual BASE plus independent CROP parameter inventory differs')
    conservative = base_count+crop_count+OLD_TIME_PARAMETERS+SEMANTIC_PARAMETERS+OLD_PAIR_PARAMETERS
    require(conservative <= 9000000000, 'Conservative whole-pipeline parameter budget exceeded')
    return trainable, dict(base=base_count, crop=crop_count, resident=base_count+crop_count,
             conservative_pipeline=conservative, original_TIME_loaded=False,
             original_TIME_counted=OLD_TIME_PARAMETERS, semantic_counted=SEMANTIC_PARAMETERS,
             old_PAIR_counted=OLD_PAIR_PARAMETERS, old_PAIR_loaded=False, adapter=ADAPTER, actual_lora_matrices=288, actual_language_targets=144)


def _softmax3(logits, np):
    values = np.asarray(logits, dtype=np.float64)
    exponential = np.exp(values-values.max())
    return (exponential/exponential.sum()).tolist()


def _deadline(reg):
    if 'deadline_utc' in reg:
        import datetime as dt
        require(dt.datetime.now(dt.timezone.utc) < dt.datetime.fromisoformat(reg['deadline_utc'].replace('Z', '+00:00')),
                'No new model call after registered goal deadline')


def _progress(model, optimizer, torch, np, step, schedule_sha, targets_ref, recipe):
    numpy_state = np.random.get_state()
    return dict(schema='CROP_R8_COMPLETE_UPDATE_PROGRESS_V1', adapter_state_dict=_adapter_state(model, torch),
         optimizer_state_dict=_cpu_tree(optimizer.state_dict(), torch), torch_rng_state=torch.get_rng_state(),
         torch_cuda_rng_state_all=[v.cpu() for v in torch.cuda.get_rng_state_all()],
         numpy_rng_state=dict(name=numpy_state[0], keys=torch.tensor(numpy_state[1].astype(np.int64)),
              position=int(numpy_state[2]), has_gauss=int(numpy_state[3]), cached_gaussian=float(numpy_state[4])),
         python_rng_state=random.getstate(), step=step, micro=step*4,
         schedule_sha256=schedule_sha, train_schedule_reference=targets_ref, recipe=recipe,
         original_TIME_loaded=False, old_PAIR_loaded=False, no_base_tensors_saved=True)


def _restore_rng(state, torch, np):
    torch.set_rng_state(state['torch_rng_state'])
    torch.cuda.set_rng_state_all(state['torch_cuda_rng_state_all'])
    n = state['numpy_rng_state']
    np.random.set_state((n['name'], n['keys'].numpy().astype(np.uint32), n['position'], n['has_gauss'], n['cached_gaussian']))
    random.setstate(state['python_rng_state'])


def _load_module(reference):
    name = '_frozen_crop31_input_loader'
    require(name not in sys.modules, 'Crop input helper already loaded from another path')
    file = bound(reference)
    sys.path.insert(0, str(file.parent))
    spec = importlib.util.spec_from_file_location(name, file)
    require(spec is not None and spec.loader is not None, 'Frozen crop input helper cannot load')
    module = importlib.util.module_from_spec(spec); sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _registration(root, phase):
    original = root/'crop_GPU_registration_32.json'; reg = read(original)
    require(reg['schema'] == 'CROP_PAIR_RENDER_LANGUAGE_PILOT_V32'
            and bound(reg['GPU_code']) == Path(__file__).resolve(), 'Exact crop32 GPU entry required')
    require(reg['recipe'] == RECIPE and reg['expected_train_micro'] == 2000 and reg['pilot_updates'] == 4
            and reg['conservative_pipeline_parameters'] == 8797892873 and 0 < reg['expected_screen_inputs'] <= 280,
            'Fixed crop training recipe/inventory/screen budget differs')
    require(bound(reg['CPU_registration']) == (root/'crop_CPU_registration_31.json').resolve()
            and bound(reg['input_acceptance']) == (root/'crop_inputs_31/input_acceptance.json').resolve(),
            'Only the bound original31 CPU registration and complete first QA are allowed')
    cpu = read(bound(reg['CPU_registration'])); gate = read(bound(reg['input_acceptance']))
    require(gate['status'] == 'PASS_ALL_CROP31_TRIPLET_FIRST_CPU_QA' and gate['train_micro'] == 2000
            and gate['screen_inputs'] == reg['expected_screen_inputs']
            and gate['first_independent_pixels_text_native_QA'] is True, 'Complete first source+A+B CPU QA required')
    require(cpu['preparation_code'] == reg['preparation_code'], 'Registered actual crop input entry differs')
    old18 = read(bound(reg['original_GPU18']))
    for reference in old18['runtime_dependencies']: bound(reference)
    old17 = read(bound(old18['pair_registration']))
    for name, digest in old17['new_code'].items():
        require(sha(root/'pair_code_17'/name) == digest, 'Frozen runtime helper changed: '+name)
    require(reg['model_config'] == old17['model_config'] and reg['old_TIME'] == old17['old_TIME_weights'],
            'Crop BASE/TIME binding differs from original frozen physical model')
    bound(reg['old_PAIR']); bound(reg['old_TIME']); bound(reg['preparation_code'])
    admission, admission_ref = reg, ref(original)
    if phase == 'remaining496':
        path = root/'crop_remaining_admission_33.json'; admission = read(path); admission_ref = ref(path)
        require(admission['schema'] == 'CROP_PAIR_REMAINING496_V33'
                and admission['original_pilot_registration'] == ref(original)
                and admission['GPU_code'] == reg['GPU_code'] and admission['input_acceptance'] == reg['input_acceptance']
                and admission['expected_remaining_updates'] == 496, 'Separate explicit remaining496 admission required')
    return reg, cpu, gate, admission, admission_ref


def _schedule(prepared, prepared_ref):
    import numpy as np
    rows = prepared['train_schedule']; screen = prepared['screen_inputs']
    require(isinstance(rows, list) and len(rows) == 2000 and len({r['id'] for r in rows}) == 2000,
            'Exactly2000 unique scheduled micro IDs required; input IDs may repeat')
    require(len({r['id'] for r in screen}) == len(screen) and bool(screen), 'Unique nonempty frozen screen inputs required')
    train_ids = {r['source_id'] for r in rows}; screen_ids = {r['source_id'] for r in screen}
    require(train_ids and not train_ids & screen_ids, 'Crop train source identities must be disjoint from screen')
    counts = Counter(row['source_id'] for row in rows)
    require(max(counts.values())-min(counts.values()) <= 1, 'Supplied2000 schedule must remain source-uniform')
    for row in rows:
        p = np.asarray(row['target'], dtype=np.float64)
        require(p.shape == (3,) and np.isfinite(p).all() and np.isin(p, [0., 1.]).all() and p.sum() == 1.,
                'Only fixed train-only three-class onehot IoU preference targets required')
        bound(row['input'])
    digest = hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return rows, digest, prepared_ref, dict(counts)


def _input(inputs, entry, torch, *, training):
    values, request = inputs.get(entry['input'])
    require(request['source_id'] == entry['source_id'] and (training or request['id'] == entry['id'])
            and request['class_token_ids'] == inputs.prepared['class_token_ids']
            and isinstance(request['source_sha256'], str) and len(request['source_sha256']) == 64,
            'Actual source/class/input identity differs; schedule ID is not an inference ID')
    require(set(values) == {'input_ids', 'attention_mask', 'pixel_values', 'image_grid_thw'}
            and signature(values) == request['input_signature'], 'Actual first-QA triplet tokens/pixels differ')
    grid = values['image_grid_thw']
    require(grid.device.type == 'cpu' and grid.dtype == torch.int64 and tuple(grid.shape) == (3, 3)
            and bool((grid > 0).all()) and bool((grid[:, 0] == 1).all()) and bool((grid[:, 1:] % 2 == 0).all()),
            'Exactly three accepted source/A/B image grids required')
    return values, request


def _same_state(actual, expected, torch):
    return set(actual) == set(expected) and all(actual[k].dtype == v.dtype and actual[k].shape == v.shape
        and torch.equal(actual[k].contiguous().view(torch.uint8), v.contiguous().view(torch.uint8)) for k, v in expected.items())


def _prediction_stage(root, model, inputs, entries, role, admission, torch, np, successful_raw):
    stage = root/'crop_model_31'/role; stage.mkdir(exist_ok=False)
    journal = stage/'attempts.jsonl'; journal.touch(exist_ok=False)
    require(len({e['id'] for e in entries}) == len(entries), 'Each screen request occurs once per weights role')
    model.eval(); require(not any(p.requires_grad for p in model.parameters()), 'Screen weights must be wholly frozen')
    vocabulary = int(model.config.text_config.vocab_size)
    aliases, completed = {}, []
    for index, entry in enumerate(entries):
        _deadline(admission); values, request = _input(inputs, entry, torch, training=False)
        classes = request['class_token_ids']
        key = json.dumps(dict(signature=request['input_signature'], source_id=request['source_id'],
            source_sha256=request['source_sha256'], classes=classes), sort_keys=True, separators=(',', ':'))
        previous = aliases.get(key); started = time.monotonic()
        if previous is None:
            gpu = {k: v.to('cuda:0') for k, v in values.items()}
            append_event(journal, event='BEGIN_NEW_ROLE_FORWARD', id=entry['id'], input=entry['input'], model_role=role)
            _deadline(admission)
            with torch.inference_mode():
                result = model(**gpu, use_cache=False, return_dict=True, logits_to_keep=1)
                raw = result.logits[0, -1].float().detach().cpu().contiguous()
            raw_path = stage/('%04d.lastlogits.pt' % index); _tensor_file(raw_path, raw, torch)
            raw_reference = ref(raw_path)
            successful_raw.append(dict(id=entry['id'], source_id=request['source_id'], source_sha256=request['source_sha256'],
                                       model_role=role, raw_logits=raw_reference))
            append_event(journal, event='FIRST_RAW_PERSISTED', id=entry['id'], raw_logits=raw_reference, model_role=role)
            torch.cuda.synchronize(); del gpu, result
        else:
            raw_reference = previous['raw_logits']; raw = torch.load(bound(raw_reference), map_location='cpu', weights_only=True)
        require(raw.ndim == 1 and raw.dtype == torch.float32 and len(raw) == vocabulary and bool(torch.isfinite(raw).all()),
                'Finite full-vocabulary raw screen logits required after persistence')
        require(len(classes) == len(set(classes)) == 3 and all(type(k) is int and 0 <= k < len(raw) for k in classes),
                'Exact three class digit IDs outside full vocabulary')
        three = raw[classes].numpy().astype(np.float64); receipt_path = stage/('%04d.receipt.json' % index)
        save(receipt_path, dict(id=entry['id'], source_id=request['source_id'], source_sha256=request['source_sha256'],
            input=entry['input'], role='CROP_SCREEN_NO_GT', model_role=role, raw_logits=raw_reference,
            class_token_ids=classes, class_logits=three.tolist(), probabilities=_softmax3(three, np),
            predicted_index=int(np.argmax(three)), full_vocabulary_size=len(raw), raw_dtype='torch.float32',
            input_signature=request['input_signature'], softmax_scope='Three class logits ONLY; not calibrated confidence',
            actual_new_forward=previous is None, alias_of=previous['receipt'] if previous else None,
            elapsed_seconds=time.monotonic()-started, screen_reference_read=False, original_TIME_loaded=False, old_PAIR_loaded=False))
        receipt_reference = ref(receipt_path)
        if previous is None: aliases[key] = dict(raw_logits=raw_reference, receipt=receipt_reference)
        completed.append(dict(id=entry['id'], input=entry['input'], receipt=receipt_reference))
        append_event(journal, event='ACCEPTED_NEW_ROLE_RESULT', id=entry['id'], receipt=receipt_reference,
                     alias=previous is not None, model_role=role)
        del values, raw
    save(stage/'completion.json', dict(status='COMPLETE_ALL_ROLE_INPUTS_RAW_LOGITS_NOT_QUALITY', model_role=role,
        entries=completed, actual_forward_calls=len(aliases), aliases=len(entries)-len(aliases), expected_inputs=len(entries),
        full_vocabulary_size=vocabulary, screen_reference_read=False, original_TIME_loaded=False, old_PAIR_loaded=False))
    return ref(stage/'completion.json')


def run(root, phase):
    root = Path(root).resolve()
    require(phase in ('pilot4', 'remaining496') and root.is_relative_to(WORK) and bool(os.environ.get('CUDA_VISIBLE_DEVICES')),
            'Explicit independent crop GPU phase/physical assignment required')
    reg, cpu, gate, admission, admission_ref = _registration(root, phase); paths(); _deadline(admission)
    from sft_contract import verify_live_gpu_reservation, REVISION
    from verify_saved_smoke import canonical_frozen_hash
    verify_live_gpu_reservation()
    require(read(WORK/'improvement_round1/active_gpu_job.json')['name'] == admission['GPU_job'], 'Active GPU reservation belongs to another job')
    import numpy as np
    import torch
    import transformers
    import peft
    from transformers import Qwen3VLForConditionalGeneration
    from peft import LoraConfig, get_peft_model, PeftModel, set_peft_model_state_dict
    from safetensors.torch import load_file
    require(transformers.__version__ == '4.57.1' and peft.__version__ == '0.17.1', 'Frozen crop runtime differs')
    torch.set_num_threads(2)
    random.seed(RECIPE['seed']); np.random.seed(RECIPE['seed']); torch.manual_seed(RECIPE['seed']); torch.cuda.manual_seed_all(RECIPE['seed'])
    preparation = _load_module(reg['preparation_code']); inputs = preparation.CropInputs(root)
    require(inputs.reg == cpu and inputs.prepared == read(bound(gate['prepared']))
            and len(inputs.prepared['screen_inputs']) == reg['expected_screen_inputs'], 'Actual frozen31 input loader/gate differs')
    cfg = read(bound(reg['model_config'])); old_time = bound(reg['old_TIME']); old_pair = bound(reg['old_PAIR'])
    require(cfg['base_parameters'] == BASE_PARAMETERS and sha(old_time) == cfg['b_adapter_sha256'], 'Original BASE/TIME identity differs')
    out = root/'crop_model_31'
    if phase == 'pilot4': out.mkdir(exist_ok=False)
    else: require(out.is_dir(), 'Remaining496 needs original completed pilot4 directory')
    save(out/(phase+'_claim.json'), dict(utc=utc(), pid=os.getpid(), phase=phase, GPU_admission=admission_ref,
        original_GPU_registration=ref(root/'crop_GPU_registration_32.json'), input_acceptance=reg['input_acceptance'],
        original_TIME_loaded=False, old_PAIR_loaded=False, model_role='BASE_THEN_NEW_CROP_ONLY'))
    successful_raw=[]; completed_step=successful_micro=0; progress_path=out/'train/progress.pt'
    try:
        pilot = resumed = None
        if phase == 'remaining496':
            require(bound(admission['pilot_completion']) == (out/'pilot_completion.json').resolve(), 'Exact completed crop pilot required')
            pilot = read(bound(admission['pilot_completion']))
            require(pilot['status'] == 'COMPLETE_FIXED4_CROP_ENGINEERING_NO_TRAINED_SCREEN'
                    and pilot['GPU_registration'] == ref(root/'crop_GPU_registration_32.json')
                    and pilot['completed_updates'] == 4 and pilot['successful_micro'] == 16
                    and admission['immutable_pilot_progress'] == pilot['progress']
                    and admission['BASE_completion'] == pilot['BASE_completion'], 'Only exact original step4/BASE completion may be adopted')
            checkpoint = bound(admission['immutable_pilot_progress']); bound(pilot['BASE_completion'])
            require(checkpoint == (out/'train/pilot_progress.pt').resolve()
                    and bound(pilot['BASE_completion']) == (out/'BASE_screen/completion.json').resolve(),
                    'Actual immutable pilot progress and original BASE screen paths differ')
            require(sha(progress_path) == sha(checkpoint), 'Mutable progress advanced beyond explicit remaining admission')
            resumed = torch.load(checkpoint, map_location='cpu', weights_only=True)
        schedule, schedule_sha, schedule_ref, source_draws = _schedule(inputs.prepared, gate['prepared'])
        _deadline(admission)
        base = Qwen3VLForConditionalGeneration.from_pretrained(cfg['model_dir'], revision=REVISION,
            local_files_only=True, torch_dtype=torch.bfloat16, device_map={'': 'cuda:0'}, low_cpu_mem_usage=True, attn_implementation='sdpa')
        for p in base.parameters(): p.requires_grad_(False)
        base.eval(); base.config.use_cache=False
        require(not any('lora_' in n for n,_ in base.named_parameters()), 'Old TIME/PAIR or another adapter was unexpectedly loaded')
        before = canonical_frozen_hash(base, torch)
        require(before['parameters'] == BASE_PARAMETERS and before['sha256'] == cfg['expected_base_sha256'], 'Original physical BASE differs')
        save(out/(phase+'_base_identity.json'), dict(base=before, original_TIME=reg['old_TIME'], old_PAIR=reg['old_PAIR'],
            original_TIME_loaded=False, old_PAIR_loaded=False, conservative_pipeline_parameters=8797892873))
        if phase == 'pilot4':
            base_completion = _prediction_stage(root, base, inputs, inputs.prepared['screen_inputs'], 'BASE_screen', admission, torch, np, successful_raw)
        else: base_completion = pilot['BASE_completion']
        targets=[n for n,m in base.named_modules() if isinstance(m,torch.nn.Linear) and TARGET.search(n)]
        require(len(targets) == 144, 'Exactly144 language q/k/v/o CROP targets required')
        random.seed(RECIPE['seed']); np.random.seed(RECIPE['seed']); torch.manual_seed(RECIPE['seed']); torch.cuda.manual_seed_all(RECIPE['seed'])
        model=get_peft_model(base,LoraConfig(r=8,lora_alpha=16,lora_dropout=0.,bias='none',target_modules=targets,
            task_type='CAUSAL_LM',modules_to_save=None),adapter_name=ADAPTER)
        for name,p in model.named_parameters(): p.requires_grad_(TRAINABLE.search(name) is not None)
        parameters,inventory=_inventory(model,True,torch)
        require(inventory['conservative_pipeline'] == 8797892873 and inventory['resident'] == 8774791408, 'Actual crop inventory differs')
        optimizer=torch.optim.AdamW([p for _,p in parameters],lr=5e-5,weight_decay=0.)
        start_step=0
        if resumed is not None:
            require(resumed['schema']=='CROP_R8_COMPLETE_UPDATE_PROGRESS_V1' and resumed['step']==4 and resumed['micro']==16
                and resumed['recipe']==RECIPE and resumed['schedule_sha256']==schedule_sha
                and resumed['train_schedule_reference']==schedule_ref, 'Step4 recipe/schedule/RNG identity differs')
            set_peft_model_state_dict(model,resumed['adapter_state_dict'],adapter_name=ADAPTER)
            require(_same_state(_adapter_state(model,torch),resumed['adapter_state_dict'],torch),'Restored crop step4 matrices differ')
            optimizer.load_state_dict(resumed['optimizer_state_dict']); _restore_rng(resumed,torch,np)
            start_step=completed_step=4; successful_micro=16
        train=out/'train'; train.mkdir(exist_ok=phase=='remaining496'); initial=_adapter_state(model,torch)
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={'use_reentrant':False}); model.train()
        for name,module in model.named_modules():
            if name.endswith('.visual'): module.eval()
        _inventory(model,True,torch)
        micro_journal=train/(phase+'_micro_loss.jsonl'); micro_journal.touch(exist_ok=False)
        update_journal=train/(phase+'_updates.jsonl'); update_journal.touch(exist_ok=False)
        stop_step=4 if phase=='pilot4' else 500
        for step in range(start_step+1,stop_step+1):
            optimizer.zero_grad(set_to_none=True); losses=[]
            for micro in range((step-1)*4,step*4):
                _deadline(admission); row=schedule[micro]; values,request=_input(inputs,row,torch,training=True)
                gpu={k:v.to('cuda:0') for k,v in values.items()}
                append_event(micro_journal,event='BEGIN_TRAIN_MICRO',step=step,micro=micro,id=row['id'],request_id=request['id'],
                    source_id=row['source_id'],input=row['input'])
                result=model(**gpu,use_cache=False,return_dict=True,logits_to_keep=1); classes=request['class_token_ids']
                require(len(classes)==len(set(classes))==3 and all(type(k)is int and 0<=k<result.logits.shape[-1] for k in classes),'Actual crop class mapping differs')
                logits=result.logits[0,-1,classes].float(); target=torch.tensor(row['target'],dtype=torch.float32,device=logits.device)
                loss=-(target*torch.nn.functional.log_softmax(logits,dim=-1)).sum(); value=float(loss.detach().cpu())
                append_event(micro_journal,event='TRAIN_RAW_LOSS',step=step,micro=micro,id=row['id'],request_id=request['id'],
                    source_id=row['source_id'],loss=value if np.isfinite(value) else None,loss_repr=repr(value),class_token_ids=classes,
                    softmax_scope='THREE_CLASSES_ONLY')
                require(np.isfinite(value),'Nonfinite crop training loss'); (loss/4).backward(); successful_micro=micro+1; losses.append(value)
                append_event(micro_journal,event='TRAIN_BACKWARD_COMPLETE',step=step,micro=micro,id=row['id'])
                del gpu,values,result,logits,target,loss
            gradients=[p.grad for _,p in parameters]
            require(all(g is not None and bool(torch.isfinite(g).all()) for g in gradients),'Missing/nonfinite CROP gradients')
            nonzero=sum(bool(torch.count_nonzero(g)) for g in gradients)
            gradient_norm=float(torch.nn.utils.clip_grad_norm_([p for _,p in parameters],1.).detach().cpu())
            require(np.isfinite(gradient_norm) and gradient_norm>0 and nonzero>0,'No finite nonzero CROP gradient update')
            optimizer.step(); completed_step=step
            checkpoint=_progress(model,optimizer,torch,np,step,schedule_sha,schedule_ref,RECIPE); _atomic_progress(progress_path,checkpoint,torch)
            append_event(update_journal,event='SUCCESSFUL_UPDATE_PERSISTED',step=step,micro=step*4,mean_micro_loss=float(np.mean(losses)),
                preclip_gradient_norm=gradient_norm,finite_gradient_matrices=len(gradients),nonzero_gradient_matrices=nonzero,progress_sha256=sha(progress_path))
            _inventory(model,True,torch)
            require(all(bool(torch.isfinite(v).all()) for v in checkpoint['adapter_state_dict'].values()),'CROP weights nonfinite after persisted update')
        optimizer.zero_grad(set_to_none=True); model.eval(); model.gradient_checkpointing_disable()
        for p in model.parameters(): p.requires_grad_(False)
        _inventory(model,False,torch); final_state=_adapter_state(model,torch)
        require(not _same_state(initial,final_state,torch),'No actual CROP update occurred')
        if phase=='pilot4':
            immutable=train/'pilot_progress.pt'; _copy_exclusive(progress_path,immutable)
            after=canonical_frozen_hash(model,torch)
            require(after==before and sha(old_time)==reg['old_TIME']['sha256'] and sha(old_pair)==reg['old_PAIR']['sha256'],'Frozen BASE/TIME/oldPAIR changed')
            save(out/'pilot_completion.json',dict(status='COMPLETE_FIXED4_CROP_ENGINEERING_NO_TRAINED_SCREEN',completed_updates=4,
                successful_micro=16,progress=ref(immutable),BASE_completion=base_completion,update_journal=ref(update_journal),
                micro_journal=ref(micro_journal),inventory=inventory,base_fingerprint=after,schedule_sha256=schedule_sha,
                train_schedule_reference=schedule_ref,train_source_draws=source_draws,GPU_registration=ref(root/'crop_GPU_registration_32.json'),
                original_TIME_loaded=False,old_PAIR_loaded=False,screen_reference_read=False,final_quality_checkpoint_selected=False))
            return
        adapter=train/'adapter'; adapter.mkdir(exist_ok=False)
        model.save_pretrained(adapter,safe_serialization=True,selected_adapters=[ADAPTER],save_embedding_layers=False)
        weights=list(adapter.rglob('adapter_model.safetensors')); require(len(weights)==1 and weights[0].parent==adapter/'crop','Exactly final crop-only adapter/crop artifact required')
        for file in adapter.rglob('*'):
            if file.is_file():
                with file.open('rb') as stream: os.fsync(stream.fileno())
        _sync_directory(adapter/'crop'); _sync_directory(adapter); weights=weights[0]
        saved=load_file(str(weights),device='cpu'); require(_same_state(saved,final_state,torch),'Saved final500 crop matrices differ')
        base=model.unload()
        for p in base.parameters(): p.requires_grad_(False)
        require(not any('lora_' in n for n,_ in base.named_parameters()),'Unloading CROP left an adapter')
        model=PeftModel.from_pretrained(base,str(weights.parent),adapter_name=ADAPTER,is_trainable=False).eval()
        for p in model.parameters(): p.requires_grad_(False)
        require(_same_state(_adapter_state(model,torch),final_state,torch),'Readonly final500 CROP reload differs'); _inventory(model,False,torch)
        trained=_prediction_stage(root,model,inputs,inputs.prepared['screen_inputs'],'TRAINED_screen',admission,torch,np,successful_raw)
        _inventory(model,False,torch)
        require(_same_state(_adapter_state(model,torch),final_state,torch),'Readonly crop changed during screen')
        after=canonical_frozen_hash(model,torch)
        require(after==before and sha(old_time)==reg['old_TIME']['sha256'] and sha(old_pair)==reg['old_PAIR']['sha256'],'Frozen BASE/TIME/oldPAIR changed')
        save(out/'completion.json',dict(status='COMPLETE_FIXED_FINAL500_CROP_COMPARISON_NOT_QUALITY',BASE_completion=base_completion,
            TRAINED_completion=trained,pilot_completion=admission['pilot_completion'],remaining_admission=admission_ref,completed_updates=500,
            successful_micro=2000,pilot_updates=4,remaining_updates=496,update_journal=ref(update_journal),micro_journal=ref(micro_journal),
            progress=ref(progress_path),adapter_weights=ref(weights),adapter_directory=str(weights.parent),adapter_reload_all288_exact=True,
            inventory=inventory,base_fingerprint=after,schedule_sha256=schedule_sha,train_schedule_reference=schedule_ref,
            train_source_draws=source_draws,actual_training_forwards=2000,actual_training_forwards_this_phase=1984,
            training_forwards_are_unique_inputs=False,unique_ordered_train_inputs=len({r['input']['sha256'] for r in schedule}),
            original_TIME_loaded=False,old_PAIR_loaded=False,original_TIME_unchanged=True,old_PAIR_unchanged=True,
            screen_reference_read=False,actual_quality_established=False,automatic_confirm=False,automatic_426=False,automatic_package=False))
    except BaseException as error:
        save(out/(phase+'_failure.json'),dict(error=repr(error),traceback=traceback.format_exc(),completed_updates=completed_step,
            successful_micro=successful_micro,successful_raw=successful_raw,last_progress=ref(progress_path) if progress_path.is_file() else None,
            preserve_all_success=True,do_not_repeat_success=True,automatic_resume=False,failure_is_not_empty=True,screen_reference_read=False))
        raise


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--phase',choices=('pilot4','remaining496'),required=True)
    args=parser.parse_args(); run(args.root,args.phase)


