"""Read-only source/clock adapter for the independent fixed40 fact veto.

Only the original pinned silver observation file and nine already measured
clocks are admitted.  This module does not acquire, decode, measure, encode,
import a model, inspect predictions, or adopt an old RGB/tensor cache.

The public registration validator reopens the full original reference, checks
its byte SHA, recounts all 40 sources/3081 observations, and reconstructs the
17 ordinary-point-covering views on the complete zero-origin source grid.
The reference remains AI silver with FAILED coverage/reference-quality gates.
"""
from __future__ import annotations

import argparse
from bisect import bisect_left
from collections import Counter
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import re


RUN = Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
MEDIA_ROOT = Path('/home/inspur/aic_video_data/videos')
REFERENCE_SHA = '37a7c93876334b3a5d0c222e3a7f99727778d50f28f3a1172e860d19d3dc82b8'
REFERENCE_BYTES = 594682
SCOPE = 'FULL_ORIGINAL_SOURCE_ZERO_ORIGIN_15_STRIDE7_5'
ENDPOINT_KIND = 'ACTUAL_LAST_DECODED_FRAME_PACKET_DURATION'
REFERENCE_LEVEL = 'AI_REVIEWED_SILVER_NOT_HUMAN_GOLD'
EXPECTED_COVERAGE = dict(sources=40, keep_sources=6, ordinary_sources=9,
                         two_ended_dense_events=1, KEEP=184, ORDINARY=222, UNKNOWN=2675)

# These are existing observed identities, not new source selections or results.
# fps/end below are assertions against the original pinned clock, not repairs
# or estimates from a filename, nominal clip length, or a rounded frame rate.
SOURCE_FACTS = (
    ('R07', 'qvh_000263_9x16', 'IdpHJK90VDw',
     '822cdc171cc21e37df7f744af73ba2b1de285f2e4628e0708f9a97ba4505c3d2',
     'd5a77136ae413ed28e18ea972f6547a3d377a7d6085f61a8d76a54a03020aa8e',
     3597, 24000, 1001, '1200199/8000', 14599788, 143742, 26),
    ('R11', 'qvh_000159_9x16', 'MC6y7jwenlE',
     'd04f9d5ef5a5a37084acc4756e55a1fb033498ef1fd50b730573aad462ca8a98',
     'f8e00ec8d82bf10498603004fb408bf54013894514d61159e9a0cad2ec154124',
     4496, 30000, 1001, '281281/1875', 13910673, 178988, 55),
    ('R15', 'qvh_000679_9x16', '8vUjoQd0fYY',
     '5d11deec3842e880a5a2d9dd9d233fdc651e61a883095d6a120e07978dec8d69',
     '7c6e7f3f50fff7527becbd69b58d89a462a4a3a20d6763c6d38f8b50c15d8b8a',
     4500, 30, 1, '150', 12596238, 149214, 25),
    ('R18', 'qvh_000750_9x16', 'Y2GVVC_cD_E',
     'db905f1b79ec7d3771a363a0ef9788b05170a0358a6df9d5d7d1f767a17e3638',
     'e0869b5122f9256645167268e9472af5807370c6798aeb4555d4c44493dc3642',
     3354, 24000, 1001, '559559/4000', 9732406, 133840, 39),
    ('R19', 'qvh_000265_9x16', 'p-III2A1E2o',
     '14a7f250c237708d35ac9fcdf2de48efda96e1c298f5843a095d3094fd3100b0',
     'c1fc134f6640a32d7d065b6b4ae3318a953e8c2ae88fe518df4fb6442067c6cb',
     3750, 25, 1, '150', 11363788, 95399, 45),
    ('S08', 'qvh_000882_9x16', 'QXC-pnmOGnM',
     '7874f5ad5ef45349b8894353377c1e0664f19054483903e763e7f1c64f5124b4',
     '9c0070ce8d6ed17a96b0872d1011fa295d4732625943f7aa353cc7c3f5213dad',
     3750, 25, 1, '150', 9375930, 95399, 3),
    ('S30', 'qvh_000729_9x16', 'E6yFTWlChmE',
     'cafe9f8e5b93f40917d37aad3a1003dfa133f2d41fc714d6a0021eb18e591dab',
     '081c08ec454a983a7210ec8926f92ac51666857b0575e461786ed19167e9a7ac',
     3750, 25, 1, '150', 10444125, 95400, 13),
    ('S32', 'qvh_000481_9x16', 'iuH6szYVWw4',
     '9829f8a967daf3926f9b6e9416a1ebe498c9dec40c6211eb5bf07d2d28b1f78f',
     '6e55e5c882c998d9473b3d6a8cd953a7aa73912860b15cc96b11de58b30405f0',
     4500, 30, 1, '150', 11469791, 149214, 4),
    ('S36', 'qvh_000482_9x16', 'TNkHgO68F6U',
     'a4227c55bbdc30b160f5bf9e63fc177d3a69310db5aa20fd3bc3e37227acae95',
     '93e2dfae3f42c7c226f25c0d45f3ba0d8b19a50f723e291641b18ce5ec002d3a',
     4496, 30000, 1001, '281281/1875', 14845458, 178987, 12),
)
FACT_KEYS = ('case_id', 'video_id', 'source_group', 'source_key', 'clock_sha256',
             'n_frames', 'fps_num', 'fps_den', 'physical_end_exact',
             'source_bytes', 'clock_bytes', 'ordinary_points')
FACTS = {row[0]: dict(zip(FACT_KEYS, row)) for row in SOURCE_FACTS}


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def unique_object(pairs):
    value = {}
    for key, item in pairs:
        require(key not in value, 'Duplicate JSON key: '+key)
        value[key] = item
    return value


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'), object_pairs_hook=unique_object,
                      parse_constant=lambda item: (_ for _ in ()).throw(ValueError('Nonfinite JSON: '+item)))


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def exact(value):
    require(type(value) in (str, int), 'Exact seconds require a rational string or non-bool integer')
    return F(value)


def validate_reference(document):
    """Recount the full file; the admission caller additionally pins byte SHA."""
    require(document['status'] == 'STOP_REFERENCE_COVERAGE_INSUFFICIENT' and
            document['reference_level'] == REFERENCE_LEVEL and
            document['coverage_pass'] is False and document['reference_quality_pass'] is False and
            document['candidate_predictions_read'] is False and
            document['old_formal_quality_failed_preserved'] is True,
            'Original silver quality/coverage FAILED and exposure facts must remain unchanged')
    require(document['coverage'] == EXPECTED_COVERAGE, 'Frozen full reference coverage changed')
    rows = document['rows']
    require(isinstance(rows, list) and len(rows) == 40 and
            len({row['case_id'] for row in rows}) == len({row['source_key'] for row in rows}) ==
            len({row['video_id'] for row in rows}) == 40,
            'Full 40 distinct source identities required; no nine-source-only derivative')
    totals, ordinary_cases, keep_cases = Counter(), set(), set()
    for row in rows:
        require(isinstance(row['source_key'], str) and re.fullmatch(r'[0-9a-f]{64}', row['source_key']) and
                isinstance(row['clock_sha256'], str) and re.fullmatch(r'[0-9a-f]{64}', row['clock_sha256']),
                'Original exact source/clock SHA identity required')
        points = row['points']
        require(isinstance(points, list) and len({point['ordinal'] for point in points}) == len(points),
                'Original observation ordinals must be complete and unique per source')
        counts = Counter()
        for point in points:
            require(type(point['ordinal']) is int and point['ordinal'] >= 0 and
                    point['label'] in ('KEEP', 'ORDINARY', 'UNKNOWN') and exact(point['exact_pts']) >= 0,
                    'Invalid original observation; UNKNOWN/unselected must not become ORDINARY')
            counts[point['label']] += 1
        require({key: counts[key] for key in ('KEEP', 'ORDINARY', 'UNKNOWN')} == row['counts'],
                'Per-source full original observation count differs')
        totals.update(counts)
        if counts['KEEP']:
            keep_cases.add(row['case_id'])
        if counts['ORDINARY']:
            ordinary_cases.add(row['case_id'])
            require(row['case_id'] in FACTS, 'Unregistered ordinary-bearing original source')
            fact = FACTS[row['case_id']]
            require(all(row[key] == fact[key] for key in
                        ('case_id', 'video_id', 'source_group', 'source_key', 'clock_sha256')) and
                    counts['ORDINARY'] == fact['ordinary_points'], 'Frozen ordinary source identity/count changed')
    require(sum(totals.values()) == 3081 and dict(totals) == {'KEEP': 184, 'ORDINARY': 222, 'UNKNOWN': 2675} and
            ordinary_cases == set(FACTS) and len(keep_cases) == 6,
            'Full original 3081 points/222 ORDINARY/nine-source denominator changed')
    return document


def load_reference(path):
    """Only the full original 594682-byte file is an admitted fact reference."""
    path = Path(path)
    require(path.is_file() and path.stat().st_size == REFERENCE_BYTES and sha(path) == REFERENCE_SHA,
            'Missing/changed full original silver reference; compact/caller-declared SHA is insufficient')
    return validate_reference(read(path))


def ordinary_rows(reference):
    validate_reference(reference)
    by_case = {row['case_id']: row for row in reference['rows']}
    return [by_case[fact[0]] for fact in SOURCE_FACTS]


def clock_document(path, clock_sha256, source_key):
    """Read an existing exact clock, never open or remeasure its media body."""
    path = Path(path)
    require(path.is_absolute() and path.is_file() and sha(path) == clock_sha256,
            'Missing/changed already successful original source clock: '+str(path))
    clock = read(path)
    require(clock['source_sha256'] == source_key and clock['raw_origin_sec'] == 0 and
            clock['endpoint_kind'] == ENDPOINT_KIND,
            'Clock source/original zero origin/actual packet endpoint differs')
    for key in ('width', 'height', 'n_frames', 'fps_num', 'fps_den'):
        require(type(clock[key]) is int and clock[key] > 0, 'Existing actual clock '+key+' is missing/invalid')
    points = clock['pts_rational']
    require(isinstance(points, list) and len(points) == clock['n_frames'] and points,
            'Complete stored pts_rational is required; no interpolation or rounded PTS')
    exact_points = list(map(exact, points))
    end = exact(clock['physical_endpoint_rational'])
    require(exact_points[0] == 0 and all(a < b for a, b in zip(exact_points, exact_points[1:])) and end > exact_points[-1],
            'Complete original zero-origin increasing PTS and actual positive last-frame duration required')
    return clock, exact_points, end


def audit_source_descriptors(reference, run_root=RUN):
    """Return nine source descriptors from the original reference and clocks.

    source_key is the already validated physical media SHA named by the pinned
    clock.  Here only source existence/size are read.  The independent actual
    CPU admission separately rehashes required_files before using media.
    """
    root = Path(run_root)
    require(root == RUN, 'Use the specified original source-clock directory; do not discover alternatives')
    result = []
    for row in ordinary_rows(reference):
        fact = FACTS[row['case_id']]
        path = root/'context_advisory_v1/input_01'/(row['source_key']+'.clock.json')
        clock, points, end = clock_document(path, row['clock_sha256'], row['source_key'])
        source_path = Path(clock['source_path'])
        require(source_path.is_absolute() and source_path.resolve().is_relative_to(MEDIA_ROOT) and source_path.is_file(),
                'Original existing media path escaped or is missing; no acquisition fallback')
        require(source_path.stat().st_size == fact['source_bytes'] and path.stat().st_size == fact['clock_bytes'] and
                (clock['width'], clock['height']) == (534, 300) and
                all(clock[key] == fact[key] for key in ('n_frames', 'fps_num', 'fps_den')) and
                end == F(fact['physical_end_exact']), 'Read-only observed source/clock metadata changed')
        result.append(dict(
            case_id=row['case_id'], video_id=row['video_id'], source_group=row['source_group'],
            source_key=row['source_key'], source_sha256=row['source_key'], source_path=str(source_path),
            source_bytes=source_path.stat().st_size, clock_path=str(path), clock_sha256=row['clock_sha256'],
            clock_bytes=path.stat().st_size, width=clock['width'], height=clock['height'],
            n_frames=clock['n_frames'], fps_num=clock['fps_num'], fps_den=clock['fps_den'],
            physical_end_exact=str(end), pts_field='pts_rational',
            physical_end_field='physical_endpoint_rational', endpoint_kind=clock['endpoint_kind']))
    require(len(result) == 9, 'All nine original ordinary-bearing sources are required')
    return result


def load_source_clock(descriptor):
    """Canonical metadata from original PTS; no origin shift, fps or end guess."""
    require(descriptor['case_id'] in FACTS and descriptor['source_sha256'] == descriptor['source_key'],
            'Frozen physical source identity required')
    fact = FACTS[descriptor['case_id']]
    require(all(descriptor[key] == fact[key] for key in
                ('video_id', 'source_group', 'source_key', 'clock_sha256')) and
            descriptor['pts_field'] == 'pts_rational' and
            descriptor['physical_end_field'] == 'physical_endpoint_rational', 'Original exact field binding changed')
    expected_path = RUN/'context_advisory_v1/input_01'/(descriptor['source_key']+'.clock.json')
    require(Path(descriptor['clock_path']) == expected_path, 'Original specified clock path changed')
    clock, points, end = clock_document(expected_path, descriptor['clock_sha256'], descriptor['source_key'])
    require(clock['source_path'] == descriptor['source_path'] and
            all(clock[key] == descriptor[key] == fact[key] for key in ('n_frames', 'fps_num', 'fps_den')) and
            (clock['width'], clock['height']) == (descriptor['width'], descriptor['height']) == (534, 300) and
            descriptor['endpoint_kind'] == clock['endpoint_kind'] and
            end == exact(descriptor['physical_end_exact']) == F(fact['physical_end_exact']),
            'Registered actual source geometry/fps/physical endpoint differs from the pinned clock')
    return dict(original_exact_pts=[str(point) for point in points],
                original_zero_origin_verified=True, first_original_pts_exact=str(points[0]),
                last_original_pts_exact=str(points[-1]), last_frame_duration_exact=str(end-points[-1]),
                physical_end_exact=str(end), timeline_shift_applied=False, native_frames=len(points),
                width=clock['width'], height=clock['height'], fps_num=clock['fps_num'], fps_den=clock['fps_den'],
                endpoint_kind=clock['endpoint_kind'], source_sha256=descriptor['source_key'],
                source_clock_sha256=descriptor['clock_sha256'])


def original_grid(physical_end):
    """Complete-source 0-origin 15/7.5 grid plus exact right tail, deduplicated."""
    end = exact(physical_end)
    require(end > 0, 'A stored positive original physical endpoint is required')
    if end <= 15:
        return [(F(0), end)]
    result, start = set(), F(0)
    while start+15 <= end:
        result.add((start, start+15))
        start += F(15, 2)
    result.add((end-15, end))
    return sorted(result)


def point_covering_views(reference, descriptors):
    """All and only full-source grid views that can touch an original O point."""
    rows = ordinary_rows(reference)
    require([row['case_id'] for row in descriptors] == [row['case_id'] for row in rows],
            'Complete ordered nine-source descriptor denominator required')
    result, total_points = [], 0
    for row, descriptor in zip(rows, descriptors):
        require(all(row[key] == descriptor[key] for key in
                    ('case_id', 'video_id', 'source_group', 'source_key', 'clock_sha256')),
                'Observation/source descriptor identity differs')
        clock = load_source_clock(descriptor)
        points = list(map(F, clock['original_exact_pts']))
        ordinary = [point for point in row['points'] if point['label'] == 'ORDINARY']
        for point in ordinary:
            ordinal, timestamp = point['ordinal'], exact(point['exact_pts'])
            require(0 <= ordinal < len(points) and points[ordinal] == timestamp,
                    'Original silver ordinal/exact PTS is not the same frame in the pinned complete clock')
        observed = {exact(point['exact_pts']) for point in ordinary}
        covered = set()
        source_views = []
        for grid_index, (start, stop) in enumerate(original_grid(clock['physical_end_exact'])):
            touched = {point for point in observed if start <= point < stop}
            if not touched:
                continue
            first, past = bisect_left(points, start), bisect_left(points, stop)
            count = past-first
            require(count >= 64, 'Fewer than 64 real native frames; reject without padding or source substitution')
            ordinals = [first+j*(count-1)//63 for j in range(64)]
            require(len(set(ordinals)) == 64 and all(start <= points[i] < stop for i in ordinals),
                    'Canonical native64 original-frame sampling differs')
            source_views.append(dict(case_id='fixed40.'+row['case_id']+'.overlap'+str(len(source_views)).zfill(4),
                fixed_case_id=row['case_id'], source_name=row['video_id'], source_sha256=row['source_key'],
                source_clock_sha256=row['clock_sha256'], window_start=str(start), window_end=str(stop),
                source_frame_ordinals=ordinals, sample_exact_pts=[str(points[i]) for i in ordinals],
                window_role='overlap', view_roles=['overlap'], original_grid_index=grid_index))
            covered.update(touched)
        require(covered == observed and source_views, 'Incomplete original ordinary-point/full-grid view coverage')
        result.extend(source_views)
        total_points += len(ordinary)
    require(total_points == 222 and len(result) == 17 and len({view['case_id'] for view in result}) == 17,
            'Exact original222-point/nine-source/seventeen-view denominator required')
    return result


def validate_registered_sources(registration):
    """Recompute source+view identities, without any media-body read or GPU work.

    Prior dev/confirm PASS, authorization, code/model/processor locks and actual
    CPU inputs are enforced independently by facts_common/facts_prepare/admit.
    This function does not treat reference geometry as execution evidence.
    """
    require(registration['schema'] == 'RECALL_FIXED40_EXECUTION_REGISTRATION_V1' and
            registration['status'] == 'REGISTERED_FIXED40_EXECUTION_AFTER_DEV_CONFIRM_PASS' and
            registration['group'] == 'facts' and registration['source_scope'] == 'EXTERNAL_NONTEST_ONLY' and
            registration['scope'] == SCOPE and registration['source_count'] == 9 and
            registration['unique_input_count'] == 17 and registration['model_parameters'] == 8782459120 and
            registration['optimizer_updates'] == 0, 'Independent immutable fixed40 execution scope required')
    ref = registration['reference_ref']
    require(isinstance(ref, dict) and set(ref) == {'path', 'sha256'} and
            Path(ref['path']).is_absolute() and ref['sha256'] == REFERENCE_SHA,
            'Full original silver path/byte-SHA reference required')
    require(registration['required_files'].get(ref['path']) == REFERENCE_SHA,
            'Full original silver file must be in the immutable required_files closure')
    reference = load_reference(ref['path'])
    sources = audit_source_descriptors(reference)
    views = point_covering_views(reference, sources)
    require(registration['sources'] == sources and registration['views'] == views,
            'Registered sources/views differ from the original222-point complete-source recomputation')
    for source in sources:
        require(registration['required_files'].get(source['source_path']) == source['source_sha256'] and
                registration['required_files'].get(source['clock_path']) == source['clock_sha256'],
                'Every original media SHA and already measured clock must be explicitly locked')
    return sources, views


def main():
    parser = argparse.ArgumentParser(description='Read-only original fixed40 source/clock metadata plan; no media decode or inference')
    parser.add_argument('--reference', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    reference = load_reference(args.reference)
    sources = audit_source_descriptors(reference)
    views = point_covering_views(reference, sources)
    document = dict(schema='RECALL_FIXED40_SOURCE_METADATA_PLAN_V1', scope=SCOPE, sources=sources, views=views,
                    reference_ref=dict(path=str(Path(args.reference).resolve()), sha256=REFERENCE_SHA),
                    reference_level=REFERENCE_LEVEL, coverage=EXPECTED_COVERAGE,
                    coverage_pass=False, reference_quality_pass=False,
                    source_count=9, unique_input_count=17, ordinary_observation_count=222,
                    metadata_only=True, model_calls=0, GPU_admitted=False)
    with Path(args.output).open('x', encoding='utf-8', newline='\n') as stream:
        json.dump(document, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


if __name__ == '__main__':
    main()
