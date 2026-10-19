"""Explicitly admitted production after disclosed engineering complete-case3/4 review.

No fitting, image processor, media decode, GPU/model forward, or auto admission.
Requires ROOT/production_admission_02.json. Never resumes a partial production.
"""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
os.environ.setdefault('OPENBLAS_NUM_THREADS', '2')
import hashlib
import importlib.util
import json
from fractions import Fraction as F
from pathlib import Path
import subprocess
import sys
import traceback
import uuid
import zipfile
import numpy as np

# Import only this task's sibling helper, independent of generic module names.
_spec = importlib.util.spec_from_file_location('_relative_precision_completecase3_delivery_helpers', Path(__file__).with_name('evaluate_completecase3c_v2.py'))
helper = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(helper)
ROOT, EVENT, W = helper.ROOT, helper.EVENT, helper.W
OLD = W/'semantic_context_production_20261016_v1'
SOURCE_CLEAR = W/'source_clear_residual_20261018_v1'
HISTORY = EVENT/'production_code_v1/current_delivered_history_01.json'
ADMISSION = ROOT/'production_admission_02.json'
BASE_PARAMETERS = 8782557449
ACTUAL_PARAMETERS = 8782692681
BASE_SHA = 'b37c4a2e6593fc800f54ecce2f860fee5e7d5dc74e17ce280f9ee6722afbccd3'
read, save, ref, bound, require = helper.read, helper.save, helper.ref, helper.bound, helper.require


def dump(path, rows):
    with Path(path).open('x', encoding='utf8') as stream:
        for row in rows:
            stream.write(json.dumps(helper.clean(row),ensure_ascii=False,separators=(',',':'),allow_nan=False)+'\n')


def histories(value):
    if isinstance(value,dict):
        for key,child in value.items():
            if key in ('canonical_sha256','canonical_SHA256','prediction_sha256','canonical_prediction_sha256') and isinstance(child,str):
                yield child
            else:
                yield from histories(child)
    elif isinstance(value,list):
        for child in value:
            yield from histories(child)


def canonical(rows):
    # Parameter metadata must never turn an identical prediction into a new one.
    value=[{key:row[key] for key in ('video_id','targetRatioWH','predictions')} for row in sorted(rows,key=lambda row:row['video_id'])]
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def main():
    require(os.name=='posix','Only the registered Linux environment')
    # This is deliberately the first runtime artifact read. An absent admission
    # must stop before opening any formal feature/native/prediction files.
    admission=read(ADMISSION)
    require(admission.get('allow_one_fixed_relative_precision_package') is True and admission['mechanism']=='RELATIVE_PRECISION_EVENT', 'Explicit reviewed single-package admission required')
    helper.deadline(admission); helper.bind_refs(admission)
    require(Path(bound(admission['prospective_selection_ref'])).resolve()==helper.SELECTION.resolve(),'Admit the unchanged prospective selection')
    require(Path(bound(admission['confirmation_ref'])).resolve()==(ROOT/'confirm3c_evaluation_02/result.json').resolve(),'Review the disclosed three-of-four engineering complete-case supplement')
    confirmation=read(bound(admission['confirmation_ref']))
    require(confirmation['status']=='COMPLETED_PROSPECTIVE_ENGINEERING_COMPLETECASE3C_REVIEW_REQUIRED' and confirmation['automatic_production'] is False,'Confirmation is research evidence, admission supplies the production decision')
    require(confirmation['partial_confirmation'] is True and confirmation['confirmation_not_full4'] is True and
            confirmation['engineering_excluded_source_ids']==['Q00'] and confirmation['no_reference_repair'] is True and
            [row['sid'] for row in confirmation['sources']]==helper.SOURCE_IDS,
            'Adopt only the explicitly disclosed engineering complete-case3/4 supplement, never original4 PASS')
    helper.engineering_evidence(read(helper.REGISTRATION))
    require(Path(bound(admission['producer_code_ref'])).resolve()==Path(__file__).resolve() and
            Path(bound(admission['evaluation_code_ref'])).resolve()==Path(helper.__file__).resolve(),'Both new implementation files are explicitly bound')
    frozen,model,pca,critic,solver=helper.frozen_model(bound(admission['prospective_selection_ref']))
    require(confirmation['frozen_outputs_ref']['sha256']==ref(ROOT/'confirm3c_evaluation_02/frozen_inference_before_metrics.json')['sha256'],'Confirmation binds the frozen predictions')
    frozen_outputs=read(bound(confirmation['frozen_outputs_ref']))
    require(frozen_outputs['engineering_registration_ref']['sha256']==ref(helper.REGISTRATION)['sha256'] and
            frozen_outputs['partial_confirmation'] is True and frozen_outputs['confirmation_not_full4'] is True,
            'Frozen complete-case outputs bind the same engineering-only exclusion registration')
    history_ref=admission['current_delivered_history_ref']
    require(bound(history_ref).resolve()==HISTORY.resolve(),'Use the complete authoritative delivered-history inventory')
    authoritative=set(histories(read(bound(history_ref))))
    require(len(authoritative)==admission['current_delivered_history_canonical_count']==33,'Exactly33 authoritative delivered canonical predictions')
    protected_risks=admission['protected_risk_completion_refs']
    require(len(protected_risks)==3 and len({v['path'] for v in protected_risks})==3,'Explicitly bind all original three risk packages')
    for value in protected_risks:
        require(Path(bound(value)).resolve().is_relative_to((EVENT/'packages').resolve()),'Protected risk completion must stay in the original event packages directory')
        require(read(bound(value)).get('canonical_sha256') is not None,'Protected risk completion must carry its actual canonical prediction')
    bound(admission['official_rule_receipt_ref'])
    accepted_path=EVENT/'formal_inputs_01/completion.json'
    accepted=read(accepted_path)
    require(accepted['status']=='PASS426_FIRST_NATIVE_EVENT_DESCRIPTOR_QA' and len(accepted['sources'])==426,'Adopt the successful original426 native/candidate first QA')
    pca_weights=dict(np.load(bound(accepted['pca_weights_ref']),allow_pickle=False))
    require(all(np.array_equal(pca[key],pca_weights[key]) for key in pca),'Actual adopted descriptor PCA equals the frozen relative PCA')
    feature_path=OLD/'feature_completion.json'
    old_features=read(feature_path)
    inherited={row['id']:row for row in old_features['sources']}
    require(len(inherited)==426 and set(inherited)=={str(i) for i in range(426)},'Complete original426 BASE4096 source inventory')
    actual=BASE_PARAMETERS+sum(v.size for v in pca.values())+sum(v.size for v in model.values())
    require(sum(v.size for v in pca.values())==135168 and sum(v.size for v in model.values())==64 and actual==ACTUAL_PARAMETERS and actual<=9_000_000_000,'Actual base/TIME/semantic+PCA+64 count exactly8.782692681B')
    sys.path.insert(0,str(EVENT/'code_v1'))
    runtime=helper.load_module('_relative_precision_adopted_event_runtime',EVENT/'code_v1/event_runtime.py')
    renderer,_=runtime.old_modules()
    require(Path(renderer.__file__).resolve()==(SOURCE_CLEAR/'code/render.py').resolve(),'Use the existing complete spatial renderer without rebinding its root')
    base_ref=read(EVENT/'registration.json')['baseline_ref']
    require(base_ref['sha256']==BASE_SHA,'Protected original40.47 archive identity')
    with zipfile.ZipFile(bound(base_ref)) as archive:
        base=[json.loads(line) for line in archive.read('predictions.jsonl').splitlines()]
    baseline_frames={(row['video_id'],prediction['frame']):prediction['bboxes'] for row in base for prediction in row['predictions']}
    require(len(base)==426 and len(baseline_frames)==123506,'Complete original40.47 record/frame denominator')
    baseline_by_sid={sid:{ordinal for source,ordinal in baseline_frames if source==sid} for sid in inherited}
    out=ROOT/'production_01'; out.mkdir()
    save(out/'start.json',dict(admission_ref=ref(ADMISSION),prospective_selection_ref=admission['prospective_selection_ref'],model_ref=frozen['weights_ref'],pca_ref=frozen['pca_ref'],adopted_native_candidate_QA_ref=ref(accepted_path),adopted_BASE_feature_completion_ref=ref(feature_path),renderer_code_ref=ref(renderer.__file__),producer_code_ref=ref(__file__),evaluation_helpers_ref=ref(helper.__file__),actual_resident_parameters=actual,utc=helper.utc(),**helper.PARTIAL_DISCLOSURE))
    items,qa=[],[]
    for receipt_ref in accepted['sources']:
        helper.deadline(admission)
        row=read(bound(receipt_ref)); sid=row['sid']; old=inherited[sid]
        with np.load(bound(row['input_ref']),allow_pickle=False) as value:
            baseline=value['baseline']
        native_path=OLD/'inputs'/sid/'native.npz'
        native_ref=dict(path=str(native_path),sha256=old['native_sha256'])
        with np.load(bound(native_ref),allow_pickle=False) as value:
            groups=value['groups']
        language_ref=dict(path=old['language_path'],sha256=old['language_sha256'])
        language_path=bound(language_ref)
        require(language_path.resolve().is_relative_to((OLD/'features').resolve()),'Use the original registered per-source language_path')
        language=np.load(language_path,allow_pickle=False)
        require(row['clock_ref']['sha256']==old['clock_sha256'],'Original accepted clock identity')
        clock=read(bound(row['clock_ref']))
        score=np.load(bound(row['semantic_output_ref']),allow_pickle=False)['residual']
        helper.native_fields(dict(baseline=baseline,groups=groups,semantic_score=score),clock,language)
        require(set(map(int,np.flatnonzero(baseline)))==baseline_by_sid[sid],'Accepted formal baseline exactly equals every original40.47 source frame')
        candidates=row['candidates']  # Adopt; never regenerate accepted proposals.
        x,raw,gain,stats=helper.difference_output_qa(critic,language,groups,baseline,candidates,pca,model)
        output_path=out/(sid+'_output.npz')
        with output_path.open('xb') as stream:
            np.savez(stream,difference32=x,raw_precision_difference=raw,estimated_precision_gain=gain)
        qa.append(dict(sid=sid,old_candidate_QA_ref=receipt_ref,old_native_ref=ref(native_path),old_language_ref=ref(language_path),old_clock_ref=row['clock_ref'],old_semantic_ref=row['semantic_output_ref'],new_output_ref=ref(output_path),candidates=len(candidates),anchor=stats,independent_direct_newframe_and_anchor_mean_equal=True,independent_no_bias_prediction_and_utility_equal=True,raw_outside_target_range=int(np.sum(np.abs(raw)>1))))
        options=[dict(candidate_index=i,added_frames=candidate['added_frames'],predicted_gain=float(gain[i])) for i,candidate in enumerate(candidates) if gain[i]>0]
        items.append(dict(sid=sid,baseline=baseline,candidates=candidates,options=options,anchor=stats))
        del language,x,raw,gain
    require(len(items)==426 and {v['sid'] for v in items}==set(inherited),'First new relative features/predictions cover all426 sources exactly once')
    save(out/'input_output_acceptance.json',dict(status='PASS426_FIRST_RELATIVE_ANCHOR_DIFFERENCE_FEATURE_AND_PREDICTION_QA',sources=qa,weights_ref=frozen['weights_ref'],pca_ref=frozen['pca_ref'],old_successes_reexecuted=False,new_8B_calls=0,media_decode=0,processor_calls=0,official_labels_read=False,utc=helper.utc()))
    exact=solver({v['sid']:v['options'] for v in items},len(baseline_frames)//10)
    save(out/'exact_global_selection.json',exact)
    selected=set(baseline_frames);decisions=[]
    for value in items:
        index=exact['chosen'].get(value['sid']); choice=None if index is None else value['candidates'][index]
        if choice is not None:
            selected.update((value['sid'],ordinal) for ordinal in range(choice['left'],choice['right']))
        decisions.append(dict(sid=value['sid'],candidate_index=index,chosen=choice,successful_null=not value['options'],omitted_by_budget=bool(value['options']) and choice is None,estimated_precision_gain=None if index is None else next(v['predicted_gain'] for v in value['options'] if v['candidate_index']==index)))
    additions=len(selected)-len(baseline_frames)
    require(0<additions<=len(baseline_frames)//10 and additions==exact['total_cost'],'Distinct actual unique native additions equal exact budget cost')
    rows,provenance,chosen,inputs=renderer.render(selected)
    current={(row['video_id'],prediction['frame']):prediction['bboxes'] for row in rows for prediction in row['predictions']}
    require(len(rows)==426 and len({row['video_id'] for row in rows})==426 and all(row['predictions'] for row in rows) and set(current)==selected,'Complete426 nonempty native rendering')
    require(set(baseline_frames)<=set(current) and all(current[key]==box for key,box in baseline_frames.items()),'Every original40.47 frame and bbox remains exact')
    for row in rows:row['model_params_b']=actual/1e9
    digest=canonical(rows)
    require(digest==runtime.canonical(rows),'Canonical prediction identity excludes parameter metadata')
    history=set(histories(read(bound(inputs['history']))));history.update(authoritative)
    old_history=set(read(OLD/'production_registration.json')['historical_prediction_sha256'])
    require(bool(old_history),'Adopt the complete previous production historical prediction list')
    history.update(old_history);history.add(canonical(base));history.add(read(SOURCE_CLEAR/'completion.json')['canonical_sha256'])
    risk_canonicals=[]
    for value in protected_risks:
        risk_canonicals.append(read(bound(value))['canonical_sha256'])
    history.update(risk_canonicals)
    for path in (EVENT/'packages').glob('*/completion.json'):
        history.add(read(path)['canonical_sha256'])
    require(digest not in history,'Genuinely different predictions from complete delivered/history/risk union')
    save(out/'history_acceptance.json',dict(status='PASS_DISTINCT_FROM_FULL_CANONICAL_HISTORY_UNION',canonical_sha256=digest,authoritative_inventory_ref=history_ref,authoritative_unique_count=len(authoritative),previous_production_unique_count=len(old_history),protected_risk_canonicals=risk_canonicals,full_union_count=len(history),parameter_metadata_excluded=True))
    dump(out/'predictions.jsonl',rows);dump(out/'selected.jsonl',chosen);dump(out/'provenance.jsonl',provenance)
    save(out/'metadata.json',read(bound(inputs['metadata'])))
    pending=out/'candidate_RELATIVE_PRECISION_EVENT.PENDING.zip'
    with zipfile.ZipFile(pending,'x',zipfile.ZIP_DEFLATED) as archive:
        archive.write(out/'predictions.jsonl','predictions.jsonl')
    subprocess.run([str(runtime.PY),'-B',str(runtime.RUN/'baseline_a_pts_v1/vendor/independent_validate.py'),'--strict-loader-root',str(runtime.RUN/'baseline_a_pts_v1/vendor/frozen_strict_loader'),'--metadata',str(out/'metadata.json'),'--selected',str(out/'selected.jsonl'),'--predictions',str(out/'predictions.jsonl'),'--provenance',str(out/'provenance.jsonl'),'--zip',str(pending),'--report',str(out/'independent_validation.json')],check=True)
    checks=read(out/'independent_validation.json')['checks']
    require(len(checks)==11 and all(checks.values()),'Actual independent11 strict acceptance')
    with zipfile.ZipFile(pending) as archive:
        require(archive.namelist()==['predictions.jsonl'] and archive.testzip() is None and hashlib.sha256(archive.read('predictions.jsonl')).hexdigest()==helper.sha(out/'predictions.jsonl'),'Single-member CRC and member SHA')
    # Rebind original protection evidence after production; never alter it.
    bound(base_ref)
    for value in protected_risks:bound(value)
    final=out/'candidate_RELATIVE_PRECISION_EVENT.zip'
    require(not final.exists(),'Never overwrite any completed package')
    pending.rename(final)
    save(out/'completion.json',dict(status='NEW_ENGINEERING_ACCEPTED_RELATIVE_PRECISION_EVENT_OFFICIAL_EFFECT_UNKNOWN',zip=ref(final),member_sha256=helper.sha(out/'predictions.jsonl'),canonical_sha256=digest,records=426,frames=len(current),added_frames=additions,removed_frames=0,changed_sources=len(exact['chosen']),successful_source_nulls=sum(v['successful_null'] for v in decisions),actual_added_seconds=sum(float(F(v['chosen']['added_duration_exact'])) for v in decisions if v['chosen']),actual_resident_parameters=actual,all_baseline_boxes_preserved=True,original_three_risk_packages_preserved=True,independent11strict=True,new_8B_calls=0,media_decode=0,processor_calls=0,official_labels_read=False,decisions=decisions,website_submitted=False,official_score='UNKNOWN',utc=helper.utc(),**helper.PARTIAL_DISCLOSURE))


if __name__=='__main__':
    try:
        main()
    except BaseException as error:
        save(ROOT/('production_v2_failure_'+uuid.uuid4().hex+'.json'),dict(error=repr(error),traceback=traceback.format_exc(),successes_preserved=True,no_automatic_retry=True,utc=helper.utc()))
        raise
