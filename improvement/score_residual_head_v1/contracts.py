"""Native ordinal contracts, independent of a particular feature extractor."""
from bisect import bisect_left
from dataclasses import dataclass
from fractions import Fraction
from math import fsum, isfinite
from numbers import Integral, Real
from typing import Optional, Sequence


def exact_clock(pts: Sequence[object]) -> tuple[Fraction, ...]:
    """Accept exact seconds only; never reconstruct VFR from average FPS."""
    if any(isinstance(x, (float, bool)) for x in pts):
        raise ValueError("PTS must be exact rational seconds, not float/bool")
    values = tuple(Fraction(x) for x in pts)
    if any(b <= a for a, b in zip(values, values[1:])):
        raise ValueError("PTS must be strictly increasing in accepted native order")
    return values


def native_interval_ordinals(pts: Sequence[object], start, end) -> tuple[int, int]:
    """Half-open [start,end): select by actual PTS, returning ordinal [lo,hi)."""
    clock = exact_clock(pts)
    bounds = exact_clock((start, end))
    return bisect_left(clock, bounds[0]), bisect_left(clock, bounds[1])


@dataclass(frozen=True)
class NativeContract:
    # Every unit is contiguous and homogeneous in baseline membership. Features
    # may be reused by several units without claiming additional observation.
    feature_count: int
    feature_index: tuple[int, ...]
    n: tuple[int, ...]
    known_n: tuple[int, ...]
    c: tuple[float, ...]
    baseline: tuple[bool, ...]
    native_unit: tuple[int, ...]
    baseline_native: tuple[bool, ...]
    reference_native: tuple[Optional[float], ...]

    @property
    def reference_scope(self) -> str:
        known = sum(self.known_n)
        return "UNKNOWN" if not known else ("FULL" if known == len(self.native_unit) else "MASKED")

    @property
    def complete_empty_reference(self) -> bool:
        return self.reference_scope == "FULL" and fsum(self.c) == 0

    def validate(self) -> None:
        if not isinstance(self.feature_count, Integral) or isinstance(self.feature_count, bool) or self.feature_count <= 0:
            raise ValueError("feature_count must be a positive integer")
        native_count = len(self.native_unit)
        if native_count == 0 or len(self.baseline_native) != native_count or len(self.reference_native) != native_count:
            raise ValueError("A video requires a nonempty, complete native ordinal domain")
        unit_count = len(self.n)
        if not unit_count or any(len(x) != unit_count for x in (self.feature_index, self.known_n, self.c, self.baseline)):
            raise ValueError("Unit arrays differ in length")
        if any(b < a for a, b in zip(self.feature_index, self.feature_index[1:])):
            raise ValueError("Feature groups must retain temporal order")
        if any(type(b) is not bool for b in self.baseline_native + self.baseline):
            raise ValueError("Baseline mask must contain bool values")
        expanded, pos = [], 0
        for u, (f, n, k, c, b) in enumerate(zip(self.feature_index, self.n, self.known_n, self.c, self.baseline)):
            if isinstance(f, bool) or not isinstance(f, Integral) or not 0 <= f < self.feature_count:
                raise ValueError("Invalid feature index")
            if isinstance(n, bool) or not isinstance(n, Integral) or n <= 0:
                raise ValueError("n counts actual native frames")
            refs = self.reference_native[pos:pos+n]
            if len(refs) != n or self.baseline_native[pos:pos+n] != (b,) * n:
                raise ValueError("Unit crosses a baseline boundary or native domain")
            if any(v is not None and (isinstance(v, bool) or not isinstance(v, Real) or not isfinite(v) or not 0 <= v <= 1) for v in refs):
                raise ValueError("Reference must be [0,1] or None for UNKNOWN")
            actual_k = sum(v is not None for v in refs)
            actual_c = fsum(v for v in refs if v is not None)
            if isinstance(k, bool) or not isinstance(k, Integral) or k != actual_k or not isfinite(c) or abs(c-actual_c) > 1e-10:
                raise ValueError("Known count/reference mass differs from native reference")
            expanded.extend([u] * n)
            pos += n
        if tuple(expanded) != self.native_unit or pos != native_count:
            raise ValueError("Units must partition native ordinal domain exactly")


def build_contract(feature_group: Sequence[int], baseline_mask: Sequence[bool],
                   reference: Sequence[Optional[float]], feature_count: int,
                   native_pts: Optional[Sequence[object]] = None) -> NativeContract:
    """Split feature groups at every baseline change; no frame is discarded.

    `reference=None` per frame means unknown, not a negative label. A video
    with missing labels must supply an explicit all-None sequence.
    """
    groups, base, refs = tuple(feature_group), tuple(baseline_mask), tuple(reference)
    if not groups or len(groups) != len(base) or len(groups) != len(refs):
        raise ValueError("Native arrays must be nonempty and equal length")
    if any(isinstance(g, bool) or not isinstance(g, Integral) for g in groups) or any(b < a for a, b in zip(groups, groups[1:])):
        raise ValueError("Feature groups must be integer indices in temporal order")
    if native_pts is not None and len(exact_clock(native_pts)) != len(groups):
        raise ValueError("Native PTS length mismatch")
    feature_index, n, known_n, c, baseline, native_unit = [], [], [], [], [], []
    start = 0
    for end in range(1, len(groups) + 1):
        if end < len(groups) and groups[end] == groups[start] and base[end] == base[start]:
            continue
        current = refs[start:end]
        feature_index.append(groups[start])
        n.append(end-start)
        known_n.append(sum(v is not None for v in current))
        # Invalid labels are rejected below; avoid silently converting strings.
        if any(v is not None and (isinstance(v, bool) or not isinstance(v, Real) or not isfinite(v) or not 0 <= v <= 1) for v in current):
            raise ValueError("Reference must be [0,1] or None")
        c.append(fsum(v for v in current if v is not None))
        baseline.append(base[start])
        native_unit.extend([len(n)-1] * (end-start))
        start = end
    result = NativeContract(feature_count, tuple(feature_index), tuple(n), tuple(known_n), tuple(c), tuple(baseline), tuple(native_unit), base, refs)
    result.validate()
    return result
