"""Supervisor audit against pinned annotations and actual media bytes."""
import argparse
import hashlib
import json
from pathlib import Path
import statistics
from evaluation_v2.temporal import intervals, read_jsonl


def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(4*1024**2),b''):
            h.update(block)
    return h.hexdigest()


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--data',required=True);ap.add_argument('--output',required=True)
    args=ap.parse_args();root=Path(args.data)
    official={split:{str(x['qid']):x for x in read_jsonl(root/'source'/f'highlight_{split}_release.jsonl')}
              for split in ('train','val')}
    sets={};summary={};seen_hashes={};errors=[]
    for split,minimum in [('train',200),('dev',50),('holdout',50)]:
        rows=read_jsonl(root/(split+'.jsonl'));ids=set();groups=set()
        for row in rows:
            key=str(row['video_id'])
            try:
                assert key not in ids,'duplicate query ID'
                ids.add(key)
                qid=key.removeprefix('qvh_')
                assert key=='qvh_'+qid and qid in official['train' if split=='train' else 'val'],'qid/split'
                ref=official['train' if split=='train' else 'val'][qid]
                assert row['source_vid']==ref['vid'],'source vid'
                assert row['query']==ref['query'],'query'
                assert row['answer']['segments']==ref['relevant_windows'],'target changed'
                assert row['source_group']==ref['vid'].rsplit('_',2)[0],'source grouping'
                groups.add(row['source_group'])
                duration=float(row['duration_sec'])
                assert abs(duration-float(ref['duration']))<=1,'duration difference'
                assert row['alignment_verified'] is True,'alignment flag'
                assert row['task_type']=='query_moment_retrieval','task type'
                assert len(ref['relevant_windows'])<=4,'too many windows'
                intervals(ref['relevant_windows'],duration)
                expected=[[2*i,min(duration,2*i+2)] for i,values in zip(ref['relevant_clip_ids'],ref['saliency_scores'])
                          if statistics.median(values)>=3 and 2*i<duration]
                assert intervals(row['saliency_segments'],duration)==intervals(expected,duration),'saliency derivation'
                path=Path(row['video_path']).resolve()
                assert str(path).startswith('/home/inspur/aic_video_data/videos/'),'outside public training media'
                if str(path) not in seen_hashes:
                    seen_hashes[str(path)]=digest(path)
                assert row['video_sha256']==seen_hashes[str(path)],'media hash'
            except (AssertionError,ValueError,KeyError,OSError) as exc:
                errors.append({'split':split,'video_id':key,'reason':str(exc)})
        assert len(rows)>=minimum,'minimum sample count'
        sets[split]=groups
        summary[split]=dict(rows=len(rows),unique_query_ids=len(ids),source_groups=len(groups),
                            trusted_identity=sum(x.get('trusted_identity') is True for x in rows),
                            sha256=digest(root/(split+'.jsonl')))
    overlap={a+'__'+b:sorted(sets[a]&sets[b]) for a,b in [('train','dev'),('train','holdout'),('dev','holdout')]}
    result=dict(structural_media_audit_passed=not errors and not any(overlap.values()),
                training_authorized=False,source_provenance_acceptance='SEPARATE_REQUIRED_DECISION',
                summary=summary,unique_media_hashed=len(seen_hashes),overlap=overlap,errors=errors)
    Path(args.output).write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='errors'}))
    if errors or any(overlap.values()):
        print(json.dumps(errors[:5]))
        raise SystemExit(1)


if __name__=='__main__':
    main()
