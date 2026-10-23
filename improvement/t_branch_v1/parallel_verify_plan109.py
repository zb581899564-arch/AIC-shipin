"""Plan complete four-arm candidate VERIFY before preparing any new inputs."""
from development_verify46 import candidate_request
from t_io import ROOT, check, read
from verify_adoption92 import adopt


def plan(sources, protocol, catalog):
    first = read(ROOT / 'parallel_cost107/initial_controls_GPU.json')['outputs']
    control_QA = read(ROOT / 'parallel_cost107/CPU_completion.json')['original50_control_first_CPU']
    trained = read(ROOT / 'parallel_remaining108/development_GPU.json')['outputs']
    trained_QA = read(ROOT / 'parallel_remaining108/CPU_completion.json')['new150dev_proofs']
    arms = protocol['development_matrix']
    pending, tasks, adopted, decisions, policies = {}, {}, {}, {}, {}
    for sid, source in sources.items():
        policies[sid] = {arm: [] for arm in arms}
        for arm in arms:
            outputs = first[sid] if arm == arms[0] else trained[arm][sid]
            proofs = control_QA if arm == arms[0] else trained_QA[arm]
            if set(outputs) != {case.name for case in source.cases}:
                raise ValueError('Complete accepted parallel source output domain differs')
            for case in source.cases:
                ref = outputs[case.name]
                if read(check(proofs[case.name]))['actual_output'] != ref:
                    raise ValueError('Adopted first parallel native output QA belongs to another output')
                output = read(check(ref))
                for index, segment in enumerate(output['segments']):
                    event, request = candidate_request(case, source, segment, index)
                    key = request['request_id']
                    if key not in tasks and key not in pending:
                        accepted = adopt(catalog, key, case, event, request)
                        if accepted is None:
                            pending[key] = dict(source=sid, case=case.name, event=event, request=request)
                        else:
                            tasks[key] = accepted['task']
                            adopted[key], decisions[key] = accepted['output'], accepted['decision']
                    elif key in pending:
                        previous = pending[key]
                        if previous['event'] != event or previous['request'] != request:
                            raise ValueError('Two distinct actual VERIFY requests share an identity')
                    elif tasks[key]['event'] != event or read(check(tasks[key]['request'])) != request:
                        raise ValueError('An adopted actual VERIFY identity collides with a new request')
                    policies[sid][arm].append(key)
    return dict(tasks=tasks, pending=pending, adopted_successful_outputs=adopted,
        adopted_independently_accepted_decisions=decisions, source_policies=policies,
        maximum_first_new_VERIFY_calls=len(pending), all_logical_source_outputs=200)
