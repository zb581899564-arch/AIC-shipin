"""First real masked-attention proof; never apply the old unmasked reference."""
import numpy as np
import torch

from localized_visual121_cpu import reference
from t_io import check, identity, read, save
from visual_query119_cpu import native_check, quantized_check, validate_features


def check_case(source, case, proof, result, code, accepted_mask, folder):
    manifest = read(check(result['witnesses'])); output = read(check(result['output']))
    raw = read(check(output['raw'])); operator = read(check(result['operator']))
    if (output['CPU'] != proof or raw['actual_input'] != proof or operator['actual_input'] != proof
            or operator['actual_output'] != result['output'] or operator['visibility'] != accepted_mask):
        raise ValueError('Actual masked output/operator/input identities differ')
    with np.load(check(accepted_mask), allow_pickle=False) as data:
        visibility = torch.from_numpy(data['visibility'].copy())
    permanent = torch.load(check(manifest['permanent']), map_location='cpu', weights_only=True)
    visual = torch.load(check(manifest['temporary_visual']), map_location='cpu', weights_only=True)
    attention = torch.load(check(manifest['temporary_attention']), map_location='cpu', weights_only=True)
    full = torch.load(check(manifest['temporary_full_vocab']), map_location='cpu', weights_only=True)['logits']
    features = validate_features(permanent, visual)
    if attention['native_query_indices'] != [0, 31] or visibility.shape != (32, manifest['prefix_tokens']):
        raise ValueError('Actual witness branch or frozen visibility shape differs')
    expected = reference(*(attention[key].float() for key in
        ['query', 'key', 'value', 'prefix_key', 'prefix_value']), attention['scaling'], visibility[[0, 31]])
    attention_check = quantized_check(attention['actual_attention_output'], expected)
    binary = full[:, [code['Yes'], code['No']]].float()
    if (full.ndim != 2 or full.shape[0] != 32 or not torch.isfinite(full).all()
            or not torch.equal(binary, permanent['binary_logits']) or binary.tolist() != raw['binary_logits']):
        raise ValueError('Actual masked full-vocabulary/binary output differs')
    projection = permanent['actual_final_hidden'].double() @ permanent['actual_original_LM_rows'].double().T
    projection_check = quantized_check(full[:, [code['Yes'], code['No']]], projection)
    native = native_check(source, case, proof, output, raw, binary, code)
    path = folder / (case.name + '.json')
    save(path, dict(state='FIRST_REAL8B_MASKED_ATTENTION_VISUAL_LM_NATIVE_CPU_PASS',
        actual_output=result['output'], actual_operator=result['operator'], actual_input=proof,
        permanent_witness=manifest['permanent'], source_visual_mapping=features,
        actual_masked_attention=attention_check, original_LM_projection=projection_check,
        native=native, source_labels_unread=True, original_input_and_mask_CPU_adopted=True))
    return identity(path), [manifest[key] for key in
        ['temporary_visual', 'temporary_attention', 'temporary_full_vocab']]
