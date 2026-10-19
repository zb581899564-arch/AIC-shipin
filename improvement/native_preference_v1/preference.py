"""Pure CPU contracts for equal-native-budget answer preferences.

No model, tokenizer, media, file, network, or accelerator operations live here.
``clock`` always contains *every* native source frame's normalized PTS, in
ordinal order.  It is not the sparse observation clock.  Answers use local
Excerpt seconds, while selections and references use source-native ordinals.

References describe each reviewer's complete source-summary selection.  An
unselected frame is not asserted to be an objectively ordinary/non-highlight
frame.  Incomplete/UNKNOWN references cannot provide the complete-source
utility used by this experiment.
"""

from bisect import bisect_left
from decimal import Decimal
from fractions import Fraction
import json
import math


MAX_SEGMENTS = 6
MAX_FRACTIONAL_DIGITS = 18


class PreferenceContractError(ValueError):
    """Malformed input or a violated experiment contract."""


class UnknownSupervisionError(PreferenceContractError):
    """A full-source reference is incomplete; missing labels are not zeroes."""


class CandidateRepresentationError(PreferenceContractError):
    """A selection cannot be encoded under the fixed answer contract."""


def _require(condition, message):
    if not condition:
        raise PreferenceContractError(message)


def _exact(value, name):
    """Do not silently import binary floating-point error into a native clock."""
    _require(type(value) in (int, str, Fraction, Decimal),
             name + " must be an exact Fraction, integer, decimal, or string")
    if isinstance(value, Decimal):
        _require(value.is_finite(), name + " must be finite")
    try:
        return Fraction(value)
    except (ValueError, ZeroDivisionError, OverflowError) as exc:
        raise PreferenceContractError(name + " must be a finite exact number") from exc


def _clock(clock):
    points = tuple(_exact(t, "native PTS") for t in clock)
    _require(bool(points) and points[0] >= 0,
             "A nonempty, nonnegative complete native source clock is required")
    _require(all(left < right for left, right in zip(points, points[1:])),
             "Native source PTS must be strictly increasing")
    return points


def _window(clock, start, end):
    points = _clock(clock)
    left, right = _exact(start, "window start"), _exact(end, "window end")
    _require(0 <= left < right, "Window must have positive duration")
    return points, left, right, bisect_left(points, left), bisect_left(points, right)


def window_bounds(clock, start, end):
    """Return [lo, hi) native ordinal bounds for source-time [start, end)."""
    _, _, _, lo, hi = _window(clock, start, end)
    return lo, hi


def _selection(selected, name="selection", frame_count=None):
    values = tuple(selected)
    _require(all(type(index) is int and index >= 0 for index in values),
             name + " must contain nonnegative integer native ordinals, not a boolean mask")
    if frame_count is not None:
        _require(all(index < frame_count for index in values),
                 name + " contains an ordinal outside the complete native clock")
    return frozenset(values)


def _no_duplicate_keys(pairs):
    value = {}
    for key, item in pairs:
        _require(key not in value, "Duplicate JSON object key: " + key)
        value[key] = item
    return value


def _invalid_constant(value):
    raise PreferenceContractError("Non-finite JSON number: " + value)


def _json_decimal(value):
    # Generated timestamps never need enormous exponents.  Reject them before
    # conversion to Fraction could allocate an enormous numerator/denominator.
    number = Decimal(value)
    _require(number.is_finite() and abs(number.as_tuple().exponent) <= 1000,
             "JSON timestamp has an unsupported exponent")
    return number


def parse_answer(text, duration, *, max_segments=MAX_SEGMENTS):
    """Parse the strict ordered JSON answer; empty is legal, malformed is not.

    Decimal JSON tokens are parsed exactly.  Overlap is rejected by the output
    grammar; ``native_selection`` separately supports unioning arbitrary valid
    interval collections, including overlapping reference intervals.
    """
    _require(type(text) is str, "Answer must be JSON text")
    limit = _exact(duration, "duration")
    _require(limit > 0, "Answer duration must be positive")
    _require(type(max_segments) is int and max_segments >= 0,
             "max_segments must be a nonnegative integer")
    try:
        value = json.loads(text, parse_float=_json_decimal,
                           parse_constant=_invalid_constant,
                           object_pairs_hook=_no_duplicate_keys)
    except (json.JSONDecodeError, TypeError, ValueError, OverflowError) as exc:
        if isinstance(exc, PreferenceContractError):
            raise
        raise PreferenceContractError("Malformed answer JSON") from exc
    _require(type(value) is dict and set(value) == {"segments"},
             "Answer must contain exactly the segments field")
    values = value["segments"]
    _require(type(values) is list and len(values) <= max_segments,
             "segments must be a list within the fixed segment limit")
    intervals, previous = [], Fraction(0)
    for pair in values:
        _require(type(pair) is list and len(pair) == 2
                 and all(type(v) in (int, Decimal) for v in pair),
                 "Each segment must be a pair of JSON numbers")
        left, right = map(Fraction, pair)
        _require(previous <= left < right <= limit,
                 "Segments must be ordered, non-overlapping, and inside the Excerpt")
        intervals.append((left, right))
        previous = right
    return intervals


def native_selection(segments, clock, start, end):
    """Union local [a,b) intervals on the complete native PTS clock.

    A frame is selected iff its native PTS is in an interval and the Excerpt.
    Duplicate/overlapping intervals never duplicate a frame.  No nearest-frame
    rounding or sparse-observation index is substituted for native ordinals.
    """
    points, origin, stop, lo, hi = _window(clock, start, end)
    duration = stop - origin
    selected = set()
    for pair in segments:
        _require(isinstance(pair, (tuple, list)) and len(pair) == 2,
                 "Each interval must have two exact endpoints")
        left, right = (_exact(pair[0], "interval start"),
                       _exact(pair[1], "interval end"))
        _require(0 <= left < right <= duration, "Interval is outside the Excerpt")
        first = max(lo, bisect_left(points, origin + left))
        last = min(hi, bisect_left(points, origin + right))
        selected.update(range(first, last))
    return selected


def contiguous_runs(selected):
    """Return maximal [lo, hi) runs of consecutive native ordinals."""
    ordered = sorted(_selection(selected))
    if not ordered:
        return []
    runs, first, previous = [], ordered[0], ordered[0]
    for index in ordered[1:]:
        if index != previous + 1:
            runs.append((first, previous + 1))
            first = index
        previous = index
    runs.append((first, previous + 1))
    return runs


def _decimal_inside(left, right):
    """Return a frozen-grammar-compatible decimal inside an exact rational gap.

    Precision increases only to represent the already fixed native selection;
    this is not a candidate boundary/offset search or a quality optimization.
    The historical grammar allows at most 18 fractional digits and requires
    numeric identity through ``str(float(text))``.  An unrepresentable gap
    rejects the candidate; the answer contract is never widened to retain it.
    """
    _require(0 <= left < right, "A positive nonnegative native PTS gap is required")
    midpoint = (left + right) / 2
    scale = 1
    for places in range(MAX_FRACTIONAL_DIGITS + 1):
        numerator = (midpoint * scale).__floor__()
        number = Fraction(numerator, scale)
        if left < number < right:
            if places == 0:
                text = str(numerator)
            else:
                whole, tail = divmod(numerator, scale)
                fractional = str(tail).zfill(places).rstrip("0")
                text = str(whole) + ("." + fractional if fractional else "")
            try:
                rounded = float(text)
                if math.isfinite(rounded) and Fraction(str(rounded)) == number:
                    return text
            except (ValueError, OverflowError):
                pass
        scale *= 10
    raise CandidateRepresentationError(
        "Native PTS gap has no selected safe decimal under the frozen 18-digit/float-roundtrip grammar")


def selection_answer(selected, clock, start, end, *, max_segments=MAX_SEGMENTS):
    """Encode a selection with safe decimal endpoints and verify exact roundtrip.

    Endpoints lie inside the adjacent native PTS gaps.  The first window run
    may begin at zero; a final run ends strictly before the exclusive Excerpt
    endpoint while still including its last selected frame.  VFR clocks are
    supported.  Equal native frame counts do not imply equal elapsed seconds.
    At most 18 fractional digits and exact float-parser roundtrip are required.
    Actual frozen-grammar completion, tokenizer prefix reachability, and equal
    suffix-token lengths remain mandatory runtime checks.
    """
    points, origin, stop, lo, hi = _window(clock, start, end)
    chosen = _selection(selected, frame_count=len(points))
    _require(all(lo <= index < hi for index in chosen),
             "Answer selection must be contained in the Excerpt")
    _require(type(max_segments) is int and max_segments >= 0,
             "max_segments must be a nonnegative integer")
    runs = contiguous_runs(chosen)
    if len(runs) > max_segments:
        raise CandidateRepresentationError("Native selection exceeds the fixed segment limit")
    encoded = []
    for first, after in runs:
        left = "0" if first == lo else _decimal_inside(
            points[first - 1] - origin, points[first] - origin)
        right_limit = points[after] if after < hi else stop
        right = _decimal_inside(points[after - 1] - origin, right_limit - origin)
        encoded.append("[" + left + "," + right + "]")
    answer = '{"segments":[' + ",".join(encoded) + "]}"
    parsed = parse_answer(answer, stop - origin, max_segments=max_segments)
    _require(native_selection(parsed, points, origin, stop) == set(chosen),
             "Canonical answer failed exact native-frame roundtrip")
    return answer


def reflect_selection(selected, lo, hi):
    """One fixed native-ordinal reflection i -> lo + hi - 1 - i.

    This off-policy counterfactual preserves frame count and connected-run
    count.  It does not preserve seconds on VFR video or prove visual plausibility.
    """
    _require(type(lo) is int and type(hi) is int and 0 <= lo <= hi,
             "Reflection bounds must be nonnegative integer ordinals")
    chosen = _selection(selected)
    _require(all(lo <= index < hi for index in chosen),
             "Reflection selection is outside [lo, hi)")
    reflected = {lo + hi - 1 - index for index in chosen}
    _require(len(reflected) == len(chosen)
             and len(contiguous_runs(reflected)) == len(contiguous_runs(chosen)),
             "Reflection changed native budget or connected-run count")
    return reflected


def _raters(raters):
    references = tuple(_selection(rater, "rater reference") for rater in raters)
    _require(bool(references), "At least one complete source reviewer reference is required")
    return references


def _known(known_masks, rater_count, frame_count=None):
    if known_masks is None:
        # Absence means the caller declares exhaustive source-summary choices.
        # It is not a mechanism for filling missing/unknown annotation values.
        return None
    masks = tuple(tuple(mask) for mask in known_masks)
    _require(len(masks) == rater_count, "One known mask per reviewer is required")
    sizes = {len(mask) for mask in masks}
    _require(len(sizes) == 1 and next(iter(sizes)) > 0,
             "Known masks must span a common nonempty complete source clock")
    count = next(iter(sizes))
    if frame_count is not None:
        _require(count == frame_count, "Known masks do not span the complete native clock")
    if any(type(value) is not bool or not value for mask in masks for value in mask):
        raise UnknownSupervisionError(
            "UNKNOWN/incomplete reference cannot define full-source summary utility; do not fill zero")
    return count


def _utility_fraction(selected, references):
    values = []
    for reference in references:
        denominator = len(selected) + len(reference)
        values.append(Fraction(2 * len(selected & reference), denominator)
                      if denominator else Fraction(1))
    return sum(values, Fraction(0)) / len(values)


def mean_source_utility(selected, raters, known_masks=None):
    """Mean native-frame F1 over every complete source-summary reference.

    Both empty is 1; only one empty is 0.  All reference frames contribute to
    the denominator, including frames outside the candidate Excerpt.  This is
    a temporal summary proxy, not AIC's spatial-IoU-weighted official score.
    """
    chosen, references = _selection(selected), _raters(raters)
    frame_count = _known(known_masks, len(references))
    if frame_count is not None:
        _selection(chosen, frame_count=frame_count)
        for reference in references:
            _selection(reference, "rater reference", frame_count=frame_count)
    return float(_utility_fraction(chosen, references))


def make_preference_pairs(seeds, raters, baseline, clock, start, end,
                          *, known_masks=None, max_segments=MAX_SEGMENTS):
    """Return unique, non-tied seed/reflection pairs; never search alternatives.

    ``seeds``, ``raters`` and ``baseline`` contain source-global ordinals.
    For each original reviewer seed, only its intersection with this Excerpt
    is reflected once.  Both candidate answers use the same native frame/run
    budget.  For ranking, append the fixed baseline outside the Excerpt and
    compare against ALL complete source references.  The returned answer order
    is based on that utility, never an assumed preference for the original seed.

    Identical, tied, duplicate, or unrepresentable pairs are omitted.  Empty
    return is a valid no-pair result: the runtime must STOP rather than relax
    the recipe.  Token-length equality still requires the actual tokenizer.
    """
    points, origin, stop, lo, hi = _window(clock, start, end)
    _require(type(max_segments) is int and max_segments >= 0,
             "max_segments must be a nonnegative integer")
    references = _raters(raters)
    for reference in references:
        _selection(reference, "rater reference", frame_count=len(points))
    _known(known_masks, len(references), frame_count=len(points))
    original = _selection(baseline, "source baseline", frame_count=len(points))
    outside = frozenset(index for index in original if not lo <= index < hi)
    seen, pairs = set(), []
    for seed_index, seed in enumerate(seeds):
        seed = _selection(seed, "reviewer seed", frame_count=len(points))
        first = frozenset(index for index in seed if lo <= index < hi)
        second = frozenset(reflect_selection(first, lo, hi))
        if first == second or len(contiguous_runs(first)) > max_segments:
            continue
        key = tuple(sorted((tuple(sorted(first)), tuple(sorted(second)))))
        if key in seen:
            continue
        seen.add(key)
        first_utility = _utility_fraction(outside | first, references)
        second_utility = _utility_fraction(outside | second, references)
        if first_utility == second_utility:
            continue
        if first_utility > second_utility:
            chosen, rejected = first, second
            good, bad, chosen_is_seed = first_utility, second_utility, True
        else:
            chosen, rejected = second, first
            good, bad, chosen_is_seed = second_utility, first_utility, False
        try:
            chosen_answer = selection_answer(chosen, points, origin, stop,
                                              max_segments=max_segments)
            rejected_answer = selection_answer(rejected, points, origin, stop,
                                                max_segments=max_segments)
        except CandidateRepresentationError:
            continue
        pairs.append(dict(
            seed_index=seed_index,
            chosen_answer=chosen_answer,
            rejected_answer=rejected_answer,
            chosen_selected=sorted(chosen), rejected_selected=sorted(rejected),
            chosen_utility=float(good), rejected_utility=float(bad),
            chosen_utility_exact=str(good), rejected_utility_exact=str(bad),
            utility_gap_exact=str(good - bad),
            chosen_is_seed=chosen_is_seed,
            budget=len(chosen), segments=len(contiguous_runs(chosen)),
            window_native_lo=lo, window_native_hi=hi,
            outside_baseline_frames=len(outside), reviewers=len(references),
            candidate_generation="one_native_ordinal_reflection_of_original_reviewer_seed",
            off_policy=True, equal_native_budget=True,
            token_length_equality_checked=False,
        ))
    return pairs


def dpo_loss(policy_chosen, policy_rejected, reference_chosen,
             reference_rejected, beta):
    """Stable scalar CPU reference for sequence-summed log-probability DPO."""
    values = (policy_chosen, policy_rejected, reference_chosen, reference_rejected, beta)
    _require(all(type(value) in (int, float) and math.isfinite(value) for value in values),
             "DPO inputs must be finite numeric scalars")
    _require(beta > 0, "DPO beta must be positive")
    margin = beta * ((policy_chosen - reference_chosen)
                     - (policy_rejected - reference_rejected))
    _require(math.isfinite(margin), "DPO relative log-probability margin overflowed")
    return max(0.0, -margin) + math.log1p(math.exp(-abs(margin)))


def causal_positions(length, suffixcount):
    """Logit positions predicting all suffix tokens, including its final EOS.

    ``length`` is the total prefix+suffix token count.  At least one prefix
    token is required.  The first suffix token is predicted at prefix_length-1.
    """
    _require(type(length) is int and type(suffixcount) is int
             and 1 <= suffixcount < length,
             "Require a nonempty prefix and suffix in the complete token sequence")
    return list(range(length - suffixcount - 1, length - 1))
