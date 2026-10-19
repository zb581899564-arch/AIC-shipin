"""One frozen CPU-only risk package: keep baseline unless both saved tasks vote0."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import traceback
import zipfile


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(8 << 20), b''):
            h.update(block)
    return h.hexdigest()


def bound(ref):
    p = Path(ref['path'])
    assert p.is_absolute() and sha(p) == ref['sha256'], 'Changed frozen file ' + str(p)
    return p


def save(path, value):
    with Path(path).open('x') as f:
        json.dump(value, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')


def lines(path):
    return [json.loads(l) for l in Path(path).read_text().splitlines() if l.strip()]


def jsonlines(path, rows):
    with Path(path).open('x') as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, separators=(',', ':'), allow_nan=False) + '\n')


def canonical(rows):
    value = [{k: r[k] for k in ('video_id', 'targetRatioWH', 'predictions')}
             for r in sorted(rows, key=lambda x: x['video_id'])]
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def main(root):
    import numpy as np
    reg = read(root / 'registration.json')
    assert reg['schema'] == 'CONSENSUS_VETO_LAST_RISK_20261016_V1'
    assert reg['selection'] == 'BASELINE_FRAME_AND_GLOBAL_OR_PAYOFF'
    assert reg['actual_total_parameters'] == 8782557449 <= 9000000000
    assert reg['offline_effect_validation'] is False and reg['online_effect'] == 'UNKNOWN'
    assert read(bound(reg['rule_check']))['automatic_local_inference_risk_scope_allowed'] is True
    assert read(bound(reg['generation_terminal']))['status'] == 'GLOBAL_LOCAL_TWO_RISK_DIRECTIONS_NATURAL_COMPLETE'
    resource = read(bound(reg['GPU_resource']))
    assert resource['status'] == 'completed' and resource['exit_code'] == 0
    assert read(bound(reg['unique_resource']))['unique_terminal_count'] == 1
    masks = read(bound(reg['output_QA']))
    assert masks['status'] == 'PASS_ALL426_GLOBAL_LOCAL_BINARY_OUTPUT_QA'
    assert [s['id'] for s in masks['sources']] == [str(i) for i in range(426)]
    baseline = bound(reg['baseline'])
    assert reg['baseline']['sha256'] == 'b37c4a2e6593fc800f54ecce2f860fee5e7d5dc74e17ce280f9ee6722afbccd3'
    with zipfile.ZipFile(baseline) as z:
        assert z.namelist() == ['predictions.jsonl'] and z.testzip() is None
        base = [json.loads(l) for l in z.read('predictions.jsonl').splitlines()]
    before = {(r['video_id'], p['frame']): p['bboxes'] for r in base for p in r['predictions']}
    assert len(base) == 426 and len(before) == 123506
    base_frames = {r['video_id']: {p['frame'] for p in r['predictions']} for r in base}
    selected = set()
    decisions = []
    for source in masks['sources']:
        sid = source['id']
        with np.load(bound(dict(path=source['native_path'], sha256=source['native_sha256'])), allow_pickle=False) as native:
            groups = native['groups'].copy()
        a = np.load(bound(dict(path=source['global_mask_path'], sha256=source['global_sha256'])), allow_pickle=False)
        b = np.load(bound(dict(path=source['payoff_mask_path'], sha256=source['payoff_sha256'])), allow_pickle=False)
        assert a.dtype == b.dtype == np.bool_ and a.shape == b.shape == (source['cells'],)
        assert groups.ndim == 1 and groups.dtype.kind in 'iu' and groups.min() == 0 and groups.max() + 1 == len(a)
        assert bool((np.diff(groups) >= 0).all())
        keep = set(np.flatnonzero((a | b)[groups]).tolist()) & base_frames[sid]
        selected.update((sid, f) for f in keep)
        decisions.append(dict(id=sid, baseline_frames=len(base_frames[sid]), kept=len(keep),
                              removed=len(base_frames[sid] - keep), global_sha256=source['global_sha256'],
                              payoff_sha256=source['payoff_sha256'], native_sha256=source['native_sha256']))
    assert selected <= set(before)
    field_inputs = read(bound(reg['field_inputs']))
    paths = {k: bound(v) for k, v in field_inputs['source_field_files'].items()}
    field = lines(paths['field_frames.jsonl'])
    field_map = {(r['video_id'], r['source_frame']): r for r in field}
    assert len(field_map) == len(field) and selected <= set(field_map)
    metadata = read(bound(field_inputs['metadata']))
    manifest = read(bound(field_inputs['source_manifest']))
    run = Path(reg['run_root'])
    sys.path[:0] = [str(run / 'b_score_aligned_package_v4'), str(run / 'baseline_a_pts_v1'),
                   str(run / 'baseline_a_pts_v1/vendor')]
    from field_contract import compose_from_field
    from pts_contract import legacy_manifest
    chosen = [field_map[k] for k in sorted(selected)]
    rows, provenance = compose_from_field(legacy_manifest(manifest), chosen,
        lines(paths['field_shots.jsonl']), lines(paths['anchor_requests.jsonl']), lines(paths['anchor_output.jsonl']))
    for row in rows:
        row['model_params_b'] = reg['actual_total_parameters'] / 1e9
    after = {(r['video_id'], p['frame']): p['bboxes'] for r in rows for p in r['predictions']}
    assert set(after) == selected and all(box == before[k] for k, box in after.items())
    digest = canonical(rows)
    history = set(reg['historical_canonical_sha256']) | {canonical(base)}
    for ref in reg['current_candidate_completions']:
        history.add(read(bound(ref))['canonical_sha256'])
    assert digest not in history and set(after) != set(before), 'No real distinct prediction; do not create ZIP'
    jsonlines(root / 'predictions.jsonl', rows)
    jsonlines(root / 'selected.jsonl', chosen)
    jsonlines(root / 'provenance.jsonl', provenance)
    save(root / 'metadata.json', metadata)
    save(root / 'decision_receipt.json', dict(rule=reg['selection'], sources=decisions,
         same_model_correlated_two_tasks=True, new_model_calls=0, new_optimizer_updates=0,
         added=0, removed=len(before) - len(after), original_retained_boxes_exact=True,
         all_zero_task_results_are_valid=True, failure_to_zero=False, registration_sha256=sha(root / 'registration.json')))
    pending = root / 'candidate_CONSENSUS_VETO.PENDING.zip'
    with zipfile.ZipFile(pending, 'x', zipfile.ZIP_DEFLATED) as z:
        z.write(root / 'predictions.jsonl', 'predictions.jsonl')
    validator = run / 'baseline_a_pts_v1/vendor/independent_validate.py'
    subprocess.run([sys.executable, str(validator), '--strict-loader-root',
        str(run / 'baseline_a_pts_v1/vendor/frozen_strict_loader'), '--metadata', str(root / 'metadata.json'),
        '--selected', str(root / 'selected.jsonl'), '--predictions', str(root / 'predictions.jsonl'),
        '--provenance', str(root / 'provenance.jsonl'), '--zip', str(pending),
        '--report', str(root / 'independent_validation.json')], check=True)
    checks = read(root / 'independent_validation.json')['checks']
    assert len(checks) == 11 and all(checks.values())
    with zipfile.ZipFile(pending) as z:
        assert z.namelist() == ['predictions.jsonl'] and z.testzip() is None
        assert hashlib.sha256(z.read('predictions.jsonl')).hexdigest() == sha(root / 'predictions.jsonl')
    final = root / 'candidate_CONSENSUS_VETO.zip'
    pending.rename(final)
    save(root / 'completion.json', dict(status='PASS_ENGINEERING_UNKNOWN_ONLINE_FINAL_RISK',
         direction='CONSENSUS_VETO', path=str(final), bytes=final.stat().st_size, sha256=sha(final),
         member_sha256=sha(root / 'predictions.jsonl'), canonical_sha256=digest, records=426, frames=len(after),
         added=0, removed=len(before) - len(after), empty_sources=sum(not r['predictions'] for r in rows),
         changed_sources=sum(x['removed'] > 0 for x in decisions), retained_original_boxes=True,
         actual_total_parameters=reg['actual_total_parameters'], independent11strict=True,
         new_model_calls=0, new_training_updates=0, offline_effect_validation=False,
         online_effect='UNKNOWN', website_submitted=False, same_model_correlated_two_tasks=True))
    print(json.dumps(read(root / 'completion.json')), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', required=True)
    root = Path(parser.parse_args().root)
    try:
        main(root)
    except BaseException as error:
        if not (root / 'failure.json').exists():
            save(root / 'failure.json', dict(error=repr(error), traceback=traceback.format_exc(),
                 preserve_success=True, no_automatic_restart=True, failure_to_zero=False))
        raise
