"""Targeted synthetic checks of VFR compatibility, ending evidence and native64."""
import copy
from fractions import Fraction as F
from native_mapping_v2 import validate_mapping
from native_window_plan import plan_windows


def reject(function, value):
    try:
        function(value)
    except ValueError:
        return
    raise AssertionError('Required mapping/plan rejection did not occur')


if __name__ == '__main__':
    source = dict(source_name='hand_vfr', annotation_frames=3, annotation_fps=30,
                  annotation_duration=1, member=dict(bytes=12, crc32='12345678'))
    clock = dict(source_name='hand_vfr', source_bytes=12, source_crc32='12345678',
                 source_sha256='a'*64, n_frames=3, normalized_exact_pts=['0', '1/10', '4/5'],
                 physical_end_exact='1', physical_endpoint_evidence=dict(
                     kind='LAST_NATIVE_FRAME_PTS_PLUS_POSITIVE_DURATION',
                     last_normalized_pts_exact='4/5', last_frame_duration_exact='1/5'))
    assert validate_mapping(source, clock)['nominal_span_is_diagnostic_only']
    for key, value in [('n_frames', 2), ('normalized_exact_pts', ['0', '1/10', '1/10']),
                       ('source_crc32', '87654321'), ('physical_end_exact', '3')]:
        changed = copy.deepcopy(clock)
        changed[key] = value
        reject(lambda item: validate_mapping(source, item), changed)
    changed = copy.deepcopy(clock)
    changed['physical_endpoint_evidence']['last_frame_duration_exact'] = '0'
    reject(lambda item: validate_mapping(source, item), changed)
    changed = copy.deepcopy(clock)
    changed['physical_endpoint_evidence']['kind'] = 'GUESSED_FPS_END'
    reject(lambda item: validate_mapping(source, item), changed)
    reject(plan_windows, clock)  # Too few physical frames cannot become native64.

    fixed = dict(normalized_exact_pts=[str(F(i, 10)) for i in range(600)], physical_end_exact='60')
    windows = plan_windows(fixed)
    assert len(windows) == 2
    assert windows[0]['source_frame_ordinals'] == [i*299//63 for i in range(64)]
    assert windows[1]['source_frame_ordinals'] == [300+i*299//63 for i in range(64)]
    assert windows[0]['end_exact'] == windows[1]['start_exact'] == '30'
    longer = dict(normalized_exact_pts=[str(F(i, 10)) for i in range(601)], physical_end_exact='601/10')
    windows = plan_windows(longer)
    assert len(windows) == 3
    assert windows[0]['start_exact'] == '0' and windows[-1]['end_exact'] == '601/10'
    assert all(F(row['end_exact'])-F(row['start_exact']) <= 30 for row in windows)
    assert all(a['end_exact'] == b['start_exact'] for a, b in zip(windows, windows[1:]))
    assigned = [index for row in windows for index in range(row['eligible_first'], row['eligible_stop'])]
    assert assigned == list(range(601))
    print('PASS synthetic VFR mapping, native-end evidence failures, exact equal windows and native64 no-repeat')
