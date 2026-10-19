"""First supplementary input-grid/output-grid binding check.

Earlier pooling QA checked saved raw tokens against pooled features using
the output grid. This separately resolves the specific remaining risk of
an equal-product H/W permutation. No pooling/model/processor is repeated.
"""
import argparse
import os
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'roi_code_06'))
from roi_runtime import read,save,ref,bound,require,check_pixels,utc


def run(root,stage):
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='','Supplementary grid audit CPU only')
    import numpy as np
    import torch
    torch.set_num_threads(2)
    output=root/('roi_grid_binding_'+stage+'_11.json')
    require(not output.exists(),'Do not repeat this successful property audit')
    stages=['roi_pilot32_06','roi_remaining590_06'] if stage=='spatial622' else ['roi_confirm_GPU_10']
    expected=622 if stage=='spatial622' else 20;rows=[];seen=set()
    for name in stages:
        completion=root/name/'completion.json';done=read(completion)
        for reference in done['entries']:
            result=read(bound(reference));source=read(bound(result['source']))
            key='input' if stage=='spatial622' else 'new_vision'
            encoded=torch.load(bound(source[key]),map_location='cpu',weights_only=True)
            vision={k:encoded[k] for k in ('pixel_values','image_grid_thw')}
            actual_grid=check_pixels(vision)
            require(tuple(result['merged_grid'])==actual_grid,'Saved output grid differs from bound actual input grid')
            tokens=torch.load(bound(result['tokens']),map_location='cpu',weights_only=True)
            require(tokens.shape==(actual_grid[0]*actual_grid[1],4096) and torch.isfinite(tokens).all(),
                    'Actual raw output token shape/finiteness binding')
            feature=np.load(bound(result['features']),allow_pickle=False)
            if stage=='spatial622':boxes=source['candidate_boxes']
            else:boxes=read(bound(result['original_BASE']))['candidate_boxes']
            require(feature.dtype==np.float32 and feature.shape==(len(boxes),12296) and np.isfinite(feature).all(),
                    'Actual pooled feature dtype/shape binding')
            require(source['item_id']==result['item_id'] and source['item_id'] not in seen,'Unique new source identity')
            seen.add(source['item_id']);rows.append(dict(item_id=source['item_id'],input=source[key],
                 result=reference,actual_input_merged_grid=list(actual_grid),output_grid_equal=True))
            del encoded,vision,tokens,feature
    require(len(seen)==expected and not torch.cuda.is_initialized(),'Complete first grid-binding supplement')
    save(output,dict(status='PASS_FIRST_SOURCE_INPUT_GRID_TO_RAW_OUTPUT_BINDING',utc=utc(),stage=stage,
         sources=expected,entries=rows,audit_code=ref(Path(__file__)),new_model_calls=0,new_processor_calls=0,
         old_pooling_QA_repeated=False,quality_metrics_repeated=False,reason='New specific equal-product H/W mapping property; older frozen evidence unchanged'))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--stage',choices=['spatial622','confirm20'],required=True)
    a=p.parse_args();run(a.root,a.stage)
