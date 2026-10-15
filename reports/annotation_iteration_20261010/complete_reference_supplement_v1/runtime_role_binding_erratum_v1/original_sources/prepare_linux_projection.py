"""Prepare an admitted metadata projection; never upload or start a model."""
import argparse,copy,hashlib,json,shutil,sys,zipfile
from pathlib import Path
from fractions import Fraction as F
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parent;OLD=ROOT.parent/'slot6_silver24_v1'
LINUX='/home/inspur/aic_video_work/annotation_iteration_20261010/complete_reference_supplement_v1'
RUN='/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for chunk in iter(lambda:f.read(8<<20),b''):h.update(chunk)
    return h.hexdigest()
def save(p,v):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2,default=str)
def main():
    args=argparse.ArgumentParser(description=__doc__);args.add_argument('--registry',required=True);args.add_argument('--output-dir',required=True);a=args.parse_args()
    plan=read(OLD/'source_window_plan.json');jobs={j['window']['window_id']:j for j in plan['jobs']}
    registry=read(a.registry);rows=registry.get('records',registry);assert set(rows)==set(jobs) and len(rows)==24
    sys.path.insert(0,str(OLD));from silver_contract import verify_window,training_schedule
    from quality_contract import duration
    refs={}; originals={}
    for key,row in rows.items():
        if not row.get('reference'):continue
        b=row['reference'];p=Path(b['path']);assert sha(p)==b['sha256'];r=read(p);verify_window(r,jobs[key]);refs[key]=r;originals[key]=p
    schedule=training_schedule(plan,{k:refs.get(k,dict(training_admitted=False)) for k in jobs})
    evaluation=sorted(k for k,j in jobs.items() if j['role']!='train')
    assert len(evaluation)==12 and all(k in refs for k in evaluation), 'All12 evaluation references must exist before projection'
    locked=[k for k in evaluation if jobs[k]['role']=='locked_development_evaluation'];groups={}
    for k in locked:
        r=refs[k];g=groups.setdefault(jobs[k]['source_group'],dict(keep=[],no=[],complete=0))
        g['keep']+=r['keep_global_exact'];g['no']+=r['no_global_exact'];g['complete']+=not r['unknown_global_exact'] and not r.get('consequential_unknowns')
    assert len(groups)==4 and sum(g['complete'] for g in groups.values())>=6
    assert sum(duration(g['keep'])>0 for g in groups.values())>=3
    assert all(duration(g['keep'])>0 or duration(g['no'])>=5 for g in groups.values())
    assert sum(duration(g['no'])>=5 for g in groups.values())>=2
    # Validate every training literal before any projection output is created.
    sys.path.insert(0,str(ROOT/'runtime'));from objective import target,classify
    sides={}
    for k in schedule['window_ids']:
        matches=[]
        for p in ROOT.glob('*_target_serialization.json'):
            s=read(p)
            if s['window_id']==k and s['reference_sha256']==sha(originals[k]):matches.append((p,s))
        assert len(matches)<=1
        if matches:sides[k]=matches[0]
        raw,_=target(refs[k],jobs[k]['window'],matches[0][1] if matches else None,sha(originals[k]))
        duration0=F(jobs[k]['window']['domain_end_exact'])-F(jobs[k]['window']['domain_start_exact'])
        parsed=classify(raw,duration0);assert parsed['status'] in ['MODEL_OK','LEGAL_EMPTY']
        assert [[F(str(x)) for x in p] for p in json.loads(raw)['segments']]==parsed['parsed_segments']
    out=Path(a.output_dir);out.mkdir(parents=True,exist_ok=False);bindings=[]
    def copy_bound(p,rel):
        p=Path(p);q=out/rel;q.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,q);assert sha(q)==sha(p)
        b=dict(path=LINUX+'/inputs/'+rel.replace('\\','/'),sha256=sha(q));bindings.append(dict(original_path=str(p),original_sha256=sha(p),linux_path=b['path'],linux_sha256=b['sha256'],operation='BYTE_EXACT_COPY'));return b
    config=dict(schema='COMPLETE_SILVER_NATIVE_RUNTIME_V1',historical_run_root=RUN,model_dir=RUN+'/models/Qwen3-VL-8B-Instruct',processor_dir=RUN+'/models/Qwen3-VL-8B-Instruct',initial_adapter_dir=RUN+'/temporal_sft8b_full_v1/train_01/adapter',initial_adapter_sha256='8e2cca463d8aac39f7a709bdf562373e3e47a3a8da490991c303d5e03b803b23',expected_base_sha256='74bcce81cfcb0893cf4b4c25ae36ec908d6ea669583aedd0f3940063080b8b59',seed=20261010,epochs=2,micro_batch=1,optimizer=dict(name='AdamW',lr=1e-5,betas=[.9,.999],eps=1e-8,weight_decay=0,clip_norm=1),source_files={},target_sidecars={},training_authorization=dict(unlocked=True,complete_silver_admitted=True),final_only_evaluation_window_ids=evaluation,train_output_dir=LINUX+'/train_01',evaluate_output_dir=LINUX+'/evaluate_01')
    config['candidate_output_dir']=LINUX+'/candidate_01'
    policy_source=ROOT.parents[1]/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/resource_unlimited_v1_20261007/effective_policy.json'
    config['resource_policy']=dict(path='/home/inspur/aic_video_work/resource_policy.json',sha256=sha(policy_source))
    config['gpu_ledger_path']='/home/inspur/aic_video_work/improvement_round1/gpu_ledger.jsonl'
    config['execution_python']='/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'
    config['pipeline_job_prefix']='aic_complete_silver_native_v1'
    config['candidate_contract']=copy_bound(ROOT/'candidate_contract_linux_v1.json','science/candidate_contract.json')
    for key,name in [('protocol','frozen_protocol_v2_explicit_empty_gate.json'),('plan','source_window_plan.json'),('processor_binding','actual_processor_binding.json'),('quality_contract','quality_contract.py'),('silver_contract','silver_contract.py'),('event_metrics','event_metrics.py')]:config[key]=copy_bound(OLD/name,'science/'+name)
    projected_rows=copy.deepcopy(rows)
    for k,r in refs.items():
        idx=next(i for i,j in enumerate(plan['jobs']) if j['window']['window_id']==k);projected=copy.deepcopy(r)
        original_binding=copy_bound(originals[k],'original_references/%02d.json'%idx)
        for name,b in r['evidence'].items():
            p=Path(b['path']);assert sha(p)==b['sha256'];projected['evidence'][name]=copy_bound(p,'evidence/%02d/%s.json'%(idx,name))
        without=lambda x:{name:value for name,value in x.items() if name!='evidence'}
        assert without(projected)==without(r) and all(projected['evidence'][n]['sha256']==r['evidence'][n]['sha256'] for n in r['evidence'])
        rel='references/%02d.json'%idx;p=out/rel;save(p,projected);b=dict(path=LINUX+'/inputs/'+rel,sha256=sha(p));projected_rows[k]['reference']=b
        bindings.append(dict(original_reference=original_binding,projected_reference=b,operation='ONLY_TOP_LEVEL_BOUND_EVIDENCE_PATH_PROJECTION',all_semantic_payload_exact=True,evidence_file_bytes_exact=True))
        if k in sides:
            original_side,side=sides[k];side=copy.deepcopy(side);side['reference_sha256']=b['sha256'];rel='targets/%02d.json'%idx;p=out/rel;save(p,side)
            target(projected,jobs[k]['window'],side,b['sha256']);config['target_sidecars'][k]=dict(path=LINUX+'/inputs/'+rel,sha256=sha(p))
            bindings.append(dict(original_sidecar=dict(path=str(original_side),sha256=sha(original_side)),projected_sidecar=config['target_sidecars'][k],operation='ONLY_REFERENCE_SHA_PROJECTION',all_target_literals_and_ranges_exact=True))
    rp=out/'reference_registry.json';save(rp,dict(records=projected_rows));config['reference_registry']=dict(path=LINUX+'/inputs/reference_registry.json',sha256=sha(rp))
    for source in [s for group in plan['sources'].values() for s in group]:config['source_files'][source['media_sha256']]=dict(path=LINUX+'/native_sources/'+source['source_id']+'.mp4',sha256=source['media_sha256'])
    for p in sorted((ROOT/'runtime').glob('*.py')):copy_bound(p,'runtime/'+p.name)
    save(out/'config.json',config)
    save(out/'projection_receipt.json',dict(status='PASS_LOCAL_SEMANTICALLY_EXACT_LINUX_METADATA_PROJECTION_NOT_TRANSFERRED_NOT_TRAINING',utc=datetime.now(timezone.utc).isoformat(),windows=24,train_windows=len(schedule['window_ids']),schedule=schedule,evaluation_windows=evaluation,original_registry=dict(path=str(Path(a.registry)),sha256=sha(a.registry)),bindings=bindings,source_upload_still_required=True,remote_resource_admission_required=True,new_model_calls=0,new_optimizer_updates=0))
    zp=out.with_suffix('.zip')
    with zipfile.ZipFile(zp,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for p in sorted(out.rglob('*')):
            if p.is_file():z.write(p,p.relative_to(out).as_posix())
    with zipfile.ZipFile(zp) as z:assert z.testzip() is None
    print(json.dumps(dict(path=str(zp),bytes=zp.stat().st_size,sha256=sha(zp),uploaded=False,new_optimizer_updates=0)))
if __name__=='__main__':main()
