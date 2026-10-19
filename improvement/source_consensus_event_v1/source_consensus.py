"""One bounded external source-stability diagnosis and conditional repair.

No media, processor, 8B forward, formal-data access, automatic production,
threshold search, fivefold, or retry. Old completed outputs stay unchanged.
"""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
os.environ.setdefault('OPENBLAS_NUM_THREADS', '2')
from pathlib import Path
import datetime as dt
import importlib.util
import json
import sys
import numpy as np

W = Path('/home/inspur/aic_video_work')
ROOT = W/'source_consensus_event_20261018_v1'
OLD = W/'relative_precision_event_20261018_v1'
EVENT = W/'meaningful_residual_20261018_v1'


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


helper = load('_source_consensus_existing_helpers', OLD/'production_code_v2/evaluate_completecase3c_v2.py')
critic = load('_source_consensus_original_relative_leaf', OLD/'code_v1/relative_precision.py')
read, save, ref, bound, require = helper.read, helper.save, helper.ref, helper.bound, helper.require
sys.path.insert(0, str(W/'calibrated_event_20261018_v1/source_normalized_code_v2'))
from multiple_choice import multiple_choice_knapsack


def deadline(fit=False):
    scope = read(ROOT/'scope_before_diagnosis_01.json')
    end = scope['new_CPU_fit_cutoff_utc'] if fit else scope['deadline_utc']
    require(dt.datetime.now(dt.timezone.utc) < dt.datetime.fromisoformat(end.replace('Z','+00:00')), 'Registered bounded work deadline')


def npz(path, **arrays):
    with Path(path).open('xb') as stream:
        np.savez(stream, **arrays)


def external_sources():
    from coverage_event import catalogue
    sources = catalogue()
    completion = read(OLD/'confirm3c_remaining_02/stages/finalize/completion.json')
    for source in completion['sources']:
        sources.append(dict(**source, cohort='exposed_completecase3c', references_ref=ref(OLD/'confirm3c_remaining_02/references/references.json')))
    require(len(sources) == 19 and len({s['sid'] for s in sources}) == 19, 'Exactly existing19 exposed sources')
    return sources


def labels(source, clock, native):
    from coverage_event import labels_for
    return labels_for(source, clock, native)


def prepare_diagnosis():
    deadline()
    out = ROOT/'diagnosis_01'; out.mkdir()
    pca = dict(np.load(EVENT/'pca.npz', allow_pickle=False))
    old_model = dict(np.load(OLD/'model.npz', allow_pickle=False))
    train = [s for s in read(EVENT/'registration.json')['sources'] if s['group'] == 'train']
    require(len(train) == 25, 'Only the fixed25 original-human training sources')
    training, source_h, source_b = [], [], []
    for source in train:
        deadline()
        native = np.load(bound(source['data_ref']), allow_pickle=False)
        clock = read(bound(source['clock_ref']))
        language = np.load(bound(source['language_ref']), allow_pickle=False)
        candidates = critic.proposals(clock, native['baseline'])
        x, stats = critic.differences(language, native['groups'], native['baseline'], candidates, pca)
        require(stats['anchor_present'] and len(candidates), 'All registered training anchors are present')
        target = critic.target_differences(native['baseline'], native['labels'], candidates)
        z = x/old_model['scale']
        source_h.append(z.T@z/len(z)); source_b.append(z.T@target/len(z))
        path = out/(source['sid']+'_train.npz')
        npz(path, difference32=x, target_precision_difference=target)
        training.append(dict(sid=source['sid'], cache_ref=ref(path), original_source=source, candidates=len(x)))
    h = np.sum(source_h, axis=0)+np.eye(32)
    require(np.allclose(np.linalg.solve(h, np.sum(source_b,axis=0)),old_model['coef'],atol=1e-12,rtol=1e-10), 'Sufficient statistics match the adopted single fit, not a new fit')
    npz(out/'sufficient_statistics.npz', h=np.asarray(source_h), rhs=np.asarray(source_b), scale=old_model['scale'])
    # These are linear contributions to the adopted estimator, not refitted heads.
    coefficient_contributions = np.linalg.solve(h, np.asarray(source_b).T).T
    old16 = {v['sid']:v for v in read(OLD/'outputs_frozen_before_metrics.json')['sources']}
    old3 = {v['sid']:v for v in read(OLD/'confirm3c_evaluation_02/frozen_inference_before_metrics.json')['sources']}
    inputs, rows = [], []
    for source in external_sources():
        deadline()
        sid=source['sid']; native=np.load(bound(source['data_ref']),allow_pickle=False)
        clock=read(bound(source['clock_ref']));language=np.load(bound(source['language_ref']),allow_pickle=False)
        baseline=native['baseline']; candidates=critic.proposals(clock,baseline)
        x,stats=critic.differences(language,native['groups'],baseline,candidates,pca)
        original = old16[sid] if sid in old16 else old3[sid]
        if sid in old16:
            outputs=np.load(bound(original['score_ref']),allow_pickle=False)
            oldmask=np.load(bound(original['mask_ref']),allow_pickle=False)
        else:
            outputs=np.load(bound(original['output_ref']),allow_pickle=False);oldmask=outputs['relative']
        raw=outputs['raw_precision_difference']; oldgain=outputs['estimated_precision_gain']
        require(len(raw)==len(x) and np.allclose(x/old_model['scale']@old_model['coef'],raw,atol=1e-12,rtol=1e-10), 'Adopt original scores and candidate alignment')
        path=out/(sid+'_input.npz')
        npz(path,difference32=x,baseline=baseline,original_raw=raw,original_gain=oldgain,original_selected=oldmask)
        inputs.append(dict(sid=sid,cohort=source['cohort'],source=source,input_ref=ref(path),clock_ref=source['clock_ref'],candidates=candidates,anchor=stats))
        human=labels(source,clock,native)
        target=critic.target_differences(baseline,human,candidates)
        contributions=(x/old_model['scale'])@coefficient_contributions.T
        selected=None
        choice=original.get('choice') if sid in old16 else original['choices']['relative']
        if choice is not None:
            matches=[i for i,c in enumerate(candidates) if c['left']==choice['left'] and c['right']==choice['right']]
            require(len(matches)==1, 'Original exact chosen event preserved')
            i=matches[0];pos=np.maximum(contributions[i],0)
            selected=dict(index=i,predicted_precision_contrast=float(raw[i]),actual_precision_contrast=float(target[i]),source_contributors_positive=int(np.sum(contributions[i]>0)),largest_positive_source_fraction=float(pos.max()/pos.sum()) if pos.sum() else None,selected_added_frames=choice['added_frames'])
        positive=raw>0
        rows.append(dict(sid=sid,cohort=source['cohort'],candidates=len(x),predicted_positive=int(positive.sum()),positive_prediction_wrong_sign=int(np.sum(positive&(target<=0))),candidate_mse=float(np.mean((raw-target)**2)) if len(raw) else None,selected=selected))
        npz(out/(sid+'_human_targets.npz'),labels=human,target_precision_difference=target)
    wrong=sum(v['selected'] is not None and v['selected']['actual_precision_contrast']<0 for v in rows)
    total=sum(v['selected'] is not None for v in rows)
    result=dict(status='COMPLETED_NEW_EXTERNAL19_SELECTION_OPTIMISM_AND_SOURCE_CONTRIBUTION_DIAGNOSIS',training_sources=25,external_sources=19,selected_sources=total,selected_precision_harm_sources=wrong,rows=rows,new_8B_calls=0,formal_data_read=False,all_validation_previously_exposed=True,utc=helper.utc())
    save(out/'inputs.json',dict(training=training,external=inputs,pca_ref=ref(EVENT/'pca.npz'),old_model_ref=ref(OLD/'model.npz'),statistics_ref=ref(out/'sufficient_statistics.npz')))
    save(out/'result.json',result)
    print(json.dumps(dict(status=result['status'],selected_sources=total,selected_precision_harm_sources=wrong,selected=[dict(sid=v['sid'],**v['selected']) for v in rows if v['selected'] is not None])),flush=True)


def lower_scores(x, candidates, baseline, model):
    members=(x/model['scale'])@model['coefs'].T
    # Fixed before this diagnostic. An empirical lower quantile is not a
    # statistically calibrated confidence interval or domain-shift guarantee.
    lower=np.quantile(members,0.05,axis=1,method='linear')
    counts=np.asarray([c['added_frames'] for c in candidates],float)
    utility=counts/(int(baseline.sum())+counts)*np.clip(lower,-1,1)
    return lower,utility,members


def fit_and_evaluate():
    deadline(True)
    require(read(ROOT/'repair_admission_02.json')['allow_one_fixed_source_bootstrap_fit'] is True,'Explicit post-diagnosis repair admission')
    manifest=read(ROOT/'diagnosis_01/inputs.json')
    stats=np.load(bound(manifest['statistics_ref']),allow_pickle=False)
    require(stats['h'].shape==(25,32,32) and stats['rhs'].shape==(25,32),'All source-equal sufficient statistics')
    rng=np.random.default_rng(20261018)
    draws=rng.multinomial(25,np.full(25,1/25),size=32)
    coefs=np.asarray([np.linalg.solve(np.einsum('s,sij->ij',count,stats['h'])+np.eye(32),count@stats['rhs']) for count in draws])
    require(np.isfinite(coefs).all(),'Finite32 source-bootstrap heads, fixedalpha1')
    model=dict(scale=stats['scale'],coefs=coefs)
    npz(ROOT/'model.npz',**model)
    restored=dict(np.load(ROOT/'model.npz',allow_pickle=False))
    require(all(np.array_equal(v,restored[k]) for k,v in model.items()),'Final weights actual save/reload equality')
    npz(ROOT/'source_bootstrap_draws.npz',counts=draws)
    save(ROOT/'fit_completion.json',dict(status='COMPLETED_ONE_FIXED32_WHOLE_SOURCE_BOOTSTRAP_ENSEMBLE',weights_ref=ref(ROOT/'model.npz'),draws_ref=ref(ROOT/'source_bootstrap_draws.npz'),seed=20261018,new_model_scalars=sum(v.size for v in model.values()),source_count=25,replicas=32,alpha=1,quantile=0.05,training_inputs_ref=ref(ROOT/'diagnosis_01/inputs.json'),old_weights_unchanged=True,utc=helper.utc()))
    out=ROOT/'evaluation_01';out.mkdir();inputs=[]
    for row in manifest['external']:
        data=np.load(bound(row['input_ref']),allow_pickle=False)
        lower,gain,members=lower_scores(data['difference32'],row['candidates'],data['baseline'],model)
        require(np.all(np.isfinite(members)) and np.allclose(members[0],np.sum(data['difference32']/model['scale']*model['coefs'][0],axis=1),atol=1e-12,rtol=1e-10),'First direct new member/output check')
        path=out/(row['sid']+'_scores.npz');npz(path,lower_precision_difference=lower,gain=gain,members=members)
        inputs.append(dict(row=row,data=data,lower=lower,gain=gain,output_ref=ref(path)))
    selections={}
    for cohort in sorted({v['row']['cohort'] for v in inputs}):
        group=[v for v in inputs if v['row']['cohort']==cohort]
        options={v['row']['sid']:[dict(candidate_index=i,added_frames=c['added_frames'],predicted_gain=float(v['gain'][i])) for i,c in enumerate(v['row']['candidates']) if v['gain'][i]>0] for v in group}
        selections[cohort]=multiple_choice_knapsack(options,sum(int(v['data']['baseline'].sum()) for v in group)//10)
    frozen=[]
    for v in inputs:
        row=v['row'];sid=row['sid'];index=selections[row['cohort']]['chosen'].get(sid);mask=v['data']['baseline'].copy()
        choice=None if index is None else row['candidates'][index]
        if choice is not None:mask[choice['left']:choice['right']]=True
        path=out/(sid+'_mask.npy')
        with path.open('xb') as f:np.save(f,mask)
        frozen.append(dict(sid=sid,cohort=row['cohort'],mask_ref=ref(path),score_ref=v['output_ref'],choice=choice,positive_candidates=int(np.sum(v['gain']>0)),successful_null=not np.any(v['gain']>0),lower_at_choice=None if index is None else float(v['lower'][index])))
    save(out/'frozen_before_metrics.json',dict(status='ALL19_FROZEN_BEFORE_CURRENT_REPAIR_METRICS',sources=frozen,selections=selections,weights_ref=ref(ROOT/'model.npz'),all19_previously_exposed=True,old_prospective3_no_longer_blind=True,utc=helper.utc()))
    rows=[]
    for v,f in zip(inputs,frozen):
        row=v['row'];sid=row['sid'];human=np.load(ROOT/'diagnosis_01'/(sid+'_human_targets.npz'),allow_pickle=False)['labels']
        mask=np.load(bound(f['mask_ref']),allow_pickle=False);before=critic.metric(v['data']['baseline'],human);old=critic.metric(v['data']['original_selected'],human);after=critic.metric(mask,human);added=mask&~v['data']['baseline']
        rows.append(dict(sid=sid,cohort=row['cohort'],before=before,old_relative=old,after=after,delta={k:after[k]-before[k] for k in ['precision','recall','f1']},minus_old={k:after[k]-old[k] for k in ['precision','recall','f1']},added_frames=int(added.sum()),old_added_frames=int(np.sum(v['data']['original_selected']&~v['data']['baseline'])),successful_null=f['successful_null'],newframe_human_precision=None if not added.any() else float(human[added].mean())))
    def summary(group):
        return dict(sources=len(group),macro_delta={k:float(np.mean([r['delta'][k] for r in group])) for k in ['precision','recall','f1']},macro_minus_old={k:float(np.mean([r['minus_old'][k] for r in group])) for k in ['precision','recall','f1']},precision_up=sum(r['delta']['precision']>0 for r in group),precision_down=sum(r['delta']['precision']<0 for r in group),f1_up=sum(r['delta']['f1']>0 for r in group),f1_down=sum(r['delta']['f1']<0 for r in group),added_frames=sum(r['added_frames'] for r in group),changed=sum(r['added_frames']>0 for r in group),successful_nulls=sum(r['successful_null'] for r in group),worst_f1=min(r['delta']['f1'] for r in group))
    result=dict(status='COMPLETED_SINGLE_SOURCE_STABILITY_REPAIR_REVIEW_REQUIRED',summary={**{c:summary([r for r in rows if r['cohort']==c]) for c in selections},'all19':summary(rows)},sources=rows,automatic_production=False,all19_previously_exposed=True,calibrated_confidence_claim=False,official_joint_score=None,new_8B_calls=0,formal_data_read=False,utc=helper.utc())
    save(out/'result.json',result);print(json.dumps(result['summary']),flush=True)


if __name__=='__main__':
    try:
        require(os.name=='posix','Linux resident only')
        {'diagnose':prepare_diagnosis,'repair':fit_and_evaluate}[sys.argv[1]]()
    except BaseException as error:
        import traceback,uuid
        save(ROOT/('failure_'+uuid.uuid4().hex+'.json'),dict(error=repr(error),traceback=traceback.format_exc(),original_successes_preserved=True,no_automatic_retry=True,utc=helper.utc()))
        raise
