"""One new CPU-only target-mismatch audit; never fits or calls a model."""
import argparse
from pathlib import Path
import sys
import traceback

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'pair_code_17'))
from pair_common import *
from pair_preference_math import prepare_policy
from marginal_addition_math import f1_delta, preference_comparison


def run(root):
    require(os.environ.get('CUDA_VISIBLE_DEVICES') == '', 'CPU audit masks only itself')
    import numpy as np
    reg = read(root/'marginal_audit_registration_24.json')
    require(reg['schema'] == 'FIRST_BASELINE_CONDITIONAL_GAIN_AUDIT_V24', 'Explicit new audit entry')
    require(bound(reg['code']) == Path(__file__).resolve(), 'This exact audit code only')
    import marginal_addition_math
    require(bound(reg['math']) == Path(marginal_addition_math.__file__).resolve(), 'Frozen exact marginal math')
    oldreg = read(bound(reg['pair_registration']))
    for name in ('pair_common.py', 'pair_preference_math.py'):
        require(sha(root/'pair_code_17'/name) == oldreg['new_code'][name], 'Accepted geometry helper changed')
    require(read(bound(reg['pair_STOP']))['production_prepare_approved'] is False, 'Old pair failure remains stopped')
    catalog = read(bound(oldreg['assembled_external']))
    prior = read(bound(oldreg['original_ranking_diagnostic']))
    annotations = {s['id']:s for s in prior['sources']}
    out = root/'marginal_audit_24'; out.mkdir(exist_ok=False)
    save(out/'claim.json', dict(utc=utc(), registration=ref(root/'marginal_audit_registration_24.json'),
         pid=os.getpid(), new_model_calls=0, new_fits=0, new_media=0))
    done=[]
    try:
        require(len(catalog['sources']) == 25 and sum(s['role']=='train' for s in catalog['sources']) == 20 and
                sum(s['role']=='dev' for s in catalog['sources']) == 5, 'Fixed historical20/5 roles')
        for source in catalog['sources']:
            sid=source['id']; old=annotations[sid]
            require(old['source_sha256'] == source['source_sha256'] and old['role'] == source['role'] and
                    old['bindings']['native'] == source['native'] and old['bindings']['source_features'] == source['features'],
                    'Same accepted source/native/feature identities')
            with np.load(bound(source['features']), allow_pickle=False) as f: groups=f['native_group'].copy()
            with np.load(bound(source['native']), allow_pickle=False) as f:
                cells=f['groups'].copy(); baseline=f['baseline'].copy()
            labelref=old['bindings']['original_annotation_array']
            raw=np.load(bound(labelref), allow_pickle=False)
            require(raw.ndim==2 and len(raw)==len(groups)==len(baseline) and np.isfinite(raw).all(),
                    'Complete exact native all-reviewer labels; no remap or missing-to-zero')
            labels=raw>0; policy=prepare_policy(groups,cells,baseline)
            anchor=None
            if policy['anchor'] is not None:
                anchor=np.zeros_like(baseline)
                a=policy['anchor'];anchor[a['native_start']:a['native_end_exclusive']]=True
            candidates=[]
            for clip in policy['candidates']:
                selected=np.zeros_like(baseline);selected[clip['native_start']:clip['native_end_exclusive']]=True
                gain=f1_delta(labels, baseline, selected)
                comparison=preference_comparison(labels,baseline,selected,anchor) if anchor is not None else None
                candidates.append(dict(clip=clip, gain=gain, old_anchor_preference=comparison))
            save(out/(sid+'.json'),dict(id=sid,role=source['role'],source_sha256=source['source_sha256'],
                native=source['native'],features=source['features'],annotation=labelref,inventory=policy,candidates=candidates,
                baseline_scope='Historical original external B0; NOT complete40.47',new_model_calls=0))
            positive=[x for x in candidates if x['gain']['macro_delta']>0]
            negative=[x for x in candidates if x['gain']['macro_delta']<0]
            done.append(dict(id=sid,role=source['role'],candidates=len(candidates),
                positive_expected_gain=len(positive),negative_expected_gain=len(negative),
                zero_expected_gain=len(candidates)-len(positive)-len(negative),
                best_positive_oracle_delta=max([0.]+[x['gain']['macro_delta'] for x in candidates]),
                positive_without_anchor_majority=sum(x['old_anchor_preference']['macro_positive_without_preference_majority']
                    for x in candidates if x['old_anchor_preference'] is not None),
                anchor_majority_without_positive=sum(x['old_anchor_preference']['preference_majority_without_macro_positive']
                    for x in candidates if x['old_anchor_preference'] is not None),
                has_fixed_anchor=anchor is not None,result=ref(out/(sid+'.json'))))
        summary={}
        for role in ('train','dev'):
            part=[x for x in done if x['role']==role]
            summary[role]=dict(sources=len(part),candidates=sum(x['candidates'] for x in part),
                sources_with_positive_gain=sum(x['positive_expected_gain']>0 for x in part),
                sources_with_negative_gain=sum(x['negative_expected_gain']>0 for x in part),
                positive_candidates=sum(x['positive_expected_gain'] for x in part),
                negative_candidates=sum(x['negative_expected_gain'] for x in part),
                zero_candidates=sum(x['zero_expected_gain'] for x in part),
                positive_without_anchor_majority=sum(x['positive_without_anchor_majority'] for x in part),
                anchor_majority_without_positive=sum(x['anchor_majority_without_positive'] for x in part),
                best_one_addition_oracle_macro_delta=float(np.mean([x['best_positive_oracle_delta'] for x in part])),
                oracle_is_not_a_model=True)
        save(out/'result.json',dict(status='COMPLETE_FIRST_NATIVE_MARGINAL_GAIN_TARGET_AUDIT_ONLY',
            sources=done,summary=summary,new_model_calls=0,new_fits=0,new_media=0,production_admitted=False,
            all_original_raters=True,historical_exposure=True,independent_blind=False,
            baseline_scope='Historical original B0 NOT complete40.47',official_joint_metric=False,
            unselected_is_not_ordinary=True))
        print(json.dumps(summary),flush=True)
    except BaseException as error:
        save(out/'failure.json',dict(error=repr(error),traceback=traceback.format_exc(),completed=done,
             preserve_all_success=True,no_automatic_retry=True))
        raise


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);run(p.parse_args().root)
