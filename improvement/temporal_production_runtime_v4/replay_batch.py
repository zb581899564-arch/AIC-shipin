"""Output-only independent CPU replay; input replay proof is reused, not rerun."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import traceback

import pr_contract as c
import pr_io as io
from output_checks import coordinate_binding,independent_endpoint_export,independent_verify,serialized_weights,strict_tokens


def terminal(protocol_path,batch_id):
    """Capture one real shared terminal/ledger into permanent evidence for input replay."""
    io.host(cpu=True);ctx=io.load(protocol_path,batch_id);store=ctx['store'];batch=ctx['batch']
    resource_path=io.RUN/'controller'/(batch['gpu_job_name']+'.resource.json')
    ledger_path=io.HOME/'improvement_round1/gpu_ledger.jsonl'
    resource_bytes=resource_path.read_bytes();ledger_bytes=ledger_path.read_bytes()
    receipt=json.loads(resource_bytes)
    ledger=[json.loads(line) for line in ledger_bytes.decode().splitlines() if line]
    matches=[row for row in ledger if row.get('name')==batch['gpu_job_name']]
    c.require(receipt['name']==batch['gpu_job_name'] and receipt['status']=='completed' and type(receipt['exit_code'])is int and
        receipt['exit_code']==0 and matches==[receipt] and receipt.get('validation_scope')!='PURE_SYNTHETIC_NOT_REAL_TERMINAL',
        'Unique actual naturally completed GPU resource/ledger required')
    gpu_pointer=io.read(ctx['root']/'gpu_completion_pointer.json')
    complete=io.read(store.checked_ref(gpu_pointer['completion_ref']))
    c.require(complete['status']=='PASS_COMPLETE_PRODUCTION_BATCH_NOT_QUALITY' and
        complete['gpu_job_name']==receipt['name'] and complete['actual_model_calls']==len(batch['request_ids']),
        'Natural terminal does not have complete successful actual batch output')
    base='permanent/proofs/runtime_v4/'+batch_id+'/terminal'
    def retain_original(relative,data):
        path=store.path(relative,'permanent');path.parent.mkdir(parents=True,exist_ok=True)
        with path.open('xb') as stream:stream.write(data);stream.flush();os.fsync(stream.fileno())
        return store.ref(relative)
    ref=retain_original(base+'/resource.json',resource_bytes)
    ledger_ref=retain_original(base+'/ledger.jsonl',ledger_bytes)
    c.require(ref['sha256']==hashlib.sha256(resource_bytes).hexdigest() and
        ledger_ref['sha256']==hashlib.sha256(ledger_bytes).hexdigest() and io.sha(resource_path)==ref['sha256'],
        'Byte-exact natural resource/complete ledger capture differs')
    origin_ref=store.write_metadata(base+'/origin_binding.json',dict(captured_utc=io.utc(),
        original_resource_path=str(resource_path),captured_resource_sha256=ref['sha256'],
        original_shared_ledger_path=str(ledger_path),captured_complete_ledger_sha256=ledger_ref['sha256'],
        resource_ref=ref,ledger_ref=ledger_ref,ledger_row_count=len(ledger),matched_job_row_count=len(matches),
        exact_original_bytes=True,subsequent_shared_ledger_appends_do_not_change_this_snapshot=True))
    io.save(ctx['root']/'terminal_pointer.json',dict(resource_ref=ref,ledger_ref=ledger_ref,
        original_resource_path=str(resource_path),original_resource_sha256=ref['sha256'],
        original_shared_ledger_path=str(ledger_path),original_shared_ledger_sha256=ledger_ref['sha256'],origin_binding_ref=origin_ref,
        batch_completion_ref=gpu_pointer['completion_ref'],new_model_calls=0))


def replay(protocol_path,batch_id):
    io.host(cpu=True);ctx=io.load(protocol_path,batch_id);accepted,CPU_ref=io.CPU_acceptance(ctx)
    store=ctx['store'];lib=ctx['lib'];batch=ctx['batch'];p=ctx['protocol']
    terminal_pointer=io.read(ctx['root']/'terminal_pointer.json')
    resource_ref=terminal_pointer['resource_ref'];ledger_ref=terminal_pointer['ledger_ref']
    resource=io.read(store.checked_ref(resource_ref));ledger=[json.loads(line) for line in store.checked_ref(ledger_ref).read_text().splitlines() if line]
    c.require(resource['name']==batch['gpu_job_name'] and resource['status']=='completed' and resource['exit_code']==0 and
        [row for row in ledger if row.get('name')==batch['gpu_job_name']]==[resource],
        'Permanent real natural batch terminal/unique ledger changed')
    complete_ref=terminal_pointer['batch_completion_ref'];complete=io.read(store.checked_ref(complete_ref))
    origin=io.read(store.checked_ref(terminal_pointer['origin_binding_ref']))
    c.require(origin['exact_original_bytes'] is True and origin['resource_ref']==resource_ref and origin['ledger_ref']==ledger_ref and
        origin['captured_resource_sha256']==resource_ref['sha256'] and origin['captured_complete_ledger_sha256']==ledger_ref['sha256'] and
        origin['matched_job_row_count']==1,'Original source path/SHA/UTC immutable terminal snapshot proof differs')
    c.require(complete['status']=='PASS_COMPLETE_PRODUCTION_BATCH_NOT_QUALITY' and complete['batch_id']==batch_id and
        complete['actual_model_calls']==len(batch['request_ids']) and complete['model_load_count']==1 and
        complete['protocol_sha256']==io.sha(ctx['protocol_path']) and complete['batch_sha256']==io.sha(ctx['batch_path']) and
        complete['global_graph_sha256']==p['full_plan_ref']['sha256'] and complete['CPU_admission_ref']==CPU_ref and
        [entry['consumer'] for entry in complete['entries']]==batch['request_ids'],'Complete actual GPU batch denominator/control binding differs')
    launch=io.read(store.checked_ref(complete['launch_ref']))
    c.require(launch['pid']!=os.getpid() and launch['GPU_admission_sha256']==io.sha(ctx['root']/'gpu_admission.json'),
              'Fresh independent output replay PID/admission required')
    checkpoint=io.read(store.checked_ref(complete['model_identity_ref']))
    weights=io.read(store.checked_ref(complete['weights_terminal_ref']))
    c.require(weights['initial_model_identity_ref']==complete['model_identity_ref'],'Terminal weight identity references another model load')
    names=serialized_weights(checkpoint,weights)
    journal=[json.loads(line) for line in store.checked_ref(complete['attempts_ref']).read_text().splitlines() if line]
    c.require(len(journal)==2*len(batch['request_ids']),'GPU journal actual call denominator differs')
    for ix,rid in enumerate(batch['request_ids'],1):
        pair=journal[2*(ix-1):2*ix]
        c.require([row['event'] for row in pair]==['BEGIN_MODEL_CALL','ACCEPTED_MODEL_CALL'] and
            all(row['call_id']==ix and row['consumer']==rid and row['batch_id']==batch_id for row in pair) and
            pair[1]['done_ref']==complete['entries'][ix-1]['done_ref'],'GPU BEGIN/raw/accepted call order/identity differs')
    code_sha=io.sha(__file__)
    c.require(store.policy['independent_replay_code_sha256']==code_sha and
        p['required_code_files'].get(str(Path(__file__).resolve()))==code_sha,
        'Actual output replay code SHA differs from pre-model permanent retention policy')
    base='permanent/proofs/runtime_v4/'+batch_id+'/output_replay'
    c.require(not store.path(base+'/launch.json','permanent').exists(),'Started/successful output replay cannot repeat automatically')
    store.write_metadata(base+'/launch.json',dict(verifier_pid=os.getpid(),verifier_code_sha256=code_sha,CPU_only=True,
        resource_ref=resource_ref,ledger_ref=ledger_ref,batch_completion_ref=complete_ref,
        new_processor_encodes=0,new_media_decodes=0,new_model_calls=0))
    current=None;proofs=[];outputs=[]
    try:
        # Original local tokenizer only; no vision processor, tensor encoder, media decoder or model loader.
        from transformers import AutoTokenizer
        config_path=io.RUN/'b_score_aligned_package_v4/config.json';config=io.read(config_path)
        c.require(io.sha(config_path)==p['original_B_config_sha256'],'Original config identity changed')
        model_dir=Path(config['model_dir'])
        tokenizer=AutoTokenizer.from_pretrained(model_dir,local_files_only=True)
        eos=io.read(model_dir/'generation_config.json')['eos_token_id'];eos=[eos] if isinstance(eos,int) else list(eos)
        asset_identity=next(iter(accepted.values()))['proof']['processor_runtime_identity']['processor_assets']
        for filename,digest in asset_identity.items():c.require(io.sha(filename)==digest,'Original tokenizer/processor asset changed')
        for entry in complete['entries']:
            current=entry['consumer'];CPU=accepted[current];meta=CPU['meta'];done=io.read(store.checked_ref(entry['done_ref']))
            raw=io.read(store.checked_ref(done['raw_ref']));request=io.read(store.checked_ref(done['request_ref']))
            GPU=io.read(store.checked_ref(done['gpu_input_ref']))
            for ref in (CPU['manifest']['private_ref'],CPU['manifest']['visual_ref']):
                if ref:store.checked_ref(ref) # Same permanent gzip bytes as successful independent input replay; no tensor re-encode.
            input_ref=store.ref('permanent/proofs/'+current+'_first_input_replay.json')
            inp=io.read(store.checked_ref(input_ref))
            c.require(inp['status']=='PASS_FIRST_INDEPENDENT_INPUT_REPLAY_ONLY_NOT_LEASE_ACCEPTANCE' and inp['consumer']==current and
                inp['prepare_pid']==CPU['proof']['prepare_pid'] and inp['prepare_pid']!=inp['verifier_pid'] and
                inp['prepare_pid']!=os.getpid() and inp['CPU_only'] is True and inp['normal_processor_from_original_RGB_verified'] is True and
                inp['first_independent_input_replay'] is True and inp['actual_first_independent_processor_encodes']==1 and
                inp['input_manifest_ref']==CPU['entry']['input_manifest_ref'] and inp['CPU_input_proof_ref']==CPU['entry']['CPU_input_proof_ref'] and
                inp['full_input_signature']==CPU['manifest']['full_signature'] and inp['input_evidence']==CPU['proof']['input_evidence'] and
                inp['original_RGB_ref']==CPU['proof']['original_RGB_ref'] and inp['resource_ref']==resource_ref and inp['ledger_ref']==ledger_ref and
                inp['new_model_calls']==inp['new_source_decodes']==0,
                'First independent original-RGB/normal-processor receipt missing or mismatched; never rerun it here')
            c.require(inp['verifier_code_sha256']==lib['input_reg']['required_code_files'][str(io.INPUT_ROOT/'code/replay_input.py')],
                      'Independent input verifier code is not the frozen input implementation')
            store.checked_ref(inp['original_RGB_ref'],'staging')
            c.require(CPU['proof']['processor_runtime_identity']['processor_assets']==asset_identity,'Consumer original tokenizer assets differ')
            role=p['endpoint_model_role'] if meta['kind']=='ENDPOINT' else 'TIME_ENABLED';disabled=role=='BASE_DISABLED'
            before=io.read(store.checked_ref(done['activation_before_ref']));inside=io.read(store.checked_ref(done['activation_inside_ref']))
            after=io.read(store.checked_ref(done['activation_after_ref']))
            c.serialized_state(before['layer_state'],False,names);c.serialized_state(inside['layer_state'],disabled,names)
            c.serialized_state(after['layer_state'],False,names)
            c.require(before['inventory']==inside['inventory']==after['inventory']==checkpoint['inventory'] and
                before['loaded_model_identity_ref']==inside['base_checkpoint_ref']==complete['model_identity_ref'] and
                before['role']==inside['role']==after['role']==role and after['all_144_states_restored'] is True and
                after['trainable_tensor_count']==0 and after['gradient_restoration']['trainable_tensor_count_after_restore']==0 and
                after['gradient_restoration']['trainable_parameters_after_restore']==0 and
                after['gradient_restoration']['action']=='MODEL_REQUIRES_GRAD_FALSE_AFTER_PEFT_CONTEXT' and
                before['weight_check_strategy']==after['weight_check_strategy']==c.WEIGHT_STRATEGY,
                'Actual per-call role/layer/frozen-gradient/inventory restoration proof differs')
            c.require(done['status']=='PASS_PRODUCTION_BATCH_DECISION_NOT_QUALITY' and done['consumer']==request['consumer']==raw['consumer']==current and
                request['prompt']==meta['prompt'] and request['finite_response_strings']==meta['finite_response_strings'] and
                request['coordinate_binding']==coordinate_binding(meta) and
                request['input_manifest_ref']==GPU['input_manifest_ref']==CPU['entry']['input_manifest_ref'] and
                request['CPU_input_proof_ref']==GPU['CPU_input_proof_ref']==CPU['entry']['CPU_input_proof_ref'] and
                request['gpu_input_ref']==raw['gpu_input_ref']==done['gpu_input_ref'] and raw['request_ref']==done['request_ref'] and
                raw['activation_inside_ref']==done['activation_inside_ref'] and request['activation_before_ref']==done['activation_before_ref'] and
                request['model_identity_ref']==GPU['loaded_model_identity_ref']==complete['model_identity_ref'] and
                request['reference_labels_read'] is False and request['past_key_values_supplied'] is False and request['prior_outputs_supplied_as_context'] is False and
                request['global_graph_sha256']==p['full_plan_ref']['sha256'] and request['batch_id']==batch_id and
                request['generation_arguments']==dict(do_sample=False,max_new_tokens=256,return_dict_in_generate=True,output_scores=True) and
                request['input_evidence']==raw['input_evidence']==done['input_evidence']==CPU['proof']['input_evidence'] and
                request['model_role']==raw['model_role']==done['model_role']==GPU['model_role']==role and
                GPU['full_input_signature']==GPU['GPU_input_signature']==CPU['manifest']['full_signature'] and
                GPU['actual_GPU_transfer'] is True and GPU['actual_weight_identity_verified'] is True and
                GPU['complete_dictionary_transferred'] is True and GPU['precision_conversion'] is False and GPU['cross_role_KV_reuse'] is False and
                raw['input_tokens']==CPU['proof']['input_tokens'] and raw['actual_physical_parameters']==c.PARAMETERS and
                raw['activated_parameters']==(c.BASE_PARAMETERS if disabled else c.PARAMETERS),
                'Actual GPU full input/raw/token/model/source/prompt binding differs')
            decision=strict_tokens(tokenizer,raw,tuple(meta['finite_response_strings']),eos)
            if meta['kind']=='ENDPOINT':
                native_meta=lib['input_contract'].native_boundary_request(meta)
                native=lib['independent_endpoint'](decision,native_meta,CPU['clock'])
                output=independent_endpoint_export(native,meta,CPU['clock'])
            else:output=independent_verify(meta,raw['raw_output'])
            c.require(decision==done['decision'] and output==done['output'],'Independent parser/native endpoint conversion differs')
            retained=dict(request=done['request_ref'],raw=done['raw_ref'],done=entry['done_ref'],CPU_input_proof=CPU['entry']['CPU_input_proof_ref'],
                GPU_input=done['gpu_input_ref'],first_independent_input_replay=input_ref,model_identity=complete['model_identity_ref'],
                weights_terminal=complete['weights_terminal_ref'],activation_before=done['activation_before_ref'],
                activation_inside=done['activation_inside_ref'],activation_after=done['activation_after_ref'],batch_completion=complete_ref,
                complete_global_request_source_lock=ctx['graph_ref'],natural_terminal_origin_binding=terminal_pointer['origin_binding_ref'])
            proof_ref=store.write_metadata(base+'/'+current+'.json',dict(schema='CACHE_FIRST_INDEPENDENT_REPLAY_ACCEPTANCE_V1',
                status='PASS_FIRST_INDEPENDENT_REPLAY',consumer=current,CPU_only=True,new_model_calls=0,first_independent_replay=True,
                prepare_pid=CPU['proof']['prepare_pid'],verifier_pid=os.getpid(),verifier_code_sha256=code_sha,
                first_input_verifier_pid=inp['verifier_pid'],first_input_verifier_code_sha256=inp['verifier_code_sha256'],
                input_manifest_ref=CPU['entry']['input_manifest_ref'],full_input_signature=CPU['manifest']['full_signature'],
                GPU_input_signature=GPU['GPU_input_signature'],normal_processor_from_original_RGB_verified=True,
                output_token_decode_grammar_parser_native_verified=True,actual_weight_identity_verified=True,
                original_RGB_ref=inp['original_RGB_ref'],gpu_job_name=batch['gpu_job_name'],retained_evidence_refs=retained,
                validation_scope='PRODUCTION_FIRST_INDEPENDENT_REPLAY',batch_id=batch_id,global_graph_sha256=p['full_plan_ref']['sha256'],
                model_role=role,native_output=output,new_processor_encodes=0,new_media_decodes=0))
            proofs.append(dict(consumer=current,proof_ref=proof_ref));outputs.append(dict(consumer=current,kind=meta['kind'],output=output,
                source_id=meta['source_id'],video_id=ctx['source_video_projection'][meta['source_id']]))
        expected_skips=[row for row in ctx['rows'] if row['execution']!='MODEL']
        c.require([item['request_id'] for item in complete['structural_skips']]==[row['request_id'] for row in expected_skips],
                  'Typed no64 structural denominator differs')
        for row,item in zip(expected_skips,complete['structural_skips']):
            c.require(item['actual_model_call'] is False and io.read(store.checked_ref(item['structural_result_ref']))==row['structural_endpoint_result'],
                      'Structural no64 request was altered or treated as a model call')
            outputs.append(dict(consumer=row['request_id'],kind='ENDPOINT',output=row['structural_endpoint_result'],
                source_id=row['source_id'],video_id=ctx['source_video_projection'][row['source_id']]))
        ref=store.write_metadata(base+'/completion.json',dict(status='PASS_COMPLETE_BATCH_OUTPUT_REPLAY_NOT_QUALITY',batch_id=batch_id,
            proofs=proofs,outputs=outputs,resource_ref=resource_ref,ledger_ref=ledger_ref,batch_completion_ref=complete_ref,
            global_graph_sha256=p['full_plan_ref']['sha256'],batch_sha256=io.sha(ctx['batch_path']),
            new_model_calls=0,new_processor_encodes=0,new_media_decodes=0,RGB_released=False,consumers_accepted=False))
        io.save(ctx['root']/'output_replay_pointer.json',dict(completion_ref=ref))
    except BaseException as error:
        store.write_metadata(base+'/failure.json',dict(status='FAILED_OUTPUT_REPLAY_RETAIN_ALL_NO_UNKNOWN_FALLBACK',consumer=current,
            successful_proofs=proofs,error=repr(error),traceback=traceback.format_exc(),new_model_calls=0,new_processor_encodes=0,new_media_decodes=0))
        raise


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=('terminal','replay'));parser.add_argument('--protocol',required=True,type=Path)
    parser.add_argument('--batch-id',required=True);args=parser.parse_args();os.environ['CUDA_VISIBLE_DEVICES']=''
    (terminal if args.stage=='terminal' else replay)(args.protocol,args.batch_id)
