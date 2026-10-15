"""Exactly one supplemental short-source PAIR chain; preserve every success/failure."""
import importlib
from control_helpers import *
from applicability_contract import validate_selection

RANK_STAGE = 'relative_pair_short_confirm_22'
JOBS = dict(B0='midnight_pair_short4_b0_20261015_v1',
    VERIFY='midnight_pair_short4_verify_20261015_v1', RANK='midnight_pair_short4_rank_20261015_v1')

def preflight(state, label):
    snapshot(state, label)
    active = HOME/'improvement_round1/active_gpu_job.json'
    require(not active.exists() or read(active) is None, 'Existing shared GPU reservation: preserve external job and stop')
    rows = subprocess.run(['nvidia-smi','--query-compute-apps=pid,process_name,used_memory','--format=csv,noheader,nounits'],
        capture_output=True, text=True, check=True).stdout.strip()
    require(not rows, 'Actual external GPU compute process exists: stop without touching it')
    require(shutil.disk_usage(ROOT).free > read(ROOT/'source_candidates.json')['maximum_pool_bytes'], 'Actual capacity cannot hold the finite registered media payload; subsequent CPU stages check measured tensor/output capacity')

def verify_deployment(state):
    require(socket.gethostname() == 'inspur-NP5570M5' and sys.platform == 'linux'
        and Path(__file__).resolve() == ROOT/'controller.py', 'Exact independent Linux host/root/controller required')
    auth = read(ROOT/'launch_authorization.json')
    require(auth['scope'] == 'ONE_SUPPLEMENTAL_SHORT_PAIR_MEDIA_CPU_GPU_CHAIN'
        and auth['controller_sha256'] == sha(__file__) and auth['root'] == str(ROOT)
        and auth['no_automatic_retry'] is True, 'Main-agent reviewed unique launch authorization required')
    manifest = read(ROOT/'deployment_manifest.json')
    for name, digest in manifest.items():
        path = ROOT/name
        require(not Path(name).is_absolute() and '..' not in Path(name).parts and sha(path) == digest,
            'New deployment differs from reviewed file: '+name)
    oldrank = read(MAIN/'relative_dev_03/registration.json')
    for path, digest in oldrank['code_files'].items():
        checked(dict(path=path,sha256=digest))
    selection, protocol = validate_selection(ROOT)
    require(read(ROOT/'public_routes.json')['source_candidates_sha256'] == sha(ROOT/'source_candidates.json'),
        'Current six Windows anonymous HEAD routes must bind this unique source registration')
    save(state/'deployment_verification.json', dict(status='PASS_NEW_CODE_SHA_AND_OLD_FROZEN_CODE_AND_SCOPED_SELECTION',
        files=manifest, new_selection_ref=ref(ROOT/'new_selection.json'), supplemental_protocol_ref=ref(ROOT/'supplemental_protocol.json'),
        old_rank_code_files=oldrank['code_files'], utc=utc()))

def register_media():
    candidates = read(ROOT/'source_candidates.json'); metadata = read(ROOT/'isolation_metadata.json')
    helper = HOME/'recall_positive_admission_verify40_46_20261015_v1/fresh_01/media_code/positive_media.py'
    paths = list((ROOT/'media').glob('*.py'))+[ROOT/name for name in
        ('source_candidates.json','public_routes.json','new_selection.json','supplemental_protocol.json','isolation_metadata.json','launch_authorization.json')]
    paths += [helper,MAIN/'policy_protocol_07.json',MAIN/'policy_comparison_08.json',MAIN/'USER_AUTHORIZATION.json',
        HOME/'videoxum_reference_iteration_20261013_v1/code/native_profile_01.py',
        HOME/'videoxum_reference_iteration_20261013_v1/code/native_profile_04.py']
    for key in ('annotation_ref','known_exclusions_ref','previous_source_candidates_ref','previous_fresh_media_completion_ref',
        'previous_neutral_PAIR_result_ref','original_development_selection_ref'):
        paths.append(checked(metadata[key]))
    paths += [checked(v) for v in metadata['prior_registry_refs']+metadata['prior26_media_receipts']+metadata['source_scope_refs']]
    required = {str(path):sha(path) for path in paths}
    reg = dict(schema='MIDNIGHT_PAIR_SHORT_MEDIA_REGISTRATION_V1',status='REGISTERED_MIDNIGHT_PAIR_SHORT_MEDIA_NATIVE',
        group='confirm',expected_accepted_sources=4,maximum_media_pool_bytes=26768757,windows_video_body_bytes=0,
        production_admitted=False,protocol_ref=ref(MAIN/'policy_protocol_07.json'),authorization_ref=ref(MAIN/'USER_AUTHORIZATION.json'),
        development_selection_ref=ref(ROOT/'new_selection.json'),source_candidates_ref=ref(ROOT/'source_candidates.json'),
        public_routes_ref=ref(ROOT/'public_routes.json'),media_helper_ref=ref(helper),required_files=required,
        supplemental_protocol_ref=ref(ROOT/'supplemental_protocol.json'),previous_neutral_PAIR_result_ref=metadata['previous_neutral_PAIR_result_ref'],
        registered_before_first_media_GET=True,registered_utc=utc())
    save(ROOT/'media_registration.json',reg)

def register_inputs(state):
    sys.path.insert(0,str(CODE)); import model_common as io
    from source_plan import source_document, unique_view_plan
    media = read(ROOT/'reference_01/completion.json')
    clocks = {row['video_id']:read(row['clock_path']) for row in media['accepted']}
    plan = unique_view_plan(source_document(media['accepted'],clocks,'confirm'),'confirm')
    require(plan['actual_input_count'] == 4 and all(v['view_roles']==['baseline'] for v in plan['unique_views']),
        'Four complete original native64 <=30-second baseline windows required')
    old = read(HOME/'recall_adapter_role_verify40_46_20261015_v1/fresh_01/positive_fresh_registration.json')
    paths = set(io.runtime_dependencies()) | set(io.processor_assets()) | {str(io.CONFIG),str(io.RUNTIME)}
    paths.update(str(p) for p in CODE.glob('*.py'))
    paths.update(str(io.CV_CODE/name) for name in ('cv_contract.py','cv_tokens.py','cv_grammar.py'))
    paths.add(old['capacity_contract']['processor_source_path'])
    paths.update(read(ROOT/'media_registration.json')['required_files'])
    paths.update(str(ROOT/name) for name in ('media_registration.json','reference_01/completion.json','new_selection.json','supplemental_protocol.json'))
    for row in media['accepted']:
        paths.update((row['media']['path'],row['clock_path'],row['reference_path'],str(Path(row['media']['path']).parent/'media_receipt.json'),str(Path(row['media']['path']).parent/'route.json')))
    required = {str(Path(path).resolve()):sha(path) for path in paths}
    reg = dict(status='REGISTERED_MIDNIGHT_PAIR_SHORT_FRESH_INPUTS_V1',group='confirm',model_parameters=8782459120,
        optimizer_updates=0,source_scope='EXTERNAL_NONTEST_ONLY',reference_available_to_inference=False,production_admitted=False,
        protocol_ref=ref(MAIN/'policy_protocol_07.json'),authorization_ref=ref(MAIN/'USER_AUTHORIZATION.json'),
        dev_selection_ref=ref(ROOT/'new_selection.json'),dev_result_ref=ref(MAIN/'policy_comparison_08.json'),
        source_registration_ref=ref(ROOT/'media_registration.json'),source_candidates_ref=ref(ROOT/'source_candidates.json'),
        reference_completion_ref=ref(ROOT/'reference_01/completion.json'),required_files=required,capacity_contract=old['capacity_contract'],
        deadline=DEADLINE,gpu_budget=dict(B0=dict(max_actual_calls=4,max_seconds=900,gpu_job_name=JOBS['B0']),
            VERIFY=dict(max_actual_calls=20,max_seconds=1800,gpu_job_name=JOBS['VERIFY'])),
        supplemental_protocol_ref=ref(ROOT/'supplemental_protocol.json'),registered_before_first_RGB_or_processor=True,registered_utc=utc())
    save(ROOT/'positive_fresh_registration.json',reg);save(state/'measured_baseline_plan.json',plan)
    return io,reg

def resource_refs(names):
    result = {}
    ledger = [json.loads(line) for line in (HOME/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if line.strip()]
    for name in names:
        path = RUN/'controller'/(name+'.resource.json');terminal = read(path)
        require(terminal['status']=='completed' and terminal['exit_code']==0 and [r for r in ledger if r['name']==name]==[terminal],
            'Unique actual completed/exit0 GPU terminal and ledger equality required')
        result[name] = ref(path)
    return result

def structural_stop(state, reason, counts, names):
    """No fabricated model/QA or quality metrics for an inapplicable cohort."""
    value = dict(schema='MIDNIGHT_RELATIVE_WORST_POLICY_COMPARISON_V1',group='confirm',
        status='STOP_SUPPLEMENTAL_PAIR_NOT_APPLICABLE',reason=reason,selected_policies=['PAIR_ONLY'],
        passed_policies=dict(PAIR_ONLY=False),passed_arms=dict(PAIR_ONLY=False),full_source_count=4,
        policies=dict(PAIR_ONLY=dict(PASS=False,gates=dict(real_changed_sources=False),macro={},cases=[],
            quality_metrics_not_computed=True)),
        bindings=dict(protocol_ref=ref(MAIN/'policy_protocol_07.json'),supplemental_protocol_ref=ref(ROOT/'supplemental_protocol.json'),
            development_selection_ref=ref(ROOT/'new_selection.json'),media_completion_ref=ref(ROOT/'reference_01/completion.json')),
        no_further_pool_or_cohort=True,old_scientific_failures_changed=False,production_admitted=False)
    save(ROOT/'policy_fresh_comparison.json',value)
    save(state/'completion.json',dict(status='STOP_FIRST_SHORT_SOURCE_PAIR_NOT_APPLICABLE',comparison_ref=ref(ROOT/'policy_fresh_comparison.json'),
        media_registration_ref=ref(ROOT/'media_registration.json'),positive_fresh_registration_ref=ref(ROOT/'positive_fresh_registration.json'),
        rank_completion_ref=None,actual_calls=counts,natural_GPU_resource_refs=resource_refs(names),production_admitted=False,utc=utc()))

def main():
    state = ROOT/'control_01';state.mkdir(exist_ok=False);stage='PREFLIGHT'
    save(state/'started.json',dict(utc=utc(),pid=os.getpid(),start_ticks=Path('/proc/self/stat').read_text().split()[21],
        argv=Path('/proc/self/cmdline').read_bytes().decode().split('\0')[:-1],controller_ref=ref(__file__),no_retry=True))
    counts = dict(B0=0,VERIFY=0,RANK=0);names=[]
    try:
        preflight(state,'initial');verify_deployment(state);register_media();stage='NEW_MEDIA_NATIVE'
        child(state,stage,[PY,'-B',ROOT/'media/confirm_media.py','--root',ROOT])
        media = read(ROOT/'reference_01/completion.json');require(len(media['accepted'])==4,'Complete new4 media/native stage required')
        io,reg = register_inputs(state)
        stage='PRIMARY_NATIVE64';child(state,stage,[PY,'-B',CODE/'prepare_inputs.py','--root',ROOT])
        stage='FIRST_NATIVE64_QA';child(state,stage,[PY,'-B',CODE/'first_input_qa.py','--root',ROOT])
        stage='B0';preflight(state,'B0_preflight');run_gpu(state,io,reg,'B0');names.append(JOBS['B0']);counts['B0']=read(ROOT/'confirm/B0/gpu_01/completion.json')['calls']
        stage='VERIFY_PREPARE';child(state,stage,[PY,'-B',CODE/'pilot_verify.py','prepare','--root',ROOT,'--group','confirm'])
        count = len(read(ROOT/'confirm/VERIFY/cpu_01/completion.json')['entries'])
        if count == 0:
            structural_stop(state,'ALL_FOUR_B0_VIEWS_HAVE_ZERO_CANDIDATES',counts,names);return
        stage='VERIFY_FIRST_INPUT_QA';child(state,stage,[PY,'-B',CODE/'verify_input_qa.py','--root',ROOT])
        stage='VERIFY';preflight(state,'VERIFY_preflight');run_gpu(state,io,reg,'VERIFY');names.append(JOBS['VERIFY']);counts['VERIFY']=count
        stage='MAP_COMPLETED_NEW_BASELINE';child(state,stage,[PY,'-B',REF/'map_confirm_completed.py','--root',ROOT,'--output',ROOT/'rank_mapping_01'])
        mapping = read(ROOT/'rank_mapping_01/inference_entries.json');entries=mapping['entries']
        require(0 <= len(entries) <= 4,'Only actual nonempty baseline views, at most4, may be ranked')
        if not any(len(e['candidate_events'])==2 for e in entries):
            structural_stop(state,'NO_ORIGINAL_BASELINE_VIEW_HAS_EXACTLY_TWO_CANDIDATES',counts,names);return
        rank_root=MAIN/RANK_STAGE;rank_root.mkdir(exist_ok=False)
        oldreg=read(MAIN/'relative_dev_03/registration.json')
        rankreg=dict(oldreg,stage=RANK_STAGE,requests_ref=ref(ROOT/'rank_mapping_01/inference_entries.json'),
            protocol_ref=ref(MAIN/'policy_protocol_07.json'),authorization_ref=ref(MAIN/'USER_AUTHORIZATION.json'),
            gpu_job_name=JOBS['RANK'],max_GPU_seconds=600,deadline=DEADLINE,development_selection_ref=ref(ROOT/'new_selection.json'),
            original_prompt_protocol_ref=ref(MAIN/'relative_protocol_03.json'),first_fresh_external_confirmation=True,
            supplemental_short_pair_cohort=True,maximum_actual_calls=4,production_admitted=False)
        save(rank_root/'registration.json',rankreg)
        stage='NEW_RELATIVE_RANK';preflight(state,'RANK_preflight');child(state,stage,[PY,'-B',MAIN/'relative_code_v1/controller.py','--stage',RANK_STAGE],GPU_ENV)
        names.append(JOBS['RANK']);counts['RANK']=read(rank_root/'completion.json')['actual_model_calls'];require(counts['RANK']==len(entries),'Exact rank denominator required')
        stage='FIRST_SUPPLEMENTAL_PAIR_COMPARISON'
        child(state,stage,[PY,'-B',REF/'policy_evaluate.py','--protocol',MAIN/'policy_protocol_07.json',
            '--manifest',ROOT/'rank_mapping_01/first_fresh_evaluation_manifest.json','--decisions',rank_root/'completion.json',
            '--development-selection',ROOT/'new_selection.json','--output',ROOT/'policy_fresh_comparison.json'],allowed=(0,5))
        comparison=read(ROOT/'policy_fresh_comparison.json')
        save(state/'completion.json',dict(status='NATURAL_COMPLETE_FIRST_SHORT_SOURCE_PAIR_APPLICABILITY_CONFIRMATION',utc=utc(),
            comparison_ref=ref(ROOT/'policy_fresh_comparison.json'),media_registration_ref=ref(ROOT/'media_registration.json'),
            positive_fresh_registration_ref=ref(ROOT/'positive_fresh_registration.json'),rank_completion_ref=ref(rank_root/'completion.json'),
            passed_policies=comparison['passed_policies'],selected_policies=['PAIR_ONLY'],full_source_count=4,
            actual_media_payload_bytes=media['actual_new_media_payload_bytes'],B0_calls=counts['B0'],VERIFY_calls=counts['VERIFY'],rank_calls=counts['RANK'],
            actual_calls=counts,natural_GPU_resource_refs=resource_refs(names),first_B0_input_QA_ref=ref(ROOT/'confirm/B0/input_qa_01/completion.json'),
            first_VERIFY_input_QA_ref=ref(ROOT/'confirm/VERIFY/input_qa_01/completion.json'),rank_first_QA_complete=True,
            old_successful_stages_repeated=0,production_admitted=False,official_improvement='UNKNOWN'))
        print(json.dumps(dict(status='COMPLETE',passed=comparison['passed_policies'],actual_calls=counts)),flush=True)
    except BaseException as error:
        save(state/'failure.json',dict(status='FAILED_FIRST_REAL_STAGE_NO_RETRY',stage=stage,utc=utc(),error=repr(error),
            traceback=traceback.format_exc(),actual_completed_calls=counts,preserve_all_success=True,automatic_retry=False,production_admitted=False))
        print(json.dumps(dict(status='FAILED',stage=stage,error=repr(error))),flush=True);raise

if __name__=='__main__':
    main()
