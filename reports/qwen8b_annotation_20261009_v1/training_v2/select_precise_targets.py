"""Select precision-preserving human targets without changing successful prior exports."""
import collections
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main():
    blocks = [json.loads(s) for s in (HERE / 'human_native_blocks.jsonl').read_text(encoding='utf-8').splitlines()]
    lookup = {(b['source_id'], b['block_index']): b for b in blocks}
    histogram = collections.Counter()
    counts = {}
    for split in ('train', 'validation'):
        path = HERE / 'data' / f'temporal_precise_{split}.jsonl'
        assert not path.exists()
        old = [json.loads(s) for s in (HERE / 'data' / f'temporal_{split}.jsonl').read_text(encoding='utf-8').splitlines()]
        out = []
        for r in old:
            scores = [lookup[r['source_id'], i]['worker_score_sum'] for i in r['block_indices']]
            assert all(20 <= x <= 100 for x in scores)
            histogram.update(scores)
            prompt = r['messages'][0]['content']
            description = prompt[prompt.index('Frame 0:'):]
            prompt = ('Rate the visual importance of each shown frame within this ordered video sequence. '
                      'Use TVSum average importance: 1 low, 3 medium, 5 high. '
                      'Encode the average multiplied by 20 as an integer 20..100, preserving 0.05-point precision. '
                      'Return ONLY JSON {"scores_x20":[...]} with exactly one integer per shown frame, in the same order. '
                      'Divide each output by 20 to recover average importance. '
                      'This is frame importance, not semantic event start/end detection.\n' + description)
            row = dict(r, task='temporal_tvsum_importance_x20',
                       messages=[{'role': 'user', 'content': '<image>\n' * len(r['images']) + prompt},
                                 {'role': 'assistant', 'content': json.dumps({'scores_x20': scores}, separators=(',', ':'))}])
            out.append(row)
        path.write_text(''.join(json.dumps(r, ensure_ascii=False, separators=(',', ':')) + '\n' for r in out), encoding='utf-8')
        counts[split] = len(out)
    receipt = {'status': 'SELECTED_EXACT_HUMAN_MEAN_X20_TARGETS', 'files': counts,
               'target_histogram': dict(sorted(histogram.items())), 'distinct_targets': len(histogram),
               'definition': 'sum of twenty original worker ratings; divide by 20 to recover exact mean',
               'old_integer_targets_preserved_but_not_selected': True,
               'all_5943_human_blocks_preserved': sum(histogram.values()) == len(blocks),
               'artifacts': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in (HERE / 'data').glob('temporal_precise_*.jsonl')}}
    (HERE / 'precise_target_selection.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in receipt.items() if k not in ('target_histogram', 'artifacts')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
