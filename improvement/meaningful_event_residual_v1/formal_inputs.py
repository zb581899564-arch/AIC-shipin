"""New event descriptors from already accepted formal features, exactly once."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
os.environ.setdefault('OPENBLAS_NUM_THREADS','2')
import sys
from pathlib import Path
ROOT=Path('/home/inspur/aic_video_work/meaningful_residual_20261018_v1')
sys.path.insert(0,str(ROOT/'code_v1'))
from event_runtime import *
import zipfile


def main():
    cpu()
    admission=read(ROOT/'production_admission.json')
    require(admission['allow_formal_first_descriptor_QA'],'Explicit frozen method admission needed')
    renderer,_=old_modules()
    require(read(SRC/'renderer_feasibility.json')['status']=='PASS_ZERO_OVERLAY_EXACT40_47_IN_MEMORY_NO_DUPLICATE_ZIP','Adopt already proven zero-overlay renderer')
    reg=read(ROOT/'registration.json')
    with zipfile.ZipFile(bound(reg['baseline_ref']))as z:base=[json.loads(x)for x in z.read('predictions.jsonl').splitlines()]
    baselines={r['video_id']:[p['frame']for p in r['predictions']]for r in base}
    inp=read(W/'twenty_hour_five_20261014_v1/temporal_family_native_package_v3/package_inputs.json')
    field={}
    for v in renderer.lines(bound(inp['source_field_files']['field_frames.jsonl'])):field.setdefault(v['video_id'],set()).add(v['source_frame'])
    pca_selection_ref=ref(ROOT/'frozen_selection.json')
    pca_weights_ref=read(ROOT/'frozen_selection.json')['weights_ref']
    pca=dict(np.load(bound(pca_weights_ref)))
    complete=read(OLD/'feature_completion.json')
    folder=ROOT/'formal_inputs_01';folder.mkdir()
    save(folder/'start.json',dict(admission_ref=ref(ROOT/'production_admission.json'),feature_completion_ref=ref(OLD/'feature_completion.json'),adopted_renderer_ref=ref(SRC/'renderer_feasibility.json'),pca_selection_ref=pca_selection_ref,pca_weights_ref=pca_weights_ref,utc=utc()))
    receipts=[]
    for s in complete['sources']:
        sid=s['id'];native=OLD/'inputs'/sid/'native.npz';clockpath=OLD/'inputs'/sid/'clock.json';lp=OLD/'features'/sid/'language.npy'
        require(sha(native)==s['native_sha256'] and sha(clockpath)==s['clock_sha256'] and sha(lp)==s['language_sha256'],'Inherited full feature/native/clock identities')
        n=np.load(native);clock=read(clockpath);language=np.load(lp);groups=n['groups'];b=np.zeros(len(groups),bool);b[baselines[sid]]=True
        inside=np.zeros(len(b),bool);inside[list(field[sid])]=True
        score_acceptance=read(OLD/'head_outputs'/sid/'acceptance.json')
        score_path=OLD/'head_outputs'/sid/'output.npz'
        require(score_acceptance['id']==sid and score_acceptance['independent_direct_native_equal'] and sha(score_path)==score_acceptance['sha256'],'Adopt accepted frozen semantic output; no repeat old head inference')
        score=np.load(score_path)['residual']
        rederived=n['baseline']|(score[groups]>1.)
        require(np.array_equal(rederived&inside,b),'Winning semantic decision exactly reproduces original baseline')
        bins=np.asarray([int(F(x)*2)for x in clock['normalized_exact_pts']],np.int64)
        require(np.array_equal(np.unique(bins,return_inverse=True)[1],groups),'Actual occupied native time groups')
        d=dict(sid=sid,clock=clock,baseline=b,groups=groups,language=language,score=score)
        c=proposals(clock,b,inside);x=descriptors(language,score,groups,clock,b,pca,c);audit=descriptor_qa(d,c,x,pca)
        require(all(all(inside[i]for i in range(v['left'],v['right'])if not b[i])for v in c),'Whole added native proposal has accepted spatial field')
        np.savez(folder/(sid+'.npz'),x=x,baseline=b)
        save(folder/(sid+'.json'),dict(sid=sid,candidates=c,input_ref=ref(folder/(sid+'.npz')),clock_ref=ref(clockpath),feature_ref=dict(path=str(lp),sha256=s['language_sha256']),semantic_acceptance_ref=ref(OLD/'head_outputs'/sid/'acceptance.json'),semantic_output_ref=dict(path=str(score_path),sha256=score_acceptance['sha256']),descriptor_QA=audit,no_formal_labels=True))
        receipts.append(ref(folder/(sid+'.json')))
        event('FORMAL_EVENT_DESCRIPTOR_FIRST_QA',sid=sid,candidates=len(c))
    require(len(receipts)==426 and set(baselines)=={str(i)for i in range(426)},'Complete426 new descriptor denominator')
    save(folder/'completion.json',dict(status='PASS426_FIRST_NATIVE_EVENT_DESCRIPTOR_QA',sources=receipts,baseline_ref=reg['baseline_ref'],admission_ref=ref(ROOT/'production_admission.json'),pca_selection_ref=pca_selection_ref,pca_weights_ref=pca_weights_ref,code_ref=ref(Path(__file__)),new_8B_calls=0,new_media_or_processor=0,utc=utc()))


if __name__=='__main__':
    try:main()
    except BaseException as e:failure('formal_first_descriptors',e);raise
