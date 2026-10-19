"""One registered CPU-only signed correction pilot; no production entry.

Every outer fold adopts only its own previously trained LM head. Its new head
is fitted on that same training fold, never on held-source references. Earlier
OOF masks from OTHER folds must not become training priors (indirect leakage).
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import sys
import traceback


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def write(path, value):
    with Path(path).open('x') as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def main(root):
    import numpy as np
    import torch
    from torch.nn import functional as F

    p = read(root / 'protocol.json')
    require(p['schema'] == 'SIGNED_LM_ADOPTED_FEATURES_PILOT_V1', 'Protocol schema')
    require(root == Path(p['root']), 'Explicit independent root')
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU child only')
    for ref in p['bound_files']:
        require(sha(ref['path']) == ref['sha256'], 'Adopted binding changed: ' + ref['path'])
    old = Path(p['semantic_root'])
    sys.path.insert(0, str(old / 'head_code09'))
    from semantic_oof09 import transform
    from monotone_head06 import ResidualHead as FrozenLMHead
    from monotone_head06 import native_prediction as monotone_prediction
    from score_residual_head_v1.contracts import build_contract
    from score_residual_head_v1.head import ResidualHead, unit_logits, native_prediction

    torch.set_num_threads(p['CPU_threads'])
    proto = read(old / 'protocol.json')
    prior = Path(proto['prior_root'])
    adopted = read(old / 'semantic_oof09/LM/result.json')
    require(adopted['passed'] is True, 'Actual successful monotone predecessor')
    require(read(old / 'semantic_oof09/independent_output_QA.json')['source_count'] == 25,
            'Adopt existing first output QA, do not repeat multimodal QA')
    data = {}
    for source in proto['sources']:
        sid = source['id']
        n = np.load(prior / 'inputs' / sid / 'native.npz', allow_pickle=False)
        labels = np.load(prior / 'label_arrays' / (source['name'] + '.npy'), allow_pickle=False) > 0
        require(labels.shape[0] == len(n['baseline']), 'Exact native human rows, no resampling')
        feature = read(old / 'features' / sid / 'completion.json')
        lp = old / 'features' / sid / 'language.npy'
        yp = old / 'features' / sid / 'yes_no.npy'
        require(sha(lp) == feature['language_sha256'] and sha(yp) == feature['yes_no_sha256'],
                'Existing complete feature identity')
        language, yesno = np.load(lp), np.load(yp)
        x = torch.from_numpy(transform(language, yesno, n, 'LM'))
        pts = read(prior / 'inputs' / sid / 'clock.json')['normalized_exact_pts']
        base = build_contract(n['groups'].tolist(), n['baseline'].tolist(),
                              labels.mean(1).tolist(), len(x), pts)
        data[sid] = dict(x=x, labels=labels, groups=n['groups'].tolist(), pts=pts, base=base)

    def metrics(mask, sid):
        mask = np.asarray(mask, bool)
        g = data[sid]['labels']
        count = int(mask.sum())
        counts = g.sum(0)
        require(bool((counts > 0).all()), 'No invented empty-rater quality')
        overlap = (g & mask[:, None]).sum(0)
        return dict(f1=float((2 * overlap / (count + counts)).mean()),
                    precision=float((overlap / max(1, count)).mean()),
                    recall=float((overlap / counts).mean()), selected=count)

    rows = []
    for fold in range(5):
        dst = root / ('fold%d' % fold)
        dst.mkdir()
        frozen = FrozenLMHead(12289, 8)
        frozen.load_state_dict(torch.load(old / ('semantic_oof09/LM/fold%d.pt' % fold),
                                         map_location='cpu', weights_only=True))
        frozen.requires_grad_(False)
        frozen.eval()
        train_ids = [s['id'] for s in proto['sources'] if s['fold'] != fold]
        held_ids = [s['id'] for s in proto['sources'] if s['fold'] == fold]
        inherited = read(old / ('semantic_oof09/LM/fold%d.json' % fold))['training']
        require(set(inherited['original_source_ids']) == set(train_ids),
                'Frozen predecessor must never have trained on this held fold')
        contracts, counts, priors = {}, {}, {}
        for sid, d in data.items():
            with torch.no_grad():
                mask = monotone_prediction(frozen(d['x']), d['base'])
            if sid in held_ids:
                saved = np.load(old / ('semantic_oof09/LM/' + sid + '_native_prediction.npy'))
                require(np.array_equal(saved, mask), 'Held source exactly adopts old OOF prediction')
            priors[sid] = mask
            c = build_contract(d['groups'], list(mask), d['labels'].mean(1).tolist(),
                               len(d['x']), d['pts'])
            contracts[sid] = c
            count = np.zeros((len(c.n), d['labels'].shape[1]), np.float32)
            np.add.at(count, np.asarray(c.native_unit), d['labels'].astype(np.float32))
            counts[sid] = torch.from_numpy(count)
        with torch.random.fork_rng(devices=[]):
            torch.manual_seed(p['seed'])
            model = ResidualHead(12289, p['hidden_dim'])
        for sid, d in data.items():
            require(native_prediction(model(d['x']), contracts[sid]) == tuple(priors[sid]),
                    'Zero signed residual must reproduce predecessor, including every native frame')
        optimizer = torch.optim.AdamW(model.parameters(), lr=p['learning_rate'], weight_decay=0.)
        history = []
        for update in range(p['updates_per_fold']):
            optimizer.zero_grad(set_to_none=True)
            losses = []
            for sid in train_ids:
                c = contracts[sid]
                z = unit_logits(model(data[sid]['x']), c, margin=1.)
                weights = torch.tensor(c.n, dtype=z.dtype)
                g = counts[sid]
                target = g.mean(1) / weights
                bce = (F.binary_cross_entropy_with_logits(z, target, reduction='none') * weights).sum() / weights.sum()
                prob = z.sigmoid()
                selected = (prob * weights).sum()
                # Exact mean of the raters' soft F1 ratios, not pooled-rater F1.
                paired = 2 * (prob[:, None] * g).sum(0) / (selected + g.sum(0))
                losses.append(bce + p['score_weight'] * (1 - paired.mean()))
            objective = torch.stack(losses).mean()
            require(bool(torch.isfinite(objective)), 'Finite CPU training objective')
            objective.backward()
            require(all(v.grad is None or bool(torch.isfinite(v.grad).all()) for v in model.parameters()),
                    'Finite signed-head gradients')
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.)
            optimizer.step()
            history.append(float(objective.detach()))
        torch.save(model.state_dict(), dst / 'head.pt')
        for sid in held_ids:
            with torch.no_grad():
                mask = native_prediction(model(data[sid]['x']), contracts[sid])
            b, a = metrics(priors[sid], sid), metrics(mask, sid)
            before, after = np.asarray(priors[sid], bool), np.asarray(mask, bool)
            row = dict(id=sid, fold=fold, before=b, after=a, delta=a['f1'] - b['f1'],
                       added=int((after & ~before).sum()), removed=int((before & ~after).sum()))
            np.save(dst / (sid + '_prediction.npy'), after)
            rows.append(row)
        write(dst / 'training.json', dict(training_ids=train_ids, held_ids=held_ids,
              updates=p['updates_per_fold'], objective_history=history,
              inherited_head_sha256=sha(old / ('semantic_oof09/LM/fold%d.pt' % fold)),
              not_using_other_folds_OOF_masks_as_training_priors=True))
        print(json.dumps(dict(fold=fold, macro_delta=float(np.mean([x['delta'] for x in rows if x['fold'] == fold])))), flush=True)
    deltas = [float(np.mean([x['delta'] for x in rows if x['fold'] == f])) for f in range(5)]
    macro = float(np.mean([x['delta'] for x in rows]))
    precision = float(np.mean([x['after']['precision'] - x['before']['precision'] for x in rows]))
    recall = float(np.mean([x['after']['recall'] - x['before']['recall'] for x in rows]))
    g = p['gates']
    gates = dict(macro=macro >= g['macro_gain_min'], folds=min(deltas) >= g['fold_delta_min'],
                 worst_source=min(x['delta'] for x in rows) >= -g['source_loss_max'],
                 precision=precision >= 0, recall=recall >= 0,
                 added_sources=sum(x['added'] > 0 for x in rows) >= g['mechanism_sources_min'],
                 removed_sources=sum(x['removed'] > 0 for x in rows) >= g['mechanism_sources_min'],
                 nonempty=all(x['after']['selected'] > 0 for x in rows))
    require(not torch.cuda.is_initialized(), 'No CUDA context in CPU pilot')
    result = dict(status='PASS_SIGNED_LM_RESEARCH_PILOT_NEEDS_TRANSFER_REFERENCE' if all(gates.values())
                  else 'STOP_SIGNED_LM_PILOT_REJECTED', gates=gates, macro_delta=macro,
                  fold_deltas=deltas, precision_delta=precision, recall_delta=recall, sources=rows,
                  new_CPU_updates=5 * p['updates_per_fold'], new_multimodal_forwards=0,
                  new_generation_calls=0, new_decodes=0, production_admitted=False,
                  new_head_parameters=model.parameter_count,
                  planned_inference_resident_parameters=8782557449 + model.parameter_count,
                  scope=p['scope'], final_head_trained=False)
    write(root / 'result.json', result)
    write(root / 'completion.json', dict(status=result['status'], result_sha256=sha(root / 'result.json'),
          new_submission_ZIPs=0, production_admitted=False, utc=datetime.datetime.now(datetime.timezone.utc).isoformat()))
    print(json.dumps({k: v for k, v in result.items() if k != 'sources'}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True)
    root = Path(parser.parse_args().root)
    try:
        main(root)
    except Exception as error:
        if not (root / 'failure.json').exists():
            write(root / 'failure.json', dict(error=repr(error), traceback=traceback.format_exc(),
                  preserve_success=True, no_automatic_restart=True))
        raise
