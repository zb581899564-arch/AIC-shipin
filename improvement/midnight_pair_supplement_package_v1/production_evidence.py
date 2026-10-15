"""Read-only proof validation for real calls and pre-GPU identical-input aliases.

The caller supplies a reference reader which verifies actual path/SHA bytes.
This module never creates a model answer, repeats a QA, or reads quality data.
"""
import json

from package_math import exact, require

ALIAS_DONE = 'ADOPTED_IDENTICAL_NEW_INPUT_MODEL_OUTPUT_NO_NEW_CALL'
REAL_QA = 'PASS_FIRST_INDEPENDENT_OUTPUT_QA'
ALIAS_QA = 'PASS_IDENTICAL_INPUT_ALIAS_NATIVE_APPLICATION_QA'
INPUT_QA = 'PASS_FIRST_NEW_PROMPT_INPUT_QA_ADOPT_OLD_NATIVE_VISION'
TABLE_SCHEMA = 'PRE_GPU_IDENTICAL_NEW_INPUT_ALIAS_TABLE_V1'
GENERATION = dict(do_sample=False, max_new_tokens=192, model_role='BASE_ONLY')
APPLICATION_FIELDS = ('source_id', 'source_sha256', 'source_ordinals', 'exact_pts', 'window_exact',
                      'window_native_end_ordinal', 'window_native_end_exact', 'candidate_events')


def ref_key(value):
    require(isinstance(value, dict) and isinstance(value.get('path'), str) and
            isinstance(value.get('sha256'), str), 'Actual path/SHA reference required')
    return value['path'], value['sha256']


def same_ref(left, right, reason):
    require(ref_key(left) == ref_key(right), reason)


def native_identity(value):
    return (value['source_sha256'], tuple(value['source_ordinals']), tuple(map(exact, value['exact_pts'])),
            tuple(map(exact, value['window_exact'])), value['window_native_end_ordinal'],
            exact(value['window_native_end_exact']))


def candidate_semantics(value):
    return tuple((tuple(map(exact, candidate['original_interval_exact'])),
                  None if candidate['selected_interval_exact'] is None else tuple(map(exact, candidate['selected_interval_exact'])),
                  candidate['decision']) for candidate in value['candidate_events'])


def validate_production_evidence(completion, read_ref, parameters):
    entries = completion['entries']
    require(isinstance(entries, list) and entries, 'Real production logical entries required')
    logical = completion.get('logical_cases', len(entries))
    model_count = completion['actual_model_calls']
    alias_count = completion.get('adopted_identical_input_aliases', 0)
    require(type(logical) is int and type(model_count) is int and type(alias_count) is int and
            logical == len(entries) and model_count > 0 and alias_count >= 0 and
            model_count + alias_count == logical, 'Actual call/alias/logical denominators differ')
    if alias_count:
        require(type(completion.get('first_model_output_QA_count')) is int and
                type(completion.get('alias_application_QA_count')) is int and
                completion.get('first_model_output_QA_count') == model_count and
                completion.get('alias_application_QA_complete') is True and
                completion.get('alias_application_QA_count') == alias_count,
                'Alias application QA cannot be counted as first model-output QA')
    elif 'first_model_output_QA_count' in completion:
        require(completion['first_model_output_QA_count'] == model_count, 'First real output-QA denominator differs')
    by_case, by_done, input_cache, qa_keys = {}, {}, {}, set()

    def load(reference):
        key = ref_key(reference)
        if key not in input_cache:
            input_cache[key] = read_ref(reference)
        return input_cache[key]

    def input_chain(entry, done):
        case = entry['case_id']
        input_ref, first_ref = done['input_ref'], done['first_input_qa_ref']
        if 'input_ref' in entry:
            same_ref(entry['input_ref'], input_ref, 'Entry input differs from actual done input')
        for field in ('first_input_qa_ref', 'input_qa_ref'):
            if field in entry:
                same_ref(entry[field], first_ref, 'Entry first input-QA reference differs')
        document, first = load(input_ref), load(first_ref)
        require(document['case_id'] == case and first['status'] == INPUT_QA and
                first.get('first_qa_not_repeated') is True and first.get('native_vision_adopted') is True,
                'Real original first new-input QA required for each logical application')
        same_ref(first['input_ref'], input_ref, 'First input QA belongs to another input document')
        require(first.get('vision_processor_calls', 0) == 0 and first.get('media_decodes', 0) == 0,
                'This production adopts successful original vision without another encode/decode')
        require(all(entry[field] == document[field] for field in APPLICATION_FIELDS),
                'Native application differs from its own first-QA accepted model input')
        return input_ref, first_ref, document

    for source in entries:
        entry = dict(source)
        case = entry['case_id']
        require(isinstance(case, str) and case and case not in by_case, 'Duplicate logical production case')
        key = ref_key(entry['decision_ref'])
        require(key not in by_done, 'Every logical case needs its own actual done document')
        done = load(entry['decision_ref'])
        require(done['case_id'] == case and 'parsed' in done, 'Done belongs to another logical case')
        if 'source_id' in done:
            require(done['source_id'] == entry['source_id'], 'Done source identity differs')
        if 'parsed' in entry:
            require(entry['parsed'] == done['parsed'], 'Logical parsed answer differs from actual done bytes')
        entry['parsed'] = done['parsed']
        is_alias = done.get('status') == ALIAS_DONE
        if is_alias:
            require(entry.get('actual_model_call') is False and done.get('actual_model_call') is False,
                    'Alias must explicitly declare no actual model call')
        else:
            require(entry.get('actual_model_call', True) is True and done.get('actual_model_call', True) is True,
                    'Only declared identical-input adoption may have zero new model calls')
        input_ref, first_ref, document = input_chain(entry, done)
        output_ref = entry['output_qa_ref']
        require(ref_key(output_ref) not in qa_keys, 'Every logical application requires its own distinct QA proof')
        qa_keys.add(ref_key(output_ref))
        proof = load(output_ref)
        require(proof.get('CPU_only') is True and proof.get('new_model_calls') == 0 and
                proof.get('model_calls', 0) == 0 and proof.get('parsed') == done['parsed'],
                'Accepted output/application QA must be CPU-only and bind unchanged actual parsed output')
        same_ref(proof['done_ref'], entry['decision_ref'], 'Output/application QA belongs to another done')
        same_ref(proof['first_input_qa_ref'], first_ref, 'Output/application QA uses another first input proof')
        if not is_alias:
            require(proof['status'] == REAL_QA, 'Real model call needs its original first independent output QA')
            raw = load(done['raw_ref'])
            require(raw.get('actual_model_call') is True and raw['case_id'] == case and
                    json.loads(raw['raw_output']) == done['parsed'], 'Canonical raw is not an actual accepted model output')
            same_ref(raw['input_ref'], input_ref, 'Actual raw used another model input')
            same_ref(raw['first_input_qa_ref'], first_ref, 'Actual raw used another first input proof')
            same_ref(proof['raw_ref'], done['raw_ref'], 'First real output QA binds another raw')
            if 'adapter_inside' in raw:
                require(raw['adapter_before'] == raw['adapter_after'] == [False] * 144 and
                        raw['adapter_inside'] == [True] * 144, 'Actual canonical generation was not frozen BASE-only')
        entry['actual_model_call'] = not is_alias
        entry['input_ref'] = input_ref
        entry['first_input_qa_ref'] = first_ref
        state = dict(entry=entry, done=done, proof=proof, input=document, alias=is_alias)
        by_case[case] = state; by_done[key] = state

    real = {case: value for case, value in by_case.items() if not value['alias']}
    aliases = {case: value for case, value in by_case.items() if value['alias']}
    require(len(real) == model_count and len(aliases) == alias_count, 'Recounted actual calls/aliases differ from completion')
    table_refs = set()
    for case, value in aliases.items():
        entry, done, proof, document = value['entry'], value['done'], value['proof'], value['input']
        canonical_case = done['alias_of']
        require(entry['alias_of'] == canonical_case and canonical_case in real, 'Canonical must be a real same-stage case, never an alias chain')
        canonical = real[canonical_case]
        canonical_done = canonical['done']
        for object_ in (entry, done, proof):
            same_ref(object_['canonical_model_done_ref'], canonical['entry']['decision_ref'], 'Alias canonical done differs from the actual same-stage real call')
        require(proof['status'] == ALIAS_QA, 'Alias requires its own native application QA, not another first model QA')
        for object_ in (entry, proof):
            same_ref(object_['canonical_output_QA_ref'], canonical['entry']['output_qa_ref'], 'Alias must adopt the actual canonical first output QA')
        # GPU-time alias done deliberately has no future output-QA dependency.
        for object_ in (entry, done, proof):
            same_ref(object_['identical_input_equality_ref'], entry['identical_input_equality_ref'], 'Alias equality table reference differs across proof chain')
        same_ref(done['raw_ref'], canonical_done['raw_ref'], 'Alias may only reuse the actual canonical raw')
        require(done['parsed'] == canonical_done['parsed'], 'Alias parsed answer changed from actual canonical output')
        require(native_identity(document) == native_identity(canonical['input']) and
                candidate_semantics(document) == candidate_semantics(canonical['input']),
                'Alias native source bytes/PTS/ordinals/window/candidate ordering differ')
        table = load(entry['identical_input_equality_ref'])
        table_refs.add(ref_key(entry['identical_input_equality_ref']))
        require(table['schema'] == TABLE_SCHEMA and table.get('registered_before_GPU') is True and
                table['actual_parameters'] == parameters and table['logical_count'] == logical and
                table['model_count'] == model_count and table['generation'] == GENERATION,
                'Pre-GPU alias table generation/grammar denominator or model scope changed')
        rows = table['aliases']
        require(isinstance(rows, list) and len(rows) == alias_count and
                {row['alias_case_id'] for row in rows} == set(aliases) and
                len({row['alias_case_id'] for row in rows}) == len(rows), 'Frozen alias table membership differs')
        row = next(row for row in rows if row['alias_case_id'] == case)
        require(row['canonical_case_id'] == canonical_case and row.get('native_identity_equal') is True and
                row.get('candidate_semantics_equal') is True, 'Frozen alias pair or native equality was not registered')
        same_ref(row['alias_input_ref'], entry['input_ref'], 'Frozen alias table points at another alias input')
        same_ref(row['canonical_input_ref'], canonical['entry']['input_ref'], 'Frozen alias table points at another canonical input')
        signature = row['input_signature']
        require(isinstance(signature, dict) and set(signature) ==
                {'input_ids', 'attention_mask', 'pixel_values_videos', 'video_grid_thw'} and
                all(isinstance(value, dict) and isinstance(value.get('shape'), list) and
                    isinstance(value.get('dtype'), str) and isinstance(value.get('sha256'), str) and
                    len(value['sha256']) == 64 for value in signature.values()), 'Complete four-tensor shape/dtype/bit signature required')
        require(type(row['candidate_count']) is int and row['candidate_count'] == len(document['candidate_events']) ==
                len(canonical['input']['candidate_events']) and signature ==
                document['retarget']['full_tensor_signature'] == canonical['input']['retarget']['full_tensor_signature'],
                'Actual complete input signature or candidate-count grammar domain differs')
        cpu = load(table['cpu_completion_ref'])
        cpu_rows = cpu['entries']
        require(cpu['status'] == 'PASS_ALL_FIRST_INPUT_QA' and cpu['actual_count'] == logical and
                len(cpu_rows) == logical and {row['case_id'] for row in cpu_rows} == set(by_case),
                'Frozen pre-GPU full logical first input-QA completion differs')
        cpu_by_case = {row['case_id']: row for row in cpu_rows}
        for member in by_case:
            same_ref(cpu_by_case[member]['input_ref'], by_case[member]['entry']['input_ref'], 'Alias pair input differs from frozen original CPU completion')
            same_ref(cpu_by_case[member]['first_qa_ref'], by_case[member]['entry']['first_input_qa_ref'], 'Alias pair first QA differs from frozen original CPU completion')
    require(len(table_refs) <= 1, 'One production stage must use one frozen identical-input alias table')
    return ([value['entry'] for value in by_case.values()],
            dict(logical_cases=logical, actual_model_calls=len(real), adopted_identical_input_aliases=len(aliases),
                 first_model_output_QA_count=len(real), alias_application_QA_count=len(aliases)))
