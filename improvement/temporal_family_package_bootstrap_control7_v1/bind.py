"""Linux metadata closure only. Never grants admission or creates a ZIP."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import socket
import sys
from control6_chain import validate_continuation, validate_producer
from control7_recovery import controller_gate, validate_recovery

HOME=Path('/home/inspur/aic_video_work')
CAMPAIGN=HOME/'twenty_hour_five_20261014_v1'
RUN=HOME/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
ROOT=CAMPAIGN/'temporal_family_native_package_v3'
INPUT=CAMPAIGN/'temporal_production_inputs_v5'
RUNTIME=CAMPAIGN/'temporal_production_runtime_v5'
CONTROL=CAMPAIGN/'temporal_production_control_v6'
FINAL=CAMPAIGN/'temporal_global_recovery_control7_v1'
BASE=CAMPAIGN/'temporal_family_package_bootstrap_control7_v1'
ORIGINAL_CONTROL=CAMPAIGN/'temporal_production_control_v5'
BOOT=CAMPAIGN/'temporal_production_bootstrap_v2'
PARAMETERS=8782459120
RENDERER_SHA='9a0369a1034b96e16a570ca4864032beeb606842b1fc897e833c492094c7962e'
ARMS=['START','END','BOTH','VERIFY','VERIFY_BOTH','SOURCE_START','SOURCE_END','SOURCE_BOTH']
FIELD_NAMES={'field_shots.jsonl','anchor_requests.jsonl','anchor_output.jsonl','field_frames.jsonl'}
MEDIA_SUFFIXES={'.mp4','.mkv','.webm','.mov','.avi','.mpeg','.mpg','.m4v'}


def require(ok,why):
    if not ok:raise ValueError(why)


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()


def file_sha(path):
    h=hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(8<<20),b''):h.update(block)
    return h.hexdigest()


def save(path,value):
    with path.open('x',encoding='utf8') as f:
        json.dump(value,f,indent=2,ensure_ascii=False,allow_nan=False);f.flush();os.fsync(f.fileno())


def get_at(value,parts):
    for part in parts:value=value[part]
    return value


class Closure:
    """Memoized SHA reads of metadata; no tensor load, RGB or media body read."""
    def __init__(self):
        self.files={};self.documents={};self.visited=set();self.cache=None
        self.provenance_only=[];self.released_RGB=[];self.deferred_payloads={}
        self.deferred_paths=set()

    def absolute(self,ref):
        require(isinstance(ref,dict) and re.fullmatch(r'[0-9a-f]{64}',ref.get('sha256','')),
            'Explicit lower-case file SHA required')
        if 'relative' in ref:
            require(self.cache is not None,'Cache root must be frozen before resolving cache references')
            relative=Path(ref['relative'])
            require(not relative.is_absolute() and '..' not in relative.parts,'Cache reference escaped')
            path=(self.cache/relative).resolve()
            require(path.is_relative_to(self.cache),'Cache reference escaped its canonical root')
        else:
            require(isinstance(ref.get('path'),str) and ref['path'].startswith('/'),'Actual Linux absolute reference required')
            path=Path(ref['path']).resolve()
        require(path.is_relative_to(HOME),'Actual closure reference escaped project HOME')
        return dict(path=str(path),sha256=ref['sha256'])

    def add(self,ref,*,body=True):
        resolved=self.absolute(ref);path=Path(resolved['path']);value=resolved['sha256']
        require(path.is_file(),'Required retained evidence missing: '+str(path))
        if 'bytes' in ref:require(path.stat().st_size==ref['bytes'],'Retained byte count changed: '+str(path))
        if str(path) in self.files:
            require(self.files[str(path)]==value,'Conflicting closure SHA: '+str(path));return resolved
        if body:
            require(path.suffix.lower() not in MEDIA_SUFFIXES and path.suffix.lower()!='.npz',
                'Binder cannot read media/RGB bodies')
            require(file_sha(path)==value,'Frozen metadata/code changed: '+str(path))
        else:self.deferred_payloads[str(path)]=dict(sha256=value,bytes=path.stat().st_size,
            digest_source='EXISTING_ACCEPTED_REFERENCE_NOT_REHASHED_BY_BINDER',
            final_renderer_checks_file_SHA=True)
        self.files[str(path)]=value
        return resolved

    def load(self,ref,*,walk=True):
        resolved=self.add(ref);path=resolved['path']
        historical_draft=CAMPAIGN/'temporal_family_package_bootstrap_v1/config_draft_01.json'
        if path==str(historical_draft):
            require(resolved['sha256']=='b5edf67cff7776a87d5afc1fdd7c32a00e693a33b44d3481df9545c98c2e2bb3',
                'Exact immutable historical draft identity required; never an active input')
            walk=False # Preserve/hash its exact bytes; unresolved historical future refs are not actual evidence.
        require(Path(path).suffix=='.json','Only explicit JSON metadata is parsed by the closure walker')
        if path not in self.documents:self.documents[path]=json.loads(Path(path).read_text(encoding='utf-8-sig'))
        value=self.documents[path]
        if walk and path not in self.visited:
            self.visited.add(path);self.walk(value)
        return value

    def reference(self,ref):
        if 'relative' not in ref and not str(ref.get('path','')).startswith('/'):
            self.provenance_only.append(ref);return
        resolved=self.absolute(ref);path=Path(resolved['path'])
        if path.suffix.lower() in MEDIA_SUFFIXES:
            self.provenance_only.append(dict(ref,reason='SOURCE_MEDIA_BYTES_ALREADY_PROVEN_NOT_READ_OR_LOCKED_BY_BINDER'));return
        if self.cache is not None and path.is_relative_to(self.cache/'staging'):
            self.released_RGB.append(dict(ref,reason='HISTORICAL_RELEASED_RGB_PROVENANCE_NOT_A_RETAINED_FILE'));return
        if str(path) in self.deferred_paths:self.add(ref,body=False);return
        if path.suffix=='.json':self.load(ref)
        elif path.suffix in ('.py','.jsonl','.txt','.toml','.yaml','.yml','.cfg','.ini'):
            self.add(ref)
        else:self.add(ref,body=False) # Exact accepted SHA/bytes; final renderer checks payload once.

    def walk(self,value):
        if isinstance(value,list):
            for item in value:self.walk(item)
        elif isinstance(value,dict):
            if ('path' in value or 'relative' in value) and 'sha256' in value:
                self.reference(value);return
            if value and all(isinstance(path,str) and path.startswith('/') and isinstance(sha,str) and
                re.fullmatch(r'[0-9a-f]{64}',sha) for path,sha in value.items()):
                for path,sha in value.items():self.reference(dict(path=path,sha256=sha))
                return
            for key,item in value.items():
                if key=='required_code_files':
                    require(isinstance(item,dict),'Frozen code map required')
                    for path,sha in item.items():self.add(dict(path=path,sha256=sha))
                else:self.walk(item)

    def copy_document(self,ref,target):
        resolved=self.add(ref);source=Path(resolved['path'])
        require(source.suffix=='.json' and target.parent==ROOT,'Only root-provided JSON documents are copied')
        if target.exists():
            require(file_sha(target)==resolved['sha256'],'Existing package document conflicts; preserve it')
        elif source!=target:
            with source.open('rb') as src,target.open('xb') as dst:
                for block in iter(lambda:src.read(1<<20),b''):dst.write(block)
                dst.flush();os.fsync(dst.fileno())
        return self.add(dict(path=str(target),sha256=resolved['sha256']))

    def observe_json(self,path):
        """Bind a fixed completed authority path once, without another producer run."""
        path=path.resolve();require(path.is_relative_to(HOME) and path.suffix=='.json','Fixed Linux authority JSON only')
        if str(path) in self.documents:return self.documents[str(path)]
        data=path.read_bytes();sha=hashlib.sha256(data).hexdigest()
        require(str(path) not in self.files or self.files[str(path)]==sha,'Completed authority changed')
        self.files[str(path)]=sha;self.documents[str(path)]=json.loads(data)
        self.visited.add(str(path));self.walk(self.documents[str(path)])
        return self.documents[str(path)]

    def observe_jsonl(self,path):
        path=path.resolve();require(path.is_relative_to(HOME) and path.suffix=='.jsonl','Fixed completed journal only')
        data=path.read_bytes();sha=hashlib.sha256(data).hexdigest()
        require(str(path) not in self.files or self.files[str(path)]==sha,'Completed journal changed')
        self.files[str(path)]=sha
        records=[json.loads(line) for line in data.splitlines() if line]
        self.walk(records);return records


def history(closure,specs):
    require(isinstance(specs,list) and specs,'Root must supply the fixed historical receipt list')
    result=[]
    for spec in specs:
        receipt=closure.load(spec['receipt_ref'],walk=False)
        records=get_at(receipt,spec['rows_path']);require(isinstance(records,list),'Explicit historical record list required')
        if spec.get('select_all_records') is True:
            require('selectors' not in spec,'Historical selection is either the fixed whole list or explicit selectors')
            chosen=records
        else:
            require(isinstance(spec['selectors'],list) and spec['selectors'],'Explicit fixed history selectors required')
            chosen=[]
            for selector in spec['selectors']:
                matches=[row for row in records if all(get_at(row,field.split('.'))==expected for field,expected in selector.items())]
                require(len(matches)==1,'Historical selector must match exactly one existing successful receipt')
                chosen.append(matches[0])
        fields=spec['field_map']
        require({'filename','ZIP_SHA256','member_SHA256','canonical_SHA256'}<=set(fields),
            'Root must provide the existing canonical/ZIP/member identity field mapping')
        for row in chosen:
            projected={key:get_at(row,value.split('.')) for key,value in fields.items()}
            require(isinstance(projected['filename'],str) and projected['filename'] and
                all(re.fullmatch(r'[0-9a-f]{64}',projected[key]) for key in ('ZIP_SHA256','member_SHA256','canonical_SHA256')),
                'Existing successful historical canonical identity is incomplete')
            projected.update(source_receipt_ref=closure.absolute(spec['receipt_ref']),original_record_sha256=digest(row))
            result.append(projected)
    require(result,'A fixed nonempty history must be bound; never infer names from time')
    return result


def gate(closure,config):
    require(config['schema']=='TEMPORAL_FAMILY_PACKAGE_BOOTSTRAP_CONTROL7_V1' and config['package_root']==str(ROOT),
        'Explicit fixed metadata binder configuration required')
    require(Path(config['production_completion_ref']['path']).resolve()==FINAL/'exports_01/global_completion.json' and
        Path(config['controller_completion_ref']['path']).resolve()==FINAL/'run_01/completion.json',
        'Only actual independent CONTROL7 aggregate recovery terminals can open this metadata gate')
    production=closure.load(config['production_completion_ref'],walk=False)
    controller=closure.load(config['controller_completion_ref'],walk=False)
    require(production['status']=='PASS_COMPLETE_ALL_PROSPECTIVE_TEMPORAL_REQUESTS_AND_FIRST_INDEPENDENT_REPLAYS' and
        production['engineering_failed_requests']==0 and production['missing_requests']==0 and
        production['physical_model_parameters']==PARAMETERS and production['optimizer_updates']==0 and
        production['test_GT_or_annotation_read'] is False and production['native_clock_matches_original_full_PTS'] is True and
        production['scientific_quality_claim'] is False and production['old_scientific_failed_gates_changed'] is False and
        production['old_packet_FAIL_reclassified'] is False and
        production['native_terminal_scope']=='NEW_PYAV17_READER_NATIVE_TERMINAL_SCOPE_V5_VERIFY_SHORT_CONTEXT_UNKNOWN',
        'Actual complete INPUT5/CONTROL6 production is required; no quality or old-failure promotion')
    controller_gate(controller, config['production_completion_ref'])
    return production,controller


def bind(config_path):
    require(sys.platform=='linux' and socket.gethostname()=='inspur-NP5570M5' and
        os.environ.get('CUDA_VISIBLE_DEVICES')=='','Linux metadata-only CPU child required')
    config_path=config_path.resolve();require(config_path.is_relative_to(HOME),'Linux frozen config only')
    config=json.loads(config_path.read_text());closure=Closure()
    production,controller=gate(closure,config) # No package-root write before both real natural terminal gates.
    config_ref=dict(path=str(config_path),sha256=file_sha(config_path));closure.add(config_ref)
    require(Path(__file__).resolve().parent==BASE/'code' and
        set(config['required_binder_code_files'])=={str(p.resolve()) for p in (BASE/'code').glob('*.py')},
        'The actually executed binder code must be explicitly frozen')
    for path,sha in config['required_binder_code_files'].items():closure.add(dict(path=path,sha256=sha))
    require(not (ROOT/'package_admission.json').exists(),'Final admission already exists; this binder cannot alter its closure')
    targets=[ROOT/name for name in ('package_inputs.json','history.json','source_package_lock.json','technical_preparation_receipt.json')]
    require(all(not path.exists() for path in targets),'Already attempted/successful bindings require explicit remaining recovery; no overwrite')
    refs=config['production_refs']
    expected_paths={'input_registration':INPUT/'registration.json','full_plan':INPUT/'plan_01/full_plan.json',
        'plan_completion':INPUT/'plan_01/completion.json','cache_initialization':INPUT/'cache_initialization.json',
        'runtime_protocol':RUNTIME/'protocol.json','control_registration':CONTROL/'registration.json',
        'bootstrap_completion':BOOT/'bootstrap_run_01/completion.json'}
    require(set(refs)==set(expected_paths),'All current production registration/graph/cache/bootstrap refs required')
    for name,path in expected_paths.items():require(Path(refs[name]['path']).resolve()==path,'Wrong current production root: '+name)
    input_reg=closure.load(refs['input_registration'],walk=False)
    closure.cache=Path(input_reg['cache_root']).resolve()
    require(closure.cache.parent==CAMPAIGN and closure.cache.name.startswith('production_stream_v'),
        'Actual frozen production cache root required')
    require(set(config['legacy_inputs']['source_field_files'])==FIELD_NAMES,'Explicit four original field files required')
    closure.deferred_paths={closure.absolute(ref)['path'] for ref in config['legacy_inputs']['source_field_files'].values()}
    documents={name:closure.load(ref) for name,ref in refs.items()}
    plan=documents['full_plan'];runtime=documents['runtime_protocol'];control=documents['control_registration']
    continuation=validate_continuation(closure,documents,refs,production,controller,CONTROL,ORIGINAL_CONTROL,BOOT)
    plan_sha=refs['full_plan']['sha256']
    require(production['global_graph_sha256']==plan_sha==control['global_graph_sha256'] and
        runtime['full_plan_ref']==refs['full_plan'] and runtime['input_registration_ref']==refs['input_registration'] and
        runtime['input_root']==str(INPUT) and control['runtime_protocol_ref']==refs['runtime_protocol'] and
        documents['plan_completion']['full_plan_sha256']==plan_sha and
        documents['cache_initialization']['whole_plan_sha256']==plan_sha and
        documents['bootstrap_completion']['status']=='PASS_ONCE_METADATA_GRAPH_CACHE_BATCH_BOOTSTRAP_NOT_FORMAL_EXECUTION_ADMISSION',
        'Actual whole graph/input/cache/runtime/controller closure differs')
    initialization=documents['cache_initialization']
    closure.load(dict(path=str(closure.cache/'policy.json'),sha256=initialization['policy_sha256']))
    closure.load(initialization['frozen_consumers_ref'])
    permission_path=Path(input_reg['actual_preparation_permission_path']).resolve()
    admission_path=Path(control['main_execution_admission_path']).resolve()
    require(permission_path.is_relative_to(INPUT) and admission_path.is_relative_to(CONTROL),
        'Actual completed source/controller authorities escaped their exact roots')
    permission=closure.observe_json(permission_path);admission=closure.observe_json(admission_path)
    require(permission['status']=='APPROVED_ONCE_NEW_V5_FORMAL_SOURCE_DECODE_AND_PROCESSOR' and
        permission['input_registration_sha256']==refs['input_registration']['sha256'] and
        admission['status']=='MAIN_APPROVED_CONTROLLED_REMAINING_PRODUCTION_V6' and
        admission['registration_sha256']==refs['control_registration']['sha256'] and
        admission['quiescent_handoff_ref']==control['quiescent_handoff_ref'] and
        admission['original_control_registration_ref']==control['original_control_registration_ref'] and
        admission['allow_remaining_original_gpu_jobs_once'] is True and admission['allow_project_init_or_rebatch'] is False,
        'Actual terminal cannot replace its independent root source/controller authorities')
    closure.load(dict(path=str(CONTROL/'run_01/launch_claim.json'),
        sha256=production['controller_launch_claim_sha256']))
    journal=closure.observe_jsonl(CONTROL/'run_01/journal.jsonl')
    validate_recovery(closure,controller,production,config,plan,journal,CONTROL,FINAL)
    lifecycle=closure.observe_jsonl(closure.cache/'permanent/lifecycle.jsonl')
    accepted=[row for row in lifecycle if row.get('event')=='CONSUMER_ACCEPTED']
    released=[row for row in lifecycle if row.get('event')=='RGB_RELEASED']
    require(len(accepted)==len(plan['consumers']) and {row['consumer'] for row in accepted}==set(plan['consumers']) and
        len(released)==len(plan['RGB_groups']) and {row['lease_id'] for row in released}==set(plan['RGB_groups']) and
        all(row['RGB_present'] is False and row['canonical_files_retained'] is True and row['old_success_files_deleted']==0
            for row in released),'Natural first-acceptance/lease-release lifecycle is incomplete')
    require(len(plan['sources'])==426 and plan['window_count']==521 and plan['event_count']==665 and
        plan['nominal_requests']==1995 and len(plan['requests'])==1995 and
        len(set(plan['consumers']))==len(plan['consumers']) and
        set(production['actual_unique_MODEL_ids'])==set(plan['consumers']) and
        len(production['actual_unique_MODEL_ids'])==len(plan['consumers']) and
        set(production['structural_unknown_request_ids'])==set(plan['structural_unknown_requests']),
        'Full426/521/665/1995 and actual-versus-structural request denominator differs')
    require({row['request_id'] for row in plan['requests'] if row['execution']=='MODEL'}==set(plan['consumers']) and
        {row['request_id'] for row in plan['requests'] if row['execution']!='MODEL'}==set(plan['structural_unknown_requests']) and
        len({row['request_id'] for row in plan['requests']})==1995,
        'Nominal requests must partition into unique actual MODEL and predeclared structural IDs')
    selection=production['frozen_development_selection_ref'];selected=closure.load(selection)
    require(selection==input_reg['selected_uniform_development_role_ref']==runtime['selected_uniform_development_role_ref'] and
        production['global_refiner_role']==selected['global_refiner_role']==input_reg['endpoint_model_role'] and
        production['global_VERIFY_role']==selected['global_VERIFY_role']==input_reg['verify_model_role']=='TIME_ENABLED',
        'Actual uniform pre-result development model role differs')
    require(set(production['native_clock_original_bindings'])==set(production['actual_source_ids'])=={str(i) for i in range(426)},
        'Complete new-native/original source identities required')
    seven=('original_clock_ref','new_clock_ref','source_CPU_completion_ref','independent_equality_ref',
        'packet_terminal_observation_ref','packet_registration_ref','packet_completion_ref')
    for bindings in production['native_clock_original_bindings'].values():
        require(bindings['old_FAIL_promoted_to_PASS'] is False,'An old failure cannot be promoted')
        for key in seven:closure.load(bindings[key])
        validate_producer(closure,bindings,production,continuation,INPUT)
    proofs=production['actual_unique_MODEL_proofs']
    require(len(proofs)==len(plan['consumers']) and {row['consumer'] for row in proofs}==set(plan['consumers']),
        'Missing/repeated independent MODEL acceptance proof')
    retained_keys={'request','raw','done','CPU_input_proof','GPU_input','first_independent_input_replay',
        'model_identity','weights_terminal','activation_before','activation_inside','activation_after',
        'batch_completion','complete_global_request_source_lock','natural_terminal_origin_binding'}
    for row in proofs:
        proof=closure.load(row['first_independent_replay_ref'])
        require(proof['status']=='PASS_FIRST_INDEPENDENT_REPLAY' and proof['consumer']==row['consumer'] and
            proof['global_graph_sha256']==plan_sha and proof['actual_weight_identity_verified'] is True and
            proof['normal_processor_from_original_RGB_verified'] is True and
            proof['output_token_decode_grammar_parser_native_verified'] is True and
            retained_keys<=set(proof['retained_evidence_refs']), 'First real independent input/output/model proof incomplete')
        manifest=closure.load(proof['input_manifest_ref'])
        for key in ('private_ref','visual_ref'):
            if manifest[key]:closure.add(manifest[key],body=False)
        closure.add(row['resource_ref']);closure.add(row['ledger_ref'])
    structural=production['structural_unknown_without_model_call_proofs']
    require(len(structural)==len(plan['structural_unknown_requests']) and
        {row['request_id'] for row in structural}==set(plan['structural_unknown_requests']),
        'Complete predeclared structural proof denominator required')
    for row in structural:
        proof=closure.load(row['proof_ref'])
        require(proof['actual_model_call'] is False and proof['new_model_calls']==0 and
            proof['raw_output_created'] is False and proof['canonical_consumer_created'] is False,
            'Structural proof cannot contain fabricated model/raw/input acceptance')
    for row in production['batch_natural_terminals']:
        resource=closure.load(row['resource_ref']);closure.load(row['closure_ref'])
        ledger=closure.add(row['ledger_ref']);records=[json.loads(line) for line in Path(ledger['path']).read_text().splitlines() if line]
        require(resource['name']==row['gpu_job_name'] and resource['status']=='completed' and
            type(resource['exit_code'])is int and resource['exit_code']==0 and
            [item for item in records if item.get('name')==resource['name']]==[resource],
            'Unique real natural resource terminal and immutable ledger differ')
    closure.load(config['production_completion_ref'])
    closure.load(config['controller_completion_ref'])
    for ref in config['additional_metadata_refs']:closure.load(ref)
    for spec in config['frozen_file_lock_specs']:
        old=closure.load(spec['receipt_ref'],walk=False);files=get_at(old,spec['files_key_path'])
        require(isinstance(files,dict) and files,'Explicit existing old model/source file-lock map required')
        for path,sha in files.items():closure.reference(dict(path=path,sha256=sha))
    legacy=config['legacy_inputs'];fields=legacy['source_field_files']
    require(set(fields)==FIELD_NAMES and fields==plan['old_spatial_field_refs']==input_reg['old_spatial_field_refs'],
        'Original continuous source-field identity differs from the frozen actual whole graph')
    for ref in fields.values():closure.add(ref,body=False) # Prior source_binding SHA; renderer performs necessary field read.
    closure.load(legacy['source_binding_ref'])
    baseline=legacy['baseline_zip']
    require(baseline['sha256']=='8aec42ae06a8cacab93aa8e052d89d5df41dc57e56d73a79cdef6dd02c6cb4ad' and
        Path(baseline['path']).resolve()==HOME/'rapid_risk_three_20261013_v1/recovery_01/control/baseline_D8.zip' and
        Path(baseline['path']).stat().st_size==368368,'Exact protected D8 ZIP metadata required; no ZIP body replay here')
    closure.add(baseline,body=False)
    for name,expected in (('metadata',RUN/'b_score_aligned_package_v4/rematch_01/metadata.json'),
        ('source_manifest',RUN/'baseline_pts_v4/scan_01/clean_manifest_v2.json')):
        require(Path(legacy[name]['path']).resolve()==expected,'Original source metadata owner differs')
        closure.load(legacy[name])
    package_code=config['package_code_refs']
    require(set(package_code)=={path.name for path in (ROOT/'code').glob('*.py')} and
        package_code['package_family.py']['sha256']==RENDERER_SHA,'All actual package code and exact renderer revision required')
    for name,ref in package_code.items():
        require(Path(ref['path']).resolve()==ROOT/'code'/name,'Package code ref escaped exact target owner');closure.add(ref)
    required={str(p.resolve()) for directory in (RUN/'b_score_aligned_package_v4',RUN/'baseline_a_pts_v1') for p in directory.glob('*.py')}
    required|={str(p.resolve()) for p in (RUN/'baseline_a_pts_v1/vendor').glob('*.py')}
    required|={str(p.resolve()) for p in (RUN/'baseline_a_pts_v1/vendor/frozen_strict_loader').rglob('*.py')}
    require(required<=set(closure.files),'Existing old source/model code, all vendor and frozen strict-loader closure incomplete')
    historical=history(closure,config['history_specs'])
    supplied=config['package_document_refs'];require(set(supplied)=={'protocol','authorization','official_rule_check'},
        'Root must supply all current frozen package protocol/authorization/rule receipts')
    protocol=closure.load(supplied['protocol'])
    require(protocol['arms']==ARMS and protocol['publication_priority']==ARMS and protocol['publication_limit']==5 and
        protocol['original_length_padding_preserved'] is True and protocol['empty_source_guard']=='PRESERVE_ORIGINAL_D8_SOURCE_SELECTION' and
        protocol['test_content_or_leaderboard_parameter_selection'] is False and protocol['quality_status']=='UNVERIFIED_EXPLICIT_RISK' and
        protocol['scientific_quality_claim'] is False and protocol['new_source_context_only_on_applied_changed_REFINE_side'] is True,
        'Root prospective eight-arm family/risk protocol differs')
    closure.load(supplied['authorization']);closure.load(supplied['official_rule_check'])
    require(ROOT.is_dir() and not (ROOT/'package_admission.json').exists(),'Admission must remain absent during technical binding')
    for name,ref in supplied.items():closure.copy_document(ref,ROOT/(name+'.json'))
    save(ROOT/'history.json',historical);history_ref=dict(path=str(ROOT/'history.json'),sha256=file_sha(ROOT/'history.json'));closure.add(history_ref)
    inputs={name:production['accepted_export_refs'][name] for name in ('events','endpoints','verification','source_clocks')}
    inputs.update({name:legacy[name] for name in ('baseline_zip','metadata','source_manifest')},history=history_ref,
        production_completion=config['production_completion_ref'],development_selection=selection,source_field_files=fields)
    for ref in production['accepted_export_refs'].values():closure.load(ref)
    save(ROOT/'package_inputs.json',inputs);closure.add(dict(path=str(ROOT/'package_inputs.json'),sha256=file_sha(ROOT/'package_inputs.json')))
    receipt=dict(status='TECHNICAL_PACKAGE_BINDINGS_READY_NO_ADMISSION_NO_ZIP_NO_QUALITY_CLAIM',
        finished_utc=dt.datetime.now(dt.timezone.utc).isoformat(),config_ref=config_ref,
        production_completion_ref=config['production_completion_ref'],controller_completion_ref=config['controller_completion_ref'],
        package_inputs_ref=dict(path=str(ROOT/'package_inputs.json'),sha256=file_sha(ROOT/'package_inputs.json')),
        history_ref=history_ref,source_count=426,window_count=521,event_count=665,nominal_requests=1995,
        actual_MODEL_proofs=len(proofs),structural_no_MODEL_proofs=len(structural),original_clock_binding_roles=list(seven),
        historical_receipt_rows=len(historical),physical_model_parameters=PARAMETERS,
        payloads_not_rehashed_by_binder=len(closure.deferred_payloads),released_RGB_provenance_refs=len(closure.released_RGB),
        media_body_reads=0,tensor_loads=0,source_decodes=0,processor_calls=0,model_calls=0,package_calls=0,new_ZIPs=0,
        package_admission_created=False,final_main_risk_rule_admission_required=True,scientific_quality_claim=False,
        controlled_stop_is_not_failed_or_natural_completion=True,
        original_control_registration_ref=control['original_control_registration_ref'],
        quiescent_handoff_ref=control['quiescent_handoff_ref'],old_successful_operations_repeated=0,
        old_success_files_or_failed_gates_modified=False,
        old_control6_failure_ref=controller['old_control6_failure_ref'],
        old_control6_journal_ref=controller['old_control6_journal_ref'],
        recovery_registration_ref=controller['recovery_registration_ref'],
        aggregate_natural_terminal_ref=controller['aggregate_natural_terminal_ref'],
        actual_new_model_calls_in_recovery=0,actual_first_QA_calls_in_recovery=0,
        old_control6_failure_not_reclassified=True)
    save(ROOT/'technical_preparation_receipt.json',receipt)
    closure.add(dict(path=str(ROOT/'technical_preparation_receipt.json'),sha256=file_sha(ROOT/'technical_preparation_receipt.json')))
    save(ROOT/'source_package_lock.json',dict(schema='TEMPORAL_FAMILY_PACKAGE_COMPLETE_EXISTING_EVIDENCE_LOCK_V1',
        files=closure.files,existing_accepted_payload_digests_deferred_to_renderer=closure.deferred_payloads,
        released_RGB_historical_refs=closure.released_RGB,provenance_only_not_active_file_refs=closure.provenance_only,
        package_admission_created=False,old_successes_reexecuted=False))
    print(json.dumps({'status':receipt['status'],'package_root':str(ROOT),'locked_files':len(closure.files),
        'source_package_lock_sha256':file_sha(ROOT/'source_package_lock.json'),'new_ZIPs':0}))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--config',type=Path,required=True);args=parser.parse_args()
    os.environ['CUDA_VISIBLE_DEVICES']='';bind(args.config)
