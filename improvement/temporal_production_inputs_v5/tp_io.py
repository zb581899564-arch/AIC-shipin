"""New formal-input caller IO; frozen math/cache libraries remain read-only."""
import ast
from fractions import Fraction as F
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import socket
import sys

from tp_contract import SCHEMA,require,validate_reader_scope,same_ref

HOME=Path('/home/inspur/aic_video_work')
CAMPAIGN=HOME/'twenty_hour_five_20261014_v1'
BASE=CAMPAIGN/'temporal_production_inputs_v5'
OLD_RULE_LEAF=CAMPAIGN/'temporal_production_inputs_v4/bindings/official_rules.json'
OLD_SELECTION_LEAF=CAMPAIGN/'temporal_production_inputs_v4/bindings/uniform_role_selection.json'
RUN=HOME/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
MEDIA_ROOT=RUN/'baseline_a/m0_426_02/media'


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(8<<20),b''):h.update(block)
    return h.hexdigest()


def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def save(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.flush();os.fsync(stream.fileno())


def host():
    require(socket.gethostname()=='inspur-NP5570M5' and sys.platform=='linux' and os.environ.get('CUDA_VISIBLE_DEVICES')=='',
            'Formal preparation is Linux CPU-only; parent CUDA must not be cleared')


def bound(ref,roots):
    path=Path(ref['path']).resolve()
    require(any(path.is_relative_to(Path(root).resolve()) for root in roots),'Frozen input escaped its explicit root')
    require(path.is_file() and sha(path)==ref['sha256'],'Frozen input changed: '+str(path))
    return path


def inherited_binding(ref,old_leaf):
    """Only one explicitly named old leaf; never admit the entire old root."""
    path=Path(ref['path']).resolve()
    require(path.is_relative_to(BASE) or path==old_leaf,
        'Only new-root metadata or the exact successful original binding leaf can be inherited')
    require(path.is_file() and sha(path)==ref['sha256'],'Frozen binding leaf changed: '+str(path))
    return path


def registration(path):
    path=Path(path).resolve();require(path.is_relative_to(BASE),'New control root only')
    reg=read(path)
    require(reg['schema']==SCHEMA and reg['source_scope']=='FORMAL426_AUTOMATIC_NEW_INFERENCE_INPUTS_ONLY' and
            reg['training'] is False and reg['test_GT_read'] is False and reg['old_successful_outputs_modified'] is False and
            reg['request_algorithm_frozen_before_any_new_model_results'] is True and
            reg['dual_coordinate_consumer_adapter_frozen'] is True,
            'Explicit automatic formal-input protocol required')
    for filename,digest in reg['required_code_files'].items():require(sha(filename)==digest,'Frozen code/library changed')
    for filename in Path(__file__).parent.glob('*.py'):
        require(reg['required_code_files'].get(str(filename.resolve()))==sha(filename),'Every production caller file must be frozen')
    inherited_binding(reg['official_rules_ref'],OLD_RULE_LEAF)
    scope=read(bound(reg['reader_native_terminal_scope_ref'],(BASE,)))
    validate_reader_scope(scope)
    require(same_ref(scope['packet_first_measurement_ref'],reg['packet_completion_ref']),
        'Frozen reader scope must bind the original first packet completion')
    reg['_registration_path']=str(path)
    reg['_registration_sha256']=sha(path)
    return reg


def libraries(reg,cpu=False):
    """Hash-bound imports, including exact v3 continuity function AST."""
    boundary_dir=Path(reg['boundary_library_directory']).resolve()
    verify_dir=Path(reg['verify_library_directory']).resolve()
    cache_dir=Path(reg['cache_library_directory']).resolve()
    for directory in (boundary_dir,verify_dir,cache_dir):
        require(directory.is_relative_to(CAMPAIGN),'Only independently frozen campaign libraries')
    for directory,names in ((boundary_dir,('lb_contract.py','lb_io.py','prepare_local_inputs.py')),
                             (verify_dir,('cv_contract.py',)),
                             (cache_dir,('__init__.py','codec.py','leases.py','pixel_dictionary.py'))):
        for name in names:require(reg['required_code_files'].get(str(directory/name))==sha(directory/name),'Required library SHA absent')
    def module(name,path,package=False):
        if name in sys.modules:
            require(Path(sys.modules[name].__file__).resolve()==path.resolve(),'Hash-bound library namespace shadowed')
            return sys.modules[name]
        spec=importlib.util.spec_from_file_location(name,path,submodule_search_locations=[str(path.parent)] if package else None)
        value=importlib.util.module_from_spec(spec);sys.modules[name]=value;spec.loader.exec_module(value);return value
    boundary=module('_tp_frozen_boundary',boundary_dir/'lb_contract.py')
    verify=module('_tp_frozen_verify',verify_dir/'cv_contract.py')
    cache=module('_tp_exact_cache',cache_dir/'__init__.py',True)
    tree=ast.parse((boundary_dir/'prepare_local_inputs.py').read_text())
    node=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='continuity')
    scope={'F':F,'normalized_clock':boundary.normalized_clock}
    exec(compile(ast.Module(body=[node],type_ignores=[]),str(boundary_dir/'prepare_local_inputs.py'),'exec'),scope)
    result=dict(boundary=boundary,verify=verify,cache=cache,continuity=scope['continuity'])
    if cpu:
        color,color_identity=source_conversion(reg)
        sys.path.insert(0,str(boundary_dir))
        if 'lb_contract' in sys.modules:require(Path(sys.modules['lb_contract'].__file__).resolve()==boundary_dir/'lb_contract.py','Boundary namespace shadowed')
        else:sys.modules['lb_contract']=boundary
        oldio=module('_tp_frozen_original_runtime_io',boundary_dir/'lb_io.py')
        import torch
        torch.set_num_threads(1)
        if torch.get_num_interop_threads()!=1:torch.set_num_interop_threads(1)
        runtime,processor,identity=oldio.cpu_runtime()
        require(not torch.cuda.is_initialized(),'CPU preparation initialized CUDA')
        result.update(runtime=runtime,processor=processor,runtime_identity=identity,
            source_color_converter=color,source_color_identity=color_identity)
    return result


def source_conversion_identity(reg):
    owner=RUN/'b_score_aligned_package_v4'
    refs={name:dict(path=str(owner/name),sha256=reg['required_code_files'][str(owner/name)])
        for name in ('source_color.py','common.py')}
    ref=reg['source_color_config_ref']
    require(Path(ref['path']).resolve()==owner/'config.json','Original source-color settings owner changed')
    bound(ref,(RUN,))
    for name,value in refs.items():require(sha(value['path'])==value['sha256'],'Original source-color helper changed')
    return dict(code_refs=refs,config_ref=ref,converter='UNCHANGED_SOURCE_COLOR_CONVERT_FRAME_RGB24')


def source_conversion(reg):
    """Load the unchanged original common/source_color owner without shadowing."""
    identity=source_conversion_identity(reg);owner=RUN/'b_score_aligned_package_v4'
    prior_path=list(sys.path)
    try:
        for name in ('common','source_color'):
            path=owner/(name+'.py')
            if name in sys.modules:
                require(Path(sys.modules[name].__file__).resolve()==path,'Original source-color namespace shadowed: '+name)
            else:
                spec=importlib.util.spec_from_file_location(name,path)
                module=importlib.util.module_from_spec(spec);sys.modules[name]=module
                spec.loader.exec_module(module)
            require(Path(sys.modules[name].__file__).resolve()==path,'Original source-color module owner changed')
        return sys.modules['source_color'].convert_frame,identity
    finally:
        sys.path[:]=prior_path


def metadata_permission(reg):
    require(reg['metadata_initialization_approved'] is True,'Only metadata initialization has not been approved')
    selected=inherited_binding(reg['selected_uniform_development_role_ref'],OLD_SELECTION_LEAF)
    # The signed-by-workflow frozen selection file is bound, not its quality metrics read.
    require(reg['endpoint_model_role'] in ('TIME_ENABLED','BASE_DISABLED') and reg['verify_model_role']=='TIME_ENABLED',
            'Uniform endpoint role and unchanged TIME VERIFY must be frozen before production')
    return selected


def actual_permission(reg):
    selected=metadata_permission(reg)
    require(reg['main_agent_actual_production_preparation_approved'] is True,
            'Main has not admitted actual formal decode/processor preparation')
    path=Path(reg['actual_preparation_permission_path']).resolve()
    require(path.is_relative_to(BASE) and path.is_file(),'Final root preparation permission is not present')
    value=read(path)
    require(value['status']=='APPROVED_ONCE_NEW_V5_FORMAL_SOURCE_DECODE_AND_PROCESSOR' and
        value['input_registration_path']==reg['_registration_path'] and
        value['input_registration_sha256']==reg['_registration_sha256'] and
        value['source_count']==426 and value['model_calls_authorized']==0,
        'Final source preparation permission must bind the exact frozen input registration; no GPU authority')
    scope=read(bound(reg['reader_native_terminal_scope_ref'],(BASE,)))
    validate_reader_scope(scope)
    return selected


def snapshot():
    import shutil
    mem={row.split(':')[0]:int(row.split(':')[1].split()[0])*1024 for row in Path('/proc/meminfo').read_text().splitlines() if ':' in row}
    return dict(mem_available_bytes=mem['MemAvailable'],disk_available_bytes=shutil.disk_usage(CAMPAIGN).free)
