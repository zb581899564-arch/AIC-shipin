"""STAR1300 lineage checks shared by conditional CPU/GPU/package stages.

These functions read metadata only. The old55 STOP is an ancestor, never an
admission. No checkpoint, tensor, source pixel, processor or model is loaded.
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'pair_code_17'))
from pair_common import bound, read, ref, save, require

REFS = ('star_GPU69_code', 'star_GPU69_registration', 'training_completion',
        'training_quality_admission', 'frozen_GPU55_code', 'frozen_GPU55_registration',
        'old55_STOP', 'old55_completion', 'old55_progress',
        'old55_adapter_weights', 'old55_value_weights', 'adapter_weights', 'value_weights')


def validate_final1300(reg, training, quality):
    require(training['status'] == 'COMPLETE_FIXED_FINAL1300_STAR_VALUES_NOT_QUALITY'
        and training['completed_updates'] == 1300 and training['successful_micro'] == 5200
        and training['actual_training_forwards'] == 10400
        and training['new_completed_updates'] == 800 and training['new_successful_micro'] == 3200
        and training['actual_new_training_forwards'] == 6400
        and all(training[k] is True for k in ('adapter_reload_all288_exact', 'head_reload_exact', 'beta_reload_exact',
            'inherited_optimizer_exact', 'inherited_trainables_exact', 'inherited_rng_restored', 'original55_quality_remains_STOP'))
        and training['GPU_registration'] == reg['star_GPU69_registration']
        and training['inherited_completion'] == reg['old55_completion']
        and training['inherited_progress'] == reg['old55_progress']
        and training['adapter_weights'] == reg['adapter_weights'] and training['value_weights'] == reg['value_weights']
        and training['adapter_weights'] != reg['old55_adapter_weights']
        and training['value_weights'] != reg['old55_value_weights'], 'Actual separate STAR1300 final weights and inherited500 lineage required')
    require(quality['status'] == 'PASS_STAR_NATIVE20_ONLY' and quality['primary'] == 'UTILITY'
        and quality['evaluation']['quality']['admitted'] is True and quality['confirm_admitted'] is True
        and quality['fixed_final_checkpoint'] is True and quality['production_admitted'] is False
        and quality['final_update'] == 1300 and quality['new_updates'] == 800
        and quality['training_completion'] == reg['training_completion']
        and quality['registration'] == reg['star_GPU69_registration']
        and quality['inherited_STOP'] == reg['old55_STOP']
        and quality['inherited_completion'] == reg['old55_completion']
        and quality['inherited_progress'] == reg['old55_progress']
        and quality['adapter_weights'] == reg['adapter_weights'] and quality['value_weights'] == reg['value_weights'],
        'New STAR native20 quality PASS required; old55 STOP can never grant admission')


def validate_ancestry(reg, registration69, old_stop, old_completion, old_registration):
    require(registration69['schema'] == 'UTILITY_CONNECTED_STAR_CONTINUATION_V69'
        and registration69['GPU_code'] == reg['star_GPU69_code']
        and registration69['original_GPU55'] == reg['frozen_GPU55_registration']
        and registration69['frozen_GPU55_code'] == reg['frozen_GPU55_code']
        and all(registration69[k] == reg[k] for k in ('old55_STOP', 'old55_completion', 'old55_progress',
            'old55_adapter_weights', 'old55_value_weights')),
        'Exact independently registered69 continuation and55 ancestor refs required')
    require(old_stop['status'] == 'STOP_UTILITY_SCREEN20_REJECTED' and old_stop['confirm_admitted'] is False
        and old_stop['training_completion'] == reg['old55_completion']
        and old_completion['status'] == 'COMPLETE_FIXED_FINAL500_UTILITY_VALUES_NOT_QUALITY'
        and old_completion['completed_updates'] == 500 and old_completion['successful_micro'] == 2000
        and old_completion['actual_training_forwards'] == 4000
        and old_completion['GPU_registration'] == reg['frozen_GPU55_registration']
        and old_completion['progress'] == reg['old55_progress']
        and old_completion['adapter_weights'] == reg['old55_adapter_weights']
        and old_completion['value_weights'] == reg['old55_value_weights']
        and old_registration['GPU_code'] == reg['frozen_GPU55_code'], 'Preserve actual failed55 evidence and complete500 identity')
    for key in ('model_config', 'old_TIME', 'old_PAIR', 'old_CROP'):
        require(registration69[key] == old_registration[key] == reg[key], 'STAR inherited physical/runtime identity differs: '+key)


def check(reg):
    require(bound(reg['identity_code']) == Path(__file__).resolve(), 'Exact STAR72 lineage implementation required')
    for key in REFS:
        bound(reg[key])
    training = read(bound(reg['training_completion'])); quality = read(bound(reg['training_quality_admission']))
    validate_final1300(reg, training, quality)
    validate_ancestry(reg, read(bound(reg['star_GPU69_registration'])), read(bound(reg['old55_STOP'])),
        read(bound(reg['old55_completion'])), read(bound(reg['frozen_GPU55_registration'])))
    return training, quality


def write_bindings(out, reg, quality):
    """CPU emits minimal qualifications, after checking original results."""
    keys = ('status', 'primary', 'evaluation', 'confirm_admitted', 'production_admitted', 'fixed_final_checkpoint',
        'final_update', 'new_updates', 'training_completion', 'registration', 'inherited_STOP',
        'inherited_completion', 'inherited_progress', 'adapter_weights', 'value_weights')
    slim = {k:quality[k] for k in keys}
    slim['evaluation'] = dict(quality=dict(admitted=quality['evaluation']['quality']['admitted']))
    save(out/'native_qualification_binding.json', dict(schema='STAR1300_NATIVE20_CPU_QUALIFICATION_BINDING_V72',
        source_quality=reg['training_quality_admission'], identity_code=reg['identity_code'],
        quality=slim, CPU_only_source_review=True, targets_included=False))
    save(out/'old55_STOP_binding.json', dict(schema='STAR72_INHERITED_FAILED55_CPU_BINDING',
        source_STOP=reg['old55_STOP'], identity_code=reg['identity_code'],
        status='STOP_UTILITY_SCREEN20_REJECTED', confirm_admitted=False,
        training_completion=reg['old55_completion'], CPU_only_source_review=True, targets_included=False))


def check_gpu(reg):
    """GPU parses only CPU qualifications; it never opens target/evaluation rows."""
    require(bound(reg['identity_code']) == Path(__file__).resolve(), 'Exact STAR72 lineage implementation required')
    for key in REFS:
        bound(reg[key])
    binding = read(bound(reg['training_quality_binding']))
    require(binding['schema'] == 'STAR1300_NATIVE20_CPU_QUALIFICATION_BINDING_V72'
        and binding['source_quality'] == reg['training_quality_admission']
        and binding['identity_code'] == reg['identity_code'] and binding['CPU_only_source_review'] is True
        and binding['targets_included'] is False, 'Exact actual CPU-qualified STAR native20 metadata required')
    stop = read(bound(reg['old55_STOP_binding']))
    require(stop['schema'] == 'STAR72_INHERITED_FAILED55_CPU_BINDING' and stop['source_STOP'] == reg['old55_STOP']
        and stop['identity_code'] == reg['identity_code'] and stop['CPU_only_source_review'] is True
        and stop['targets_included'] is False, 'Exact actual CPU-reviewed old55 STOP binding required')
    training = read(bound(reg['training_completion'])); quality = binding['quality']
    validate_final1300(reg, training, quality)
    validate_ancestry(reg, read(bound(reg['star_GPU69_registration'])), stop,
        read(bound(reg['old55_completion'])), read(bound(reg['frozen_GPU55_registration'])))
    return training, quality
