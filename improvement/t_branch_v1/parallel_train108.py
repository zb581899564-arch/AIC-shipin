"""Fixed complete217 windows/five publisher updates, first107 micro adopted once."""
from fractions import Fraction
import math
import time

from joint_data44 import Case, Source
from native_prepared103 import Prefetch
from native_recovery102 import publisher_update, restore_first
from native_sets import NativeTimeline
from native_state100 import fingerprint
from parallel_input106 import values
from parallel_step108 import step
from parallel_training107 import training_mode
from t_io import ROOT, check, identity, read, save


def cases(data):
    result = {}
    for sid, item in data['sources'].items():
        timeline = NativeTimeline.from_clock(read(check(item['source']['clock'])))
        result[sid] = Source(sid, [], timeline, [], {})
        for target in item['cases']:
            meta = read(check(read(check(target['original_CPU']))['input']))
            result[sid].cases.append(Case(target['case'], target['original_CPU'], meta, {}, {}))
    return result


def train(model, processor, rt, loaded, optimizer, trainable, data, code, out, temporary):
    first_result = read(ROOT / 'parallel_cost107/GPU_completion.json')
    first = first_result['first_micro']
    checkpoint = restore_first(model, optimizer, trainable, first, loaded['base'])
    sources = cases(data)
    first_sid = data['publishers'][data['schedule'][0]][0]
    if first['target_binding'] != data['sources'][first_sid]['cases'][0]:
        raise ValueError('Actual first parallel micro does not belong to fixed first source/case')
    save(out / 'adopted_first_micro.json', dict(cursor=first['cursor'], target_binding=first['target_binding'],
        actual_selection=first['actual_selection'], exact_recovery_gradient=first['exact_successful_gradient'],
        adopted_actual_GPU=identity(ROOT / 'parallel_cost107/GPU_completion.json'),
        adopted_first_CPU=identity(ROOT / 'parallel_cost107/CPU_completion.json'),
        no_new_forward_backward_or_CPU_repeat=True))
    adopted = identity(out / 'adopted_first_micro.json')
    count, updates = 1, []
    training_mode(model)  # One hook lifecycle for all training; no duplicate enable per window.
    (out / 'micro').mkdir()
    (out / 'publisher').mkdir()

    def loader(entry):
        _, sid, case, target = entry
        started = time.monotonic()
        actual = values(case, target['actual_input_CPU'], processor.tokenizer, rt)
        return actual, time.monotonic() - started

    for episode, publisher in enumerate(data['schedule'], 1):
        before = fingerprint(model, 'actor', loaded['base'])
        rows = [adopted] if episode == 1 else []
        cursor = first['cursor'] if episode == 1 else None
        entries = []
        mass = 0.
        for sid in data['publishers'][publisher]:
            item = data['sources'][sid]
            weight = float(Fraction(item['publisher_source_weight']))
            for case, target in zip(sources[sid].cases, item['cases']):
                mass += (target['positive_mass'] + target['negative_mass']) * weight
                if episode == 1 and sid == first_sid and case.name == first['cursor']['case']:
                    continue
                entries.append((publisher, sid, case, target))
        if not math.isclose(mass, 1., abs_tol=1e-12, rel_tol=0):
            raise ValueError('Actual complete-source equal-publisher preference denominator differs')
        with Prefetch(entries, loader) as pending:
            for (_, sid, case, target), (actual, cpu_seconds) in pending:
                count += 1
                cursor = dict(publisher=publisher, source=sid, case=case.name,
                              completed_micro=count, optimizer_updates=episode - 1)
                rows.append(step(model, sources[sid], case, target,
                    data['sources'][sid]['publisher_source_weight'], code, before, actual, rt,
                    out / 'micro' / ('M%03d' % count), temporary, trainable, cursor, checkpoint, cpu_seconds))
                del actual
        if fingerprint(model, 'actor', loaded['base']) != before:
            raise ValueError('Actor weights changed before completing actual full publisher')
        if cursor is None:
            raise ValueError('A registered publisher has no actual training windows')
        result, checkpoint = publisher_update(model, optimizer, trainable, temporary,
            out / 'publisher' / ('P%d' % episode), episode, cursor, before, loaded['base'], rows)
        updates.append(result)
        print('PARALLEL108_COMPLETE_PUBLISHER_UPDATE', episode, publisher, count, flush=True)
    if count != 217 or len(updates) != 5:
        raise ValueError('Fixed217 complete native windows/five updates not reached')
    return dict(publisher_updates=updates, complete_windows=217, adopted_first_windows=1,
                actual_new_target_forwards=216, actual_optimizer_updates=5,
                actor_initial=first['actual_actor_state'], actor_final=fingerprint(model, 'actor', loaded['base']))
