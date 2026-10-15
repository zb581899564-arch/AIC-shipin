"""Strict finite KEEP/UNKNOWN/DROP grammar, full-context generated token decode."""
import json
from cv_contract import responses


class VerifyGrammarError(RuntimeError):
    pass


def candidate_tokens(tokenizer, values):
    chars = frozenset(''.join(values))
    result = []
    for token in sorted(set(tokenizer.get_vocab().values())):
        piece = tokenizer.decode([token], skip_special_tokens=False, clean_up_tokenization_spaces=False)
        if piece and piece.isascii() and set(piece) <= chars:
            result.append(token)
    return tuple(result)


class VerifyConstraint:
    def __init__(self, tokenizer, prompt_length, req, eos_token_ids, candidates=None):
        if type(prompt_length) is not int or prompt_length < 1:
            raise ValueError('Actual accepted prompt token prefix required')
        if not eos_token_ids or any(type(i) is not int or i < 0 for i in eos_token_ids):
            raise ValueError('Explicit actual EOS tokens required')
        self.tokenizer, self.prompt_length = tokenizer, prompt_length
        self.responses, self.eos = responses(req), frozenset(eos_token_ids)
        selected = candidate_tokens(tokenizer, self.responses) if candidates is None else candidates
        self.candidates = tuple(sorted(set(selected)-self.eos))
        self.cache = {}
        self.stats = dict(calls=0, full_context_decodes=0, dead_ends=0)

    def decode(self, ids):
        self.stats['full_context_decodes'] += 1
        return self.tokenizer.decode(list(ids), skip_special_tokens=False, clean_up_tokenization_spaces=False)

    def __call__(self, batch_id, input_ids):
        del batch_id
        self.stats['calls'] += 1
        ids = input_ids.tolist() if hasattr(input_ids, 'tolist') else list(input_ids)
        if len(ids) < self.prompt_length or any(type(i) is not int or i < 0 for i in ids):
            raise VerifyGrammarError('Actual generated-prefix token identity changed')
        suffix = tuple(ids[self.prompt_length:])
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
            raise VerifyGrammarError('No valid continuation; block this attempt without fallback')
        self.cache[suffix] = tuple(allowed)
        return allowed

    def assert_complete(self, token_ids):
        ids = token_ids.tolist() if hasattr(token_ids, 'tolist') else list(token_ids)
        if not ids or any(type(i) is not int or i < 0 for i in ids):
            raise VerifyGrammarError('Missing/invalid actual generated tokens')
        if ids[-1] in self.eos:
            ids = ids[:-1]
        if any(token in self.eos for token in ids):
            raise VerifyGrammarError('EOS before complete canonical JSON')
        text = self.decode(ids)
        if text not in self.responses:
            raise VerifyGrammarError('Incomplete/invalid raw JSON; no repair')
        return json.loads(text)
