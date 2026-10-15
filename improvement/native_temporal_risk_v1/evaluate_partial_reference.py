"""Grade only the fixed, partial dev observations; never infer a quality PASS."""
import hashlib
import json
import sys
from fractions import Fraction as F
from pathlib import Path


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def evaluate(reference_path, replay_bundle_path):
    reference = read(reference_path)
    bundle = read(replay_bundle_path)
    assert bundle['replay']['status'] == 'PASS_SIX_DENSE128_INDEPENDENT_CPU_REPLAYS_NOT_QUALITY'
    assert bundle['gpu']['actual_model_calls'] == 6
    cases = {x['case_id']: x for x in reference['cases']}
    done = bundle['done_by_case']
    assert len(cases) == len(done) == 6 and set(cases) == set(done)
    rows = []
    for case, ref in cases.items():
        answer = done[case]
        window = answer['source_window']
        assert window['source_id'] == case and window['source_sha256'] == ref['source_sha256']
        assert answer['output_valid'] and answer['parse_errors'] == []
        assert len(ref['states']) == len(ref['sample_exact_pts']) == 64
        origin = F(window['exact_raw_start'])
        segments = [(origin + F(str(a)), origin + F(str(b))) for a, b in answer['parsed_segments']]
        hits = {state: 0 for state in ('KEEP', 'ORDINARY', 'UNKNOWN')}
        counts = {state: 0 for state in hits}
        for state, timestamp in zip(ref['states'], ref['sample_exact_pts']):
            counts[state] += 1
            hits[state] += any(a <= F(timestamp) < b for a, b in segments)
        assert counts == ref['counts']
        rows.append(dict(case_id=case, counts=counts, selected_observations=hits,
                         parsed_segments=answer['parsed_segments'],
                         selected_native_frames=sum(stop-first for first, stop in answer['native_frame_realizability']['ranges']),
                         selected_seconds=str(sum((b-a for a, b in segments), F(0)))))
    known_keep_sources = [row for row in rows if row['counts']['KEEP']]
    assert len(known_keep_sources) == 3
    obviously_bad = all(row['selected_observations']['KEEP'] == 0 for row in known_keep_sources)
    return dict(status='STOP_OBVIOUS_CORE_ACTION_LOSS' if obviously_bad else 'NO_PREDECLARED_OBVIOUS_LOSS_STOP_RISK_ONLY',
                reference_sha256=hashlib.sha256(Path(reference_path).read_bytes()).hexdigest(),
                replay_bundle_sha256=hashlib.sha256(Path(replay_bundle_path).read_bytes()).hexdigest(),
                rows=rows, predeclared_obviously_bad=obviously_bad,
                formal_quality_reference='FAILED_PRESERVED', scientific_quality_pass=False,
                limitation='Dual AI partial silver observations, 287 UNKNOWN; no formal quality or official score claim',
                new_model_calls=0, new_optimizer_updates=0, official_score=None)


if __name__ == '__main__':
    assert len(sys.argv) == 4
    result = evaluate(sys.argv[1], sys.argv[2])
    with Path(sys.argv[3]).open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2)
        stream.write('\n')
    print(json.dumps(result, ensure_ascii=False))
