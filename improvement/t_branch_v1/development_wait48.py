"""Single dependency controller; no timer, model retry or implicit production."""
import time
import traceback

from t_io import ROOT, check, identity, read, save

OUT = ROOT / 'development_wait48'


def main():
    OUT.mkdir()
    train = ROOT / 'joint_remaining47'
    save(OUT / 'registration.json', dict(required_train_root=str(train),
        dependency='Natural GPU and first independent CPU completion of exactly frozen4 episodes',
        action='Run fixed2publisher dev and exact40.47 downstream only after train mechanism PASS',
        no_new_timer_or_production_or_official_submission=True))
    while not (train / 'completion.json').exists():
        if (train / 'failure.json').exists():
            save(OUT / 'completion.json', dict(state='DEPENDENCY_FAILED_NO_DEV_STARTED',
                actual_training_failure=identity(train / 'failure.json'), new_GPU_calls=0))
            return
        time.sleep(10)
    final = read(train / 'completion.json')
    check(final['CPU_audit'])
    if final['state'] != 'JOINT4_TRAINING_ENGINEERING_COMPLETE':
        save(OUT / 'completion.json', dict(state='DEPENDENCY_NO_MECHANISM_NO_DEV_STARTED',
            actual_training_terminal=identity(train / 'completion.json'), new_GPU_calls=0))
        return
    import development48
    development48.main()
    save(OUT / 'completion.json', dict(state='FROZEN_DEVELOPMENT_FINISHED',
        development=identity(ROOT / 'development48/completion.json'), no_automatic_confirmation_or_production=True))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(), preserve_all_successes=True))
        raise
