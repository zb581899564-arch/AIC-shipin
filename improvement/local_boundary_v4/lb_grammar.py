"""Finite three-decision generation grammar, strict full-context token decode.

Separate name prevents importing/replacing any frozen original B grammar.
"""
import json
from lb_contract import response_strings, verification_responses


class BoundaryGrammarError(RuntimeError):
    pass


def candidates(tokenizer, responses):
    chars = frozenset(''.join(responses))
    result = []
    for token_id in sorted(set(tokenizer.get_vocab().values())):
        piece = tokenizer.decode([token_id], skip_special_tokens=False,
                                 clean_up_tokenization_spaces=False)
        if piece and piece.isascii() and set(piece) <= chars:
            result.append(token_id)
    return tuple(result)


class BoundaryConstraint:
    def __init__(self, tokenizer, prompt_length, request, eos_token_ids,
                 candidate_token_ids=None, finite_responses=None):
        if type(prompt_length) is not int or prompt_length < 1:
            raise ValueError('Actual accepted processor prefix length required')
        if not eos_token_ids or any(type(i) is not int or i < 0 for i in eos_token_ids):
            raise ValueError('Explicit EOS token identities required')
        self.tokenizer = tokenizer
        self.prompt_length = prompt_length
        self.responses = response_strings(request) if finite_responses is None else tuple(finite_responses)
        if (not self.responses or len(set(self.responses)) != len(self.responses) or
                any(not isinstance(s, str) or not s.isascii() or
                    json.dumps(json.loads(s), separators=(',', ':')) != s for s in self.responses)):
            raise ValueError('Explicit unique canonical finite JSON decisions required')
        self.eos = frozenset(eos_token_ids)
        selected = candidates(tokenizer, self.responses) if candidate_token_ids is None else candidate_token_ids
        if any(type(i) is not int or i < 0 for i in selected):
            raise ValueError('Invalid generation candidate tokens')
        self.candidates = tuple(sorted(set(selected)-self.eos))
        self.cache = {}
        self.stats = dict(calls=0, cache_hits=0, full_context_decodes=0, dead_ends=0,
                          candidate_token_count=len(self.candidates))

    def decode(self, ids):
        self.stats['full_context_decodes'] += 1
        return self.tokenizer.decode(list(ids), skip_special_tokens=False,
                                     clean_up_tokenization_spaces=False)

    def __call__(self, batch_id, input_ids):
        del batch_id
        self.stats['calls'] += 1
        ids = input_ids.tolist() if hasattr(input_ids, 'tolist') else list(input_ids)
        if len(ids) < self.prompt_length or any(type(i) is not int or i < 0 for i in ids):
            raise BoundaryGrammarError('Actual prefix token identity changed')
        output = tuple(ids[self.prompt_length:])
        if output in self.cache:
            self.stats['cache_hits'] += 1
            return list(self.cache[output])
        text = self.decode(output)
        if text in self.responses:
            allowed = sorted(self.eos)
        elif any(r.startswith(text) for r in self.responses):
            allowed = []
            for token in self.candidates:
                next_text = self.decode(output+(token,))
                if (len(next_text) > len(text) and next_text.startswith(text) and
                        any(r.startswith(next_text) for r in self.responses)):
                    allowed.append(token)
        else:
            allowed = []
        if not allowed:
            self.stats['dead_ends'] += 1
            raise BoundaryGrammarError('No valid decision continuation; stop without fallback')
        self.cache[output] = tuple(allowed)
        return allowed

    def assert_complete(self, token_ids):
        ids = token_ids.tolist() if hasattr(token_ids, 'tolist') else list(token_ids)
        if not ids or any(type(i) is not int or i < 0 for i in ids):
            raise BoundaryGrammarError('Missing/invalid generated token identity')
        if ids[-1] in self.eos:
            ids = ids[:-1]
        if any(i in self.eos for i in ids):
            raise BoundaryGrammarError('EOS before complete decision')
        text = self.decode(ids)
        if text not in self.responses:
            raise BoundaryGrammarError('Incomplete decision; stop without repair')
        return json.loads(text)


class VerificationConstraint(BoundaryConstraint):
    """Draft only: not called by any current plan/CPU/GPU pilot entry."""
    def __init__(self, tokenizer, prompt_length, eos_token_ids, candidate_token_ids=None):
        super().__init__(tokenizer, prompt_length, None, eos_token_ids,
                         candidate_token_ids, finite_responses=verification_responses())
