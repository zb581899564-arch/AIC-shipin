"""Build one policy artifact, preserving original native indices and field boxes."""
import subprocess
import sys
import zipfile
from fractions import Fraction
from routing_package63_common import ROOT, RUN, FULL_PARAMETERS, canonical, frame_boxes, write_lines, read, ref, save


def validate_native(rows, selected, clocks, baseline, routed, policy):
    if len(rows) != 426 or {row['video_id'] for row in rows} != {str(i) for i in range(426)}:
        raise ValueError('Candidate must contain all426 source records')
    boxes = frame_boxes(rows); old = frame_boxes(baseline)
    if set(boxes) != selected or any(boxes[k] != old[k] for k in boxes.keys() & old.keys()):
        raise ValueError('Actual frame set or retained40.47 boxes changed')
    old_by_id = {row['video_id']: row for row in baseline}
    for row in rows:
        sid = row['video_id']; clock = clocks[sid]
        pts = [Fraction(p) for p in clock['normalized_exact_pts']]
        if not pts or any(a >= b for a, b in zip(pts, pts[1:])) or Fraction(clock['physical_end_exact']) <= pts[-1]:
            raise ValueError('Original nativePTS clock/end is not valid')
        if any(type(p['frame']) is not int or not 0 <= p['frame'] < len(pts) for p in row['predictions']):
            raise ValueError('Candidate frame outside original native clock')
        if sid not in routed and row['predictions'] != old_by_id[sid]['predictions']:
            raise ValueError('Nonrouted source must preserve original40.47 exactly')
        if policy == 'source_rerank' and len(row['predictions']) != len(old_by_id[sid]['predictions']):
            raise ValueError('Rerank must keep exact original per-source coverage')
    if policy == 'source_remove' and not boxes.keys() <= old.keys():
        raise ValueError('Removal policy added native frames')
    return boxes, old


def build(policy, union_rows, union_provenance, selected_rows, selected, clocks, baseline, routed, metadata, history):
    rows = [dict(video_id=row['video_id'], targetRatioWH=row['targetRatioWH'],
        predictions=[p for p in row['predictions'] if (row['video_id'], p['frame']) in selected],
        model_params_b=FULL_PARAMETERS / 1e9) for row in union_rows]
    provenance = [row for row in union_provenance if (row['video_id'], row['source_frame']) in selected]
    boxes, old = validate_native(rows, selected, clocks, baseline, routed, policy)
    digest = canonical(rows)
    if digest in history:
        raise ValueError('Actual predictions duplicate baseline/history or another new candidate')
    if not boxes.keys() ^ old.keys():
        raise ValueError('No actual frame-selection change; accounting fields are not a new candidate')
    output = ROOT / policy; output.mkdir()
    write_lines(output / 'predictions.jsonl', rows)
    write_lines(output / 'selected.jsonl', selected_rows)
    write_lines(output / 'provenance.jsonl', provenance)
    save(output / 'metadata.json', metadata)
    name = 'SPORT_ROUTE_RERANK_8B' if policy == 'source_rerank' else 'SPORT_ROUTE_REMOVE_8B'
    pending = output / ('candidate_' + name + '.PENDING.zip')
    with zipfile.ZipFile(pending, 'x', zipfile.ZIP_DEFLATED) as archive:
        archive.write(output / 'predictions.jsonl', 'predictions.jsonl')
    validator = RUN / 'baseline_a_pts_v1/vendor/independent_validate.py'
    with (output / 'independent_validation.log').open('x') as log:
        subprocess.run([sys.executable, str(validator), '--strict-loader-root',
            str(RUN / 'baseline_a_pts_v1/vendor/frozen_strict_loader'),
            '--metadata', str(output / 'metadata.json'), '--selected', str(output / 'selected.jsonl'),
            '--predictions', str(output / 'predictions.jsonl'), '--provenance', str(output / 'provenance.jsonl'),
            '--zip', str(pending), '--report', str(output / 'independent_validation.json')],
            stdout=log, stderr=subprocess.STDOUT, check=True)
    checks = read(output / 'independent_validation.json')['checks']
    if len(checks) != 11 or not all(checks.values()):
        raise ValueError('Independent frozen11strict validation failed')
    with zipfile.ZipFile(pending) as archive:
        if archive.namelist() != ['predictions.jsonl'] or archive.testzip() is not None:
            raise ValueError('ZIP membership or CRC invalid')
        import hashlib
        if hashlib.sha256(archive.read('predictions.jsonl')).hexdigest() != ref(output / 'predictions.jsonl')['sha256']:
            raise ValueError('ZIP member differs from reviewed JSONL')
    final = output / ('candidate_' + name + '.zip'); pending.rename(final)
    result = dict(policy=policy, ZIP=ref(final), member=ref(output / 'predictions.jsonl'),
        canonical_sha256=digest, records=426, selected_frames=len(boxes), added_frames=len(boxes.keys() - old.keys()),
        removed_frames=len(old.keys() - boxes.keys()), empty_sources=sum(not row['predictions'] for row in rows),
        changed_sources=sum(row['predictions'] != old_row['predictions'] for row, old_row in
            zip(sorted(rows, key=lambda r: r['video_id']), sorted(baseline, key=lambda r: r['video_id']))),
        retained_baseline_boxes_exact=True, nonrouted_sources_exact=True, nativePTS=True,
        actual_model_parameters=FULL_PARAMETERS, independent11strict=True,
        official_score='UNKNOWN', website_submitted=False,
        limitation='One exposed held sport supports this narrow route; global performance and class-confusion effects remain unknown')
    save(output / 'completion.json', result); history.add(digest)
    return result
