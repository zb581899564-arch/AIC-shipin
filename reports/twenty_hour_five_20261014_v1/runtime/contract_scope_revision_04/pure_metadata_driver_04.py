"""Linux in-memory scope rejection checks; no plan/source/processor/model."""
import ast
import base64
import copy
import hashlib
import json
import sys
import types

payload = json.loads(base64.b64decode(sys.stdin.buffer.readline()))
sources, old = payload['new_code'], payload['v2_code']
trees = {name:ast.parse(code) for name,code in sources.items()}
oldtrees = {name:ast.parse(code) for name,code in old.items()}
def functions(tree):
    return {node.name:ast.dump(node, include_attributes=False) for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
if functions(trees['lb_contract.py']) != functions(oldtrees['lb_contract.py']):
    raise ValueError('Revision03 contract math/prompt/UNKNOWN/end functions changed')
for name, funcnames in {'prepare_local_inputs.py':['continuity'],
                        'replay_local_boundaries.py':['independent_endpoint'],
                        'lb_io.py':['save_tensor_cache','load_tensor_cache']}.items():
    newfunctions, oldfunctions = functions(trees[name]), functions(oldtrees[name])
    if any(newfunctions[name] != oldfunctions[name] for name in funcnames):
        raise ValueError('Frozen revision03 continuity/replay/gzip function changed')
for name in ('lb_contract', 'lb_io', 'plan_local_inputs'):
    module = types.ModuleType(name)
    module.__file__ = '/memory_only_local_boundary_v3/'+name+'.py'
    sys.modules[name] = module
    exec(compile(sources[name+'.py'], module.__file__, 'exec'), module.__dict__)
contract, io, planner = (sys.modules[name] for name in ('lb_contract','lb_io','plan_local_inputs'))
extractpath, selectpath = str(io.EXPECTED_BASE/'confirmation_extraction.json'), str(io.EXPECTED_BASE/'development_selection.json')
def registration(scope, count):
    confirm = scope == 'EXTERNAL_CONFIRMATION_DIAGNOSTIC'
    reg = dict(schema=contract.SCHEMA, contract_revision=contract.CONTRACT_REVISION,
        status=planner.REGISTRATION_STATUS, validation_scope=scope,
        source_scope='EXTERNAL_NONTEST_CONFIRMATION_ONLY' if confirm else 'EXTERNAL_NONTEST_DEVELOPMENT_ONLY',
        events=[{'event_id':'PURE_'+str(i)} for i in range(count)],
        selection_frozen_before_new_model_results=True,
        existing_sources_are_exposed_development_not_new_confirmation=not confirm,
        half_window_exact='3', frames_per_request=64, endpoint_sides=['start','end'],
        actual_model_call_budget=count*2, download_media=False, training=False,
        official_rule_check_sha256='a'*64, protocol_sha256='b'*64,
        confirmation_event_extraction_frozen_before_development_results=True,
        confirmation_event_extraction_path=extractpath, confirmation_event_extraction_sha256='c'*64,
        required_files={extractpath:'c'*64})
    if confirm:
        reg.update(development_selection_path=selectpath, development_selection_sha256='d'*64,
            confirmation_metrics_sealed_until_development_selection_frozen=True)
        reg['required_files'][selectpath] = 'd'*64
    return reg
accepted = 0
for scope, count in [('ONE_EVENT_INTERFACE_SMOKE',1), ('EXTERNAL_DEVELOPMENT_DIAGNOSTIC',10),
                     ('EXTERNAL_DEVELOPMENT_DIAGNOSTIC',20), ('EXTERNAL_CONFIRMATION_DIAGNOSTIC',10),
                     ('EXTERNAL_CONFIRMATION_DIAGNOSTIC',20)]:
    reg = registration(scope, count)
    info = planner.scope_metadata(reg)
    meta = dict(source_path=str(io.CHARADES_MEDIA_ROOTS[1]/'media_01'/'PURE'/'PURE.mp4'),
                source_role=info['required_source_role'], source_id='PURE', source_name='PURE', source_group='Charades:PURE')
    planner.event_scope_metadata(meta, info)
    accepted += 1
rejected = []
def reject(name, action):
    try:
        action()
    except ValueError:
        rejected.append(name)
    else:
        raise ValueError('Metadata scope wrongly accepted: '+name)
for scope in ('EXTERNAL_DEVELOPMENT_DIAGNOSTIC','EXTERNAL_CONFIRMATION_DIAGNOSTIC'):
    for count in (9,21):
        reject(scope+'_'+str(count), lambda scope=scope,count=count: planner.scope_metadata(registration(scope,count)))
for scope, flag in [('EXTERNAL_DEVELOPMENT_DIAGNOSTIC',False), ('EXTERNAL_CONFIRMATION_DIAGNOSTIC',True)]:
    reg = registration(scope,10)
    reg['existing_sources_are_exposed_development_not_new_confirmation'] = flag
    reject(scope+'_EXPOSURE', lambda reg=reg: planner.scope_metadata(reg))
for field in ('development_selection_sha256','confirmation_event_extraction_sha256'):
    reg = registration('EXTERNAL_CONFIRMATION_DIAGNOSTIC',10)
    del reg[field]
    reject('MISSING_'+field, lambda reg=reg: planner.scope_metadata(reg))
for field in ('confirmation_event_extraction_frozen_before_development_results',
              'confirmation_metrics_sealed_until_development_selection_frozen'):
    reg = registration('EXTERNAL_CONFIRMATION_DIAGNOSTIC',10)
    reg[field] = False
    reject('FALSE_'+field, lambda reg=reg: planner.scope_metadata(reg))
reg = registration('EXTERNAL_CONFIRMATION_DIAGNOSTIC',10)
del reg['required_files'][selectpath]
reject('UNLOCKED_DEVELOPMENT_SELECTION', lambda: planner.scope_metadata(reg))
dev = planner.scope_metadata(registration('EXTERNAL_DEVELOPMENT_DIAGNOSTIC',10))
confirm = planner.scope_metadata(registration('EXTERNAL_CONFIRMATION_DIAGNOSTIC',10))
meta = dict(source_path=str(io.CHARADES_MEDIA_ROOTS[0]/'media_01'/'PURE'/'PURE.mp4'),
            source_role='dev', source_id='PURE', source_name='PURE', source_group='Charades:PURE')
reject('OLD_DEV_RELABEL_AS_CONFIRM', lambda: planner.event_scope_metadata(meta,confirm))
wrong = dict(meta, source_role='confirm')
reject('CONFIRM_IN_DEVELOPMENT', lambda: planner.event_scope_metadata(wrong,dev))
wrong = dict(meta, source_role='confirm', source_path=str(io.LEGACY_EXTERNAL_ROOTS[0]/'media'/'PURE.mp4'))
reject('SUMME_NOT_NEW_CONFIRM', lambda: planner.event_scope_metadata(wrong,confirm))
wrong = dict(meta, source_role='confirm', source_path=str(io.COARSE_RECEIPT_ROOT/'gpu_01'/'raw.json'))
reject('COARSE_RAW_NOT_MEDIA', lambda: planner.event_scope_metadata(wrong,confirm))
if any(io.COARSE_RECEIPT_ROOT == root for root in io.MEDIA_ROOTS):
    raise ValueError('Coarse receipt root leaked into media roots')
reject('V2_OUTPUT_ROOT', lambda: io.base_path(io.ROOT/'twenty_hour_five_20261014_v1/local_boundary_v2'))
if io.base_path(io.EXPECTED_BASE) != io.EXPECTED_BASE:
    raise ValueError('Independent v3 output root failed')
print(json.dumps(dict(status='PASS_V3_SCOPE_METADATA_REJECTION_AND_REVISION03_FUNCTION_IDENTITY_ONLY',
    syntax_files=len(sources), accepted_scope_cases=accepted, rejected_metadata_cases=rejected,
    contract_math_prompt_unknown_exclusive_end_functions_unchanged=True,
    continuity_independent_replay_gzip_functions_unchanged=True,
    coarse_evidence_root_excluded_from_media=True, old_successful_smoke_not_repeated=True,
    no_reference_or_coarse_answers_read=True, real_plan_calls=0, media_reads=0, processor_calls=0, model_calls=0,
    deployed=False, code_files={name:dict(bytes=len(code.encode()),sha256=hashlib.sha256(code.encode()).hexdigest())
                               for name,code in sources.items()})))
