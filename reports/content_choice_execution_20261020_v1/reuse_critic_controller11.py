"""Explicit CPU critic production from an independently admitted contrast pool."""
import importlib.util
import os
from pathlib import Path
import traceback

R=Path('/home/inspur/aic_video_work/content_choice_20261019_v1');W=R.parent
spec=importlib.util.spec_from_file_location('finite_control',R/'control.py')
c=importlib.util.module_from_spec(spec);spec.loader.exec_module(c)
FORMAL=R/'production_assets.private.json'
QA=W/'five_summary_sprint_20261019_v41/first_independent_output_QA41.json'

def main():
    phase='CLAIM'
    try:
        c.save(R/'critic_reuse_controller_started11.json',dict(utc=c.utc(),pid=os.getpid(),
            start_ticks=Path('/proc/self/stat').read_text().rsplit(')',1)[1].split()[19],new_qwen_calls=0))
        assert os.environ.get('CUDA_VISIBLE_DEVICES')==''
        decision=c.load(R/'critic_reuse_decision11.json');assert decision['approved'] is True
        review=R/'review_critic/review.json';origin=R/'production_contrast/completion.json'
        assert c.load(review)['status']=='ELIGIBLE_FOR_EXECUTION_REVIEW'
        assert decision['review_sha256']==c.ref(review)['sha256']
        assert decision['production_pool_sha256']==c.ref(origin)['sha256']
        original_parent=c.load(R/'production_contrast_controller_completion08.json')
        assert original_parent['status']=='FORMAL_PRODUCTION_COMPLETE_PENDING_EXPLICIT_PACKAGE_REVIEW'
        phase='REUSE_ADMISSION'
        draft=R/'critic_reuse_production.draft.json'
        c.stage('critic_reuse_admission11',[c.PY,'-B',c.CODE/'admission.py','--action','production','--candidate','critic',
            '--config',c.CFG,'--assets',c.ASSETS,'--production-assets',FORMAL,'--review-run',review,'--formal-qa',QA,
            '--production-pool',origin,'--output',draft],1800)
        admitted=c.load(draft)
        admitted.update(approved=True,draft_only=False,reviewed_by='Execution main agent, separate critic and admitted complete contrast pool review',
            reviewed_at=c.utc(),review_notes=decision['review_notes'],execution_decision_ref=c.ref(R/'critic_reuse_decision11.json'))
        admission=R/'critic_reuse_production.admission.json';c.save(admission,admitted)
        phase='CPU_REUSE_AND_INDEPENDENT_INPUT_OUTPUT_REVIEW'
        c.stage('critic_reuse_production11',c.cli('production','--candidate','critic','--production-assets',FORMAL,
            '--review-run',review,'--formal-qa',QA,'--production-pool',origin,'--admission',admission),1860)
        complete=c.load(R/'production_critic/completion.json')
        assert complete['status']=='COMPLETE_PRODUCTION_NOT_PACKAGED'
        assert complete['execution_mode']=='CPU_CRITIC_FROM_ADMITTED_CONTRAST_POOL'
        assert all(v==0 for v in complete['counts'].values())
        assert complete['source_count']==426 and complete['window_count']==522
        baseline=c.ref(c.BASELINE);assert baseline['sha256']=='b37c4a2e6593fc800f54ecce2f860fee5e7d5dc74e17ce280f9ee6722afbccd3'
        c.save(R/'production_critic_controller_completion08.json',dict(utc=c.utc(),
            status='FORMAL_PRODUCTION_COMPLETE_PENDING_EXPLICIT_PACKAGE_REVIEW',candidate='critic',
            execution_mode=complete['execution_mode'],resource_ref=original_parent['resource_ref'],
            resource_is_adopted_origin_only_not_new_charge=True,new_qwen_calls=0,counts=complete['counts'],
            production_ref=c.ref(R/'production_critic/completion.json'),baseline_ref=baseline,automatic_package=False))
    except BaseException as e:
        c.save(R/'critic_reuse_controller_failure11.json',dict(utc=c.utc(),phase=phase,error=str(e),traceback=traceback.format_exc(),automatic_retry=False))
        raise

if __name__=='__main__':main()
