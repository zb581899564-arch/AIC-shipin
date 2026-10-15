"""Explicit CPU-only finalization; no model, media, or metric-based risk screening."""
from pathlib import Path
import argparse,datetime as dt,hashlib,json,os,socket,subprocess,sys,time,traceback

HOME=Path('/home/inspur/aic_video_work')
ROOT=HOME/'midnight_five_verify40_46_20261015_v1'
OLD=HOME/'twenty_hour_five_20261014_v1/temporal_family_native_package_v3'
RUN=HOME/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
PRODUCTION=ROOT/'production_unique_09'
PY=HOME/'env/qwen3vl_isolated_20260910/bin/python'
PARAMETERS=8782459120
BASELINE_SHA='86593725c6bad919dc0d342fe98ad65e489a13a6e492da5de3afd247a3226543'

def require(x,m):
    if not x:raise ValueError(m)
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return dict(path=str(Path(p).resolve()),sha256=sha(p))
def checked(r):
    p=Path(r['path']);require(p.resolve().is_relative_to(HOME) and sha(p)==r['sha256'],'Actual reference/path differs');return p
def utc():return dt.datetime.now(dt.timezone.utc).isoformat()
def save(p,d):
    with Path(p).open('x',encoding='utf8') as f:json.dump(d,f,ensure_ascii=False,indent=2,allow_nan=False)
def setup():
    require(socket.gethostname()=='inspur-NP5570M5' and os.environ.get('CUDA_VISIBLE_DEVICES')=='','Linux CPU-only finalization required')
    deployment=read(ROOT/'finalization_deployment_15.json')
    for path,digest in deployment['code_files'].items():require(sha(path)==digest,'Frozen finalization source changed')
    package_deployment=read(ROOT/'package_release_deployment_13.json')
    for path,digest in package_deployment['code_files'].items():require(sha(path)==digest,'Frozen package source changed')
    return package_deployment

def initialize_engineering():
    deployment=setup();completed=read(PRODUCTION/'completion.json')
    require(read(PRODUCTION/'chain_completion.json')['status']=='NATURAL_COMPLETE_NEW_STAGE','Natural parent completion required')
    require(completed['status']=='COMPLETE_NEW_FIVE_WAY_INFERENCE_ENGINEERING_NOT_QUALITY' and completed['actual_parameters']==PARAMETERS,'Actual complete production required')
    terminal=read(checked(completed['unique_gpu_terminal_ref']))
    ledger=[json.loads(s) for s in (HOME/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if s.strip()]
    require(terminal['status']=='completed' and terminal['exit_code']==0 and [v for v in ledger if v['name']==terminal['name']]==[terminal],'Unique completed/exit0 actual ledger required')
    sys.path.insert(0,str(ROOT/'package_code_v2'))
    from production_evidence import validate_production_evidence
    _,counts=validate_production_evidence(completed,lambda r:read(checked(r)),PARAMETERS)
    require(counts==dict(logical_cases=519,actual_model_calls=518,adopted_identical_input_aliases=1,first_model_output_QA_count=518,alias_application_QA_count=1),'Actual production and QA denominators differ')
    baseline=OLD/'package_VERIFY/candidate_TEMPORAL_VERIFY.zip'
    require(baseline.stat().st_size==380199 and sha(baseline)==BASELINE_SHA,'Protected original 40.46 archive changed')
    history=read(checked(deployment['history_ref']))
    require(len(history['records'])==21 and history['only_duplicate_prevention_not_quality_evaluation'] is True,'Complete actual historical delivery identities required')
    permit=dict(status='PASS_NEW_FIVE_WAY_CPU_PACKAGE_ENGINEERING_ADMISSION',actual_parameters=PARAMETERS,
        production_completion_sha256=sha(PRODUCTION/'completion.json'),automatic_removal_and_recall_authorized=True,
        three_risk_arms_without_offline_quality_screening=True,test_labels_or_manual_edits_used=False,
        current_official_rules_rechecked=True,history_complete_for_all_preexisting_deliveries=True,
        production_evidence_counts=counts,unknown_official_effect=True,UTC=utc())
    save(ROOT/'package_engineering_admission_15.json',permit)
    inputs=dict(old_package_inputs_ref=ref(OLD/'package_inputs.json'),old_source_package_lock_ref=ref(OLD/'source_package_lock.json'),
        protected_baseline_zip_ref=ref(baseline),production_completion_ref=ref(PRODUCTION/'completion.json'),
        history_ref=deployment['history_ref'],protocol_ref=deployment['protocol_ref'],authorization_ref=ref(ROOT/'USER_AUTHORIZATION.json'),
        official_rule_check_ref=ref(ROOT/'official_rule_check.json'),package_admission_ref=ref(ROOT/'package_engineering_admission_15.json'),code_files=deployment['code_files'])
    for name,r in inputs.items():
        if name.endswith('_ref'):checked(r)
    save(ROOT/'package_inputs.json',inputs)
    print('PASS_COMPLETE_ACTUAL_NEW_PRODUCTION_ENGINEERING_NOT_EFFECT',json.dumps(counts),flush=True)

def admit_quality():
    setup();result_path=ROOT/'relative_confirm/policy_fresh_comparison.json';result=read(result_path)
    development_path=ROOT/'policy_comparison_08.json';development=read(development_path)
    selection=read(ROOT/'policy_comparison_08_selection.json');publication=read(ROOT/'publication_protocol_13.json')
    require(result['schema']=='MIDNIGHT_RELATIVE_WORST_POLICY_COMPARISON_V1' and result['group']=='confirm' and result['full_source_count']==4,'Actual first fresh four-source comparison required')
    require(result['status']=='FIRST_FRESH_POLICY_COMPARISON_COMPLETE' and result['source_model_answers_modified'] is False and result['old_scientific_failures_changed'] is False,'First actual frozen comparison required')
    require(selection['selected_policies']==['ALL_WINDOW_WORST','PAIR_ONLY']==result['selected_policies'],'Only previously frozen development selection may be confirmed')
    require(result['bindings']['protocol_ref']==selection['protocol_ref']==ref(ROOT/'policy_protocol_07.json'),'Confirmation must bind frozen original protocol')
    require(publication['development_selection_ref']==ref(ROOT/'policy_comparison_08_selection.json'),'Published application mapping binds another development selection')
    for r in result['bindings'].values():checked(r)
    manifest=read(checked(result['bindings']['manifest_ref']));dev_manifest=read(checked(development['bindings']['manifest_ref']))
    require(manifest.get('group')=='confirm','Fresh manifest group differs')
    require(len(manifest['sources'])==len(dev_manifest['sources'])==4 and
        not ({v['source_name'] for v in manifest['sources']} & {v['source_name'] for v in dev_manifest['sources']}) and
        not ({v['source_sha256'] for v in manifest['sources']} & {v['source_sha256'] for v in dev_manifest['sources']}),
        'First confirmation IDs and actual source bytes must be disjoint from development')
    fresh=read(checked(manifest['fresh_admission_ref']))
    require(fresh['status']=='PASS_MIDNIGHT_NEW4_ID_BYTES_NATIVE_ADMISSION' and
        fresh['sources_unexposed_before_registration'] is True and fresh['quality_metrics_examined_before_freeze'] is False,
        'New source admission must be actual and before first confirmation metrics')
    # The evaluator already binds actual native references and complete group.
    # No unselected risk field or risk quality measure is read by this function.
    arms={}
    for arm,policy in [('ORDINARY','ALL_WINDOW_WORST'),('REDUNDANT','PAIR_ONLY')]:
        passed=result['passed_policies'][policy] is True and development['passed_policies'][policy] is True
        value=dict(status='PASS' if passed else 'FAILED_FIXED_NEW_CONFIRMATION',reference_scope='Four unseen external event-conditioned human-summary sources, all-rater paired duration F1 and precision; not official unconditional highlight GT; global/pretraining overlap UNKNOWN',
            independent_confirmation=True,test_labels_used=False,development_ref=ref(development_path),confirmation_ref=ref(result_path),frozen_rule_ref=ref(ROOT/'publication_protocol_13.json'),
            deterministic_deletion_policy=publication['deletion_application_policy'][arm],actual_model_parsed_unchanged=True,source_policy=policy,official_improvement='UNKNOWN')
        arms[arm]=value
    save(ROOT/'quality_admission.json',dict(schema='FIRST_FRESH_TWO_FROZEN_DELETION_POLICY_ADMISSION_V1',arms=arms,UTC=utc(),risk_effect_quality_screening=False,old_scientific_gates_changed=False))
    print('FIRST_FRESH_TWO_POLICY_QUALITY_ADMISSION',json.dumps({k:v['status'] for k,v in arms.items()}),flush=True)

def package(arms):
    setup();argv=[str(PY),'-B',str(ROOT/'package_code_v2/package_five.py'),'--arms',*arms]
    subprocess.run(argv,env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'),check=True)

def wait_risk():
    setup();folder=ROOT/'risk_finalization_15';folder.mkdir(exist_ok=False)
    save(folder/'started.json',dict(pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split()[21],UTC=utc(),operation='Wait existing natural production; initialize engineering then three risk CPU packages only'))
    try:
        while not (PRODUCTION/'chain_completion.json').exists():
            require(not any((PRODUCTION/p).exists() for p in ['chain_failure.json','infer_failure.json','output_qa_failure.json']),'Actual production failed; never auto recover or package missing outputs')
            require(dt.datetime.now(dt.timezone.utc)<dt.datetime.fromisoformat('2026-10-15T16:00:00+00:00'),'Taipei midnight reached without natural production completion')
            time.sleep(15)
        initialize_engineering();package(['ACTION','REACTION','INFORMATION'])
        save(folder/'completion.json',dict(status='REQUESTED_RISK_CPU_PACKAGING_COMPLETE_SEE_ACTUAL_PACKAGES',UTC=utc(),new_model_calls=0))
    except BaseException as e:
        save(folder/'failure.json',dict(error=repr(e),traceback=traceback.format_exc(),UTC=utc(),automatic_retry=False,keep_all_successful=True));raise

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('operation',choices=['initialize','admit_quality','wait_risk','package_quality']);a=p.parse_args()
    if a.operation=='initialize':initialize_engineering()
    elif a.operation=='admit_quality':admit_quality()
    elif a.operation=='wait_risk':wait_risk()
    else:package(['ORDINARY','REDUNDANT'])
