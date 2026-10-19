"""Conditional one-shot Q00..Q03 evaluation; predictions precede human values.

No preparation, model forward, fitting, recovery, or automatic production.
Run only after the registered generic pipeline has completed its first QA.
"""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
os.environ.setdefault('OPENBLAS_NUM_THREADS', '2')
from bisect import bisect_left
import datetime as dt
from fractions import Fraction as F
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import traceback
import uuid
import numpy as np

W = Path('/home/inspur/aic_video_work')
ROOT = W/'relative_precision_event_20261018_v1'
EVENT = W/'meaningful_residual_20261018_v1'
PIPELINE = ROOT/'confirm4c_01'
SELECTION = ROOT/'prospective_selection_before_confirm4c_01.json'
REGISTRATION = ROOT/'new4c_confirmation_registration_01.json'
MODEL_SHA = '27debc750703a3be87bc998a29fd17f3faeee8e63eade27018830dca7e7aefb4'
SOURCE_IDS = ['Q00', 'Q01', 'Q02', 'Q03']


def require(ok, message):
    if not ok:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            value.update(block)
    return value.hexdigest()


def ref(path):
    path = Path(path)
    return dict(path=str(path), bytes=path.stat().st_size, sha256=sha(path))


def bound(value):
    path = Path(value['path'])
    require(path.is_file() and sha(path) == value['sha256'] and
            ('bytes' not in value or path.stat().st_size == value['bytes']), 'Changed adopted file: '+str(path))
    return path


def bind_refs(value):
    """Check every explicit file ref in a prospective/admission document."""
    if isinstance(value, dict):
        if 'path' in value and 'sha256' in value:
            bound(value)
        for child in value.values():
            bind_refs(child)
    elif isinstance(value, list):
        for child in value:
            bind_refs(child)


def clean(value):
    if isinstance(value, dict):
        return {str(k):clean(v) for k,v in value.items()}
    if isinstance(value, (tuple, list)):
        return [clean(v) for v in value]
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, np.generic):
        return value.item()
    return value


def save(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf8') as stream:
        json.dump(clean(value), stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n'); stream.flush(); os.fsync(stream.fileno())


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def deadline(value):
    limit = value.get('deadline_utc', value.get('deadline'))
    require(limit is not None, 'An explicit registered final deadline is required')
    parsed = dt.datetime.fromisoformat(limit.replace('Z', '+00:00'))
    require(parsed.tzinfo is not None and dt.datetime.now(dt.timezone.utc) < parsed, 'Registered final work deadline reached')


def load_module(name, path):
    specification = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(specification)
    sys.modules[name] = module
    specification.loader.exec_module(module)
    return module


def frozen_model(selection_path=SELECTION):
    frozen = read(selection_path)
    deadline(frozen); bind_refs(frozen)
    require(frozen.get('final_new_confirmation_attempt') is True and frozen.get('new_model_fit') == 0,
            'Adopt the prospective final confirmation with no new fit')
    weights = frozen['weights_ref']
    require(weights['sha256'] == MODEL_SHA, 'The one already fitted final relative64 model')
    model = dict(np.load(bound(weights), allow_pickle=False))
    require(set(model) == {'scale', 'coef'} and all(v.shape == (32,) for v in model.values()) and
            all(np.isfinite(v).all() for v in model.values()) and (model['scale'] > 0).all(), 'Exactly64 finite fitted scalars, no intercept')
    pca = dict(np.load(bound(frozen['pca_ref']), allow_pickle=False))
    require(set(pca) == {'pca_mean', 'pca_components'} and pca['pca_mean'].shape == (4096,) and
            pca['pca_components'].shape == (32,4096) and all(np.isfinite(v).all() for v in pca.values()), 'Exactly the frozen135168-scalar PCA32')
    fit = read(bound(frozen.get('fit_ref', frozen.get('fit_completion_ref'))))
    require(fit['weights_ref']['sha256'] == MODEL_SHA and fit['pca_ref'] == frozen['pca_ref'] and fit['new_model_scalars'] == 64,
            'Prospective selection and actual fit bind the same model/PCA')
    critic_ref = frozen.get('code_ref', frozen.get('critic_code_ref'))
    critic_path = bound(critic_ref)
    sys.path.insert(0, str(EVENT/'code_v1'))
    critic = load_module('_relative_precision_prospective_leaf', critic_path)
    require(Path(critic.predict.__code__.co_filename).resolve() == critic_path.resolve() and
            Path(critic.differences.__code__.co_filename).resolve() == critic_path.resolve(), 'Actual prediction and difference functions use the frozen critic')
    solver_path = bound(frozen['solver_ref'])
    solver = load_module('_relative_precision_prospective_solver', solver_path)
    return frozen, model, pca, critic, solver.multiple_choice_knapsack


def native_fields(data, clock, language):
    baseline, groups, score = data['baseline'], data['groups'], data['semantic_score']
    points = list(map(F, clock['normalized_exact_pts']))
    require(baseline.dtype == np.bool_ and groups.ndim == score.ndim == 1 and len(baseline) == len(groups) == len(points), 'Complete native policy and group field')
    require(len(points) > 0 and points[0] == 0 and all(a < b for a,b in zip(points,points[1:])) and points[-1] < F(clock['physical_end_exact']), 'Unshifted full measured native clock')
    bins = np.asarray([int(t*2) for t in points], np.int64)
    require(np.array_equal(np.unique(bins, return_inverse=True)[1], groups), 'Exact occupied2Hz native groups')
    require(groups.min() == 0 and groups.max()+1 == len(score) and language.shape == (len(score),4096) and
            np.isfinite(language).all() and np.isfinite(score).all(), 'Actual finite BASE4096/semantic field aligned to groups')
    return baseline, groups, score


def difference_output_qa(critic, language, groups, baseline, candidates, pca, model):
    x, statistics = critic.differences(language, groups, baseline, candidates, pca)
    projected = critic.projected(language, pca)
    anchor = projected[groups[baseline]].mean(0) if baseline.any() else None
    direct = []
    for i, candidate in enumerate(candidates):
        left, right = candidate['left'], candidate['right']
        require(0 <= left < right <= len(baseline), 'Real candidate native interval')
        indices = np.flatnonzero(~baseline[left:right])+left
        require(len(indices) == candidate['added_frames'] > 0, 'Every unique actual added frame counted once')
        direct.append(np.zeros(32) if anchor is None else projected[groups[indices]].mean(0)-anchor)
    direct = np.asarray(direct, np.float64).reshape(-1,32)
    require(np.allclose(x, direct, atol=2e-12, rtol=1e-10), 'First direct native-index anchor/difference feature QA')
    raw, gain = critic.predict(x, candidates, baseline, model, statistics['anchor_present'])
    direct_raw = np.sum(direct/model['scale']*model['coef'], axis=1)
    sizes = np.asarray([c['added_frames'] for c in candidates], float)
    direct_gain = sizes/(int(baseline.sum())+sizes)*np.clip(direct_raw,-1,1) if len(sizes) else np.empty(0)
    if anchor is None:
        direct_gain[:] = 0
    require(np.allclose(raw,direct_raw,atol=2e-12,rtol=1e-10) and np.allclose(gain,direct_gain,atol=2e-12,rtol=1e-10), 'First independent no-bias precision utility output QA')
    return x, raw, gain, statistics


def labels_exact(clock, reference):
    points = list(map(F, clock['normalized_exact_pts']))
    require(clock['original_exact_pts'] == clock['normalized_exact_pts'] and points[0] == 0, 'Original exact seconds, no reference shifting')
    spans = reference['annotator_intervals_exact_seconds']
    require(len(spans) == 10 and all(spans), 'All ten original human reviewers')
    labels = np.zeros((len(points),10), bool)
    for reviewer, intervals in enumerate(spans):
        for start, stop in intervals:
            start, stop = F(start), F(stop)
            require(0 <= start < stop <= F(clock['physical_end_exact']), 'Original endpoint fits without resizing')
            labels[bisect_left(points,start):bisect_left(points,stop),reviewer] = True
    return labels


def summarize(rows, name):
    deltas = {metric:[v[name+'_delta'][metric] for v in rows] for metric in ('precision','f1','recall')}
    return dict(sources=len(rows), **{'macro_'+k+'_delta':float(np.mean(v)) for k,v in deltas.items()},
        f1_improved=sum(v>0 for v in deltas['f1']), f1_decreased=sum(v<0 for v in deltas['f1']),
        precision_improved=sum(v>0 for v in deltas['precision']), precision_decreased=sum(v<0 for v in deltas['precision']),
        worst_f1_delta=min(deltas['f1']), worst_precision_delta=min(deltas['precision']),
        changed_sources=sum(row[name+'_added_frames']>0 for row in rows), added_frames=sum(row[name+'_added_frames'] for row in rows),
        successful_nulls=sum(row[name+'_successful_null'] for row in rows), budget_omissions=sum(row[name+'_budget_omitted'] for row in rows))


def main():
    require(os.name == 'posix', 'Only the registered Linux execution environment')
    frozen, model, pca, critic, solver = frozen_model()
    registration = read(REGISTRATION)
    require(registration['source_ids'] == SOURCE_IDS and Path(registration['pipeline_root']) == PIPELINE, 'Exactly the fixed prospective Q00..Q03 cohort')
    prepared_path = PIPELINE/'stages/finalize/completion.json'
    prepared = read(prepared_path)
    require(prepared['status'] == 'PASS' and prepared.get('labels_read') is False and
            [s['sid'] for s in prepared['sources']] == SOURCE_IDS and all(s['labels_read'] is False for s in prepared['sources']), 'First complete pipeline/output QA, no labels in model')
    require(len({s['name'] for s in prepared['sources']}) == 4, 'Four distinct original source identities')
    if 'selection' in registration:
        require([s['name'] for s in prepared['sources']] == [s['video_id'] for s in registration['selection']], 'Model cohort exactly matches the registered original source order')
    require(prepared['original_model_parameters']+prepared['original_semantic_parameters'] == 8782557449, 'Adopt the actual original full policy parameter count')
    admission_path = PIPELINE/'references/native_admission_for_model.json'
    admission = read(admission_path)
    require(admission['status'] == 'PASS' and admission['source_ids'] == SOURCE_IDS and admission['original_endpoints_fit'] is True and
            admission['no_label_resizing'] is True and admission['labels_provided_to_model'] is False, 'Unchanged original endpoint admission')
    out = ROOT/'confirm4c_evaluation_01'; out.mkdir()
    save(out/'start.json', dict(prospective_selection_ref=ref(SELECTION), registration_ref=ref(REGISTRATION), code_ref=ref(__file__), pipeline_completion_ref=ref(prepared_path), native_admission_ref=ref(admission_path), utc=utc()))
    items = []
    for source in prepared['sources']:
        deadline(frozen)
        require(admission['clock_sha256_by_sid'][source['sid']] == source['clock_ref']['sha256'], 'Endpoint admission binds this exact clock')
        data = np.load(bound(source['data_ref']),allow_pickle=False)
        clock = read(bound(source['clock_ref'])); language = np.load(bound(source['language_ref']),allow_pickle=False)
        baseline, groups, score = native_fields(data,clock,language)
        candidates = critic.proposals(clock,baseline)
        x,raw,gain,stats = difference_output_qa(critic,language,groups,baseline,candidates,pca,model)
        field = score[groups]
        means = np.asarray([field[c['left']:c['right']][~baseline[c['left']:c['right']]].mean() for c in candidates])
        control = None
        if len(means):
            index = int(np.argmax(means))  # Raw ordering, sigmoid only for budget value.
            control = dict(sid=source['sid'],candidate_index=index,added_frames=candidates[index]['added_frames'],predicted_gain=float(1/(1+np.exp(-np.clip(means[index],-30,30)))))
        options = [dict(candidate_index=i,added_frames=c['added_frames'],predicted_gain=float(gain[i])) for i,c in enumerate(candidates) if gain[i]>0]
        items.append(dict(source=source,clock=clock,baseline=baseline,candidates=candidates,x=x,raw=raw,gain=gain,stats=stats,control=control,options=options))
    budget = sum(int(v['baseline'].sum()) for v in items)//10
    relative_selection = solver({v['source']['sid']:v['options'] for v in items},budget)
    control_selected = critic.knapsack([v['control'] for v in items if v['control']],budget) if hasattr(critic,'knapsack') else None
    # relative_precision imports only named event leaves, so obtain the original
    # source-local top1 budget function from their already loaded module.
    if control_selected is None:
        from event_features import knapsack
        control_selected = knapsack([v['control'] for v in items if v['control']],budget)
    outputs = []
    for item in items:
        sid = item['source']['sid']; masks,choices = {},{}
        indices = dict(relative=relative_selection['chosen'].get(sid),control=None if sid not in control_selected else item['control']['candidate_index'])
        for name,index in indices.items():
            mask = item['baseline'].copy(); choice = None if index is None else item['candidates'][index]
            if choice is not None: mask[choice['left']:choice['right']] = True
            require(np.all(item['baseline']<=mask), 'Original full baseline native frames preserved')
            masks[name]=mask;choices[name]=choice
        path=out/(sid+'_outputs.npz')
        with path.open('xb') as stream:
            np.savez(stream,baseline=item['baseline'],relative=masks['relative'],control=masks['control'],difference32=item['x'],raw_precision_difference=item['raw'],estimated_precision_gain=item['gain'])
        outputs.append(dict(sid=sid,name=item['source']['name'],source=item['source'],output_ref=ref(path),candidates=item['candidates'],choices=choices,anchor=item['stats'],relative_added_frames=int(np.sum(masks['relative']&~item['baseline'])),control_added_frames=int(np.sum(masks['control']&~item['baseline'])),relative_successful_null=not item['options'],control_successful_null=item['control'] is None,relative_budget_omitted=bool(item['options']) and indices['relative'] is None,control_budget_omitted=item['control'] is not None and indices['control'] is None))
    require(sum(v['relative_added_frames'] for v in outputs) == relative_selection['total_cost'] <= budget and
            sum(v['control_added_frames'] for v in outputs) <= budget, 'Both actual unique-native selections obey the same original10percent budget')
    save(out/'frozen_inference_before_metrics.json',dict(status='ALL_Q00_Q03_OUTPUTS_AND_BOTH_BUDGETS_FROZEN_BEFORE_HUMAN_VALUES',sources=outputs,relative_selection=relative_selection,control_selected=sorted(control_selected),budget=budget,weights_ref=frozen['weights_ref'],pca_ref=frozen['pca_ref'],prospective_selection_ref=ref(SELECTION),labels_read=False,no_new_fit=True,utc=utc()))
    # First access to the actual interval file occurs after every prediction and
    # both global selections have been committed above.
    reference_path=PIPELINE/'references/references.json'
    reference_rows=read(reference_path)
    references={v['name']:v for v in reference_rows}
    require(len(reference_rows)==len(references)==4 and set(references)=={v['name'] for v in outputs}, 'All and only the four original reference identities')
    rows=[]
    for item,output in zip(items,outputs):
        labels=labels_exact(item['clock'],references[output['name']])
        data=np.load(bound(output['output_ref']),allow_pickle=False)
        baseline_metric=critic.metric(data['baseline'],labels)
        row=dict(sid=output['sid'],name=output['name'],baseline=baseline_metric,choices=output['choices'],native_frames=len(labels),reviewers=10)
        for name in ('relative','control'):
            result=critic.metric(data[name],labels); added=data[name]&~data['baseline']
            row[name]=result;row[name+'_delta']={k:result[k]-baseline_metric[k] for k in ('precision','f1','recall')}
            row[name+'_added_frames']=int(added.sum());row[name+'_newframe_reviewer_precision']=None if not added.any() else float(labels[added].mean())
            row[name+'_successful_null']=output[name+'_successful_null'];row[name+'_budget_omitted']=output[name+'_budget_omitted']
        row['relative_minus_control']={k:row['relative'][k]-row['control'][k] for k in ('precision','f1','recall')}
        rows.append(row)
    summaries={name:summarize(rows,name) for name in ('relative','control')}
    summaries['relative_minus_control']={k:float(np.mean([v['relative_minus_control'][k] for v in rows])) for k in ('precision','f1','recall')}
    save(out/'result.json',dict(status='COMPLETED_PROSPECTIVE_FIXED4C_RESEARCH_REVIEW_REQUIRED',summary=summaries,sources=rows,references_ref=ref(reference_path),frozen_outputs_ref=ref(out/'frozen_inference_before_metrics.json'),official_joint_score_estimate=None,global_pretraining_independence='UNKNOWN',automatic_production=False,source_or_method_retuned=False,new_fit=0,new_8B_calls=0,utc=utc()))
    save(out/'completion.json',dict(status='COMPLETED_ONCE_NO_AUTOMATIC_PRODUCTION',result_ref=ref(out/'result.json'),utc=utc()))
    print(json.dumps(clean(summaries)),flush=True)


if __name__=='__main__':
    try:
        main()
    except BaseException as error:
        save(ROOT/('confirm4c_evaluation_failure_'+uuid.uuid4().hex+'.json'),dict(error=repr(error),traceback=traceback.format_exc(),successes_preserved=True,no_automatic_retry=True,utc=utc()))
        raise
