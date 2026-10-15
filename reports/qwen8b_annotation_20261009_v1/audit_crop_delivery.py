"""Independent CPU artifact audit: no imported annotation validator or model calls."""
from pathlib import Path
from collections import Counter,defaultdict
from datetime import datetime,timezone
from fractions import Fraction
import json,hashlib
from PIL import Image
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'exports/codex_crop_v1'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as fp:
        for chunk in iter(lambda:fp.read(4*1024*1024),b''):h.update(chunk)
    return h.hexdigest()
def jsonl(p):return [json.loads(s) for s in p.read_text(encoding='utf-8').splitlines() if s]
def write(p,rows):
    p.write_text(''.join(json.dumps(x,ensure_ascii=False,separators=(',',':'))+'\n' for x in rows),encoding='utf-8')
def main():
    split=read(ROOT/'split.json');groups={x['source_id']:x for x in split['sources']}
    assert len(groups)==50 and Counter(x['split'] for x in groups.values())=={'train':40,'validation':10}
    cat=Counter((x['category'],x['split']) for x in groups.values())
    assert len(cat)==20 and all(v==(4 if s=='train' else 1) for (c,s),v in cat.items())
    manifests={s:read(ROOT/'input'/s/'manifest.json') for s in groups}
    media_hashes=[];frame_map={};bindings=[]
    for sid,m in manifests.items():
        g=groups[sid];assert m['source_group']==g['source_group'] and m['split']==g['split']
        mp=ROOT/'input'/sid/m['media_file'];assert digest(mp)==m['media_sha256'];media_hashes.append(m['media_sha256'])
        pts=ROOT/'input'/sid/'native_pts.npz';assert digest(pts)==m['native_pts_sha256']
        assert len(m['frames'])==12 and {f['sample_index'] for f in m['frames']}==set(range(12))
        for f in m['frames']:
            p=ROOT/'input'/sid/f['file'];assert digest(p)==f['png_sha256']
            im=Image.open(p).convert('RGB');assert im.size==(f['width'],f['height'])
            assert hashlib.sha256(im.tobytes()).hexdigest()==f['rgb24_sha256']
            assert f['sample_id'] not in frame_map;frame_map[f['sample_id']]=(m,f,p)
        bindings.append(dict(source_id=sid,split=m['split'],manifest_sha256=digest(ROOT/'input'/sid/'manifest.json'),media_sha256=m['media_sha256'],native_pts_sha256=m['native_pts_sha256']))
    assert len(frame_map)==600 and len(set(media_hashes))==50
    labels=jsonl(OUT/'labels.jsonl');assert len(labels)==1200
    keys=set();passes={};states=Counter();sizes=Counter();views_checked=set();categories=defaultdict(Counter)
    for row in labels:
        sid=row['source_id'];m,f,p=frame_map[row['sample_id']];assert m['source_id']==sid
        assert row['split']==m['split'] and row['source_group']==m['source_group']
        assert Path(row['image_path']).resolve()==p.resolve() and row['png_sha256']==f['png_sha256']
        assert row['source_media_sha256']==m['media_sha256'] and row['frame_index']==f['frame_index']
        assert row['pts']==f['pts'] and row['time_base']==f['time_base']
        assert (Fraction(row['pts'])*Fraction(*row['time_base']))==Fraction(f['pts'])*Fraction(*f['time_base'])
        ratio=tuple(row['ratio']);assert ratio in ((16,9),(9,16));key=(row['sample_id'],ratio);assert key not in keys;keys.add(key)
        raw=Path(row['draft_path']);rev=Path(row['review_path'])
        assert digest(raw)==row['draft_sha256'] and digest(rev)==row['review_sha256']
        review=read(rev);assert review['draft_sha256']==digest(raw)
        c=next(c for c in review['checks'] if c['sample_index']==f['sample_index'] and tuple(c['targetRatioWH'])==ratio)
        assert c==row['visual_check'];verdict=c['verdict'];assert verdict in ('PASS','UNKNOWN','REJECT');states[verdict]+=1
        categories[(m['category'],m['split'])][verdict]+=1
        if row['state']=='UNKNOWN':assert row.get('box_xywh') is None and c['actual_crop'] is None and verdict=='UNKNOWN';continue
        assert row['state']=='CROP' and verdict!='UNKNOWN'
        x,y,w,h=row['box_xywh'];assert all(type(n)==int for n in (x,y,w,h))
        assert x>=0 and y>=0 and w>0 and h>0 and w*ratio[1]==h*ratio[0]
        assert x+w<=f['width'] and y+h<=f['height']
        actual=c['actual_crop'];cp=Path(actual['file']);assert digest(cp)==actual['sha256']
        original=Image.open(p).convert('RGB');expected=original.crop((x,y,x+w,y+h));got=Image.open(cp).convert('RGB')
        assert got.size==(w,h) and got.tobytes()==expected.tobytes()
        views_checked.add(str(cp))
        if verdict=='PASS':
            passes[key]=row;sizes[(m['split'],f'{ratio[0]}x{ratio[1]}','identity' if (x,y,w,h)==(0,0,f['width'],f['height']) else 'nonidentity')]+=1
    assert len(keys)==1200 and len(views_checked)==states['PASS']+states['REJECT']
    all_ids=set();sets={};nonidentity={};summary={}
    for name in ('train','validation'):
        rows=jsonl(OUT/f'crop_sft_{name}.jsonl');sets[name]=set();focus=[];ratio_counts=Counter()
        for r in rows:
            assert r['id'] not in all_ids;all_ids.add(r['id']);lr=r['label_record'];key=(lr['sample_id'],tuple(lr['ratio']))
            assert lr==passes[key] and lr['split']==name and r['images']==[lr['image_path']]
            m,f,p=frame_map[lr['sample_id']];sets[name].add(m['source_group'])
            assert r['source_id']==m['source_id'] and r['source_group']==m['source_group']
            x,y,w,h=lr['box_xywh'];assert json.loads(r['messages'][1]['content'])=={'box_xyw':[x,y,w]}
            assert '<image>' in r['messages'][0]['content'] and f'{f["width"]}x{f["height"]}' in r['messages'][0]['content']
            assert r['annotation_quality']=='MODEL_ANNOTATED_WEAK_LABEL';ratio_counts[f'{lr["ratio"][0]}x{lr["ratio"][1]}']+=1
            if (x,y,w,h)!=(0,0,f['width'],f['height']):focus.append(r)
        # Optional derived data excluding the many trivial unchanged horizontal images.
        write(OUT/f'crop_sft_{name}_nonidentity.jsonl',focus);nonidentity[name]=len(focus)
        summary[name]=dict(rows=len(rows),source_groups=len(sets[name]),ratio_counts=dict(ratio_counts),nonidentity_rows=len(focus))
    assert not sets['train']&sets['validation'] and len(all_ids)==len(passes)
    assert len(sets['train'])==40 and len(sets['validation'])==10
    artifacts={p.name:dict(bytes=p.stat().st_size,sha256=digest(p)) for p in sorted(OUT.glob('*.jsonl'))}
    report=dict(status='PASS_INDEPENDENT_FULL_CORPUS_ARTIFACT_AUDIT',utc=datetime.now(timezone.utc).isoformat(),sources=50,frames=600,ratio_records=1200,
        verdict_counts=dict(states),sft=summary,actual_crop_rgb_equal_original_pixel_region=len(views_checked),
        unique_media_sha256=50,source_group_disjoint=True,category_split_counts={f'{c}/{s}':v for (c,s),v in sorted(cat.items())},
        category_verdict_counts={f'{c}/{s}':dict(v) for (c,s),v in sorted(categories.items())},
        split_sha256=digest(ROOT/'split.json'),acceptance_sha256=digest(OUT/'acceptance.json'),source_bindings=bindings,
        raw_source_and_review_sha_verified=True,artifacts=artifacts,annotation_quality='MODEL_WEAK_LABEL_AND_SELF_REVIEW; NOT_HUMAN_GOLD',
        actual_model_training_started=False,gpu_used=False,new_model_calls=0,
        exclusions='UNKNOWN and REJECT are absent from all SFT targets; unknown is not a negative label.',
        nonidentity_subset='Deterministic subset of accepted full SFT rows with a box different from full original image; no oversampling, relabeling, or split changes.')
    (OUT/'independent_audit.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:report[k] for k in ('status','sources','frames','ratio_records','verdict_counts','sft','actual_crop_rgb_equal_original_pixel_region')},ensure_ascii=False,indent=2))
if __name__=='__main__':main()
