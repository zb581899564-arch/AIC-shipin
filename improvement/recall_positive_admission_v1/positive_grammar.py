"""Finite canonical positive-admission grammar with full-prefix token decoding."""
import json
from positive_contract import responses


def candidate_tokens(tokenizer, values):
    chars = frozenset(''.join(values))
    result = []
    for token in sorted(set(tokenizer.get_vocab().values())):
        piece = tokenizer.decode([token], skip_special_tokens=False,
                                 clean_up_tokenization_spaces=False)
        if piece and piece.isascii() and set(piece) <= chars:
            result.append(token)
    return tuple(result)


class PositiveConstraint:
    def __init__(self, tokenizer, prefix, req, eos, candidates=None):
        if type(prefix) is not int or prefix < 1 or not eos or any(type(i) is not int or i < 0 for i in eos):
            raise ValueError('Actual accepted input prefix and EOS required')
        self.tokenizer, self.prefix, self.eos = tokenizer, prefix, frozenset(eos)
        self.responses = responses(req)
        selected = candidate_tokens(tokenizer, self.responses) if candidates is None else candidates
        self.candidates = tuple(sorted(set(selected)-self.eos))
        self.cache = {}
        self.stats = dict(calls=0, full_context_decodes=0, dead_ends=0)

    def decode(self, ids):
        self.stats['full_context_decodes'] += 1
        return self.tokenizer.decode(list(ids), skip_special_tokens=False,
                                     clean_up_tokenization_spaces=False)

    def __call__(self, batch_id, input_ids):
        del batch_id
        self.stats['calls'] += 1
        ids = input_ids.tolist() if hasattr(input_ids, 'tolist') else list(input_ids)
        if len(ids) < self.prefix or any(type(i) is not int or i < 0 for i in ids):
            raise ValueError('Actual generated-prefix identity changed')
        suffix = tuple(ids[self.prefix:])
        if suffix in self.cache:
            return list(self.cache[suffix])
        text = self.decode(suffix)
        if text in self.responses:
            allowed = sorted(self.eos)
        elif any(value.startswith(text) for value in self.responses):
            allowed = []
            for token in self.candidates:
                continued = self.decode(suffix+(token,))
                if len(continued) > len(text) and continued.startswith(text) and any(
                        value.startswith(continued) for value in self.responses):
                    allowed.append(token)
        else:
            allowed = []
        if not allowed:
            self.stats['dead_ends'] += 1
            raise ValueError('Finite grammar dead end; no repair or fallback')
        self.cache[suffix] = tuple(allowed)
        return allowed

    def assert_complete(self, token_ids):
        ids = token_ids.tolist() if hasattr(token_ids, 'tolist') else list(token_ids)
        if not ids or any(type(i) is not int or i < 0 for i in ids):
            raise ValueError('Missing/invalid actual generated tokens')
        if ids[-1] in self.eos:
            ids = ids[:-1]
        if any(i in self.eos for i in ids):
            raise ValueError('EOS before complete canonical JSON')
        text = self.decode(ids)
        if text not in self.responses:
            raise ValueError('Incomplete/noncanonical actual JSON; no output repair')
        return json.loads(text)
