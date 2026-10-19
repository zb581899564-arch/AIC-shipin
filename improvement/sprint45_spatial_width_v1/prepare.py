"""First new-purpose602 JPEG->RGB/processor and first independent CPU input QA.

No screen/confirm inputs, labels, scores, download or old RGB/tensor dependency.
"""
from width_common import *


def original_order(ctx):
    items=ctx.labeled_manifest();journal=Path(ctx.proto['original_accepted_journal'])
    require(journal.is_absolute() and journal.is_file() and sha(journal)==ctx.proto['original_accepted_journal_sha'],'Original accepted journal identity')
    old=rows(journal);require(len(old)==602,'Actual interrupted602 accepted denominator; never pad to1000')
    old_proofs=[]
    for item,source in zip(items,old):
        required(source,('item_id','source','source_sha256','proof','target','reference_original_xyxy'),'Original accepted row')
        require(item['id']==source['item_id'] and Path(item['source']).resolve()==Path(source['source']).resolve() and item['source_sha256']==source['source_sha256'] and item['target_width']==source['target']['width'] and item['reference_original_xyxy']==source['reference_original_xyxy'],'Exact original accepted602 order/source/human target')
        require(Path(item['source']).is_file() and sha(item['source'])==item['source_sha256'],'Existing original JPEG changed/missing; no download or replacement')
        proof=Path(source['proof']);require(proof.is_absolute() and proof.is_file(),'Retained original proof missing; old RGB/tensors are not required')
        old_proofs.append(dict(path=str(proof),sha256=sha(proof)))
    return items,old_proofs


def prepare(ctx):
    cpu_only();ctx.claim('prepare');items,old_proofs=original_order(ctx)
    import numpy as np
    from PIL import Image
    from transformers import AutoProcessor
    processor=AutoProcessor.from_pretrained(ctx.model_config()['model_dir'],local_files_only=True,min_pixels=65536,max_pixels=65536)
    for name in ('inputs','rgb','labels'):(ctx.root/name).mkdir()
    save(ctx.root/'labels/train602.json',dict(status='ADOPT_ORIGINAL602_HUMAN_WIDTH_TARGETS',
         rows=[dict(sample_id='I%04d'%i,**item,old_proof=old_proofs[i]) for i,item in enumerate(items)],
         original_accepted_journal_sha=ctx.proto['original_accepted_journal_sha'],**ctx.binding))
    accepted=[]
    for index,item in enumerate(items):
        sample='I%04d'%index;directory=ctx.root/'inputs'/sample;directory.mkdir()
        with Image.open(item['source']) as image:
            require(image.format=='JPEG' and image.getexif().get(274,1)==1,'Original JPEG/EXIF1 only; no EXIF transform')
            W,H=image.size;array=np.asarray(image.convert('RGB')).copy()
        require(array.dtype==np.uint8 and array.shape==(H,W,3) and min(W,H)>0,'Original full-resolution RGB')
        rgb=ctx.root/'rgb'/(sample+'.npy')
        with rgb.open('xb') as handle:np.save(handle,array,allow_pickle=False)
        values,text=encode(processor,Image.fromarray(array));tensor=directory/'input.pt';tensor_save(tensor,values)
        proof=dict(status='PASS_FIRST_NEW_PURPOSE_WIDTH_IMAGE_INPUT',sample_id=sample,id=item['id'],source=item['source'],
                   source_sha256=item['source_sha256'],width=W,height=H,RGB_path=str(rgb),RGB_file_sha256=sha(rgb),
                   RGB_pixel_sha256=hashlib.sha256(array.tobytes()).hexdigest(),tensor_path=str(tensor),tensor_sha256=sha(tensor),
                   tensors=tensor_info(values),template_text=text,input_tokens=int(values['input_ids'].shape[1]),
                   labels_in_input=False,old_tensor_reused=False,first_new_purpose_JPEG_decode=True)
        save(directory/'proof.json',proof);accepted.append(proof)
    save(ctx.root/'cpu_acceptance.json',dict(status='PASS_602_NEW_PURPOSE_JPEG_RGB_PREFIX_INPUTS',sources=accepted,
         train=602,screen=0,confirm=0,new_model_calls=0,new_JPEG_decodes=602,new_processor_inputs=602,
         train_label_file_sha256=sha(ctx.root/'labels/train602.json'),**ctx.binding))


def qa(ctx):
    cpu_only();ctx.claim('input_qa')
    import numpy as np
    import torch
    from PIL import Image
    from transformers import AutoProcessor
    accepted,sources=checked_cpu_sources(ctx)
    processor=AutoProcessor.from_pretrained(ctx.model_config()['model_dir'],local_files_only=True,min_pixels=65536,max_pixels=65536)
    for proof in sources:
        require(sha(proof['RGB_path'])==proof['RGB_file_sha256'] and sha(proof['tensor_path'])==proof['tensor_sha256'],'Saved new RGB/tensor bytes')
        array=np.load(proof['RGB_path'],allow_pickle=False)
        require(array.dtype==np.uint8 and array.shape==(proof['height'],proof['width'],3) and hashlib.sha256(array.tobytes()).hexdigest()==proof['RGB_pixel_sha256'],'Saved full-resolution RGB first independent QA')
        actual,text=encode(processor,Image.fromarray(array));saved=torch.load(proof['tensor_path'],map_location='cpu',weights_only=True)
        require(text==proof['template_text'] and tensor_info(actual)==proof['tensors'] and set(saved)==set(actual) and all(torch.equal(saved[k],actual[k]) for k in actual),'First independent processor/ids/grid bit equality')
        require(QUESTION in text and int(actual['attention_mask'][0,-1])==1,'Fixed no-GT prompt and final valid prefix position')
    save(ctx.root/'input_QA.json',dict(status='PASS_602_FIRST_INDEPENDENT_SAVED_RGB_PROCESSOR_BIT_QA',sources=602,
         new_JPEG_decodes=0,first_independent_processor_replays=602,old_successful_inputs_replayed=0,
         cpu_acceptance_sha256=sha(ctx.root/'cpu_acceptance.json'),**ctx.binding))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',required=True);parser.add_argument('--stage',choices=['prepare','qa'],required=True);args=parser.parse_args();ctx=Context(args.root)
    try:{'prepare':prepare,'qa':qa}[args.stage](ctx)
    except BaseException as error:fail(ctx,args.stage,error);raise
