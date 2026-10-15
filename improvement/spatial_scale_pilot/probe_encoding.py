"""Independent real-processor equality with old image path, without loading weights."""
import hashlib
import json
import sys
from pathlib import Path
from encoding import encode

HERE = Path(__file__).resolve().parent
RUN = Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
sys.path[:0] = [str(RUN/'b_score_aligned_package_v4'), str(RUN/'baseline_a_pts_v1'),
               str(RUN/'baseline_a_pts_v1/vendor'), str(RUN/'temporal_sft8b_v1')]


def main():
    import torch
    from PIL import Image
    from transformers import AutoProcessor
    from spatial_baseline import Qwen3VL
    config = json.loads((RUN/'b_score_aligned_package_v4/config.json').read_text())
    processor = AutoProcessor.from_pretrained(config['model_dir'],local_files_only=True,
                                             min_pixels=131072,max_pixels=131072)
    checks = []
    for item in json.loads((HERE/'inputs.json').read_text()):
        image = Image.open(HERE/item['path']).convert('RGB')
        received = {}
        class Capture:
            def generate(self, **kwargs):
                received.update(kwargs)
                ids = kwargs['input_ids']
                return torch.cat([ids, torch.zeros((1,1),dtype=ids.dtype)],dim=1)
        old = object.__new__(Qwen3VL)
        old.processor,old.torch,old.model,old.device = processor,torch,Capture(),torch.device('cpu')
        old.max_pixels=131072
        old.predict_focus(image,item['ratio'],128)
        # Capture the unchanged original prompt rather than duplicating its string.
        messages = []
        class PromptCapture:
            def _generate(self,m,limit):
                messages.extend(m)
                return ''
        PromptCapture.max_pixels=131072
        Qwen3VL.predict_focus(PromptCapture(),image,item['ratio'],128)
        new,_,_ = encode(processor,messages)
        old_tensors={k:v for k,v in received.items() if isinstance(v,torch.Tensor)}
        if set(old_tensors)!=set(new):raise ValueError('processor tensor keys differ')
        equality={k:torch.equal(old_tensors[k],new[k]) for k in new}
        if not all(equality.values()):raise ValueError('old/new baseline actual tensors differ')
        checks.append(dict(item_id=item['item_id'],all_tensors_equal=equality,
            input_tokens=int(new.input_ids.shape[1]),
            tensor_shapes={k:list(v.shape) for k,v in new.items()}))
    if torch.cuda.is_initialized():raise ValueError('CPU acceptance initialized CUDA')
    receipt=dict(status='PASS_ALL_FOUR_ORIGINAL_BASELINE_PROCESSOR_TENSORS_EXACT',
                 checks=checks,model_calls=0,weights_loaded=False,CUDA_initialized=False,
                 encoding_source_sha256=hashlib.sha256((HERE/'encoding.py').read_bytes()).hexdigest())
    with (HERE/'encoding_acceptance.json').open('x') as f:json.dump(receipt,f,indent=2)
    print(json.dumps(receipt))


if __name__=='__main__':main()
