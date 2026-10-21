"""Exactly one frozen text batch and first image batches; no target access."""
import sys
import numpy as np
import torch
from common import ROOT,checked,ref,read,write


def encode_source(model,source):
    sid=source['sid'];out=ROOT/'outputs'/sid;out.mkdir()
    rgb=np.load(checked(source['rgb']),mmap_mode='r',allow_pickle=False)
    frames=rgb.reshape(-1,224,224,3)
    mean=torch.tensor([.48145466,.4578275,.40821073],device='cuda')[None,:,None,None]
    std=torch.tensor([.26862954,.26130258,.27577711],device='cuda')[None,:,None,None]
    files=[]
    for begin in range(0,len(frames),32):
        pixels=torch.from_numpy(frames[begin:begin+32].copy()).permute(0,3,1,2).cuda().float()/255
        with torch.inference_mode():
            raw=model.encode_image((pixels-mean)/std).cpu().numpy()
        path=out/f'image_{begin:05d}.npy'
        with path.open('xb') as f:np.save(f,raw,allow_pickle=False)
        assert raw.shape==(len(pixels),512) and np.isfinite(raw).all()
        files.append(ref(path))
    record=dict(sid=sid,image_embeddings=len(frames),actual_forward_batches=len(files),files=files,
                source_cells=source['native_cells'],labels_opened=False)
    write(out/'acceptance.json',record)
    with (ROOT/'inference_journal.jsonl').open('a') as f:
        import json
        f.write(json.dumps(dict(sid=sid,image_embeddings=len(frames),forward_batches=len(files)))+'\n')
    return record


def main():
    sys.path.insert(0,str(ROOT/'vendor'))
    import clip
    assert torch.cuda.is_available()
    source=read(ROOT/'input_acceptance.json')
    model,_=clip.load(str(ROOT/'model/ViT-B-32.pt'),device='cuda',jit=False)
    model.eval().requires_grad_(False)
    assert sum(p.numel() for p in model.parameters())==read(ROOT/'asset_acceptance.json')['actual_clip_parameters']
    (ROOT/'outputs').mkdir()
    tokens=torch.from_numpy(np.load(checked(source['tokens']),allow_pickle=False)).cuda()
    with torch.inference_mode():
        text=model.encode_text(tokens).cpu().numpy()
    with (ROOT/'outputs/text_raw.npy').open('xb') as f:np.save(f,text,allow_pickle=False)
    assert text.shape==(26,512) and np.isfinite(text).all()
    rows=[encode_source(model,s) for s in source['sources']]
    write(ROOT/'inference_completion.json',dict(status='FROZEN_CLIP_PRIMARY_OUTPUTS_COMPLETE',
              text=ref(ROOT/'outputs/text_raw.npy'),sources=rows,text_forward_batches=1,
              image_forward_batches=sum(r['actual_forward_batches'] for r in rows),
              image_embeddings=sum(r['image_embeddings'] for r in rows),
              peak_allocated_bytes=torch.cuda.max_memory_allocated(),
              target_labels_opened=False,new_updates=0,new_8B_calls=0))


if __name__=='__main__':
    main()
