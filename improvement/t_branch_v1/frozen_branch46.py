"""Pinned original VERIFY/semantic modules; never reinitialize original runtime."""
from pathlib import Path
import sys

from t_io import ROOT, WORK, check, identity, read, save

# Import the old metadata context before canonical engine-common binding once.
sys.path.insert(0, str(WORK / 'general_highlight_supervision_20261021_v1/code'))
from baseline_bridge57_common import semantic_modules, verify_modules

RUN = WORK / 'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
SEM = WORK / 'semantic_context_production_20261016_v1'


def final_actor(model, training_terminal):
    import torch
    from peft import get_peft_model_state_dict, set_peft_model_state_dict
    from safetensors.torch import load_file
    final = read(training_terminal)['final_adapter']
    weights = load_file(str(check(final['weights'])), device='cpu')
    model.load_adapter(final['adapter_directory'], adapter_name='actor', is_trainable=False)
    set_peft_model_state_dict(model, weights, adapter_name='actor')
    actual = get_peft_model_state_dict(model, adapter_name='actor')
    if set(actual) != set(weights) or any(not torch.equal(actual[key].detach().cpu(), weights[key]) for key in weights):
        raise ValueError('Actual final actor inference load rounded away trained values')
    for p in model.parameters():
        p.requires_grad_(False)
    return final


def semantic_prediction(baseline, accepted, output_refs):
    import numpy as np
    import torch
    _, transform, head_module = semantic_modules()
    language, yesno = [], []
    if len(accepted['chunks']) != len(output_refs):
        raise ValueError('Full frozen semantic input/output count differs')
    for case, ref in zip(accepted['chunks'], output_refs):
        part = torch.load(check(ref), map_location='cpu', weights_only=True)
        if part['input'] != case['input'] or part['samples'] != case['samples']:
            raise ValueError('First semantic output identity differs')
        if part['language'].shape != (case['queries'], 4096) or part['yes_no'].shape != (case['queries'], 2):
            raise ValueError('Frozen semantic query representation shape differs')
        language.append(part['language'].numpy()); yesno.append(part['yes_no'].numpy())
    with np.load(check(accepted['native']), allow_pickle=False) as archive:
        groups = archive['groups'].copy()
    reg = read(SEM / 'production_registration.json')
    x = transform.transform(np.concatenate(language), np.concatenate(yesno),
                            dict(baseline=baseline, groups=groups), reg['selected_view'])
    head = head_module.ResidualHead(reg['feature_dimension'], 8)
    head.load_state_dict(torch.load(check(reg['selected_head']), map_location='cpu', weights_only=True), strict=True)
    if head.parameter_count != 98329:
        raise ValueError('Frozen semantic actual parameter count differs')
    head.eval()
    with torch.inference_mode():
        residual = head(torch.from_numpy(x)).numpy()
    if not np.isfinite(residual).all():
        raise ValueError('Frozen semantic output nonfinite')
    return baseline | (residual[groups] > 1.), residual
