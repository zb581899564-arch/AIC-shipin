"""Adopt successful RGB, token and native target identities; do not recreate them."""
import numpy as np
from common import ROOT, PREVIOUS, checked, read, ref, write


def main():
    previous = read(PREVIOUS / 'completion.json')
    assert previous['status'] == 'STOP_FROZEN_SEMANTIC_GROUNDING'
    inputs = read(PREVIOUS / 'input_acceptance.json')
    assert len(inputs['sources']) == 8 and len(inputs['queries']) == 26
    tokens = np.load(checked(inputs['tokens']), allow_pickle=False)
    # The adopted OpenAI tokenizer emits int32 on current Torch. Both integer
    # dtypes are accepted by Embedding; preserve its successful exact bytes.
    assert tokens.shape == (26, 77) and tokens.dtype in (np.int32, np.int64)
    assert np.all((0 <= tokens) & (tokens < 49408))
    for source in inputs['sources']:
        rgb = np.load(checked(source['rgb']), mmap_mode='r', allow_pickle=False)
        assert rgb.shape == (source['native_cells'], 8, 224, 224, 3)
        assert rgb.dtype == np.uint8
        target = np.load(checked(source['target']), allow_pickle=False)
        assert target['counts'].sum() == source['native_frames']
    assert sum(s['native_cells'] for s in inputs['sources']) == 512
    write(ROOT / 'input_acceptance.json', dict(**inputs,
          explicit_adoption=ref(PREVIOUS / 'input_acceptance.json'),
          previous_quality=ref(PREVIOUS / 'review.json'),
          adopted_old_stop=True, new_decode=0, new_processor=0,
          control='Reverse the same8frames within every cell; no pixels removed or added'))


if __name__ == '__main__':
    main()
