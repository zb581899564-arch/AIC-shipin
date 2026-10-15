"""Targeted checks for original clock origin, exact endpoints and split ranges."""
from fractions import Fraction as F
from types import SimpleNamespace as NS

from download_media_batch_04 import member_ranges
from native_profile_04 import (measure_original_video, native64_windows,
                               validate_original_origin, validate_reference_endpoints)


class Container:
    start_time = None
    duration = 60000001

    def __init__(self, offset=0, final_duration=1, duplicate=False):
        self.offset, self.final_duration, self.duplicate = offset, final_duration, duplicate
        self.streams = NS(video=[NS(start_time=None, time_base=F(1, 10), average_rate=F(10), index=0)])

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def decode(self, stream):
        for index in range(600):
            yield NS(pts=index+self.offset-(1 if self.duplicate and index == 2 else 0),
                     time_base=F(1, 10), width=320, height=180,
                     duration=self.final_duration if index == 599 else 1)


def expect_failure(call):
    try:
        call()
    except ValueError:
        return
    raise AssertionError('Expected actual gate rejection')


def main():
    av = NS(__version__='synthetic_only', open=lambda path: Container())
    clock = measure_original_video('synthetic', av)
    validate_original_origin(clock)
    assert clock['physical_end_exact'] == '60' and clock['native_frames'] == 600
    assert clock['container_duration_microseconds_diagnostic_only'] == 60000001
    assert len(native64_windows(clock)) == 2
    references = [[['1/3', '60']] for _ in range(10)]
    validate_reference_endpoints(clock, references)
    expect_failure(lambda: validate_reference_endpoints(clock, [[['0', '600001/10000']] for _ in range(10)]))
    positive = measure_original_video('synthetic', NS(__version__='synthetic_only', open=lambda path: Container(offset=1)))
    assert positive['first_original_pts_exact'] == '1/10'
    expect_failure(lambda: validate_original_origin(positive))
    expect_failure(lambda: measure_original_video('synthetic', NS(__version__='synthetic_only', open=lambda path: Container(final_duration=0))))
    expect_failure(lambda: measure_original_video('synthetic', NS(__version__='synthetic_only', open=lambda path: Container(duplicate=True))))
    assert member_ranges(dict(body_global_offset=8, member_bytes=7), 10,
                         [{'bytes': 10}, {'bytes': 10}]) == [(0, 8, 2), (1, 0, 5)]
    expect_failure(lambda: member_ranges(dict(body_global_offset=19, member_bytes=2), 10,
                                        [{'bytes': 10}, {'bytes': 10}]))
    print('PASS targeted synthetic clock/origin/endpoint/split-range checks; actual media acceptance0')


if __name__ == '__main__':
    main()
