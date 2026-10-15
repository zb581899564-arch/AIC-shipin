"""CPU-only proof of complete native domains and one-to-one development grids."""
import hashlib,json
from pathlib import Path
def read(p):
    return [json.loads(s) for s in p.read_text(encoding='utf-8-sig').splitlines() if s.strip()]
def audit(old):
    paths=[old/'human_native_blocks.jsonl',old/'fixed_grid_samples.jsonl',old/'data/temporal_fixed_validation.jsonl']
    blocks,grid,targets=map(read,paths)
    sources=sorted({r['source_id'] for r in targets});assert len(sources)==9 and len(targets)==89
    assert {r['source_id'] for r in grid if r['split']=='validation'}==set(sources)
    assert {r['source_id'] for r in blocks if r['split']=='validation'}==set(sources)
    result={}
    for sid in sources:
        meta=json.loads((old.parent/'input'/sid/'manifest.json').read_text())
        n=meta['native_frames'];media=meta['media_sha256'];assert n==meta['human_vector_length']
        bb=sorted((b for b in blocks if b['source_id']==sid),key=lambda b:b['block_index'])
        gg=sorted((g for g in grid if g['source_id']==sid),key=lambda g:g['grid_index'])
        for records,index in ((bb,'block_index'),(gg,'grid_index')):
            assert [r[index] for r in records]==list(range(len(records)))
            assert records[0]['first_native_ordinal']==0 and records[-1]['end_native_ordinal_exclusive']==n
            end=0
            for r in records:
                assert r['first_native_ordinal']==end and r['end_native_ordinal_exclusive']>end
                end=r['end_native_ordinal_exclusive']
                assert r['split']=='validation' and r['source_group']=='youtube:'+sid and r['media_sha256']==media
                assert r['first_native_ordinal']<=r['sample_native_ordinal']<end
                assert len(r['worker_scores'])==20 and all(type(v) is int and 1<=v<=5 for v in r['worker_scores'])
                assert sum(r['worker_scores'])==r.get('worker_score_sum',r.get('scores_x20'))
        assert {r['native_pts_sha256'] for r in bb}=={meta['native_pts_sha256']}
        seen=[]
        for t in (t for t in targets if t['source_id']==sid):
            scores=json.loads(t['messages'][1]['content'])['scores_x20']
            assert t['media_sha256']==media and t['split']=='validation' and t['source_group']=='youtube:'+sid
            assert len(scores)==len(t['images'])==len(t['grid_indices'])==len(t['native_ordinals'])
            for g,ordinal,score,image in zip(t['grid_indices'],t['native_ordinals'],scores,t['images']):
                r=gg[g];assert ordinal==r['sample_native_ordinal'] and score==r['scores_x20'] and image==r['image'];seen.append(g)
        assert sorted(seen)==list(range(len(gg)))
        result[sid]={'native_frames':n,'human_blocks':len(bb),'grid_bins':len(gg),'complete_partition':True,'exact_target_coverage':True,'media_sha256':media}
    return {'status':'PASS_EXACT_NATIVE_PARTITIONS_AND_TARGET_GRID_COVERAGE','sources':result,'file_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
if __name__=='__main__':
    old=Path(__file__).resolve().parent.parent/'qwen8b_annotation_20261009_v1/training_v2'
    print(json.dumps(audit(old),indent=2))
