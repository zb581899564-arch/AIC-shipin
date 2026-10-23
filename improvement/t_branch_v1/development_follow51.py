"""Wait for the one explicit50 final/CPU; never restart failed48 or any GPU job."""
import time
import traceback

from t_io import ROOT, check, identity, read, save

OUT = ROOT / 'development_follow51'
TRAIN = ROOT / 'joint_continue50'


def main():
    OUT.mkdir()
    save(OUT / 'registration.json', dict(upstream=str(TRAIN), same_frozen_development_science=True,
        old48_not_restarted=True, no_new_timer_or_confirmation_or_production=True))
    while not (TRAIN / 'completion.json').exists():
        if (TRAIN / 'failure.json').exists():
            save(OUT / 'completion.json', dict(state='DEPENDENCY_FAILED_NO_DEV_STARTED', failure=identity(TRAIN / 'failure.json')))
            return
        time.sleep(10)
    final = read(TRAIN / 'completion.json'); check(final['CPU_audit'])
    if final['state'] != 'JOINT4_TRAINING_ENGINEERING_COMPLETE':
        save(OUT / 'completion.json', dict(state='DEPENDENCY_NO_MECHANISM_NO_DEV_STARTED', training=identity(TRAIN / 'completion.json')))
        return
    import development51
    development51.main()
    save(OUT / 'completion.json', dict(state='FIXED_DEVELOPMENT_FINISHED', development=identity(ROOT / 'development51/completion.json')))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc(), preserve_all_successes=True))
        raise
