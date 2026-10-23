"""First independent binary-policy/native rendering audit, no labels or model calls."""
from fractions import Fraction
import hashlib
import math

import numpy as np

from t_io import check, identity, read, save


def audit(ref, source, case, proof, code, folder):
    accepted = read(check(ref))
    cpu = read(check(proof))
    raw = read(check(accepted['raw']))
    if (accepted['case'] != case.name or accepted['source'] != source.sid
            or accepted['CPU'] != proof or accepted['original_CPU'] != case.CPU
            or raw['actual_input'] != proof or raw['actual_GPU_signature'] != cpu['actual_signature']
            or raw['query_code'] != code or raw['query_positions'] != cpu['query_positions']
            or raw['actual_model_state'] != accepted['actual_model_state']
            or raw['model_role'] != accepted['model_role'] or raw['actual_forward_calls'] != 1):
        raise ValueError('Actual parallel output/input/model/query contract binding differs')
    z = raw['binary_logits']
    if len(z) != 32 or any(len(row) != 2 or not all(math.isfinite(x) for x in row) for row in z):
        raise ValueError('An incomplete parallel output became a legal empty selection')
    chosen = [min([code['Yes'], code['No']], key=lambda token:
        (-values[0 if token == code['Yes'] else 1], token)) for values in z]
    picked = [token == code['Yes'] for token in chosen]
    if chosen != raw['selected_token_ids'] or picked != accepted['selected_cells']:
        raise ValueError('Actual independent Yes/No argmax/tie convention differs')
    mask = np.zeros(len(source.timeline.points), dtype=bool)
    cells = cpu['source_native_cells']
    if len(cells) != 32:
        raise ValueError('Actual source native-cell domain is incomplete')
    for selected, (start, stop) in zip(picked, cells):
        if not 0 <= start < stop <= len(mask):
            raise ValueError('A parallel native action has no original frame support')
        if selected:
            mask[start:stop] = True
    origin = Fraction(case.meta['window_start'])
    reconstructed = source.timeline.intervals([(origin + Fraction(a), origin + Fraction(b))
                                               for a, b in accepted['segments']])
    if (not np.array_equal(mask, reconstructed) or accepted['native_frames'] != int(mask.sum())
            or accepted['native_mask_sha256'] != hashlib.sha256(mask.tobytes()).hexdigest()
            or accepted['status'] != ('MODEL_OK' if mask.any() else 'LEGAL_EMPTY')):
        raise ValueError('Independent original native support/interval/empty reconstruction differs')
    path = folder / (case.name + '.json')
    save(path, dict(state='FIRST_PARALLEL_NATIVE_ARGMAX_AND_PTS_CPU_PASS', actual_output=ref,
        actual_input=proof, all32_choices_checked=True, original_native_frames=int(mask.sum()),
        successful_empty=not bool(mask.any()), no_human_labels_read=True))
    return mask, identity(path)
