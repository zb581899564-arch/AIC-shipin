"""W01-only publisher identity / two-second-bin descriptive audit."""
import argparse
from fractions import Fraction as F
import io
import json
from pathlib import Path
import zipfile
import h5py
import numpy as np
from geometry_diagnostic import sha, write_once

EXPECTED_BINDINGS = {
    'manifest': '518062f9b012356d7fb375295e1de971dde7899d320c5d3468c84bad13c3820f',
    'clock': 'fec7990c2869b08775e2b33f4d5120693500a04b23c404e389fa1ca06f21e3e7',
    'source': '0c91bfa880e3af0e1716e7456ada0a304a97911eef76b1cd4fdce5066a52e8f7',
    'plan': '09ecb28971932bd3bf8ac275c30d0a6fd534345442f2d2ec3529fa3f8e1e4b22',
    'tsv_archive': '9f718779ba0847e9fc70a361a65037a14b8e48408a732aea699d2bccb4c4fc1f',
    'mat_archive': 'bbe67f89964e8f42179869922708ef73a56db7d4de28a22f2e602f7243ba4e9d',
}


def assert_bound(path, kind):
    if sha(path) != EXPECTED_BINDINGS[kind]:
        raise ValueError('original bound bytes changed: '+kind)


def matching_tsv_rows(archive):
    with zipfile.ZipFile(archive) as z:
        names = [n for n in z.namelist() if n.endswith('/ydata-tvsum50-anno.tsv')]
        if len(names) != 1:
            raise ValueError('annotation member identity ambiguous')
        with z.open(names[0]) as lines:
            return [line.decode().strip().split('\t') for line in lines
                    if line.startswith(b'kLxoNp-UchI\t')]


def verify_publisher(vectors, mat_vectors, mat_frames, native_frames, mat_mean):
    exact = np.array_equal(np.asarray(vectors), mat_vectors)
    mean_equal = bool(np.allclose(np.mean(mat_vectors,axis=0), mat_mean, rtol=0, atol=1e-12))
    if not exact or not mean_equal or mat_frames != native_frames:
        raise ValueError('publisher TSV/MAT, mean or source-frame count differs')
    return exact, mean_equal


def run(root, output):
    root = Path(root)
    iteration = root/'reports/annotation_iteration_20261010'
    observations = iteration/'slot6_silver24_v1/observations/00_kLxoNp-UchI_W01'
    manifest_path, clock_path = observations/'manifest.json', observations/'native_clock.json'
    assert_bound(manifest_path,'manifest')
    assert_bound(clock_path,'clock')
    assert_bound(iteration/'slot6_silver24_v1/source_window_plan.json','plan')
    manifest = json.loads(manifest_path.read_text(encoding='utf-8-sig'))
    clock = json.loads(clock_path.read_text(encoding='utf-8-sig'))
    if manifest['source_id'] != 'kLxoNp-UchI' or manifest['role'] != 'train':
        raise ValueError('only registered exposed training W01 is admitted')
    if manifest['domain_global_seconds_exact'] != ['30', '60']:
        raise ValueError('W01 exact domain changed')
    assert_bound(manifest['source_path'],'source')
    if manifest['source_sha256'] != EXPECTED_BINDINGS['source']:
        raise ValueError('source video SHA mismatch')
    ordinals = [r['source_ordinal'] for r in clock]
    if len(clock) != 899 or ordinals != list(range(900, 1799)):
        raise ValueError('fixed W01 native-clock coverage changed')
    times = [F(r['global_seconds_exact']) for r in clock]
    if any(not (30 <= t < 60) for t in times) or any(a >= b for a,b in zip(times, times[1:])):
        raise ValueError('clock order/domain invalid')
    if [frame['frame_id'] for frame in manifest['frames']] != [f'F{i:02d}' for i in range(64)]:
        raise ValueError('registered sample frame identity differs')
    if len({f['source_ordinal'] for f in manifest['frames']}) != 64:
        raise ValueError('registered sample ordinals duplicated')
    for frame in manifest['frames']:
        if F(frame['global_seconds_exact']) != times[frame['source_ordinal']-900]:
            raise ValueError('registered native sample ordinal/time binding differs')
        if F(frame['local_seconds_exact']) != F(frame['global_seconds_exact'])-30:
            raise ValueError('registered sample local clock differs')
        if sha(frame['path']) != frame['png_sha256']:
            raise ValueError('registered native sample PNG bytes differ')
    data = root/'reports/gemini_distillation_data_20261009/data/tvsum/ydata-tvsum50-v1_1'
    archive, matlab = data/'ydata-tvsum50-data.zip', data/'ydata-tvsum50-matlab.zip'
    assert_bound(archive,'tsv_archive')
    assert_bound(matlab,'mat_archive')
    rows = matching_tsv_rows(archive)
    vectors = [[int(v) for v in row[2].split(',')] for row in rows]
    if len(vectors) != 20 or any(len(v) != manifest['source_total_frames'] for v in vectors):
        raise ValueError('publisher row/frame count mismatch')
    if any(v not in range(1,6) for row in vectors for v in row):
        raise ValueError('invalid ordinal score')
    # Read MATLAB v7.3 directly in memory; do not extract archives or write caches.
    with zipfile.ZipFile(matlab) as z, h5py.File(io.BytesIO(z.read('matlab/ydata-tvsum50.mat')), 'r') as h:
        group = h['tvsum50']
        indices = [i for i, ref in enumerate(group['video'][()].flat)
                   if ''.join(chr(int(v)) for v in h[ref][()].flat) == 'kLxoNp-UchI']
        if len(indices) != 1:
            raise ValueError('publisher MATLAB source identity ambiguous')
        i = indices[0]
        mat_vectors = h[group['user_anno'][()].flat[i]][()]
        mat_frames = int(h[group['nframes'][()].flat[i]][()].flat[0])
        mat_mean = h[group['gt_score'][()].flat[i]][()].reshape(-1)
    publisher_vectors_exact_equal, publisher_mean_equal = verify_publisher(
        vectors, mat_vectors, mat_frames, manifest['source_total_frames'], mat_mean)
    changes, outside, unique = 0, [], set()
    for worker, scores in enumerate(vectors):
        for k in range(1, len(clock)):
            if scores[ordinals[k]] == scores[ordinals[k-1]]:
                continue
            changes += 1
            unique.add(ordinals[k])
            if times[k]//2 == times[k-1]//2:
                outside.append(dict(worker_row=worker, source_ordinal=ordinals[k]))
    report = dict(status='W01_PUBLISHER_BINDING_AND_BIN_DIAGNOSTIC_ONLY',
                  source_id=manifest['source_id'], role='EXPOSED_TRAIN_DEVELOPMENT_ONLY',
                  denominator=dict(native_frames=len(clock), publisher_worker_rows=20),
                  source_sha256=manifest['source_sha256'],
                  bindings={str(p.relative_to(root)):sha(p) for p in
                            [manifest_path,clock_path,archive,matlab,data/'README',
                             iteration/'slot6_silver24_v1/source_window_plan.json']},
                  publisher_tsv_mat_vectors_exact_equal=publisher_vectors_exact_equal,
                  publisher_mat_nframes_equal=mat_frames == manifest['source_total_frames'],
                  publisher_mean_matches_gt_score=publisher_mean_equal,
                  within_window_score_changes=changes, unique_change_ordinals=len(unique),
                  local_two_second_bin_consistency=not outside,
                  changes_not_on_native_two_second_bin_crossing=outside,
                  evidence='Local consistency supports expanded 2-second importance; not a publisher timing convention proof',
                  highlight_target_equivalence='NOT_ESTABLISHED',
                  prior_B_exposure='NOT_ESTABLISHED',
                  human_scores_not_converted_to_KEEP_NO=True,
                  threshold_selected=False, quality_gate_pass=False, training_admitted=False,
                  new_model_calls=0, new_optimizer_updates=0, locked_truth_read=False)
    report.pop('locked_truth_read')
    report.update(tsv_container_binary_rows_streamed=True,
                  other_source_tsv_text_decoded=False,
                  other_source_mat_score_arrays_dereferenced=False,
                  other_source_mat_video_ids_read_for_identity=True,
                  registered_native_sample_png_SHA_checked=64,
                  processed_student_tensor_reexecuted=False,
                  score_threshold_or_summary_labels_generated=False)
    write_once(output, report)


if __name__ == '__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--root', required=True)
    parser.add_argument('--output', required=True)
    args=parser.parse_args()
    run(args.root,args.output)
