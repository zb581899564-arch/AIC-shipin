"""Prospective exact-offset mapping; never trim excess segments to repair output."""
from bisect import bisect_left
from fractions import Fraction
from contract import floor64, context_domain, sample_domain, intersection


def native_ranges(segments, all_exact_pts, origin):
    points = [Fraction(x) for x in all_exact_pts]
    result = []
    for a, b in segments:
        start, stop = Fraction(str(a))+origin, Fraction(str(b))+origin
        first, last = bisect_left(points, start), bisect_left(points, stop)
        if not 0 <= first < last <= len(points):
            raise ValueError('positive interval has no real native source frame')
        result.append([first, last])
    return result


def project_context(values, candidates, offset, duration, all_exact_pts, origin):
    shifted = [[Fraction(str(a))+offset, Fraction(str(b))+offset] for a, b in values]
    source = [[Fraction(str(a)), Fraction(str(b))] for a, b in candidates]
    exact = intersection(shifted, source)
    if len(exact) > 5:
        raise ValueError('candidate intersection exceeds five segments; no truncation or gap bridging')
    result = [[float(a), float(b)] for a, b in exact]
    previous = Fraction(0)
    for a, b in result:
        if not previous <= Fraction(str(a)) < Fraction(str(b)) <= duration:
            raise ValueError('projected selection violates original window geometry')
        if not any(Fraction(str(c)) <= Fraction(str(a)) < Fraction(str(b)) <= Fraction(str(d)) for c,d in candidates):
            raise ValueError('projected float representation escapes candidate')
        previous = Fraction(str(b))
    actual = native_ranges(result, all_exact_pts, origin)
    expected = native_ranges(exact, all_exact_pts, origin)
    if actual != expected:
        raise ValueError('float projection changes exact native membership')
    return result, dict(exact_shifted=[[str(a),str(b)] for a,b in shifted],
        exact_final=[[str(a),str(b)] for a,b in exact], native_ranges=actual,
        float_and_exact_native_membership_equal=True)
