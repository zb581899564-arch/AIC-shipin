"""First remaining93 original TIME generations; adopt four accepted answers."""
from pilot_context30 import ROOT, WORK, OUT, RUN, check, identity, read, save, legacy_runtime, original_outputs

def gpu():
    rt = legacy_runtime()
    from sft_contract import verify_live_gpu_reservation
    verify_live_gpu_reservation()
    from coarse_call25 import generate_case
    for ref in read(OUT / 'source_input_lock.json')['code'].values():
        check(ref)
    config = read(RUN / 'b_score_aligned_package_v4/config.json')
    model, processor, loaded = rt.b_engine.load_model(config)
    prior = read(ROOT / 'pilot_cost25/model_identity.json')
    if (loaded['logical_parameters'] != 8782459120 or
            loaded['base']['sha256'] != prior['base']['sha256'] or
            loaded['adapter']['sha256'] != prior['adapter']['sha256']):
        raise ValueError('Original whole-source control model differs from accepted first4')
    save(OUT / 'model_identity.json', loaded)
    originals = original_outputs()
    folder = OUT / 'outputs'
    folder.mkdir()
    outputs, new = [], 0
    with (OUT / 'accepted.jsonl').open('x') as journal:
        for cpu_ref in read(ROOT / 'pilot_input_qa29/completion.json')['accepted']:
            cpu = read(check(cpu_ref))
            meta = read(check(cpu['input']))
            if meta['case_id'] in originals:
                outputs.append(originals[meta['case_id']])
                continue
            ref = generate_case(model, processor, rt, cpu_ref, folder)
            outputs.append(ref)
            new += 1
            journal.write(__import__('json').dumps(dict(case=meta['case_id'], output=ref)) + '\n')
            journal.flush()
    if len(outputs) != 97 or new != 93:
        raise ValueError('Whole-source original control denominator differs')
    if (rt.b_engine.frozen_identity(model, config) != loaded['base'] or
            rt.b_engine.adapter_identity(model, config) != loaded['adapter']):
        raise ValueError('Frozen BASE/TIME changed')
    save(OUT / 'gpu_completion.json', dict(state='ALL97_ORIGINAL_COARSE_CONTROLS_COMPLETE', outputs=outputs,
        first_remaining_calls=new, adopted_calls=4, actual_parameters=loaded['logical_parameters'], updates=0))


if __name__ == '__main__':
    gpu()
