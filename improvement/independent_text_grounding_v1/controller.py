"""One bounded frozen-model capability run, with all data and outputs on Linux."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import traceback
from common import ROOT,WORK,ref,read,write

PY=WORK/'env/qwen3vl_isolated_20260910/bin/python'
WRAPPER=WORK/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z/resource_unlimited_v1_20261007/gpu_run.py'
RESOURCE=WRAPPER.parent.parent/'controller'
LEDGER=WORK/'improvement_round1/gpu_ledger.jsonl'
JOB='independent_text_grounding_clip8_20261021_v1'


def stage(name,script,gpu=False):
    env=dict(os.environ,CUDA_VISIBLE_DEVICES='0' if gpu else '',PYTHONDONTWRITEBYTECODE='1',
             OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
    command=[str(PY),'-u','-B',str(ROOT/'code'/script)]
    if gpu:
        assert not (RESOURCE/f'{JOB}.resource.json').exists()
        command=[str(PY),'-B',str(WRAPPER),'--name',JOB,'--max-seconds','900',
                 '--planned-output-bytes','100000000','--capacity-reason',
                 'Live GPU empty and14GB free before admission; one frozen151M CLIP,32images/batch, cached RGB only; no Qwen load or outside task changes',
                 '--queue-seconds','0','--']+command
    started=time.monotonic()
    with (ROOT/f'{name}.log').open('x') as log:
        p=subprocess.Popen(command,env=env,cwd=ROOT,stdin=subprocess.DEVNULL,stdout=log,stderr=subprocess.STDOUT)
        ticks=Path(f'/proc/{p.pid}/stat').read_text().rsplit(')',1)[1].split()[19]
        write(ROOT/f'{name}_launch.json',dict(pid=p.pid,start_ticks=ticks,argv=command))
        code=p.wait()
    write(ROOT/f'{name}_terminal.json',dict(exit_code=code,seconds=time.monotonic()-started))
    if code:
        raise RuntimeError(f'{name} naturally failed; preserve successful assets, no automatic retries')


def main():
    write(ROOT/'controller_claim.json',dict(pid=os.getpid(),scope='Frozen semantic capability only, not automatic production'))
    stage('acquire','acquire.py')
    stage('prepare','prepare.py')
    write(ROOT/'source_input_lock.json',dict(protocol=ref(ROOT/'protocol.json'),
              code={p.name:ref(p) for p in sorted((ROOT/'code').glob('*.py'))},
              assets=ref(ROOT/'asset_acceptance.json'),inputs=ref(ROOT/'input_acceptance.json'),
              wrapper=ref(WRAPPER),target='Human query event localization, not generic highlights'))
    stage('gpu','infer.py',True)
    record=read(RESOURCE/f'{JOB}.resource.json')
    ledger=[json.loads(s) for s in LEDGER.read_text().splitlines() if s.strip()]
    assert record['status']=='completed' and record['exit_code']==0
    assert [r for r in ledger if r.get('name')==JOB]==[record]
    stage('review','review.py')
    stage('audit','audit.py')
    review=read(ROOT/'review.json');inference=read(ROOT/'inference_completion.json')
    baseline=Path('/home/inspur/aic_video_work/semantic_context_production_20261016_v1/package/candidate_CONTEXT_SEMANTIC_RESIDUAL.zip')
    assert ref(baseline)['sha256']==read(ROOT/'protocol.json')['protected_sha256']
    write(ROOT/'completion.json',dict(status=review['status'],source_macro_AP=review['source_macro_AP'],
              tests=review['tests'],charged_seconds=record['charged_seconds'],
              peak_memory_mib_sampled=record.get('sampled_peak_memory_mib'),
              actual_clip_parameters=read(ROOT/'asset_acceptance.json')['actual_clip_parameters'],
              combined_parameters=read(ROOT/'asset_acceptance.json')['combined_with_protected_baseline'],
              image_embeddings=inference['image_embeddings'],image_forward_batches=inference['image_forward_batches'],
              text_forward_batches=1,review=ref(ROOT/'review.json'),audit=ref(ROOT/'independent_cpu_audit.json'),
              baseline_unchanged=True,production_allowed=False,new_zip=0,new_updates=0))


if __name__=='__main__':
    try:
        main()
    except BaseException:
        write(ROOT/'failure.json',dict(status='ACTUAL_FAILURE_PRESERVED',traceback=traceback.format_exc()))
        raise
