"""G0 actual asset handoff and metadata-only sample selection. No model calls."""
import argparse
import copy
from pathlib import Path
import socket
import sys
import traceback

from sg8_common import (HERE, RUN, OLD, V14, BASE, BASE_SHA, ADAPTER_SHA,
                        V14_LOCK_SHA, sha, digest, read, rows, utc, save,
                        require, state, old_helpers, inputs)
from sg8_sampling import select


def inventory():
    """Do not open any answer/coordinate file before deterministic selection."""
    require(socket.gethostname() == 'inspur-NP5570M5', 'wrong Linux host')
    require(not (HERE / 'input_01/sample_plan.json').exists(), 'sample already selected; do not resample')
    common, p2j, production = old_helpers()
    config, manifest, clocks = inputs('nontest')
    meta = {r['video_id']: r for r in manifest['records']}
    folder = V14 / 'nontest_01'
    request_rows = rows(folder / 'anchor_requests.jsonl')
    shots = rows(folder / 'field_shots.jsonl')
    fields = rows(folder / 'field_frames.jsonl')
    field_contract = sys.modules['field_contract']
    require(production.field_frames(manifest, clocks) == fields, 'full native source-frame field changed')
    expected = field_contract.build_field_requests(fields, shots, 8)
    require(expected == request_rows, 'original request schedule/pixel hashes changed')
    request_map = {(r['video_id'], r['source_frame']): r for r in request_rows}
    shot_map = {(r['video_id'], r['source_frame']): r for r in shots}
    field_map = {(r['video_id'], r['source_frame']): r for r in fields}
    candidates = []
    for shot_id, shot in enumerate(p2j.group_shots(shots)):
        vid = shot[0]['video_id']
        planned = p2j.anchor_frames([r['source_frame'] for r in shot], 8)
        for index in range(1, len(planned)-2):
            q = planned[index-1:index+3]
            if q[2]-q[1] != 8:
                continue
            candidates.append(dict(scope='nontest', source_group=meta[vid]['source_group'],
                source_sha256=meta[vid]['source_sha256'], video_id=vid, shot_id=shot_id,
                support_ordinals=q, support_request_sha256=[request_map[vid, f]['anchor_request_sha256'] for f in q]))
    selected = select(candidates)  # rejects <8; developer expansion is never implicit
    require(len(selected) == 8 and len({x['source_group'] for x in selected}) == 8,
            'eight unique registered source groups required')
    requests = []
    for group in selected:
        vid = group['video_id']
        for role, ordinals in [('support', group['support_ordinals']), ('probe', group['probe_ordinals'])]:
            for frame in ordinals:
                request = dict(field_map[vid, frame], kind='QWEN_ANCHOR_SAME_FRAME',
                    expected_pixel_sha256=shot_map[vid, frame]['decoded_pixel_sha256'])
                request['anchor_request_sha256'] = field_contract._request_sha(request)
                if role == 'support':
                    require(request == request_map[vid, frame], 'support original request identity mismatch')
                else:
                    require((vid, frame) not in request_map, 'probe cannot enter original support set')
                requests.append(dict(group_index=group['group_index'], group_role=group['role'],
                    observation_role=role, request=request))
    require(len(requests) == 88 and sum(x['observation_role'] == 'probe' for x in requests) == 56,
            'all phases and denominators required')
    plan = dict(schema='SG8_METADATA_SAMPLE_V1', utc=utc(), metadata_only=True,
        answer_files_opened_before_selection=0, candidates=len(candidates),
        source_groups=len({x['source_group'] for x in candidates}),
        metadata_inputs={str(folder / name): sha(folder / name) for name in
                         ['field_frames.jsonl', 'field_shots.jsonl', 'anchor_requests.jsonl']},
        manifest_sha256=sha(config['inputs']['nontest']['manifest']),
        sampling_source_sha256=sha(HERE / 'sg8_sampling.py'), groups=selected,
        requests=requests, observations_upper_bound=88, support_observations=32,
        isolated_probe_observations=56, no_quality_claim=True)
    save(HERE / 'input_01/sample_plan.json', plan)
    save(HERE / 'input_01/inventory_summary.json', {k:v for k,v in plan.items() if k not in ('groups','requests')})
    state('G0_METADATA_SELECTED_EXPOSURE_AND_ASSET_HANDOFF_PENDING', groups=8,
          engineering_groups=2, confirmation_groups=6, observations=88, new_spatial_calls=0,
          sample_plan_sha256=sha(HERE / 'input_01/sample_plan.json'))


def cache_inventory():
    """Find cache identity without exposing raw responses or coordinates."""
    plan = read(HERE / 'input_01/sample_plan.json')
    by_hash = {x['request']['anchor_request_sha256']: x for x in plan['requests']}
    matches = {h: [] for h in by_hash}
    scanned = []
    for path in sorted(RUN.glob('*/**/anchor_requests.jsonl')):
        require('100confirm' not in str(path).lower(), 'forbidden confirmation path encountered')
        if HERE in path.parents:
            continue
        # Cache indexes contain request identity only, never answers.
        count = 0
        for request in rows(path):
            h = request.get('anchor_request_sha256')
            if h in by_hash:
                require(request == by_hash[h]['request'], 'request SHA collision or contradictory cache identity')
                matches[h].append(dict(request_index=str(path), request_index_sha256=sha(path),
                    output_exists=(path.parent / 'anchor_output.jsonl').is_file()))
                count += 1
        scanned.append(dict(path=str(path), sha256=sha(path), selected_identity_matches=count))
    result = dict(utc=utc(), sample_plan_sha256=sha(HERE / 'input_01/sample_plan.json'),
        coordinate_or_raw_files_opened=0, request_indexes=scanned,
        observations=[dict(group_index=x['group_index'], observation_role=x['observation_role'],
                           request_sha256=h, caches=matches[h]) for h,x in by_hash.items()],
        probe_observations_with_matching_request=sum(bool(matches[h]) for h,x in by_hash.items()
                                                    if x['observation_role']=='probe'),
        cache_existence_is_not_exposure_or_model_identity_acceptance=True)
    save(HERE / 'input_01/cache_inventory.json', result)
    state('G0_CACHE_IDENTITY_INVENTORIED_EXPOSURE_REVIEW_PENDING',
        probe_observations_with_matching_request=result['probe_observations_with_matching_request'],
        new_spatial_calls=0)


def assets():
    """Verify actual bytes and old authority, without re-running accepted old jobs."""
    require(socket.gethostname() == 'inspur-NP5570M5', 'wrong Linux host')
    require(sha(V14 / 'source_lock.json') == V14_LOCK_SHA, 'V14 original lock changed')
    bound = {}
    for entry in [OLD, V14]:
        lock = read(entry / 'source_lock.json')
        for key in ('files', 'production_files'):
            for path, expected in lock.get(key, {}).items():
                require(path not in bound or bound[path] == expected, 'historical locks disagree on same file')
                bound[path] = expected
    checked_bytes = 0
    for index,(path, expected) in enumerate(sorted(bound.items()), 1):
        require(sha(path) == expected, 'old frozen dependency changed: '+path)
        checked_bytes += Path(path).stat().st_size
        if index % 500 == 0 or index == len(bound):
            state('G0_CPU_VERIFY_ORIGINAL_BOUND_BYTES', checked=index, total=len(bound),
                  checked_bytes=checked_bytes, new_spatial_calls=0)
    common, p2j, production = old_helpers()
    config = read(OLD / 'config.json')
    model_reference = config['model_receipt']
    require(set(model_reference)=={'path','sha256'} and sha(model_reference['path'])==model_reference['sha256'],
            'original pinned model receipt binding differs')
    model_receipt = read(model_reference['path'])
    require(model_receipt['status'] == 'COMPLETE_HASH_VERIFIED' and
            model_receipt['revision'] == config['model_revision'], 'original pinned model authority missing')
    model_files = {}
    for item in model_receipt['completed']:
        path = Path(config['model_dir']) / item['name']
        require(path.is_file() and path.stat().st_size == item['bytes'] and sha(path)==item['sha256'],
                'actual pinned base model file differs: '+str(path))
        model_files[str(path)] = item['sha256']
    complete = read(V14 / 'completion.json')
    require(complete['status']=='PASS_AUTOPILOT_FINAL_T_ZIP_ON_LINUX', 'V14 final authority not successful')
    scopes = {}
    linear_equal = changed = 0
    original_requests_total = 0
    for scope, videos, windows, selected_count, anchors in [('nontest',8,8,447,206),('rematch',426,521,102470,31295)]:
        _, manifest, clocks = inputs(scope)
        folder = V14 / (scope+'_01')
        temporal = rows(folder/'temporal.jsonl')
        stage = read(folder/'temporal.stage.json')
        require(stage['status']=='PASS_TEMPORAL_EXECUTION' and stage['videos']==videos and
            stage['windows']==windows and stage['invalid_windows']==0 and stage['selected_adapter_sha256']==ADAPTER_SHA and
            stage['output_sha256']==sha(folder/'temporal.jsonl'), 'fixed time asset terminal mismatch')
        selected = rows(folder/'selected.jsonl')
        require(len(selected)==selected_count and production.select_frames(manifest,temporal,clocks)==selected,
                'fixed V14 native frame-key selection differs')
        fields, shots = rows(folder/'field_frames.jsonl'), rows(folder/'field_shots.jsonl')
        req, out = rows(folder/'anchor_requests.jsonl'), rows(folder/'anchor_output.jsonl')
        require(production.field_frames(manifest,clocks)==fields, 'full source native field mismatch')
        fc = sys.modules['field_contract']
        require(fc.build_field_requests(fields,shots,8)==req and len(req)==len(out)==anchors,
                'complete original spatial schedule/count differs')
        cache = read(folder/'cache_reuse_receipt.json')
        require(cache['status']=='PASS_COMPLETE_TIME_INDEPENDENT_SOURCE_CACHE', 'old exact space cache not accepted')
        for name, expected in cache['files'].items():
            require(sha(folder/name)==expected, 'old accepted spatial cache bytes changed')
        spatial = read(folder/'spatial.stage.json')
        require(spatial['rows']==anchors and spatial['invalid']==0 and spatial['logical_parameters']==8767123696 and
                spatial['time_adapter_enabled'] is False, 'old spatial model contract differs')
        # Original compose validates every original output/raw-identity mapping. It is not old acceptance rerun.
        projected = sys.modules['frame_contract'].legacy_manifest(manifest)
        old_pred, old_prov = fc.compose_from_field(projected, selected, shots, req, out)
        require(old_pred==rows(folder/'predictions.jsonl') and old_prov==rows(folder/'provenance.jsonl'),
                'actual pinned old linear field does not reproduce original accepted projection')
        from sg8_math import interpolate
        meta={x['video_id']:x for x in manifest['records']}
        outputs={(x['video_id'],x['source_frame']):x for x in out}
        raw_parser=sys.modules['contracts'].parse_focus_norm
        baseline=common.load(OLD/'spatial_baseline.py','sg8_original_spatial_baseline')
        for row in out:
            m=meta[row['video_id']]
            center=raw_parser(row['raw_output'],m['width'],m['height'])
            require(center is not None and center==row['center_norm'], 'old raw parser/center differs')
            cw,ch=baseline.compute_crop_size(m['width'],m['height'],*m['targetRatioWH'])
            require(baseline.center_to_box(*center,m['width'],m['height'],cw,ch)==row['box_xyw'],
                    'original raw-to-final-box mapping differs')
        for shot in p2j.group_shots(shots):
            vid=shot[0]['video_id'];m=meta[vid]
            q=p2j.anchor_frames([x['source_frame'] for x in shot],8)
            boxes={f:outputs[vid,f]['box_xyw'] for f in q}
            for row in shot:
                f=row['source_frame'];box,prov=interpolate(f,boxes,m['width'],m['height'],m['targetRatioWH'],p2j.interpolate_box)
                oldbox,oldprov=p2j.interpolate_box(f,boxes)
                if prov['spatial_source']!='SHOT_PCHIP_XY_ORDINAL_GAP8':
                    require((box,prov)==(oldbox,oldprov),'ordinary old linear branch changed')
                    linear_equal+=1
                else:
                    changed+=box!=oldbox
        files={str(folder/name):sha(folder/name) for name in ['temporal.jsonl','temporal.stage.json','selected.jsonl',
            'field_frames.jsonl','field_shots.jsonl','anchor_requests.jsonl','anchor_output.jsonl',
            'spatial.stage.json','schedule.stage.json','cache_reuse_receipt.json','predictions.jsonl','provenance.jsonl',
            'independent_validation.json','package.stage.json']}
        for item in manifest['records']:
            require(sha(item['source_path'])==item['source_sha256'], 'original source bytes changed')
            files[item['source_path']]=item['source_sha256']
        scopes[scope]=dict(videos=videos, windows=windows, selected_frames=selected_count,
            full_source_frames=len(fields), original_anchors=anchors, files=files)
        original_requests_total+=anchors
        state('G0_CPU_SCOPE_ASSETS_ACCEPTED', scope=scope, **{k:v for k,v in scopes[scope].items() if k!='files'},
              new_spatial_calls=0)
    save(HERE/'g0_asset_handoff.json',dict(status='PASS_ACTUAL_ORIGINAL_ASSET_AND_PINNED_LINEAR_HANDOFF_NOT_FULL_G0',
        utc=utc(), scopes=scopes, historical_bound_files=len(bound), historical_bound_bytes=checked_bytes,
        historical_bound_map_sha256=digest(bound), model_files=model_files, original_anchor_count=original_requests_total,
        ordinary_linear_integer_boxes_exact=linear_equal, structural_new_branch_box_changes_inventory=changed,
        live_model_tensor_hash_pending=True, decoder_processor_pending=True, independent_new_field_strict_pending=True,
        new_model_calls=0,new_optimizer_updates=0,source_locks_unchanged=True))
    state('G0_ASSET_HANDOFF_PASS_NATIVE_PROCESSOR_AND_NEW_FIELD_STRICT_PENDING', new_spatial_calls=0)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('stage',choices=['inventory','cache_inventory','assets'])
    args=parser.parse_args()
    try:
        globals()[args.stage]()
    except Exception:
        save(HERE/('g0_'+args.stage+'_failure_'+utc().replace(':','').replace('+','_')+'.json'),dict(utc=utc(),stage=args.stage,traceback=traceback.format_exc(),
            new_model_calls=0,new_optimizer_updates=0))
        raise
