"""Same-input development ablation: TIME proposals, base-only new admission.

No encoder, downloader, preparation, training or old-model call is present.
Only one pre-registered adapter activation factor differs from prior strict
positive calls. All old successful inputs and their first QA are adopted.
"""
import argparse
import datetime as dt
from fractions import Fraction as F
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
import time
import traceback

HOME=Path('/home/inspur/aic_video_work')
CANDIDATE='BASE_ONLY_POSITIVE_ADMISSION_SAME_INPUT_PAIR'
ROLE='BASE_ONLY_FOR_NEW_ADMISSION_TIME_FOR_PROPOSALS'
PARAMETERS=8782459120
BASE_PARAMETERS=8767123696


def require(ok,message):
    if not ok: raise ValueError(message)


def load(path):
    return json.loads(Path(path).read_text(encoding='utf8'))


def modules(root):
    """Explicit frozen helpers, no duplicate old execution or dynamic fallback."""
    reg=load(root/'registration.json')
    code=Path(reg['prior_code_dir'])
    require(code==Path(reg['prior_root'])/'code','Exact successful positive helper namespace required')
    if str(code) not in sys.path:sys.path.insert(0,str(code))
    import positive_io as io
    import positive_runtime as prior
    import positive_contract as contract
    import positive_grammar as grammar
    import positive_metrics as metrics
    import positive_evaluate as evaluator
    for name,module in [('positive_io',io),('positive_runtime',prior),('positive_contract',contract),
                        ('positive_grammar',grammar),('positive_metrics',metrics),('positive_evaluate',evaluator)]:
        require(Path(module.__file__).resolve()==code/(name+'.py'),'Frozen module shadowed: '+name)
    return io,prior,contract,grammar,metrics,evaluator


def registration(root):
    io,prior,c,g,m,e=modules(root);reg=io.read(root/'registration.json')
    require(reg['status']=='REGISTERED_ADAPTER_ROLE_DEV10_SAME_INPUT_V1' and reg['group']=='dev' and
        reg['candidate']==CANDIDATE and reg['activation_role']==ROLE and reg['model_parameters']==PARAMETERS and
        reg['optimizer_updates']==0 and reg['reference_available_to_inference'] is False and
        reg['production_admitted'] is False and reg['fresh_confirmation_admitted'] is False,
        'Independent same-input adapter-role development-only authority required')
    require(root.is_relative_to(HOME) and Path(__file__).resolve().parent==root/'code','New independent code/root required')
    protocol=io.read(io.checked_ref(reg['protocol_ref']))
    prior_protocol=io.read(io.checked_ref(reg['prior_protocol_ref']))
    require(protocol['candidate']==CANDIDATE and protocol['single_factor']==ROLE and
        protocol['quality_gates']==prior_protocol['quality_gates'] and protocol['model_parameters']==PARAMETERS and
        protocol['actual_new_model_call_denominator']==10 and protocol['all_sources_previously_exposed'] is True and
        protocol['confirmation_requires_new_registration_and_unexposed_sources'] is True,
        'Only adapter activation may differ; old quality gates and exposure remain explicit')
    required=reg['required_files']
    for name,digest in required.items():io.checked(name,digest)
    for path in Path(__file__).parent.glob('*.py'):
        require(required.get(str(path))==io.sha(path),'Every new code file must be frozen')
    for path in Path(reg['prior_code_dir']).glob('*.py'):
        require(required.get(str(path))==io.sha(path),'All adopted frozen positive code must be locked')
    require(required.get(reg['protocol_ref']['path'])==reg['protocol_ref']['sha256'] and
        required.get(reg['activation_contract_ref']['path'])==reg['activation_contract_ref']['sha256'],
        'New protocol and proven adapter context semantics must be frozen')
    budget=reg['gpu_budget']
    require(budget['max_actual_calls']==10 and budget['max_seconds']==1200 and
        budget['gpu_job_name']=='recall_base_positive_admission_dev10_20261015_v1',
        'One bounded ten-call same-input development role')
    return reg,protocol,(io,prior,c,g,m,e)


def activation_contract(reg,io):
    p=io.checked_ref(reg['activation_contract_ref'])
    spec=importlib.util.spec_from_file_location('_adopted_role_activation_contract',p)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    require(module.PHYSICAL_PARAMETERS==PARAMETERS and module.BASE_PARAMETERS==BASE_PARAMETERS and module.LORA_LAYERS==144,
        'Exact existing 144-layer activation context contract required')
    return module


def adopted(root):
    reg,protocol,helpers=registration(root);io,pr,c,g,m,e=helpers
    old=Path(reg['prior_root']);oldreg,oldgate,oldgatep,values=pr.accepted(old,'dev')
    oldgpu=pr.completed(old,'dev',oldreg,oldgate,oldgatep,values)
    qa=io.read(io.checked_ref(reg['prior_input_QA_ref']));outqa=io.read(io.checked_ref(reg['prior_output_QA_ref']))
    oldcpu=io.read(old/'dev/POSITIVE/cpu_01/completion.json')
    require(len(values)==qa['calls']==oldgpu['calls']==outqa['calls']==oldcpu['expected_input_count']==10 and
        qa['status']==io.QA_STATUS and outqa['status']==io.REPLAY_STATUS and
        qa['CPU_only'] is True and qa['CUDA_initialized'] is False and
        outqa['CPU_only'] is True and outqa['CUDA_initialized'] is False,
        'All ten unchanged successful complete input/token first-QA and old paired outputs required')
    require(reg['prior_input_QA_ref']==oldgate['first_input_QA_ref'] and
        outqa['gpu_completion_ref']==io.ref(old/'dev/POSITIVE/gpu_01/completion.json'),
        'Actual first QA and successful control output binding differ')
    resource,digest=io.terminal(oldgate)
    require(outqa['resource_terminal_sha256']==digest,'Original complete output QA must bind the unique natural terminal')
    require([v[0]['case_id'] for v in values]==[p['case_id'] for p in qa['proofs']]==[p['case_id'] for p in outqa['proofs']],
        'Ten-case same-input ordered paired denominator changed')
    return reg,protocol,helpers,oldreg,values


def admit(root):
    reg,protocol,helpers,oldreg,values=adopted(root);io,pr,c,g,m,e=helpers;io.host(cpu=True)
    files=dict(io.read(Path(reg['prior_root'])/'source_lock_dev_POSITIVE.json')['files'])
    for name,digest in reg['required_files'].items():
        require(name not in files or files[name]==digest,'Frozen adopted closure digest conflict');files[name]=digest
    for path in [root/'registration.json',io.checked_ref(reg['protocol_ref']),io.checked_ref(reg['prior_input_QA_ref']),
                 io.checked_ref(reg['prior_output_QA_ref'])]:files[str(path)]=io.sha(path)
    io.save(root/'source_lock.json',dict(files=files,role=ROLE,adopted_first_input_QA=10,new_input_encoder_calls=0))
    io.save(root/'gpu_admission.json',dict(status='PASS_ROLE_SAME_INPUT_ADOPTED_QA_GPU_ADMISSION',group='dev',
        expected_input_count=10,registration_ref=io.ref(root/'registration.json'),source_lock_ref=io.ref(root/'source_lock.json'),
        first_input_QA_ref=reg['prior_input_QA_ref'],activation_role=ROLE,deadline=reg['deadline'],**reg['gpu_budget']))


def accepted(root):
    reg,protocol,helpers,oldreg,values=adopted(root);io,pr,c,g,m,e=helpers
    gate=io.read(root/'gpu_admission.json')
    require(gate['status']=='PASS_ROLE_SAME_INPUT_ADOPTED_QA_GPU_ADMISSION' and gate['activation_role']==ROLE and
        gate['expected_input_count']==10 and gate['registration_ref']==io.ref(root/'registration.json') and
        gate['first_input_QA_ref']==reg['prior_input_QA_ref'] and gate['source_lock_ref']==io.ref(root/'source_lock.json') and
        gate['gpu_job_name']==reg['gpu_budget']['gpu_job_name'], 'Explicit new role source/input/GPU binding differs')
    io.validate_lock(io.checked_ref(gate['source_lock_ref']),set(reg['required_files'])|{str(root/'registration.json')})
    return reg,protocol,helpers,oldreg,values,gate


def role_output(raw,done=None):
    ids,scores=raw['output_token_ids'],raw['selected_token_scores']
    require(0<len(ids)==len(scores)==raw['generated_score_count']==raw['output_tokens']<=256 and
        all(type(i) is int and i>=0 for i in ids) and all(type(s) in (int,float) and math.isfinite(s) for s in scores) and
        raw['adapter_disabled_layers']==[True]*144 and raw['actual_model_call'] is True and
        raw['actual_physical_parameters']==PARAMETERS and raw['activated_base_parameters']==BASE_PARAMETERS and
        raw['activation_role']==ROLE,'Actual new BASE output IDs/scores/activation evidence invalid')
    if done is not None:require(done['output_tokens']==len(ids),'Output denominator changed')
    return ids


def infer(root):
    reg,protocol,helpers,oldreg,values,gate=accepted(root);io,pr,c,g,m,e=helpers;io.host(cpu=False)
    legacy=io.legacy(oldreg);legacy.deadline(gate);legacy.gpu_reservation(gate)
    runtime=legacy.runtime_only();tm=io.tokens_module(oldreg);ac=activation_contract(reg,io)
    import torch
    out=root/'gpu_01';out.mkdir(exist_ok=False)
    io.save(out/'launch_claim.json',dict(pid=os.getpid(),utc=io.utc(),expected_input_count=10,admission_ref=io.ref(root/'gpu_admission.json'),
        adopted_first_input_QA=10,new_input_encoder_calls=0,activation_role=ROLE))
    with (out/'attempts.jsonl').open('x'):pass
    current=None;begun=0;entries=[]
    try:
        config=io.read(legacy.CONFIG);model,processor,identity=runtime.b_engine.load_model(config);legacy.verify_model(model,identity)
        inventory=ac.inventory(model);initial=ac.layer_state(model,False);names=initial['layer_names'];ac.frozen_gradients(model)
        io.save(out/'model_identity.json',dict(identity=identity,inventory=inventory,initial=initial,activation_role=ROLE,
            adapter_loaded_but_disabled_only_inside_admission=True,optimizer_updates=0))
        eos=legacy.eos_ids(model);candidates=g.candidate_tokens(processor.tokenizer,c.responses())
        for entry,req,_ in values:
            legacy.deadline(gate);current=entry['case_id'];folder=out/current;folder.mkdir(exist_ok=False)
            tokens=legacy.load_cache(req['token_cache_path']);original=legacy.load_cache(req['original_vision_cache_path'])
            encoded={**tokens,**{k:original[k] for k in tm.VISION_KEYS}};gpu={k:v.to('cuda') for k,v in encoded.items()}
            require(runtime.tensor_signature(encoded)==runtime.tensor_signature(gpu)==req['input_evidence']['tensor_signature'],
                'Adopted CPU/GPU actual bit signature changed')
            prefix=int(gpu['input_ids'].shape[1]);constraint=g.PositiveConstraint(processor.tokenizer,prefix,req,eos,candidates)
            io.save(folder/'request.json',dict(input_ref=entry['input_ref'],prompt=req['prompt'],input_evidence=req['input_evidence'],
                first_input_QA_ref=gate['first_input_QA_ref'],activation_role=ROLE,previous_outputs_supplied=False,past_key_values_supplied=False))
            before=dict(layer_state=ac.layer_state(model,False,names),gradients=ac.frozen_gradients(model));io.save(folder/'before.json',before)
            try:
                with model.disable_adapter():
                    inside=dict(layer_state=ac.layer_state(model,True,names),gradients=ac.frozen_gradients(model));io.save(folder/'inside.json',inside)
                    begun+=1;io.append(out/'attempts.jsonl',dict(event='BEGIN',case_id=current,call_id=begun,utc=io.utc()))
                    started=time.monotonic()
                    with torch.inference_mode():
                        generated=model.generate(**gpu,do_sample=False,max_new_tokens=256,prefix_allowed_tokens_fn=constraint,
                            return_dict_in_generate=True,output_scores=True)
                    torch.cuda.synchronize();ids=generated.sequences[0,prefix:]
                    text=processor.tokenizer.decode(ids,skip_special_tokens=True,clean_up_tokenization_spaces=False)
                    scores=[float(score[0,int(token)]) for score,token in zip(generated.scores,ids)]
                    io.save(folder/'raw.json',dict(raw_output=text,output_token_ids=ids.tolist(),selected_token_scores=[s if math.isfinite(s) else str(s) for s in scores],
                        generated_score_count=len(generated.scores),output_tokens=len(ids),input_tokens=prefix,generation_seconds=time.monotonic()-started,
                        actual_model_call=True,input_evidence=req['input_evidence'],eos_token_ids=eos,adapter_disabled_layers=inside['layer_state']['disable_adapters'],
                        actual_physical_parameters=PARAMETERS,activated_base_parameters=BASE_PARAMETERS,activation_role=ROLE))
                    ac.layer_state(model,True,names);ac.frozen_gradients(model)
            finally:
                # PEFT context re-enables adapter gradients; no optimizer exists.
                restored=ac.restore_frozen_gradients(model)
                after=dict(layer_state=ac.layer_state(model,False,names),gradients=ac.frozen_gradients(model))
                io.save(folder/'after.json',dict(after=after,restored=restored))
            raw=io.read(folder/'raw.json');role_output(raw);ac.validate_restoration(before,inside,after,restored,names)
            parsed=constraint.assert_complete(ids);require(json.dumps(parsed,separators=(',',':'))==text,'Untouched generated canonical grammar differs')
            decision=c.resolve(text,req,execution_status='MODEL_OK')
            io.save(folder/'done.json',dict(status='PASS_ROLE_ADMISSION_OUTPUT_NOT_QUALITY',case_id=current,group='dev',
                decision_result=decision,raw_ref=io.ref(folder/'raw.json'),request_ref=io.ref(folder/'request.json'),
                before_ref=io.ref(folder/'before.json'),inside_ref=io.ref(folder/'inside.json'),after_ref=io.ref(folder/'after.json'),
                input_evidence=req['input_evidence'],input_tokens=prefix,output_tokens=len(ids),activation_role=ROLE))
            receipt=dict(case_id=current,done_ref=io.ref(folder/'done.json'));entries.append(receipt)
            io.append(out/'attempts.jsonl',dict(event='ACCEPTED',call_id=begun,utc=io.utc(),**receipt))
            print(json.dumps(dict(stage='ROLE_BASE',complete=len(entries),expected=10,decision=decision['decision'])),flush=True)
            del encoded,gpu,original,tokens,generated,ids
        require(begun==len(entries)==10,'Complete unique ten-call development denominator required')
        require(runtime.b_engine.frozen_identity(model,config)==identity['base'] and runtime.b_engine.adapter_identity(model,config)==identity['adapter'],
            'Loaded base/adapter weights changed during activation-only calls')
        ac.inventory(model);ac.layer_state(model,False,names);ac.frozen_gradients(model)
        io.save(out/'completion.json',dict(status='PASS_ROLE_ALL10_MODEL_CALLS_NOT_QUALITY',calls=10,entries=entries,
            admission_ref=io.ref(root/'gpu_admission.json'),attempts_ref=io.ref(out/'attempts.jsonl'),model_identity_ref=io.ref(out/'model_identity.json'),
            model_parameters=PARAMETERS,activation_role=ROLE,new_optimizer_updates=0,new_input_encoder_calls=0))
    except BaseException as error:
        io.save(out/'failure.json',dict(current=current,begun=begun,successful_entries=entries,error=repr(error),traceback=traceback.format_exc(),no_automatic_retry=True));raise


def completed(root,io,gate):
    out=root/'gpu_01';gpu=io.read(out/'completion.json');journal=io.rows(io.checked_ref(gpu['attempts_ref']))
    require(gpu['status']=='PASS_ROLE_ALL10_MODEL_CALLS_NOT_QUALITY' and gpu['calls']==len(gpu['entries'])==10 and len(journal)==20 and
        gpu['admission_ref']==io.ref(root/'gpu_admission.json'),'Complete unique natural role output required')
    for i,row in enumerate(gpu['entries'],1):
        a,b=journal[2*(i-1):2*i]
        require(a['event']=='BEGIN' and b['event']=='ACCEPTED' and a['call_id']==b['call_id']==i and
            a['case_id']==b['case_id']==row['case_id'] and b['done_ref']==row['done_ref'],'Actual unique call journal mismatch')
    resource,sha=io.terminal(gate)
    return gpu,resource,sha


def qa(root):
    reg,protocol,helpers,oldreg,values,gate=accepted(root);io,pr,c,g,m,e=helpers;io.host(cpu=True)
    gpu,resource,resource_sha=completed(root,io,gate);ac=activation_contract(reg,io)
    legacy=io.legacy(oldreg);runtime,processor=legacy.cpu_processor()
    generation=io.read(Path(io.read(legacy.CONFIG)['model_dir'])/'generation_config.json');eos=generation['eos_token_id'];eos=[eos] if isinstance(eos,int) else list(eos)
    candidates=g.candidate_tokens(processor.tokenizer,c.responses());modelmeta=io.read(io.checked_ref(gpu['model_identity_ref']));legacy.verify_identity(modelmeta['identity'])
    names=modelmeta['initial']['layer_names'];ac.serialized_state(modelmeta['initial'],False,names)
    out=root/'output_qa_01';out.mkdir(exist_ok=False);proofs=[];events=[];current=None
    try:
        require([row['case_id'] for row in gpu['entries']]==[entry['case_id'] for entry,_,_ in values],'Same-input ordered paired output differs')
        for receipt,(entry,req,_) in zip(gpu['entries'],values):
            current=entry['case_id'];done=io.read(io.checked_ref(receipt['done_ref']));raw=io.read(io.checked_ref(done['raw_ref']));request=io.read(io.checked_ref(done['request_ref']))
            before=io.read(io.checked_ref(done['before_ref']));inside=io.read(io.checked_ref(done['inside_ref']));after_doc=io.read(io.checked_ref(done['after_ref']))
            ac.validate_restoration(before,inside,after_doc['after'],after_doc['restored'],names)
            require(done['case_id']==current and done['status']=='PASS_ROLE_ADMISSION_OUTPUT_NOT_QUALITY' and
                request['input_ref']==entry['input_ref'] and request['first_input_QA_ref']==reg['prior_input_QA_ref'] and
                request['prompt']==req['prompt']==c.prompt(req) and done['input_evidence']==raw['input_evidence']==request['input_evidence']==req['input_evidence'] and
                request['previous_outputs_supplied'] is False and request['past_key_values_supplied'] is False,
                'New actual output must bind unchanged prior first-QA input/prompt and independent prefill')
            ids=role_output(raw,done);require(raw['eos_token_ids']==eos and raw['input_tokens']==req['input_evidence']['input_tokens'],'Output input/EOS denominator differs')
            text=processor.tokenizer.decode(ids,skip_special_tokens=True,clean_up_tokenization_spaces=False);require(text==raw['raw_output'],'Independent token decode differs')
            constraint=g.PositiveConstraint(processor.tokenizer,raw['input_tokens'],req,eos,candidates);parsed=constraint.assert_complete(ids)
            require(json.dumps(parsed,separators=(',',':'))==text,'Independent exact complete finite grammar differs')
            decision,native=pr.independent_result(req,text);require(decision==done['decision_result'],'Independent native/parser decision differs')
            path=out/(current+'.json');io.save(path,dict(status='PASS_ROLE_INDEPENDENT_OUTPUT_QA',case_id=current,done_ref=receipt['done_ref'],
                raw_ref=done['raw_ref'],first_input_QA_ref=reg['prior_input_QA_ref'],activation_role=ROLE,CPU_only=True,CUDA_initialized=False,
                input_encoder_calls=0,new_model_calls=0,native_range=native,decision_result=decision));proofs.append(dict(case_id=current,proof_ref=io.ref(path)))
            events.append(dict(source_name=req['source_name'],case_id=current,original_interval_exact=req['original_interval_exact'],
                decision=decision['decision'],original_native_range=native))
        import torch
        require(not torch.cuda.is_initialized() and len(proofs)==10,'Full independent CPU output-only QA required')
        io.save(out/'completion.json',dict(status='PASS_ROLE_ALL10_OUTPUT_QA_NOT_QUALITY',calls=10,proofs=proofs,events=events,
            gpu_completion_ref=io.ref(root/'gpu_01/completion.json'),resource_terminal_sha256=resource_sha,CPU_only=True,CUDA_initialized=False,
            input_encoder_calls=0,prior_QA_repeated=0,new_model_calls=0))
    except BaseException as error:
        io.save(out/'failure.json',dict(current=current,successful_proofs=proofs,error=repr(error),traceback=traceback.format_exc(),no_automatic_retry=True));raise


def evaluate(root):
    reg,protocol,helpers,oldreg,values,gate=accepted(root);io,pr,c,g,m,e=helpers;io.host(cpu=True)
    gpu,resource,resource_sha=completed(root,io,gate);qa=io.read(root/'output_qa_01/completion.json')
    require(qa['status']=='PASS_ROLE_ALL10_OUTPUT_QA_NOT_QUALITY' and qa['calls']==len(qa['proofs'])==len(qa['events'])==10 and
        qa['resource_terminal_sha256']==resource_sha and qa['gpu_completion_ref']==io.ref(root/'gpu_01/completion.json'),
        'Complete independent new output QA before any development metric')
    oldresult=io.read(io.checked_ref(reg['prior_result_ref']));require(oldresult['group']=='dev' and len(oldresult['cases'])==4,'Full exposed dev control required')
    require([row['case_id'] for row in qa['proofs']]==[entry['case_id'] for entry,_,_ in values],'Complete independent QA order differs')
    allowed={entry['case_id']:req for entry,req,_ in values};cases=[];counts={};paired=[]
    oldout=io.read(Path(reg['prior_root'])/'dev/POSITIVE/verification_export.json')
    olddecisions={event['event_id']+'.positive':event['decision_result']['decision'] for event in oldout['events']}
    for event,qa_row,receipt in zip(qa['events'],qa['proofs'],gpu['entries']):
        req=allowed[event['case_id']];require(event['source_name']==req['source_name'] and event['original_interval_exact']==req['original_interval_exact'],
            'Evaluation cannot replace actual candidate/source/endpoints')
        proof=io.read(io.checked_ref(qa_row['proof_ref']));done=io.read(io.checked_ref(receipt['done_ref']))
        require(event['case_id']==qa_row['case_id']==receipt['case_id']==proof['case_id']==done['case_id'] and
            proof['done_ref']==receipt['done_ref'] and proof['decision_result']==done['decision_result'] and
            event['decision']==proof['decision_result']['decision'] and event['original_native_range']==proof['native_range'],
            'Metric export must equal actual independently checked model decision/native evidence')
        counts[event['decision']]=counts.get(event['decision'],0)+1
        paired.append(dict(case_id=event['case_id'],old_TIME=olddecisions[event['case_id']],new_BASE=event['decision']))
    for oldcase in oldresult['cases']:
        name=oldcase['video_id'];reference=io.read(io.checked_ref(oldcase['reference_ref']));clock=io.read(io.checked_ref(oldcase['clock_ref']))
        baseline=m.merged(oldcase['baseline_spans']);added=m.merged([x['original_interval_exact'] for x in qa['events'] if x['source_name']==name and x['decision']=='KEEP'])
        augmented=m.merged(baseline+added);raters=reference['annotator_intervals_exact_seconds']
        require(len(raters)==reference['annotator_count']>=2,'All original reference raters required')
        pairs=[(m.metrics(baseline,r),m.metrics(augmented,r)) for r in raters]
        average=lambda arm:{key:sum((pair[arm][key] for pair in pairs),F(0))/len(pairs) for key in ('f1','recall','precision')}
        oldaverage=average(0);require(all(str(value)==oldcase['baseline'][key]['exact'] for key,value in oldaverage.items()),'Protected full-source baseline differs from prior exact accepted arm')
        pts=list(map(F,clock['original_exact_pts']));oldframes=m.frames(baseline,pts);newframes=m.frames(augmented,pts)
        cases.append(dict(video_id=name,baseline=oldaverage,augmented=average(1),all_rater_recall_preserved=all(b['recall']>=a['recall'] for a,b in pairs),
            baseline_native_frames_preserved=oldframes<=newframes,added_native_frames=len(newframes-oldframes),
            baseline_spans=[[str(a),str(b)] for a,b in baseline],augmented_spans=[[str(a),str(b)] for a,b in augmented],reference_ref=oldcase['reference_ref'],clock_ref=oldcase['clock_ref']))
    conditions,macro=e.assess(cases,protocol['quality_gates']);passed=all(conditions.values())
    serialized=[{**case,**{arm:{key:dict(exact=str(value),value=float(value)) for key,value in case[arm].items()} for arm in ('baseline','augmented')}} for case in cases]
    status='PASS_ADAPTER_ROLE_DEV_PENDING_NEW_FRESH_CONFIRM' if passed else 'STOP_ADAPTER_ROLE_DEV_REJECTED'
    out=root/'comparison_01';out.mkdir(exist_ok=False)
    io.save(out/'result.json',dict(status=status,utc=io.utc(),group='dev',candidate=CANDIDATE,conditions=conditions,macro=macro,cases=serialized,
        new_decisions=counts,paired_decisions=paired,all_sources_previously_exposed=True,source_metrics_exposed_first_time=False,
        bindings=dict(protocol_ref=reg['protocol_ref'],registration_ref=io.ref(root/'registration.json'),output_QA_ref=io.ref(root/'output_qa_01/completion.json')),
        model_parameters=PARAMETERS,activated_new_admission_parameters=BASE_PARAMETERS,proxy_is_not_dense_highlight_or_ORDINARY_gold=True,
        actual_online_improvement='UNKNOWN',old_failed_gates_changed=False,production_admitted=False,fresh_confirmation_admitted=False))
    if passed:io.save(root/'selection_before_new_confirmation.json',dict(status='PASS_ROLE_DEV_FROZEN_REQUIRES_NEW_UNEXPOSED_CONFIRMATION',
        protocol_ref=reg['protocol_ref'],result_ref=io.ref(out/'result.json'),new_confirm_metrics_examined=False,production_admitted=False))
    print(json.dumps(dict(status=status,conditions=conditions,macro=macro,new_decisions=counts)),flush=True)
    return 0 if passed else 5


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=('admit','infer','qa','evaluate'))
    parser.add_argument('--root',type=Path,required=True);args=parser.parse_args()
    if args.action!='infer':os.environ['CUDA_VISIBLE_DEVICES']=''
    result=globals()[args.action](args.root.resolve());sys.exit(result or 0)
