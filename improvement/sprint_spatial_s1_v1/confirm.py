"""Only the dev-frozen final adapter; first80 confirmation outputs, no tuning."""
import torch
from common import ROOT, RUN, checked, read, ref, write, runtime_paths
from model_io import generate


def main():
    runtime_paths()
    from peft import PeftModel
    from spatial_baseline import Qwen3VL
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    selected = read(ROOT / 'selected.json')
    checked(selected['adapter'])
    cfg = read(RUN / 'b_score_aligned_package_v4/config.json')
    wrapper = Qwen3VL(cfg['model_dir'], max_pixels=131072, device_map={'': 'cuda:0'}, attn_implementation='sdpa')
    model = PeftModel.from_pretrained(wrapper.model, str(checked(selected['adapter']).parent), is_trainable=False)
    model.eval().requires_grad_(False)
    items = [r for r in read(ROOT / 'conditioned_eval.json') if r['role'] == 'confirm']
    for index, item in enumerate(items):
        generate(model, wrapper.processor, item, selected['arm'], 'confirm')
        if (index + 1) % 20 == 0:
            print('FIRST_CONFIRM', index + 1, flush=True)
    write(ROOT / 'confirm_completion.json', dict(status='PASS80_FIRST_CONFIRM_OUTPUTS', arm=selected['arm'],
          new_generations=len(items), training_updates=0, frozen_selection=ref(ROOT / 'selected.json'),
          peak_allocated_bytes=torch.cuda.max_memory_allocated()))


if __name__ == '__main__':
    main()
