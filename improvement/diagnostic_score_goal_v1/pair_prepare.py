"""First CPU preparation and independent QA for a new two-video experiment."""
import argparse
import itertools
from pathlib import Path
import sys
import traceback
from pair_common import *
from pair_preference_math import full_clips, make_train_pairs, preference_votes, prepare_policy
from pair_video_input import pair_video_pixels, build_text_input, independent_pixel_check, independent_text_check


def run(root):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU child masks itself only')
    import numpy as np
    import torch
    from transformers import AutoProcessor
    torch.set_num_threads(2)
    reg = registration(root)
    out = root/'pair_inputs_17'; out.mkdir(exist_ok=False)
    save(out/'claim.json', dict(utc=utc(), registration=ref(root/'pair_registration_17.json'), pid=os.getpid()))
    done = []
    try:
        sys.path.insert(0, str(OLD/'code'))
        from data import source_pixels
        accepted = read(bound(reg['accepted_external']))
        catalog = read(bound(reg['assembled_external']))
        annotation = {s['id']: s for s in read(bound(reg['original_ranking_diagnostic']))['sources']}
        roles = {s['id']: s for s in catalog['sources']}
        require(len(roles) == len(accepted['sources']) == 25 and
                sum(s['role'] == 'train' for s in roles.values()) == 20 and
                sum(s['role'] == 'dev' for s in roles.values()) == 5, 'Fixed original20/5 source split')
        require(not ({s['source_sha256'] for s in roles.values() if s['role'] == 'train'} &
                     {s['source_sha256'] for s in roles.values() if s['role'] == 'dev'}),
                'Known source byte identities must be train/dev disjoint')
        proof = read(bound(reg['original_pairing_proof']))
        require(proof['status'] == 'PASS_DIRECT_VIDEO_PROCESSOR_BIT_EQUAL_EVEN_AND_ODD',
                'Adopt prior measured pixel-pairing identity without repeating processor')
        sources = []
        for old in accepted['sources']:
            s = dict(old)
            require(s['source_sha256'] == roles[s['id']]['source_sha256'], 'Source bytes/split alignment')
            s['role'] = roles[s['id']]['role']; sources.append(s)
        source_path = out/'source_catalog.json'
        save(source_path, dict(sources=sources, original_acceptance=reg['accepted_external']))
        cfg = read(bound(reg['model_config']))
        processor = AutoProcessor.from_pretrained(cfg['model_dir'], local_files_only=True,
            max_pixels=65536, min_pixels=65536)
        class_ids = None
        train_entries, dev_entries, train_summaries, eval_pairs, policy_sources, original_labels = [], [], [], [], [], []
        request_refs = {}
        for source in sources:
            sid = source['id']; role = source['role']; src_dir = out/sid; src_dir.mkdir()
            fpath = bound(roles[sid]['features'])
            with np.load(fpath, allow_pickle=False) as f:
                groups = f['native_group'].copy()
            with np.load(bound(source['native']), allow_pickle=False) as f:
                cells = f['groups'].copy(); baseline = f['baseline'].copy(); saved_ordinals = f['sample_ordinals'].copy()
            label_ref = annotation[sid]['bindings']['original_annotation_array']
            raw_labels = np.load(bound(label_ref), allow_pickle=False)
            require(raw_labels.ndim == 2 and len(raw_labels) == len(groups) == source['native_frames'] and
                    np.isfinite(raw_labels).all(), 'No missing human labels converted to zero or native remapping')
            labels = raw_labels > 0
            clock = read(bound(source['clock']))
            frames, grid, ordinals = source_pixels(source)
            require(ordinals == saved_ordinals.tolist() and clock['source_sha256'] == source['source_sha256'],
                    'Actual native samples/source identity')
            clips = full_clips(groups, cells)
            require(len(clips) >= 2, 'Insufficient original source domain for two complete clips')
            original_labels.append(dict(id=sid, source_sha256=source['source_sha256'], role=role,
                                        annotation_array=label_ref, native=source['native'], groups=roles[sid]['features']))

            def input_ref(a, b):
                nonlocal class_ids
                ranges = [[a['cell_start'], a['cell_end_exclusive']], [b['cell_start'], b['cell_end_exclusive']]]
                key = hashlib.sha256(json.dumps([source['source_sha256'], ranges], separators=(',', ':')).encode()).hexdigest()[:24]
                cid = sid+'_'+key
                if cid in request_refs:
                    return cid, request_refs[cid]
                pair = pair_video_pixels(frames, grid, ranges, ordinals, clock['normalized_exact_pts'],
                                         pairing_proof_ref=reg['original_pairing_proof'])
                encoded, text = build_text_input(processor, pair)
                independent_pixel_check(frames, grid, ranges, ordinals, clock['normalized_exact_pts'], pair)
                independent_text_check(processor, pair, encoded, text)
                ids = text['class_token_ids']
                if class_ids is None:
                    class_ids = ids
                require(ids == class_ids, 'One unchanged actual digit-token class mapping')
                values = dict(**encoded, pixel_values_videos=pair['pixel_values_videos'], video_grid_thw=pair['video_grid_thw'])
                token_path = src_dir/(cid+'.tokens.pt')
                with token_path.open('xb') as stream:
                    torch.save(encoded, stream)
                restored = torch.load(token_path, map_location='cpu', weights_only=True)
                require(signature(encoded) == signature(restored), 'New token cache actual save/reload')
                path = src_dir/(cid+'.json')
                request = dict(id=cid, source_id=sid, source_sha256=source['source_sha256'], clip_ranges=ranges,
                    clip_A=a, clip_B=b, tokens=ref(token_path), class_token_ids=ids,
                    input_signature=signature(values), video_grid_thw=pair['video_grid_thw'].tolist(),
                    text_evidence=text, clip_metadata=pair['clip_metadata'], sample_bindings=pair['sample_bindings'],
                    old_pairing_proof=reg['original_pairing_proof'], original_decode=0, original_processor_calls=0,
                    target_or_GT_in_prompt=False)
                save(path, request); request_refs[cid] = ref(path)
                done.append(dict(id=cid, source_id=sid, input=request_refs[cid], role=role))
                if role == 'dev':
                    dev_entries.append(dict(id=cid, source_id=sid, input=request_refs[cid], role='EXTERNAL_DEV_INFERENCE'))
                return cid, request_refs[cid]

            def pair_record(a, b, target, purpose):
                first, first_ref = input_ref(a, b); reverse, reverse_ref = input_ref(b, a)
                eval_pairs.append(dict(source_id=sid, source_sha256=source['source_sha256'], purpose=purpose,
                    first_id=first, reverse_id=reverse, target=target, same_clip=False))
                return first, reverse

            if role == 'train':
                selection = make_train_pairs(source['source_sha256'], clips, labels)
                require(selection['selected_pairs'] > 0, 'No successful training source may be silently dropped')
                train_summaries.append(dict(id=sid, **{k:v for k,v in selection.items() if k != 'pairs'}))
                for pair in selection['pairs']:
                    for order in pair['orders']:
                        cid, reference = input_ref(order['clip_A'], order['clip_B'])
                        train_entries.append(dict(id=cid, source_id=sid, input=reference, target=order['target'],
                            unordered_pair_id=pair['pair_id'], order=order['order'], stratum=pair['stratum']))
            else:
                # Source-hash-only generic pairs, independent of votes or B0 applicability.
                unordered = list(itertools.combinations(clips, 2))
                unordered.sort(key=lambda ab: hashlib.sha256(json.dumps([source['source_sha256'],
                    ab[0]['cell_start'], ab[1]['cell_start']], separators=(',', ':')).encode()).hexdigest())
                for a, b in unordered[:16]:
                    pair_record(a, b, preference_votes(labels, a, b)['distribution'], 'FIXED_GENERIC_PAIR')
                policy = prepare_policy(groups, cells, baseline)
                candidates = []
                if policy['anchor'] is not None:
                    for candidate in policy['candidates']:
                        first, reverse = pair_record(candidate, policy['anchor'],
                            preference_votes(labels, candidate, policy['anchor'])['distribution'], 'FIXED_ADDITION_POLICY')
                        candidates.append(dict(clip=candidate, first_id=first, reverse_id=reverse))
                self_id, self_ref = input_ref(clips[0], clips[0])
                eval_pairs.append(dict(source_id=sid, source_sha256=source['source_sha256'],
                    purpose='IDENTICAL_CLIP_TIE_CONTROL', first_id=self_id, reverse_id=self_id,
                    target=[0.,0.,1.], same_clip=True))
                policy_sources.append(dict(id=sid, source_sha256=source['source_sha256'],
                    native=source['native'], groups=roles[sid]['features'], clock=source['clock'],
                    inventory=policy, candidates=candidates, self_control=self_id,
                    baseline_scope='Original external B0 NOT complete40.47'))
            save(src_dir/'source_acceptance.json', dict(status='PASS_NEW_TWO_VIDEO_SOURCE_INPUTS',
                source_sha256=source['source_sha256'], new_unique_inputs=sum(x['source_id'] == sid for x in done),
                native_frames=source['native_frames'], actual_image_grid=grid,
                original_decode=0, original_processor_calls=0, role=role))
            print('FIRST_CPU_PREFERENCE_INPUTS', sid, len(done), flush=True)
            del frames
        require(len({r['id'] for r in train_entries}) == len(train_entries) and
                {r['source_id'] for r in train_entries} == {s['id'] for s in sources if s['role'] == 'train'},
                'Unique source-balanced ordered training examples')
        train_path = out/'train_targets.json'; save(train_path, train_entries)
        save(root/'pair_evaluation_targets_17.json', dict(pairs=eval_pairs, policies=policy_sources,
                                                       original_labels=original_labels, not_model_input=True))
        save(out/'training_distribution.json', dict(sources=train_summaries,
            unordered_pairs=sum(s['selected_pairs'] for s in train_summaries),
            ordered_examples=len(train_entries), native_source_independence=20,
            two_orders_not_independent=True, class_token_ids=class_ids))
        prepared = out/'prepared.json'
        save(prepared, dict(source_catalog=ref(source_path), inputs=done,
            train_targets=ref(train_path), dev_inputs=dev_entries,
            train_source_ids=sorted(s['id'] for s in sources if s['role'] == 'train'),
            dev_source_ids=sorted(s['id'] for s in sources if s['role'] == 'dev'),
            class_token_ids=class_ids, original_processor_calls=0, original_decode=0))
        save(out/'input_acceptance.json', dict(status='PASS_ALL_NEW_TWO_VIDEO_PREFERENCE_CPU_INPUTS',
            prepared=ref(prepared), inputs=len(done), train_ordered_examples=len(train_entries),
            dev_inference_inputs=len(dev_entries), class_token_ids=class_ids,
            old_pairing_QA_adopted=reg['original_pairing_proof'], independent_pixels_and_text=True,
            new_real_vision_processor_calls=0, original_QA_repeated=False))
        require(not torch.cuda.is_initialized(), 'CPU preparation cannot initialize GPU')
        print('ALL_CPU_INPUTS_ACCEPTED', len(done), 'DEV', len(dev_entries), flush=True)
    except BaseException as error:
        save(out/'failure.json', dict(error=repr(error), traceback=traceback.format_exc(),
             completed_new_inputs=done, preserve_all_success=True, no_automatic_retry=True))
        raise


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--root', type=Path, required=True)
    run(p.parse_args().root)
