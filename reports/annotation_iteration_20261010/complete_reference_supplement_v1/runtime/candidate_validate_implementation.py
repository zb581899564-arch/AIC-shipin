"""Record pure logic verification and actual source identities; no runtime work."""
import argparse
import ast
import io
import json
from pathlib import Path
import sys
import unittest

from common import require, save, sha
import candidate_support as cs
import candidate_test


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--version', default='v1')
    args = p.parse_args()
    require(args.version.isascii() and args.version.replace('_', '').replace('-', '').isalnum(), 'safe version suffix required')
    here = Path(__file__).resolve().parent
    suffix = '' if args.version == 'v1' else '_'+args.version
    targets = [here/('candidate_dependency_manifest'+suffix+'.json'), here/('candidate_implementation_validation'+suffix+'.json')]
    require(all(not p.exists() for p in targets), 'implementation acceptance artifacts already exist')
    source = sorted(here.glob('candidate_*.py'))
    for p in source:
        ast.parse(p.read_text(encoding='utf-8'), filename=str(p))
    json.loads((here/'candidate_contract_schema.json').read_text(encoding='utf-8'))
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(candidate_test))
    forbidden = ('torch', 'transformers', 'av', 'numpy', 'peft')
    require(not any(name in sys.modules for name in forbidden), 'pure implementation validation imported a model/decoder dependency')
    print(stream.getvalue(), end='')
    require(result.wasSuccessful(), 'candidate pure logic tests failed')
    files = source+[here/'candidate_contract_schema.json', here/'candidate_IMPLEMENTATION.md']
    run = candidate_test.RUN
    dependencies = [dict(relative_path=name, local_mirror_sha256=sha(run/name)) for name in cs.DEPENDENCIES]
    manifest = dict(schema='FIXED_SILVER_CANDIDATE_DEPENDENCY_MANIFEST_V1', utc=cs.utc(),
        implementation_version=args.version,
        owned_sources=[dict(path=str(p.resolve()), sha256=sha(p)) for p in files],
        extra_historical_dependencies=dependencies,
        strict_loader_dependency='baseline_a_pts_v1/vendor/frozen_strict_loader/* recursive ALL files',
        dynamic_locked_inputs=['candidate_contract', 'plan', 'manifest', 'clock_registry',
            'registry.records[].clock_arrays', 'manifest.records[].source_path', 'changed_cpu_acceptance',
            'space.field_frames', 'space.field_shots', 'space.anchor_requests', 'space.anchor_output',
            'space.schedule_stage', 'space.spatial_stage'],
        config_projection=dict(candidate_contract=dict(path='ACTUAL_LINUX_ABSOLUTE_SPEC_PATH', sha256='ACTUAL_SPEC_SHA256')),
        fixed_input_shas=cs.FIXED_INPUT_SHAS, fixed_space_shas=cs.FIXED_SPACE_SHAS,
        local_mirror_dependency_hashes_are_informational=True,
        actual_Linux_paths_and_bytes_must_be_bound_by_new_lock=True)
    save(targets[0], manifest)
    report = dict(status='PASS_CANDIDATE_PURE_LOGIC_IMPLEMENTATION_ONLY', utc=cs.utc(),
        implementation_version=args.version,
        tests_run=result.testsRun, test_failures=len(result.failures), test_errors=len(result.errors),
        AST_parsed_candidate_sources=len(source), contract_schema_JSON='PASS',
        dependency_manifest=cs.ref(targets[0]), source_shas=manifest['owned_sources'],
        torch_transformers_av_numpy_peft_imported=False, new_model_calls=0, new_native_decodes=0,
        processor_calls=0, remote_transfers=0, real_521_runtime_verified=False,
        real_11_strict_ZIP_verified=False, training_admitted=False, scientific_quality_claim=False)
    save(targets[1], report)
    print(json.dumps({k:report[k] for k in ('status', 'tests_run', 'AST_parsed_candidate_sources', 'new_model_calls', 'new_native_decodes')}))


if __name__ == '__main__':
    main()
