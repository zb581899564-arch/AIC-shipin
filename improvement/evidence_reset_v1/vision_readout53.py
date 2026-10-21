"""One fixed pre-language visual readout; adopt accepted native inputs.

No decoder, processor, language-model forward, backbone update or production.
The old last-prefill features/results are controls, not repeated here.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import time
import traceback


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def save(path, value):
    with Path(path).open('x', encoding='utf8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)


def context(root):
    n = Path(root).resolve(strict=True)
    r, w = n.parent, n.parent.parent
    trainer = module(r/'relative_ranker06/rank_train07.py', 'original_rank53')
    old, _, api, p, common, manifest, store, canonical, _, a06 = trainer.context(r/'relative_ranker06')
    admission = json.loads((n/'admission53.json').read_text())
    api.require(admission['code_ref'] == api.ref(__file__) and admission['approved'], 'Exact53 admission')
    lock = api.loadref(admission['source_lock_ref'], w)
    for key in ['old_readout_control_ref', 'old_solver_ref', 'native_helper_ref']:
        api.checked(lock[key], w)
    api.require(lock['code_refs']['protocol53.json'] == admission['protocol_ref'], 'Frozen53 protocol identity')
    a11 = api.loadref(admission['input11_ref'], w)
    a06_bound = api.loadref(admission['input06_ref'], w)
    api.require(a06 == a06_bound, 'Original accepted06 identity')
    return n, r, w, api, common, manifest, store, canonical, a06, a11, admission


def excerpt_shape(grid, plan):
    rows = grid.tolist() if hasattr(grid, 'tolist') else grid
    if len(rows) != 2 or len(plan['videos']) != 2:
        raise ValueError('Two source-owned videos required')
    counts = []
    for row, view in zip(rows, plan['videos']):
        t, h, w = row
        if t != view['groups'] or t <= 0 or h <= 0 or w <= 0 or h % 2 or w % 2:
            raise ValueError('Actual grid/group ownership mismatch')
        if len(view['native_ordinals']) != 2*t or view['padding'] != 0:
            raise ValueError('Only original real paired native observations')
        counts.append(t*h*w//4)
    if plan['videos'][0]['role'] != 'Overview' or plan['videos'][1]['role'] != 'Excerpt':
        raise ValueError('Role order changed')
    return counts, rows[1][0], rows[1][1]*rows[1][2]//4


def independent_pool(torch, group_means):
    raw = group_means.double().mean(0)
    centered = raw - raw.mean()
    return (centered / (centered.square().mean() + 1e-5).sqrt()).float()


def adopted_values(n, r, w, api, common, manifest, store_class, a06, a11, torch):
    """Read existing exact pixel caches; no RGB decoding/encoding/QA replay."""
    inputs11 = module(r/'domain_rank11/domain_inputs11.py', 'original_inputs53')
    references = dict(a11['case_refs'])
    references.update({u: ref for u, ref in a06['case_refs'].items()
                       if api.loadref(ref, w)['scope'] == 'check'})
    api.require(len(references) == 100, 'Exact72 train plus28 check')
    cases = {u: api.loadref(ref, w) for u, ref in references.items()}
    train_sha = {c['source_sha256'] for u, c in cases.items() if u in a11['case_refs']}
    check_sha = {c['source_sha256'] for u, c in cases.items() if u not in a11['case_refs']}
    api.require(len(train_sha) == 18 and len(check_sha) == 8 and not (train_sha & check_sha),
                'Exact train/check physical media isolation adopted')
    values = {}
    store = store_class(manifest, 'check')
    dictionary = store._dictionary_helper()
    for reference in a11['source_refs']:
        s = api.loadref(reference, w)
        frames, grid, ordinals = inputs11.load_source11(s, api, w, torch, dictionary)
        clock = api.loadref(s['clock_ref'], w)
        lookup = {o: i for i, o in enumerate(ordinals)}
        overview = dict(role='Overview', cells=[lookup[o] for o in s['Overview_ordinals']], origin_exact='0')
        for uid, case in cases.items():
            if uid not in a11['case_refs'] or case['sid'] != s['sid']:
                continue
            v, plan = api.build_pixels(torch, frames, grid, ordinals, clock['normalized_exact_pts'],
                                       overview, case['block'], s['sid'], s['source_sha256'])
            v.update(torch.load(api.checked(case['prefix_ref'], w), map_location='cpu', weights_only=True))
            api.require(plan == case['plan'] and common.signature(v) == case['input_signature'],
                        'Adopt exact previously accepted native input')
            excerpt_shape(v['video_grid_thw'], plan)
            values[uid] = v
        del frames
    for uid, case in sorted(cases.items()):
        if uid in values:
            continue
        frames, grid, ordinals = store._source_pixels(case['sid'])
        clock = store.clocks[case['sid']]
        overview = store.requests[store.by_source[case['sid']][0]]['plan']['videos'][0]
        v, plan = api.build_pixels(torch, frames, grid, ordinals, clock['normalized_exact_pts'],
                                   overview, case['block'], case['sid'], case['source_sha256'])
        v.update(torch.load(api.checked(case['prefix_ref'], w), map_location='cpu', weights_only=True))
        api.require(plan == case['plan'] and common.signature(v) == case['input_signature'], 'Adopt original check bytes')
        excerpt_shape(v['video_grid_thw'], plan)
        values[uid] = v
    store.close()
    api.require(len(values) == 100, 'Every original accepted input adopted before model load')
    save(n/'input_adoption53.json', dict(status='PASS100_OLD_ACCEPTED_INPUTS_EXACT_SUBSET_VISION_INTERFACE',
        case_refs=references, new_decoder_calls=0, new_processor_calls=0, old_QA_replayed=False))
    return values, cases


def features(root):
    n, r, w, api, common, manifest, store, canonical, a06, a11, admission = context(root)
    import sys
    sys.path.insert(0, str(w/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/temporal_sft8b_v1'))
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    import torch
    from transformers import Qwen3VLForConditionalGeneration
    api.require(os.environ.get('CUDA_VISIBLE_DEVICES') not in ('', None, '-1') and torch.cuda.is_available(), 'Actual reserved CUDA')
    values, cases = adopted_values(n, r, w, api, common, manifest, store, a06, a11, torch)
    spec = manifest['model_spec']
    model = Qwen3VLForConditionalGeneration.from_pretrained(spec['model_dir'], revision=spec['revision'],
        local_files_only=True, trust_remote_code=False, torch_dtype=torch.bfloat16,
        device_map={'': 'cuda:0'}, low_cpu_mem_usage=True, attn_implementation='sdpa')
    model.eval()
    for parameter in model.parameters():
        parameter.requires_grad_(False)
    before = canonical(model, torch)
    api.require(before['sha256'] == spec['base_sha256'], 'Original BASE bytes')
    calls = [0, 0]
    start = time.monotonic()
    def vision_guard(_module, _args):
        api.require(time.monotonic()-start < admission['max_gpu_seconds'], 'Finite visual readout')
        api.require(not any(p.requires_grad for p in model.parameters()), 'Entire BASE frozen')
        calls[0] += 1
    def forbid_language(_module, _args):
        calls[1] += 1
        raise RuntimeError('Language forward is not admitted')
    hv = model.model.visual.register_forward_pre_hook(vision_guard)
    hl = model.model.language_model.register_forward_pre_hook(forbid_language)
    out = n/'features53'
    out.mkdir()
    refs, adopted = [], {}
    for uid, v in sorted(values.items()):
        case = cases[uid]
        counts, groups, spatial = excerpt_shape(v['video_grid_thw'], case['plan'])
        key = json.dumps({k: case['input_signature'][k] for k in ['pixel_values_videos', 'video_grid_thw']}, sort_keys=True)
        previous = adopted.get(key)
        if previous is None:
            with (n/'events53.jsonl').open('a') as log:
                log.write(json.dumps(dict(event='BEGIN_FIRST_VISUAL_OUTPUT', uid=uid))+'\n');log.flush();os.fsync(log.fileno())
            with torch.inference_mode():
                embeddings, deepstack = model.get_video_features(v['pixel_values_videos'].to('cuda:0'),
                                                                 v['video_grid_thw'].to('cuda:0'))
                api.require(len(embeddings) == 2 and [len(x) for x in embeddings] == counts and
                            all(x.shape[1] == 4096 for x in embeddings), 'Exact installed merged vision split')
                excerpt = embeddings[1].float()
                f = torch.nn.functional.layer_norm(excerpt.mean(0), (4096,), eps=1e-5).cpu().clone()
                # Independent CPU FP64 spatial group reductions, retained for later CPU readout QA.
                group_means = excerpt.cpu().double().reshape(groups, spatial, 4096).mean(1).float()
                del embeddings, deepstack, excerpt
            fp = out/(uid+'.pt')
            torch.save(dict(feature=f, independent_group_means=group_means, uid=uid,
                            source_sha256=case['source_sha256'], input_signature=case['input_signature'],
                            video_grid_thw=v['video_grid_thw']), fp)
            fr = api.ref(fp)
            # Persist the first real pooled output before numerical QA. A failed
            # QA must keep this artifact, never recover by another vision call.
            reconstructed = independent_pool(torch, group_means)
            torch.testing.assert_close(f, reconstructed, atol=2e-5, rtol=1e-4)
            api.require(bool(torch.isfinite(f).all()) and bool(f.abs().max() > 0), 'Finite nonconstant feature')
            adopted[key] = fr
        else:
            fr = previous
        row = dict(uid=uid, source_sha256=case['source_sha256'], feature_ref=fr, case_ref=api.ref(Path(n/'input_adoption53.json')),
                   original_case_signature=case['input_signature'], excerpt_groups=groups, tokens_per_group=spatial,
                   feature_definition='FINAL_MERGED_PRE_LANGUAGE_EXCERPT_TOKENS_SPATIOTEMPORAL_MEAN_FIXED_LN_1e-5',
                   actual_new_vision_forward=previous is None, target_values_used=False)
        rp = out/(uid+'.json');save(rp, row);refs.append(api.ref(rp))
        api.require(sum(p.stat().st_size for p in out.iterdir()) <= admission['planned_output_bytes'], 'Finite persistent output budget')
    hv.remove();hl.remove()
    after = canonical(model, torch)
    api.require(before == after and len(refs) == 100 and calls[1] == 0 and calls[0] == len(adopted), 'Frozen unique visual outputs only')
    save(n/'gpu_completion53.json', dict(status='COMPLETE_FIRST_PRE_LANGUAGE_VISUAL_FEATURES_NOT_QUALITY',
        feature_refs=refs, logical_cases=100, actual_visual_forwards=calls[0], adopted_identical_inputs=100-calls[0],
        language_forwards=calls[1], backbone_updates=0, backward_calls=0, base_before=before, base_after=after,
        seconds=time.monotonic()-start, actual_loaded_parameters=before['parameters'], labels_in_model_inputs=False))


def metric(np, rows, differences, weight):
    out = []
    for row, x in zip(rows, differences):
        margin = float(x @ weight)
        probability = float(np.exp(-np.logaddexp(0, -margin)))
        y = row['preference_left']
        out.append(dict(source_id=row['source_id'], pair_id=row['pair_id'], probability=probability,
                        target=y, correct=.5 if margin == 0 else float((margin > 0) == (y > .5)), brier=(probability-y)**2))
    ids = sorted({x['source_id'] for x in out})
    means = {k: sum(sum(x[k] for x in out if x['source_id'] == sid)/sum(x['source_id'] == sid for x in out)
                    for sid in ids)/len(ids) for k in ['correct', 'brier']}
    return dict(source_macro_accuracy=means['correct'], source_macro_brier=means['brier'], pairs=len(rows), sources=len(ids), rows=out)


def fit(root):
    n, r, w, api, common, manifest, store, canonical, a06, a11, admission = context(root)
    import torch
    import numpy as np
    api.require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU-only first output review/fit')
    complete = json.loads((n/'gpu_completion53.json').read_text())
    adopted_cases = json.loads((n/'input_adoption53.json').read_text())['case_refs']
    decision = json.loads((n/'fit_admission53.json').read_text())
    api.require(decision['completion_ref'] == api.ref(n/'gpu_completion53.json') and
                decision['natural_wrapper_exit_code'] == 0, 'Natural unique terminal before fit')
    values = {}
    for rr in complete['feature_refs']:
        row = api.loadref(rr, w)
        original = api.loadref(adopted_cases[row['uid']], w)
        groups_count = original['plan']['videos'][1]['groups']
        api.require(row['source_sha256'] == original['source_sha256'] and
                    row['original_case_signature'] == original['input_signature'] and
                    row['excerpt_groups'] == groups_count and row['case_ref'] == api.ref(n/'input_adoption53.json'),
                    'Independent original native source/plan identity')
        payload = torch.load(api.checked(row['feature_ref'], w), map_location='cpu', weights_only=True)
        f, groups = payload['feature'], payload['independent_group_means']
        primary_owner = api.loadref(adopted_cases[payload['uid']], w)
        api.require(payload['source_sha256'] == primary_owner['source_sha256'] and
                    payload['input_signature'] == primary_owner['input_signature'], 'Primary output source/input identity')
        api.require(all(payload['input_signature'][key] == original['input_signature'][key]
                        for key in ['pixel_values_videos', 'video_grid_thw']),
                    'An adopted vision output must have identical actual neural inputs; text is not forwarded')
        _, actual_groups, actual_spatial = excerpt_shape(payload['video_grid_thw'], original['plan'])
        api.require(actual_groups == row['excerpt_groups'] and actual_spatial == row['tokens_per_group'],
                    'Independent actual merged-grid pooling ownership')
        api.require(f.dtype == groups.dtype == torch.float32 and tuple(f.shape) == (4096,) and
                    tuple(groups.shape) == (row['excerpt_groups'], 4096), 'First persisted output identity')
        torch.testing.assert_close(f, independent_pool(torch, groups), atol=2e-5, rtol=1e-4)
        values[row['uid']] = f.numpy().astype(float)
    api.require(len(values) == 100, 'All100 pooled outputs independently reviewed')
    solver = module(r/'domain_rank11/domain_run12.py', 'unchanged_convex_solver53')
    train = api.loadref(a11['training_target_ref'], w)
    check = api.loadref(a06['check_target_ref'], w)
    check = sorted(check, key=lambda x: hashlib.sha256(x['pair_id'].encode()).hexdigest())
    api.require(len(train) == 36 and len({x['source_id'] for x in train}) == 18 and len(check) == 14,
                'Exact old matched-domain training and source-disjoint check')
    api.require(not ({x['source_id'] for x in train} & {x['source_id'] for x in check}), 'No source-ID overlap')
    xtrain = np.vstack([(values[x['left']]-values[x['right']])/64 for x in train])
    xcheck = np.vstack([(values[x['left']]-values[x['right']])/64 for x in check])
    weight, receipt = solver.convex_fit(np, xtrain, np.asarray([x['preference_left'] for x in train]))
    fp = n/'head53.pt';torch.save(dict(weight=torch.from_numpy(weight.copy())), fp)
    reloaded = torch.load(fp, map_location='cpu', weights_only=True)['weight']
    api.require(torch.equal(reloaded.view(torch.uint8), torch.from_numpy(weight).view(torch.uint8)), 'Exact fitted head save/reload')
    api.require(abs(float(reloaded @ torch.from_numpy(xcheck[0]))-float(weight @ xcheck[0])) < 1e-10, 'Independent scalar readout')
    measured = dict(train=metric(np, train, xtrain, weight), check=metric(np, check, xcheck, weight),
                    permuted_content=metric(np, check, np.roll(xcheck, 1, axis=0), weight))
    old = json.loads((r/'domain_rank11/review12.json').read_text())['metrics']['SumMe']['check']
    reasons = []
    real, perm = measured['check'], measured['permuted_content']
    if real['source_macro_accuracy'] < .75:reasons.append('REAL_ACCURACY_BELOW_POINT75')
    if real['source_macro_accuracy'] <= old['source_macro_accuracy']:reasons.append('NOT_BETTER_THAN_PRIOR_BEST_PREFILL_CONTROL')
    if real['source_macro_brier'] >= old['source_macro_brier']:reasons.append('SOFT_TARGET_BRIER_NOT_BETTER_THAN_PRIOR_CONTROL')
    if real['source_macro_accuracy'] <= perm['source_macro_accuracy'] or real['source_macro_brier'] >= perm['source_macro_brier']:
        reasons.append('CONTENT_PERMUTATION_CONTROL_NOT_SURPASSED')
    improved = [sid for sid in sorted({x['source_id'] for x in check})
                if np.mean([x['correct'] for x in real['rows'] if x['source_id'] == sid]) >
                   np.mean([x['correct'] for x in old['rows'] if x['source_id'] == sid])]
    if len(improved) < 2:reasons.append('FEWER_THAN_TWO_SOURCES_IMPROVED')
    receipt.update(weight_ref=api.ref(fp), parameters=4096, raw_feature_dimension=4096,
                   prior_solver_implementation=api.ref(r/'domain_rank11/domain_run12.py'))
    save(n/'solver53.json', receipt)
    save(n/'review53.json', dict(status='STOP_FIXED_PRE_LANGUAGE_VISUAL_READOUT' if reasons else
         'ELIGIBLE_FOR_SEPARATE_FULL_SOURCE_EXTERNAL_REVIEW', stop_reasons=reasons, metrics=measured,
         prior_best_prefill_control=old, improved_sources=improved, first_output_QA='ALL100_PASS',
         actual_new_CPU_heads=1, actual_Newton_updates=receipt['updates'], actual_backbone_updates=0,
         donor_swap_not_independent='Vision-only excerpt donor simply transfers its original feature; not a new control.',
         historical_exposed=True, proxy_not_official_joint_truth=True, automatic_production=False,
         new_ZIP=0, official_submissions=0))


if __name__ == '__main__':
    parser = argparse.ArgumentParser();parser.add_argument('--run-root', required=True)
    parser.add_argument('--phase', choices=['features', 'fit'], required=True);args = parser.parse_args()
    try:
        (features if args.phase == 'features' else fit)(args.run_root)
    except BaseException:
        save(Path(args.run_root)/('failure_'+args.phase+'53.json'),
             dict(status='ACTUAL_FAILURE_PRESERVE_NO_AUTOMATIC_RETRY', traceback=traceback.format_exc()))
        raise
