"""Only registered official CLIP assets and tiny project-local dependencies."""
import ipaddress
import json
from pathlib import Path
import shutil
import subprocess
import sys
import urllib.request
import zipfile

from common import ROOT,REPO,WEIGHT_URL,WEIGHT_BYTES,WEIGHT_SHA,digest,ref,write

OPENER=urllib.request.build_opener(urllib.request.ProxyHandler({}))


def route(response):
    peer=response.fp.raw._sock.getpeername()[0]
    info=json.loads(subprocess.check_output(['ip','-j','route','get',peer],text=True))
    dev=info[0]['dev']
    assert ipaddress.ip_address(peer).is_global
    assert (Path('/sys/class/net')/dev/'device').exists()
    assert not any(t in dev.lower() for t in ['tun','tap','tailscale','wg','warp','easytier'])
    return dict(peer=peer,route=info,proxy='EXPLICIT_EMPTY',final_url=response.geturl())


def fetch(url,path,limit,expected=None):
    assert not path.exists() and not path.with_suffix(path.suffix+'.partial').exists()
    partial=path.with_suffix(path.suffix+'.partial')
    with OPENER.open(url,timeout=40) as response:
        observed=route(response)
        write(path.with_suffix(path.suffix+'.route.json'),observed)
        size=0
        with partial.open('xb') as f:
            while chunk:=response.read(1024*1024):
                size+=len(chunk)
                assert size<=limit
                f.write(chunk)
    if expected:
        assert size==expected[0] and digest(partial)==expected[1]
    partial.rename(path)
    return dict(url=url,**ref(path))


def dependency(name,version):
    info=ROOT/'downloads'/f'{name}-{version}.json'
    fetch(f'https://pypi.org/pypi/{name}/{version}/json',info,250000)
    data=json.loads(info.read_text())
    wheels=[r for r in data['urls'] if r['filename'].endswith('py3-none-any.whl') or r['filename'].endswith('py2.py3-none-any.whl')]
    assert len(wheels)==1
    wheel=wheels[0]
    path=ROOT/'downloads'/wheel['filename']
    fetch(wheel['url'],path,200000,(wheel['size'],wheel['digests']['sha256']))
    with zipfile.ZipFile(path) as z:
        assert z.testzip() is None
        for member in z.infolist():
            p=(ROOT/'vendor'/member.filename).resolve()
            assert p.is_relative_to((ROOT/'vendor').resolve())
            assert not ((member.external_attr>>16)&0o170000)==0o120000
        z.extractall(ROOT/'vendor')
    return ref(path)


def main():
    write(ROOT/'acquire_claim.json',dict(scope='One official353976522B model, official code/BPE, two <=200KB dependency wheels; direct only'))
    for name in ['downloads','vendor','model']:
        (ROOT/name).mkdir()
    (ROOT/'vendor/clip').mkdir()
    assert shutil.disk_usage(ROOT).free>WEIGHT_BYTES+60_000_000
    records=[]
    for name in ['__init__.py','clip.py','model.py','simple_tokenizer.py','bpe_simple_vocab_16e6.txt.gz']:
        records.append(fetch(f'https://raw.githubusercontent.com/openai/CLIP/{REPO}/clip/{name}',ROOT/'vendor/clip'/name,2000000))
    for name in ['LICENSE','model-card.md','README.md']:
        records.append(fetch(f'https://raw.githubusercontent.com/openai/CLIP/{REPO}/{name}',ROOT/'downloads'/name,100000))
    assert 'MIT License' in (ROOT/'downloads/LICENSE').read_text()
    records.append(dependency('ftfy','6.3.1'))
    records.append(dependency('wcwidth','0.2.13'))
    records.append(fetch(WEIGHT_URL,ROOT/'model/ViT-B-32.pt',WEIGHT_BYTES,(WEIGHT_BYTES,WEIGHT_SHA)))
    sys.path.insert(0,str(ROOT/'vendor'))
    import clip
    import torch
    # No image/text inference here: enumerate the genuine complete official model.
    archive=torch.jit.load(str(ROOT/'model/ViT-B-32.pt'),map_location='cpu')
    parameters=sum(p.numel() for p in archive.parameters())
    del archive
    assert parameters+8782557449<=9_000_000_000
    write(ROOT/'asset_acceptance.json',dict(status='DIRECT_OFFICIAL_CLIP_ASSETS_ACCEPTED',
              files=records,actual_clip_parameters=parameters,
              combined_with_protected_baseline=parameters+8782557449,
              model_downloads=1,model_inferences=0))


if __name__=='__main__':
    main()
