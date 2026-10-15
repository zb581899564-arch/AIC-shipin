"""Main-run conditional HALF configuration and one binder launch; no polling."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys

R=Path('/home/inspur/aic_video_work/twenty_hour_five_20261014_v1')
P=R/'temporal_family_native_package_v3'
H=R/'temporal_family_half_package_v1'
B=R/'temporal_family_half_bootstrap_control7_v1'
W=R/'cpu_finalization_control7_03'
C=R/'temporal_global_recovery_control7_v1'
PY='/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python'
PROTOCOL=R/'boundary_residual_half_risk_v1/protocol.json'
PROTOCOL_SHA='7a6a14dbf309c19931ff7c514e865e1c2cd3929f77c560270e2ddc28bbbe5fce'
RULE_SHA='7450752081c20971616444c43c21e57d44cf09d552ef5247c9c97d9e7eb9df68'
PARAMETERS=8782459120
BINDER_CODE={
    'bind_half.py':'0906994b7722a1a16d0fe0950a21f9adca1db596c2ad2d4998397c55f8470222',
    'half_bind_contract.py':'0501b3814ebb36539c8d72993d1f42f13ee258f963bd0c6a0dc35949d17e2de2',
    'pure_recovery_metadata.py':'2d99bef2b0bd10b0de9ab130ea9ebb55eb9c21e28d2dd4a3a1dabbcfeb4254fc'}
HALF_CODE={
    'pure_geometry.py':'389ccaf8098968580198d7a515712e4810c1da202fb0967536607a089fc8cb1a',
    'package_half.py':'e6c371f3642aa37803f1b49ee905c9014beda83628eb65523acd709281fdafdc',
    'half_math.py':'10eda4740fb57a2eba1be8388968ae28f779a895327f48afce7672b5733d60c1'}


def require(ok,why):
    if not ok:raise ValueError(why)


def ref(path):
    return dict(path=str(path),sha256=hashlib.sha256(path.read_bytes()).hexdigest())


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def save(path,value):
    with path.open('x',encoding='utf8') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False)
        stream.flush();os.fsync(stream.fileno())


def contract():
    require({p.name for p in (B/'code').glob('*.py')}==set(BINDER_CODE),'Exactly the three frozen new HALF binder files required')
    for name,sha in BINDER_CODE.items():require(ref(B/'code'/name)['sha256']==sha,'Frozen HALF binder changed: '+name)
    sys.path.insert(0,str(B/'code'))
    import half_bind_contract
    require(Path(half_bind_contract.__file__).resolve()==B/'code/half_bind_contract.py','Wrong HALF metadata contract imported')
    return half_bind_contract


def original_and_production():
    require(sys.platform=='linux' and socket.gethostname()=='inspur-NP5570M5','Registered Linux host required')
    family_ref=ref(P/'completion.json');family=read(P/'completion.json')
    natural=read(W/'original/natural_terminal.json')
    require(natural['status']=='PASS_ORIGINAL_EIGHT_ARM_RENDERER_NATURAL_EXIT0' and natural['stage']=='original' and
        type(natural['exit_code']) is int and natural['exit_code']==0 and natural['naturally_completed'] is True and
        natural['process_was_killed_or_restarted'] is False and natural['completion_ref']==family_ref and
        natural['renderer_ref']==dict(path=str(P/'code/package_family.py'),sha256='9a0369a1034b96e16a570ca4864032beeb606842b1fc897e833c492094c7962e') and
        str(P/'code/package_family.py') in natural['argv'],'Original family needs its actual unchanged renderer natural exit0')
    require(not (P/'failure.json').exists(),'Actual original family failed; preserve it')
    count=family['actual_packages'];packages=family['packages']
    arms=['START','END','BOTH','VERIFY','VERIFY_BOTH','SOURCE_START','SOURCE_END','SOURCE_BOTH']
    actual_arms=[row['arm'] for row in packages]
    require(family['status']=='COMPLETE_AVAILABLE_ACTUALLY_DISTINCT_NEW_FAMILY_PACKAGES' and
        type(count) is int and count==len(packages) and 0<=count<=5 and family['required_goal_count']==5 and
        family['goal_complete_claimed'] is False and len(set(actual_arms))==count and
        all(arm in arms for arm in actual_arms) and
        [arms.index(arm) for arm in actual_arms]==sorted(arms.index(arm) for arm in actual_arms) and
        len({row['canonical_SHA256'] for row in packages})==count and
        all(row['status']=='PASS_ENGINEERING_NEW_TEMPORAL_EXPLICIT_RISK_ZIP_NOT_OFFICIAL_SCORE' and
            row['independent11strict'] is True and row['quality_pass_claimed'] is False and
            row['actual_parameters']==PARAMETERS and row['records']==426 and
            row['model_calls_in_packaging']==0 and row['website_submitted'] is False and
            all(isinstance(row[key],str) and len(row[key])==64 and set(row[key])<=set('0123456789abcdef')
                for key in ('SHA256','member_SHA256','canonical_SHA256')) for row in packages),
        'Original actual package priority/identity/risk terminal incomplete')
    if count>=5:return family,count,None,None,None
    rules=contract();require(rules.original_count(family)==count,'Frozen original family count differs')
    production_ref=ref(C/'exports_01/global_completion.json')
    production=read(C/'exports_01/global_completion.json');controller=read(C/'run_01/completion.json')
    technical=read(P/'technical_preparation_receipt.json')
    rules.production_gate(production,controller,technical,production_ref)
    require(technical['controller_completion_ref']==ref(C/'run_01/completion.json') and
        technical['package_inputs_ref']==ref(P/'package_inputs.json'),'Original actual technical inputs changed')
    for key,filename in [('old_control6_failure_ref','failure.json'),('old_control6_journal_ref','journal.jsonl')]:
        require(controller[key]==ref(R/'temporal_production_control_v6/run_01'/filename),'Original C6 failure identity changed')
    require(not (R/'temporal_production_control_v6/run_01/completion.json').exists(),'Old C6 failure cannot become completed')
    require(ref(PROTOCOL)['sha256']==PROTOCOL_SHA and ref(P/'official_rule_check.json')['sha256']==RULE_SHA,
        'Original HALF protocol/current rule leaf changed')
    rules.protocol_gate(read(PROTOCOL))
    for name,sha in HALF_CODE.items():require(ref(H/'code'/name)['sha256']==sha,'Unchanged HALF renderer/dependency required')
    require({p.name for p in (H/'code').glob('*.py')}==set(HALF_CODE),'Exactly the original HALF renderer code required')
    return family,count,production,controller,technical


def launch(stage,evidence):
    wrapper=W/'run_once_01.py';registration=read(W/'registration.json')
    require(registration['writer_ref']==ref(wrapper),'Actual frozen once-stage wrapper changed')
    require(not (W/stage).exists() and not (W/(stage+'_wrapper_launch.json')).exists() and
        not (W/(stage+'_wrapper_launch_claim.json')).exists(),'This CPU stage was already claimed or attempted')
    argv=[PY,'-B','-u',str(wrapper),'--stage',stage]
    claim=dict(status='EXCLUSIVE_ONCE_CPU_STAGE_LAUNCH_CLAIM_NO_RETRY',stage=stage,argv=argv,
        wrapper_ref=ref(wrapper),evidence_ref=evidence,utc=dt.datetime.now(dt.timezone.utc).isoformat())
    save(W/(stage+'_wrapper_launch_claim.json'),claim)
    with (W/(stage+'_wrapper.log')).open('xb') as log:
        child=subprocess.Popen(argv,cwd=R,env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'),
            stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    start_ticks=int((Path('/proc')/str(child.pid)/'stat').read_text().rsplit(')',1)[1].split()[19])
    result=dict(pid=child.pid,start_ticks=start_ticks,stage=stage,argv=argv,evidence_ref=evidence,
        launch_claim_ref=ref(W/(stage+'_wrapper_launch_claim.json')),utc=dt.datetime.now(dt.timezone.utc).isoformat())
    save(W/(stage+'_wrapper_launch.json'),result)
    print(json.dumps(result))


def main():
    family,count,production,controller,technical=original_and_production()
    if count>=5:
        print(json.dumps(dict(status='SKIP_HALF_ORIGINAL_FIVE_SUFFICIENT_NO_WRITES',actual_packages=count)))
        return
    require(not (B/'config_01.json').exists() and not (B/'refs/root_HALF_risk_authorization.json').exists(),
        'HALF configuration already attempted; preserve all partial writes')
    require(not (W/'half_binder').exists() and not (W/'half_binder_wrapper_launch.json').exists() and
        not (W/'half_binder_wrapper_launch_claim.json').exists(),'HALF binder cannot repeat')
    require(all(not (H/name).exists() for name in ('package_inputs.json','history.json','source_package_lock.json',
        'technical_preparation_receipt.json','package_admission.json','started.json','completion.json','failure.json')),
        'HALF already bound, admitted, attempted or completed')
    template=R/'temporal_family_half_bootstrap_v1/code/config_root_draft_01.json'
    require(ref(template)['sha256']=='9f4fa89313ebfc234eec98e251d01d61b788fd7c4cb5e05b8978bf846a4d7810',
        'Fixed original HALF configuration template changed')
    config=read(template)
    require(config['package_root']==str(H) and set(config['half_package_code_refs'])==set(HALF_CODE),
        'Original HALF package/code template identity changed')
    for name,sha in HALF_CODE.items():
        require(config['half_package_code_refs'][name]==dict(path=str(H/'code'/name),sha256=sha,
            bytes=(H/'code'/name).stat().st_size),'Template renderer code refs must remain exact')
    human=read(P/'authorization.json')
    require(human['new_zip_target']==5 and human['old_deliveries_count_toward_new_target'] is False and
        human['old_scientific_gates_may_be_changed'] is False and human['old_risk_failure_reruns_allowed'] is False,
        'Inherited human five-new-package authorization boundary changed')
    authorization=dict(schema='MAIN_HALF_FIXED_ALPHA_EXPLICIT_RISK_AUTHORIZATION_CONTROL7_V1',
        human_authorization_ref=ref(P/'authorization.json'),original_family_completion_ref=ref(P/'completion.json'),
        original_natural_terminal_ref=ref(W/'original/natural_terminal.json'),actual_original_packages=count,
        remaining_publication_slots=5-count,fixed_protocol_ref=ref(PROTOCOL),alpha_exact='1/2',
        physical_model_parameters=PARAMETERS,maximum_model_parameters=9000000000,model_calls=0,first_QA_calls=0,
        old_scientific_failed_gates_changed=False,old_C6_failure_not_reclassified=True,
        original_graph_or_weights_or_raw_modified=False,quality_status='UNVERIFIED_EXPLICIT_RISK',
        scientific_quality_claim=False,official_score='UNKNOWN',known_quality_PASS_claimed=False,
        no_leaderboard_or_test_GT_or_manual_test_content_used=True,peer_messages_sent=0,
        approval_is_not_official_special_permission=True,utc=dt.datetime.now(dt.timezone.utc).isoformat())
    config['schema']='TEMPORAL_FAMILY_HALF_TECHNICAL_BOOTSTRAP_CONTROL7_V1'
    config['metadata_binding_approved_by_main']=True
    config['production_completion_ref']=ref(C/'exports_01/global_completion.json')
    config['controller_completion_ref']=ref(C/'run_01/completion.json')
    for key,filename in [('original_technical_receipt_ref','technical_preparation_receipt.json'),
        ('original_inputs_ref','package_inputs.json'),('original_source_lock_ref','source_package_lock.json'),
        ('original_family_completion_ref','completion.json')]:config[key]=ref(P/filename)
    config['original_family_natural_terminal_ref']=ref(W/'original/natural_terminal.json')
    config['required_binder_code_files']={str(B/'code'/name):sha for name,sha in BINDER_CODE.items()}
    config['package_document_refs']['protocol']=ref(PROTOCOL)
    config['package_document_refs']['official_rule_check']=ref(P/'official_rule_check.json')
    require(config['create_package_admission'] is False and config['test_GT_or_manual_test_content_read'] is False,
        'Technical binder cannot create admission or inspect test contents')
    (B/'refs').mkdir(exist_ok=True)
    save(B/'refs/root_HALF_risk_authorization.json',authorization)
    config['package_document_refs']['authorization']=ref(B/'refs/root_HALF_risk_authorization.json')
    save(B/'config_01.json',config)
    launch('half_binder',ref(B/'config_01.json'))


if __name__=='__main__':main()
