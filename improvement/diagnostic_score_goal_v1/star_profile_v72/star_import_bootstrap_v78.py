"""Fresh CPU import preflight, then exec ONE unchanged registered73/74 stage.

Standalone stdlib bootstrap: no project imports or business work on import.
Only three explicitly bound dependency parents enter child PYTHONPATH.
"""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import traceback

WORK=Path('/home/inspur/aic_video_work')
DEADLINE='2026-10-18T03:22:24Z'
CODEDIR='star_profile_code_72/star_profile_v72'
EXTERNAL=('reference_screen','CPU_resized20','GPU_resized20','reference_confirm','CPU_resized19','GPU_resized19')
PRODUCTION=('CPU_pilot32','CPU_remaining','GPU_production','package')
ROLES=('pair_common','geometry31','math55','image31','frozen55')
PATH_ROLES=('pair_common','geometry31','math55')
IMPORT_ROLES=('pair_common','geometry31','math55','image31')


def require(value,message):
    if not value:raise ValueError(message)


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for part in iter(lambda:f.read(8<<20),b''):h.update(part)
    return h.hexdigest()


def reference(path):return dict(path=str(Path(path).resolve()),sha256=sha(path))


def bound(r,root=WORK):
    require(isinstance(r,dict) and set(r)=={'path','sha256'},'Explicit immutable file reference')
    p=Path(r['path']).resolve()
    require(p.is_relative_to(Path(root).resolve()) and p.is_file() and sha(p)==r['sha256'],'Bound file identity changed or outside authorized root: '+str(p))
    return p


def read(path):return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def save(path,value):
    with Path(path).open('x',encoding='utf-8') as f:
        json.dump(value,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())


def dependency_plan(reg,sources):
    """Pure exact source-field projection; do not infer names or search paths."""
    cpu,gpu,old=sources['CPU68'],sources['GPU69'],sources['GPU55']
    require(cpu['schema']=='UTILITY_CONNECTED_STAR_CPU_V68' and gpu['schema']=='UTILITY_CONNECTED_STAR_CONTINUATION_V69',
        'Actual frozen68/69 dependency sources required')
    require(old['GPU_code']==gpu['frozen_GPU55_code']
        and Path(old['GPU_code']['path']).parent.resolve()==Path(old['math_code']['path']).parent.resolve(),
        'Frozen55 dynamic helper inserts its own parent; actual math must share that registered directory')
    expected=dict(pair_common=cpu['helper_code'],geometry31=cpu['geometry_code'],math55=old['math_code'],
        image31=gpu['image_code'],frozen55=gpu['frozen_GPU55_code'])
    modules=reg['modules'];require(isinstance(modules,list) and len(modules)==len(ROLES)
        and {m['role'] for m in modules}==set(ROLES),'Exactly the reviewed five role bindings')
    byrole={m['role']:m for m in modules};names=[];directories=[]
    for role in ROLES:
        m=byrole[role];name=m['module_name'];p=Path(m['reference']['path'])
        require(re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]*',name) is not None and p.suffix=='.py' and p.stem==name
            and m['reference']==expected[role],'Explicit module name/stem and actual registered source ref differ: '+role)
        names.append(name)
        if role in PATH_ROLES:
            directory=str(p.parent.resolve())
            if directory not in directories:directories.append(directory)
    require(len(names)==len(set(names)),'No same-name module-role ambiguity')
    require(byrole['pair_common']['module_name']=='pair_common'
        and byrole['geometry31']['module_name']=='crop_geometry_v31'
        and byrole['image31']['module_name']=='crop_image_input_v31','Reviewed CPU dependency module names')
    return dict(modules=[byrole[r] for r in ROLES],pythonpath=directories,
        imported_roles=list(IMPORT_ROLES),resolve_only_roles=['frozen55'])


def child_environment(plan,stage=False):
    env=dict(os.environ,PYTHONPATH=os.pathsep.join(plan['pythonpath']),PYTHONSAFEPATH='1',
        PYTHONDONTWRITEBYTECODE='1',CUDA_VISIBLE_DEVICES='0' if stage else '',
        OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
    return env


CHILD=r'''
import hashlib,importlib,importlib.util,json,os,pathlib,sys
plan=json.loads(sys.argv[1]); result=[]
blocked={'.pt','.safetensors','.npy','.npz','.mp4','.mov','.jpg','.jpeg','.png','.webp','.jsonl'}
def audit(event,args):
    if event in ('socket.connect','socket.connect_ex','subprocess.Popen'):
        raise RuntimeError('Import preflight forbids network and child processes')
    if event=='open' and args and isinstance(args[0],(str,bytes,os.PathLike)):
        p=pathlib.Path(os.fsdecode(args[0]))
        if p.suffix.lower() in blocked:raise RuntimeError('Import preflight forbids model/tensor/media/target artifact reads: '+str(p))
sys.addaudithook(audit)
def digest(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
for m in plan['modules']:
    p=pathlib.Path(m['reference']['path']).resolve();name=m['module_name'];role=m['role']
    if digest(p)!=m['reference']['sha256']:raise RuntimeError('Changed code before fresh import: '+name)
    if role in ('pair_common','geometry31','math55'):
        spec=importlib.util.find_spec(name)
        if spec is None or pathlib.Path(spec.origin).resolve()!=p:raise RuntimeError('Same-name import resolves to wrong file: '+name)
        for directory in plan['pythonpath']:
            candidate=pathlib.Path(directory)/(name+'.py')
            if candidate.is_file() and candidate.resolve()!=p:raise RuntimeError('Conflicting same-name file in bound dependency parents: '+str(candidate))
        resolution='PYTHONPATH_FIND_SPEC'
    else:
        existing=sys.modules.get(name)
        if existing is not None and pathlib.Path(existing.__file__).resolve()!=p:raise RuntimeError('Wrong existing module owner: '+name)
        spec=importlib.util.spec_from_file_location(name,p);resolution='BOUND_FILE_SPEC'
    if spec is None or pathlib.Path(spec.origin).resolve()!=p:raise RuntimeError('Wrong bound spec origin: '+name)
    executed=role in plan['imported_roles']
    if executed:
        if role in ('pair_common','geometry31','math55'):module=importlib.import_module(name)
        else:
            module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module)
        if pathlib.Path(module.__file__).resolve()!=p:raise RuntimeError('Executed module owner changed: '+name)
    elif name in sys.modules:raise RuntimeError('Resolve-only frozen GPU helper was unexpectedly executed: '+name)
    if digest(p)!=m['reference']['sha256']:raise RuntimeError('Code changed during fresh import: '+name)
    result.append(dict(role=role,module_name=name,origin=str(p),sha256=m['reference']['sha256'],executed=executed,resolution=resolution))
if 'transformers' in sys.modules or 'peft' in sys.modules:raise RuntimeError('CPU code-only preflight imported model frameworks')
torch=sys.modules.get('torch')
if torch is not None and torch.cuda.is_initialized():raise RuntimeError('CPU import initialized CUDA')
print('STAR78_IMPORT_PREFLIGHT_JSON='+json.dumps(dict(status='PASS_FRESH_CPU_IMPORT_BINDINGS_ONLY_NOT_INPUT_QA',modules=result,
    pythonpath=plan['pythonpath'],CUDA_VISIBLE_DEVICES=os.environ.get('CUDA_VISIBLE_DEVICES'),cuda_initialized=False,
    model_calls=0,pixel_tensor_target_reads=0,quality_established=False,frozen_GPU_helper_executed=False),sort_keys=True),flush=True)
'''


def fresh_preflight(plan,*,cwd,python=sys.executable):
    completed=subprocess.run([python,'-B','-c',CHILD,json.dumps(plan,allow_nan=False)],cwd=cwd,
        env=child_environment(plan),stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=120)
    require(completed.returncode==0,'Fresh import preflight failed: '+completed.stderr[-6000:])
    lines=[line[len('STAR78_IMPORT_PREFLIGHT_JSON='):] for line in completed.stdout.splitlines() if line.startswith('STAR78_IMPORT_PREFLIGHT_JSON=')]
    require(len(lines)==1,'One actual fresh import result required')
    value=json.loads(lines[0]);require(value['status']=='PASS_FRESH_CPU_IMPORT_BINDINGS_ONLY_NOT_INPUT_QA','Actual code-only import result')
    return value


def validate_registration(root,rp):
    root=Path(root).resolve();rp=Path(rp).resolve()
    require(rp.is_relative_to(root) and rp.is_file(),'Explicit dependency registration inside ROOT')
    reg=read(rp);require(reg['schema']=='STAR_MINIMAL_BOUND_IMPORT_BOOTSTRAP_V78'
        and reg['deadline_utc']==DEADLINE and bound(reg['bootstrap_code'])==Path(__file__).resolve(),
        'Exact78 bootstrap registration and unchanged Goal deadline')
    require(bound(reg['deployment_receipt'])==(root/'star_conditional_code_deployment_72.json').resolve(), 'Exact original frozen72 deployment receipt')
    deployment=read(bound(reg['deployment_receipt']))
    require(deployment['status']=='STAR72_CODE_READY_NO_REAL_SCOPE_ADMITTED' and deployment['actual_test_exit_code']==0
        and Path(deployment['code_directory']).resolve()==(root/CODEDIR).resolve(),'Actual tested frozen72 deployment')
    for name,entry in deployment['members'].items():
        require(name.startswith('star_profile_v72/') and '/' not in name[len('star_profile_v72/'):],'Exact original72 member namespace')
        p=root/'star_profile_code_72'/name
        require(p.stat().st_size==entry['size'] and sha(p)==entry['sha256'],'Changed frozen72 member: '+name)
    for key,name in (('stage73_code','star_register_stage_v73.py'),('production74_code','star_register_production_v74.py')):
        require(bound(reg[key])==(root/CODEDIR/name).resolve(),'Exact unchanged registered stage entrypoint: '+key)
    refs=reg['source_registrations'];require(set(refs)=={'CPU68','GPU69','GPU55'},'Only exact three source registrations')
    require(bound(refs['CPU68'])==(root/'utility_star_CPU_registration_68.json').resolve()
        and bound(refs['GPU69'])==(root/'utility_star_GPU_registration_69.json').resolve(),'Explicit original68/69 sources')
    sources={k:read(bound(v)) for k,v in refs.items()}
    require(sources['GPU69']['CPU_registration']==refs['CPU68'] and sources['GPU69']['original_GPU55']==refs['GPU55'],
        'Actual69→68/55 dependency ownership')
    plan=dependency_plan(reg,sources)
    for m in plan['modules']:bound(m['reference'])
    require(Path(next(m['reference']['path'] for m in plan['modules'] if m['role']=='pair_common')).parent.resolve()==(root/'pair_code_17').resolve(),
        'Original pair_common stays in exact ROOT/pair_code_17')
    return reg,plan


def stage_command(root,stage,admission,reg):
    require(stage in EXTERNAL+PRODUCTION,'One explicit73/74 stage only')
    path=Path(admission).resolve();require(path.is_relative_to(root) and path.is_file(),'Explicit stage admission inside ROOT')
    data=read(path);key='stage73_code' if stage in EXTERNAL else 'production74_code'
    require(data['stage']==stage and data['launch_approved'] is True and data['deadline_utc']==DEADLINE
        and data['register_code']==reg[key] and data['deployment_receipt']==reg['deployment_receipt'],
        'Bootstrap cannot replace or weaken exact existing stage admission')
    if stage in PRODUCTION:require(data['stage73_code']==reg['stage73_code'],'Same exact inherited73 used by74')
    return [sys.executable,'-B','-u',str(bound(reg[key])),'--root',str(root),'--stage',stage,'--admission',str(path)]


def run(root,rp,*,phase=None,stage=None,admission=None):
    root=Path(root).resolve();require(sys.platform=='linux' and root.is_relative_to(WORK),'Authorized Linux work root only')
    require((phase=='preflight') is (stage is None),'Only preflight or one explicit stage')
    reg,plan=validate_registration(root,rp)
    require(dt.datetime.now(dt.timezone.utc)<dt.datetime.fromisoformat(DEADLINE.replace('Z','+00:00')),'Original Goal deadline')
    argv=stage_command(root,stage,admission,reg) if stage else None
    prefix='star_dependency_preflight_78' if stage is None else 'star_bootstrap_'+stage+'_78'
    output=root/(prefix+'.json');require(not output.exists() and not (root/(prefix+'_failure.json')).exists(),
        'Exclusive import evidence; preserve success/failure without implicit retry')
    try:
        value=fresh_preflight(plan,cwd=root)
        save(output,dict(value,dependency_registration=reference(rp),bootstrap_code=reg['bootstrap_code'],
            stage=stage,utc=dt.datetime.now(dt.timezone.utc).isoformat(),scientific_stage_started=False))
    except BaseException as error:
        save(root/(prefix+'_failure.json'),dict(error=repr(error),traceback=traceback.format_exc(),
            dependency_registration=reference(rp),scientific_stage_started=False,no_automatic_retry=True));raise
    if stage is None:return
    ticks=Path('/proc',str(os.getpid()),'stat').read_text().split(') ',1)[1].split()[19]
    save(root/(prefix+'_entry.json'),dict(stage=stage,bootstrap_argv=sys.argv,exec_argv=argv,pid=os.getpid(),start_ticks=ticks,
        dependency_registration=reference(rp),admission=reference(admission),preflight=reference(output),
        bootstrap_code=reg['bootstrap_code'],pythonpath=plan['pythonpath'],automatic_next_stage=False,
        science_gates_remain_in_registered73_or74=True))
    os.execve(sys.executable,argv,child_environment(plan,stage=True))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--dependencies',type=Path,required=True)
    mode=parser.add_mutually_exclusive_group(required=True);mode.add_argument('--phase',choices=['preflight'])
    mode.add_argument('--stage',choices=EXTERNAL+PRODUCTION);parser.add_argument('--admission',type=Path)
    args=parser.parse_args()
    require((args.stage is None)==(args.admission is None),'Stage requires its exact admission; preflight accepts none')
    run(args.root,args.dependencies,phase=args.phase,stage=args.stage,admission=args.admission)
