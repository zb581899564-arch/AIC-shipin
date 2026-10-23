"""Adopt four successful causal TFs from failed38, first independent scalar replay."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
import traceback

from policy_replay36 import independent_logps
from t_io import ROOT, WORK, check, identity, read, save

OUT = ROOT / 'policy_adopt40'
OLD = ROOT / 'policy_probe38'
RUN = WORK / 'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
JOB = 'T_real_causal_actor_backward_probe_20261022_v35'


def main():
    OUT.mkdir()
    log_path = RUN / 'controller' / (JOB + '.log')
    text = log_path.read_text()
    if ('ValueError: Actual8B actor is not an exact original TIME copy' not in text or
            text.count('FIRST_CAUSAL_TF34_ACCEPTED ') != 4):
        raise ValueError('Actual failed actor-copy trace does not prove exactly4 accepted TFs')
    check(read(OLD / 'source_input_lock.json')['code']['policy_probe34.py'])
    resource = read(RUN / 'controller' / (JOB + '.resource.json'))
    if resource['status'] != 'failed' or resource['exit_code'] != 1:
        raise ValueError('Original natural failed GPU terminal differs')
    accepted = []
    for ref in read(ROOT / 'causal_contract32/completion.json')['accepted']:
        descriptor = read(check(ref))
        path = OLD / 'causal_outputs' / (descriptor['case'] + '.json')
        payload = read(path)
        if payload['native_contract'] != descriptor:
            raise ValueError('Successful saved causal TF has a different actual input contract')
        accepted.append(identity(path))
    checks = [independent_logps(ref) for ref in accepted]
    save(OUT / 'completion.json', dict(state='FOUR_SUCCESSFUL_CAUSAL_TF_ADOPTED_CPU_SCALAR_PASS',
        accepted=accepted, scalar_checks=checks, actual_failure=identity(log_path),
        prior_GPU_seconds=resource['charged_seconds'], original_GPU_limit_seconds=600,
        remaining_GPU_seconds_integer=int(600 - resource['charged_seconds']),
        first_reference_TFs=4, repeated_TFs=0, new_GPU_calls=0,
        no_optimizer_or_source_quality_claim=True))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc()))
        raise
