"""Causal suffix and actual allowed actions for self-sampled constrained sequences."""
import torch


def causal_suffix(prefix, tokens):
    if prefix.ndim != 2 or prefix.shape[0] != 1 or prefix.dtype != torch.long:
        raise ValueError('One original integer text prefix is required')
    if not tokens or not all(type(value) is int and value >= 0 for value in tokens):
        raise ValueError('Actual nonempty generated token suffix is required')
    target = torch.tensor([tokens], dtype=torch.long, device=prefix.device)
    joined = torch.cat((prefix, target[:, :-1]), dim=1)
    # Last L causal positions start at the last prefix token and predict all L
    # sampled actions, including EOS. No human reference text is appended.
    positions = list(range(prefix.shape[1] - 1, joined.shape[1]))
    if len(positions) != len(tokens) or positions[-1] != joined.shape[1] - 1:
        raise ValueError('Causal target/prediction positions differ')
    return dict(input_ids=joined, attention_mask=torch.ones_like(joined),
                logits_to_keep=len(tokens), targets=target, causal_positions=positions)


def actual_allowed_states(prefix, tokens, grammar):
    actions = []
    for index, token in enumerate(tokens):
        preceding = torch.cat((prefix[0], torch.tensor(tokens[:index], dtype=torch.long, device=prefix.device)))
        allowed = list(grammar(0, preceding))
        if not allowed or len(allowed) != len(set(allowed)) or token not in allowed:
            raise ValueError('Actual sampled action not uniquely supported by its grammar state')
        actions.append(allowed)
    grammar.assert_complete(torch.tensor(tokens, dtype=torch.long, device=prefix.device))
    return actions
