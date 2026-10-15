"""Map only an actually completed newly admitted relative first confirmation.

No acquisition, QA replay, encoding, baseline inference or comparison occurs.
The complete new B0/VERIFY and first QA are adopted by map_existing's JSON
binding checks before any new classifier input is exported.
"""
import argparse
from pathlib import Path

from map_existing import map_existing
from reference_common import checked, read, ref, require, save

ROOT = Path('/home/inspur/aic_video_work/midnight_five_verify40_46_20261015_v1/relative_confirm')


def main(root, output):
    root = root.resolve(); require(root == ROOT, 'Exact independent relative first-confirm root required')
    reg = read(root/'positive_fresh_registration.json')
    require(reg['status'] == 'REGISTERED_MIDNIGHT_RELATIVE_FIRST_FRESH_INPUTS_V1', 'New independent relative input registration required')
    selection = read(checked(reg['dev_selection_ref'])); result = read(checked(reg['dev_result_ref']))
    require(selection['schema'] == 'MIDNIGHT_DELETE_DEV_SELECTION_V1' and selection['confirm_metrics_examined'] is False
        and selection['protocol_ref'] == result['bindings']['protocol_ref'] == reg['protocol_ref']
        and selection['result_ref'] == reg['dev_result_ref'] and selection['passed_arms'] == result['passed_arms']
        and any(selection['passed_arms'].values()), 'Actual fixed passing relative development required')
    candidates = read(checked(reg['source_candidates_ref'])); media = read(checked(reg['reference_completion_ref']))
    require(media['status'] == 'PASS_MIDNIGHT_RELATIVE_FRESH_MEDIA_NATIVE_SECONDS_NOT_INPUT_OR_GPU'
        and media['source_candidates_ref'] == reg['source_candidates_ref'] and media['protocol_ref'] == reg['protocol_ref']
        and media['dev_selection_ref'] == reg['dev_selection_ref'] and len(media['accepted']) == 4,
        'Actual complete independent media/native stage required')
    summary = map_existing(root, 'confirm', output, checked(reg['protocol_ref']))
    manifest = read(output/'evaluation_manifest.json'); sources = manifest['sources']
    require([source['source_name'] for source in sources] == [row['video_id'] for row in media['accepted']],
            'Full actual new four-source order must match original complete input plan')
    protected = set(candidates['protected_source_ids']); prohibited = set(candidates['prohibited_media_sha256'])
    require(len({source['source_name'] for source in sources}) == len({source['source_sha256'] for source in sources}) == 4
        and all(source['source_name'] not in protected and source['source_sha256'] not in prohibited for source in sources),
        'Actual new source ID/byte isolation must hold, not just proposed selection')
    admission = dict(status='PASS_MIDNIGHT_NEW4_ID_BYTES_NATIVE_ADMISSION',
        sources_unexposed_before_registration=True, quality_metrics_examined_before_freeze=False,
        protocol_ref=reg['protocol_ref'], source_names=[source['source_name'] for source in sources],
        source_sha256=[source['source_sha256'] for source in sources],
        development_selection_ref=reg['dev_selection_ref'], development_result_ref=reg['dev_result_ref'],
        admitted_arms=selection.get('selected_policies', [arm for arm, passed in selection['passed_arms'].items() if passed]),
        source_candidates_ref=reg['source_candidates_ref'], media_completion_ref=reg['reference_completion_ref'],
        input_registration_ref=ref(root/'positive_fresh_registration.json'),
        cpu_acceptance_ref=ref(root/'cpu_acceptance_confirm.json'),
        B0_completion_ref=ref(root/'confirm/B0/gpu_01/completion.json'),
        VERIFY_completion_ref=ref(root/'confirm/VERIFY/gpu_01/completion.json'),
        B0_first_QA_ref=ref(root/'confirm/B0/replay_01/completion.json'),
        VERIFY_first_QA_ref=ref(root/'confirm/VERIFY/replay_01/completion.json'),
        model_calls=0, prior_QA_repeated=0, hidden_alias_or_subclip_semantic_disjointness='UNKNOWN')
    admission_path = output/'fresh_admission.json'; save(admission_path, admission)
    save(output/'first_fresh_evaluation_manifest.json', dict(manifest,
        exposure_label='first_fresh_confirmation_previously_unexposed', fresh_admission_ref=ref(admission_path)))
    print(summary)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True); args = parser.parse_args(); main(args.root, args.output)
