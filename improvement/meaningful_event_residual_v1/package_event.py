"""Apply an admitted frozen mechanism and package with the original source field."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
os.environ.setdefault('OPENBLAS_NUM_THREADS','2')
import sys
from pathlib import Path
ROOT=Path('/home/inspur/aic_video_work/meaningful_residual_20261018_v1')
sys.path.insert(0,str(ROOT/'code_v1'))
from event_runtime import *
import zipfile,subprocess


def dump(path,rows):
    with Path(path).open('x',encoding='utf8')as f:
        for row in rows:f.write(json.dumps(clean(row),ensure_ascii=False,separators=(',',':'),allow_nan=False)+'\n')


def histories(value):
    if isinstance(value,dict):
        for k,v in value.items():
            if k in ('canonical_sha256','canonical_SHA256','prediction_sha256','canonical_prediction_sha256')and isinstance(v,str):yield v
            else:yield from histories(v)
    elif isinstance(value,list):
        for v in value:yield from histories(v)


def mechanism(name):
    if name=='EVENT_VISUAL_QUALITY':
        selection=ROOT/'frozen_selection.json';predictor='ridge';evaluation=ROOT/'external_evaluation.json'
    elif name=='EVENT_REFERENCE_MEMORY':
        selection=ROOT/'event_memory_01/frozen_selection.json';predictor='memory';evaluation=ROOT/'event_memory_01/external_evaluation.json'
    elif name=='EVENT_AUDIO_VISUAL':
        selection=ROOT/'event_audio_01/frozen_selection.json';predictor='audio';evaluation=ROOT/'event_audio_01/external_evaluation.json'
    elif name=='SEMANTIC_EVENT_RANK':
        selection=ROOT/'semantic_event_01/frozen_selection.json';predictor='semantic';evaluation=ROOT/'semantic_event_01/adopted_evaluation.json'
    else:raise ValueError('Unregistered event mechanism')
    frozen=read(selection);model=dict(np.load(bound(frozen['weights_ref'])))
    return model,predictor,selection,evaluation


def main(name):
    cpu();admission=read(ROOT/'production_admission.json')
    require(name in admission['mechanisms'],'Explicit mechanism admission before formal read')
    accepted=read(ROOT/'formal_inputs_01/completion.json')
    require(accepted['status']=='PASS426_FIRST_NATIVE_EVENT_DESCRIPTOR_QA','All426 first new descriptor QA before inference')
    model,predictor,selection,evaluation=mechanism(name)
    bound(accepted['pca_selection_ref']);pca=dict(np.load(bound(accepted['pca_weights_ref'])))
    require(all(np.array_equal(model[k],pca[k])for k in ['pca_mean','pca_components']),'Actual frozen production/model PCA identity')
    if predictor=='memory':
        sys.path.insert(0,str(ROOT/'memory_code_v1'));from event_memory import predict as memory_predict
    if predictor=='audio':
        audio_qa=read(ROOT/'formal_audio_01/completion.json')
        require(audio_qa['status']=='PASS426_FIRST_AUDIO_PROPOSAL_INPUT_QA','First audio-specific formal inputs must all pass')
        audio_receipts={read(bound(v))['sid']:v for v in audio_qa['sources']}
        require(set(audio_receipts)=={str(i)for i in range(426)},'All426 audio receipts explicitly bound')
    renderer,_=old_modules();base_ref=read(ROOT/'registration.json')['baseline_ref']
    with zipfile.ZipFile(bound(base_ref))as z:base=[json.loads(x)for x in z.read('predictions.jsonl').splitlines()]
    baseline={(r['video_id'],p['frame']):p['bboxes']for r in base for p in r['predictions']}
    selected=set(baseline);items=[];out=ROOT/'packages'/name;out.mkdir(parents=True)
    actual=8782459120+98329+sum(v.size for v in model.values())
    require(actual<=9_000_000_000,'All frozen backbone/TIME/semantic/new mechanism tensors<=9B')
    for receipt in accepted['sources']:
        r=read(bound(receipt));sid=r['sid'];d=np.load(bound(r['input_ref']));x=d['x'];c=r['candidates'];b=d['baseline']
        if predictor=='memory':q=memory_predict(x,model)
        elif predictor=='semantic':q=x[:,96]
        else:
            if predictor=='audio':
                a=read(bound(audio_receipts[sid]));ax=np.load(bound(a['input_ref']))['x']
                require(a['sid']==sid and a['visual_receipt_ref']==receipt and a['clock_ref']==r['clock_ref'],'Audio sid/native clock/visual candidate order must be exactly bound')
                bound(a['visual_receipt_ref']);bound(a['clock_ref'])
                require(ax.shape==(len(x),8),'First audio descriptors aligned with visual candidates')
                x=np.concatenate([x,ax],1)
            q=np.clip(((x-model['mean'])/model['std'])@model['coef']+float(model['bias']),-.5,1.)
        require(np.isfinite(q).all(),'Finite formal quality, failure never becomes null')
        k=np.asarray([p['added_frames']for p in c],float)
        if predictor=='semantic':
            gain=1/(1+np.exp(-np.clip(q,-30,30)))
            idx=None if not len(q)else int(np.argmax(q))
        else:
            gain=2*k*q/(b.sum()+k+len(b)*float(model['rho_train']))
            idx=None if len(gain)==0 or gain.max()<=0 else int(gain.argmax())
        action=None if idx is None else dict(sid=sid,candidate_index=idx,added_frames=c[idx]['added_frames'],predicted_gain=float(gain[idx]))
        items.append(dict(sid=sid,c=c,q=q,gain=gain,action=action))
        np.savez(out/(sid+'_output.npz'),predicted_quality=q,estimated_gain=gain)
    require(len(items)==426,'Complete426 formal model input denominator')
    chosen_ids=knapsack([v['action']for v in items if v['action']],len(baseline)//10)
    decisions=[]
    for v in items:
        sid=v['sid'];idx=None;spec=None
        if sid in chosen_ids:
            idx=v['action']['candidate_index'];spec=v['c'][idx]
            selected.update((sid,i)for i in range(spec['left'],spec['right']))
        decisions.append(dict(sid=sid,chosen=spec,predicted_quality=None if idx is None else float(v['q'][idx]),predicted_gain=None if idx is None else float(v['gain'][idx])))
    require(0<len(selected)-len(baseline)<=len(baseline)//10,'Real new native-frame difference within frozen exposure budget')
    save(out/'inference_completion.json',dict(status='PASS426_FROZEN_CPU_EVENT_INFERENCE',selection_ref=ref(selection),mechanism=name,decisions=decisions,added_frames=len(selected)-len(baseline),changed_sources=len(chosen_ids),actual_resident_parameters=actual,new_8B_calls=0))
    rows,provenance,chosen,inputs=renderer.render(selected)
    current={(r['video_id'],p['frame']):p['bboxes']for r in rows for p in r['predictions']}
    require(len(rows)==426 and all(r['predictions']for r in rows)and set(current)==selected,'Complete426/nonempty/native unique set')
    require(set(baseline)<=set(current)and all(current[k]==v for k,v in baseline.items()),'Original40.47allframes and every bbox must remain exact')
    for r in rows:r['model_params_b']=actual/1e9
    canonical_sha=canonical(rows)
    history=set(histories(read(bound(inputs['history']))));history.update(read(OLD/'production_registration.json')['historical_prediction_sha256']);history.add(canonical(base));history.add(read(SRC/'completion.json')['canonical_sha256'])
    history.update(histories(read(bound(admission['current_delivered_history_ref']))))
    for prior in (ROOT/'packages').glob('*/completion.json'):history.add(read(prior)['canonical_sha256'])
    require(canonical_sha not in history,'Not a renamed old or same-round prediction')
    rule=read(ROOT/'official_primary_02/receipt.json')
    require(rule['new_attachment_bytes_identical_to_full_read'],'Current official attachment scope bound')
    dump(out/'predictions.jsonl',rows);dump(out/'selected.jsonl',chosen);dump(out/'provenance.jsonl',provenance);save(out/'metadata.json',read(bound(inputs['metadata'])))
    pending=out/('candidate_'+name+'.PENDING.zip')
    with zipfile.ZipFile(pending,'x',zipfile.ZIP_DEFLATED)as z:z.write(out/'predictions.jsonl','predictions.jsonl')
    subprocess.run([str(PY),'-B',str(RUN/'baseline_a_pts_v1/vendor/independent_validate.py'),'--strict-loader-root',str(RUN/'baseline_a_pts_v1/vendor/frozen_strict_loader'),'--metadata',str(out/'metadata.json'),'--selected',str(out/'selected.jsonl'),'--predictions',str(out/'predictions.jsonl'),'--provenance',str(out/'provenance.jsonl'),'--zip',str(pending),'--report',str(out/'independent_validation.json')],check=True)
    checks=read(out/'independent_validation.json')['checks'];require(len(checks)==11 and all(checks.values()),'Independent11strict')
    with zipfile.ZipFile(pending)as z:require(z.namelist()==['predictions.jsonl']and z.testzip()is None and hashlib.sha256(z.read('predictions.jsonl')).hexdigest()==sha(out/'predictions.jsonl'),'ZIP/CRC/memberSHA')
    final=out/('candidate_'+name+'.zip');pending.rename(final)
    completion=dict(status='NEW_ENGINEERING_ACCEPTED_EVENT_CANDIDATE_OFFICIAL_EFFECT_UNKNOWN',mechanism=name,zip=ref(final),member_sha256=sha(out/'predictions.jsonl'),canonical_sha256=canonical_sha,records=426,frames=len(current),added_frames=len(current)-len(baseline),removed_frames=0,changed_sources=len(chosen_ids),actual_added_seconds=sum(float(F(v['chosen']['added_duration_exact']))for v in decisions if v['chosen']),all_baseline_boxes_preserved=True,actual_resident_parameters=actual,independent11strict=True,selection_ref=ref(selection),evaluation_ref=ref(evaluation),risk_level=admission['mechanisms'][name],official_score='UNKNOWN',website_submitted=False,utc=utc())
    save(out/'completion.json',completion);event('EVENT_PACKAGE_READY',mechanism=name,zip=completion['zip'],added_frames=completion['added_frames'])


if __name__=='__main__':
    try:main(sys.argv[1])
    except BaseException as e:failure('package_event_'+sys.argv[1],e);raise
