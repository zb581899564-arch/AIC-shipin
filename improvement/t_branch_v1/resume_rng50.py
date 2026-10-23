"""Replay sampling RNG consumption from saved actions, without model generation."""
import torch

from t_io import check, read


def kernel_contract(vocabulary):
    """Check actual CUDA multinomial consumption at the original full shape."""
    start = torch.cuda.get_rng_state()
    endings = []
    for support in [1, 2, vocabulary]:
        torch.cuda.set_rng_state(start)
        scores = torch.zeros((1, vocabulary), dtype=torch.float32, device='cuda')
        scores[0, :support] = 1 / support
        torch.multinomial(scores, num_samples=1)
        endings.append(torch.cuda.get_rng_state())
    torch.cuda.set_rng_state(start)
    if any(not torch.equal(endings[0], value) for value in endings[1:]):
        raise ValueError('Actual CUDA draw consumption depends on support; cannot resume RNG')
    return dict(actual_kernel='torch.multinomial(float32[1,V],num_samples=1)',
        vocabulary=vocabulary, support_independent_counter_verified=[1, 2, vocabulary],
        no_model_generation=True)


def advance(result, vocabulary):
    tokens = result['tokens']
    payload = None
    if 'allowed_scores' in result:
        payload = torch.load(check(result['allowed_scores']), map_location='cpu', weights_only=True)
        if payload['tokens'] != tokens:
            raise ValueError('Persisted sampling actions differ from accepted raw')
    for index, token in enumerate(tokens):
        if payload is None:
            # Only for an actually complete raw whose score serialization was
            # interrupted. No logits/probabilities are invented or claimed.
            probabilities = torch.full((1, vocabulary), 1 / vocabulary, device='cuda', dtype=torch.float32)
        else:
            scores = torch.full((1, vocabulary), -torch.inf, device='cuda', dtype=torch.float32)
            ids = torch.tensor(payload['allowed'][index], device='cuda')
            scores[0, ids] = payload['scores'][index].cuda()
            probabilities = torch.softmax(scores, dim=-1)
        drawn = int(torch.multinomial(probabilities, num_samples=1)[0, 0])
        if payload is not None and drawn != token:
            raise ValueError('Saved actual sampled token cannot be reproduced from checkpoint RNG')
    return dict(actual_draws_replayed=len(tokens), model_calls=0,
        sampled_choices_reproduced=payload is not None,
        raw_only_counter_consumption=payload is None,
        no_new_probability_or_model_quality_claim=True)
