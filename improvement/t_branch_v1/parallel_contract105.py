"""First actual tokenizer, causal position and gradient CPU checks; no8B calls."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''

from pathlib import Path
import traceback

import numpy as np
import torch
from transformers import AutoTokenizer

from frozen_branch46 import RUN
from native_codec98 import preference_loss
from parallel_query105 import assemble, select, vocabulary
from t_io import ROOT, identity, read, save

OUT = ROOT / 'parallel_contract105'


def causal_check():
    torch.manual_seed(7405)
    layer = torch.nn.TransformerEncoderLayer(8, 2, dim_feedforward=16, dropout=0., batch_first=True)
    model = torch.nn.TransformerEncoder(layer, 2, enable_nested_tensor=False).eval()
    embedding = torch.nn.Embedding(40, 8)
    head = torch.nn.Linear(8, 2)
    code = dict(anchors=list(range(32)), Question=32, Yes=33, No=34)
    data = assemble(torch.tensor([[35, 36, 37]]), code)
    ids = data['input_ids']
    with torch.no_grad():
        full = head(model(embedding(ids), mask=torch.nn.Transformer.generate_square_subsequent_mask(ids.shape[1])))
        for position in data['logits_to_keep']:
            clipped = ids[:, :position + 1]
            separate = head(model(embedding(clipped),
                mask=torch.nn.Transformer.generate_square_subsequent_mask(clipped.shape[1])))[:, -1]
            if not torch.allclose(full[:, position], separate, atol=1e-6, rtol=1e-5):
                raise ValueError('Parallel query position differs from its actual causal prefix')
    return dict(actual_torch_causal_positions=32, synthetic_full_vs_prefix_equal=True,
                not_an8B_numerical_equivalence_claim=True)


def gradient_check():
    torch.manual_seed(7405)
    logits = torch.randn(1, 69, 40, requires_grad=True)
    code = dict(anchors=list(range(32)), Question=32, Yes=33, No=34)
    data = assemble(torch.tensor([[35, 36, 37, 38, 39]]), code)
    positions = data['logits_to_keep']
    z = logits[0, positions][:, [33, 34]]
    a, b = torch.ones(32) / 64, torch.ones(32) / 64
    a[7] = 0; b[7] = 0
    loss, _ = preference_loss(z, a, b, .5)
    loss.backward()
    expected = torch.zeros_like(logits, dtype=torch.bool)
    for j, position in enumerate(positions):
        if j != 7:
            expected[0, position, [33, 34]] = True
    if ((logits.grad != 0) != expected).any():
        raise ValueError('Query loss gradients escaped true choice positions or UNKNOWN mask')
    return dict(query_position_gradients_only=True, task_UNKNOWN_zero_gradient=True,
                no_previous_answer_teacher_forcing=True)


def main():
    OUT.mkdir()
    torch.set_num_threads(2)
    tokenizer = AutoTokenizer.from_pretrained(read(RUN / 'b_score_aligned_package_v4/config.json')['model_dir'],
                                             local_files_only=True)
    prior = read(ROOT / 'native_action_contract98/completion.json')
    code = vocabulary(tokenizer, prior['actual_token_codec'])
    data = assemble(torch.tensor([[1, 2, 3]]), code)
    if (data['input_ids'][0, 3:].tolist() != [v for a in code['anchors'] for v in [a, code['Question']]]
            or data['logits_to_keep'] != list(range(4, 67, 2))):
        raise ValueError('Actual query-only suffix or causal prediction indices differ')
    if select(np.tile([-1., 1.], (32, 1)), code).any():
        raise ValueError('Successful allNo query choices must remain a legal empty')
    for bad in [np.zeros((31, 2)), np.full((32, 2), np.nan)]:
        try:
            select(bad, code)
        except ValueError:
            continue
        raise ValueError('An actual query failure was silently converted to empty')
    expected_tie = code['Yes'] < code['No']
    if not np.all(select(np.zeros((32, 2)), code) == expected_tie):
        raise ValueError('Actual finite argmax tie convention differs')
    causal, gradient = causal_check(), gradient_check()
    if torch.cuda.is_initialized():
        raise ValueError('Query CPU contract initialized CUDA')
    save(OUT / 'completion.json', dict(state='FIRST_PARALLEL_NATIVE_QUERY_POSITION_CAUSAL_GRADIENT_CPU_PASS',
        actual_query_code=code, causal=causal, gradient=gradient, successful_empty_and_failure_separate=True,
        prior_clone_and_source_loss_CPU_adopted=identity(ROOT / 'native_action_contract98/completion.json'),
        prior_exact_native_partition_adopted=identity(ROOT / 'native_action_feasibility97/completion.json'),
        code={n: identity(Path(__file__).with_name(n)) for n in ['parallel_contract105.py', 'parallel_query105.py']},
        actual8B_forwards=0, actual_optimizer_updates=0, no_quality_or_production_admission=True))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(), preserve_all_previous_successes=True))
        raise
