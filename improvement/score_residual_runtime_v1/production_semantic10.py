"""CONDITIONAL semantic09 production: prepare/qa/infer; never a launcher.

Requires a frozen actual semantic OOF PASS and production registration. Reuses
production_prepare's accepted CPU image tensors; no image processor or decoder.
Saved per-batch forwards are immutable and adopted on an explicitly launched
continuation, never silently recomputed. No reference labels are accessed.
"""
import sys
from fractions import Fraction
from common_runtime import *
from semantic09 import QUESTION

QUERY = ROOT / 'query09'
IDS = {str(i) for i in range(426)}
FINAL_STATUS = 'PASS_FIXED_SEMANTIC_OOF_EXPLORATION_FINAL25_NO_POSTFIT_REFERENCE'


def checked_registration():
    reg = read(ROOT/'production_registration.json')
    ref = reg['external_result']
    require(sha(ref['path']) == ref['sha256'], 'Frozen actual external result changed')
    quality = read(ref['path'])
    require(quality['status'] == FINAL_STATUS and quality['new_production_allowed'] is True,
            'Actual semantic OOF/final25 gate required; conditional code is not permission')
    require(reg['selected_view'] == quality['selected_view'] in ('D4', 'LM'), 'Frozen semantic view')
    head = reg['selected_head']
    require(head['sha256'] == quality['weights_sha256'] and sha(head['path']) == head['sha256'], 'Actual final25 weights')
    expected_dim = 4 if reg['selected_view'] == 'D4' else 12289
    expected_head_parameters = expected_dim*8+8+8+1
    require(reg['feature_dimension'] == expected_dim and quality['head_parameters'] == expected_head_parameters and
            reg['actual_resident_parameters'] == quality['resident_parameters'] == 8782459120+expected_head_parameters <= 9_000_000_000,
            'Selected feature/physical parameter registration')
    require(sha(reg['baseline']['path']) == '86593725c6bad919dc0d342fe98ad65e489a13a6e492da5de3afd247a3226543', 'Protected VERIFY40.46 changed')
    return reg


def checked_cpu():
    accepted = read(ROOT/'cpu_acceptance.json')
    require(accepted['status'] == 'PASS_ALL_REGISTERED_NEW_FEATURE_INPUTS' and
            accepted['protocol_sha256'] == sha(ROOT/'protocol.json'), 'All426 real CPU input gate')
    sources = accepted['sources']
    require(len(sources) == 426 and {s['id'] for s in sources} == IDS, 'Exactly one source per426 ID')
    for source in sources:
        sid = source['id']; directory = ROOT/'inputs'/sid
        require(read(directory/'acceptance.json') == source and source['status'] == 'PASS_FIRST_NEW_IMAGE_CPU_INPUTS', 'Actual source CPU receipt')
        require(sha(directory/'native.npz') == source['native_sha256'] and sha(directory/'clock.json') == source['clock_sha256'], 'Frozen native/clock identity')
        observed = [i for c in source['chunks'] for i in c['samples']]
        require(len(observed) == source['feature_cells'] > 0 and observed == sorted(set(observed)), 'Ordered unique native target cells')
    require(sum(s['feature_cells'] for s in sources) == accepted['total_cells'], 'Full CPU target denominator')
    return accepted


def exact_texts(processor, pts, chunk):
    """Identical semantic09 question, native frame order and placeholder recipe."""
    k = len(chunk['samples']); grids = chunk['grid']; texts = []
    require(1 <= k <= 8 and len(grids) == k, 'Original image chunk/query mapping')
    for target in range(k):
        content = [dict(type='text', text=QUESTION+'These are ordered frames from a short silent sequence.\n')]
        for j, ordinal in enumerate(chunk['samples']):
            content.extend([dict(type='text', text='Frame %d, relative time %.3fs.\n' %
                                 (j+1, float(pts[ordinal]-pts[chunk['samples'][0]]))), dict(type='image')])
        content.append(dict(type='text', text='Does frame %d depict a visual highlight in this context? Answer exactly Yes or No.' % (target+1)))
        text = processor.apply_chat_template([dict(role='user', content=content)], tokenize=False, add_generation_prompt=True, enable_thinking=False)
        require(text.count('<|image_pad|>') == k, 'Native image placeholders')
        for grid in grids:
            require(len(grid) == 3 and grid[0] == 1 and all(type(x) is int and x > 0 for x in grid) and grid[1]*grid[2] % 4 == 0, 'Actual Qwen image merge grid')
            text = text.replace('<|image_pad|>', '<|placeholder|>'*(grid[0]*grid[1]*grid[2]//4), 1)
        texts.append(text.replace('<|placeholder|>', '<|image_pad|>'))
    return texts


def save_once_tensor(path, values):
    import torch
    with Path(path).open('xb') as handle:
        torch.save(values, handle)
        handle.flush(); os.fsync(handle.fileno())


def prepare():
    import torch
    from transformers import AutoProcessor
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU text-only preparation')
    checked_registration(); accepted = checked_cpu(); QUERY.mkdir(exist_ok=True)
    # No image_processor is invoked; only native template/tokenizer calls.
    processor = AutoProcessor.from_pretrained(read(RUN/'b_score_aligned_package_v4/config.json')['model_dir'], local_files_only=True)
    processor.tokenizer.padding_side = 'left'
    token_ids = {word: processor.tokenizer.encode(word, add_special_tokens=False) for word in ('Yes', 'No')}
    require(all(len(v) == 1 for v in token_ids.values()), 'Frozen single-token Yes/No')
    sources = []; image_id = processor.tokenizer.convert_tokens_to_ids('<|image_pad|>')
    for source in accepted['sources']:
        sid = source['id']; directory = QUERY/sid; directory.mkdir(exist_ok=True)
        pts = [Fraction(x) for x in read(ROOT/'inputs'/sid/'clock.json')['normalized_exact_pts']]
        cases = []
        for ci, chunk in enumerate(source['chunks']):
            require(sha(chunk['path']) == chunk['sha256'], 'Adopted original image cache changed')
            texts = exact_texts(processor, pts, chunk)
            encoded = processor.tokenizer(texts, return_tensors='pt', padding=True, add_special_tokens=False)
            encoded = {key: encoded[key].contiguous() for key in ('input_ids', 'attention_mask')}
            expected = sum(g[0]*g[1]*g[2]//4 for g in chunk['grid'])
            require(encoded['input_ids'].shape[1] <= 4096 and bool(((encoded['input_ids'] == image_id).sum(1) == expected).all()), 'Actual query token/image budget')
            path = directory/('query_%04d.pt' % ci)
            if path.exists():
                old = torch.load(path, map_location='cpu', weights_only=True)
                require(set(old) == set(encoded) and all(torch.equal(old[k], encoded[k]) for k in old), 'Existing serialized tokens differ; never overwrite')
            else:
                save_once_tensor(path, encoded)
            cases.append(dict(query_path=str(path), query_sha256=sha(path), original_image_chunk=chunk,
                              queries=len(texts), text_sha256=[hashlib.sha256(t.encode()).hexdigest() for t in texts]))
        receipt = dict(id=sid, feature_cells=source['feature_cells'], cases=cases,
                       native_sha256=source['native_sha256'], clock_sha256=source['clock_sha256'],
                       source_CPU_acceptance_sha256=sha(ROOT/'inputs'/sid/'acceptance.json'))
        path = directory/'acceptance.json'
        if path.exists(): require(read(path) == receipt, 'Saved query source receipt differs')
        else: write(path, receipt)
        sources.append(receipt)
    result = dict(status='PASS_ALL426_NEW_SEMANTIC_TEXT_INPUTS', sources=sources,
                  readout_token_ids={k:v[0] for k,v in token_ids.items()}, original_unique_images=accepted['total_cells'],
                  original_CPU_acceptance_sha256=sha(ROOT/'cpu_acceptance.json'),
                  registration_sha256=sha(ROOT/'production_registration.json'), new_vision_processors=0, new_decodes=0, labels_read=False)
    path = QUERY/'cpu_acceptance.json'
    if path.exists(): require(read(path) == result, 'Frozen text input manifest changed')
    else: write(path, result)


def checked_queries():
    checked_registration(); checked_cpu()
    accepted = read(QUERY/'cpu_acceptance.json')
    require(accepted['status'] == 'PASS_ALL426_NEW_SEMANTIC_TEXT_INPUTS' and len(accepted['sources']) == 426 and
            {s['id'] for s in accepted['sources']} == IDS, 'Complete426 text gate')
    require(accepted['original_CPU_acceptance_sha256'] == sha(ROOT/'cpu_acceptance.json') and
            accepted['registration_sha256'] == sha(ROOT/'production_registration.json'), 'Query root binding changed')
    for source in accepted['sources']:
        require(read(QUERY/source['id']/'acceptance.json') == source, 'Query source manifest changed')
    return accepted


def qa():
    """Independent token-level QA over the serialized material, no processor."""
    import torch
    from transformers import AutoTokenizer
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'Independent CPU text QA')
    accepted = checked_queries(); manifest_sha = sha(QUERY/'cpu_acceptance.json')
    receipt_path = QUERY/'independent_text_QA.json'
    if receipt_path.exists():
        proof = read(receipt_path)
        require(proof['status'] == 'PASS_ALL426_SERIALIZED_SEMANTIC_TEXT_QA' and proof['query_manifest_sha256'] == manifest_sha, 'Prior successful QA binding')
        # Successful QA is adopted; infer still verifies actual token-file SHA.
        return
    tokenizer = AutoTokenizer.from_pretrained(read(RUN/'b_score_aligned_package_v4/config.json')['model_dir'], local_files_only=True)
    image_id = tokenizer.convert_tokens_to_ids('<|image_pad|>'); batches = queries = 0
    require(all(tokenizer.encode(word,add_special_tokens=False) == [accepted['readout_token_ids'][word]] for word in ('Yes','No')), 'Independent exact Yes/No readout token identity')
    for source in accepted['sources']:
        pts = [Fraction(x) for x in read(ROOT/'inputs'/source['id']/'clock.json')['normalized_exact_pts']]
        for case in source['cases']:
            require(sha(case['query_path']) == case['query_sha256'], 'Serialized new tokens changed')
            x = torch.load(case['query_path'], map_location='cpu', weights_only=True)
            ids, mask = x['input_ids'], x['attention_mask']; k = case['queries']
            require(ids.dtype == mask.dtype == torch.int64 and ids.shape == mask.shape and ids.ndim == 2 and ids.shape[0] == k and ids.shape[1] <= 4096, 'Actual query batch shape/dtype')
            require(bool((mask[:,-1] == 1).all()) and bool(((mask == 0)|(mask == 1)).all()) and bool((mask[:,1:] >= mask[:,:-1]).all()), 'Strict left padding and valid readout')
            chunk = case['original_image_chunk']; require(sha(chunk['path']) == chunk['sha256'], 'Original image cache binding')
            original = torch.load(chunk['path'], map_location='cpu', weights_only=True)
            require(original['image_grid_thw'].tolist() == chunk['grid'] and original['sample_ordinals'] == chunk['samples'], 'Saved actual image/grid/target order')
            require(original['pixel_values'].ndim == 2 and bool(torch.isfinite(original['pixel_values']).all()), 'Adopted finite CPU image payload')
            lengths_expected = [g[0]*g[1]*g[2]//4 for g in chunk['grid']]
            for target in range(k):
                row = ids[target][mask[target].bool()].tolist(); lengths = []; running = 0
                for token in row+[None]:
                    if token == image_id: running += 1
                    elif running: lengths.append(running); running = 0
                require(lengths == lengths_expected, 'Independent ordered placeholder-to-grid mapping')
                decoded = tokenizer.decode(row, skip_special_tokens=False)
                require(QUESTION in decoded and 'Does frame %d depict a visual highlight in this context? Answer exactly Yes or No.' % (target+1) in decoded, 'Exact frozen target-specific task text')
                markers = ['Frame %d, relative time %.3fs.\n' % (j+1,float(pts[o]-pts[chunk['samples'][0]])) for j,o in enumerate(chunk['samples'])]
                positions = [decoded.find(marker) for marker in markers]
                require(all(pos >= 0 for pos in positions) and positions == sorted(set(positions)), 'Independent exact native context times and image order')
            batches += 1; queries += k
    require(queries == accepted['original_unique_images'], 'Independent total426 target denominator')
    write(receipt_path, dict(status='PASS_ALL426_SERIALIZED_SEMANTIC_TEXT_QA', query_manifest_sha256=manifest_sha,
                             batches=batches, queries=queries, labels_read=False, new_image_processors=0, new_decodes=0))


def load_saved_batch(path, case):
    import torch
    part = torch.load(path, map_location='cpu', weights_only=True)
    require(part['query_sha256'] == case['query_sha256'] and part['image_sha256'] == case['original_image_chunk']['sha256'] and
            part['sample_ordinals'] == case['original_image_chunk']['samples'], 'Saved successful forward input binding')
    require(part['language'].shape == (case['queries'],4096) and part['yes_no'].shape == (case['queries'],2) and
            bool(torch.isfinite(part['language']).all()) and bool(torch.isfinite(part['yes_no']).all()), 'Saved real semantic output shape/finite')
    proof = path.with_suffix('.json')
    receipt = dict(status='PASS_SAVED_SEMANTIC_CONTEXT_BATCH', path=str(path), sha256=sha(path),
                   query_sha256=case['query_sha256'], image_sha256=case['original_image_chunk']['sha256'], samples=part['sample_ordinals'])
    if proof.exists(): require(read(proof) == receipt, 'Saved forward proof changed')
    else: write(proof, receipt)  # Complete proof for a fully saved forward; no rerun.
    return part


def infer():
    import numpy as np
    import torch
    from peft.tuners.tuners_utils import BaseTunerLayer
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '0', 'Only shared GPU wrapper may invoke infer on declared GPU0')
    torch.set_num_threads(2); reg = checked_registration(); accepted = checked_queries()
    qa_proof = read(QUERY/'independent_text_QA.json')
    require(qa_proof['status'] == 'PASS_ALL426_SERIALIZED_SEMANTIC_TEXT_QA' and qa_proof['query_manifest_sha256'] == sha(QUERY/'cpu_acceptance.json'), 'Independent first text QA required')
    require(not (ROOT/'feature_completion.json').exists(), 'Successful full426 feature stage must never be relaunched')
    sys.path.insert(0,str(RUN/'b_score_aligned_package_v4')); import engine
    cfg = read(RUN/'b_score_aligned_package_v4/config.json'); model, processor, identity = engine.load_model(cfg)
    native = model.get_base_model(); core = native.model
    flags = [(p,p.requires_grad) for p in model.parameters()]
    layers = [m for m in model.modules() if isinstance(m,BaseTunerLayer)]
    require(len(layers) == 144 and identity['logical_parameters'] == 8782459120, 'Actual physical base+TIME inventory')
    records = []; new_batches = new_queries = new_image_evaluations = adopted_batches = 0
    try:
        with model.disable_adapter(), torch.inference_mode():
            require(all(m.disable_adapters for m in layers), 'Actual BASE semantic role')
            for source in accepted['sources']:
                sid = source['id']; directory = ROOT/'features'/sid; directory.mkdir(parents=True,exist_ok=True)
                pieces = []; pairs = []
                for ci,case in enumerate(source['cases']):
                    chunk = case['original_image_chunk']
                    require(sha(chunk['path']) == chunk['sha256'] and sha(case['query_path']) == case['query_sha256'], 'Actual frozen image/token payload')
                    path = directory/('context_%04d.pt' % ci)
                    if path.exists():
                        part = load_saved_batch(path,case); adopted_batches += 1
                    else:
                        require(not path.with_suffix('.json').exists(), 'Orphan prior receipt blocks recomputation')
                        original = torch.load(chunk['path'],map_location='cpu',weights_only=True)
                        text = torch.load(case['query_path'],map_location='cpu',weights_only=True); k = case['queries']
                        gpu = {key:value.to('cuda:0') for key,value in text.items()}
                        gpu['pixel_values'] = original['pixel_values'].repeat(k,1).to('cuda:0')
                        gpu['image_grid_thw'] = original['image_grid_thw'].repeat(k,1).to('cuda:0')
                        output = core(**gpu,use_cache=False,return_dict=True); last = output.last_hidden_state[:,-1,:]
                        logits = native.lm_head(last).float()
                        pair = logits[:,[accepted['readout_token_ids']['Yes'],accepted['readout_token_ids']['No']]].cpu()
                        # Durable per-batch payload is saved immediately, before
                        # source concatenation or any later engineering check.
                        require(bool(torch.isfinite(last).all()) and bool(torch.isfinite(pair).all()), 'Actual finite semantic forward')
                        save_once_tensor(path,dict(language=last.float().cpu(),yes_no=pair,
                                                 query_sha256=case['query_sha256'], image_sha256=chunk['sha256'],sample_ordinals=chunk['samples']))
                        part = load_saved_batch(path,case)
                        new_batches += 1; new_queries += k; new_image_evaluations += k*k
                        event('PRODUCTION_SEMANTIC_BATCH_SAVED',id=sid,batch=ci,queries=k,image_evaluations=k*k)
                        del gpu, output, last, logits, pair, original, text
                    pieces.append(part['language'].numpy()); pairs.append(part['yes_no'].numpy())
                language = np.concatenate(pieces); yesno = np.concatenate(pairs)
                require(language.shape == (source['feature_cells'],4096) and yesno.shape == (source['feature_cells'],2), 'Complete native target order')
                for filename, values in [('language.npy',language),('yes_no.npy',yesno)]:
                    path = directory/filename
                    if path.exists(): require(np.array_equal(np.load(path),values), 'Previously saved source concatenation changed')
                    else:
                        with path.open('xb') as handle: np.save(handle,values)
                rec = dict(id=sid,cells=len(language),dimension=4096,language_path=str(directory/'language.npy'),
                           yes_no_path=str(directory/'yes_no.npy'),language_sha256=sha(directory/'language.npy'),yes_no_sha256=sha(directory/'yes_no.npy'),
                           native_sha256=source['native_sha256'],clock_sha256=source['clock_sha256'],query_acceptance_sha256=sha(QUERY/sid/'acceptance.json'))
                path = directory/'completion.json'
                if path.exists(): require(read(path) == rec, 'Source completion identity changed')
                else: write(path,rec)
                records.append(rec)
                if len(records) == 4:
                    sys.path.insert(0,str(ROOT))
                    from semantic_oof09 import transform
                    from monotone_head06 import ResidualHead,native_prediction
                    from score_residual_head_v1.contracts import build_contract
                    for previous in records:
                        n = np.load(ROOT/'inputs'/previous['id']/'native.npz')
                        x = transform(np.load(previous['language_path']),np.load(previous['yes_no_path']),n,reg['selected_view'])
                        require(x.shape == (previous['cells'],reg['feature_dimension']), 'Actual first4 selected transform dimension')
                        c = build_contract(n['groups'].tolist(),n['baseline'].tolist(),[None]*len(n['baseline']),len(x),read(ROOT/'inputs'/previous['id']/'clock.json')['normalized_exact_pts'])
                        zero = ResidualHead(x.shape[1],8)
                        require(native_prediction(zero(torch.from_numpy(x)).detach(),c) == c.baseline_native and
                                zero.parameter_count+8782459120 == reg['actual_resident_parameters'], 'Actual first4 zero native identity/parameters')
                    proof = dict(status='PASS_FOUR_REAL_SOURCES_SEMANTIC_NATIVE_MAPPING_ZERO_IDENTITY',sources=records.copy(),selected_view=reg['selected_view'],actual_resident_parameters=reg['actual_resident_parameters'])
                    path = ROOT/'semantic_engineering4.json'
                    if path.exists(): require(read(path) == proof, 'Prior first4 engineering proof changed')
                    else: write(path,proof)
    finally:
        for parameter,flag in flags: parameter.requires_grad_(flag)
    require(all(not m.disable_adapters for m in layers) and all(p.requires_grad == flag for p,flag in flags), 'Exact PEFT enable/parameter flags restoration')
    require(engine.frozen_identity(model,cfg) == identity['base'] and engine.adapter_identity(model,cfg) == identity['adapter'], 'Actual frozen model changed')
    write(ROOT/'feature_completion.json',dict(status='PASS_ALL426_NEW_SEMANTIC_CONTEXT_FEATURES',sources=records,
          model_identity=identity,selected_view=reg['selected_view'],registration_sha256=sha(ROOT/'production_registration.json'),
          query_manifest_sha256=sha(QUERY/'cpu_acceptance.json'),forward_batches_this_invocation=new_batches,
          target_queries_this_invocation=new_queries,image_evaluations_this_invocation=new_image_evaluations,
          adopted_successful_batches_this_invocation=adopted_batches,total_target_queries=sum(s['cells'] for s in records),
          total_image_evaluations=sum(c['queries']**2 for s in accepted['sources'] for c in s['cases']),
          actual_backbone_parameters=8782459120,new_generation_calls=0,new_optimizer_updates=0,labels_read=False,
          all_parameter_flags_restored=True,quality_scope='Historically exposed OOF; final25 official effect UNKNOWN'))


if __name__ == '__main__':
    try:
        {'prepare':prepare,'qa':qa,'infer':infer}[sys.argv[1]]()
    except BaseException as error:
        import traceback
        failure = QUERY/('%s_failure_%s.json' % (sys.argv[1] if len(sys.argv)>1 else 'arguments',os.getpid()))
        if not failure.exists(): write(failure,dict(error=repr(error),traceback=traceback.format_exc(),utc=utc()))
        raise
