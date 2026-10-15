"""Read-only human-importance proxy diagnostic; never creates training targets."""
import collections,hashlib,json
from fractions import Fraction
from pathlib import Path
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    original=H.parent/'qwen8b_annotation_20261009_v1/training_v2/human_native_blocks.jsonl'
    blocks=[json.loads(s) for s in original.read_text().splitlines()]
    paths=sorted((H/'agy_v2').glob('*/labels.json'));assert len(paths)==6
    clips=[];state_counts=collections.Counter()
    for p in paths:
        labels=json.loads(p.read_text());m=json.loads((p.parent/'manifest.json').read_text())
        assert labels['source_id']==m['source_id'] and labels['input_sha256']==m['clip_sha256']
        assert sha(p.parent/'clip.mp4')==m['clip_sha256']
        bb=[b for b in blocks if b['source_id']==m['source_id']]
        assert all(b['media_sha256']==m['source_sha256'] and b['split']=='train' for b in bb)
        lookup={i:b['worker_score_sum']/20 for b in bb for i in range(b['first_native_ordinal'],b['end_native_ordinal_exclusive'])}
        samples=[]
        for c in labels['candidates']:
            k=c['candidate_id'];frames=[x['ordinal'] for x in m['source_mapping'] if 2*k<=Fraction(x['local_seconds_exact'])<2*k+2]
            assert frames and all(i in lookup for i in frames)
            state_counts[c['state']]+=1
            samples.append({'candidate_id':k,'state':c['state'],'native_frames':len(frames),'human_proxy_mean':sum(lookup[i] for i in frames)/len(frames),
               'teacher_claimed_observation_instants':c['actually_observed_local_seconds'],'not_semantic_highlight_gold':True})
        assert [x['candidate_id'] for x in samples]==list(range(15))
        clips.append({'clip':p.parent.name,'samples':samples,'labels_sha256':sha(p),'manifest_sha256':sha(p.parent/'manifest.json'),
          'mean_human_proxy_by_state':{s:sum(x['human_proxy_mean'] for x in samples if x['state']==s)/sum(x['state']==s for x in samples) for s in set(x['state'] for x in samples)}})
    report={'status':'SIX_SHORT_CLIPS_COMPLETE_WEAK_LABELS_QUARANTINED','clips':clips,'states':dict(state_counts),
       'training_admitted':0,'actual_clips':6,'candidate_bins':90,'source_groups':3,'full_observation_proven':False,
       'human_reference_sha256':sha(original),'proxy_only_not_teacher_accuracy':True,'UNKNOWN_never_negative':True}
    with (H/'annotation_summary.json').open('x') as f:json.dump(report,f,indent=2)
    print(json.dumps({k:v for k,v in report.items() if k!='clips'}))
if __name__=='__main__':main()
