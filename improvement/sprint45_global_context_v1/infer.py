"""Controller-invoked unique generation, then separate CPU-only output/native QA."""
from global_context_common import *
from prepare import load_case


def checked_registration(root, manifest):
    qa = read(root/'input_qa.json'); reg = read(root/'generation_registration.json')
    require(qa['status'] == 'PASS_ALL426_INDEPENDENT_GLOBAL_LOCAL_INPUT_QA' and
            qa['input_manifest_sha256'] == sha(root/'input_manifest.json') and
            qa['protocol_sha256'] == sha(root/'protocol.json'), 'First independent actual input QA gate')
    require(reg['schema'] == 'GLOBAL_LOCAL_BINARY_CONTEXT_GENERATION_REGISTRATION_V1' and
            reg['protocol_sha256'] == sha(root/'protocol.json') and
            reg['input_manifest_sha256'] == sha(root/'input_manifest.json') and
            reg['input_qa_sha256'] == sha(root/'input_qa.json'), 'Controller frozen generation registration')
    require(reg['unique_inputs'] == qa['unique_inputs'] == manifest['unique_inputs'] and
            reg['cases'] == qa['cases'] == manifest['cases'] and reg['sources'] == 426 and
            isinstance(reg['shared_gpu_job_name'],str) and reg['shared_gpu_job_name'] and
            0 < reg['stop_reserve_seconds'] < reg['budget_seconds'], 'Registered actual unique count/job/budget')
    return reg


def journal_counts(root):
    records = [json.loads(line) for line in (root/'journal.jsonl').read_text(encoding='utf-8').splitlines() if line.strip()] if (root/'journal.jsonl').exists() else []
    counts = {}
    for row in records:
        if row['stage'] in ('BEGIN','ACCEPTED'):
            key = row['effective_key']; pair = counts.setdefault(key,dict(BEGIN=0,ACCEPTED=0))
            pair[row['stage']] += 1
            require(pair[row['stage']] == 1, 'Duplicate actual generation BEGIN/ACCEPTED: '+key)
    return counts


def checked_output(root, case, grammar, tokenizer=None):
    import torch
    path = root/'outputs'/(case['effective_key']+'.pt')
    value = torch.load(path, map_location='cpu', weights_only=True)
    query = torch.load(case['query_path'], map_location='cpu', weights_only=True)
    require(value['effective_key'] == case['effective_key'] and value['canonical_case_id'] == case['canonical_case_id'] and
            value['query_sha256'] == case['query_sha256'] and
            value['actual_input_fingerprints'] == case['actual_input_fingerprints'], 'Actual output full input identity')
    seq = value['sequences']; prefix = query['input_ids'].shape[1]; k = len(case['targets'])
    require(seq.dtype == torch.int64 and seq.shape == (1,prefix+4*k) and
            torch.equal(seq[:,:prefix],query['input_ids']), 'Actual generation exact input prefix and complete length')
    tokens = seq[0,prefix:].tolist()
    require(len(value['selected_scores']) == len(tokens) and all(math.isfinite(v) for v in value['selected_scores']), 'Real complete generation selected scores')
    raw = value['raw']
    if tokenizer is not None:
        require(tokenizer.decode(tokens[:-1], skip_special_tokens=False, clean_up_tokenization_spaces=False) == raw, 'Independent exact raw decode')
    global_bits, payoff_bits = parse_output(tokens,k,grammar,raw)
    require(value['global_highlight'] == global_bits and value['event_payoff'] == payoff_bits, 'Saved actual binary masks')
    return value, binding(path)


def infer(root):
    import importlib
    import sys
    import torch
    from peft.tuners.tuners_utils import BaseTunerLayer
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '0', 'Shared GPU wrapper must declare only GPU0')
    root, protocol, sources = checked_protocol(root); manifest = checked_manifest(root)
    reg = checked_registration(root,manifest)
    require(not (root/'generation_completion.json').exists(), 'Successful full stage cannot be rerun')
    # Unique local phase lock supplements, never replaces, the controller shared GPU lock.
    import fcntl
    lock = (root/'infer.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    (root/'outputs').mkdir(exist_ok=True)
    inventory = journal_counts(root)
    cases = [load_case(c) for s in manifest['sources'] for c in s['cases']]
    uniques = [c for c in cases if c['unique_generation']]
    require(len(uniques) == manifest['unique_inputs'], 'Unique full actual inputs')
    for case in uniques:
        key = case['effective_key']; output = root/'outputs'/(key+'.pt')
        require(key not in inventory or output.exists(), 'Prior BEGIN without durable output blocks blind generation retry')
        require(not output.exists() or key in inventory, 'Saved output without actual BEGIN provenance')
    # global_context_common has a unique name; engine imports its own historical common.
    engine_dir = RUN/'b_score_aligned_package_v4'; sys.path.insert(0,str(engine_dir))
    require('common' not in sys.modules or Path(sys.modules['common'].__file__).resolve() == (engine_dir/'common.py').resolve(), 'Engine common namespace collision')
    engine = importlib.import_module('engine')
    require(Path(engine.__file__).resolve() == (engine_dir/'engine.py').resolve(), 'Original engine module identity')
    cfg = read(bound(protocol['frozen_model_config']))
    model, processor, identity = engine.load_model(cfg)
    require(identity['logical_parameters'] == cfg['complete_parameters'] == 8782459120 and
            8782459120+98329 == protocol['controls']['complete_reproduction_parameters'] <= 9_000_000_000,
            'Actual GPU physical inventory and complete baseline reproduction parameters')
    require(grammar_spec(processor.tokenizer) == manifest['grammar'], 'Actual inference tokenizer grammar identity')
    grammar = manifest['grammar']; flags = [(parameter,parameter.requires_grad) for parameter in model.parameters()]
    layers = [module for module in model.modules() if isinstance(module,BaseTunerLayer)]
    require(len(layers) == 144 and all(not layer.disable_adapters for layer in layers), 'Exact physical TIME inventory initially enabled')
    completed = []; new_calls = adopted = 0; cache = ChunkCache()
    try:
        with model.disable_adapter(),torch.inference_mode():
            require(all(layer.disable_adapters for layer in layers), 'BASE role disables exactly TIME144 inside context')
            for case in uniques:
                key = case['effective_key']; path = root/'outputs'/(key+'.pt')
                if path.exists():
                    value, ref = checked_output(root,case,grammar,processor.tokenizer); adopted += 1
                else:
                    query = torch.load(case['query_path'],map_location='cpu',weights_only=True)
                    composed = compose(case['images'],cache)
                    actual_key, fingerprints = effective_input({**query,**composed})
                    require(actual_key == key and fingerprints == case['actual_input_fingerprints'], 'Actual GPU input reconstructed byte-exactly')
                    prefix = query['input_ids'].shape[1]; k = len(case['targets'])
                    gpu = {name:value.to('cuda:0') for name,value in {**query,**composed}.items()}
                    def constraint(batch_id, token_ids):
                        require(batch_id == 0, 'Only generation batch1')
                        return allowed_tokens(len(token_ids)-prefix,k,grammar)
                    event(root,'BEGIN',effective_key=key,case_id=case['case_id'],registration_sha256=sha(root/'generation_registration.json'))
                    output = model.generate(**gpu,do_sample=False,num_beams=1,num_return_sequences=1,
                        max_new_tokens=4*k,min_new_tokens=0,use_cache=True,
                        prefix_allowed_tokens_fn=constraint,eos_token_id=grammar['eos'],pad_token_id=grammar['eos'],
                        forced_bos_token_id=None,forced_eos_token_id=None,return_dict_in_generate=True,output_scores=True)
                    torch.cuda.synchronize()
                    seq = output.sequences.detach().cpu(); tokens = seq[0,prefix:].tolist()
                    scores = [float(score[0,tokens[i]].detach().cpu()) for i,score in enumerate(output.scores) if i<len(tokens)]
                    raw = processor.tokenizer.decode(tokens[:-1],skip_special_tokens=False,clean_up_tokenization_spaces=False)
                    # Save real raw/tokens before admission; a format failure stays failure.
                    save_tensor(root/'outputs'/(key+'.attempt.pt'),dict(sequences=seq,
                        full_raw_including_eos=processor.tokenizer.decode(tokens,skip_special_tokens=False,clean_up_tokenization_spaces=False),
                        raw_without_final_token=raw,selected_scores=scores,actual_score_count=len(output.scores),
                        effective_key=key,canonical_case_id=case['case_id'],query_sha256=case['query_sha256'],
                        actual_input_fingerprints=fingerprints))
                    require(len(tokens)==len(output.scores),'Complete actual generation score count')
                    value = dict(effective_key=key,canonical_case_id=case['case_id'],query_sha256=case['query_sha256'],
                        actual_input_fingerprints=fingerprints,sequences=seq,raw=raw,selected_scores=scores,
                        global_highlight=[],event_payoff=[],started_registration_sha256=sha(root/'generation_registration.json'))
                    global_bits,payoff_bits = parse_output(tokens,k,grammar,raw)
                    value['global_highlight']=global_bits; value['event_payoff']=payoff_bits
                    save_tensor(path,value)
                    del gpu,composed,query,output
                    value,ref = checked_output(root,case,grammar,processor.tokenizer)
                    new_calls += 1
                counts = journal_counts(root)
                if not counts[key]['ACCEPTED']:
                    event(root,'ACCEPTED',effective_key=key,case_id=case['case_id'],output_sha256=ref['sha256'])
                record = dict(effective_key=key,canonical_case_id=case['case_id'],output=ref,
                    targets=len(case['targets']),global_highlight=value['global_highlight'],event_payoff=value['event_payoff'])
                receipt = root/'outputs'/(key+'.json')
                if receipt.exists(): require(read(receipt) == record, 'Existing output acceptance differs')
                else: write(receipt,record)
                completed.append(record)
    finally:
        # PEFT can change LoRA flags on disable_adapter exit. Restore before byte identity.
        for parameter,flag in flags: parameter.requires_grad_(flag)
    require(all(not layer.disable_adapters for layer in layers) and all(p.requires_grad == f for p,f in flags), 'TIME activation and exact parameter flags restored')
    require(engine.frozen_identity(model,cfg) == identity['base'] and engine.adapter_identity(model,cfg) == identity['adapter'], 'Actual complete frozen base/adapter bytes unchanged')
    counts = journal_counts(root)
    require(set(counts) == {c['effective_key'] for c in uniques} and
            all(v == dict(BEGIN=1,ACCEPTED=1) for v in counts.values()), 'Unique actual BEGIN/ACCEPTED inventory')
    write(root/'generation_completion.json',dict(status='PASS_ALL_UNIQUE_GLOBAL_LOCAL_GENERATIONS',utc=utc(),
        protocol_sha256=sha(root/'protocol.json'),input_manifest_sha256=sha(root/'input_manifest.json'),
        input_qa_sha256=sha(root/'input_qa.json'),registration_sha256=sha(root/'generation_registration.json'),
        sources=426,cases=manifest['cases'],unique_inputs=len(completed),aliases=manifest['aliases'],
        actual_unique_BEGIN=len(counts),actual_unique_ACCEPTED=len(counts),new_calls_this_invocation=new_calls,
        adopted_successes_this_invocation=adopted,outputs=completed,model_identity=identity,
        gpu_resident_parameters=8782459120,complete_reproduction_parameters=8782557449,
        all_parameter_flags_restored=True,new_image_processors=0,new_decoders=0,new_optimizer_updates=0,
        online_effect='UNKNOWN',failure_to_zero=False))
    fcntl.flock(lock,fcntl.LOCK_UN); lock.close()


def output_qa(root):
    import numpy as np
    from transformers import AutoTokenizer
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'Independent CPU-only output QA')
    root,protocol,sources = checked_protocol(root); manifest = checked_manifest(root)
    checked_registration(root,manifest)
    complete = read(root/'generation_completion.json')
    require(complete['status'] == 'PASS_ALL_UNIQUE_GLOBAL_LOCAL_GENERATIONS' and
            complete['input_manifest_sha256'] == sha(root/'input_manifest.json') and
            complete['registration_sha256'] == sha(root/'generation_registration.json') and
            complete['unique_inputs'] == manifest['unique_inputs'] and complete['cases'] == manifest['cases'], 'Actual complete unique generation binding')
    require(not (root/'output_acceptance.json').exists(), 'Successful output QA cannot be rerun')
    require(not (root/'masks').exists(), 'Partial mask export requires explicit engineering recovery')
    tokenizer = AutoTokenizer.from_pretrained(read(bound(protocol['frozen_model_config']))['model_dir'],local_files_only=True)
    require(grammar_spec(tokenizer) == manifest['grammar'], 'Independent output tokenizer grammar')
    counts = journal_counts(root)
    require(len(counts) == manifest['unique_inputs'] and all(v == dict(BEGIN=1,ACCEPTED=1) for v in counts.values()), 'Independent actual unique calls')
    unique_values = {}; unique_cases = {}; rows = []; cases_seen = targets_seen = 0; first4=[]
    for source,prepared in zip(sources,manifest['sources']):
        require(source['id'] == prepared['id'], 'Export source identity')
        refs,pts,groups = checked_source(source); global_mask=np.zeros(len(refs),dtype=np.bool_);payoff_mask=np.zeros(len(refs),dtype=np.bool_)
        assignments=[]; case_outputs=[]
        for entry in prepared['cases']:
            case=load_case(entry);key=case['effective_key']
            if case['unique_generation']:
                value,ref=checked_output(root,case,manifest['grammar'],tokenizer)
                require(key not in unique_values, 'Unique output accounted twice')
                unique_values[key]=(value,ref);unique_cases[key]=case
                require(read(root/'outputs'/(key+'.json'))['output']==ref, 'Actual accepted output SHA')
            require(key in unique_values, 'Alias must follow preregistered unique input')
            value,ref=unique_values[key];canonical=unique_cases[key]
            require(case['canonical_case_id'] == canonical['case_id'] and
                    case['actual_input_fingerprints'] == canonical['actual_input_fingerprints'] and
                    len(case['targets']) == len(canonical['targets']), 'Independent same full input alias proof')
            require(case['targets'] == [dict(target_index=j+1,cell_index=t['cell_index'],ordinal=refs[t['cell_index']]['ordinal'],
                    image_index=t['image_index'],exact_pts=refs[t['cell_index']]['exact_pts']) for j,t in enumerate(case['targets'])], 'Exact target native cell mapping')
            for j,target in enumerate(case['targets']):
                i=target['cell_index'];assignments.append(i)
                global_mask[i]=value['global_highlight'][j];payoff_mask[i]=value['event_payoff'][j]
            case_outputs.append(dict(case_id=case['case_id'],effective_key=key,canonical_case_id=canonical['case_id'],
                alias=not case['unique_generation'],same_input_proof=case['actual_input_fingerprints'],output=ref))
            cases_seen+=1;targets_seen+=len(case['targets'])
        require(assignments == list(range(len(refs))), 'Complete unique native cell assignments in source order')
        directory=root/'masks'/source['id'];directory.mkdir(parents=True,exist_ok=False)
        for name,value in [('global',global_mask),('payoff',payoff_mask)]:
            with (directory/(name+'.npy')).open('xb') as stream:np.save(stream,value,allow_pickle=False)
        rows.append(dict(id=source['id'],cells=len(refs),global_mask_path=str(directory/'global.npy'),
            payoff_mask_path=str(directory/'payoff.npy'),global_sha256=sha(directory/'global.npy'),payoff_sha256=sha(directory/'payoff.npy'),
            native_path=prepared['native_path'],native_sha256=prepared['native_sha256'],
            clock_path=prepared['clock_path'],clock_sha256=prepared['clock_sha256'],
            sample_ordinals=[r['ordinal'] for r in refs],case_output_bindings=case_outputs))
        if len(first4)<4:first4.append(dict(id=source['id'],cells=len(refs),all_native_cells_mapped=True,scope='ENGINEERING_ONLY_NO_EFFECT_EVALUATION'))
    require([s['id'] for s in rows] == IDS and len(unique_values) == manifest['unique_inputs'] and
            cases_seen == manifest['cases'] and targets_seen == manifest['targets'], 'Full426 masks/calls/cells denominator')
    require({r['effective_key'] for r in complete['outputs']} == set(unique_values) and
            all(r['output']==unique_values[r['effective_key']][1] for r in complete['outputs']), 'Generation completion actual output set/SHA')
    write(root/'output_acceptance.json',dict(status='PASS_ALL426_GLOBAL_LOCAL_BINARY_OUTPUT_QA',utc=utc(),
        sources=rows,cases=cases_seen,targets=targets_seen,unique_inputs=len(unique_values),aliases=manifest['aliases'],
        protocol_sha256=sha(root/'protocol.json'),input_manifest_sha256=sha(root/'input_manifest.json'),
        input_qa_sha256=sha(root/'input_qa.json'),generation_completion_sha256=sha(root/'generation_completion.json'),
        first4_source_engineering_only=first4,gpu_resident_parameters=8782459120,
        complete_reproduction_parameters=8782557449,new_forward_calls=0,new_image_processors=0,new_decoders=0,
        prior_native_npz_baseline_is_VERIFY40_46=True,current_package_baseline=protocol['current_baseline'],
        online_effect='UNKNOWN',independent_quality_experiment=False,all_zero_is_legal=True,failure_to_zero=False))


if __name__ == '__main__': run_phase({'infer':infer,'output-qa':output_qa})
