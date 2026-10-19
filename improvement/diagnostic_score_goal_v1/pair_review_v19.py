"""First independent output QA and fixed-policy external comparison; CPU only."""
import argparse
from pathlib import Path
import sys
import traceback
_support = Path(__file__).resolve().parents[1]/'pair_code_17'
if _support.is_dir():
    sys.path.insert(0, str(_support))
from pair_common import *
from pair_preference_math import source_metrics, select_addition, apply_selection, swapped_distribution, brier


def qa(root, role):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'Only CPU output review')
    import numpy as np
    import torch
    torch.set_num_threads(2)
    registration(root)
    gpu_registration = read(root/'pair_GPU_registration_18.json')
    require(sha(Path(__file__)) == gpu_registration['review_code']['sha256'], 'Frozen first review runtime differs')
    gate = read(bound(gpu_registration['input_acceptance']))
    prepared = read(bound(gate['prepared']))
    expected = {e['id']: e for e in prepared['dev_inputs']}
    completion_path = root/'pair_model_17'/role/'completion.json'
    completion = read(completion_path)
    require(completion['model_role'] == role and completion['status'] == 'COMPLETE_ALL_ROLE_INPUTS_RAW_LOGITS_NOT_QUALITY',
            'Naturally complete actual model role before first independent QA')
    require(len(completion['entries']) == len(expected) == completion['expected_inputs'], 'Complete first-role input set')
    seen, prior_receipts, output = set(), {}, []
    calls = aliases = 0
    for row in completion['entries']:
        require(row['id'] in expected and row['id'] not in seen and row['input'] == expected[row['id']]['input'],
                'Actual output repeated/missing source request')
        receipt = read(bound(row['receipt'])); request = read(bound(row['input']))
        require(receipt['id'] == row['id'] and receipt['source_id'] == request['source_id'] == expected[row['id']]['source_id'] and
                receipt['input'] == row['input'] and receipt['input_signature'] == request['input_signature'] and
                receipt['class_token_ids'] == request['class_token_ids'] and receipt['model_role'] == role,
                'Independent input/source/class/model-role binding')
        tokens = torch.load(bound(request['tokens']), map_location='cpu', weights_only=True)
        require(signature(tokens) == {k:request['input_signature'][k] for k in ('input_ids','attention_mask')},
                'Original first-QA prefix tokens changed')
        raw = torch.load(bound(receipt['raw_logits']), map_location='cpu', weights_only=True)
        require(raw.ndim == 1 and raw.dtype == torch.float32 and torch.isfinite(raw).all() and
                len(raw) == receipt['full_vocabulary_size'], 'Finite actual saved full-vocabulary last logits')
        ids = request['class_token_ids']
        require(len(ids) == len(set(ids)) == 3 and all(type(k) is int and 0 <= k < len(raw) for k in ids),
                'Exact original0/1/2 class token mapping')
        three = raw[ids].double()
        require(np.array_equal(three.numpy(), np.asarray(receipt['class_logits'], dtype=np.float64)),
                'Independent raw class-index extraction')
        p = torch.softmax(three, dim=0).numpy()
        require(np.allclose(p, receipt['probabilities'], rtol=0, atol=5e-15) and
                int(np.argmax(p)) == receipt['predicted_index'], 'Independent3class softmax/argmax')
        if receipt['actual_new_forward']:
            require(receipt['alias_of'] is None, 'A real new forward must not be an alias')
            calls += 1
        else:
            original = prior_receipts.get(receipt['alias_of']['path'])
            require(original is not None and row['receipt'] != receipt['alias_of'] and
                    receipt['alias_of'] == original['reference'] and
                    receipt['input_signature'] == original['receipt']['input_signature'] and
                    receipt['raw_logits'] == original['receipt']['raw_logits'], 'Only exact earlier same-role input aliases')
            aliases += 1
        prior_receipts[row['receipt']['path']] = dict(reference=row['receipt'], receipt=receipt)
        seen.add(row['id']); output.append(dict(id=row['id'], source_id=request['source_id'],
            input=row['input'], receipt=row['receipt'], probabilities=p.tolist(), model_role=role))
    require(seen == set(expected) and calls == completion['actual_forward_calls'] and aliases == completion['aliases'] and
            not torch.cuda.is_initialized(), 'Exact first independent all-role QA counts')
    save(root/('pair_'+role+'_output_acceptance_18.json'), dict(status='PASS_FIRST_ALL_RAW_LOGIT_INPUT_ROLE_QA',
        role=role, completion=ref(completion_path), predictions=output, inputs=len(output), actual_new_forwards=calls,
        exact_input_aliases=aliases, new_model_calls=0, dev_GT_read=False, probability_scope='Three-digit class score; not calibrated highlight probability'))


def evaluate(root):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'Only CPU fixed-policy comparison')
    import numpy as np
    import torch
    torch.set_num_threads(2)
    reg = registration(root); gpu_reg = read(root/'pair_GPU_registration_18.json')
    require(sha(Path(__file__)) == read(root/'pair_remaining_admission_19.json')['comparison_code']['sha256'], 'Explicit first comparison19 runtime differs')
    labels = read(bound(gpu_reg['evaluation_targets']))
    gate = read(bound(gpu_reg['input_acceptance'])); prepared = read(bound(gate['prepared']))
    train = read(bound(prepared['train_targets']))
    by_source = {sid:[] for sid in prepared['train_source_ids']}
    for row in train:
        by_source[row['source_id']].append(row['target'])
    prior = np.mean([np.mean(v, axis=0) for v in by_source.values()], axis=0)
    old_ranking = {s['id']:s for s in read(bound(reg['original_ranking_diagnostic']))['sources']}
    roles, predictions = {}, {}
    for role in ('BASE', 'TRAINED'):
        acceptance_path = root/('pair_'+role+'_output_acceptance_18.json')
        acceptance = read(acceptance_path)
        require(acceptance['status'] == 'PASS_FIRST_ALL_RAW_LOGIT_INPUT_ROLE_QA', 'All first output QA before reference comparison')
        roles[role] = ref(acceptance_path)
        predictions[role] = {r['id']:r['probabilities'] for r in acceptance['predictions']}
    out = root/'pair_comparison_19'; out.mkdir(exist_ok=False)
    summaries = {}
    for role, pred in predictions.items():
        categories = {}
        for purpose in ('FIXED_GENERIC_PAIR', 'FIXED_ADDITION_POLICY', 'IDENTICAL_CLIP_TIE_CONTROL'):
            records = {sid:[] for sid in prepared['dev_source_ids']}
            for row in labels['pairs']:
                if row['purpose'] != purpose:
                    continue
                records.setdefault(row['source_id'], []).append(dict(target=row['target'],
                    first_order=pred[row['first_id']], reverse_order=pred[row['reverse_id']], same_clip=row['same_clip']))
            categories[purpose] = source_metrics(records) if records else None
        additions = []
        for source in labels['policies']:
            sid = source['id']
            with np.load(bound(source['native']), allow_pickle=False) as f:
                cells = f['groups']; baseline = f['baseline']
            with np.load(bound(source['groups']), allow_pickle=False) as f:
                groups = f['native_group']
            votes = [dict(start_group=c['clip']['start_group'], candidate_first=pred[c['first_id']],
                          anchor_first=pred[c['reverse_id']]) for c in source['candidates']]
            decision = select_addition(groups, cells, baseline, votes)
            mask = apply_selection(baseline, decision)
            require(np.all(mask[baseline]), 'All original B0 frames preserved under new policy')
            human_ref = next(r for r in labels['original_labels'] if r['id'] == sid)['annotation_array']
            raw_human = np.load(bound(human_ref), allow_pickle=False)
            require(raw_human.ndim == 2 and len(raw_human) == len(mask) and np.isfinite(raw_human).all(),
                    'Original all-rater human native length, no padding/truncation/missing-to-negative')
            human = raw_human > 0
            before = old_ranking[sid]['old_B0_paired_f1']
            if np.array_equal(mask, baseline):
                after = before
            else:
                truth = human.sum(0); denominator = int(mask.sum())+truth
                after = float(np.divide(2*(mask[:,None]&human).sum(0), denominator,
                    out=np.ones(len(truth), dtype=float), where=denominator != 0).mean())
            p = out/(role+'_'+sid+'.policy.json')
            save(p, dict(source_sha256=source['source_sha256'], decision=decision,
                         old_baseline_scope=source['baseline_scope']))
            additions.append(dict(id=sid, source_sha256=source['source_sha256'], policy=ref(p),
                baseline_F1=before, proposal_F1=after, delta_F1=after-before,
                added_native_frames=int(mask.sum()-baseline.sum()), removed_native_frames=0,
                selected=decision['selected'], anchor=decision['anchor']))
        summaries[role] = dict(pair_metrics=categories, policies=additions,
            B0_macro_F1=float(np.mean([r['baseline_F1'] for r in additions])),
            proposal_macro_F1=float(np.mean([r['proposal_F1'] for r in additions])),
            macro_delta_F1=float(np.mean([r['delta_F1'] for r in additions])),
            worst_source_F1_delta=min(r['delta_F1'] for r in additions),
            added_native_frames=sum(r['added_native_frames'] for r in additions),
            changed_sources=sum(r['added_native_frames'] > 0 for r in additions))
    constants = {}
    generic = [r for r in labels['pairs'] if r['purpose'] == 'FIXED_GENERIC_PAIR']
    for name, constant in [('TRAIN_SOURCE_EQUAL_PRIOR', prior), ('ALWAYS_TIE', [0.,0.,1.])]:
        values = {}
        for row in generic:
            values.setdefault(row['source_id'], []).append((brier(constant, row['target']) +
                brier(swapped_distribution(constant), row['target']))/2)
        constants[name] = dict(probabilities=np.asarray(constant).tolist(),
            source_equal_generic_Brier=float(np.mean([np.mean(v) for v in values.values()])))
    save(out/'result.json', dict(status='COMPLETE_ONE_FIXED200_PAIR_LANGUAGE_COMPARISON_NOT_AUTOMATIC_PRODUCTION',
        summaries=summaries, constant_controls=constants, original_output_QA=roles,
        evaluation_targets=gpu_reg['evaluation_targets'], original_external_baseline='B0_NOT_COMPLETE40.47',
        historical_exposure=True, independent_blind_confirmation=False,
        all_raters_used=True, official_joint_metric=False, production_admitted=False,
        no_threshold_or_model_selection_scan=True))
    require(not torch.cuda.is_initialized(), 'CPU comparison cannot initialize CUDA')


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('mode', choices=['evaluate'])
    p.add_argument('--root', type=Path, required=True); a = p.parse_args()
    if a.mode == 'evaluate': evaluate(a.root)
    else: qa(a.root, a.mode)
