"""No new media: derive width-only training inputs; reference accepted eval tensors."""
import hashlib
import json
import traceback
from gws_common import ROOT,OLD,TRAINOLD,RUN,paths,read,save,sha,info,encode

def main():
    paths()
    import numpy as np
    import torch
    from PIL import Image
    from transformers import AutoProcessor
    from sft_contract import assistant_labels
    if read(TRAINOLD/'recovery_01/completion.json')['status']!='STOP_TRAINED_SCREEN_REJECTED_CONFIRM_NOT_RUN':
        raise ValueError('original joint route terminal required')
    prior=read(TRAINOLD/'source_lock.json')
    for p,h in prior['files'].items():
        if sha(p)!=h:raise ValueError('prior accepted inputs/code changed')
    cfg=read(RUN/'b_score_aligned_package_v4/config.json');processor=AutoProcessor.from_pretrained(
         cfg['model_dir'],local_files_only=True,min_pixels=131072,max_pixels=131072)
    (ROOT/'tensors').mkdir();(ROOT/'proofs').mkdir()
    train=[]
    for row in read(TRAINOLD/'train_inputs.json'):
        array=np.load(row['rgb'],allow_pickle=False)
        if hashlib.sha256(array.tobytes()).hexdigest()!=row['RGB_sha256']:raise ValueError('cached training RGB changed')
        image=Image.fromarray(array);target={'width':row['target']['width']};answer=json.dumps(target,separators=(',',':'))
        full,text,suffix=encode(processor,image,answer);prompt,prefix,_=encode(processor,image)
        if not torch.equal(full['pixel_values'],prompt['pixel_values']) or not torch.equal(full['image_grid_thw'],prompt['image_grid_thw']):
            raise ValueError('assistant text changed real image tensors')
        mask=assistant_labels(full['input_ids'][0].tolist(),full['attention_mask'][0].tolist(),
                              prompt['input_ids'][0].tolist(),prompt['attention_mask'][0].tolist())
        if processor.tokenizer.decode(mask['assistant_token_ids'],skip_special_tokens=False,clean_up_tokenization_spaces=False)!=suffix:
            raise ValueError('width-only assistant target boundary')
        full['labels']=torch.tensor([mask['tail_labels']],dtype=torch.long)
        key=row['item_id'].rsplit(':',1)[-1];tensor=ROOT/'tensors'/f'{key}.pt';torch.save(full,tensor)
        proof=ROOT/'proofs'/f'{key}.json'
        save(proof,{'path':str(tensor),'file_sha256':sha(tensor),'saved_tensors':info(full),'assistant_mask':mask,
             'answer':answer,'template_text':text,'source_RGB':row['rgb'],'original_source_sha256':row['source_sha256']})
        train.append({**row,'target':target,'tensor':str(tensor),'proof':str(proof),'original_joint_tensor_repeated':False})
    save(ROOT/'train_inputs.json',train)
    evaluation=[]
    for row in read(OLD/'inputs.json'):
        prior=read(OLD/row['proof'])['stages']['width'];tensor=OLD/prior['path']
        if sha(tensor)!=prior['file_sha256']:raise ValueError('prior width input bytes changed')
        values=torch.load(tensor,map_location='cpu',weights_only=True)
        if info(values)!=prior['tensors']:raise ValueError('prior width tensor identities changed')
        proof=ROOT/'proofs'/f'{row["key"]}.json'
        save(proof,{**prior,'path':str(tensor),'saved_tensors':prior['tensors'],'tensors':prior['tensors'],
             'template_text':prior['template_text'],'input_reencoded':False})
        evaluation.append({**row,'tensor':str(tensor),'new_proof':str(proof),'reused_RGB':str(OLD/'rgb'/f'{row["key"]}.npy')})
    save(ROOT/'eval_inputs.json',evaluation)
    if len(train)!=200 or len(evaluation)!=40 or torch.cuda.is_initialized():raise ValueError('real CPU input gate')
    save(ROOT/'cpu_acceptance.json',{'status':'PASS_200_HUMAN_TRAIN_40_EVAL_REAL_CPU_INPUTS','train':200,'eval':40,
         'JPEG_decodes':0,'new_media':0,'eval_processor_reencodes':0,'CUDA_initialized':False,
         'balanced_bin_sizes':[sum(r['target']['width']<=750 for r in train),sum(750<r['target']['width']<=950 for r in train),sum(r['target']['width']>950 for r in train)]})
    files={str(p):sha(p) for p in ROOT.rglob('*') if p.is_file() and p.suffix!='.log' and p.name not in
           ('chain_launch.json','chain_launch_claim.json','deployment.json','chain_started.json')}
    for p in [TRAINOLD/'source_lock.json',TRAINOLD/'train_inputs.json',TRAINOLD/'recovery_01/completion.json',
              OLD/'reference/labels.json',OLD/'inputs.json',OLD/'recovery_01/screen/predictions.jsonl']:
        files[str(p)]=sha(p)
    for row in train:
        for key in ('rgb','source'):files[row[key]]=sha(row[key])
    for row in evaluation:
        for key in ('tensor','reused_RGB'):files[row[key]]=sha(row[key])
        proof=OLD/row['proof'];files[str(proof)]=sha(proof)
        baseline=OLD/read(proof)['stages']['baseline']['path'];files[str(baseline)]=sha(baseline)
    for n in ['b_score_aligned_package_v4/config.json','b_score_aligned_package_v4/engine.py','b_score_aligned_package_v4/common.py',
              'b_score_aligned_package_v4/spatial_baseline.py','temporal_sft8b_v1/sft_contract.py','temporal_sft8b_v1/train_sft.py']:
        files[str(RUN/n)]=sha(RUN/n)
    save(ROOT/'source_lock.json',{'files':files,'original_successes_repeated':False})

if __name__=='__main__':
    try:main()
    except Exception as e:
        save(ROOT/'prepare_failure.json',{'error':repr(e),'traceback':traceback.format_exc(),'preserve_success_no_retry':True});raise
