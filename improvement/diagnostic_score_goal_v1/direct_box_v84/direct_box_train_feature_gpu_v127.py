"""One explicitly admitted, readonly final105 train602 feature pass; no GT IO."""
from __future__ import annotations
import argparse
import importlib.util
import os
from pathlib import Path
import sys
import time
import traceback

_here=Path(__file__).resolve()
for _support in (_here.parents[1]/'pair_code_17',_here.parents[1],_here.parents[2]/'pair_code_17'):
    if (_support/'pair_common.py').is_file():sys.path.insert(0,str(_support));break
from pair_common import WORK,read,save,ref,bound,require,utc,paths,append_event

SCHEMA='FROZEN_DIRECT_BOX105_TRAIN602_FEATURES_GPU_V127'
ROLE='DIRECT_BOX105_TRAIN602_FEATURES'
STATUS='COMPLETE_DIRECT_BOX127_TRAIN602_RAW_NOT_QUALITY'
INTEGRITY='PASS_DIRECT_BOX127_READONLY_MODEL_BYTE_IDENTITY'
GPU_REFS=('GPU_code','frozen_GPU105_code','frozen_GPU105_registration','frozen_GPU93_code','frozen_math93_code',
    'frozen_math84_code','math_code','training_completion','adapter_weights','head_weights','adapter_config',
    'model_config','preparation_code','CPU_registration','prepared','input_acceptance','old_TIME','old_PAIR','old_CROP','protocol')


def module(reference,name):
    p=bound(reference);require(name not in sys.modules,'One pinned127 module identity')
    sys.path.insert(0,str(p.parent));spec=importlib.util.spec_from_file_location(name,p)
    m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m


def validate_inputs(reg,prepared,gate):
    require(reg['schema']==SCHEMA and reg['purpose']=='CRITIC_TRAIN_FEATURES_ONLY' and reg['feature_pass_admitted'] is True
        and type(reg['expected_inputs']) is int and reg['expected_inputs']==reg['expected_sources']==602,
        'Explicit one train602 feature purpose; no quality/production qualification')
    require(prepared['schema']=='DIRECT_BOX_SOURCE_ONLY_INPUTS_V84'
        and gate['status']=='PASS_DIRECT_BOX84_ALL622_SOURCE_ONLY_FIRST_CPU_QA'
        and gate['prepared']==reg['prepared'] and gate['registration']==reg['CPU_registration'], 'Adopt original622 input QA')
    entries=prepared['train_inputs'];screen=prepared['screen_inputs']
    require(len(entries)==len({e['id'] for e in entries})==len({e['source_id'] for e in entries})
        ==len({e['source_sha256'] for e in entries})==602 and all(e['role']=='train' for e in entries),
        'Exactly original602 unique train source inputs')
    require(len(screen)==20 and not {e['source_sha256'] for e in entries}&{e['source_sha256'] for e in screen},
        'No historical39 or screen input may enter new train602 pass')
    return entries


def validate_training(reg,original,trained):
    require(original['GPU_code']==reg['frozen_GPU105_code']
        and all(original[k]==reg[k] for k in ('model_config','preparation_code','CPU_registration','prepared','input_acceptance',
            'math_code','frozen_GPU93_code','frozen_math93_code','frozen_math84_code','old_TIME','old_PAIR','old_CROP')),
        'Exact105 physical model/runtime and original87 input identity')
    require(trained['status']=='COMPLETE_DIRECT_BOX105_NEW778_NOT_QUALITY' and trained['GPU_registration']==reg['frozen_GPU105_registration']
        and trained['completed_updates']==778 and trained['successful_micro']==trained['actual_training_forwards']==3112
        and trained['original_successful_updates']==20 and trained['original_successful_forwards']==88
        and trained['total_adopted_plus_new_updates']==798 and trained['original93_progress']==original['original93_progress']
        and trained['optimizer_reset'] is True and trained['hidden_transform']=='F32_L2_UNIT_VECTOR_NO_EPS'
        and trained['adapter_reload_all288_exact'] is True and trained['head_reload_all2_exact'] is True
        and all(trained[k]==reg[k] for k in ('adapter_weights','head_weights')),
        'Only fixed final105 weights, never train/dev qualification fabrication')


def extract_stage(out,reg,registration_ref,entries,reader,model,head,helper,math105,io,torch,trace):
    journal=out/'attempts.jsonl';journal.touch(exist_ok=False)
    require(not any(p.requires_grad for p in model.parameters()) and not any(p.requires_grad for p in head.parameters()),'Readonly all model/head weights')
    completed=[];raw_paths=set();model.eval();head.eval()
    for index,entry in enumerate(entries):
        require(entry['role']=='train','No dev/test source feature forward')
        io._deadline(reg);values,q=helper._input(reader,entry,torch)
        require(q['role']=='train','Only train602 request role')
        append_event(journal,event='BEGIN_NEW_ROLE_FORWARD',id=entry['id'],input=entry['input'],model_role=ROLE)
        trace['attempted'].append(entry['id']);gpu={k:v.to('cuda:0') for k,v in values.items()}
        with torch.inference_mode():hidden=helper._hidden(model,gpu,torch,False);cpu=hidden.float().cpu().contiguous()
        hp=out/('%04d.hidden.pt'%index);io._tensor_file(hp,cpu,torch)
        item=dict(id=entry['id'],source_id=q['source_id'],source_sha256=q['source_sha256'],raw_hidden=ref(hp),model_forward_returned=True)
        trace['raw'].append(item)
        with torch.inference_mode():raw=head(math105.normalize_hidden(hidden));raw_cpu=raw.float().cpu().contiguous()
        zp=out/('%04d.head.pt'%index);io._tensor_file(zp,raw_cpu,torch);item['raw_head']=ref(zp)
        append_event(journal,event='FIRST_RAW_PERSISTED',id=entry['id'],model_role=ROLE,raw_hidden=item['raw_hidden'],raw_head=item['raw_head'])
        require(cpu.dtype==raw_cpu.dtype==torch.float32 and tuple(cpu.shape)==(4096,) and tuple(raw_cpu.shape)==(3,)
            and bool(torch.isfinite(cpu).all()) and bool(torch.isfinite(raw_cpu).all()),'Actual persisted finite hidden4096/head3')
        with torch.inference_mode():decoded=math105.decode_torch(raw,q['width'],q['height']).float().cpu().tolist()
        torch.cuda.synchronize()
        rp=out/('%04d.receipt.json'%index)
        save(rp,dict(id=entry['id'],source_id=q['source_id'],source_sha256=q['source_sha256'],role='train',model_role=ROLE,input=entry['input'],
            width=q['width'],height=q['height'],input_signature=q['input_signature'],image_grid_thw=q['image_grid_thw'],
            raw_hidden=item['raw_hidden'],raw_head=item['raw_head'],decoded_xyw=decoded,hidden_transform=math105.RECIPE['hidden_transform'],
            raw_dtype='torch.float32',hidden_dimension=4096,head_dimension=3,adapter_weights=reg['adapter_weights'],head_weights=reg['head_weights'],
            actual_new_forward=True,alias_of=None,targets_read=False,no_training=True,no_LM_generation=True,purpose=reg['purpose']))
        rr=ref(rp);completed.append(dict(id=entry['id'],source_id=q['source_id'],source_sha256=q['source_sha256'],input=entry['input'],receipt=rr))
        require(str(hp) not in raw_paths and str(zp) not in raw_paths,'No duplicate127 raw destination');raw_paths.update((str(hp),str(zp)))
        append_event(journal,event='ACCEPTED_NEW_ROLE_RESULT',id=entry['id'],receipt=rr,model_role=ROLE,alias=False)
        del values,gpu,hidden,cpu,raw,raw_cpu
    require(len(completed)==reg['expected_inputs'],'All registered new train feature inputs completed')
    save(out/'completion.json',dict(status=STATUS,model_role=ROLE,purpose=reg['purpose'],entries=completed,expected_inputs=len(entries),sources=len(entries),
        actual_forward_calls=len(completed),aliases=0,attempts=ref(journal),GPU_registration=registration_ref,
        input_prepared=reg['prepared'],CPU_registration=reg['CPU_registration'],input_acceptance=reg['input_acceptance'],
        training_completion=reg['training_completion'],adapter_weights=reg['adapter_weights'],head_weights=reg['head_weights'],
        hidden_transform=math105.RECIPE['hidden_transform'],targets_read=False,no_training=True,quality_established=False,
        automatic_confirm=False,automatic_production=False))
    return ref(out/'completion.json')


def run(root,registration_path):
    root=Path(root).resolve();rp=Path(registration_path).resolve();reg=read(rp)
    require(root.is_relative_to(WORK) and rp==root/'direct_box_train_feature_GPU_registration_127.json'
        and bool(os.environ.get('CUDA_VISIBLE_DEVICES')),'One explicitly registered Linux GPU127 purpose')
    for key in GPU_REFS:bound(reg[key])
    require(bound(reg['GPU_code'])==Path(__file__).resolve(),'Exact127 GPU code')
    require(Path(reg['output_directory']).resolve()==root/'direct_box_train_features_127','New isolated127 output namespace')
    prepared=read(bound(reg['prepared']));gate=read(bound(reg['input_acceptance']));entries=validate_inputs(reg,prepared,gate)
    original=read(bound(reg['frozen_GPU105_registration']));trained=read(bound(reg['training_completion']));validate_training(reg,original,trained)
    old32=read(bound(original['original_GPU32']));old18=read(bound(original['original_GPU18']))
    for item in old18['runtime_dependencies']:bound(item)
    old17=read(bound(old18['pair_registration']))
    for name,expected in old17['new_code'].items():require(ref(root/'pair_code_17'/name)['sha256']==expected,'Pinned runtime helper changed')
    helper=module(reg['frozen_GPU105_code'],'_train127_frozen105');io=module(old32['GPU_code'],'_train127_frozen_io32');paths()
    math105=module(reg['math_code'],'_train127_math105')
    require(trained['recipe']==original['recipe']==math105.RECIPE
        and Path(math105.frozen93.__file__).resolve()==bound(reg['frozen_math93_code'])
        and Path(math105.frozen93.frozen84.__file__).resolve()==bound(reg['frozen_math84_code']),'Exact105 L2/decoder dependency paths')
    reader_module=module(reg['preparation_code'],'_train127_input87');reader=reader_module.DirectBoxInputs(root)
    require(reader.prepared==prepared and ref(root/'direct_box_CPU_registration_87.json')==reg['CPU_registration'],'Exact adopted87 reader/cache')
    # Narrow the runtime reader below its original622 whitelist; no target or screen get.
    reader.allowed={e['id']:e for e in entries};reader.ref_to_id={(e['input']['path'],e['input']['sha256']):e['id'] for e in entries}
    import torch
    import transformers
    import peft
    from transformers import Qwen3VLForConditionalGeneration
    from peft import PeftModel
    from safetensors.torch import load_file
    from sft_contract import REVISION,verify_live_gpu_reservation
    from verify_saved_smoke import canonical_frozen_hash
    require(transformers.__version__=='4.57.1' and peft.__version__=='0.17.1','Pinned127 runtime')
    verify_live_gpu_reservation();require(read(WORK/'improvement_round1/active_gpu_job.json')['name']==reg['GPU_job'],'Exact unique127 GPU reservation')
    io._deadline(reg);torch.set_num_threads(2);out=Path(reg['output_directory']);out.mkdir(exist_ok=False)
    save(out/'claim.json',dict(utc=utc(),pid=os.getpid(),GPU_registration=ref(rp),purpose=reg['purpose'],targets_read=False,no_training=True))
    trace=dict(attempted=[],raw=[]);started=time.monotonic();torch.cuda.reset_peak_memory_stats()
    try:
        cfg=read(bound(reg['model_config']))
        base=Qwen3VLForConditionalGeneration.from_pretrained(cfg['model_dir'],revision=REVISION,local_files_only=True,torch_dtype=torch.bfloat16,
            device_map={'':'cuda:0'},low_cpu_mem_usage=True,attn_implementation='sdpa').eval()
        for p in base.parameters():p.requires_grad_(False)
        base.config.use_cache=False;before=canonical_frozen_hash(base,torch)
        require(before['parameters']==helper.BASE and before['sha256']==cfg['expected_base_sha256'] and before==trained['base_fingerprint'],'Frozen original BASE bytes')
        directory=Path(reg['adapter_directory']).resolve();adapter=bound(reg['adapter_weights'])
        require(directory==adapter.parent==Path(trained['adapter_directory']).resolve() and bound(reg['adapter_config'])==directory/'adapter_config.json','Exact final105 adapter directory')
        model=PeftModel.from_pretrained(base,str(directory),adapter_name='direct_box',is_trainable=False,local_files_only=True).eval()
        for p in model.parameters():p.requires_grad_(False)
        head=torch.nn.Linear(4096,3,bias=True,device='cuda:0',dtype=torch.float32)
        saved=torch.load(bound(reg['head_weights']),map_location='cpu',weights_only=True)
        require(set(saved)=={'weight','bias'} and tuple(saved['weight'].shape)==(3,4096) and tuple(saved['bias'].shape)==(3,)
            and all(v.dtype==torch.float32 and bool(torch.isfinite(v).all()) for v in saved.values()),'Exact final105 head2')
        head.load_state_dict(saved);head.requires_grad_(False);head.eval()
        _,inventory=helper._inventory(model,head,False,torch);require(inventory==trained['inventory'],'Actual resident/pipeline inventory')
        initial=helper._trainables(model,head,torch,io)
        require(io._same_state(initial['adapter_state_dict'],load_file(str(adapter),device='cpu'),torch)
            and io._same_state(initial['head_state_dict'],saved,torch),'All288+head2 loaded byte exact')
        completion=extract_stage(out,reg,ref(rp),entries,reader,model,head,helper,math105,io,torch,trace)
        require(helper._tree_equal(helper._trainables(model,head,torch,io),initial,torch) and canonical_frozen_hash(model,torch)==before,'Readonly pass changed model')
        helper._inventory(model,head,False,torch)
        for key in ('adapter_weights','head_weights','old_TIME','old_PAIR','old_CROP'):bound(reg[key])
        io._deadline(reg)
        save(out/'model_integrity.json',dict(status=INTEGRITY,completion=completion,registration=ref(rp),training_completion=reg['training_completion'],
            inventory=inventory,base_fingerprint=before,adapter_all288_exact=True,head_all2_exact=True,all_weights_frozen=True,
            no_training=True,targets_read=False,seconds=time.monotonic()-started,peak_allocated_mib=torch.cuda.max_memory_allocated()/2**20,
            peak_reserved_mib=torch.cuda.max_memory_reserved()/2**20))
    except BaseException as error:
        save(out/'failure.json',dict(utc=utc(),error=repr(error),traceback=traceback.format_exc(),attempted_model_calls=trace['attempted'],
            successful_raw=trace['raw'],preserve_all_success=True,automatic_retry=False,failure_is_not_empty=True,no_training=True,automatic_next_phase=False));raise


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--registration',type=Path,required=True)
    a=p.parse_args();run(a.root,a.registration)
