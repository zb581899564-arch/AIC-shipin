"""Bind already-successful field/parameters and the new human risk authorization."""
from datetime import datetime, timezone
import json
import os
import shutil
import socket
import subprocess
from common import ROOT, OLD, ASSETS, read, ref, checked, save_new, lines
from improvement.final_sprint_v1.frozen_field import load_cache, export_selection
from improvement.final_sprint_v1.packaging import read_zip_rows
from improvement.final_sprint_v1.contracts import validate_sources, total_parameters


def main():
    if os.environ.get('CUDA_VISIBLE_DEVICES') != '':
        raise ValueError('CPU process must mask only its own CUDA')
    if subprocess.check_output(['git','rev-parse','HEAD'],cwd=OLD,text=True).strip() != '8dcde128be0ffe2df3ccba75d69929b7a9769a6f':
        raise ValueError('Original exact runtime checkout changed')
    assets = read(ASSETS)
    field_receipt = read(checked(assets['frozen_spatial_field']))
    cache = load_cache(field_receipt, assets)
    rows = read_zip_rows(checked(assets['protected_baselines']['40.48']))
    selected = {r['video_id']: [p['frame'] for p in r['predictions']] for r in rows}
    if len(rows) != 426 or sum(map(len, selected.values())) != 123479 or not all(selected.values()):
        raise ValueError('Protected40.48 complete nonempty membership changed')
    original_package = read(ROOT.parent / 'final_sprint_temporal_r_production_20261023_v6/candidates/r_time_event/package/package_receipt.json')
    parameters = original_package['parameter_budget']['receipt_refs']
    inventory = total_parameters(parameters)
    if inventory['total_elements'] != 8816809946:
        raise ValueError('Actual complete inherited parameter union differs')
    export = export_selection(cache, selected, ROOT / 'selected_export')
    spec = read(checked(cache['spec_ref']))
    validator = checked(spec['renderer']['independent_validator_ref'])
    old_text = validator.read_text()
    allowed = '{"QWEN_ANCHOR_SAME_FRAME", "SHOT_LINEAR_INTERPOLATION"}'
    new_allowed = '{"QWEN_ANCHOR_SAME_FRAME", "SHOT_LINEAR_INTERPOLATION", "ANCHOR_PCHIP_TRAJECTORY", "ANCHOR_MEDIAN3_TRAJECTORY", "SHOT_REPRESENTATIVE_ANCHOR"}'
    if old_text.count(allowed) != 1:
        raise ValueError('Independent validator derivation must change exactly the declared source enum')
    new_validator = ROOT / 'independent_validate_trajectory.py'
    with new_validator.open('x') as f:
        f.write(old_text.replace(allowed, new_allowed))
    save_new(ROOT / 'validator_derivation.json', dict(original=ref(validator), derived=ref(new_validator),
        only_change='Extend provenance enum with three explicitly registered derived trajectory sources',
        original_strict_loader_unchanged=True, all_11_existing_checks_preserved=True))
    source_clocks = validate_sources(assets['sources'], verify_media=False)
    for sid, frames in selected.items():
        for frame in frames:
            if str(source_clocks[sid][0][frame]) != cache['native_pts'][sid][str(frame)]:
                raise ValueError('Actual native clock disagrees with frozen field support')
    records = dict(host=socket.gethostname(), disk_free=shutil.disk_usage(ROOT).free,
        memory_available=[s for s in open('/proc/meminfo') if s.startswith('MemAvailable:')],
        active_processes=subprocess.check_output(['ps','-eo','pid,ppid,stat,pcpu,args','--sort=-pcpu'],text=True).splitlines()[:10],
        CPU_threads_max=2, new_models=0, output_estimate_bytes=512 << 20)
    if records['host'] != 'inspur-NP5570M5' or records['disk_free'] < records['output_estimate_bytes']:
        raise ValueError('Actual capacity cannot hold these outputs; protected dependencies remain')
    save_new(ROOT / 'live_resource.json', records)
    save_new(ROOT / 'bound_inputs.json', dict(assets_ref=ref(ASSETS), spec_ref=cache['spec_ref'],
        cache_ref=cache['cache_ref'], metadata_ref=cache['metadata_ref'], selection_export=export,
        source_clocks_verified=True, selected_frames=123479, parameter_receipts=parameters,
        actual_parameter_budget=inventory, baseline_refs=assets['protected_baselines'],
        validator_ref=ref(new_validator), strict_loader=spec['renderer']['strict_loader_root'],
        metadata=spec['renderer']['metadata_ref']))
    history_paths=sorted(set(ROOT.parent.glob('*/*history*.jsonl'))|set(ROOT.parent.glob('*/*/*history*.jsonl')))
    histories=[]
    for path in history_paths:
        if path.is_relative_to(ROOT):
            continue
        for row in lines(path):
            if isinstance(row,dict) and 'prediction_sha256' in row:
                histories.append(row)
    from common import save_lines
    save_lines(ROOT/'distinct_package_history.jsonl',histories)
    save_new(ROOT/'history_adoption.json',dict(entries=len(histories),
        original_history_files=[ref(p) for p in history_paths if not p.is_relative_to(ROOT)],
        original_histories_not_modified=True))
    save_new(ROOT / 'registration.json', dict(schema='THREE_ANCHORED_SPATIAL_RISK_20261024_V1',
        human_authorization='User expressly requests three most promising risk candidates and automatic upload within3hours; no offline quality gate',
        created_at=datetime.now(timezone.utc).isoformat(), deadline_utc='2026-10-24T04:00:00+00:00',
        base='40.48 full123479 native frames and crop widths preserved; protected40.48/40.47 never overwritten',
        candidates=dict(pchip='Monotone shape-preserving cubic through original within-shot model positions, using actual native PTS; original anchors exact',
          median3='Per-axis replicated-endpoint median of3 neighboring same-shot model anchors, then actual-PTS linear interpolation',
          shot_representative='Use actual same-shot model anchor nearest per-axis median position, tie earliest, unchanged crop dimensions'),
        quality='RISK_EXPLORATION_NO_OFFLINE_QUALITY_VALIDATION_NO_GAIN_CLAIM',
        limits=dict(new_model_calls=0,new_training=0,new_media_decodes=0,new_downloads=0,CPU_threads=2,output_bytes=512 << 20),
        geometry='Every source uses its registered ratio; every original selected native frame remains; no unknown field point is added',
        historical_failed_subject_G_R_M_protocols_unchanged=True, original_runtime=ref(ASSETS),
        code={p.name:ref(p) for p in (ROOT/'code').glob('*.py')}, inputs=ref(ROOT/'bound_inputs.json'),
        no_new_goal_or_automation=True, automatic_edge_submission_authorized=True,
        confirmation_or_quality_evidence_not_claimed=True))
    print('BOUND426_ALL123479_TIME_MEMBERS_AND_WIDTHS_PARAMETERS8816809946',flush=True)


if __name__ == '__main__':
    main()
