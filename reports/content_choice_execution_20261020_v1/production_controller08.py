"""One explicitly reviewed PR3 formal stage. No automatic packaging."""
import argparse
from datetime import datetime,timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import time
import traceback

R=Path('/home/inspur/aic_video_work/content_choice_20261019_v1')
W=R.parent
spec=importlib.util.spec_from_file_location('finite_control',R/'control.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
FORMAL=R/'production_assets.private.json'
QA=W/'five_summary_sprint_20261019_v41/first_independent_output_QA41.json'

def main(candidate):
    name='production_'+candidate
    phase='CLAIM'
    try:
        c.save(R/(name+'_controller_started08.json'),dict(utc=c.utc(),pid=os.getpid(),
            start_ticks=Path('/proc/self/stat').read_text().rsplit(')',1)[1].split()[19],
            argv=__import__('sys').argv,automatic_package=False))
        assert os.environ.get('CUDA_VISIBLE_DEVICES')=='0'
        decision=c.load(R/(name+'_decision08.json'))
        assert decision['approved'] is True and decision['candidate']==candidate
        assert c.load(R/'user_resume_01.json')['explicit_human_resume'] is True
        review=R/('review_'+candidate)/'review.json'
        d=c.load(review)
        assert d['status']=='ELIGIBLE_FOR_EXECUTION_REVIEW' and d['stop_reasons']==[]
        assert decision['review_sha256']==c.ref(review)['sha256']
        assert decision['production_assets_sha256']==c.ref(FORMAL)['sha256']
        if candidate=='critic':
            assert c.load(R/'train_fit_control_completion.json')['status']=='TRAIN_COLLECTION_FIT_AND_REVIEW_COMPLETE'
            assert not c.load(R/'train_fit_control_completion.json')['scientific_stop']
        else:
            assert c.load(R/'check_control_completion.json')['status']=='CHECK_COLLECTION_AND_CONTRAST_REVIEW_COMPLETE'
        phase='ADMISSION_DRAFT'
        draft=R/(name+'.draft.json')
        c.stage(name+'_admission08',[c.PY,'-B',c.CODE/'admission.py','--action','production','--candidate',candidate,
            '--config',c.CFG,'--assets',c.ASSETS,'--production-assets',FORMAL,'--review-run',review,
            '--formal-qa',QA,'--output',draft],1800)
        admitted=c.load(draft)
        admitted.update(approved=True,draft_only=False,reviewed_by='Execution main agent, direct scientific and engineering review',
            reviewed_at=c.utc(),review_notes=decision['review_notes'],execution_decision_ref=c.ref(R/(name+'_decision08.json')))
        admission=R/(name+'.admission.json');c.save(admission,admitted)
        phase='GPU_PRODUCTION'
        budget=c.load(R/'active_resume_budget07.json')
        resume=datetime.fromisoformat(budget['resume_remote_utc'])
        elapsed=(datetime.now(timezone.utc)-resume).total_seconds()
        allowed=int(min(7200,budget['max_window_seconds_from_resume']-elapsed-budget['reserve_final_QA_delivery_seconds']))
        assert allowed>0,'No runtime remains after QA/delivery reserve'
        c.save(R/(name+'_deadline08.json'),dict(elapsed_after_resume=elapsed,outer_max_seconds=allowed,
            frozen_inner_max_seconds=7200,final_QA_delivery_reserve=budget['reserve_final_QA_delivery_seconds']))
        resource=c.gpu(name,c.cli('production','--candidate',candidate,'--review-run',review,
            '--production-assets',FORMAL,'--formal-qa',QA,'--admission',admission,
            '--torch-checks',R/'torch_cpu_checks.json'),allowed)
        complete=c.load(R/name/'completion.json')
        assert complete['status']=='COMPLETE_PRODUCTION_NOT_PACKAGED'
        assert complete['source_count']==426 and complete['window_count']==522
        baseline=c.ref(c.BASELINE);assert baseline['bytes']==384630 and baseline['sha256']=='b37c4a2e6593fc800f54ecce2f860fee5e7d5dc74e17ce280f9ee6722afbccd3'
        c.save(R/(name+'_controller_completion08.json'),dict(utc=c.utc(),
            status='FORMAL_PRODUCTION_COMPLETE_PENDING_EXPLICIT_PACKAGE_REVIEW',candidate=candidate,
            resource_ref=resource,production_ref=c.ref(R/name/'completion.json'),
            counts=complete['counts'],baseline_ref=baseline,automatic_package=False))
    except BaseException as e:
        c.save(R/(name+'_controller_failure08.json'),dict(utc=c.utc(),phase=phase,error=str(e),
            traceback=traceback.format_exc(),automatic_retry=False,failed_to_empty=False))
        raise

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--candidate',choices=['critic','contrast'],required=True)
    main(p.parse_args().candidate)
