"""Exact frame-coordinate compatibility, without asserting equal terminal policies."""
from fractions import Fraction


def compare_clock_frames(points, physical_end, legacy_points, legacy_end, selected):
    if points != legacy_points:
        raise ValueError('NATIVE_PTS_CHANGED')
    if not points or points[0] != 0 or any(a >= b for a, b in zip(points, points[1:])):
        raise ValueError('INVALID_NATIVE_POINTS')
    physical_end, legacy_end = Fraction(physical_end), Fraction(legacy_end)
    if points[-1] >= physical_end or legacy_end <= 0:
        raise ValueError('INVALID_ENDPOINT')
    if any(type(i) is not int or not 0 <= i < len(points) for i in selected):
        raise ValueError('SELECTED_ORDINAL_OUTSIDE_CLOCK')
    if any(not 0 <= points[i] < min(physical_end, legacy_end) for i in selected):
        raise ValueError('SELECTED_PTS_OUTSIDE_ONE_BOUND_ENDPOINT')
    return dict(all_native_points_exactly_equal=True, native_points=len(points),
                selected_points_checked=len(selected), terminal_policies_equal=physical_end == legacy_end,
                physical_end_exact=str(physical_end), original_renderer_end_exact=str(legacy_end),
                selected_points_valid_in_both=True, endpoints_rewritten=False, selections_changed=False)


def targeted_checks():
    p = [Fraction(0), Fraction(1, 2), Fraction(1)]
    assert compare_clock_frames(p, 2, p, Fraction(3, 2), [0, 1, 2])['selected_points_valid_in_both']
    assert compare_clock_frames(p, 2, p, 1, [0, 1])['terminal_policies_equal'] is False
    assert compare_clock_frames(p, 2, p, 2, [])['selected_points_checked'] == 0
    bad = [
        (p, 2, [Fraction(0), Fraction(1, 3), Fraction(1)], 2, [0]),
        (p, 2, p, 1, [2]),
        (p, 1, p, 2, []),
        (p, 2, p, 2, [3]),
        (p, 2, p, 2, [-1]),
        (p, 2, p, 2, [True]),
        ([Fraction(0), Fraction(0)], 2, [Fraction(0), Fraction(0)], 2, []),
    ]
    for args in bad:
        try:
            compare_clock_frames(*args)
        except ValueError:
            continue
        raise AssertionError('Unsafe compatibility accepted')
    return dict(status='PASS_TARGETED_EXACT_CLOCK_COMPATIBILITY', cases=10,
                synthetic_only=True, real_sources_or_model_calls=0)


if __name__ == '__main__':
    import json
    print(json.dumps(targeted_checks()))
