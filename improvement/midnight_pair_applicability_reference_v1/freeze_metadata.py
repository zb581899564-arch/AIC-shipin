"""One metadata registration, before current HEAD or media; no inference."""
from fractions import Fraction as F
from decimal import Decimal
import hashlib
from pathlib import Path
import sys
from applicability_contract import *

def main():
    require(sys.platform == 'linux' and Path(__file__).resolve().parent == ROOT, 'Exact new Linux root required')
    require(not (ROOT/'new_selection.json').exists(), 'Never repeat registered selection')
    meta = read(ROOT/'isolation_metadata.json'); p, d, original = original_contract(meta)
    template = read(ROOT/'source_candidates_template.json')
    # All eligible lengths and IDs were exported without reading any event labels.
    short = {r['video_id']: r['author_duration_raw'] for r in meta['eligible_short_author_metadata']}
    annotation = json.loads(checked(meta['annotation_ref']).read_text(encoding='utf-8-sig'), parse_float=Decimal)
    actual_short = {row['video_id']:str(row['duration']) for row in annotation
        if row['video_id'] not in meta['excluded_source_IDs'] and 0 < F(str(row['duration'])) <= 30}
    del annotation
    require(actual_short == short, 'Metadata-only author duration/ID stratum must equal the complete pinned annotation')
    salt = 'RECALL_VERIFY40_46_VIDE0XUM_SMALL8_20261014_V1'
    inventory = read(ROOT/'provider_short_metadata.json')
    eligible = []
    for name, length in short.items():
        require(0 < F(length) <= 30 and name not in meta['excluded_source_IDs'], 'Short metadata isolation changed')
        if name in inventory['providers']:
            row = dict(video_id=name, author_duration_raw=length, youtube_id=name[2:],
                selection_hash=hashlib.sha256((salt+'|'+name).encode()).hexdigest(), provider=inventory['providers'][name])
            eligible.append(row)
    eligible.sort(key=lambda r:r['selection_hash'])
    require(len(short) == 95 and len(eligible) == 77 and eligible[:4] == template['selection']
        and eligible[4:6] == template['ordered_engineering_reserves'], 'Original hash order/short strata cannot be changed')
    for key in ('annotation_ref', 'known_exclusions_ref', 'previous_source_candidates_ref', 'previous_fresh_media_completion_ref'):
        checked(meta[key])
    for value in meta['prior_registry_refs']+meta['prior26_media_receipts']+meta['source_scope_refs']:
        checked(value)
    protocol = dict(schema='MIDNIGHT_SINGLE_SUPPLEMENTAL_PAIR_SHORT_PROTOCOL_V1',
        selected_policies=['PAIR_ONLY'], stratum='AUTHOR_DECLARED_0_LT_DURATION_LE_30_SECONDS',
        selection_uses_labels=False, selection_hash_salt=salt, single_additional_cohort_only=True,
        engineering_replacement_only=['PUBLIC_OBJECT_404','EXPLICIT_ORIGINAL_NATIVE_DOMAIN_REJECTED','EXPLICIT_ORIGINAL_REFERENCE_NATIVE_DOMAIN_REJECTED'],
        native_domain='ZERO_ORIGIN_EXACT_PTS_AND_PHYSICAL_END_LE30_AND_AT_LEAST64_DISTINCT_FRAMES',
        no_quality_based_replacement=True, full_source_count=4, full_original_raters=True,
        original_policy_protocol_ref=ref(checked(meta['original_policy_protocol_ref'])),
        original_development_selection_ref=ref(checked(meta['original_development_selection_ref'])),
        prior_neutral_no_applicability_result_ref=ref(checked(meta['previous_neutral_PAIR_result_ref'])),
        deletion_quality_gates=p['deletion_quality_gates'], deadline=DEADLINE,
        expected_B0_views=4, maximum_rank_nonempty_views=4,
        gpu_budgets=dict(B0=dict(calls=4,seconds=900),VERIFY=dict(calls=20,seconds=1800),RANK=dict(calls=4,seconds=600)),
        selected_media_bytes=21961720, maximum_media_pool_bytes=26768757,
        outcome_if_no_pair_or_quality_failure='STOP_NO_FURTHER_POOL_OR_COHORT', new_metrics_examined=False)
    save(ROOT/'supplemental_protocol.json', protocol)
    selection = dict(original, selected_policies=['PAIR_ONLY'],
        selected_predictions_genuinely_distinct=False, original_development_selection_ref=ref(checked(meta['original_development_selection_ref'])),
        supplemental_protocol_ref=ref(ROOT/'supplemental_protocol.json'), prior_fresh_result_ref=ref(checked(meta['previous_neutral_PAIR_result_ref'])),
        prior_confirm_metrics_examined=True, old_confirm_result_unchanged=True,
        confirm_metrics_examined=False, confirm_metrics_examined_scope='THIS_NEW_SHORT_COHORT_ONLY',
        selection_reason='ORIGINAL_DEVELOPMENT_PASS_AWAITING_APPLICABILITY_IN_SINGLE_PREDECLARED_SHORT_SOURCE_STRATUM')
    save(ROOT/'new_selection.json', selection)
    candidates = dict(template, development_selection_ref=ref(ROOT/'new_selection.json'),
        supplemental_protocol_ref=ref(ROOT/'supplemental_protocol.json'),
        source_isolation_metadata_ref=ref(ROOT/'isolation_metadata.json'),
        status='REGISTERED_SHORT_SOURCE_APPLICABILITY_METADATA_BEFORE_FIRST_HEAD_OR_MEDIA',
        metadata_selection_registered_before_current_HEAD=True, reference_labels_or_event_text_examined=False)
    save(ROOT/'source_candidates.json', candidates)
    validate_selection()
    print('REGISTERED_SHORT4_METADATA', candidates['selected_media_bytes'], candidates['maximum_pool_bytes'])

if __name__ == '__main__':
    main()
