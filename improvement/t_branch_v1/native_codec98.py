"""Anchored finite native-cell choices, independent of timestamp string decoding."""
import numpy as np
import torch

ANCHORS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef'


def vocabulary(tokenizer, eos):
    words = list(ANCHORS) + ['Yes', 'No']
    ids = []
    for word in words:
        encoded = tokenizer.encode(word, add_special_tokens=False)
        if len(encoded) != 1 or tokenizer.decode(encoded, clean_up_tokenization_spaces=False) != word:
            raise ValueError('Native action codewords must be exact distinct single tokens')
        ids.append(encoded[0])
    if len(set(ids)) != 34 or set(ids) & set(eos):
        raise ValueError('Native action codewords collide with each other or actual EOS')
    return dict(anchors=ids[:32], Yes=ids[32], No=ids[33], EOS=min(eos))


class NativeChoices:
    def __init__(self, prefix, code):
        self.prefix, self.code = prefix, code

    def allowed(self, suffix):
        if len(suffix) > 64:
            raise ValueError('Native choice sequence has trailing data beyond32 anchored choices')
        for j, token in enumerate(suffix):
            valid = [self.code['anchors'][j // 2]] if j % 2 == 0 else [self.code['Yes'], self.code['No']]
            if token not in valid:
                raise ValueError('Actual native action escaped its finite anchored policy')
        if len(suffix) == 64:
            return [self.code['EOS']]
        if len(suffix) % 2 == 0:
            return [self.code['anchors'][len(suffix) // 2]]
        return sorted([self.code['Yes'], self.code['No']])

    def __call__(self, batch, tokens):
        del batch
        values = tokens.tolist()
        if len(values) < self.prefix:
            raise ValueError('Actual native policy prefix was shortened')
        return self.allowed(values[self.prefix:])

    def parse(self, tokens):
        if len(tokens) != 65 or tokens[-1] != self.code['EOS']:
            raise ValueError('Incomplete model execution cannot become a successful empty choice')
        self.allowed(tokens[:-1])
        return np.array([token == self.code['Yes'] for token in tokens[1:64:2]], dtype=bool)


def preference_loss(logits, positive, negative, source_weight):
    """Source-global coefficients retain all reviewers and zero task-unobserved cells."""
    if logits.shape != (32, 2) or positive.shape != (32,) or negative.shape != (32,):
        raise ValueError('Exact32 original source-weighted native action cells required')
    if (not torch.isfinite(logits).all() or not torch.isfinite(positive).all()
            or not torch.isfinite(negative).all() or (positive < 0).any() or (negative < 0).any()
            or not 0 < source_weight <= 1):
        raise ValueError('Actual native preference logits/coefficients/denominator invalid')
    logp = torch.nn.functional.log_softmax(logits.float(), dim=-1)
    value = -(positive.float() * logp[:, 0] + negative.float() * logp[:, 1]).sum()
    return value * source_weight, logp


def causal_history(prefix, generated, code):
    """Train at choice positions following actual generated anchors/history only."""
    NativeChoices(prefix.shape[1], code).parse(generated)
    suffix = torch.tensor([generated[:-1]], dtype=torch.long)
    values = torch.cat([prefix, suffix], dim=1)
    return dict(input_ids=values, attention_mask=torch.ones_like(values),
                logits_to_keep=list(range(prefix.shape[1], prefix.shape[1] + 64, 2)))
