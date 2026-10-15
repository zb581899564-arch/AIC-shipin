"""Prospective generation constraint: every interval contains a real PTS.

Keeps the original JSON vocabulary, decimal precision, empty semantics and
token-prefix adapter. It changes the feasible numeric domain during generation,
never rounds, expands or discards an already generated interval.
"""
from bisect import bisect_left
from fractions import Fraction
from original_grammar import BoundedSegmentsGrammar, PrefixConstraint


class NativeSegmentsGrammar(BoundedSegmentsGrammar):
    def __init__(self, duration, source_pts, origin, max_segments=5, allow_empty=True):
        super().__init__(duration, max_segments, allow_empty)
        self.origin = Fraction(origin)
        all_points = [Fraction(x) for x in source_pts]
        if not all_points or any(a >= b for a, b in zip(all_points, all_points[1:])):
            raise ValueError('strict increasing actual source PTS required')
        self.points = [p-self.origin for p in all_points
                       if self.origin <= p < self.origin+self.duration]
        if not self.points:
            raise ValueError('clip contains no actual native source frames')
        self.start_upper = min(self.end_units-1, int(self.points[-1]*self.SCALE))

    def _end_lower(self, start):
        index = bisect_left(self.points, Fraction(start, self.SCALE))
        if index == len(self.points):
            return self.end_units+1
        # Half-open interval must end strictly after its first contained PTS.
        return max(start+1, int(self.points[index]*self.SCALE)+1)

    def _scan(self, text):
        if not isinstance(text, str) or not text.isascii():
            return False, False
        if len(text) <= len(self.OPENING):
            return self.OPENING.startswith(text), False
        if not text.startswith(self.OPENING):
            return False, False
        state, number, previous_end, start, count = 'first', '', 0, None, 0
        for char in text[len(self.OPENING):]:
            if state in ('first', 'segment_open'):
                if state == 'first' and char == ']' and self.allow_empty:
                    state = 'object_close'
                    continue
                if char != '[' or count >= self.max_segments or previous_end > self.start_upper:
                    return False, False
                state, number = 'start', ''
            elif state in ('start', 'end'):
                lower = previous_end if state == 'start' else self._end_lower(start)
                upper = self.start_upper if state == 'start' else self.end_units
                if char in '0123456789.':
                    number += char
                    if not self._number_can_finish(number, lower, upper):
                        return False, False
                    continue
                delimiter = ',' if state == 'start' else ']'
                value = self._number_units(number)
                if char != delimiter or value is None or not lower <= value <= upper:
                    return False, False
                if state == 'start':
                    start, state, number = value, 'end', ''
                else:
                    previous_end, count, state = value, count+1, 'after_segment'
            elif state == 'after_segment':
                if char == ']':
                    state = 'object_close'
                elif char == ',' and count < self.max_segments and previous_end <= self.start_upper:
                    state = 'segment_open'
                else:
                    return False, False
            elif state == 'object_close':
                if char != '}':
                    return False, False
                state = 'complete'
            else:
                return False, False
        return True, state == 'complete'


def make_native_constraint(tokenizer, prompt_length, duration, source_pts, origin,
                           max_segments=5, candidate_token_ids=None,
                           eos_token_ids=None, allow_empty=True):
    adapter = PrefixConstraint(tokenizer, prompt_length, duration, max_segments,
                               candidate_token_ids, eos_token_ids, allow_empty)
    adapter.grammar = NativeSegmentsGrammar(duration, source_pts, origin,
                                           max_segments, allow_empty)
    return adapter
