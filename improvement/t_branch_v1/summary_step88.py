"""Accumulate every original review before one publisher-balanced update."""
from fractions import Fraction
from pathlib import Path
import subprocess
import os
import math

import torch
import torch.nn.functional as functional

from summary_actor88 import digest
from summary_data88 import actual_suffix
from summary_recovery88 import first_optimizer_witness, gradient_state, publisher_checkpoint
from t_io import ROOT, WORK, identity, read, save

OUT = ROOT / 'summary_train88'
TEMP = Path('/dev/shm/aic_T_summary_train88')
PY = WORK / 'env/qwen3vl_isolated_20260910/bin/python'


def first_TF_QA(logits, suffix, row, signature, selected, norm, loss, weight):
    path = TEMP / 'first_TF_full_logits.pt'
    with path.open('xb') as stream:
        torch.save(dict(logits=logits.detach().cpu()), stream)
    save(OUT / 'first_TF_raw.json', dict(accepted_target=row,
        causal_signature=signature, target_ids=suffix['targets'][0].tolist(),
        selected_logp=(selected - norm).detach().cpu().tolist(), unweighted_NLL=float(loss.detach()),
        publisher_review_weight=str(weight), temporary_full_logits=identity(path),
        inference_prefix_contains_no_human_reference=True, role='new_summary_only',
        actual_teacher_forcing_contains_previous_human_targets=True))
    child = subprocess.run([str(PY), '-B', str(Path(__file__).with_name('summary_teacher88_cpu.py')),
        str(OUT / 'first_TF_raw.json')], text=True, capture_output=True,
        env=dict(os.environ, CUDA_VISIBLE_DEVICES='', OMP_NUM_THREADS='2', MKL_NUM_THREADS='2'))
    if child.returncode:
        save(OUT / 'first_TF_CPU_failure.json', dict(exit_code=child.returncode,
            stdout=child.stdout, stderr=child.stderr, no_optimizer_step_yet=True))
        raise RuntimeError('First actual8B full-target CPU replay failed')


def one_review(model, rt, prefix, row, sid, episode, micro, weight, trainable, checkpoint):
    if model.active_adapter != 'summary':
        raise ValueError('An actual content teacher-forced call used the wrong adapter role')
    suffix, signature = actual_suffix(prefix, row, rt)
    values = {k: suffix[k].cuda() for k in ['input_ids', 'attention_mask']}
    output = model(**values, logits_to_keep=suffix['logits_to_keep'], use_cache=False, return_dict=True)
    logits = output.logits[0].float(); targets = suffix['targets'][0].cuda()
    if logits.shape[0] != len(targets) or not torch.isfinite(logits).all():
        raise ValueError('Actual summary target logit shape or finiteness differs')
    loss = functional.cross_entropy(logits, targets, reduction='mean')
    selected = logits.gather(1, targets[:, None]).squeeze(1); norm = torch.logsumexp(logits, dim=-1)
    scalar = float(loss.detach()); projected = float((norm - selected).detach().mean())
    if not math.isfinite(scalar) or not math.isclose(scalar, projected, rel_tol=2e-5, abs_tol=2e-5):
        raise ValueError('Actual full-vocabulary CE and target-projection mean differ')
    if micro == 1:
        first_TF_QA(logits, suffix, row, signature, selected, norm, loss, weight)
    logp = (selected - norm).detach().cpu().tolist()
    (loss * float(weight)).backward()
    cursor = dict(episode=episode, source=sid, original_review_row=row['original_row'], micro=micro)
    state = gradient_state(TEMP / ('G%03d.pt' % micro), trainable, cursor, checkpoint)
    path = OUT / 'micro' / ('M%03d.json' % micro)
    save(path, dict(cursor=cursor, actual_target=row, causal_signature=signature,
        selected_target_logp=logp, mean_NLL=scalar, publisher_update_weight=str(weight),
        weighted_NLL=scalar * float(weight), exact_recovery_gradient=state,
        original_whole_target_no_truncation=True, gradient_before_optimizer=True))
    print('SUMMARY88_FIRST_TARGET_BACKWARD', micro, sid, row['original_row'], scalar, flush=True)
    return identity(path)


def one_publisher(model, rt, data, prefixes, sids, publisher, episode, micro,
                  optimizer, trainable, checkpoint):
    before_digest = digest(model); optimizer.zero_grad(set_to_none=True)
    refs = []; weight_total = Fraction(0)
    for sid in sids:
        for row in data['source_targets'][sid]:
            weight = Fraction(row['global_publisher_source_reviewer_weight']) * 5
            weight_total += weight; micro += 1
            refs.append(one_review(model, rt, prefixes[sid], row, sid, episode, micro,
                                   weight, trainable, checkpoint))
    if weight_total != 1 or digest(model) != before_digest:
        raise ValueError('Publisher denominator or pre-update parameter constancy differs')
    if any(p.grad is not None for name, p in model.named_parameters()
           if '.lora_A.summary.' not in name and '.lora_B.summary.' not in name):
        raise ValueError('Content gradient reached protected BASE/TIME/vision parameters')
    norm = float(torch.nn.utils.clip_grad_norm_([p for _, p in trainable], 1., error_if_nonfinite=True))
    clipped = gradient_state(TEMP / ('clipped_E%02d.pt' % episode), trainable,
                             dict(episode=episode, micro=micro, before_optimizer=True), checkpoint)
    if not math.isfinite(norm) or norm <= 0 or clipped['norm_float64'] > 1.00002:
        raise ValueError('Complete publisher has no finite nonzero clipped gradient')
    first_before = {name: p.detach().cpu().clone() for name, p in trainable} if episode == 1 else None
    optimizer.step(); after_digest = digest(model)
    if before_digest == after_digest:
        raise ValueError('Actual publisher optimizer step changed no content-adapter value')
    witness = first_optimizer_witness(OUT / 'first_optimizer_witness.pt', first_before, clipped, trainable) if episode == 1 else None
    checkpoint = publisher_checkpoint(TEMP / ('publisher_E%02d.pt' % episode), model, optimizer,
                                     episode, dict(completed_episode=episode, completed_micro=micro))
    path = OUT / 'publisher' / ('E%02d.json' % episode)
    save(path, dict(episode=episode, publisher=publisher, original_sources=sids, all_original_reviews=refs,
        optimizer_updates=1, before=before_digest, after=after_digest, norm_before_clip=norm,
        clipped_gradient=clipped, first_optimizer_witness=witness, recovery_checkpoint=checkpoint,
        final_checkpoint_selection_only=True))
    print('SUMMARY88_PUBLISHER_UPDATE', episode, micro, publisher, flush=True)
    return identity(path), checkpoint, micro
