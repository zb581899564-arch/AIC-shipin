"""Generation-time JSON contract; no output repair, model or third-party imports.

Canonical output: {"segments":[[start,end],...]}, with 0..5 sorted,
non-overlapping positive intervals bounded by the verified clip duration.
Numbers are nonnegative JSON decimals with at most four fractional digits,
matching the frozen parser's output precision. Integer/digit prefixes remain
legal only when some completion on that precision can satisfy the bounds.
"""
from __future__ import annotations

from fractions import Fraction
import json
import re


class ConstraintDeadEnd(RuntimeError):
    """No valid next token exists: stop this attempt instead of falling back."""


class IncompleteConstrainedOutput(ValueError):
    """Generation ended before a complete contract-valid JSON object."""


class BoundedSegmentsGrammar:
    SCALE = 10_000
    OPENING = '{"segments":['
    NUMBER = re.compile(r"(?:0|[1-9][0-9]*)(?:\.[0-9]{1,4})?\Z")
    NUMBER_PREFIX = re.compile(r"(?:0|[1-9][0-9]*)(?:\.[0-9]{0,4})?\Z")

    def __init__(self, duration, max_segments=5, allow_empty=True):
        if isinstance(duration, bool):
            raise ValueError("duration must be a finite positive number")
        try:
            self.duration = duration if isinstance(duration, Fraction) else Fraction(str(duration))
        except (ValueError, ZeroDivisionError, OverflowError) as exc:
            raise ValueError("duration must be a finite positive number") from exc
        if type(allow_empty) is not bool:
            raise ValueError("allow_empty must be a bool")
        if self.duration <= 0 or type(max_segments) is not int or not 1 <= max_segments <= 5:
            raise ValueError("positive duration and 1..5 maximum segments required")
        # A four-decimal endpoint cannot exceed the verified physical endpoint.
        self.end_units = (self.duration.numerator*self.SCALE)//self.duration.denominator
        if self.end_units < 1 and not allow_empty:
            raise ValueError("duration has no positive interval at frozen decimal precision")
        self.max_segments = max_segments
        self.allow_empty = allow_empty

    def _number_can_finish(self, prefix, lower, upper):
        """Does any legal number continuing prefix lie in [lower,upper]?"""
        if lower > upper:
            return False
        if not prefix:
            return True
        if not self.NUMBER_PREFIX.fullmatch(prefix):
            return False
        try:
            if "." in prefix:
                integer, fraction = prefix.split(".")
                factor = 10**(4-len(fraction))
                first = int(integer)*self.SCALE + (int(fraction) if fraction else 0)*factor
                return max(first,lower) <= min(first+factor-1,upper)
            value = int(prefix)
        except ValueError:
            return False
        # It may finish as an integer, gain decimals, or gain integer digits.
        # For each possible additional integer length, four decimal digits
        # cover a contiguous range of representable values. Leading 0 cannot
        # gain another integer digit, but can gain a fractional part.
        factor = 1
        while True:
            first = value*factor*self.SCALE
            last = (value+1)*factor*self.SCALE-1
            if max(first,lower) <= min(last,upper):
                return True
            if value == 0 or first > upper:
                return False
            factor *= 10

    def _number_units(self, text):
        if not self.NUMBER.fullmatch(text):
            return None
        try:
            integer, separator, fraction = text.partition(".")
            return int(integer)*self.SCALE + (int(fraction.ljust(4,"0")) if separator else 0)
        except ValueError:
            return None

    def _scan(self, text):
        if not isinstance(text,str) or not text.isascii():
            return False, False
        if len(text) <= len(self.OPENING):
            return self.OPENING.startswith(text), False
        if not text.startswith(self.OPENING):
            return False, False
        # Only this initial state may close an empty list. After a comma the
        # state is segment_open, which requires another interval and therefore
        # cannot admit a trailing comma even when empty output is enabled.
        state, number, previous_end, start, count = "first_segment_or_close", "", 0, None, 0
        for char in text[len(self.OPENING):]:
            if state in ("first_segment_or_close", "segment_open"):
                if state == "first_segment_or_close" and char == "]" and self.allow_empty:
                    state = "object_close"
                    continue
                if char != "[" or count >= self.max_segments or previous_end >= self.end_units:
                    return False,False
                state, number = "start", ""
            elif state in ("start","end"):
                lower = previous_end if state == "start" else start+1
                upper = self.end_units-1 if state == "start" else self.end_units
                if char in "0123456789.":
                    number += char
                    if not self._number_can_finish(number,lower,upper):
                        return False,False
                    continue
                delimiter = "," if state == "start" else "]"
                value = self._number_units(number)
                if char != delimiter or value is None or not lower <= value <= upper:
                    return False,False
                if state == "start":
                    start, state, number = value, "end", ""
                else:
                    previous_end, count, state = value, count+1, "after_segment"
            elif state == "after_segment":
                if char == "]":
                    state = "object_close"
                elif char == "," and count < self.max_segments and previous_end < self.end_units:
                    state = "segment_open"
                else:
                    return False,False
            elif state == "object_close":
                if char != "}":
                    return False,False
                state = "complete"
            else:
                return False,False
        return True, state == "complete"

    def valid_prefix(self, text):
        return self._scan(text)[0]

    def complete(self, text):
        valid, complete = self._scan(text)
        return valid and complete


ASCII_GRAMMAR_CHARS = frozenset('{}[]":,segments0123456789.')


def ascii_token_candidates(tokenizer):
    """Advisory single-token ASCII prefilter; full-context decode stays binding."""
    ids = sorted(set(tokenizer.get_vocab().values()))
    result = []
    for token_id in ids:
        piece = tokenizer.decode([token_id],skip_special_tokens=False,clean_up_tokenization_spaces=False)
        if piece and piece.isascii() and set(piece) <= ASCII_GRAMMAR_CHARS:
            result.append(token_id)
    return tuple(result)


class PrefixConstraint:
    """HF prefix_allowed_tokens_fn adapter, with explicit completion validation.

    prompt_length includes the complete processor input token prefix. Pass only
    newly generated token IDs to assert_complete(). Reuse candidate_token_ids
    across durations to avoid repeating vocabulary decode. No candidate is
    accepted solely because of its isolated decoded piece.
    """
    def __init__(self, tokenizer, prompt_length, duration, max_segments=5,
                 candidate_token_ids=None, eos_token_ids=None, allow_empty=True):
        if type(prompt_length) is not int or prompt_length < 0:
            raise ValueError("prompt_length must be a nonnegative integer")
        self.tokenizer, self.prompt_length = tokenizer, prompt_length
        self.grammar = BoundedSegmentsGrammar(duration,max_segments,allow_empty)
        eos = tokenizer.eos_token_id if eos_token_ids is None else eos_token_ids
        if isinstance(eos,int) and not isinstance(eos,bool):
            eos = [eos]
        if not isinstance(eos,(list,tuple,set)) or not eos or any(type(i) is not int or i < 0 for i in eos):
            raise ValueError("explicit valid EOS token IDs required")
        self.eos_token_ids = frozenset(eos)
        candidates = ascii_token_candidates(tokenizer) if candidate_token_ids is None else candidate_token_ids
        if any(type(i) is not int or i < 0 for i in candidates):
            raise ValueError("invalid candidate token IDs")
        self.candidate_token_ids = tuple(sorted(set(candidates)-self.eos_token_ids))
        self.cache = {}
        self.stats = {"calls":0,"cache_hits":0,"full_context_decodes":0,"dead_ends":0,
                      "candidate_token_count":len(self.candidate_token_ids)}

    def _decode(self, ids):
        self.stats["full_context_decodes"] += 1
        return self.tokenizer.decode(list(ids),skip_special_tokens=False,clean_up_tokenization_spaces=False)

    def __call__(self, batch_id, input_ids):
        del batch_id
        self.stats["calls"] += 1
        ids = input_ids.tolist() if hasattr(input_ids,"tolist") else list(input_ids)
        if len(ids) < self.prompt_length or any(type(i) is not int for i in ids):
            raise ConstraintDeadEnd("invalid HF prefix/prompt token identity")
        output_ids = tuple(ids[self.prompt_length:])
        if output_ids in self.cache:
            self.stats["cache_hits"] += 1
            return list(self.cache[output_ids])
        text = self._decode(output_ids)
        allowed = []
        if self.grammar.complete(text):
            allowed = sorted(self.eos_token_ids)
        elif self.grammar.valid_prefix(text):
            for token_id in self.candidate_token_ids:
                continued = self._decode(output_ids+(token_id,))
                if len(continued)>len(text) and continued.startswith(text) and self.grammar.valid_prefix(continued):
                    allowed.append(token_id)
        if not allowed:
            self.stats["dead_ends"] += 1
            raise ConstraintDeadEnd("no contract-valid token continuation; STOP without fallback")
        self.cache[output_ids] = tuple(allowed)
        return allowed

    def assert_complete(self, generated_token_ids):
        ids = generated_token_ids.tolist() if hasattr(generated_token_ids,"tolist") else list(generated_token_ids)
        if any(type(i) is not int or i < 0 for i in ids):
            raise IncompleteConstrainedOutput("invalid generated token identity")
        if ids and ids[-1] in self.eos_token_ids:
            ids = ids[:-1]
        if any(i in self.eos_token_ids for i in ids):
            raise IncompleteConstrainedOutput("EOS appeared before the complete JSON object")
        text = self._decode(ids)
        if not self.grammar.complete(text):
            raise IncompleteConstrainedOutput("truncated or invalid JSON; STOP without output repair")
        return json.loads(text)


def make_prefix_constraint(tokenizer, prompt_length, duration, max_segments=5,
                           candidate_token_ids=None, eos_token_ids=None, allow_empty=True):
    return PrefixConstraint(tokenizer,prompt_length,duration,max_segments,
                            candidate_token_ids,eos_token_ids,allow_empty)
