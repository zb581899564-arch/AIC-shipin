"""CPU-only lifecycle check for bounded loading and immutable shared visual tensors."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

from unittest.mock import patch

import torch

from native_prepared103 import Prefetch, causal_values, unchanged, versions
from t_io import ROOT, save


def main():
    observed = []
    def loader(item):
        observed.append(item)
        return dict(pixel_values_videos=torch.tensor([item], dtype=torch.float32))
    with Prefetch([1, 2, 3], loader) as source:
        actual = [(item, int(value['pixel_values_videos'].item())) for item, value in source]
    if actual != [(1, 1), (2, 2), (3, 3)] or observed != [1, 2, 3]:
        raise ValueError('One-worker prefetch repeated or reordered a physical input')
    video = torch.arange(12).reshape(3, 4)
    original = dict(input_ids=torch.tensor([[1, 2]]), attention_mask=torch.ones((1, 2), dtype=torch.long),
                    pixel_values_videos=video)
    expected = versions(original)
    history = dict(input_ids=torch.tensor([[1, 2, 3, 4]]), attention_mask=torch.ones((1, 4), dtype=torch.long))
    with patch.object(torch.Tensor, 'cuda', lambda self: self):
        teacher = causal_values(original, history)
    unchanged(original, expected)
    if teacher['pixel_values_videos'] is not video or torch.equal(teacher['input_ids'], original['input_ids']):
        raise ValueError('Teacher must share unmodified visual data and use separate causal text')
    video.add_(1)
    try:
        unchanged(original, expected)
    except ValueError:
        pass
    else:
        raise ValueError('A mutated shared tensor was not rejected')
    if torch.cuda.is_initialized():
        raise ValueError('CPU-only prefetch contract initialized CUDA')
    out = ROOT / 'native_prepared_contract103'
    out.mkdir()
    save(out / 'completion.json', dict(state='PASS_THREE_PREPARED_INPUT_LIFECYCLE_CPU_CONTRACTS',
        deterministic_one_load_per_case=True, unchanged_visual_storage_shared=True,
        in_place_mutation_rejected=True, real8B_forwards=0, no_old_actual_input_QA_repeated=True))


if __name__ == '__main__':
    main()
