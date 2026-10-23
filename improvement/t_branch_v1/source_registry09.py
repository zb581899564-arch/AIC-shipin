"""Freeze source roles before new quality results; adopt old native acceptances."""
from collections import Counter
import hashlib

from t_io import ROOT, WORK, check, identity, read, save

OLD = WORK / 'general_highlight_supervision_20261021_v1'


def normalize(ref, history):
    row = read(check(ref))
    source = row.get('original_source', row.get('source'))
    if not isinstance(source, dict):
        raise ValueError('Original publisher/source identity is not a mapping')
    clock, labels = read(check(row['clock'])), read(check(row['annotations']))
    if row['native_frames'] != clock['native_frames']:
        raise ValueError('Bound native count differs')
    return dict(sid=row['sid'], source=source, acceptance=ref,
                media=row['media'], clock=row['clock'], annotations=row['annotations'],
                native_frames=clock['native_frames'], independent_reviewers=len(labels),
                publisher=source['host'], historical_quality_exposure=history,
                exact_source_independence='Known identity/byte checks only; global overlap UNKNOWN')


def main():
    output = ROOT / 'source_registry09'
    output.mkdir()
    old_terminal = [OLD / 'native25/completion.json', OLD / 'speech36/input_acceptance.json']
    new_terminal = ROOT / 'native07/completion.json'
    old = [normalize(ref, True) for path in old_terminal for ref in read(path)['accepted']]
    new = [normalize(ref, False) for ref in read(new_terminal)['accepted']]
    if len(old) != 11 or len(new) < 3:
        raise ValueError('Expected eleven adopted sources and at least three newly aligned sources')
    rows = old + new
    if len({r['sid'] for r in rows}) != len(rows) or len({r['media']['sha256'] for r in rows}) != len(rows):
        raise ValueError('Repeated recording or exact media bytes')
    publishers = sorted({r['publisher'] for r in old}, key=lambda h: hashlib.sha256(('T-publisher-role-v1/' + h).encode()).hexdigest())
    development = set(publishers[-2:])
    fresh_publishers = {r['publisher'] for r in new}
    if fresh_publishers & set(publishers):
        raise ValueError('Fresh confirmation publisher overlaps with fit/development')
    for row in rows:
        row['role'] = ('confirmation' if not row['historical_quality_exposure'] else
                       'development' if row['publisher'] in development else 'fit')
    baseline = identity(WORK / 'semantic_context_production_20261016_v1/package/candidate_CONTEXT_SEMANTIC_RESIDUAL.zip')
    if baseline['bytes'] != 384630 or baseline['sha256'] != 'b37c4a2e6593fc800f54ecce2f860fee5e7d5dc74e17ce280f9ee6722afbccd3':
        raise ValueError('Protected 40.47 differs')
    record = dict(state='SOURCE_ROLES_FROZEN_NOT_TRAINING_ADMISSION', sources=rows,
                  role_counts=dict(Counter(r['role'] for r in rows)),
                  publisher_groups=len({r['publisher'] for r in rows}),
                  original_acceptances=[identity(p) for p in old_terminal + [new_terminal]],
                  protected_baseline=baseline, independent_recordings=len(rows),
                  labels='Unmodified multi-rater human summaries; preference, not dense HL/NHL',
                  summary_unselected_and_unrated_importance_remain_semantically_UNKNOWN=True,
                  new_confirmation_metrics_exposed=False,
                  strict_global_source_or_pretraining_blindness_claim=False,
                  no_decode_RGB_processor_or_model_repeated=True,
                  main_training_admitted=False,
                  remaining='True T supervision/mechanism agreement and small-pilot contract; do not launch old SFT or UMT')
    save(output / 'registration.json', record)
    # Histogram only on historically exposed fitting/development labels; confirmation stays unevaluated.
    scores = Counter()
    for row in old:
        for review in read(check(row['annotations'])):
            for segment in review['summary_timestamps']:
                scores[str(segment.get('score', 'MISSING'))] += 1
    save(output / 'adopted_label_schema.json', dict(
        original_selected_interval_score_histogram=dict(scores),
        only_historical_sources_read=True,
        selected_low_importance_is_not_explicit_generic_ordinary=True,
        no_unknown_to_zero_conversion=True))
    save(output / 'completion.json', dict(
        state=record['state'], sources=len(rows), role_counts=record['role_counts'],
        native_frames=sum(r['native_frames'] for r in rows),
        human_reviews=sum(r['independent_reviewers'] for r in rows),
        registry=identity(output / 'registration.json'),
        source_and_label_scope='Human summary preferences only; no new dense ordinary labels',
        new_model_calls=0, new_training=0, new_ZIP=0, baseline_unchanged=True))
    print('T_REGISTRY09_COMPLETE', len(rows), record['role_counts'], flush=True)


if __name__ == '__main__':
    main()
