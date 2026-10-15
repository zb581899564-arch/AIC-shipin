"""In-memory proof-chain checks; no production, file write, or inference."""
from copy import deepcopy
import hashlib
import json

from production_evidence import (ALIAS_DONE, ALIAS_QA, GENERATION, INPUT_QA, REAL_QA,
                                  TABLE_SCHEMA, ref_key, validate_production_evidence)

PARAMETERS = 8782459120


def fixture():
    documents, refs = {}, {}

    def add(name, value):
        reference = dict(path='/synthetic/' + name, sha256=hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest())
        documents[ref_key(reference)] = value
        refs[name] = reference
        return reference

    signature = {name: dict(shape=[1, 64], dtype='torch.int64' if name != 'pixel_values_videos' else 'torch.float32', sha256='a' * 64)
                 for name in ('input_ids', 'attention_mask', 'pixel_values_videos', 'video_grid_thw')}
    parsed = dict(ordinary=[0], redundant=[0], action=[30, 40], reaction=[], information=[])
    inputs = {}
    for case, source in (('canonical', '0'), ('alias', '1')):
        request = dict(case_id=case, source_id=source, source_sha256='b' * 64, source_ordinals=list(range(64)),
                       exact_pts=[str(index) for index in range(64)], window_exact=['0', '64'],
                       window_native_end_exact='64', window_native_end_ordinal=64,
                       candidate_events=[dict(event_id=case + str(index), original_interval_exact=[str(index * 20), str(index * 20 + 10)],
                                               selected_interval_exact=[str(index * 20), str(index * 20 + 10)], decision='KEEP') for index in range(2)],
                       retarget=dict(full_tensor_signature=deepcopy(signature)))
        inputs[case] = request
        input_ref = add(case + '/input', request)
        add(case + '/input_qa', dict(status=INPUT_QA, input_ref=input_ref, first_qa_not_repeated=True,
                                    native_vision_adopted=True, vision_processor_calls=0, media_decodes=0))
    cpu_ref = add('cpu_completion', dict(status='PASS_ALL_FIRST_INPUT_QA', actual_count=2,
        entries=[dict(case_id=case, input_ref=refs[case + '/input'], first_qa_ref=refs[case + '/input_qa'])
                 for case in ('canonical', 'alias')]))
    table_ref = add('table', dict(schema=TABLE_SCHEMA, logical_count=2, model_count=1, registered_before_GPU=True,
        actual_parameters=PARAMETERS, generation=deepcopy(GENERATION), cpu_completion_ref=cpu_ref,
        aliases=[dict(alias_case_id='alias', canonical_case_id='canonical', alias_input_ref=refs['alias/input'],
                      canonical_input_ref=refs['canonical/input'], input_signature=signature, candidate_count=2,
                      native_identity_equal=True, candidate_semantics_equal=True)]))
    raw_ref = add('canonical/raw', dict(case_id='canonical', actual_model_call=True, raw_output=json.dumps(parsed),
        input_ref=refs['canonical/input'], first_input_qa_ref=refs['canonical/input_qa'],
        adapter_before=[False] * 144, adapter_inside=[True] * 144, adapter_after=[False] * 144))
    real_done_ref = add('canonical/done', dict(case_id='canonical', parsed=deepcopy(parsed), raw_ref=raw_ref,
        input_ref=refs['canonical/input'], first_input_qa_ref=refs['canonical/input_qa']))
    real_qa_ref = add('canonical/output_qa', dict(status=REAL_QA, done_ref=real_done_ref, raw_ref=raw_ref,
        first_input_qa_ref=refs['canonical/input_qa'], parsed=deepcopy(parsed), CPU_only=True, new_model_calls=0))
    alias_done_ref = add('alias/done', dict(status=ALIAS_DONE, actual_model_call=False, case_id='alias', alias_of='canonical',
        canonical_model_done_ref=real_done_ref, identical_input_equality_ref=table_ref, input_ref=refs['alias/input'],
        first_input_qa_ref=refs['alias/input_qa'], raw_ref=raw_ref, parsed=deepcopy(parsed)))
    alias_qa_ref = add('alias/application_qa', dict(status=ALIAS_QA, done_ref=alias_done_ref,
        canonical_model_done_ref=real_done_ref, canonical_output_QA_ref=real_qa_ref,
        identical_input_equality_ref=table_ref, first_input_qa_ref=refs['alias/input_qa'],
        parsed=deepcopy(parsed), CPU_only=True, new_model_calls=0))
    real_entry = dict(inputs['canonical'], decision_ref=real_done_ref, output_qa_ref=real_qa_ref)
    alias_entry = dict(inputs['alias'], actual_model_call=False, alias_of='canonical', decision_ref=alias_done_ref,
        output_qa_ref=alias_qa_ref, input_ref=refs['alias/input'], first_input_qa_ref=refs['alias/input_qa'],
        canonical_model_done_ref=real_done_ref, canonical_output_QA_ref=real_qa_ref, identical_input_equality_ref=table_ref)
    completion = dict(logical_cases=2, actual_model_calls=1, adopted_identical_input_aliases=1,
        first_model_output_QA_count=1, alias_application_QA_complete=True, alias_application_QA_count=1,
        entries=[real_entry, alias_entry])
    return completion, documents, refs


def check(completion, documents):
    return validate_production_evidence(completion, lambda reference: documents[ref_key(reference)], PARAMETERS)


def rejected(mutator):
    completion, documents, refs = fixture()
    mutator(completion, documents, refs)
    try:
        check(completion, documents)
    except ValueError:
        return
    raise AssertionError('Expected alias proof-chain rejection')


def main():
    completion, documents, refs = fixture()
    snapshot = deepcopy((completion, documents))
    entries, counts = check(completion, documents)
    assert counts == dict(logical_cases=2, actual_model_calls=1, adopted_identical_input_aliases=1,
                          first_model_output_QA_count=1, alias_application_QA_count=1)
    assert [entry['actual_model_call'] for entry in entries] == [True, False]
    assert (completion, documents) == snapshot
    # The ordinary no-alias completion still derives real calls from its raw
    # and original first output proof, without needing optional alias fields.
    legacy = dict(actual_model_calls=1, entries=[deepcopy(completion['entries'][0])])
    assert check(legacy, documents)[1]['adopted_identical_input_aliases'] == 0
    rejected(lambda c, d, r: c.update(actual_model_calls=2))
    rejected(lambda c, d, r: c.update(alias_application_QA_count=0))
    rejected(lambda c, d, r: c['entries'][1].update(actual_model_call=True))
    rejected(lambda c, d, r: d[ref_key(r['canonical/raw'])].update(actual_model_call=False))
    rejected(lambda c, d, r: d[ref_key(r['canonical/output_qa'])].update(status=ALIAS_QA))
    rejected(lambda c, d, r: d[ref_key(r['alias/application_qa'])].update(status=REAL_QA))
    rejected(lambda c, d, r: d[ref_key(r['alias/application_qa'])].update(canonical_output_QA_ref=r['alias/application_qa']))
    rejected(lambda c, d, r: d[ref_key(r['alias/done'])].update(alias_of='alias'))
    rejected(lambda c, d, r: d[ref_key(r['alias/done'])].update(raw_ref=r['alias/input']))
    rejected(lambda c, d, r: d[ref_key(r['table'])].update(registered_before_GPU=False))
    rejected(lambda c, d, r: d[ref_key(r['table'])]['generation'].update(do_sample=True))
    rejected(lambda c, d, r: d[ref_key(r['table'])]['aliases'][0].update(candidate_count=1))
    rejected(lambda c, d, r: d[ref_key(r['alias/input'])]['retarget']['full_tensor_signature']['input_ids'].update(sha256='c' * 64))

    def wrong_native(c, d, r):
        c['entries'][1]['source_sha256'] = 'c' * 64
        d[ref_key(r['alias/input'])]['source_sha256'] = 'c' * 64
    rejected(wrong_native)

    def wrong_order(c, d, r):
        c['entries'][1]['candidate_events'] = list(reversed(c['entries'][1]['candidate_events']))
        d[ref_key(r['alias/input'])]['candidate_events'] = list(reversed(d[ref_key(r['alias/input'])]['candidate_events']))
    rejected(wrong_order)

    def fabricated_parsed(c, d, r):
        changed = dict(ordinary=[], redundant=[], action=[], reaction=[], information=[])
        d[ref_key(r['alias/done'])]['parsed'] = changed
        d[ref_key(r['alias/application_qa'])]['parsed'] = changed
    rejected(fabricated_parsed)
    rejected(lambda c, d, r: d[ref_key(r['cpu_completion'])]['entries'][1].update(first_qa_ref=r['canonical/input_qa']))
    print('PASS_IN_MEMORY_REAL_MODEL_ALIAS_INPUT_SIGNATURE_NATIVE_ORDER_QA_CHAIN_AND_COUNTS')


if __name__ == '__main__':
    main()
