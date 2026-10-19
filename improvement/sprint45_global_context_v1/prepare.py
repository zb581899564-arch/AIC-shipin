"""Text/reference preparation and first independent CPU input QA, no media work."""
from global_context_common import *


def prepare(root):
    import torch
    from transformers import AutoProcessor
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU-only text preparation required')
    root, protocol, sources = checked_protocol(root)
    require(not (root/'input_manifest.json').exists(), 'Successful input preparation cannot be rerun')
    require(not (root/'queries').exists(), 'Partial preparation needs explicit engineering recovery, no overwrite')
    (root/'queries').mkdir()
    cfg = read(bound(protocol['frozen_model_config']))
    processor = AutoProcessor.from_pretrained(cfg['model_dir'], local_files_only=True)
    tokenizer = processor.tokenizer; grammar = grammar_spec(tokenizer)
    image_id = tokenizer.convert_tokens_to_ids('<|image_pad|>')
    require(type(image_id) is int and image_id >= 0, 'Actual image token identity')
    results = []; canonical = {}; total_targets = total_images = total_tokens = 0
    for source in sources:
        refs, pts, groups = checked_source(source); cache = ChunkCache()
        anchor_indices = anchors(len(refs)); directory = root/'queries'/source['id']; directory.mkdir()
        cases = []
        for ci, start in enumerate(range(0, len(refs), 8)):
            local = list(range(start, min(start+8,len(refs))))
            images, targets, global_positions = case_mapping(refs, local, anchor_indices)
            text = render_text(processor, images, targets, global_positions)
            encoded = tokenizer(text, return_tensors='pt', add_special_tokens=False)
            query = {key: encoded[key].contiguous() for key in ('input_ids','attention_mask')}
            require(query['input_ids'].shape[0] == 1 and query['input_ids'].shape[1] <= 8192 and
                    bool((query['attention_mask'] == 1).all()), 'Actual batch1/input8192 token budget')
            composed = compose(images, cache)
            key, fingerprints = effective_input({**query, **composed})
            case_id = '%s:%04d' % (source['id'],ci)
            unique = key not in canonical
            if unique: canonical[key] = case_id
            query_path = directory/('query_%04d.pt' % ci); save_tensor(query_path, query)
            case = dict(case_id=case_id, id=source['id'], index=ci, effective_key=key,
                canonical_case_id=canonical[key], unique_generation=unique,
                query_path=str(query_path), query_sha256=sha(query_path),
                text=text, text_sha256=hashlib.sha256(text.encode()).hexdigest(), input_tokens=query['input_ids'].shape[1],
                images=images, targets=targets, global_image_indices=global_positions,
                global_anchor_cell_indices=anchor_indices, actual_input_fingerprints=fingerprints,
                output_bits=2*len(targets), max_new_tokens=4*len(targets),
                old_source_acceptance=binding(Path(ADOPTED)/'inputs'/source['id']/'acceptance.json'),
                source_native_sha256=source['native_sha256'], source_clock_sha256=source['clock_sha256'],
                pixels_serialized=False, composed_actual_input=True)
            proof_path = directory/('case_%04d.json' % ci); write(proof_path, case)
            cases.append(dict(case_id=case_id, path=str(proof_path), sha256=sha(proof_path),
                effective_key=key, canonical_case_id=canonical[key], unique_generation=unique,
                targets=len(targets), images=len(images)))
            total_targets += len(targets); total_images += len(images); total_tokens += case['input_tokens']
            del composed, query, encoded
        require(sum(c['targets'] for c in cases) == source['feature_cells'], 'Every source cell is exactly one target')
        results.append(dict(id=source['id'], cells=source['feature_cells'], cases=cases,
            source_acceptance=binding(Path(ADOPTED)/'inputs'/source['id']/'acceptance.json'),
            native_path=str(Path(ADOPTED)/'inputs'/source['id']/'native.npz'), native_sha256=source['native_sha256'],
            clock_path=str(Path(ADOPTED)/'inputs'/source['id']/'clock.json'), clock_sha256=source['clock_sha256']))
        event(root, 'NEW_COMPOSED_INPUT_SOURCE_PREPARED', id=source['id'], cases=len(cases), cells=source['feature_cells'])
    require(total_targets == sum(s['feature_cells'] for s in sources), 'Full426 denominator')
    write(root/'input_manifest.json', dict(status='PASS_ALL426_NEW_GLOBAL_LOCAL_INPUTS', schema=SCHEMA,
        protocol_sha256=sha(root/'protocol.json'), adopted_cpu_acceptance=protocol['adopted_cpu_acceptance'],
        sources=results, cases=sum(len(s['cases']) for s in results), targets=total_targets,
        unique_inputs=len(canonical), aliases=sum(len(s['cases']) for s in results)-len(canonical),
        physical_image_appearances=total_images, total_input_tokens=total_tokens, grammar=grammar,
        image_token_id=image_id, question_sha256=hashlib.sha256(QUESTION.encode()).hexdigest(),
        anchor_policy='exact rational linspace indices; round-half-to-even; stable dedup',
        new_image_processors=0, new_decoders=0, new_pixel_files=0, new_model_calls=0,
        historical_native_baseline='VERIFY40.46 only; never used as current40.47 baseline',
        current_baseline=protocol['current_baseline'], utc=utc()))


def load_case(entry):
    case = read(bound(dict(path=entry['path'], sha256=entry['sha256'])))
    require(case['case_id'] == entry['case_id'] and case['effective_key'] == entry['effective_key'] and
            case['canonical_case_id'] == entry['canonical_case_id'] and
            case['unique_generation'] is entry['unique_generation'], 'Bound full case manifest identity')
    require(sha(case['query_path']) == case['query_sha256'] and case['pixels_serialized'] is False, 'Bound tokens, no pixel copies')
    return case


def input_qa(root):
    import torch
    from transformers import AutoTokenizer
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'Independent CPU-only input QA required')
    root, protocol, sources = checked_protocol(root); manifest = checked_manifest(root)
    require(not (root/'input_qa.json').exists(), 'Successful first input QA cannot be rerun')
    tokenizer = AutoTokenizer.from_pretrained(read(bound(protocol['frozen_model_config']))['model_dir'], local_files_only=True)
    require(grammar_spec(tokenizer) == manifest['grammar'], 'Independent tokenizer binary/space/EOS identity')
    require(tokenizer.convert_tokens_to_ids('<|image_pad|>') == manifest['image_token_id'], 'Independent image token')
    seen = {}; cases = targets = appearances = 0; first4 = []
    for source, prepared in zip(sources, manifest['sources']):
        require(source['id'] == prepared['id'], 'Source identity/order')
        refs, pts, groups = checked_source(source); cache = ChunkCache(); actual_cells = []
        require(len(prepared['cases']) == (len(refs)+7)//8, 'Registered local8 case count')
        for ci, entry in enumerate(prepared['cases']):
            case = load_case(entry)
            local = list(range(ci*8,min(ci*8+8,len(refs))))
            images, mappings, global_positions = case_mapping(refs,local,anchors(len(refs)))
            require(case['images'] == images and case['targets'] == mappings and
                    case['global_image_indices'] == global_positions and
                    case['global_anchor_cell_indices'] == anchors(len(refs)), 'Independent global/local/native image mapping')
            x = torch.load(case['query_path'], map_location='cpu', weights_only=True)
            require(set(x) == {'input_ids','attention_mask'}, 'Only new tokens/mask serialized')
            ids, mask = x['input_ids'],x['attention_mask']
            require(ids.dtype == mask.dtype == torch.int64 and ids.shape == mask.shape and
                    ids.ndim == 2 and ids.shape[0] == 1 and 0 < ids.shape[1] <= 8192 and
                    bool((mask == 1).all()), 'Independent batch1 tokens/mask/8192 budget')
            require(hashlib.sha256(case['text'].encode()).hexdigest() == case['text_sha256'] and
                    tokenizer.encode(case['text'], add_special_tokens=False) == ids[0].tolist(), 'Independent actual serialized token encoding')
            decoded = tokenizer.decode(ids[0].tolist(), skip_special_tokens=False, clean_up_tokenization_spaces=False)
            require(QUESTION in decoded, 'Frozen two-question text retained')
            markers = [content['text'] for content in prompt_content(images,mappings,global_positions) if content['type'] == 'text']
            require(all(marker in decoded for marker in markers), 'Independent whole-source/local target text and exact PTS')
            lengths = []; running = 0
            for token in ids[0].tolist()+[None]:
                if token == manifest['image_token_id']: running += 1
                elif running: lengths.append(running); running = 0
            require(lengths == [math.prod(r['grid'])//4 for r in images], 'Ordered per-image placeholder/grid mapping')
            composed = compose(images,cache)
            key, fingerprints = effective_input({**x,**composed})
            require(key == case['effective_key'] and fingerprints == case['actual_input_fingerprints'], 'Independent full actual composed input bit hashes')
            unique = key not in seen
            if unique: seen[key] = case['case_id']
            require(case['unique_generation'] is unique and case['canonical_case_id'] == seen[key], 'Independent exact input alias/canonical proof')
            require(case['output_bits'] == 2*len(local) and case['max_new_tokens'] == 4*len(local), 'Fixed grammar length')
            actual_cells.extend(t['cell_index'] for t in mappings)
            cases += 1; targets += len(local); appearances += len(images)
            del composed,x
        require(actual_cells == list(range(len(refs))), 'All source target cells exactly once in native order')
        if len(first4) < 4:
            first4.append(dict(id=source['id'], cells=len(refs), cases=len(prepared['cases']), native_mapping_verified=True))
    require(cases == manifest['cases'] and targets == manifest['targets'] and len(seen) == manifest['unique_inputs'] and
            appearances == manifest['physical_image_appearances'], 'Actual full input/unique denominators')
    write(root/'input_qa.json', dict(status='PASS_ALL426_INDEPENDENT_GLOBAL_LOCAL_INPUT_QA',
        protocol_sha256=sha(root/'protocol.json'), input_manifest_sha256=sha(root/'input_manifest.json'),
        cases=cases, sources=426, targets=targets, unique_inputs=len(seen), aliases=cases-len(seen),
        physical_image_appearances=appearances, first4_source_engineering_only=first4,
        effective_key_fields=['input_ids','attention_mask','pixel_values','image_grid_thw'],
        exact_same_input_alias_proofs_verified=True, new_image_processors=0, new_decoders=0,
        new_pixel_files=0, new_model_calls=0, utc=utc()))


if __name__ == '__main__': run_phase({'prepare':prepare, 'input-qa':input_qa})
