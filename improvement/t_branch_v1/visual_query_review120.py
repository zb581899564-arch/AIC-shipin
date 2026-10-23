"""Same first119 real-transform checks, with an explicit new output root."""
import torch

from t_io import check, identity, read, save
from visual_query119_cpu import native_check, quantized_check, validate_features
from shared_visual_query118_cpu import concatenated_attention


def check_case(source, case, proof, result, code, folder):
    manifest = read(check(result['witnesses'])); output = read(check(result['output']))
    raw = read(check(output['raw']))
    if output['CPU'] != proof or raw['actual_input'] != proof:
        raise ValueError('Remaining local-visual output belongs to another accepted source input')
    permanent = torch.load(check(manifest['permanent']), map_location='cpu', weights_only=True)
    visual = torch.load(check(manifest['temporary_visual']), map_location='cpu', weights_only=True)
    attention = torch.load(check(manifest['temporary_attention']), map_location='cpu', weights_only=True)
    full = torch.load(check(manifest['temporary_full_vocab']), map_location='cpu', weights_only=True)['logits']
    features = validate_features(permanent, visual)
    expected_attention = concatenated_attention(*(attention[k].float() for k in
        ['query', 'key', 'value', 'prefix_key', 'prefix_value']), attention['scaling'])
    checked_attention = quantized_check(attention['actual_attention_output'], expected_attention)
    binary = full[:, [code['Yes'], code['No']]].float()
    if (full.ndim != 2 or full.shape[0] != 32 or not torch.isfinite(full).all()
            or not torch.equal(binary, permanent['binary_logits']) or binary.tolist() != raw['binary_logits']):
        raise ValueError('First remaining original full vocabulary/binary readout differs')
    projection = permanent['actual_final_hidden'].double() @ permanent['actual_original_LM_rows'].double().T
    checked_projection = quantized_check(full[:, [code['Yes'], code['No']]], projection)
    native = native_check(source, case, proof, output, raw, binary, code)
    path = folder / (case.name + '.json')
    save(path, dict(state='FIRST_REMAINING_REAL_VISUAL_ATTENTION_LM_NATIVE_CPU_PASS',
        actual_output=result['output'], actual_input=proof, permanent_witness=manifest['permanent'],
        source_visual_mapping=features, actual_attention=checked_attention,
        original_LM_projection=checked_projection, native=native, source_labels_unread=True))
    return identity(path), [manifest[key] for key in
        ['temporary_visual', 'temporary_attention', 'temporary_full_vocab']]
