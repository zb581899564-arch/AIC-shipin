"""Descriptive full-answer multiplicity audit; no probabilities, masks or model."""
from collections import Counter,defaultdict
import argparse
import json
from pathlib import Path

from diagnose_underselection28 import read,ref,bound,save


def main(root):
    reg=read(root/'modal_target_registration34.json')
    assert ref(__file__)==reg['code_ref']
    rows=[json.loads(l) for l in bound(reg['target_ref']).read_text().splitlines() if l]
    assert len(rows)==2236
    groups=defaultdict(list)
    for x in rows:
        groups[x['uid']].append(x)
    details=[]
    for uid,items in groups.items():
        exact=Counter(x['target_json'] for x in items)
        empty=sum(n for text,n in exact.items() if not json.loads(text)['segments'])
        nonempty=[n for text,n in exact.items() if json.loads(text)['segments']]
        maximum=max(nonempty,default=0)
        details.append(dict(uid=uid,sid=items[0]['sid'],reviewers=len(items),empty_count=empty,
            nonempty_reviewers=len(items)-empty,distinct_nonempty_answers=len(nonempty),
            largest_identical_nonempty_count=maximum,empty_strict_full_answer_mode=empty>maximum,
            empty_full_answer_tied_mode=empty==maximum and empty>0,
            nonempty_reviewers_majority=len(items)-empty>empty))
    result=dict(status='COMPLETE_DESCRIPTIVE_ORIGINAL_TARGET_MULTIPLICITY_NO_MODEL',
        registration_ref=ref(root/'modal_target_registration34.json'),windows=len(details),targets=len(rows),
        empty_strict_full_answer_mode_windows=sum(x['empty_strict_full_answer_mode'] for x in details),
        empty_mode_even_with_nonempty_reviewer_majority=sum(x['empty_strict_full_answer_mode'] and x['nonempty_reviewers_majority'] for x in details),
        tied_empty_mode_windows=sum(x['empty_full_answer_tied_mode'] for x in details),
        all_reviewers_unselected_windows=sum(x['empty_count']==x['reviewers'] for x in details),
        details=details,model_calls=0,new_fit=0,prediction_or_reference_assisted_submission_masks_saved=False,
        interpretation='An identical empty answer can be the mode among distinct reviewer-specific interval answers even when most reviewers select content. Greedy token decoding is not full-sequence MAP; this descriptive fact does not establish causal sufficiency or justify merging/deleting human labels.')
    save(root/'modal_target_result34.json',result)
    print(json.dumps({k:v for k,v in result.items() if k!='details'},ensure_ascii=False))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True)
    main(p.parse_args().root)
