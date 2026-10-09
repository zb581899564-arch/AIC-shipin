import bw_common as c
def main():
    c.verify();rt,ex,cc,student,old,frames,production=c.helpers();plan,jobs=c.jobs_for('nontest')
    c.require(len(jobs)==8 and all(not c.is_changed(p) for j in jobs for p in j['windows']),'NT8 must remain exact original')
    for job in jobs:
        for ix,part in enumerate(job['windows']):c.checked(c.done_path('nontest',job,ix,'BW',cc),job,ix,'BW',ex)
    c.save(c.HERE/'nontest_01/nontest.completion.json',dict(status='PASS_ALL_BALANCED_TWO_WINDOW_ATTEMPTS',utc=c.utc(),records=8,
        total_windows=8,fresh_model_calls=0,reused_exact_original_calls=8,new_optimizer_updates=0,new_32B_calls=0,new_overview_calls=0))
if __name__=='__main__':main()
