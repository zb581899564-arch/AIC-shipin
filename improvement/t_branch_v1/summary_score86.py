"""Independent NumPy FP64 reduction of first new full-vocabulary greedy scores."""
import numpy as np
import torch

from t_io import check


def full_greedy(raw, maximum_tokens):
    scores = torch.load(check(raw['temporary_scores']), map_location='cpu', weights_only=True)['scores'].numpy().astype(np.float64)
    ids = np.asarray(raw['tokens'], dtype=np.int64)
    if (scores.ndim != 2 or len(scores) != len(ids) or not 0 < len(ids) <= maximum_tokens
            or np.isnan(scores).any() or np.isposinf(scores).any()
            or not np.array_equal(scores.argmax(axis=1), ids)
            or ids[-1] not in raw['eos'] or any(t in raw['eos'] for t in ids[:-1])):
        raise ValueError('Actual free output is not a complete finite greedy EOS sequence')
    maximum = scores.max(axis=1)
    norm = maximum + np.log(np.exp(scores - maximum[:, None]).sum(axis=1))
    logp = scores[np.arange(len(ids)), ids] - norm
    if not np.allclose(logp, raw['selected_logp'], atol=2e-5, rtol=2e-5):
        raise ValueError('First independent full-vocabulary probability reduction differs')
    return ids, dict(full_vocabulary=scores.shape[1], CPU_mean_logp=float(logp.mean()),
                     all_greedy_argmax=True, EOT_observed=True)
