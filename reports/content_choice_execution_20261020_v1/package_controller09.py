"""Separate explicit package review after natural formal completion."""
import argparse
import importlib.util
import os
from pathlib import Path
import traceback

R=Path('/home/inspur/aic_video_work/content_choice_20261019_v1');W=R.parent
spec=importlib.util.spec_from_file_location('finite_control',R/'control.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
FORMAL=R/'production_assets.private.json'

def main(candidate):
    name='package_'+candidate
    phase='CLAIM'
    try:
        c.save(R/(name+'_controller_started09.json'),dict(utc=c.utc(),pid=os.getpid(),
            start_ticks=Path('/proc/self/stat').read_text().rsplit(')',1)[1].split()[19],argv=__import__('sys').argv))
        assert os.environ.get('CUDA_VISIBLE_DEVICES')==''
        decision=c.load(R/(name+'_decision09.json'));assert decision['approved'] is True and decision['candidate']==candidate
        parent=c.load(R/('production_'+candidate+'_controller_completion08.json'))
        assert parent['status']=='FORMAL_PRODUCTION_COMPLETE_PENDING_EXPLICIT_PACKAGE_REVIEW'
        completion=R/('production_'+candidate)/'completion.json'
        assert decision['production_sha256']==c.ref(completion)['sha256']
        resource=c.load(parent['resource_ref']['path'])
        rows=[__import__('json').loads(s) for s in (W/'improvement_round1/gpu_ledger.jsonl').read_text().splitlines() if s.strip()]
        assert resource['status']=='completed' and resource['exit_code']==0
        assert [x for x in rows if x.get('name')==resource['name']]==[resource]
        phase='ADMISSION'
        draft=R/(name+'.draft.json')
        c.stage(name+'_admission09',[c.PY,'-B',c.CODE/'admission.py','--action','package','--candidate',candidate,
            '--config',c.CFG,'--assets',c.ASSETS,'--production-assets',FORMAL,'--production-run',completion,'--output',draft],1800)
        admitted=c.load(draft)
        admitted.update(approved=True,draft_only=False,reviewed_by='Execution main agent after natural wrapper and complete formal outputs',
            reviewed_at=c.utc(),review_notes=decision['review_notes'],execution_decision_ref=c.ref(R/(name+'_decision09.json')))
        admission=R/(name+'.admission.json');c.save(admission,admitted)
        phase='PACKAGE_AND_INDEPENDENT_QA'
        c.stage(name+'_run09',c.cli('package','--candidate',candidate,'--production-assets',FORMAL,
            '--production-run',completion,'--admission',admission),1860)
        c.save(R/(name+'_controller_completion09.json'),dict(utc=c.utc(),
            status='PACKAGE_AND_INDEPENDENT_QA_NATURALLY_COMPLETED_WINDOWS_DELIVERY_PENDING',
            package_completion_ref=c.ref(R/name/'completion.json'),candidate=candidate,automatic_website_submission=False))
    except BaseException as e:
        c.save(R/(name+'_controller_failure09.json'),dict(utc=c.utc(),phase=phase,error=str(e),traceback=traceback.format_exc(),automatic_retry=False))
        raise

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--candidate',choices=['critic','contrast'],required=True)
    main(p.parse_args().candidate)
