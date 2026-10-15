"""Incremental check of the added real-first-QA metadata guards only."""
import ast
import copy


def run(backend_source):
    tree=ast.parse(backend_source)
    call=next(node for node in ast.walk(tree) if isinstance(node,ast.Call) and
        isinstance(node.func,ast.Name) and node.func.id=='require' and len(node.args)==2 and
        isinstance(node.args[1],ast.Constant) and node.args[1].value==
        'Actual first ordinary processor input QA cannot be replaced by byte-only checks')
    test=compile(ast.Expression(call.args[0]),'<actual-new-first-QA-guard>','eval')
    ref={'relative':'synthetic','sha256':'a'*64,'bytes':1};sig={'synthetic_signature':True}
    context=dict(consumer='C',manifest_ref=ref,manifest={'full_signature':sig},rgb_ref=ref,
        resource_ref=ref,ledger_ref=ref,evidence={'CPU_input_proof':ref},proof={'prepare_pid':1})
    first=dict(status='PASS_FIRST_INDEPENDENT_INPUT_REPLAY_ONLY_NOT_LEASE_ACCEPTANCE',consumer='C',CPU_only=True,
        first_independent_input_replay=True,normal_processor_from_original_RGB_verified=True,
        actual_first_independent_processor_encodes=1,input_manifest_ref=ref,full_input_signature=sig,
        original_RGB_ref=ref,resource_ref=ref,ledger_ref=ref,CPU_input_proof_ref=ref,new_model_calls=0,
        new_source_decodes=0,prepare_pid=1,verifier_pid=2)
    assert eval(test,{},dict(context,first=first)) is True
    for key,value in [('status','FAILED'),('CPU_input_proof_ref',dict(ref,sha256='b'*64)),
                      ('new_model_calls',1),('prepare_pid',3)]:
        bad=copy.deepcopy(first);bad[key]=value
        assert eval(test,{},dict(context,first=bad)) is False
    return dict(status='PASS_INCREMENTAL_REAL_FIRST_QA_METADATA_GUARDS',checks=5,
        synthetic_metadata_only=True,model_calls=0,processor_encodes=0,media_decodes=0,
        old_race_or_tensor_fixtures_repeated=False)
