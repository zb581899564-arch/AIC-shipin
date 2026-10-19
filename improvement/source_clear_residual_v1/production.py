"""One CPU-only application to adopted formal BASE features, one novel ZIP."""
from sr_common import *
from render import render,lines
from fit import candidates,predict
import zipfile
import subprocess

def dump_lines(path,rows):
    with Path(path).open('x',encoding='utf8')as f:
        for r in rows:f.write(json.dumps(clean(r),ensure_ascii=False,separators=(',',':'),allow_nan=False)+'\n')

def main():
    cpu();import numpy as np
    import torch
    torch.set_num_threads(2)
    reg=read(ROOT/'registration.json');selection=read(ROOT/'frozen_selection.json');comparison=read(ROOT/'external_comparison.json')
    require(read(ROOT/'targeted_checks.json')['status']=='PASS_TARGETED_NEW_UTILITY_AND_BASELINE_REGRESSIONS','New logic checks')
    require(read(ROOT/'renderer_feasibility.json')['status']=='PASS_ZERO_OVERLAY_EXACT40_47_IN_MEMORY_NO_DUPLICATE_ZIP','40.47 zero-overlay reproduction required')
    # This narrow check detects wholly failed additional selections across all
    # reviewers; it is not the old generic proxy-F1 gate or a tunable cutoff.
    check=[x for x in comparison['sources']if x['group']=='check'and x['added_frames']>0]
    require(not(len(check)>=3 and all(x['actual_added_rater_precision']==0 for x in check)),'Every new check selection misses all original reviewers; no package')
    model=dict(np.load(bound(selection['weights_ref'])))
    require(sum(v.size for v in model.values())==37,'All learned normalization and coefficient scalars counted')
    actual=8782459120+98329+sum(v.size for v in model.values());require(actual<=9_000_000_000,'All physical main/auxiliary tensors <=9B')
    with zipfile.ZipFile(bound(reg['baseline']))as z:base=[json.loads(x)for x in z.read('predictions.jsonl').splitlines()]
    baseline={(r['video_id'],p['frame']):p['bboxes']for r in base for p in r['predictions']};selected=set(baseline)
    inp=read(W/'twenty_hour_five_20261014_v1/temporal_family_native_package_v3/package_inputs.json')
    field_domain={}
    for row in lines(bound(inp['source_field_files']['field_frames.jsonl'])):field_domain.setdefault(row['video_id'],set()).add(row['source_frame'])
    sources=[];added_sets=[];out=ROOT/'production';out.mkdir(exist_ok=False)
    complete=read(OLD/'feature_completion.json');require(len(complete['sources'])==426,'Adopt all426 existing accepted features')
    for s in complete['sources']:
        sid=s['id'];n=np.load(OLD/'inputs'/sid/'native.npz');groups=n['groups'];language=np.load(OLD/'features'/sid/'language.npy');yn=OLD/'features'/sid/'yes_no.npy'
        require(sha(OLD/'features'/sid/'language.npy')==s['language_sha256']and sha(yn)==s['yes_no_sha256'],'Frozen formal feature identity')
        require(sha(OLD/'inputs'/sid/'native.npz')==s['native_sha256'],'Inherited original formal native mapping identity')
        b=np.zeros(len(groups),bool);old_selected=[frame for video,frame in baseline if video==sid];b[old_selected]=True
        hidden,score,rederived=semantic(language,n['baseline'],groups)
        field=field_domain[sid];inside=np.zeros(len(groups),bool);inside[list(field)]=True
        require(np.array_equal(rederived&inside,b),'Actual frozen full40.47 semantic policy does not reproduce baseline')
        saved=np.load(OLD/'head_outputs'/sid/'output.npz')
        require(np.array_equal(saved['residual'],score),'New hidden readout must match adopted old score exactly')
        x,eligible=candidates(hidden,score,b,groups)
        # Eligibility is fixed source-field availability, never reference labels.
        valid_counts=np.bincount(groups,weights=(~b & inside),minlength=len(hidden));all_counts=np.bincount(groups,weights=~b,minlength=len(hidden))
        eligible &= valid_counts==all_counts
        chosen,utility=predict(x,eligible,model);addition=np.zeros(len(b),bool)
        if chosen is not None:addition=(groups==chosen)&~b
        keys={(sid,int(i))for i in np.flatnonzero(addition)};require(all(frame in field for _,frame in keys),'No unknown spatial field extrapolation')
        selected.update(keys);added_sets.extend(keys)
        record=dict(sid=sid,chosen_cell=chosen,added_frames=len(keys),predicted_delta=None if chosen is None else float(utility[chosen]),native_cells=len(hidden))
        sources.append(record)
        np.savez(out/(sid+'_output.npz'),added_native=addition,utility=utility,chosen_cell=-1 if chosen is None else chosen)
    require(len(sources)==426 and {s['sid']for s in sources}=={str(i)for i in range(426)},'Complete426 prediction denominator')
    require(added_sets,'No actual new selected native frames; do not rename old ZIP')
    save(out/'head_completion.json',dict(status='PASS_ONE_FROZEN_CPU_UTILITY_ALL426',sources=sources,added_frames=len(added_sets),actual_resident_parameters=actual,new426_model_calls=0,weights_ref=selection['weights_ref']))
    rows,provenance,chosen,inputs=render(selected)
    current={(r['video_id'],p['frame']):p['bboxes']for r in rows for p in r['predictions']}
    require(set(current)==selected and set(baseline)<=set(current)and all(current[k]==v for k,v in baseline.items()),'All40.47 frames and original boxes must remain exactly')
    for r in rows:r['model_params_b']=actual/1e9
    semantic_sha=canonical(rows);history=read(inputs['history']['path'])
    def collect(v):
        if isinstance(v,dict):
            for k,x in v.items():
                if k in ('canonical_sha256','prediction_sha256','canonical_prediction_sha256')and isinstance(x,str):yield x
                else:yield from collect(x)
        elif isinstance(v,list):
            for x in v:yield from collect(x)
    history_sha=set(collect(history));history_sha.add(canonical(base));history_sha.update(read(OLD/'production_registration.json')['historical_prediction_sha256'])
    require(semantic_sha not in history_sha,'Actual prediction matches a historical package')
    require(read(ROOT/'official_rule_check_before_package.json')['approved_automatic_external_trained_head_scope'],'Current official rule check required')
    dump_lines(out/'predictions.jsonl',rows);dump_lines(out/'selected.jsonl',chosen);dump_lines(out/'provenance.jsonl',provenance)
    save(out/'metadata.json',read(bound(inputs['metadata'])))
    pending=out/'candidate_SOURCE_CLEAR_INCREMENTAL_UTILITY.PENDING.zip'
    with zipfile.ZipFile(pending,'x',zipfile.ZIP_DEFLATED)as z:z.write(out/'predictions.jsonl','predictions.jsonl')
    subprocess.run([str(PY),str(RUN/'baseline_a_pts_v1/vendor/independent_validate.py'),'--strict-loader-root',str(RUN/'baseline_a_pts_v1/vendor/frozen_strict_loader'),'--metadata',str(out/'metadata.json'),'--selected',str(out/'selected.jsonl'),'--predictions',str(out/'predictions.jsonl'),'--provenance',str(out/'provenance.jsonl'),'--zip',str(pending),'--report',str(out/'independent_validation.json')],check=True)
    validation=read(out/'independent_validation.json');require(len(validation['checks'])==11 and all(validation['checks'].values()),'Independent11strict must pass')
    with zipfile.ZipFile(pending)as z:
        require(z.namelist()==['predictions.jsonl']and z.testzip()is None and hashlib.sha256(z.read('predictions.jsonl')).hexdigest()==sha(out/'predictions.jsonl'),'ZIP single-member/CRC/SHA')
    final=out/'candidate_SOURCE_CLEAR_INCREMENTAL_UTILITY.zip';pending.rename(final)
    completion=dict(status='ONE_NEW_ENGINEERING_ACCEPTED_ZIP_OFFICIAL_EFFECT_UNKNOWN',zip=ref(final),member_sha256=sha(out/'predictions.jsonl'),canonical_sha256=semantic_sha,records=426,frames=len(current),added_frames=len(added_sets),removed_frames=0,changed_sources=sum(s['added_frames']>0 for s in sources),all_baseline_boxes_preserved=True,actual_resident_parameters=actual,independent11strict=True,external_summary=comparison['summary'],official_score='UNKNOWN',website_submitted=False,utc=utc())
    save(ROOT/'completion.json',completion);event('NEW_FINAL_ZIP_READY',**completion)

if __name__=='__main__':
    try:main()
    except BaseException as e:failure('production',e);raise
