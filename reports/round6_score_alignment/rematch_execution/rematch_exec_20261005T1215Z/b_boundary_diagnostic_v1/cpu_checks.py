"""Actual frozen C terminal replay plus new B CPU interfaces, never inference."""
from collections import Counter
import json
from pathlib import Path
import subprocess
import bdiag_common as c
import bdiag_engine as engine


def main():
    cad,ex,student,old,teacher,boundary=c.helpers()
    c.require(Path(old.__file__).resolve()!=Path(c.__file__).resolve() and hasattr(old,'rows'), 'real original production helper must not bind diagnostic common module')
    frozen=ex.verify()
    reporter=c.load(c.CAD/'report.py','bdiag_original_full_report')
    plan,out,rows=reporter.records('full')
    c.require(rows==c.read(out/'full.mechanism_rows.json'),'complete104 original raw/validator/native selection replay')
    report=c.read(out/'full.report.json')
    subset=[r for r in rows if r['source_group'] not in set(plan['pilot_source_groups'])]
    f=lambda r,a:r['arms'][a]['closed_world_teacher_set_agreement']['f1']
    comparisons={}
    for name,part in [('all104',rows),('new72_source_groups',subset)]:
        comparisons[name]={'records':len(part),'source_groups':len({r['source_group'] for r in part})}
        for arm in ('B0','N','X'):
            comparisons[name]['R_minus_'+arm]=reporter.bootstrap_video_macro([f(r,'R')-f(r,arm) for r in part],part)
    c.require(comparisons==report['comparisons'],'all104/new72 original bootstrap and point estimator')
    groups={r['source_group'] for r in rows}
    import statistics
    down=sum(statistics.mean(f(r,'R')-f(r,'B0') for r in rows if r['source_group']==g)<0 for g in groups)
    identical=all(r['native_selected_sets_R_N_equal'] for r in rows)
    decision=reporter.investment_decision(identical,comparisons['all104']['R_minus_B0']['mean'],down/len(groups),
        [comparisons[k]['R_minus_'+a]['mean'] for k in comparisons for a in ('B0','N')])
    c.require(decision==(False,False,False) and report['status']=='STOP_C_PRODUCTION_INVESTMENT','original C STOP must stay STOP')
    terminal=c.read(c.CAD/'developer_01/full.completion.json')
    c.require(terminal['records']==104 and terminal['fresh_local_calls']==344 and terminal['reused_local_calls']==104
        and terminal['fresh_overview_calls']==80 and terminal['reused_overview_calls']==24,'complete full actual counts')
    resource=c.read(c.RUN/'controller/aic_CAD_v1_full.resource.json')
    ledger=old.rows('/home/inspur/aic_video_work/improvement_round1/gpu_ledger.jsonl')
    c.require([r for r in ledger if r.get('name')=='aic_CAD_v1_full']==[resource] and resource['status']=='completed'
        and resource['exit_code']==0 and resource['stop_reason'] is None and resource['charged_seconds']>0,'original unique full GPU terminal charge')
    new=c.read(c.HERE/'input_01/plan.json')
    c.require(len(new['events'])==16 and len({x['source_group'] for x in new['events']})==16,'new fixed16 source groups')
    admission=c.read(c.HERE/'input_01/teacher_recipe.json');admission['job_source_lock_sha256']='0'*64
    teacher.validate_admission(admission,teacher.validator_for(c.HERE))
    cpu=c.HERE/'cpu_01';cpu.mkdir()
    proofs=[];cases=0
    first=new['events'][0]
    for variant in first['variants']:
        folder=cpu/variant['name'];folder.mkdir()
        observation=engine.observe(variant['window'],folder,student)
        c.require(observation['source_full_decode_performed'] is False and observation['source_sequential_decode_through_last_sample'] is True,
            'sequential prefix decode must not claim full-source decode')
        prompt=c.diagnostic_prompt(observation,first['raw_source_event_seconds'],teacher,boundary)
        content=teacher.frame_content(observation,namespaced=True)
        c.require(len(content)==2*len(observation['actual_pts_sec']),'all ordered actual64 HTTP frame construction')
        table=boundary.tables(observation);last=len(table['boundary_ids'])-1
        whole={'start_boundary_id':'B0','end_boundary_id':'B'+str(last),'evidence_frame_ids':['F0']}
        valid={'state':'KEEP','segments':[whole],'evidence_frame_ids':[],'reason':'CPU_FORMAT_ONLY_NOT_LABEL'}
        unknown={'state':'UNKNOWN','segments':[],'evidence_frame_ids':['F0'],'reason':'CPU_FORMAT_ONLY_NOT_LABEL'}
        no=dict(unknown,state='NO_HIGHLIGHT')
        c.require(c.matched_projection(valid,observation,first['raw_source_event_seconds'],boundary)['status']=='WEAK_UNIQUE_OVERLAPPING_CANDIDATE','unique candidate mapping')
        for value in (unknown,no):
            r=c.matched_projection(value,observation,first['raw_source_event_seconds'],boundary)
            c.require(r['status']=='UNKNOWN_UNCONFIRMED_CANDIDATE' and r['candidate_boundary_seconds'] is None,'NO/UNKNOWN not negative or fabricated boundaries')
        grammar=boundary.ordered_grammar(observation)
        examples=[{'text':json.dumps(v),'expected':True} for v in (valid,unknown,no)]
        bad=[{},dict(valid,segments=[]),dict(valid,segments=[whole,whole]),dict(valid,segments=[dict(whole,evidence_frame_ids=[])]),
            dict(valid,segments=[dict(whole,start_boundary_id='B'+str(last),end_boundary_id='B0')]),dict(unknown,evidence_frame_ids=['B0'])]
        examples += [{'text':json.dumps(v),'expected':False} for v in bad]
        result=subprocess.run([str(Path(teacher.HERE)/'runtime_schema_check')],input=json.dumps({'grammar':grammar,'root':'root','examples':examples}),
            capture_output=True,text=True,timeout=90)
        c.require(result.returncode==0 and json.loads(result.stdout)['all_examples_match_expectations'],'actual pinned runtime grammar CPU regression')
        cases+=len(examples)
        c.save(folder/'HTTP_construct.json',{'prompt':prompt,'content':content,'grammar':grammar})
        proofs.append({'variant':variant['name'],'frames':len(observation['actual_pts_sec']),
            'actual_native_source_decode_and_lossless_HTTP_construction':True,'prompt_sha256':teacher.text_sha(prompt),
            'observation_sha256':c.sha(folder/'decode_receipt.json'),'runtime_grammar_cases':len(examples)})
    for event in new['events']:
        for variant in event['variants']:
            w=variant['window'];ids=w['planned_source_frame_ordinals'];pts=w['planned_actual_pts_sec']
            c.require(len(ids)==len(pts) and ids==student.floor_indices(ids[0],ids[-1]+1), 'exact floor64 ordinal endpoints')
            c.require(all(w['window_pts_start_sec']<=p<w['window_pts_end_exclusive_sec'] for p in pts),'native points inside exact half-open window')
    result={'status':'PASS_EXACT_C_STOP_AND_B_MATCHED_NATIVE_CPU_INTERFACES','utc':c.utc(),
        'C_full_original_frozen_files':len(frozen['files']),'C_full_source_files':104,'C_full_groups':96,
        'C_original_local_windows':112,'C_full_actual_GPU_charge_seconds':resource['charged_seconds'],
        'C_all_raw_validator_native_rows_and_frozen_rule_equal':True,'C_report_sha256':c.sha(out/'full.report.json'),
        'C_original_STOP_preserved':True,'fixed_B_events':16,'fixed_context_variants':new['variant_denominator'],
        'real_first_event_CPU_proofs':proofs,'actual_pinned_runtime_grammar_cases':cases,
        'new_32B_calls':0,'new_8B_calls':0,'optimizer_updates':0,'training_admitted':False}
    c.save(c.HERE/'cpu_acceptance.json',result)
    print(json.dumps(result),flush=True)


if __name__=='__main__':main()
