"""One new label-free nested-observation plan and reference-only CPU audit."""
import argparse
from pathlib import Path
import sys
import traceback
import datetime as dt
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'pair_code_17'))
from pair_common import *
from observation_sampling import augment_native_samples, compare_observations


def run(root):
    require(os.environ.get('CUDA_VISIBLE_DEVICES')=='','CPU-only observation audit')
    import numpy as np
    reg=read(root/'observation_registration_27.json')
    require(reg['schema']=='NESTED_OLD8_PLUS24_NATIVE_OBSERVABILITY_ONLY_V27' and
            bound(reg['code'])==Path(__file__).resolve(),'Exact first observation audit')
    import observation_sampling
    require(bound(reg['sampling_code'])==Path(observation_sampling.__file__).resolve(),'Frozen exact label-free sampling')
    require(dt.datetime.now(dt.timezone.utc)<dt.datetime.fromisoformat(reg['deadline_utc'].replace('Z','+00:00')),
            'Within overall work window')
    audit=read(bound(reg['marginal_audit']))
    catalog=read(bound(reg['source_catalog']))
    sources={s['id']:s for s in catalog['sources']}
    out=root/'observation_audit_27';out.mkdir(exist_ok=False)
    save(out/'claim.json',dict(utc=utc(),pid=os.getpid(),registration=ref(root/'observation_registration_27.json'),
        model_calls=0,media_reads=0,decoder_calls=0,processor_calls=0))
    done=[]
    try:
        for entry in audit['sources']:
            data=read(bound(entry['result']));sid=data['id'];source=sources[sid]
            require(source['source_sha256']==data['source_sha256'] and source['native']==data['native'] and
                    source['role']==data['role'],'One actual source/label/native identity')
            clock=read(bound(source['clock']))
            require(clock['source_sha256']==source['source_sha256'],'Bound original source PTS')
            with np.load(bound(data['native']),allow_pickle=False) as value:sample_ordinals=value['sample_ordinals'].copy()
            raw=np.load(bound(data['annotation']),allow_pickle=False)
            require(raw.ndim==2 and len(raw)==clock['n_frames'] and np.isfinite(raw).all(),'Complete original native human labels')
            labels=raw>0;clip_cache={}
            def observe(clip):
                key=(clip['native_start'],clip['native_end_exclusive'])
                if key not in clip_cache:
                    original=sample_ordinals[clip['cell_start']:clip['cell_end_exclusive']].tolist()
                    sampling=augment_native_samples(clock['normalized_exact_pts'],*key,original,
                        source_end_exact=clock['physical_end_exact'],samples=32)
                    result=compare_observations(labels,original,sampling)
                    clip_cache[key]=dict(clip=clip,sampling=sampling,result=result)
                return clip_cache[key]
            anchor=data['inventory']['anchor']
            anchor_observe=observe(anchor) if anchor is not None else None
            rows=[]
            for candidate in data['candidates']:
                observation=observe(candidate['clip']);result=observation['result']
                comparisons={}
                if anchor_observe is not None and result['new32_applicable'] and anchor_observe['result']['new32_applicable']:
                    target=np.asarray(candidate['old_anchor_preference']['preference_distribution'],dtype=float)
                    for view_name in ('OLD8','NEW32'):
                        def counts(observed):
                            v=observed['result']['views'][view_name]
                            weights=np.asarray(v['nearest_observation_native_reconstruction']['observation_native_frame_weights'],dtype=np.int64)
                            return (labels[v['sample_ordinals']].astype(np.int64)*weights[:,None]).sum(axis=0)
                        c=counts(observation);a=counts(anchor_observe)
                        nc=candidate['clip']['native_frames'];na=anchor['native_frames']
                        pref=np.where(c*na>a*nc,0,np.where(c*na<a*nc,1,2))
                        distribution=np.bincount(pref,minlength=3)/labels.shape[1]
                        comparisons[view_name]=dict(distribution=distribution.tolist(),
                            distribution_brier=float(np.sum((distribution-target)**2)),
                            candidate_strict_majority=bool((pref==0).sum()*2>len(pref)),
                            reference_censoring_simulation_only=True)
                rows.append(dict(clip=candidate['clip'],macro_gain=candidate['gain']['macro_delta'],
                    complete_native_candidate_preference_majority=(candidate['old_anchor_preference']['candidate_has_strict_rater_majority']
                        if candidate['old_anchor_preference'] is not None else None),
                    observation=observation,preference_reconstruction=comparisons))
            result_path=out/(sid+'.json')
            save(result_path,dict(id=sid,source_sha256=source['source_sha256'],role=data['role'],rows=rows,
                 anchor=anchor_observe,reference_only=True,model_quality=False,source_clock=source['clock']))
            applicable=[r for r in rows if r['observation']['result']['new32_applicable']]
            stats={}
            for view in ('OLD8','NEW32'):
                stats[view]=dict(
                    native_weighted_density_MAE=float(np.mean([x['observation']['result']['views'][view]['nearest_observation_native_reconstruction']['mean_absolute_density_error'] for x in applicable])) if applicable else None,
                    native_reference_disagreement=float(np.mean([x['observation']['result']['views'][view]['nearest_observation_native_reconstruction']['mean_native_reference_disagreement_fraction'] for x in applicable])) if applicable else None,
                    preference_reconstruction_Brier=float(np.mean([x['preference_reconstruction'][view]['distribution_brier'] for x in applicable if x['preference_reconstruction']])) if any(x['preference_reconstruction'] for x in applicable) else None)
            positives=[x for x in applicable if x['macro_gain']>0]
            path=[x for x in positives if x['complete_native_candidate_preference_majority'] is True]
            done.append(dict(id=sid,role=data['role'],candidates=len(rows),new32_applicable=len(applicable),
                positive_candidates=len(positives),positive_policy_path_candidates=len(path),metrics=stats,result=ref(result_path),
                positive_path_old_Brier=float(np.mean([x['preference_reconstruction']['OLD8']['distribution_brier'] for x in path])) if path else None,
                positive_path_new_Brier=float(np.mean([x['preference_reconstruction']['NEW32']['distribution_brier'] for x in path])) if path else None))
        summary={}
        for role in ('train','dev'):
            part=[r for r in done if r['role']==role];values={}
            for view in ('OLD8','NEW32'):
                values[view]={key:float(np.mean([s['metrics'][view][key] for s in part if s['metrics'][view][key] is not None]))
                              for key in ('native_weighted_density_MAE','native_reference_disagreement','preference_reconstruction_Brier')}
            summary[role]=dict(sources=len(part),candidates=sum(s['candidates'] for s in part),
                applicable=sum(s['new32_applicable'] for s in part),positive_policy_path_candidates=sum(s['positive_policy_path_candidates'] for s in part),
                source_equal_metrics=values,positive_source_details=[s for s in part if s['positive_candidates']])
        save(out/'result.json',dict(status='COMPLETE_FIRST_NESTED_OBSERVABILITY_METADATA_NOT_MODEL_QUALITY',
            sources=done,summary=summary,model_calls=0,media_reads=0,decoder_calls=0,processor_calls=0,
            all_raters=True,historical_exposure=True,baseline_scope='B0 NOT complete40.47',
            original_GT_unchanged=True,production_admitted=False,new_dense_GT_created=False))
        print(json.dumps(summary),flush=True)
    except BaseException as error:
        save(out/'failure.json',dict(error=repr(error),traceback=traceback.format_exc(),completed=done,preserve_all_success=True))
        raise


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);run(p.parse_args().root)
