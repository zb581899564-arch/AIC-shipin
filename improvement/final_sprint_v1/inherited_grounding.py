"""Explicit, SHA-bound adoption after the first grounding schema failure.

Only actual old successful answers whose tokens pass the new JSON grammar are
adopted. The original failure, invalid answer, wrapper and costs remain intact.
No claim or model output is relabelled as a new inference.
"""
from .contracts import checked, ref, require, stable_key, strict_load
from .spatial import parse_grounding


def validate_manifest(assets, identity):
    manifest = strict_load(checked(identity))
    require(manifest.get('schema') == 'AIC_GROUNDING_GRAMMAR_ADOPTION_V1',
            'Wrong explicit grounding adoption schema')
    require(manifest['new_implementation'] == assets['source_commit']['commit'],
            'Grounding adoption is for another new implementation')
    old = strict_load(checked(manifest['old_assets']))
    wrapper = strict_load(checked(manifest['old_wrapper']))
    require(wrapper['asset_lock'] == manifest['old_assets'] and wrapper['work_terminated'] is True
            and wrapper['no_external_task_signaled'] is True and wrapper['child_exit_code'] == 1,
            'Exact natural failed wrapper required before cross-code adoption')
    require(old['source_commit']['commit'] == 'a02403adf6f8a07dd618191771a382cea6129c06',
            'Only the audited first unstructured grounding implementation is eligible')
    for key in ('qwen', 'protected_baselines', 'sources', 'baseline_parameter_receipts'):
        require(old[key] == assets[key], 'Grounding adoption changed actual inputs/model: ' + key)
    require(manifest['new_grammar_source'] == ref(__file__.replace('inherited_grounding.py', 'grounding_grammar.py')),
            'Grammar replay proof uses different source bytes')
    result = {}
    for row in manifest['rows']:
        claim = strict_load(checked(row['claim']))
        success = strict_load(checked(row['success']))
        packet = strict_load(checked(row['returned']))
        require(claim['task_id'] == row['task_id'] and claim['binding']['base']['asset_lock'] == manifest['old_assets'],
                'Inherited call was not made against the original bound inputs')
        require(success['artifacts']['result'] == row['returned'] and
                packet['binding_sha256'] == claim['binding_sha256'] == stable_key(claim['binding']),
                'Inherited successful raw/claim identity differs')
        replay = row['grammar_replay']
        value = packet['result']
        require(replay['valid'] is True and replay['new_model_calls'] == 0 and
                replay['output_token_sha256'] == stable_key(value['output_token_ids']) and
                replay['input_sha256'] == value['input_sha256'], 'Actual CPU token replay evidence differs')
        parse_grounding(value['raw_text'], 3)
        require(row['task_id'] not in result, 'Duplicate inherited grounding task')
        result[row['task_id']] = (claim['binding']['call'], row['returned'])
    return result


def adopt_result(entries, task_id, call_binding):
    if task_id not in entries:
        return None
    old_call, identity = entries[task_id]
    require(old_call == call_binding, 'Inherited frame pixels/native PTS/prompt/model changed')
    packet = strict_load(checked(identity))
    result = dict(packet['result'])
    result['adopted_from_original_success'] = identity
    result['new_inference_calls_for_adoption'] = 0
    return result, identity
