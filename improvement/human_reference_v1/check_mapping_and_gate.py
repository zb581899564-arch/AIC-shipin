"""Hand-built alignment failures and early rejection before a prediction read."""
import copy
import json
import tempfile
from pathlib import Path
from native_mapping import validate_mapping
from evaluate_candidates import main as compare


if __name__ == '__main__':
    source = dict(source_name='hand_case', annotation_frames=3, annotation_fps=2,
                  annotation_duration=1.5, member=dict(bytes=12, crc32='12345678'))
    clock = dict(source_name='hand_case', source_bytes=12, source_crc32='12345678',
                 source_sha256='a'*64, n_frames=3, normalized_exact_pts=['0', '1/2', '1'],
                 physical_end_exact='3/2')
    assert validate_mapping(source, clock)['human_frames'] == 3
    for key, changed in [('n_frames', 2), ('normalized_exact_pts', ['0', '1/2']),
                         ('normalized_exact_pts', ['0', '1/2', '1/2']),
                         ('source_crc32', '87654321'), ('physical_end_exact', '4')]:
        broken = copy.deepcopy(clock)
        broken[key] = changed
        try:
            validate_mapping(source, broken)
        except ValueError:
            pass
        else:
            raise AssertionError('Ambiguous original mapping accepted: ' + key)
    with tempfile.TemporaryDirectory(prefix='aic_human_gate_') as directory:
        root = Path(directory)
        (root/'native_input_acceptance.json').write_text(json.dumps(dict(status='FAILED')))
        # Invalid JSON would throw JSONDecodeError if the early rejection were bypassed.
        (root/'developer_prediction_export.json').write_text('THIS MUST NOT BE READ')
        try:
            compare(root)
        except ValueError as error:
            assert str(error) == 'All registered media/native inputs must pass before prediction access'
        else:
            raise AssertionError('Failed input admission reached actual predictions')
    print('PASS hand mapping, length/duplicate-PTS/CRC/duration rejects, failed-input gate before prediction access')
