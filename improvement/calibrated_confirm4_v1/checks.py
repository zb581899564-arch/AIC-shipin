"""Synthetic-only checks: no media, processor, CUDA, model or reference access."""
import argparse
import ast
from fractions import Fraction as F
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
from unittest.mock import patch

import numpy as np
from prepare import _RecordingAV, image_grid65
from replay import time_masks


def main(native_profile_dir):
    passed = []
    for path in Path(__file__).parent.glob('*.py'):
        ast.parse(path.read_text(encoding='utf8'))
    passed.append('all_new_source_syntax')
    root = Path(native_profile_dir).resolve()
    for name in ('native_profile_01', 'native_profile_04'):
        spec = importlib.util.spec_from_file_location(name, root/(name+'.py'))
        module = importlib.util.module_from_spec(spec); sys.modules[name] = module; spec.loader.exec_module(module)
    profile = sys.modules['native_profile_04']

    class Container:
        start_time = 0
        duration = 60000000
        def __init__(self, final_duration=1):
            self.final_duration = final_duration
            self.streams = SimpleNamespace(video=[SimpleNamespace(index=0, start_time=0, time_base=F(1, 25), average_rate=F(25))])
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def decode(self, stream):
            for index in range(1500):
                yield SimpleNamespace(pts=index, time_base=F(1, 25), width=320, height=180,
                                      duration=1 if index < 1499 else self.final_duration)

    # The recorder also enumerates all stream headers; mimic the PyAV collection.
    class Streams:
        def __init__(self):
            self.video = [SimpleNamespace(index=0, type='video', start_time=0, time_base=F(1, 25), average_rate=F(25))]
        def __iter__(self):
            return iter(self.video)
    def fake(final_duration=1):
        container = Container(final_duration); container.streams = Streams()
        return SimpleNamespace(__version__='SYNTHETIC_NO_MEDIA', open=lambda _: container)

    recorder = _RecordingAV(fake())
    clock = profile.measure_original_video('synthetic', recorder)
    profile.validate_original_origin(clock)
    windows = profile.native64_windows(clock)
    assert len(windows) == 2 and len(recorder.observed['frames']) == 1500
    assert all(len(set(window['source_frame_ordinals'])) == 64 and F(window['end_exact'])-F(window['start_exact']) <= 30 for window in windows)
    failed = _RecordingAV(fake(None))
    try:
        profile.measure_original_video('synthetic', failed)
    except ValueError:
        assert len(failed.observed['frames']) == 1500 and failed.observed['frames'][-1]['duration'] is None
    else:
        raise AssertionError('Unobserved endpoint must fail with measured PTS retained')
    passed.append('native64_exact_plan_and_partial_measurement_evidence')

    clock = dict(normalized_exact_pts=[str(F(i, 4)) for i in range(40)], physical_end_exact='10')
    events = [dict(event_id='keep', original_interval_exact=['2', '4']),
              dict(event_id='drop', original_interval_exact=['3', '5'])]
    b0, retained = time_masks(clock, [dict(window_start='0', window_end='10', events=events)], {'keep': 'UNKNOWN', 'drop': 'DROP'})
    points = list(map(F, clock['normalized_exact_pts']))
    assert np.array_equal(retained, [F(5, 4) <= point < F(9, 2) for point in points])
    assert np.array_equal(b0, [F(5, 4) <= point < F(11, 2) for point in points])
    try:
        time_masks(clock, [dict(window_start='0', window_end='10', events=events)], {'keep': 'UNKNOWN'})
    except ValueError:
        pass
    else:
        raise AssertionError('A missing decision cannot become UNKNOWN')
    passed.append('D8_padding_unknown_keep_and_overlap_union')
    assert image_grid65(256, 256, 16, 2) == [1, 16, 16]
    assert image_grid65(64, 64, 16, 2) == [1, 16, 16]
    assert image_grid65(180, 320, 16, 2) == [1, 12, 22]
    passed.append('65K_geometry_including_small_image_rounding')
    from datetime import datetime
    assert datetime.fromisoformat('2026-10-18T16:00:00Z'.replace('Z', '+00:00')).utcoffset().total_seconds() == 0
    passed.append('python310_Z_deadline_parse')
    import confirm_common as common
    run = common.Run.__new__(common.Run)
    run.c = dict(native_admission_path='/SYNTHETIC_NO_FILE', source_ids=['C00'])
    run.receipt = lambda _: dict(sources=[dict(sid='C00', clock_ref=dict(sha256='exact-new-clock'))])
    admission = dict(status='PASS', source_ids=['C00'], clock_sha256_by_sid={'C00': 'exact-new-clock'},
                     original_endpoints_fit=True, no_label_resizing=True, labels_provided_to_model=False)
    with patch.object(common, 'read', return_value=admission), patch.object(common, 'ref', return_value={'synthetic': True}):
        assert run.native_admission() == {'synthetic': True}
        admission['clock_sha256_by_sid'] = {'C00': 'wrong-clock'}
        try:
            run.native_admission()
        except ValueError:
            pass
        else:
            raise AssertionError('Endpoint admission from a different native clock must not unlock GPU')
    passed.append('external_no_label_endpoint_gate_exact_clock_binding')
    print(__import__('json').dumps(dict(status='PASS_SYNTHETIC_ONLY', checks=passed, actual_media_opens=0,
          actual_decodes=0, processors=0, GPU_calls=0, labels_read=False)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('native_profile_dir')
    main(parser.parse_args().native_profile_dir)
