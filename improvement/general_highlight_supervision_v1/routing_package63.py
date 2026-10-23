"""Two new CPU-only artifacts after all426 model/independent QA; never submit."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
os.environ['OMP_NUM_THREADS'] = '2'
os.environ['MKL_NUM_THREADS'] = '2'
from pathlib import Path
import shutil
import time
import traceback
import numpy as np
from routing_package63_common import ROOT, PRODUCTION, POLICIES, RUN, read, ref, save, checked, lines, zip_rows, canonical
from routing_package63_rules import check_current_rules
from routing_package63_artifact import build


def main():
    ROOT.mkdir()
    launch = read(PRODUCTION.parent / 'routing_production62_launch.json')
    save(ROOT / 'await_registered_production.json', dict(registered_launch=launch,
        exact_terminal=str(PRODUCTION / 'model_and_selection_completion.json'),
        wait_only_no_model_or_recovery=True, maximum_wait_seconds=1800))
    deadline = time.monotonic() + 1800
    while not (PRODUCTION / 'model_and_selection_completion.json').exists():
        if (PRODUCTION / 'failure.json').exists():
            raise RuntimeError('Producer reports actual failure; preserve all work, do not package')
        if time.monotonic() >= deadline:
            raise TimeoutError('No terminal within packaging wait bound; never restart the producer')
        time.sleep(10)
    complete = read(PRODUCTION / 'model_and_selection_completion.json')
    if complete['state'] != 'ALL426_MODEL_AND_FIRST_CPU_QA_COMPLETE_PACKAGE_PENDING':
        raise ValueError('All426 primary and independent CPU terminal required')
    selection = read(checked(complete['selection']))
    reg = read(PRODUCTION / 'registration.json'); assets = read(checked(reg['assets']))
    expected = sum(row['actual_bytes'] for row in assets['field_files'].values()) * 4
    free = shutil.disk_usage(ROOT).free
    if expected > free:
        raise RuntimeError('Conservative actual field-derived package byte requirement exceeds current capacity')
    save(ROOT / 'capacity_admission.json', dict(actual_field_derived_required_bytes=expected, actual_free_bytes=free,
        new_GPU=False, source_field_reused=True, no_external_task_interference=True))
    check_current_rules()
    baseline = zip_rows(checked(reg['protected_baseline']))
    historical = read(Path(__file__).parent / 'historical_artifact_catalog63.json')
    history = {row['canonical_sha256'] for row in historical['accepted']}; history.add(canonical(baseline))
    masks = {policy: set() for policy in POLICIES}; routed = set()
    for source in selection['sources']:
        sid = source['video_id']
        if source['source_routed']: routed.add(sid)
        with np.load(checked(source['selection']), allow_pickle=False) as values:
            for policy in POLICIES:
                masks[policy].update((sid, int(frame)) for frame in np.flatnonzero(values[policy]))
    selected_union = masks[POLICIES[0]] | masks[POLICIES[1]]
    field = lines(checked(assets['field_files']['field_frames.jsonl']['identity']))
    field_map = {(row['video_id'], row['source_frame']): row for row in field}
    if len(field_map) != len(field) or not selected_union <= field_map.keys():
        raise ValueError('Selected point has no unique accepted continuous spatial field')
    # Exact canonical original helpers avoid the research module named common
    # shadowing the historical package/field engine. No model is loaded here.
    from time_entry53 import original_runtime
    _, bindings = original_runtime()
    from field_contract import compose_from_field
    from pts_contract import legacy_manifest
    union_rows, union_provenance = compose_from_field(
        legacy_manifest(read(checked(assets['source_manifest']))),
        [field_map[key] for key in sorted(selected_union)],
        *[lines(checked(assets['field_files'][name]['identity']))
          for name in ('field_shots.jsonl', 'anchor_requests.jsonl', 'anchor_output.jsonl')])
    save(ROOT / 'package_registration.json', dict(production_terminal=ref(PRODUCTION / 'model_and_selection_completion.json'),
        selection=complete['selection'], protocol=ref(PRODUCTION / 'protocol.json'),
        rules=ref(ROOT / 'official_rule_check_before_package.json'), source_assets=reg['assets'],
        historical_artifact_catalog=ref(Path(__file__).parent / 'historical_artifact_catalog63.json'),
        code={p.name: ref(p) for p in Path(__file__).parent.glob('routing_package63*.py')},
        helpers={key: ref(path) for key, path in bindings.items()}, no_new_model_or_training=True))
    clocks = read(checked(assets['clocks'])); metadata = read(checked(assets['metadata']))
    results = [build(policy, union_rows, union_provenance,
        [field_map[key] for key in sorted(masks[policy])], masks[policy], clocks,
        baseline, routed, metadata, history) for policy in POLICIES]
    checked(reg['protected_baseline'])
    save(ROOT / 'completion.json', dict(state='TWO_DISTINCT_ALL426_CPU_PACKAGES_QA_COMPLETE_WINDOWS_PENDING',
        candidates=results, source_routed_count=len(routed), protected_baseline=reg['protected_baseline'],
        no_automatic_submission=True, no_new_model_calls=True))


if __name__ == '__main__':
    try: main()
    except BaseException:
        if ROOT.exists(): save(ROOT / 'failure.json', dict(traceback=traceback.format_exc(), keep_all_prior_success=True))
        raise
