"""Bind existing accepted VERIFY assets once, while training uses the GPU."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

from pathlib import Path
import traceback

import torch

from parallel_verify_catalog109 import catalog
from t_io import ROOT, identity, save

OUT = ROOT / 'parallel_verify_catalog109'


def main():
    OUT.mkdir()
    torch.set_num_threads(2)
    values, proofs = catalog()
    if torch.cuda.is_initialized():
        raise ValueError('Existing success-catalog binding initialized CUDA')
    save(OUT / 'completion.json', dict(state='ALL_PRIOR_EXACT_VERIFY_ADOPTION_CATALOG109_BOUND',
        catalog=values, original_first_QA=proofs, exact_successful_tasks=len(values),
        code={n: identity(Path(__file__).with_name(n)) for n in
              ['parallel_catalog_contract109.py', 'parallel_verify_catalog109.py']},
        old_model_token_QA_or_metrics_repeated=0, new_model_calls=0,
        no_new_policy_quality_or_confirmation_labels_read=True))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(), no_old_calls_repeated=True))
        raise
