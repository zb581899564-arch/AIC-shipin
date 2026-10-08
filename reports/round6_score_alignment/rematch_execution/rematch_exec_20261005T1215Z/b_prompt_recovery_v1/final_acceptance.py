"""Independent full source/response/ZIP/ledger closure, no GPU generation."""
import subprocess
import zipfile
import brec_common as c

def main():
    c.verify();rt,ex,cc,student,old,frames,production=c.helpers()
    reports={}
    for scope,count,windows in (('nontest',8,8),('rematch',426,521)):
        out=c.HERE/(scope+'_01');plan=c.read(c.HERE/'input_01'/(scope+'_plan.json'))
        ref,manifest,clocks=old.inputs(scope);temporal=old.rows(out/'temporal.jsonl')
        c.require(len(temporal)==len(plan['jobs'])==count and {x['video_id'] for x in temporal}=={x['video_id'] for x in manifest['records']} and
            sum(len(x['windows']) for x in temporal)==windows,'complete final scope identity')
        for job in plan['jobs']:
            record=next(x for x in temporal if x['video_id']==job['video_id'])
            for ix,part in enumerate(job['windows']):
                value=c.checked(c.done_path(scope,job,ix,'B1',cc),job,ix,'B1',ex)
                c.require(value['parsed_segments']==record['windows'][ix]['parsed_segments'] and value['model_identity']==
                    c.read(c.HERE/'input_01/resume_manifest.json')['model_identity'],'final raw response/model identity')
        candidate=out/'candidate_B_PROMPT_RECOVERY_8B.zip';independent=out/'final_independent_validation.json'
        subprocess.run([c.PY,'-B',str(c.RUN/'baseline_a_pts_v1/vendor/independent_validate.py'),
            '--strict-loader-root',str(c.RUN/'baseline_a_pts_v1/vendor/frozen_strict_loader'),
            '--metadata',str(out/'metadata.json'),'--selected',str(out/'selected.jsonl'),
            '--predictions',str(out/'predictions.jsonl'),'--provenance',str(out/'provenance.jsonl'),
            '--zip',str(candidate),'--report',str(independent)],check=True)
        accepted=c.read(independent);production.check_independent(accepted,scope,len(old.rows(out/'selected.jsonl')))
        c.require(accepted['zip_sha256']==c.sha(candidate) and accepted['predictions_sha256']==c.sha(out/'predictions.jsonl'),'actual final bytes differ')
        with zipfile.ZipFile(candidate) as z:
            c.require(z.namelist()==['predictions.jsonl'] and z.testzip() is None and z.read('predictions.jsonl')==(out/'predictions.jsonl').read_bytes(),'actual ZIP CRC/unique JSONL/original bytes')
        space=c.read(out/'spatial.stage.json')
        c.require(space['status']=='PASS_EMPTY_SPACE_NO_MODEL_CALL' or space.get('reused_cache') is True,'unregistered fresh spatial inference')
        reports[scope]={'records':count,'windows':windows,'all_11_checks':accepted['checks'],
            'independent_report_sha256':c.sha(independent),'candidate':str(candidate),'zip_bytes':candidate.stat().st_size,'zip_sha256':c.sha(candidate)}
    ledger=old.rows('/home/inspur/aic_video_work/improvement_round1/gpu_ledger.jsonl');resources={}
    for name in ('developer','rematch'):
        runname='aic_BREC_v1_'+name;p=c.RUN/'controller'/(runname+'.resource.json');v=c.read(p)
        c.require([r for r in ledger if r.get('name')==runname]==[v] and v['status']=='completed' and
            v['exit_code']==0 and v['stop_reason'] is None and v['charged_seconds']>0,'new GPU unique terminal receipt')
        resources[name]={'path':str(p),'sha256':c.sha(p),'charged_seconds':v['charged_seconds']}
    c.save(c.HERE/'final_acceptance.json',{'status':'PASS_INDEPENDENT_HISTORICAL_B1_FINAL',
        'utc':c.utc(),'candidate':reports['rematch']['candidate'],'zip_bytes':reports['rematch']['zip_bytes'],
        'zip_sha256':reports['rematch']['zip_sha256'],'reports':reports,'resource_receipts':resources,
        'original_costs_preserved':c.read(c.HERE/'input_01/resume_manifest.json')['resources'],
        'ledger_historical_offset':7200,'new_cpu_model_calls':0,'new_optimizer_updates':0,'new_32B_calls':0,
        'new_overview_calls':0,'new_spatial_calls':0,'production_weight':'ORIGINAL_B_8B',
        'coupled_historical_B1_prompt_and_nonempty_grammar':True,'official_score':None,
        'not_guaranteed_to_exceed_37_63':True,'source_lock_sha256':c.sha(c.HERE/'source_lock.json')})

if __name__=='__main__':main()
