"""New runtime protocol/reader; frozen input/cache libraries remain untouched."""
import ast
import datetime as dt
from fractions import Fraction as F
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import socket
import sys

import pr_contract as c

HOME=Path('/home/inspur/aic_video_work')
CAMPAIGN=HOME/'twenty_hour_five_20261014_v1'
BASE=CAMPAIGN/'temporal_production_runtime_v3'
INPUT_ROOT=None # Explicit protocol field only; never silently use an old input root.
RUN=HOME/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'


def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(8<<20),b''):h.update(block)
    return h.hexdigest()


def utc():return dt.datetime.now(dt.timezone.utc).isoformat()


def save(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8') as f:json.dump(value,f,indent=2,allow_nan=False);f.flush();os.fsync(f.fileno())


def append(path,value):
    with Path(path).open('a',encoding='utf-8') as f:
        f.write(json.dumps(value,separators=(',',':'),allow_nan=False)+'\n');f.flush();os.fsync(f.fileno())


def host(cpu):
    c.require(socket.gethostname()=='inspur-NP5570M5' and sys.platform=='linux','Linux computation required')
    c.require((os.environ.get('CUDA_VISIBLE_DEVICES')=='') if cpu else bool(os.environ.get('CUDA_VISIBLE_DEVICES')),
              'CPU child hides only own CUDA; GPU parent must have nonempty CUDA')


def bound(ref,roots):
    path=Path(ref['path']).resolve()
    c.require(any(path.is_relative_to(Path(root).resolve()) for root in roots) and path.is_file() and sha(path)==ref['sha256'],
              'Frozen path/SHA changed or escaped its exact root')
    return path


def module(name,path,package=False):
    path=Path(path).resolve()
    if name in sys.modules:
        c.require(Path(sys.modules[name].__file__).resolve()==path,'Frozen import namespace shadowed');return sys.modules[name]
    spec=importlib.util.spec_from_file_location(name,path,submodule_search_locations=[str(path.parent)] if package else None)
    result=importlib.util.module_from_spec(spec);sys.modules[name]=result;spec.loader.exec_module(result);return result


def libraries(protocol):
    input_dir=Path(protocol['input_library_directory']).resolve()
    c.require(input_dir==INPUT_ROOT/'code','Frozen input library directory required')
    for name in ('tp_io.py','tp_contract.py','tp_device.py','consumer_api.py','replay_input.py'):
        path=input_dir/name;c.require(protocol['required_code_files'].get(str(path))==sha(path),'Input ABI file SHA missing')
    sys.path.insert(0,str(input_dir))
    inputs=module('tp_io',input_dir/'tp_io.py')
    consumer=module('_pr_inputs_consumer',input_dir/'consumer_api.py')
    input_contract=module('tp_contract',input_dir/'tp_contract.py')
    input_reg=inputs.registration(bound(protocol['input_registration_ref'],(INPUT_ROOT,)))
    frozen=inputs.libraries(input_reg)
    boundary_dir=Path(input_reg['boundary_library_directory']);verify_dir=Path(input_reg['verify_library_directory'])
    for name,value in (('lb_contract',frozen['boundary']),('cv_contract',frozen['verify'])):
        if name in sys.modules:c.require(Path(sys.modules[name].__file__).resolve()==Path(value.__file__).resolve(),'Frozen grammar dependency shadowed')
        else:sys.modules[name]=value
    for directory,name in ((boundary_dir,'lb_grammar.py'),(boundary_dir,'replay_local_boundaries.py'),(verify_dir,'cv_grammar.py')):
        path=directory/name;c.require(protocol['required_code_files'].get(str(path))==sha(path),'Output grammar/native replay SHA absent')
    boundary_grammar=module('_pr_boundary_grammar',boundary_dir/'lb_grammar.py')
    verify_grammar=module('_pr_verify_grammar',verify_dir/'cv_grammar.py')
    replay_node=next(n for n in ast.parse((boundary_dir/'replay_local_boundaries.py').read_text()).body
                    if isinstance(n,ast.FunctionDef) and n.name=='independent_endpoint')
    from bisect import bisect_left
    scope=dict(F=F,bisect_left=bisect_left,json=json,response_strings=frozen['boundary'].response_strings)
    exec(compile(ast.Module(body=[replay_node],type_ignores=[]),str(boundary_dir/'replay_local_boundaries.py'),'exec'),scope)
    oldio=module('_pr_original_b_io',boundary_dir/'lb_io.py')
    return dict(inputs=inputs,consumer=consumer,input_contract=input_contract,input_reg=input_reg,
        frozen=frozen,boundary_grammar=boundary_grammar,verify_grammar=verify_grammar,
        independent_endpoint=scope['independent_endpoint'],oldio=oldio)


def load(path,batch_id,require_admission=True):
    global INPUT_ROOT
    path=Path(path).resolve();c.require(path.is_relative_to(BASE),'New runtime protocol root only')
    protocol=read(path)
    requested=Path(protocol['input_root']).resolve()
    c.require(requested.parent==CAMPAIGN and requested.name=='temporal_production_inputs_v3',
              'Explicit registered production input version/root required')
    c.require(INPUT_ROOT is None or INPUT_ROOT==requested,'Input version cannot change in a live runtime process')
    INPUT_ROOT=requested
    c.require(protocol['schema']==c.SCHEMA and protocol['training'] is False and protocol['test_GT_read'] is False and
        protocol['old_successful_outputs_modified'] is False and protocol['algorithm_and_uniform_roles_frozen_before_production'] is True and
        protocol['weight_check_strategy']==c.WEIGHT_STRATEGY and protocol['actual_physical_parameters']==c.PARAMETERS and
        protocol['optimizer_updates']==0 and protocol['natural_terminal_per_batch_before_RGB_release'] is True,
        'Explicit pre-production batch/model/retention protocol required')
    c.require(protocol['native_terminal_scope']=='NEW_PYAV17_READER_NATIVE_TERMINAL_SCOPE' and
        protocol['dual_coordinate_application']=='LEGACY_RECIPE_KEEP_UNKNOWN_NATIVE_CUT_ONLY_MOVED_REFINE',
        'New native terminal / dual-coordinate application contract required')
    for filename,digest in protocol['required_code_files'].items():c.require(sha(filename)==digest,'Protocol code/library changed')
    for filename in Path(__file__).parent.glob('*.py'):
        c.require(protocol['required_code_files'].get(str(filename.resolve()))==sha(filename),'Every runtime file must be frozen')
    lib=libraries(protocol);reg=lib['input_reg']
    c.require(protocol['endpoint_model_role']==reg['endpoint_model_role'] and protocol['verify_model_role']==reg['verify_model_role']=='TIME_ENABLED' and
              protocol['selected_uniform_development_role_ref']==reg['selected_uniform_development_role_ref'],'Uniform development role selection differs')
    lib['inputs'].actual_permission(reg)
    plan_path=bound(protocol['full_plan_ref'],(INPUT_ROOT,));plan=read(plan_path)
    source_projection=c.source_video_projection(plan)
    init=read(bound(protocol['cache_initialization_ref'],(INPUT_ROOT,)))
    c.require(init['whole_plan_sha256']==protocol['full_plan_ref']['sha256'] and init['cache_root']==reg['cache_root'] and
        init['control_registration_sha256']==reg['_registration_sha256'] and init['control_registration_path']==reg['_registration_path'],
        'Original global request/input/control graph changed')
    store=lib['frozen']['cache'].LeaseStore(reg['cache_root'])
    c.require(store.frozen_ref==init['frozen_consumers_ref'] and sha(Path(reg['cache_root'])/'policy.json')==init['policy_sha256'],
        'Permanent full consumer table/cache policy changed')
    graph_ref=protocol['cache_global_request_lock_ref'];graph=read(store.checked_ref(graph_ref))
    c.require(graph['whole_plan_sha256']==protocol['full_plan_ref']['sha256'] and graph['all_requests']==plan['requests'] and
              graph['all_consumers']==plan['consumers'],'Cache permanent global source/request graph changed')
    batch_path=BASE/'batches'/(c.safe_id(batch_id)+'.json');batch=read(batch_path)
    c.require(batch['schema']==c.SCHEMA and batch['batch_id']==batch_id and batch['global_graph_sha256']==protocol['full_plan_ref']['sha256'] and
              batch['protocol_sha256']==sha(path),'Batch/global protocol SHA changed')
    rows=c.batch_membership(batch,plan)
    c.require(batch['capacity_receipt_ref'] and batch['global_source_order_sha256']==c.digest([s['source_id'] for s in plan['sources']]),
              'Pre-call actual capacity and original source order witness needed')
    bound(batch['capacity_receipt_ref'],(BASE,INPUT_ROOT))
    root=BASE/'runs'/batch_id
    if require_admission:
        permit_path=root/'gpu_admission.json';permit=read(permit_path)
        c.require(permit['status']=='PASS_INDEPENDENT_PRODUCTION_BATCH_GPU_ADMISSION' and permit['protocol_sha256']==sha(path) and
            permit['batch_sha256']==sha(batch_path) and permit['global_graph_sha256']==protocol['full_plan_ref']['sha256'] and
            permit['batch_CPU_admission_sha256']==sha(root/'CPU_admission.json') and
            permit['input_admission_sha256']==sha(root/'input_admission.json') and
            permit['actual_model_call_budget']==len(batch['request_ids']) and permit['gpu_job_name']==batch['gpu_job_name'] and
            permit['actual_physical_parameters']==c.PARAMETERS and permit['optimizer_updates']==0,
            'Main independent unique batch GPU admission is missing/changed')
    return dict(protocol=protocol,protocol_path=path,batch=batch,batch_path=batch_path,rows=rows,plan=plan,lib=lib,
        store=store,root=root,init=init,graph_ref=graph_ref,source_video_projection=source_projection)


def CPU_acceptance(context):
    """All source consumers of this capacity batch must be ready before model load."""
    batch=context['batch'];store=context['store'];root=context['root']
    admission=read(root/'CPU_admission.json')
    c.require(admission['status']=='PASS_INDEPENDENT_COMPLETE_BATCH_CPU_INPUTS' and admission['batch_sha256']==sha(context['batch_path']) and
        admission['global_graph_sha256']==context['protocol']['full_plan_ref']['sha256'] and
        admission['source_ids']==batch['source_ids'] and admission['request_ids']==batch['request_ids'],
        'Complete exact batch CPU/source acceptance missing')
    sources={s['source_id']:s for s in context['plan']['sources']};refs={};accepted={}
    for sid in batch['source_ids']:
        ref=admission['source_completion_refs'][sid];complete=read(store.checked_ref(ref))
        c.require(complete['status']=='PASS_COMPLETE_SOURCE_NEW_INPUTS_NOT_GPU_OR_QUALITY' and complete['source_id']==sid and
            complete['new_native_RGB_materialization_decodes']==1 and complete['new_model_calls']==0 and
            complete['actual_new_processor_encodes']==len(complete['consumers']), 'Source new native CPU completion differs')
        expected=[row['request_id'] for row in context['rows'] if row['source_id']==sid and row['execution']=='MODEL']
        c.require([row['consumer'] for row in complete['consumers']]==expected,'Batch split or omitted a source consumer')
        for entry in complete['consumers']:
            rid=entry['consumer'];c.require(rid not in accepted,'Repeated CPU consumer')
            manifest=read(store.checked_ref(entry['input_manifest_ref']));proof=read(store.checked_ref(entry['CPU_input_proof_ref']))
            meta=manifest['original_metadata'];clock=read(store.checked_ref(meta['new_clock_ref']))['clock']
            context['lib']['input_contract'].compare_clock(sources[sid],clock)
            skeleton=next(row for row in context['rows'] if row['request_id']==rid)
            want=context['lib']['input_contract'].materialized_request(sources[sid],skeleton,clock,
                context['lib']['frozen']['boundary'],context['lib']['frozen']['continuity'],context['lib']['frozen']['verify'],clock['native_duration_by_ordinal'])
            c.require(all(meta.get(key)==value for key,value in want.items()),'Exact source/event/prompt/native request identity differs')
            c.require(manifest['consumer']==proof['consumer']==rid and proof['input_manifest_ref']==entry['input_manifest_ref'] and
                proof['full_input_signature']==manifest['full_signature'] and proof['CPU_only'] is True and
                proof['actual_new_processor_encodes']==1 and proof['new_model_calls']==0 and
                proof['processor_runtime_identity']['original_config_sha256']==context['protocol']['original_B_config_sha256'],
                'Canonical CPU proof/source/original B config binding differs')
            accepted[rid]=dict(entry=entry,manifest=manifest,proof=proof,meta=meta,clock=clock)
        refs[sid]=ref
    c.require(list(accepted)==batch['request_ids'],'Complete actual batch input denominator/order differs')
    return accepted,dict(path=str(root/'CPU_admission.json'),sha256=sha(root/'CPU_admission.json'))
