"""Explicit source-transport recovery: identical pinned Git blobs via direct API."""
import base64
import hashlib
import json
import sys
from common import ROOT,REPO,WEIGHT_URL,WEIGHT_BYTES,WEIGHT_SHA,ref,write
from acquire import fetch,dependency

BLOBS={
    '__init__.py':(20,'dcc5619538c0f7c782508bdbd9587259d805e0d9'),
    'clip.py':(9644,'398a6282cc243e449430d91c2562491fc799929d'),
    'model.py':(17374,'232b7792eb97440642547bd462cf128df9243933'),
    'simple_tokenizer.py':(4632,'0a66286b7d5019c6e221932a813768038f839c91'),
    'bpe_simple_vocab_16e6.txt.gz':(1356917,'7b5088a527f720063f044eb928eee315f63b2fc0'),
}


def from_api(url,path,name,expected=None):
    meta=ROOT/'downloads'/f'api_{name}.json'
    fetch(url,meta,3_000_000)
    obj=json.loads(meta.read_text())
    assert obj['encoding']=='base64'
    data=base64.b64decode(obj['content'])
    git_sha=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
    assert git_sha==obj['sha'] and len(data)==obj['size']
    if expected:
        assert (len(data),git_sha)==expected
    with path.open('xb') as f:f.write(data)
    return dict(**ref(path),git_blob_sha1=git_sha,api_metadata=ref(meta),commit=REPO)


def main():
    assert not list((ROOT/'vendor/clip').iterdir()) and not list((ROOT/'model').iterdir())
    write(ROOT/'acquire_remaining02_claim.json',dict(previous='Raw-source HTTPS timeout before first success; original failure preserved',
              successful_assets_before_recovery=0,scientific_protocol_unchanged=True,
              transport='Same pinned author Git blobs via API, real direct physical route verified'))
    files=[]
    for name,expected in BLOBS.items():
        files.append(from_api(f'https://api.github.com/repos/openai/CLIP/git/blobs/{expected[1]}',ROOT/'vendor/clip'/name,name,expected))
    for name in ['LICENSE','model-card.md','README.md']:
        files.append(from_api(f'https://api.github.com/repos/openai/CLIP/contents/{name}?ref={REPO}',ROOT/'downloads'/name,name))
    assert 'MIT License' in (ROOT/'downloads/LICENSE').read_text()
    files.append(dependency('ftfy','6.3.1'))
    files.append(dependency('wcwidth','0.2.13'))
    files.append(fetch(WEIGHT_URL,ROOT/'model/ViT-B-32.pt',WEIGHT_BYTES,(WEIGHT_BYTES,WEIGHT_SHA)))
    sys.path.insert(0,str(ROOT/'vendor'))
    import clip
    import torch
    model=torch.jit.load(str(ROOT/'model/ViT-B-32.pt'),map_location='cpu')
    params=sum(p.numel() for p in model.parameters())
    assert params+8782557449<=9_000_000_000
    write(ROOT/'asset_acceptance.json',dict(status='DIRECT_OFFICIAL_CLIP_ASSETS_ACCEPTED',files=files,
              actual_clip_parameters=params,combined_with_protected_baseline=params+8782557449,
              model_downloads=1,model_inferences=0,explicit_recovery='acquire_remaining02'))


if __name__=='__main__':
    main()
