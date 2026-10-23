"""First actual8B visual grouping, read-only attention, LM and native-output QA."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

import hashlib
from pathlib import Path

import numpy as np
import torch

from parallel_train108 import cases
from shared_visual_query118_cpu import concatenated_attention
from t_io import ROOT, check, identity, read, save

OUT = ROOT / 'visual_query_engine119'
TEMP = Path('/dev/shm/aic_T_visual_query119_first')


def quantized_check(actual, expected):
    epsilon = torch.finfo(actual.dtype).eps
    expected = expected.double()
    exponent = torch.floor(torch.log2(expected.abs().clamp_min(torch.finfo(actual.dtype).tiny)))
    bound = 2 * epsilon * torch.pow(2., exponent) + 2e-6
    difference = (actual.double() - expected).abs()
    if not bool((difference <= bound).all()):
        raise ValueError('Actual original attention/LM result exceeds preregistered two-ULP bound')
    return dict(maximum_absolute_error=float(difference.max()),
                maximum_allowed_element_bound=float(bound.max()), two_dtype_ULP_plus_2e_minus6=True)


def validate_features(witness, visual):
    temporal, height, width = map(int, witness['grid'][0].tolist())
    features = visual['video_features']
    if temporal != 32 or len(features) % temporal:
        raise ValueError('Actual real visual features cannot form exact32 original temporal groups')
    expected = features.double().reshape(temporal, -1, features.shape[-1]).mean(dim=1)
    pooled = witness['pooled_FP32']
    if not torch.allclose(pooled.double(), expected, atol=1e-6, rtol=1e-5):
        raise ValueError('Actual8B visual pooling differs from independent CPU original-token slices')
    queries = witness['actual_query_embeddings']; question = witness['original_Question_embedding']
    if (queries.shape[:2] != (32, 2) or not torch.equal(queries[:, 0], pooled.to(queries.dtype))
            or not torch.equal(queries[:, 1], question.expand(32, -1))):
        raise ValueError('Actual query vectors contain extra IDs, scaling or another visual group')
    positions = witness['actual_query_positions']
    prefix_positions = visual['actual_prefix_position_ids']
    base = int(prefix_positions.max()) + 1
    expected_positions = torch.arange(base, base + 2).view(1, 1, 2).expand(3, 32, 2)
    if not torch.equal(positions.cpu(), expected_positions):
        raise ValueError('Actual independent queries differ in query positions or native RoPE continuation')
    return dict(maximum_pooling_error=float((pooled.double() - expected).abs().max()),
        actual_temporal_groups=32, actual_spatial_tokens_per_group=len(features)//32,
        actual_hidden_width=features.shape[-1], query_positions_identical=True,
        no_cell_ID_or_previous_answer_vectors=True)


def native_check(source, case, proof, output, raw, binary, code):
    chosen = [min([code['Yes'], code['No']], key=lambda token:
        (-float(pair[0 if token == code['Yes'] else 1]), token)) for pair in binary]
    selected = [token == code['Yes'] for token in chosen]
    if chosen != raw['selected_token_ids'] or selected != output['selected_cells']:
        raise ValueError('Actual original LM binary argmax/tie/native choices differ')
    mask = np.zeros(len(source.timeline.points), dtype=bool)
    for selected_cell, (start, stop) in zip(selected, read(check(proof))['source_native_cells']):
        if selected_cell:
            mask[start:stop] = True
    reconstructed = source.selection(case, output)
    if (not np.array_equal(mask, reconstructed) or output['native_frames'] != int(mask.sum())
            or output['native_mask_sha256'] != hashlib.sha256(mask.tobytes()).hexdigest()):
        raise ValueError('Independent actual32 choices/native support/empty parser differs')
    return dict(selected_native_frames=int(mask.sum()), legal_empty=not bool(mask.any()),
                all32_native_choices_and_original_PTS_checked=True)


def case_check(source, case, proof, result, code):
    manifest = read(check(result['witnesses'])); output = read(check(result['output']))
    raw = read(check(output['raw']))
    if output['CPU'] != proof or raw['actual_input'] != proof:
        raise ValueError('Actual local visual output belongs to another accepted input')
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
            or not torch.equal(binary, permanent['binary_logits'])
            or binary.tolist() != raw['binary_logits']):
        raise ValueError('Actual full original vocabulary and retained binary readout disagree')
    expected_projection = permanent['actual_final_hidden'].double() @ permanent['actual_original_LM_rows'].double().T
    checked_projection = quantized_check(full[:, [code['Yes'], code['No']]], expected_projection)
    native = native_check(source, case, proof, output, raw, binary, code)
    path = OUT / 'first_CPU' / (case.name + '.json')
    save(path, dict(state='FIRST_REAL8B_LOCAL_VISUAL_INPUT_ATTENTION_LM_NATIVE_CPU_PASS',
        actual_output=result['output'], actual_input=proof, permanent_witness=manifest['permanent'],
        source_visual_mapping=features, actual_attention=checked_attention, original_LM_projection=checked_projection,
        native=native, all_labels_unread=True, old_native_inputs_and_QA_adopted=True))
    return identity(path), [manifest[key] for key in
        ['temporary_visual', 'temporary_attention', 'temporary_full_vocab']]


def main():
    torch.set_num_threads(2)
    result = read(OUT / 'GPU_completion.json'); inputs = read(ROOT / 'visual_query_inputs119/completion.json')
    old = read(ROOT / 'parallel_inputs106/completion.json'); data = read(check(old['loss_bindings']))
    source = cases(data)[inputs['source']]; by_name = {case.name: case for case in source.cases}
    (OUT / 'first_CPU').mkdir(); proofs, temporary = [], []
    for name in inputs['first_engineering_cases']:
        proof, retire = case_check(source, by_name[name], inputs['inputs'][name],
                                   result['outputs'][name], inputs['actual_query_code'])
        proofs.append(proof); temporary.extend(retire)
    if len(proofs) != 2 or torch.cuda.is_initialized():
        raise ValueError('Complete two actual engineering/native CPU proofs or CPU role differ')
    cpu = OUT / 'CPU_completion.json'
    save(cpu, dict(state='FIRST2_ACTUAL8B_SHARED_LOCAL_VISUAL_ENGINEERING_CPU_PASS_NOT_QUALITY',
        first_real8B_input_attention_LM_native_proofs=proofs, actual_multimodal_prefills=2,
        actual32_branch_decoder_batches=2, actual_native_judgments=64,
        actual_complete_model_parameters=8853994586, new_training_updates=0,
        no_source_or_confirmation_labels_read=True, no_training_or_production_admission=True))
    retired = []
    for ref in temporary:
        path = check(ref)
        if path.is_symlink() or path.parent != TEMP.resolve(strict=True):
            raise ValueError('New temporary activation outside exact registered directory; do not retire')
        path.unlink(); retired.append(ref)
    save(OUT / 'first_activation_retirement.json', dict(first_CPU=identity(cpu),
        only_new_full_activations_retired=retired, permanent_native_model_projection_proofs_retained=True,
        no_old_success_or_model_raw_deleted=True))


if __name__ == '__main__':
    main()
