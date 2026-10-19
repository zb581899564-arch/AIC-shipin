"""First independent saved-state QA for objective20; no model/input replay."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import torch
from safetensors.torch import load_file

ROOT = Path('/home/inspur/aic_video_work/bottleneck_24h_20261019_v1/summary_objective_v20')
WORK = Path('/home/inspur/aic_video_work')
RUN = WORK/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(8 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def bound(value):
    path = Path(value['path']).resolve(strict=True)
    assert path.is_relative_to(WORK) and path.is_file() and sha(path) == value['sha256']
    return path


def ref(path):
    path = Path(path)
    return dict(path=str(path), bytes=path.stat().st_size, sha256=sha(path))


def main():
    assert os.uname().nodename == 'inspur-NP5570M5' and not torch.cuda.is_initialized()
    torch.set_num_threads(2)
    output = ROOT/'first_final_training_acceptance_21.json'
    assert not output.exists(), 'Successful first independent final QA cannot repeat'
    model = ROOT/'summary_model_20'; complete = read(model/'full_completion.json')
    assert complete['status'] == 'PASS_SUMMARY_FINAL559_SINGLE_EPOCH'
    assert complete['completed_updates'] == 559 and complete['successful_micro'] == 2236
    job = 'summary_time_fixed_token_normalizer25_full559_20261019_v20'
    resource_path = RUN/'controller'/(job+'.resource.json'); resource = read(resource_path)
    ledger = [json.loads(line) for line in (WORK/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines()
              if line.strip() and json.loads(line).get('name') == job]
    assert resource['status'] == 'completed' and resource['exit_code'] == 0 and ledger == [resource]
    state = torch.load(bound(complete['progress_ref']), map_location='cpu', weights_only=True)
    assert state['completed_updates'] == 559 and state['successful_micro'] == 2236
    assert state['schedule_sha256'] == complete['schedule_sha256'] and state['recipe'] == complete['recipe']
    weights = load_file(str(bound(complete['adapter_weights_ref'])), device='cpu')
    assert set(weights) == set(state['adapter_state_dict']) and len(weights) == 288
    assert all(torch.equal(weights[key], state['adapter_state_dict'][key])
               and torch.isfinite(weights[key]).all() for key in weights)
    original = load_file(str(bound(complete['original_TIME_weights_ref'])), device='cpu')
    assert set(weights) == set(original)
    changed = sum(not torch.equal(weights[key], original[key].to(weights[key].dtype)) for key in weights)
    assert changed > 0
    optim = state['optimizer_state_dict']['state']
    assert len(optim) == 288 and all(float(value['step']) == 559
        and torch.isfinite(value['exp_avg']).all() and torch.isfinite(value['exp_avg_sq']).all()
        for value in optim.values())
    targets = [json.loads(line) for line in bound(state['training_targets_ref']).read_text().splitlines() if line.strip()]
    assert len(targets) == 2236
    order = torch.randperm(2236, generator=torch.Generator().manual_seed(20261019)).tolist()
    updates = [json.loads(line) for line in (model/'updates.jsonl').read_text().splitlines() if line.strip()]
    assert [row['step'] for row in updates] == list(range(1, 560))
    assert all(row['successful_micro'] == row['step']*4 and row['finite_gradient_matrices'] == 288
               and 0 < row['nonzero_gradient_matrices'] <= 288 for row in updates)
    assert updates[-1]['progress'] == complete['progress_ref']
    micro = [json.loads(line) for line in (model/'micro.jsonl').read_text().splitlines() if line.strip()]
    losses = [row for row in micro if row['event'] == 'RAW_LOSS']
    backwards = [row for row in micro if row['event'] == 'BACKWARD_COMPLETE']
    assert [row['micro'] for row in losses] == [row['micro'] for row in backwards] == list(range(2236))
    assert [row['successful_micro'] for row in backwards] == list(range(1, 2237))
    normalizer = math.fsum(row['weight']*len(row['suffix_ids']) for row in targets) / math.fsum(row['weight'] for row in targets)
    assert normalizer == complete['recipe']['fixed_loss_normalizer'] == 22.007595566797036
    for index, actual in enumerate(losses):
        target = targets[order[index]]
        assert actual['uid'] == target['uid'] and actual['reviewer'] == target['reviewer']
        assert actual['weight'] == target['weight'] and actual['suffix_tokens'] == len(target['suffix_ids'])
        assert actual['loss_reduction'] == 'TOKEN_SUM_OVER_FIXED_SOURCE_WEIGHTED_MEAN_LENGTH'
        assert actual['fixed_normalizer'] == normalizer and math.isfinite(actual['loss'])
    assert complete['base_fingerprint']['sha256'] == '74bcce81cfcb0893cf4b4c25ae36ec908d6ea669583aedd0f3940063080b8b59'
    value = dict(status='PASS_FIRST_INDEPENDENT_OBJECTIVE20_FINAL559_STATE_AND_ACTUAL2236_ORDER',
        utc=datetime.now(timezone.utc).isoformat(), completion_ref=ref(model/'full_completion.json'),
        resource_ref=ref(resource_path), unique_ledger_equal=True, adapter_weights_ref=complete['adapter_weights_ref'],
        changed_adapter_matrices=changed, optimizer288_step559=True, saved288_equal_checkpoint=True,
        successful_updates=559, actual_backward_targets=2236, correct_fixed_normalizer=True,
        successful_micro_repeated=False, base_fingerprint=complete['base_fingerprint'],
        quality_not_asserted=True, new_model_or_input_QA_replay=0, dev_metrics_read=False)
    with output.open('x') as stream:
        json.dump(value, stream, indent=2); stream.flush(); os.fsync(stream.fileno())
    print(json.dumps(value))


if __name__ == '__main__':
    main()
