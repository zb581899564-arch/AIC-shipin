"""Preserve the initial review and record the contradictory full-size evidence."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / 'reports/reliable_reference_20261012_v1'


def main():
    paths = [REPORT / f'reviewer_{side}_detail02.json' for side in ('a', 'b')]
    reviews = [json.loads(path.read_text(encoding='utf-8')) for path in paths]
    for side, review in zip(('A', 'B'), reviews):
        assert review['reviewer'] == side
        assert review['prediction_blind'] is True
        assert review['level'] == 'AI_REVIEWED_SILVER_NOT_HUMAN_GOLD'
        assert review['end_band_exact'] is None
        assert 'R19_ID180.jpg' in review['viewed_files']
    receipt = dict(
        status='R19_LAST_VISIBLE_FLOW_END_UNKNOWN',
        case_id='R19',
        event_convention='First liquid contact with pan through last visible liquid flow',
        first_contact_supported_band_exact=['113', '2826/25'],
        end_band_exact=None,
        last_checked_visible_flow_exact='2857/25',
        supersedes_field='R19 pouring event end_band_exact in dense02_consensus.json',
        initial_claimed_end_band_exact=['571/5', '572/5'],
        corrected_two_ended_dense_events=1,
        rationale='Both full-size reviews observe flow after the old claimed end; withdrawal and bulk-flow thinning are distinct phases.',
        review_sha256={side: hashlib.sha256(path.read_bytes()).hexdigest()
                       for side, path in zip(('a', 'b'), paths)},
        original_reviews_and_consensus_preserved=True,
        candidate_predictions_read=False,
        reference_quality_pass=False,
    )
    with (REPORT / 'detail02_adjudication.json').open('x', encoding='utf-8') as handle:
        json.dump(receipt, handle, ensure_ascii=False, indent=2)
    state_path = REPORT / 'current_state.json'
    state = json.loads(state_path.read_text(encoding='utf-8-sig'))
    state['dense02']['detail_adjudication'] = 'detail02_adjudication.json'
    state['dense02']['corrected_two_ended_events'] = 1
    state['dense02']['R19_last_flow_end_unknown'] = True
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(receipt, ensure_ascii=False))


if __name__ == '__main__':
    main()
