"""Exact successful VERIFY adoption and first QA for new content-goal outputs."""
import math

import torch

from frozen_branch46 import verify_modules
from t_io import ROOT, check, identity, read, save


def accepted_catalog():
    stages = [
        ('development_remaining55', 'verify_CPU_completion.json',
         'verify_GPU_completion.json', 'independent_CPU_audit.json'),
        ('event_verify_inputs76', 'completion.json',
         '../event_full78/GPU_completion.json', '../event_full78/independent_CPU_completion.json'),
    ]
    catalog, proofs = {}, []
    for stage, inputs, outputs, first_QA in stages:
        folder = ROOT / stage
        cpu = read(folder / inputs); gpu = read(folder / outputs)['outputs']
        proofs.append(identity(folder / first_QA))
        if set(cpu['tasks']) != set(gpu):
            raise ValueError('Accepted old VERIFY task/output denominator differs')
        for key, task in cpu['tasks'].items():
            row = read(check(gpu[key]))
            if row['input'] != task:
                raise ValueError('Old successful VERIFY is bound to a different input')
            value = dict(task=task, output=gpu[key], decision=row['decision'])
            if key in catalog and catalog[key] != value:
                raise ValueError('Two accepted identical VERIFY identities conflict')
            catalog[key] = value
    return catalog, proofs


def adopt(catalog, key, case, event, request):
    if key not in catalog:
        return None
    item = catalog[key]; task = item['task']
    if (task['event'] != event or read(check(task['request'])) != request
            or read(check(task['CPU']))['original_CPU'] != case.CPU):
        raise ValueError('Same VERIFY identity does not bind the same native candidate/input')
    return item


def first_decisions(cpu, gpu, tokenizer, folder):
    """Audit only first new outputs; old complete proofs are identity-adopted."""
    contract, grammar, _ = verify_modules()
    candidates = grammar.candidate_tokens(tokenizer, contract.responses())
    resolved = {key: value['decision'] for key, value in
                cpu['adopted_independently_accepted_decisions'].items()}
    if set(gpu['outputs']) != set(cpu['tasks']):
        raise ValueError('Complete union of source-specific VERIFY outputs absent')
    folder.mkdir(); proofs = []
    for key in gpu['first_new_keys']:
        task = cpu['tasks'][key]; row = read(check(gpu['outputs'][key]))
        raw = read(check(row['raw'])); request = read(check(task['request']))
        accepted = read(check(task['CPU']))
        if row['input'] != task or raw['prefix'] != accepted['detail']['input_tokens']:
            raise ValueError('First VERIFY actual raw/input prefix differs')
        rule = grammar.VerifyConstraint(tokenizer, raw['prefix'], request, raw['eos'], candidates)
        rule.assert_complete(torch.tensor(raw['tokens'], dtype=torch.long))
        text = tokenizer.decode(raw['tokens'], skip_special_tokens=True,
                                clean_up_tokenization_spaces=False)
        decision = contract.resolve(text, request, execution_status='MODEL_OK')
        if (text != raw['text'] or decision != row['decision']
                or len(raw['scores']) != len(raw['tokens'])
                or not all(math.isfinite(s) for s in raw['scores'])):
            raise ValueError('First VERIFY token/parser/decision or finite scores differ')
        resolved[key] = decision['decision']
        path = folder / (key + '.json')
        save(path, dict(state='PASS_FIRST_NEW_VERIFY_TOKEN_GRAMMAR_REQUEST_CPU',
                        actual_output=gpu['outputs'][key], CPU=task['CPU']))
        proofs.append(identity(path))
    if (set(resolved) != set(cpu['tasks'])
            or len(proofs) != cpu['maximum_first_new_VERIFY_calls']):
        raise ValueError('First/adopted VERIFY denominator differs')
    return resolved, proofs
