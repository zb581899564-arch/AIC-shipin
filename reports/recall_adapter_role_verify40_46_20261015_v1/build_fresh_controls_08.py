"""Build separate first-fresh controls; preserve every prior frozen file."""
import ast
from pathlib import Path

WORK=Path(__file__).resolve().parents[2]


def replace(source,old,new):
    assert source.count(old)==1,(old[:100],source.count(old))
    return source.replace(old,new,1)


def main():
    fresh=WORK/'improvement/recall_adapter_role_fresh_v1';positive=WORK/'improvement/recall_adapter_role_confirm_v1'
    assert not (Path(__file__).parent/'fresh_chain_launch_09.json').exists(), 'Never rebuild deployed/frozen code'
    fresh.mkdir(exist_ok=True);positive.mkdir(exist_ok=True)
    for p in (WORK/'improvement/recall_positive_fresh_v1').glob('*.py'):
        text=p.read_text(encoding='utf8')
        if p.name=='fresh_registration.py':
            text=text.replace('REGISTERED_POSITIVE_FIRST_FRESH_CONFIRM_V1','REGISTERED_ROLE_FIRST_FRESH_CONFIRM_V1')
            text=text.replace("protocol['candidate'] == 'OLD_EXPLICIT_KEEP_PLUS_POSITIVE_EVIDENCE_NEW_ADMISSION'","protocol['candidate'] == 'BASE_ONLY_POSITIVE_ADMISSION_SAME_INPUT_PAIR'")
            text=text.replace("selection['status'] == 'PASS_DEV_FROZEN_FOR_FIRST_CONFIRMATION' and selection['confirm_metrics_examined'] is False","selection['status'] == 'PASS_ROLE_DEV_FROZEN_REQUIRES_NEW_UNEXPOSED_CONFIRMATION' and selection['new_confirm_metrics_examined'] is False")
            text=text.replace("selection['protocol_sha256'] == reg['protocol_ref']['sha256']","selection['protocol_ref'] == reg['protocol_ref']")
            text=text.replace("result['status'] == 'PASS_POSITIVE_DEV_FROZEN_PENDING_FRESH_CONFIRMATION'","result['status'] == 'PASS_ADAPTER_ROLE_DEV_PENDING_NEW_FRESH_CONFIRM'")
            text=text.replace("registry['schema'] == 'POSITIVE_FRESH_MEDIA_REGISTRATION_V1'","registry['schema'] == 'ROLE_FIRST_FRESH_MEDIA_REGISTRATION_V1'")
            text=text.replace("registry['status'] == 'REGISTERED_POSITIVE_FIRST_FRESH_MEDIA_NATIVE'","registry['status'] == 'REGISTERED_ROLE_FIRST_FRESH_MEDIA_NATIVE'")
            text=text.replace("complete['status'] == 'PASS_POSITIVE_FRESH_MEDIA_NATIVE_SECONDS_NOT_INPUT_OR_GPU'","complete['status'] == 'PASS_ROLE_FRESH_MEDIA_NATIVE_SECONDS_NOT_INPUT_OR_GPU'")
            text=text.replace("candidates['exclusions']['all_old_conservative_plus_acquired_IDs']","candidates['all_old_protected_and_acquired_IDs']")
            text=text.replace("registry['prior_media_receipts']","registry['prior18_media_receipts']")
            original=(WORK/'improvement/recall_positive_fresh_recovery_v2/fresh_registration.py').read_text(encoding='utf8')
            function=original[original.index('def validate_source_grouped_order('):original.index('def first_remaining_launch(')]
            text+='\n\n'+function
        if p.name=='first_input_qa.py':
            text=replace(text,'from fresh_registration import registration, media_files','from fresh_registration import registration, media_files, validate_source_grouped_order')
            text=replace(text,"io.read(root/'confirm/view_plan.json') == plan and\n        [v['case_id'] for v in plan['unique_views']] == [e['case_id'] for e in complete['entries']],",
                "io.read(root/'confirm/view_plan.json') == plan and\n        complete['registration_sha256'] == io.sha(root/'positive_fresh_registration.json'),")
            text=replace(text,"    views = {v['case_id']: v for v in plan['unique_views']}","    validate_source_grouped_order(plan, complete['entries'], [row['video_id'] for row in reference['accepted']])\n    views = {v['case_id']: v for v in plan['unique_views']}")
        if p.name=='fresh_chain.py':
            text=replace(text,"io.require(code == positive_root/'code', 'Use exact frozen dev positive code for confirmation')",
                "io.require(code == positive_root/'confirm_code', 'Use frozen same-factor BASE-admission confirmation implementation')")
            text=replace(text,"devreg = io.read(reg['development_registration_ref']['path'])","devreg = io.read(reg['positive_template_registration_ref']['path'])")
            text=replace(text,"value = dict(devreg, stage_group='confirm', protocol_ref=reg['protocol_ref'],",
                "value = dict(devreg, status='REGISTERED_ROLE_POSITIVE_CONFIRM_V1', activation_contract_ref=reg['activation_contract_ref'], role_runtime_ref=reg['role_runtime_ref'], stage_group='confirm', protocol_ref=reg['protocol_ref'],")
            text=text.replace('PASS_POSITIVE_FRESH_CONFIRM_PENDING_FIXED40','PASS_ROLE_FRESH_CONFIRM_PENDING_FIXED40').replace('STOP_POSITIVE_CONFIRM_REJECTED','STOP_ROLE_FRESH_CONFIRM_REJECTED')
        ast.parse(text)
        with (fresh/p.name).open('w',encoding='utf8') as stream:stream.write(text)
    for p in (WORK/'improvement/recall_positive_admission_v1').glob('*.py'):
        text=p.read_text(encoding='utf8')
        if p.name=='positive_io.py':
            text=replace(text,"REG_STATUS = 'REGISTERED_POSITIVE_ADMISSION_V1'","REG_STATUS = 'REGISTERED_ROLE_POSITIVE_CONFIRM_V1'")
            text=text.replace("protocol['candidate'] == 'OLD_EXPLICIT_KEEP_PLUS_POSITIVE_EVIDENCE_NEW_ADMISSION'","protocol['candidate'] == 'BASE_ONLY_POSITIVE_ADMISSION_SAME_INPUT_PAIR'")
            text=text.replace("selection['status'] == 'PASS_DEV_FROZEN_FOR_FIRST_CONFIRMATION'","selection['status'] == 'PASS_ROLE_DEV_FROZEN_REQUIRES_NEW_UNEXPOSED_CONFIRMATION'")
            text=text.replace("selection['confirm_metrics_examined'] is False","selection['new_confirm_metrics_examined'] is False")
            text=text.replace("selection['protocol_sha256'] == reg['protocol_ref']['sha256']","selection['protocol_ref'] == reg['protocol_ref']")
            text=replace(text,"require(group in ('dev', 'confirm'), 'Explicit dev/confirm group required')","require(group == 'confirm', 'This frozen role code permits first independent confirmation only')")
        if p.name=='positive_runtime.py':
            text=replace(text,"    runtime = legacy.runtime_only(); tm = io.tokens_module(reg)\n    import torch\n    out = base(root, group)/'gpu_01'",
                "    runtime = legacy.runtime_only(); tm = io.tokens_module(reg)\n    role = io.load_module('_frozen_role_dev_runtime', reg['role_runtime_ref']); ac = role.activation_contract(reg, io)\n    import torch\n    out = base(root, group)/'gpu_01'")
            text=replace(text,"        io.save(out/'model_identity.json', dict(identity=identity, adapter_enabled_for_all_calls=True, optimizer_updates=0))",
                "        initial = ac.layer_state(model, False); names = initial['layer_names']; ac.inventory(model); ac.frozen_gradients(model)\n        io.save(out/'model_identity.json', dict(identity=identity, initial=initial, activation_role=role.ROLE, adapter_enabled_for_all_calls=False, physical_parameters=role.PARAMETERS, optimizer_updates=0))")
            text=replace(text,"            disabled = legacy.enabled_layers(model)","            before = dict(layer_state=ac.layer_state(model, False, names), gradients=ac.frozen_gradients(model))\n            io.save(folder/'activation_before.json', before)")
            text=replace(text,"            with torch.inference_mode():\n                generated = model.generate(**gpu, do_sample=False, max_new_tokens=c.MAX_OUTPUT_TOKENS,\n                    prefix_allowed_tokens_fn=grammar, return_dict_in_generate=True, output_scores=True)\n            torch.cuda.synchronize()",
                "            try:\n                with model.disable_adapter():\n                    inside = dict(layer_state=ac.layer_state(model, True, names), gradients=ac.frozen_gradients(model))\n                    io.save(folder/'activation_inside.json', inside)\n                    with torch.inference_mode():\n                        generated = model.generate(**gpu, do_sample=False, max_new_tokens=c.MAX_OUTPUT_TOKENS,\n                            prefix_allowed_tokens_fn=grammar, return_dict_in_generate=True, output_scores=True)\n                    torch.cuda.synchronize(); ac.layer_state(model, True, names); ac.frozen_gradients(model)\n            finally:\n                restored = ac.restore_frozen_gradients(model)\n                after = dict(layer_state=ac.layer_state(model, False, names), gradients=ac.frozen_gradients(model))\n                io.save(folder/'activation_after.json', dict(after=after, restored=restored))\n            ac.validate_restoration(before, inside, after, restored, names)\n            disabled = inside['layer_state']['disable_adapters']")
            text=replace(text,"input_evidence=evidence, adapter_disabled_layers=disabled, constraint_stats=grammar.stats))",
                "input_evidence=evidence, adapter_disabled_layers=disabled, constraint_stats=grammar.stats, activation_role=role.ROLE, actual_physical_parameters=role.PARAMETERS, activated_base_parameters=role.BASE_PARAMETERS))")
            text=replace(text,"            legacy.output_tokens(io.read(folder/'raw.json'))","            role.role_output(io.read(folder/'raw.json'))")
            text=replace(text,"request_ref=io.ref(folder/'request.json'), input_evidence=evidence, input_tokens=prefix,",
                "request_ref=io.ref(folder/'request.json'), activation_before_ref=io.ref(folder/'activation_before.json'), activation_inside_ref=io.ref(folder/'activation_inside.json'), activation_after_ref=io.ref(folder/'activation_after.json'), input_evidence=evidence, input_tokens=prefix,")
            text=replace(text,"        legacy = io.legacy(reg)\n        runtime, processor = legacy.cpu_processor()",
                "        legacy = io.legacy(reg)\n        role = io.load_module('_frozen_role_dev_runtime', reg['role_runtime_ref']); ac = role.activation_contract(reg, io)\n        model_meta = io.read(io.checked_ref(complete['model_identity_ref'])); names = model_meta['initial']['layer_names']\n        ac.serialized_state(model_meta['initial'], False, names)\n        runtime, processor = legacy.cpu_processor()")
            text=replace(text,"            ids = legacy.output_tokens(raw, done)",
                "            before = io.read(io.checked_ref(done['activation_before_ref'])); inside = io.read(io.checked_ref(done['activation_inside_ref'])); after = io.read(io.checked_ref(done['activation_after_ref']))\n            ac.validate_restoration(before, inside, after['after'], after['restored'], names)\n            ids = role.role_output(raw, done)")
        if p.name=='positive_evaluate.py':
            text=text.replace('PASS_POSITIVE_FRESH_CONFIRM_PENDING_FIXED40','PASS_ROLE_FRESH_CONFIRM_PENDING_FIXED40')
            text=text.replace("'STOP_POSITIVE_'+group.upper()+'_REJECTED'","'STOP_ROLE_FRESH_CONFIRM_REJECTED'")
        ast.parse(text)
        with (positive/p.name).open('w',encoding='utf8') as stream:stream.write(text)
    print('Created12 fresh +8 positive confirmation files, preserving all prior frozen files; not deployed')


if __name__=='__main__':main()
