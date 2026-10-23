"""First finite-action argmax/token/geometry QA; aliases adopt their token proof."""
import math
from fractions import Fraction

from native_codec98 import NativeChoices
from native_render100 import render
from t_io import check, identity, read, save


def audit(ref, source, case, proof, code, tokenizer, folder, token_proofs):
    row = read(check(ref)); cpu = read(check(proof)); raw = read(check(row['raw']))
    if (row['case'] != case.name or row['source'] != source.sid or row['CPU'] != proof
            or row['original_CPU'] != case.CPU or raw['codec'] != code
            or raw['actual_model_state'] != row['actual_model_state']
            or raw['actual_GPU_signature'] != cpu['actual_signature']
            or raw['prefix'] != cpu['input_tokens']):
        raise ValueError('First native output/input/model/codec binding differs')
    rule = NativeChoices(cpu['input_tokens'], code); selected = rule.parse(raw['tokens'])
    previous = token_proofs.get(row['raw']['sha256'])
    if previous is None:
        if len(raw['allowed']) != 65 or len(raw['allowed_logits']) != 65:
            raise ValueError('Complete first native generation score trace absent')
        for j, (token, domain, values) in enumerate(zip(raw['tokens'], raw['allowed'], raw['allowed_logits'])):
            if domain != rule.allowed(raw['tokens'][:j]) or len(values) != len(domain) or not all(math.isfinite(v) for v in values):
                raise ValueError('Actual finite native policy state/logit trace differs')
            if token != min(t for t, value in zip(domain, values) if value == max(values)):
                raise ValueError('First native policy full-domain greedy tie break differs')
        if tokenizer.decode(raw['tokens'], skip_special_tokens=True,
                clean_up_tokenization_spaces=False) != raw['text']:
            raise ValueError('Actual native token/text replay differs')
    elif row['physical_alias'] is None:
        raise ValueError('A repeated native physical output lacks an explicit alias')
    expected = render(source, case, cpu['source_native_cells'], selected)
    if any(row[key] != value for key, value in expected.items()):
        raise ValueError('First actual cell/native PTS/parser/empty replay differs')
    path = folder / (case.name + '.json')
    save(path, dict(state='PASS_FIRST_ANCHORED_NATIVE_ACTION_TOKEN_GREEDY_AND_PTS_CPU',
        actual_output=ref, actual_input=proof, selected_native_frames=expected['native_frames'],
        successful_empty=expected['status'] == 'LEGAL_EMPTY',
        physical_token_QA_adopted=previous, no_human_labels_read=True))
    current = identity(path); token_proofs.setdefault(row['raw']['sha256'], current)
    origin = Fraction(case.meta['window_start'])
    mask = source.timeline.intervals([(origin + Fraction(a), origin + Fraction(b))
                                      for a, b in row['segments']])
    return mask, current
