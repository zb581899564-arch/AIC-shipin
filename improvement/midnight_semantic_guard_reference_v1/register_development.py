"""Freeze one new CPU development comparison; never evaluate source labels."""
import argparse
import datetime as dt
from pathlib import Path
import socket
import sys
from reference_common import GATES, checked, read, ref, require, save, validate_gates
from semantic_rule import POLICY, RULE

ROOT = Path('/home/inspur/aic_video_work/midnight_semantic_guard_20261015_v1')
MAIN = ROOT.parent/'midnight_five_verify40_46_20261015_v1'

def main(root):
    require(root.resolve()==ROOT and Path(__file__).resolve().parent==root/'code'
        and sys.platform=='linux' and socket.gethostname()=='inspur-NP5570M5', 'Exact independent new Linux root/code required')
    bindings=read(root/'code/frozen_development_bindings.json')
    for value in bindings.values():checked(value)
    old_protocol=read(checked(bindings['policy_protocol']));validate_gates(old_protocol)
    manifest=read(checked(bindings['source_manifest_ref']));inputs=read(checked(manifest['inputs_ref']))
    completion=read(checked(bindings['source_completion_ref']))
    require(manifest['group']==inputs['group']=='dev' and manifest['exposure_label']=='development_previously_exposed'
        and inputs['all_sources_previously_exposed'] is True and len(manifest['sources'])==4
        and len(inputs['entries'])==len(completion['entries'])==8
        and completion['first_input_QA_complete'] is True and completion['first_output_QA_complete'] is True,
        'Only complete original eight successful answers and exposed four-source development may be adopted')
    pair=MAIN.parent/'midnight_pair_applicability_20261015_v1/policy_fresh_comparison.json'
    require(ref(pair)['sha256']=='876f2cf98e307cf5644d1ef1634888983e4908840c45a1884e2855a9a1e23d10'
        and read(pair)['passed_policies']['PAIR_ONLY'] is False, 'Prior real PAIR failure remains unchanged')
    protocol=dict(schema='MIDNIGHT_SEMANTIC_GUARD_FIXED_PROTOCOL_V1',policy=POLICY,rule=RULE,
        deletion_quality_gates=dict(GATES),mechanism_gates=dict(minimum_sources_with_real_restored_native_frames_vs_unprotected_worst_all=1,
            minimum_sources_with_real_deleted_native_frames_vs_original_VERIFY=1),
        source_manifest_ref=bindings['source_manifest_ref'],source_completion_ref=bindings['source_completion_ref'],
        original_relative_prompt_protocol_ref=bindings['source_protocol_ref'],original_policy_protocol_ref=bindings['policy_protocol'],
        original_unprotected_result_ref=bindings['prior_all_window_result_ref'],prior_pair_failure_ref=ref(pair),
        model_parameters=8782459120,new_model_calls=0,new_processor_calls=0,new_media_decodes=0,old_QA_repeated=0,
        development_exposure='ALL_FOUR_ALREADY_EXPOSED_DEVELOPMENT_ONLY',fresh_confirmation_allowed_only_after_this_development_PASS=True,
        future_confirmation=dict(source_count=4,maximum_public_pool_count=6,source_order_salt='RECALL_VERIFY40_46_VIDE0XUM_SMALL8_20261014_V1',
            exclude_known_all_registered_and_previous_confirm_and_SHORT6=True,profile='ORIGINAL_MAX30_SECONDS_NATIVE64_NO_FORCED_SHORT_STRATUM',
            new_source_selection_or_acquisition_before_development_PASS=False,media_bytes='MUST_BE_SEPARATELY_REGISTERED_BEFORE_DOWNLOAD'),
        development_FAIL_action='STOP_NO_CONFIRMATION_SELECTION_DOWNLOAD_OR_MODEL',deadline='2026-10-15T16:00:00Z',
        first_new_development_comparison_not_yet_executed=True,registered_utc=dt.datetime.now(dt.timezone.utc).isoformat())
    save(root/'protocol.json',protocol)
    files={str(p):ref(p)['sha256'] for p in (root/'code').iterdir() if p.is_file()}
    registration=dict(status='REGISTERED_ONE_NEW_SEMANTIC_GUARD_DEVELOPMENT_CPU_COMPARISON',group='dev',
        protocol_ref=ref(root/'protocol.json'),source_manifest_ref=bindings['source_manifest_ref'],
        source_completion_ref=bindings['source_completion_ref'],code_files=files,full_source_count=4,expected_adopted_answers=8,
        registered_before_first_new_comparison=True,reference_labels_opened_during_registration=False,
        new_model_calls=0,new_processor_calls=0,new_media_decodes=0,old_QA_repeated=0)
    save(root/'development_registration.json',registration)
    print(dict(status=registration['status'],protocol_ref=ref(root/'protocol.json'),registration_ref=ref(root/'development_registration.json')))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);main(p.parse_args().root)
