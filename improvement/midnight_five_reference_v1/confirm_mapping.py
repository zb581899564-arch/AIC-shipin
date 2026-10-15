"""Pure first-fresh candidate isolation and unchanged baseline-only native plan.

No URL fetch, media decode, processor, tensor load, QA or model operation exists.
The candidate export remains metadata, not actual source/native admission.
"""
import argparse
from bisect import bisect_left
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path

from reference_common import checked, read, ref, require, save, sha, validate_gates

INVENTORY_SHA = 'b3849e17b6b821044c87789c2b1108009a4c50a0b08d255cd908a97255916042'
SELECTION_SALT = 'RECALL_VERIFY40_46_VIDE0XUM_SMALL8_20261014_V1'


def validate_export(export):
    require(export['selection_salt'] == SELECTION_SALT and export['min_author_duration'] == '30'
        and export['max_author_duration'] == '60' and export['reference_votes_viewed'] is False,
        'Original pre-exposure ID-only order/duration scope required')
    rows = export['ordered_candidates']; hashes = [row['selection_hash'] for row in rows]
    require(len(rows) == 64 and len({row['video_id'] for row in rows}) == len(rows)
        and hashes == sorted(hashes) and len(set(hashes)) == len(hashes), 'Complete original sorted ID-only prefix required')
    return rows


def export_provider_prefix(id_export, inventory, output):
    """Make a small control subset from the already resident pinned inventory."""
    rows = validate_export(read(id_export))
    require(sha(inventory) == INVENTORY_SHA, 'Actual retained publisher inventory changed')
    all_provider = {}
    with Path(inventory).open(encoding='utf8') as stream:
        for line in stream:
            row = json.loads(line); require(row['video_id'] not in all_provider, 'Duplicate provider ID')
            all_provider[row['video_id']] = row
    providers = [all_provider[row['youtube_id']] for row in rows if row['youtube_id'] in all_provider]
    save(output, dict(schema='MIDNIGHT_PINNED_PROVIDER_PREFIX_V1', original_inventory_sha256=INVENTORY_SHA,
        original_inventory_bytes=Path(inventory).stat().st_size, original_id_export_sha256=sha(id_export),
        complete_candidate_prefix_count=len(rows), provider_rows=providers,
        absent_ids=[row['video_id'] for row in rows if row['youtube_id'] not in all_provider],
        source_label_or_event_text_read=False, media_downloads=0))


def select_first_fresh(id_export, provider_prefix, role_root, protocol_path, development_selection, output):
    """Read complete old identity evidence, then take first4+next2 by old hash."""
    export = read(id_export); ordered = validate_export(export); prefix = read(provider_prefix)
    require(prefix['schema'] == 'MIDNIGHT_PINNED_PROVIDER_PREFIX_V1'
        and prefix['original_inventory_sha256'] == INVENTORY_SHA
        and prefix['original_id_export_sha256'] == sha(id_export)
        and prefix['complete_candidate_prefix_count'] == len(ordered), 'Complete pinned metadata prefix binding required')
    providers = {row['video_id']: row for row in prefix['provider_rows']}
    require(len(providers) == len(prefix['provider_rows']) and {row['video_id'] for row in ordered} ==
        {'v_'+name for name in providers} | set(prefix['absent_ids']), 'Available/absent provider prefix must cover every old candidate')
    protocol_ref = ref(protocol_path); validate_gates(read(checked(protocol_ref)))
    selection = read(checked(ref(development_selection))); result = read(checked(selection['result_ref']))
    require(selection['schema'] == 'MIDNIGHT_DELETE_DEV_SELECTION_V1' and selection['protocol_ref'] == protocol_ref
        and selection['confirm_metrics_examined'] is False and any(selection['passed_arms'].values())
        and result['group'] == 'dev' and result['passed_arms'] == selection['passed_arms']
        and result['bindings']['protocol_ref'] == protocol_ref, 'Actual frozen new deletion development PASS required')
    role_root = Path(role_root).resolve(); oldreg = read(role_root/'media_registration.json')
    old_candidates = read(checked(oldreg['source_candidates_ref']))
    known_ref = oldreg['known_exclusions_ref']; known = read(checked(known_ref))
    require(export['exclusions_sha256'] == known_ref['sha256']
        and export['source_file_sha256'] == oldreg['annotation_file_ref']['sha256'], 'Original annotation/known exclusion identity changed')
    excluded = {name if name.startswith('v_') else 'v_'+name for name in known['youtube_ids']}
    excluded.update(old_candidates['all_old_protected_and_acquired_IDs'])
    prohibited = set(known['known_media_sha256']); prior_refs = list(oldreg['prior18_media_receipts'])
    latest_pointer = role_root/'reference_completion_confirm.json'
    latest_path = checked(read(latest_pointer)); latest = read(latest_path)
    require(latest['status'] == 'PASS_ROLE_FRESH_MEDIA_NATIVE_SECONDS_NOT_INPUT_OR_GPU'
        and len(latest['accepted']) == 4 and not latest['rejected'], 'Exact complete latest ROLE media metadata required')
    for row in latest['accepted']:
        receipt_path = Path(row['media']['path']).parent/'media_receipt.json'
        receipt = read(receipt_path)
        require(all(receipt[key] == row['media'][key] for key in ('video_id', 'sha256', 'bytes', 'path')),
                'Latest ROLE accepted/source receipt identity differs')
        prior_refs.append(ref(receipt_path))
    prior = []
    for receipt_ref in prior_refs:
        receipt = read(checked(receipt_ref))
        require(receipt['known_ID_and_byte_separation'] is True, 'Old actual media receipt must retain source separation')
        excluded.add(receipt['video_id']); prohibited.add(receipt['sha256']); prior.append(receipt)
    require(len(prior) == len({row['video_id'] for row in prior}) == 22, 'All actual recent22 acquired identities must be excluded')
    eligible = [dict(row, provider=providers[row['youtube_id']]) for row in ordered
        if row['video_id'] not in excluded and row['youtube_id'] in providers]
    require(len(eligible) >= 6, 'Insufficient original unexposed source prefix; do not invent or reseed candidates')
    selected, reserves = eligible[:4], eligible[4:6]
    for index, row in enumerate(selected+reserves):
        row.update(group='confirm', role='selected_confirm' if index < 4 else 'ordered_engineering_reserve', role_index=index if index < 4 else index-4)
    save(output, dict(schema='MIDNIGHT_FIRST_FRESH_SOURCE_CANDIDATES_V1',
        status='FROZEN_ID_ONLY_CANDIDATES_NOT_MEDIA_NATIVE_INPUT_OR_GPU_ADMISSION', selection=selected,
        ordered_engineering_reserves=reserves, selection_salt=SELECTION_SALT,
        source_order='Original64 pre-exposure hash order; complete pinned-provider prefix; known/old acquired/exposed ID exclusion; first4+next2',
        protocol_ref=protocol_ref, development_selection_ref=ref(development_selection), development_result_ref=selection['result_ref'],
        id_export_ref=ref(id_export), provider_prefix_ref=ref(provider_prefix), original_inventory_sha256=INVENTORY_SHA,
        known_exclusions_ref=known_ref, prior22_media_receipts=prior_refs,
        latest_ROLE_media_completion_ref=ref(latest_path), prior_ROLE_candidates_ref=oldreg['source_candidates_ref'],
        annotation_file_ref=oldreg['annotation_file_ref'], source_scope_refs=oldreg['source_scope_refs'],
        protected_source_ids=sorted(excluded), prohibited_media_sha256=sorted(prohibited),
        selected_media_bytes=sum(row['provider']['size_bytes'] for row in selected),
        maximum_pool_bytes=sum(row['provider']['size_bytes'] for row in selected+reserves),
        source_votes_or_event_text_examined=False, media_downloads=0, model_calls=0,
        hidden_alias_or_subclip_semantic_disjointness='UNKNOWN', production_admitted=False))


def baseline_only_plan(document, group='confirm'):
    """Same ceil(T/30) equal windows and ordinal formula; no overlap views."""
    require(document['schema'] == 'RECALL_SOURCE_CLOCKS_V1' and len(document['sources']) == 4
        and group == 'confirm', 'Complete first fresh four-source clock document required')
    views, source_rows, aliases, names = [], [], [], set()
    for source in document['sources']:
        name = source['video_id']; require(name not in names, 'Repeated baseline source'); names.add(name)
        points = list(map(F, source['normalized_exact_pts'])); end = F(source['physical_end_exact'])
        require(len(points) == source['n_frames'] and points[0] == 0 and points == sorted(set(points))
            and end > points[-1], 'Complete positive zero-origin native clock required')
        count = (end.numerator+30*end.denominator-1)//(30*end.denominator); windows = []
        for index in range(count):
            a, b = end*index/count, end*(index+1)/count
            first, limit = bisect_left(points, a), bisect_left(points, b); number = limit-first
            require(number >= 64 and 0 < b-a <= 30, 'Unchanged baseline window cannot supply64 distinct native observations')
            ordinals = [first+i*(number-1)//63 for i in range(64)]; samples = [str(points[i]) for i in ordinals]
            identity = dict(source_sha256=source['source_sha256'], video_id=name, window_start_exact=str(a),
                window_end_exact=str(b), source_frame_ordinals=ordinals, sample_exact_pts=samples)
            key = 'view_'+hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
            window = dict(case_id=name+'.baseline%04d'%index, index=index, start_exact=str(a), end_exact=str(b),
                eligible_first=first, eligible_stop=limit, source_frame_ordinals=ordinals, sample_exact_pts=samples, input_view_key=key)
            windows.append(window); views.append(dict(window, group=group, source_name=name, video_id=name,
                source_sha256=source['source_sha256'], window_role='baseline', view_roles=['baseline']))
            aliases.append(dict(video_id=name, role='baseline', planned_case_id=window['case_id'], actual_case_id=window['case_id'], input_view_key=key))
        source_rows.append(dict(video_id=name, source_sha256=source['source_sha256'], physical_end_exact=str(end),
            n_frames=source['n_frames'], windows=windows))
    baseline = dict(schema='RECALL_BASELINE_EQUAL_PLAN_V1', mode='baseline', native_frames=64,
        interval_policy='EXACT_HALF_OPEN_NO_PADDING', source_count=4, window_count=len(views), sources=source_rows,
        window_policy='EQUAL_NONOVERLAP_CEIL_PHYSICAL_END_DIV_30', maximum_window_seconds_exact='30')
    return dict(schema='MIDNIGHT_BASELINE_ONLY_UNIQUE_ACTUAL_VIEW_PLAN_V1', group=group, baseline_plan=baseline,
        unique_views=views, role_aliases=aliases, actual_input_count=len(views), baseline_alias_count=len(views),
        overlap_alias_count=0, shared_actual_inputs=0, maximum_possible_VERIFY_calls=5*len(views),
        same_view_actual_calls=1, scientific_quality_pass=False, GPU_admitted=False, model_calls=0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); commands = parser.add_subparsers(dest='action', required=True)
    prefix = commands.add_parser('export-provider-prefix')
    prefix.add_argument('--id-export', type=Path, required=True); prefix.add_argument('--inventory', type=Path, required=True)
    prefix.add_argument('--output', type=Path, required=True)
    select = commands.add_parser('select')
    for name in ('id-export', 'provider-prefix', 'role-root', 'protocol', 'development-selection', 'output'):
        select.add_argument('--'+name, type=Path, required=True)
    plan = commands.add_parser('baseline-plan'); plan.add_argument('--sources', type=Path, required=True)
    plan.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.action == 'export-provider-prefix':
        export_provider_prefix(args.id_export, args.inventory, args.output)
    elif args.action == 'select':
        select_first_fresh(args.id_export, args.provider_prefix, args.role_root, args.protocol, args.development_selection, args.output)
    else:
        save(args.output, baseline_only_plan(read(args.sources)))
