"""One bounded new CPU-only native-audio and ASR chain; no old work relaunched."""
import os
os.environ['CUDA_VISIBLE_DEVICES']=''
from pathlib import Path
import subprocess
import time
import traceback
from common import ROOT,WORK,save,ref,read


def main():
    target=ROOT/'speech_chain38';target.mkdir()
    save(target/'registration.json',dict(scope='First4 previously unused native publisher sources; full ordered ASR for semantic-information test',
        scientific_difference='Old8 ASR used local excerpt text only; old pooled latent and PANN event fusions STOP unchanged',
        parent_CUDA='',no_GPU_launch=True,original40_47_unchanged=True,
        no_old_successful_decode_encoding_or_model_call_repeated=True,
        code={n:ref(Path(__file__).parent/n) for n in ['source_audio36.py','asr37.py','audio38.py','common.py','pilot_common28.py']}))
    for stage in ['source_audio36.py','asr37.py']:
        command=[str(WORK/'env/qwen3vl_isolated_20260910/bin/python'),'-B','-u',str(Path(__file__).parent/stage)]
        with (target/(stage+'.log')).open('x') as log:
            process=subprocess.Popen(command,env=dict(os.environ,CUDA_VISIBLE_DEVICES='',OMP_NUM_THREADS='2',MKL_NUM_THREADS='2'),stdout=log,stderr=subprocess.STDOUT)
            save(target/(stage+'.launch.json'),dict(pid=process.pid,command=command,
                start_ticks=Path(f'/proc/{process.pid}/stat').read_text().rsplit(')',1)[1].split()[19]))
            code=process.wait()
        save(target/(stage+'.terminal.json'),dict(exit_code=code))
        if code:raise RuntimeError('Actual first new CPU stage failed: '+stage)
    save(target/'completion.json',dict(state='NEW_WHOLE_SOURCE_ASR_INPUTS_COMPLETE',
        ASR=ref(ROOT/'speech36/ASR_completion.json'),new_GPU=0,new_ZIP=0))


if __name__=='__main__':
    try:main()
    except BaseException:
        save(ROOT/'speech38_failure.json',dict(traceback=traceback.format_exc(),no_silent_retry=True));raise
