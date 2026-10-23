"""Adopt all prior successful exact VERIFY tasks, including completed summary93."""
from t_io import ROOT, check, identity, read
from verify_adoption92 import accepted_catalog


def catalog():
    tasks, proofs = accepted_catalog()
    inputs = read(ROOT / 'summary_verify_inputs92/completion.json')
    outputs = read(ROOT / 'summary_full93/GPU_completion.json')['outputs']
    if set(inputs['tasks']) != set(outputs):
        raise ValueError('Successful93 actual VERIFY task/output domain differs')
    proofs.append(identity(ROOT / 'summary_full93/independent_CPU_completion.json'))
    for key, task in inputs['tasks'].items():
        row = read(check(outputs[key]))
        if row['input'] != task:
            raise ValueError('Prior93 successful VERIFY output belongs to a different task')
        accepted = dict(task=task, output=outputs[key], decision=row['decision'])
        if key in tasks and tasks[key] != accepted:
            raise ValueError('Prior exact successful VERIFY identities conflict; never pick a favorable answer')
        tasks[key] = accepted
    return tasks, proofs
