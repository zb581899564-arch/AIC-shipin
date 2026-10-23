"""Token-level schema enforcement; no replacement answers or box truncation."""
from functools import lru_cache
import re

import regex

from .spatial import parse_grounding

_SPACE = r"[ \t\r\n]*"
_NUMBER = r"(?:0|[1-9][0-9]{0,2}|1000)"
_BOX = r"\[" + _SPACE + (_NUMBER + _SPACE + "," + _SPACE) * 3 + _NUMBER + _SPACE + r"\]"
_HEAD = r'\{' + _SPACE + '"mode"' + _SPACE + ":" + _SPACE
_TAIL = _SPACE + "," + _SPACE + '"boxes"' + _SPACE + ":" + _SPACE
_SUBJECT = '"subject"' + _TAIL + r"\[" + _SPACE + _BOX + "(?:" + _SPACE + "," + _SPACE + _BOX + "){0,2}" + _SPACE + r"\]"
_SCENE = '"whole_scene"' + _TAIL + r"\[" + _SPACE + r"\]"
_PATTERN = regex.compile(_HEAD + "(?:" + _SUBJECT + "|" + _SCENE + ")" + _SPACE + r"\}" + _SPACE)
_ALPHABET = set('{}[]:,"modeboxessubjectwhole_scene0123456789 \t\r\n')


@lru_cache(maxsize=4096)
def _number_choices(lower, upper, excluded):
    complete = {str(value) for value in range(lower, upper + 1) if value not in excluded}
    prefixes = {value[:length] for value in complete for length in range(1, len(value) + 1)}
    return complete, prefixes


def _coordinates_possible(text):
    numbers, boxes = [], []
    for match in re.finditer(r"[0-9]+", text):
        offset = len(numbers) % 4
        lower = numbers[-2] + 1 if offset in (2, 3) else 0
        upper = 999 if offset in (0, 1) else 1000
        excluded = ()
        if offset == 3:
            same_prefix = [box for box in boxes if box[:3] == numbers[-3:]]
            # Duplicate extents have already been ruled out in earlier boxes.
            if same_prefix:
                excluded = tuple(sorted(box[3] for box in same_prefix))
        complete, prefixes = _number_choices(lower, upper, excluded)
        digits = match.group()
        if match.end() == len(text):
            return digits in prefixes
        if digits not in complete:
            return False
        numbers.append(int(digits))
        if len(numbers) % 4 == 0:
            boxes.append(numbers[-4:])
    return True


@lru_cache(maxsize=65536)
def valid_prefix(text):
    return _PATTERN.fullmatch(text, partial=True) is not None and _coordinates_possible(text)


class GroundingGrammar:
    """An ASCII token trie prunes whole vocabulary branches before regex checks."""

    def __init__(self, tokenizer):
        self.tokenizer = tokenizer
        self.trie = {}
        specials = set(tokenizer.all_special_ids)
        for token in sorted(set(tokenizer.get_vocab().values()) - specials):
            piece = tokenizer.decode([token], skip_special_tokens=False,
                                     clean_up_tokenization_spaces=False)
            if not piece or not set(piece) <= _ALPHABET:
                continue
            node = self.trie
            for char in piece:
                node = node.setdefault(char, {})
            node.setdefault(None, []).append(token)

    def allowed(self, text, eos):
        if not valid_prefix(text):
            raise ValueError('Grounding generation left its registered JSON grammar')
        result = []
        if _PATTERN.fullmatch(text) is not None:
            parse_grounding(text, 3)
            result.extend(eos)
        pending = [(self.trie, text)]
        while pending:
            node, prefix = pending.pop()
            result.extend(node.get(None, []))
            for char, child in node.items():
                if char is not None and valid_prefix(prefix + char):
                    pending.append((child, prefix + char))
        if not result:
            raise ValueError('No valid grounding token; never substitute a default box')
        return result

    def constraint(self, prefix, eos):
        prefix = list(prefix)

        def allowed_tokens(_batch, row):
            values = row.tolist()
            if values[:len(prefix)] != prefix:
                raise ValueError('Grounding decoder prefix changed')
            text = self.tokenizer.decode(values[len(prefix):], skip_special_tokens=False,
                                         clean_up_tokenization_spaces=False)
            return self.allowed(text, eos)
        return allowed_tokens

    def validate_output(self, token_ids, eos):
        """CPU-only token replay before adopting an old successful answer."""
        emitted = []
        for position, token in enumerate(token_ids):
            text = self.tokenizer.decode(emitted, skip_special_tokens=False,
                                         clean_up_tokenization_spaces=False)
            if token not in self.allowed(text, eos):
                raise ValueError('Inherited output violates the new grammar at token ' + str(position))
            if token in eos:
                if position != len(token_ids) - 1:
                    raise ValueError('Tokens follow grounding EOS')
                return parse_grounding(text, 3)
            emitted.append(token)
        raise ValueError('Inherited grounding output lacks EOS')
