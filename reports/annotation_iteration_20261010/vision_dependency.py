"""Training-only cross-source true/swap visual evidence, assistant NLL paired."""
import argparse,hashlib,json,sys
from pathlib import Path
def main():
    p=argparse.ArgumentParser()
    for k in ('root','model','adapter','output'):p.add_argument('--'+k,required=True)
    a=p.parse_args();root=Path(a.root);sys.path.insert(0,str(root/'training_v2'))
    from sft_contract import ImageSFTCollator,load_rows
    import torch
    from transformers import AutoProcessor,Qwen3VLForConditionalGeneration
    from peft import PeftModel
    rows=load_rows(root/'training_v2/data/temporal_fixed_train.jsonl',root)
    sources={}
    for r in sorted(rows,key=lambda r:hashlib.sha256(r['id'].encode()).hexdigest()):
        if len(r['images'])==16 and r['source_group'] not in sources:sources[r['source_group']]=r
    chosen=list(sources.values())[:12];assert len(chosen)==12
    processor=AutoProcessor.from_pretrained(a.model,local_files_only=True,min_pixels=4096,max_pixels=65536)
    model=PeftModel.from_pretrained(Qwen3VLForConditionalGeneration.from_pretrained(a.model,local_files_only=True,
                    torch_dtype=torch.bfloat16,attn_implementation='sdpa'),a.adapter,local_files_only=True).to('cuda').eval()
    collator=ImageSFTCollator(processor,root);report=[]
    for i,row in enumerate(chosen):
        other=chosen[(i+6)%12];assert other['source_group']!=row['source_group']
        values=[]
        for mode in ('normal','cross_source_swap'):
            input_row=dict(row)
            if mode!='normal':input_row['images']=other['images']
            encoded=collator.encode(input_row)
            sig=hashlib.sha256(encoded['pixel_values'].contiguous().numpy().tobytes()).hexdigest()
            with torch.inference_mode():loss=float(model(**{k:v.to('cuda') for k,v in encoded.items()}).loss)
            assert torch.isfinite(torch.tensor(loss))
            values.append({'mode':mode,'assistant_nll':loss,'pixel_tensor_sha256':sig})
        assert values[0]['pixel_tensor_sha256']!=values[1]['pixel_tensor_sha256']
        report.append({'id':row['id'],'swap_source':other['source_group'],'conditions':values,
                       'swap_minus_normal':values[1]['assistant_nll']-values[0]['assistant_nll']})
        print(json.dumps(report[-1]),flush=True)
    delta=sum(r['swap_minus_normal'] for r in report)/12;positive=sum(r['swap_minus_normal']>0 for r in report)
    with Path(a.output).open('x') as f:json.dump({'rows':report,'mean_swap_minus_normal':delta,'normal_better_rows':positive,
            'visual_dependency_gate':delta>0 and positive>=7,'source':'TRAIN_ONLY_FIXED_HASH_12_FULL_ROWS','not_highlight_quality':True},f,indent=2)
if __name__=='__main__':main()
