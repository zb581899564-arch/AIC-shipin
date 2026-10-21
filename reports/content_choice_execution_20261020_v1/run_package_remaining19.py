"""Explicit CPU-only continuation after the preserved endpoint-policy failure."""
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import signal
import sys
import traceback

R = Path('/home/inspur/aic_video_work/content_choice_20261019_v1')
RECOVERY = R / 'package_recovery19'
OUT = R / 'package_contrast_remaining19'
sys.path[:0] = [str(RECOVERY), str(R / 'code')]

from improvement.native_preference_v1.assets import read_json, path_ref, check_ref, write_new
from improvement.content_choice_v1.contracts import code_identity, pipeline_parameters
from improvement.content_choice_v1.admission import package_refs
from clock_bridge19 import targeted_checks


def main():
    phase = 'CLAIM_AND_ADOPT_SUCCESSFUL_QA'
    try:
        assert os.environ.get('CUDA_VISIBLE_DEVICES') == ''
        def deadline(signum, frame):
            raise TimeoutError('Explicit remaining CPU stage exceeded1800seconds')
        signal.signal(signal.SIGALRM, deadline)
        signal.alarm(1800)
        registration = read_json(R / 'package_remaining_registration19.json')
        assert registration['approved'] is True
        for reference in registration['execution_code_refs'].values():
            check_ref(reference, R.parent)
        write_new(R / 'package_contrast_remaining_controller_started19.json', dict(
            utc=datetime.now(timezone.utc).isoformat(), pid=os.getpid(), argv=sys.argv,
            start_ticks=Path('/proc/self/stat').read_text().rsplit(')', 1)[1].split()[19]))
        production_path = check_ref(registration['production_ref'], R.parent)
        complete = read_json(production_path)
        assert complete['status'] == 'COMPLETE_PRODUCTION_NOT_PACKAGED'
        assert complete['source_count'] == 426 and complete['window_count'] == 522
        assert complete['code_identity'] == code_identity()
        failure = read_json(check_ref(registration['original_failure_ref'], R.parent))
        assert failure['error'] == 'Actual source PTS or physical endpoint differs from the frozen field'
        qa = read_json(check_ref(registration['successful_output_QA_ref'], R.parent))
        assert qa['status'] == 'PASS_REREAD_ALL522_OUTPUTS_AND426_SOURCE_DECISIONS'
        assert qa['source_count'] == 426 and qa['window_count'] == 522
        assert qa['production_completion_ref'] == path_ref(production_path)
        assert qa['selection_ref'] == complete['selection_ref']
        field = read_json(check_ref(registration['successful_field_domain_ref'], R.parent))
        assert field['status'] == 'PASS_NO_FIELD_DOMAIN_EXCLUSION'
        assert field['excluded_unavailable_field_frames'] == 0
        assert field['source_selection_ref'] == complete['selection_ref']
        OUT.mkdir(exist_ok=False)
        write_new(OUT / 'adopted_first_output_QA19.json', dict(
            status='ADOPTED_ORIGINAL_SUCCESSFUL_ALL522_OUTPUT_QA_NO_REPLAY',
            source_count=426, window_count=522,
            first_QA_ref=registration['successful_output_QA_ref'], model_calls=0,
            independent_replay_calls=0, registration_ref=path_ref(R / 'package_remaining_registration19.json')))
        write_new(OUT / 'targeted_clock_compatibility_checks19.json', targeted_checks())
        manifest_path = check_ref(registration['production_assets_ref'], R.parent)
        manifest = read_json(manifest_path)
        manifest['_asset_manifest_ref'] = path_ref(manifest_path)
        selected = read_json(check_ref(complete['selection_ref'], R.parent))
        binding = {key: complete[key] for key in ('code_identity', 'config_ref', 'asset_manifest_ref')}
        expected = package_refs(binding, complete, production_path, manifest_path)
        admission = read_json(check_ref(registration['original_package_admission_ref'], R.parent))
        spec = importlib.util.spec_from_file_location(
            'improvement.content_choice_v1.render_remaining19', RECOVERY / 'render_remaining19.py')
        module = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)
        module.RECOVERY_REGISTRATION_REF = path_ref(R / 'package_remaining_registration19.json')
        phase = 'FIRST_REMAINING_COMPOSITION_AND_11STRICT'
        receipt = module.render_candidate(manifest, selected, OUT / 'rendered', candidate='contrast',
            parameter_count=pipeline_parameters('contrast'), admission=admission, expected_refs=expected)
        assert complete['code_identity'] == code_identity()
        for reference in registration['execution_code_refs'].values():
            check_ref(reference, R.parent)
        write_new(OUT / 'completion.json', dict(
            schema='AIC_CONTENT_CHOICE_PACKAGE_REMAINING19', candidate='contrast',
            receipt=receipt, registration_ref=path_ref(R / 'package_remaining_registration19.json'),
            adopted_successful_QA_ref=path_ref(OUT / 'adopted_first_output_QA19.json'),
            original_failure_preserved=True, no_models_or_replay_repeated=True,
            website_submitted=False))
        write_new(R / 'package_contrast_remaining_controller_completion19.json', dict(
            utc=datetime.now(timezone.utc).isoformat(),
            status='PACKAGE_AND_INDEPENDENT_QA_NATURALLY_COMPLETED_WINDOWS_DELIVERY_PENDING',
            package_completion_ref=path_ref(OUT / 'completion.json'),
            recovery_registration_ref=path_ref(R / 'package_remaining_registration19.json'),
            original_endpoint_equality_failure_preserved=True, automatic_website_submission=False))
        signal.alarm(0)
    except BaseException as error:
        write_new(R / 'package_contrast_remaining_controller_failure19.json', dict(
            utc=datetime.now(timezone.utc).isoformat(), phase=phase, error=str(error),
            traceback=traceback.format_exc(), automatic_retry=False))
        raise


if __name__ == '__main__':
    main()
