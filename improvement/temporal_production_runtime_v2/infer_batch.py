"""One admitted capacity batch, one shared GPU job, one original B load."""
import argparse
from contextlib import nullcontext
import datetime as dt
import json
import math
import os
from pathlib import Path
import time
import traceback

import pr_contract as c
import pr_io as io


def deadline(protocol):
    c.require(dt.datetime.now(dt.timezone.utc)<dt.datetime.fromisoformat(protocol['deadline'].replace('Z','+00:00')),
              'Frozen production deadline passed; no new model call')


def infer(protocol_path,batch_id):
    io.host(cpu=False);ctx=io.load(protocol_path,batch_id)
    accepted,CPU_ref=io.CPU_acceptance(ctx);lib=ctx['lib'];store=ctx['store'];batch=ctx['batch'];p=ctx['protocol']
    deadline(p)
    runtime,runtime_files=lib['oldio'].legacy_runtime()
    for value in accepted.values():
        c.require(runtime_files==value['proof']['processor_runtime_identity']['runtime_files'],'Frozen original B runtime differs')
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    c.require(io.read(io.HOME/'improvement_round1/active_gpu_job.json')['name']==batch['gpu_job_name'],
              'Wrong active unique shared GPU reservation')
    prefix='permanent/proofs/runtime_v2/'+batch_id+'/gpu'
    journal=store.path(prefix+'/attempts.jsonl','permanent')
    c.require(not journal.exists() and not store.path(prefix+'/launch.json','permanent').exists(),
              'Started/successful batch cannot repeat; retain raw/failure and require explicit new recovery')
    journal.parent.mkdir(parents=True,exist_ok=True)
    with journal.open('x'):pass
    launch_ref=store.write_metadata(prefix+'/launch.json',dict(batch_id=batch_id,pid=os.getpid(),utc=io.utc(),
        protocol_path=str(ctx['protocol_path']),protocol_sha256=io.sha(ctx['protocol_path']),batch_sha256=io.sha(ctx['batch_path']),
        GPU_admission_sha256=io.sha(ctx['root']/'gpu_admission.json'),batch_CPU_admission_ref=CPU_ref,
        global_graph_sha256=p['full_plan_ref']['sha256'],actual_model_call_budget=len(batch['request_ids']),
        one_model_load_intended=True,new_input_processor_encodes=0,new_media_decodes=0,optimizer_updates=0))
    begun=0;entries=[];skips=[];current=None
    try:
        import torch
        config=io.read(io.RUN/'b_score_aligned_package_v4/config.json')
        c.require(io.sha(io.RUN/'b_score_aligned_package_v4/config.json')==p['original_B_config_sha256'],'Original B config changed')
        model,processor,identity=runtime.b_engine.load_model(config)
        lib['oldio'].verify_model(model,identity)
        model.requires_grad_(False)
        initial_state=c.layer_state(model,False);initial_inventory=c.inventory(model)
        model_ref=store.write_metadata(prefix+'/model_identity.json',dict(identity=identity,inventory=initial_inventory,
            initial_layer_state=initial_state,model_load_count=1,weight_check_strategy=c.WEIGHT_STRATEGY,
            original_B_config_sha256=p['original_B_config_sha256'],optimizer_updates=0))
        eos=model.generation_config.eos_token_id;eos=[eos] if isinstance(eos,int) else list(eos)
        strings=tuple(sorted({s for value in accepted.values() for s in value['meta']['finite_response_strings']}))
        boundary_candidates=lib['boundary_grammar'].candidates(processor.tokenizer,strings)
        verify_candidates=lib['verify_grammar'].candidate_tokens(processor.tokenizer,strings)
        for row in ctx['rows']:
            current=row['request_id'];folder=prefix+'/'+current
            if row['execution']!='MODEL':
                # Pre-model no64 is a typed request outcome, never a fake BEGIN/raw model call.
                structural_ref=store.ref('permanent/proofs/'+current+'_structural_unknown.json')
                c.require(io.read(store.checked_ref(structural_ref))==row['structural_endpoint_result'],
                          'Predeclared structural endpoint UNKNOWN changed')
                skips.append(dict(request_id=current,structural_result_ref=structural_ref,actual_model_call=False))
                continue
            deadline(p)
            CPU=accepted[current]
            gpu,meta,gpu_proof=lib['consumer'].gpu_input(lib['input_reg'],current,'cuda')
            c.require(gpu_proof['input_manifest_ref']==CPU['entry']['input_manifest_ref'] and
                gpu_proof['CPU_input_proof_ref']==CPU['entry']['CPU_input_proof_ref'] and
                gpu_proof['GPU_input_signature']==CPU['manifest']['full_signature'] and meta==CPU['meta'],
                'Actual GPU dict/CPU/source/request identity changed')
            role=p['endpoint_model_role'] if row['kind']=='ENDPOINT' else 'TIME_ENABLED'
            c.require(gpu_proof['model_role']==role,'Role changed after frozen development selection')
            disabled=role=='BASE_DISABLED';before=c.layer_state(model,False,initial_state['layer_names']);before_inventory=c.inventory(model)
            before_ref=store.write_metadata(folder+'/activation_before.json',dict(layer_state=before,inventory=before_inventory,
                role=role,loaded_model_identity_ref=model_ref,weight_check_strategy=c.WEIGHT_STRATEGY,trainable_tensor_count=0))
            gpu_proof.update(actual_weight_identity_verified=True,loaded_model_identity_ref=model_ref,activation_before_ref=before_ref,
                weight_check_strategy=c.WEIGHT_STRATEGY,actual_physical_parameters=c.PARAMETERS)
            gpu_ref=store.write_metadata(folder+'/gpu_input.json',gpu_proof)
            request_ref=store.write_metadata(folder+'/request.json',dict(consumer=current,event_id=meta['event_id'],kind=meta['kind'],
                original_case_id=meta['original_case_id'],original_segment_index=meta['original_segment_index'],
                original_interval_exact=meta['original_interval_exact'],prompt=meta['prompt'],
                finite_response_strings=meta['finite_response_strings'],input_manifest_ref=CPU['entry']['input_manifest_ref'],
                CPU_input_proof_ref=CPU['entry']['CPU_input_proof_ref'],input_evidence=CPU['proof']['input_evidence'],
                gpu_input_ref=gpu_ref,activation_before_ref=before_ref,model_identity_ref=model_ref,
                model_role=role,global_graph_sha256=p['full_plan_ref']['sha256'],batch_id=batch_id,
                generation_arguments=dict(do_sample=False,max_new_tokens=256,return_dict_in_generate=True,output_scores=True),
                reference_labels_read=False,past_key_values_supplied=False,prior_outputs_supplied_as_context=False))
            tokens=int(gpu['input_ids'].shape[1])
            c.require(tokens==CPU['proof']['input_tokens'] and tokens<=16384,'Actual prompt token budget differs')
            grammar=(lib['boundary_grammar'].BoundaryConstraint(processor.tokenizer,tokens,meta,eos,boundary_candidates)
                     if row['kind']=='ENDPOINT' else lib['verify_grammar'].VerifyConstraint(processor.tokenizer,tokens,meta,eos,verify_candidates))
            try:
                with model.disable_adapter() if disabled else nullcontext():
                    inside=c.layer_state(model,disabled,initial_state['layer_names']);inside_inventory=c.inventory(model)
                    inside_ref=store.write_metadata(folder+'/activation_inside.json',dict(layer_state=inside,inventory=inside_inventory,
                        role=role,base_checkpoint_ref=model_ref,adapter_unloaded=False))
                    c.require(begun<len(batch['request_ids']),'Frozen actual batch model budget exceeded')
                    begun+=1
                    io.append(journal,dict(event='BEGIN_MODEL_CALL',call_id=begun,consumer=current,batch_id=batch_id,utc=io.utc()))
                    started=time.monotonic()
                    with torch.inference_mode():
                        generated=model.generate(**gpu,do_sample=False,max_new_tokens=256,prefix_allowed_tokens_fn=grammar,
                            return_dict_in_generate=True,output_scores=True)
                    torch.cuda.synchronize();ids=generated.sequences[0,tokens:]
                    text=processor.tokenizer.decode(ids,skip_special_tokens=True,clean_up_tokenization_spaces=False)
                    scores=[float(score[0,int(token)]) for score,token in zip(generated.scores,ids)]
                    raw_ref=store.write_metadata(folder+'/raw.json',dict(consumer=current,actual_model_call=True,raw_output=text,
                        output_token_ids=ids.tolist(),selected_token_scores=[s if math.isfinite(s) else str(s) for s in scores],
                        generated_score_count=len(generated.scores),input_tokens=tokens,output_tokens=len(ids),
                        generation_seconds=time.monotonic()-started,eos_token_ids=eos,constraint_stats=grammar.stats,
                        input_evidence=CPU['proof']['input_evidence'],request_ref=request_ref,gpu_input_ref=gpu_ref,
                        activation_inside_ref=inside_ref,model_role=role,actual_physical_parameters=c.PARAMETERS,
                        activated_parameters=c.BASE_PARAMETERS if disabled else c.PARAMETERS))
                    c.layer_state(model,disabled,initial_state['layer_names'])
            finally:
                gradients=c.restore_gradients(model)
                after=c.layer_state(model,False,initial_state['layer_names']);after_inventory=c.inventory(model)
                after_ref=store.write_metadata(folder+'/activation_after.json',dict(layer_state=after,inventory=after_inventory,
                    gradient_restoration=gradients,role=role,weight_check_strategy=c.WEIGHT_STRATEGY,
                    all_144_states_restored=True,trainable_tensor_count=0))
            c.require(0<len(ids)<=256 and len(scores)==len(ids) and all(map(math.isfinite,scores)),
                      'Output token/finite score denominator failed; keep raw and block')
            decision=grammar.assert_complete(ids)
            c.require(json.dumps(decision,separators=(',',':'))==text,'Actual generated tokens/raw/parser decision differ')
            output=(lib['frozen']['boundary'].resolve_endpoint(decision,meta) if row['kind']=='ENDPOINT' else
                    lib['frozen']['verify'].resolve(text,meta,execution_status='MODEL_OK'))
            done_ref=store.write_metadata(folder+'/done.json',dict(status='PASS_PRODUCTION_BATCH_DECISION_NOT_QUALITY',consumer=current,
                event_id=meta['event_id'],kind=meta['kind'],decision=decision,output=output,raw_ref=raw_ref,request_ref=request_ref,
                gpu_input_ref=gpu_ref,activation_before_ref=before_ref,activation_inside_ref=inside_ref,activation_after_ref=after_ref,
                input_evidence=CPU['proof']['input_evidence'],model_role=role,optimizer_updates=0))
            io.append(journal,dict(event='ACCEPTED_MODEL_CALL',call_id=begun,consumer=current,done_ref=done_ref,batch_id=batch_id,utc=io.utc()))
            entries.append(dict(consumer=current,done_ref=done_ref))
            print(json.dumps(dict(batch_id=batch_id,accepted_calls=len(entries),actual_budget=len(batch['request_ids']),consumer=current)),flush=True)
            del gpu,generated,ids
        c.require(begun==len(entries)==len(batch['request_ids']),'Complete actual batch model denominator failed')
        model.requires_grad_(False);final_state=c.layer_state(model,False,initial_state['layer_names']);final_inventory=c.inventory(model)
        final_weights=dict(base=runtime.b_engine.frozen_identity(model,config),adapter=runtime.b_engine.adapter_identity(model,config))
        c.require(final_weights==dict(base=identity['base'],adapter=identity['adapter']),'Frozen full base/288 adapter changed at batch end')
        final_ref=store.write_metadata(prefix+'/weights_terminal.json',dict(identity=final_weights,inventory=final_inventory,
            layer_state=final_state,initial_model_identity_ref=model_ref,full_base_and_288_adapter_rechecked=True,
            weight_check_strategy=c.WEIGHT_STRATEGY,model_load_count=1,optimizer_updates=0))
        complete_ref=store.write_metadata(prefix+'/completion.json',dict(status='PASS_COMPLETE_PRODUCTION_BATCH_NOT_QUALITY',batch_id=batch_id,
            actual_model_calls=begun,entries=entries,structural_skips=skips,model_identity_ref=model_ref,weights_terminal_ref=final_ref,
            attempts_ref=store.ref(prefix+'/attempts.jsonl'),launch_ref=launch_ref,CPU_admission_ref=CPU_ref,
            protocol_sha256=io.sha(ctx['protocol_path']),batch_sha256=io.sha(ctx['batch_path']),global_graph_sha256=p['full_plan_ref']['sha256'],
            gpu_job_name=batch['gpu_job_name'],model_load_count=1,new_input_processor_encodes=0,new_media_decodes=0,optimizer_updates=0))
        io.save(ctx['root']/'gpu_completion_pointer.json',dict(completion_ref=complete_ref,actual_model_calls=begun))
    except BaseException as error:
        store.write_metadata(prefix+'/failure.json',dict(status='FAILED_BATCH_RETAIN_RAW_NO_UNKNOWN_FALLBACK',batch_id=batch_id,
            consumer=current,actual_started_model_calls=begun,successful_entries=entries,error=repr(error),traceback=traceback.format_exc(),
            optimizer_updates=0,old_successful_outputs_modified=False,new_media_decodes=0,new_input_processor_encodes=0))
        raise


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--protocol',required=True,type=Path);parser.add_argument('--batch-id',required=True)
    args=parser.parse_args();infer(args.protocol,args.batch_id)
