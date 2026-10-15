"""Actual pre-training static426/521 byte admission; no final/model/media work."""
import argparse
from pathlib import Path
import sys

from common import admit, require, save, verify_lock
import candidate_support as cs

DEFERRED_LIBRARIES = ('torch', 'transformers', 'av', 'numpy', 'peft')


def execute(contract, output):
    out = Path(output).resolve()
    require(not out.exists() and out.parent.is_dir(), 'fresh static preflight file in existing directory required')
    candidate = Path(contract['config']['candidate_output_dir']).resolve()
    require(not candidate.exists() and out != candidate and candidate not in out.parents,
            'static preflight must not create candidate output')
    # This new process should never import a model/decoder library. There is
    # deliberately no CUDA_VISIBLE_DEVICES or hardware capacity admission gate.
    require(not any(name in sys.modules for name in DEFERRED_LIBRARIES),
            'static preflight process already imported model/processor/decoder libraries')
    prepared = cs.prepare(contract)
    require(not any(name in sys.modules for name in DEFERRED_LIBRARIES),
            'static candidate preparation imported model/processor/decoder libraries')
    require(not candidate.exists(), 'static preparation unexpectedly created candidate output')
    attempts = prepared['attempts']
    require(len(attempts) == 521 and len({a['video_id'] for a in attempts}) == 426 and
            sum(a['changed'] for a in attempts) == 116, 'actual fixed static denominator differs')
    verify_lock(contract['lock_path'], contract['lock_sha'])
    spec = prepared['spec']
    receipt = dict(status='PASS_ACTUAL_CPU_STATIC_FIXED_426_521_CANDIDATE_INPUT_BINDINGS', utc=cs.utc(),
        config_sha256=contract['config_sha'], lock_sha256=contract['lock_sha'],
        candidate_contract=prepared['spec_ref'], records=426, planned_temporal_calls=521,
        changed_windows=116, unchanged_windows=405, clock_records=len(prepared['clocks']),
        original_spatial_anchor_rows=prepared['space_stage']['rows'], static_bindings_only=True,
        actual_byte_bound_inputs={k:spec[k] for k in ('plan', 'manifest', 'clock_registry', 'changed_cpu_acceptance')},
        actual_byte_bound_space=spec['space'], strict_loader_root=spec['strict_loader_root'],
        model_loaded=False, processor_loaded=False, native_decoder_called=False,
        model_processor_decoder_libraries_imported=False, new_model_calls=0,
        new_native_decodes=0, processor_calls=0, new_optimizer_updates=0,
        candidate_output_created=False, final_adapter_or_quality_receipt_required=False,
        fresh_temporal_runtime_verified=False, real_11_strict_ZIP_verified=False,
        quality_claim=False, training_started=False)
    save(out, receipt)
    return receipt


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('config', 'lock', 'expected-lock', 'output'):
        p.add_argument('--'+name, required=True)
    args = p.parse_args()
    contract = admit(args.config, args.lock, args.expected_lock, 'train')
    try:
        report = execute(contract, args.output)
    except BaseException as exc:
        target = Path(args.output).with_suffix('.failure.json')
        if target.parent.is_dir() and not target.exists():
            cs.failure(target, exc)
        raise
    print(__import__('json').dumps({k:report[k] for k in ('status', 'records', 'planned_temporal_calls', 'new_model_calls', 'new_native_decodes')}))


if __name__ == '__main__':
    main()
