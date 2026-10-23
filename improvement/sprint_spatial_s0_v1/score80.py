"""One frozen author-model forward per image; score all legal proposals together."""
import time
import sys
from pathlib import Path
_ROOT = Path('/home/inspur/aic_video_work/sprint_spatial_s0_20261021_v1')
sys.path[:0] = [str(_ROOT / path) for path in ['code_v7', 'code_run', 'code']]
import numpy as np
import torch
from control import ROOT, RUN, read, checked, write, append, reference, signature
from runtime import load_model


def main():
    sys.path.insert(0, str(RUN / 'temporal_sft8b_v1'))
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    accepted = read(ROOT / 'learned_weight_acceptance.json')
    checked(read(ROOT / 'input_acceptance.json')['inputs'])
    model = load_model(checked(accepted['weight'])).cuda().eval().requires_grad_(False)
    records = read(ROOT / 'inputs.json')
    raw_folder = ROOT / 'scores'
    raw_folder.mkdir()
    start = time.monotonic()
    for index, item in enumerate(records):
        inputs = torch.load(checked(item['input']), map_location='cpu', weights_only=True)
        if any(signature(value) != item['signatures'][key] for key, value in inputs.items()):
            raise ValueError('Learned scorer image or ROI tensor changed')
        with torch.inference_mode():
            output = model(inputs['image'].cuda(), inputs['rois'].cuda()).detach().cpu().numpy()
        path = raw_folder / (str(index) + '.npy')
        with path.open('xb') as stream:
            np.save(stream, output, allow_pickle=False)
        append(ROOT / 'raw_journal.jsonl', dict(item_id=item['item_id'], input=item['input'], output=reference(path),
            output_shape=list(output.shape), weight=accepted['weight']))
        scores = output.reshape(-1)
        if len(scores) != len(item['candidates']) or not np.isfinite(scores).all():
            raise ValueError('All candidate scores must be finite; failed output is retained')
        choice = max(range(len(scores)), key=lambda k: (float(scores[k]), item['candidates'][k][2]))
        append(ROOT / 'predictions.jsonl', dict(item_id=item['item_id'], chosen_index=choice,
            chosen_box=item['candidates'][choice], scores=scores.tolist(), raw=reference(path)))
        if index == 3:
            write(ROOT / 'throughput4.json', dict(first4_seconds=time.monotonic() - start, forwards=4,
                model_predictions_used_for_parameter_selection=False))
        if (index + 1) % 20 == 0:
            print('GAIC_FIRST_DEV', index + 1, flush=True)
    write(ROOT / 'model_completion.json', dict(status='PASS80_FIRST_FROZEN_GAIC_FORWARDS',
        actual_image_forwards=len(records), actual_candidate_scores=sum(len(r['candidates']) for r in records),
        new_training_updates=0, predictions=reference(ROOT / 'predictions.jsonl'),
        wall_seconds=time.monotonic() - start, peak_allocated_bytes=torch.cuda.max_memory_allocated(),
        actual_parameters=accepted['actual_parameters'], combined_parameters=accepted['combined_pipeline_parameters']))


if __name__ == '__main__':
    main()
