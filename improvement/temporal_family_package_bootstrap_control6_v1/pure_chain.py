"""Narrow new CONTROL6 count/ref/provenance ABI checks, no actual closure read."""
from pathlib import Path


def run(module, binder_text):
    assert "controller['actual_total_model_calls_in_original_graph']==len(production['actual_unique_MODEL_ids'])" in binder_text
    assert "controller['actual_new_model_calls']==len(production['actual_unique_MODEL_ids'])" not in binder_text
    assert "TEMPORAL_FAMILY_PACKAGE_BOOTSTRAP_CONTROL6_V1" in binder_text

    class Closure:
        def __init__(self, completion):self.completion=completion;self.walks=[]
        def load(self, ref):return self.completion
        def absolute(self, ref):return module.comparable(ref)
        def walk(self, value):self.walks.append(value)

    ref={'path':'/cache/source_S_completion.json','sha256':'a'*64}
    inherited={'source_id':'S'}
    closure=Closure(inherited)
    module.validate_producer(closure,{'source_CPU_completion_ref':ref,'actual_producer_provenance':None},{},
                             {'source_reuse':{'S':ref}},Path('/INPUT5'))
    try:
        module.validate_producer(closure,{'source_CPU_completion_ref':ref,'actual_producer_provenance':None},{},
                                 {'source_reuse':{}},Path('/INPUT5'))
    except ValueError:
        pass
    else:
        raise AssertionError('Old writer cannot be invented without a real adopted success')
    phase={'path':'/new/source.py','sha256':'b'*64}
    backend={'path':'/new/backend.py','sha256':'c'*64}
    backend_admit={'path':'/new/backend_admission.json','sha256':'d'*64}
    phase_admit={'path':'/new/source_admission.json','sha256':'e'*64}
    declared={'prospective_phase_ref':phase,'prospective_backend_ref':backend_admit,
              'prospective_backend_code_ref':backend,
              'prospective_source_phase_admission_ref':dict(phase_admit,bytes=123),
              'actual_source_writer_execution_kind':'EXPLICIT_FUNCTION_GLOBALS_COPY_UNCHANGED_FROZEN_BYTECODE',
              'original_source_math_bytecode_unchanged':True,
              'original_preparation_code_ref':{'path':'/INPUT5/code/prepare_source.py','sha256':'f'*64}}
    new={'source_id':'S','prospective_producer_provenance':declared,'structural_producer_provenance_refs':{}}
    closure=Closure(new)
    production={'actual_prospective_source_phase_code_ref':phase,'prospective_backend_admission_ref':backend_admit,
                'actual_prospective_backend_code_ref':backend,'prospective_source_phase_admission_ref':phase_admit}
    module.validate_producer(closure,{'source_CPU_completion_ref':ref,'actual_producer_provenance':declared},
                             production,{'source_reuse':{}},Path('/INPUT5'))
    assert closure.walks==[declared]
    return {'status':'PASS_NEW_CONTROL6_BINDER_AST_AND_SYNTHETIC_PRODUCER_ABI_ONLY',
            'checks':['whole_graph_total_distinct_from_new_calls','old_SOURCE_requires_adopted_exact_receipt',
                      'new_actual_writer_refs_bound','same_path_SHA_with_optional_bytes_not_false_rejected'],
            'actual_production_metadata_reads':0,'old_ZIP_reads':0,'model_calls':0,'binder_calls':0,'package_calls':0}
