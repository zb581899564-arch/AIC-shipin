"""A frozen independent text/vision capability pilot, not a highlight selector."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent
OLD = WORK/'i3d_umt_cross_domain_20261021_v1/crossdata12'
REPO = 'd05afc436d78f1c48dc0dbf8e5980a9d471f35f6'
WEIGHT_URL = 'https://openaipublic.azureedge.net/clip/models/40d365715913c9da98579312b702a82c18be219cc2a73407c4526f58eba950af/ViT-B-32.pt'
WEIGHT_BYTES = 353976522
WEIGHT_SHA = '40d365715913c9da98579312b702a82c18be219cc2a73407c4526f58eba950af'


def read(path):
    return json.loads(Path(path).read_text())


def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for part in iter(lambda:f.read(1024*1024),b''):
            h.update(part)
    return h.hexdigest()


def ref(path):
    p=Path(path).resolve()
    return dict(path=str(p),bytes=p.stat().st_size,sha256=digest(p))


def checked(value):
    p=Path(value['path'])
    assert digest(p)==value['sha256'],p
    return p


def write(path,value):
    with Path(path).open('x',encoding='utf-8') as f:
        json.dump(value,f,ensure_ascii=False,indent=2,allow_nan=False)


def grouped_ap(scores,positive_counts,counts):
    """Average precision with whole equal-score groups, not favorable tie ordering."""
    import numpy as np
    scores,p,n=map(np.asarray,(scores,positive_counts,counts))
    assert scores.shape==p.shape==n.shape and np.isfinite(scores).all()
    assert np.all((0<=p)&(p<=n)) and np.all(n>0)
    total=float(p.sum())
    if not 0 < total < n.sum():
        return None
    order=np.argsort(-scores,kind='stable')
    tp=seen=area=0.0
    i=0
    while i<len(order):
        j=i+1
        while j<len(order) and scores[order[j]]==scores[order[i]]:
            j+=1
        batch=order[i:j]
        new=float(p[batch].sum())
        tp+=new;seen+=float(n[batch].sum())
        area+=(new/total)*(tp/seen)
        i=j
    return float(area)
