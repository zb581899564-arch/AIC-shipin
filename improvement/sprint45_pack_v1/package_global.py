"""Render two preregistered automatic masks; no effect evaluation or model call."""
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
        for part in iter(lambda: f.read(8 << 20), b''):
            h.update(part)
    return h.hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def save(path, data):
    with Path(path).open('x') as f:
        json.dump(data, f, ensure_ascii=False, indent=2, allow_nan=False)
        f.write('\n')


def jsonlines(path, rows):
    with Path(path).open('x') as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, separators=(',', ':'), allow_nan=False) + '\n')


def lines(path):
    return [json.loads(x) for x in Path(path).read_text().splitlines() if x.strip()]


def bound(ref):
    p = Path(ref['path'])
    require(p.is_absolute() and p.is_file() and sha(p) == ref['sha256'], 'Bound file changed: ' + str(p))
    return p


def canonical(rows):
    values = [{k: r[k] for k in ('video_id', 'targetRatioWH', 'predictions')}
              for r in sorted(rows, key=lambda r: r['video_id'])]
    return hashlib.sha256(json.dumps(values, sort_keys=True, separators=(',', ':'),
                                    allow_nan=False).encode()).hexdigest()


def main(model_root, root, registration):
    import numpy as np
    reg = read(registration)
    require(reg['schema'] == 'SPRINT45_GLOBAL_TWO_RISK_PACKAGES_V1' and
            Path(reg['out_root']) == root and Path(reg['model_root']) == model_root,
            'Independent package registration')
    require(reg['offline_effect_gate_required'] is False and reg['online_effect'] == 'UNKNOWN',
            'Disclose unvalidated online effect')
    require(reg['actual_total_parameters'] == 8782557449 <= 9_000_000_000,
            'Full reproduction base+TIME+baseline semantic auxiliary')
    rules = read(bound(reg['official_rule_check']))
    require(rules['automatic_local_inference_risk_scope_allowed'] is True,
            'Current rule interpretation required, no test labels/teacher/training')
    resource = read(model_root / 'GPU_resource.json')
    require(resource['status'] == 'completed' and resource['exit_code'] == 0 and
            read(model_root / 'unique_resource_verified.json')['unique_terminal_count'] == 1,
            'Natural unique shared-GPU terminal must precede packaging')
    masks = read(model_root / 'output_acceptance.json')
    require(masks['status'] == 'PASS_ALL426_GLOBAL_LOCAL_BINARY_OUTPUT_QA' and len(masks['sources']) == 426,
            'All real output token/native mapping QA must precede packaging')
    inputs = read(bound(reg['source_field_inputs']))
    field_paths = {name: bound(ref) for name, ref in inputs['source_field_files'].items()}
    metadata_path = bound(inputs['metadata'])
    metadata = read(metadata_path)
    manifest = read(bound(inputs['source_manifest']))
    field = lines(field_paths['field_frames.jsonl'])
    field_map = {(r['video_id'], r['source_frame']): r for r in field}
    require(len(field_map) == len(field), 'No duplicate frozen spatial domain')
    baseline = bound(reg['baseline'])
    require(sha(baseline) == 'b37c4a2e6593fc800f54ecce2f860fee5e7d5dc74e17ce280f9ee6722afbccd3',
            'Protected current user40.47 package')
    with zipfile.ZipFile(baseline) as z:
        require(z.namelist() == ['predictions.jsonl'] and z.testzip() is None, 'Current original archive')
        base = [json.loads(l) for l in z.read('predictions.jsonl').splitlines()]
    b = {(r['video_id'], p['frame']): p['bboxes'] for r in base for p in r['predictions']}
    require(len(base) == 426 and {r['video_id'] for r in base} == {str(i) for i in range(426)} and
            set(b) <= set(field_map), 'Complete baseline/frame domain')
    run = Path(reg['run_root'])
    sys.path[:0] = [str(run / 'b_score_aligned_package_v4'), str(run / 'baseline_a_pts_v1'),
                   str(run / 'baseline_a_pts_v1/vendor')]
    from field_contract import compose_from_field
    from pts_contract import legacy_manifest
    history = set(reg['historical_canonical_sha256']) | {canonical(base)}
    results = []
    for arm, name in [('global', 'GLOBAL_CONTEXT'), ('payoff', 'EVENT_PAYOFF')]:
        out = root / name
        out.mkdir()
        selected = set(b)
        excluded = 0
        source_ids = []
        for source in masks['sources']:
            sid = source['id']
            source_ids.append(sid)
            native = np.load(bound(dict(path=source['native_path'], sha256=source['native_sha256'])))
            path = bound(dict(path=source[arm + '_mask_path'], sha256=source[arm + '_sha256']))
            mask = np.load(path, allow_pickle=False)
            require(mask.dtype == np.bool_ and mask.shape == (source['cells'],), 'Complete actual boolean cell mask')
            groups = native['groups']
            require(groups.ndim == 1 and int(groups.max()) + 1 == len(mask), 'Exact native occupied cell mapping')
            for frame in np.flatnonzero(mask[groups]).tolist():
                key = (sid, frame)
                if key in field_map:
                    selected.add(key)
                else:
                    excluded += 1
        require(len(source_ids) == len(set(source_ids)) == 426 and set(source_ids) == {str(i) for i in range(426)},
                'All426 native sources, including any legitimate model-zero source')
        chosen = [field_map[k] for k in sorted(selected)]
        rows, provenance = compose_from_field(legacy_manifest(manifest), chosen,
            lines(field_paths['field_shots.jsonl']), lines(field_paths['anchor_requests.jsonl']),
            lines(field_paths['anchor_output.jsonl']))
        for row in rows:
            row['model_params_b'] = reg['actual_total_parameters'] / 1e9
        n = {(r['video_id'], p['frame']): p['bboxes'] for r in rows for p in r['predictions']}
        require(set(n) == selected and set(b) <= set(n) and all(n[k] == v for k, v in b.items()),
                'All original selected native frame/box pairs retained')
        digest = canonical(rows)
        if digest in history:
            record = dict(status='STOP_NO_NEW_PREDICTION_FOR_THIS_DIRECTION', direction=name,
                          canonical_sha256=digest, no_ZIP_created=True, online_effect='UNKNOWN')
            save(out / 'completion.json', record)
            results.append(record)
            continue
        history.add(digest)
        jsonlines(out / 'predictions.jsonl', rows)
        jsonlines(out / 'selected.jsonl', chosen)
        jsonlines(out / 'provenance.jsonl', provenance)
        save(out / 'metadata.json', metadata)
        archive = out / ('candidate_' + name + '.PENDING.zip')
        with zipfile.ZipFile(archive, 'x', zipfile.ZIP_DEFLATED) as z:
            z.write(out / 'predictions.jsonl', 'predictions.jsonl')
        validator = run / 'baseline_a_pts_v1/vendor/independent_validate.py'
        subprocess.run([sys.executable, str(validator), '--strict-loader-root',
            str(run / 'baseline_a_pts_v1/vendor/frozen_strict_loader'), '--metadata', str(out / 'metadata.json'),
            '--selected', str(out / 'selected.jsonl'), '--predictions', str(out / 'predictions.jsonl'),
            '--provenance', str(out / 'provenance.jsonl'), '--zip', str(archive),
            '--report', str(out / 'independent_validation.json')], check=True)
        checks = read(out / 'independent_validation.json')['checks']
        require(len(checks) == 11 and all(checks.values()), 'Independent format/source/native/ZIP legality')
        with zipfile.ZipFile(archive) as z:
            require(z.testzip() is None and z.namelist() == ['predictions.jsonl'] and
                    hashlib.sha256(z.read('predictions.jsonl')).hexdigest() == sha(out / 'predictions.jsonl'),
                    'Final CRC/member integrity')
        final = out / ('candidate_' + name + '.zip')
        archive.rename(final)
        record = dict(status='PASS_ENGINEERING_UNKNOWN_ONLINE_RISK_CANDIDATE', direction=name,
            path=str(final), bytes=final.stat().st_size, sha256=sha(final),
            member_sha256=sha(out / 'predictions.jsonl'), canonical_sha256=digest,
            records=len(rows), frames=len(n), added=len(set(n) - set(b)), removed=0,
            original_boxes_retained=True, fixed_field_domain_excluded=excluded,
            actual_total_parameters=reg['actual_total_parameters'], independent11strict=True,
            offline_effect_validation=False, online_effect='UNKNOWN', website_submitted=False,
            generation_output_QA_sha256=sha(model_root / 'output_acceptance.json'))
        save(out / 'completion.json', record)
        results.append(record)
    save(root / 'completion.json', dict(status='GLOBAL_CONTEXT_TWO_DIRECTIONS_ENGINEERING_FINISHED',
        directions=results, actual_new_ZIPs=sum(x.get('independent11strict') is True for x in results),
        online_effect='UNKNOWN', website_submitted=False))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--model-root', required=True)
    parser.add_argument('--out-root', required=True)
    parser.add_argument('--registration', required=True)
    args = parser.parse_args()
    root = Path(args.out_root)
    try:
        main(Path(args.model_root), root, Path(args.registration))
    except Exception as error:
        if not (root / 'failure.json').exists():
            save(root / 'failure.json', dict(error=repr(error), traceback=traceback.format_exc(),
                 preserve_all_success=True, no_automatic_repeat=True))
        raise
