"""Explicit color-format recovery;97 real successful inputs adopted, zero prior model calls."""
from pathlib import Path
import json
import os
import traceback
from routing_production60_common import ADMISSION,WORK,RUN,WRAPPER,ENGINEERING,SPORT,FULL_PARAMETERS,read,ref,save,checked
import routing_production60 as controller

ROOT=ADMISSION/'routing_production62';OLD=ADMISSION/'routing_production60';CODE=Path(__file__).parent
JOB='semantic_sport_expert_route426_20261022_remaining62'


def retire():
    roots={read(OLD/'RAM_cache_registration.json')['path'],read(ROOT/'RAM_cache_registration.json')['path']}
    files=[];directories=[]
    for text in roots:
        root=Path(text).resolve(strict=True)
        if root.parent!=Path('/dev/shm') or root.stat().st_uid!=os.getuid() or not root.name.startswith(('aic_routing60_','aic_routing62_')):
            raise ValueError('Own temporary cache scope/owner differs')
        entries=list((root/'inputs').glob('*/*'))
        if any(not p.is_file() or p.is_symlink() or p.name not in {'rgb.npy','groups.npy','acceptance.json'} for p in entries):
            raise ValueError('Unknown temporary member; do not delete')
        files.extend(entries);directories.append(root)
    save(ROOT/'RAM_retirement_manifest.json',dict(files=[dict(path=str(p),bytes=p.stat().st_size) for p in files],
        reason='Declared own-cache lifecycle after all outputs/QA; includes original failed partial only, no original media/model data',
        all_durable_proofs_and_model_raw_kept=True))
    for p in files:p.unlink()
    for root in directories:
        for folder in (root/'inputs').iterdir():folder.rmdir()
        (root/'inputs').rmdir();root.rmdir()
    save(ROOT/'RAM_retirement_completion.json',dict(state='BOTH_OWN_EPHEMERAL_CACHES_RELEASED_AFTER_QA',retired_files=len(files)))


def main():
    ROOT.mkdir()
    if 'Operation not supported' not in (OLD/'routing_production60_prepare.log').read_text() or (OLD/'CPU_completion.json').exists():
        raise ValueError('Expected actual color-tag materialization failure differs')
    if (OLD/'GPU_completion.json').exists() or (OLD/'source_input_lock.json').exists():raise ValueError('Prior model work unexpectedly exists')
    reg=read(OLD/'registration.json');save(ROOT/'registration.json',reg)
    save(ROOT/'protocol.json',read(OLD/'protocol.json'))
    save(ROOT/'remaining_registration.json',dict(prior_failure=ref(OLD/'failure.json'),actual_failure_log=ref(OLD/'routing_production60_prepare.log'),
        original_protocol=ref(OLD/'protocol.json'),original_registration=ref(OLD/'registration.json'),
        adopted_first_successful_inputs=len(list((OLD/'CPU').glob('*/input_acceptance.json'))),prior_model_calls=0,
        only_repair='Use pre-existing40.47 SHA-pinned unsupported transfer-tag/matrix correction inside exact original I3D resize/crop; default other sources byte algorithm unchanged',
        frozen_source_color_policy=ref(RUN/'b_score_aligned_package_v4/source_color.py'),
        frozen_existing_configuration=ref(RUN/'b_score_aligned_package_v4/config.json'),
        no_new_test_content_class_or_threshold_selection=True,no_successful_decode_or_input_encoding_repeated=True))
    controller.ROOT=ROOT;controller.JOB=JOB
    controller.stage('routing_prepare62.py')
    names=['common.py','routing_production60_common.py','routing_production60_prepare.py','routing_production60_gpu.py',
        'routing_production60_review.py','routing_production60.py','routing_prepare62.py','routing_entry62.py',
        'routing_gpu62.py','routing_review62.py','routing_production62.py']
    dependencies=[ENGINEERING/'runtime.py',ENGINEERING/'profile_gpu.py',SPORT/'code/pilot15_common.py',SPORT/'code/pilot15_gpu.py',
        ENGINEERING/'crossdata12/code/prepare_raw.py',RUN/'b_score_aligned_package_v4/source_color.py',WRAPPER]
    save(ROOT/'source_input_lock.json',dict(protocol=ref(ROOT/'protocol.json'),registration=ref(ROOT/'registration.json'),
        recovery=ref(ROOT/'remaining_registration.json'),CPU=ref(ROOT/'CPU_completion.json'),
        code={n:ref(CODE/n) for n in names},dependencies={str(p):ref(p) for p in dependencies}))
    controller.stage('routing_gpu62.py',True)
    record=read(RUN/'controller'/(JOB+'.resource.json'))
    rows=[json.loads(x) for x in (WORK/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if x.strip()]
    if record['status']!='completed' or record['exit_code']!=0 or [r for r in rows if r.get('name')==JOB]!=[record]:
        raise ValueError('Actual natural production terminal/unique ledger differs')
    controller.stage('routing_review62.py');checked(reg['protected_baseline']);retire()
    save(ROOT/'model_and_selection_completion.json',dict(state='ALL426_MODEL_AND_FIRST_CPU_QA_COMPLETE_PACKAGE_PENDING',
        selection=ref(ROOT/'selection_acceptance.json'),GPU_seconds=record['charged_seconds'],
        actual_GPU_status=record['status'],actual_GPU_exit=record['exit_code'],actual_parameters=FULL_PARAMETERS,
        new8B_calls=0,new_ZIP=0,baseline40_47_unchanged=True,old60_failure_preserved=True))


if __name__=='__main__':
    try:main()
    except BaseException:
        if ROOT.exists():save(ROOT/'failure.json',dict(traceback=traceback.format_exc(),keep_all_successful_inputs_and_raw=True))
        raise
