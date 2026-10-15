"""One exact full-scope generation, same images/protocol for all model arms."""
import argparse,hashlib,json,sys,time
from pathlib import Path
from PIL import Image
from score_grammar import Constraint,candidates

def main():
    p=argparse.ArgumentParser();p.add_argument('--root',required=True);p.add_argument('--model',required=True)
    p.add_argument('--data',required=True);p.add_argument('--adapter');p.add_argument('--output',required=True)
    p.add_argument('--swap',action='store_true');a=p.parse_args();root=Path(a.root)
    sys.path.insert(0,str(root/'training_v2'))
    from sft_contract import load_rows,typed_messages,decode_output
    import torch
    from transformers import AutoProcessor,Qwen3VLForConditionalGeneration
    assert torch.cuda.is_available();rows=load_rows(a.data,root);out=Path(a.output);assert not out.exists()
    processor=AutoProcessor.from_pretrained(a.model,local_files_only=True,min_pixels=4096,max_pixels=65536)
    model=Qwen3VLForConditionalGeneration.from_pretrained(a.model,local_files_only=True,torch_dtype=torch.bfloat16,attn_implementation='sdpa')
    if a.adapter:
        from peft import PeftModel
        model=PeftModel.from_pretrained(model,a.adapter,local_files_only=True)
    model=model.to('cuda').eval();ids=candidates(processor.tokenizer);torch.cuda.reset_peak_memory_stats()
    with out.open('x',encoding='utf-8') as f:
        for index,row in enumerate(rows):
            images=[]
            for path in row['images']:
                with Image.open(root/path) as im:images.append(im.convert('RGB'))
            if a.swap:images=images[1:]+images[:1]
            messages=typed_messages(row,images)[:1]
            text=processor.apply_chat_template(messages,tokenize=False,add_generation_prompt=True)
            encoded=processor(text=[text],images=images,return_tensors='pt').to('cuda')
            n=encoded['input_ids'].shape[1];assert n<=16384 and encoded['image_grid_thw'].shape[0]==len(images)
            constraint=Constraint(processor.tokenizer,n,len(images),ids)
            with torch.inference_mode():output=model.generate(**encoded,do_sample=False,max_new_tokens=256,prefix_allowed_tokens_fn=constraint)
            token_ids=output[0,n:].tolist();answer,obj=constraint.finish(token_ids)
            decode_output(answer,row['task'],image_count=len(images))
            record={'id':row['id'],'source_group':row['source_group'],'answer':answer,'output_token_ids':token_ids,
                    'input_tokens':n,'valid':True,'gold_in_input':False,'swapped_images':a.swap,
                    'prompt_sha256':hashlib.sha256(text.encode()).hexdigest()}
            f.write(json.dumps(record)+'\n');f.flush()
            print(json.dumps({'stage':'ACTUAL_CONSTRAINED_GENERATION','rows_done':index+1,'rows_total':len(rows),'peak_bytes':torch.cuda.max_memory_allocated()}),flush=True)
if __name__=='__main__':main()
