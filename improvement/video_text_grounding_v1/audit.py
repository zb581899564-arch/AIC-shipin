"""Independent first output/dense AP review, with no repeated model forward."""
import numpy as np
from common import ROOT, adopted_module, checked, read, ref, write

dense_ap = adopted_module('audit').dense_ap


def audited_source(source):
    primary = read(ROOT / 'outputs' / source['sid'] / 'acceptance.json')
    streams = {}
    batches = 0
    for mode in ['real', 'reverse']:
        parts = []
        for row in sorted((r for r in primary['outputs'] if r['mode'] == mode), key=lambda r: r['start']):
            data = np.load(checked(row['output']), allow_pickle=False)
            video = data['video'].astype(np.float64)
            text = data['text'].astype(np.float64)
            assert np.allclose(np.linalg.norm(video, axis=-1), 1., atol=1e-5)
            assert np.allclose(np.linalg.norm(text, axis=-1), 1., atol=1e-5)
            replay = np.einsum('bd,bkd->bk', video, text)
            assert np.allclose(replay, data['scores'], atol=2e-6, rtol=1e-5)
            # Rank the actual saved primary scores, not float64 replay roundoff.
            parts.append(data['scores'])
            batches += 1
        streams[mode] = np.concatenate(parts)
        assert streams[mode].shape == (source['native_cells'], 26)
    return streams, batches


def main():
    inputs = read(ROOT / 'input_acceptance.json')
    review = read(ROOT / 'review.json')
    batches = comparisons = 0
    for index, source in enumerate(inputs['sources']):
        scores, count = audited_source(source)
        batches += count
        target = np.load(checked(source['target']), allow_pickle=False)
        ids = source['query_ids']
        other = inputs['sources'][(index + 1) % 8]['query_ids']
        expected = next(s for s in review['sources'] if s['sid'] == source['sid'])
        for j, query in enumerate(ids):
            streams = dict(correct=scores['real'][:, query], reverse=scores['reverse'][:, query],
                  within_query_swap=scores['real'][:, ids[(j + 1) % len(ids)]],
                  cross_video_query_swap=scores['real'][:, other[j % len(other)]],
                  temporal_shift=np.roll(scores['real'][:, query], len(target['counts']) // 2))
            for name, values in streams.items():
                measured = dense_ap(values, target['positive'][j], target['counts'])
                assert abs(measured - expected['events'][j]['AP'][name]) < 1e-12
                comparisons += 1
    inference = read(ROOT / 'inference_completion.json')
    assert batches == inference['actual_video_forward_batches']
    assert comparisons == 130
    write(ROOT / 'independent_cpu_audit.json', dict(status='PASS_COMPONENT_DOT_AND_DENSE_AP',
          forward_batches_replayed_on_CPU=batches, dense_AP_comparisons=comparisons,
          real_new_model_calls=0, targets_in_encoder=False, review=ref(ROOT / 'review.json')))


if __name__ == '__main__':
    main()
