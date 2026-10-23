"""First whole-review content-target inventory, no images, models or held labels."""
from collections import Counter
import json
from pathlib import Path
import sys

from t_io import ROOT, WORK, check, identity, read, save

OUT = ROOT / 'summary_content81'


def whole_review_target(row):
    """Preserve every selected-event description; never invent an empty target."""
    intervals = row.get('summary_timestamps')
    if not isinstance(intervals, list) or not intervals:
        raise ValueError('Unknown or absent summary cannot become empty supervision')
    descriptions = []
    for interval in intervals:
        text = interval.get('description')
        if not isinstance(text, str) or not text.strip():
            raise ValueError('Incomplete human content excludes this whole task')
        descriptions.append(text)
    # No timestamp, score, reviewer identity, or source identity in the target.
    return json.dumps(dict(summary=descriptions), ensure_ascii=False, separators=(',', ':'))


def contracts():
    row = dict(annotator_id='not-an-input', summary_timestamps=[
        dict(start_time=123, end_time=456, score=3, description='A visible event.'),
        dict(start_time=789, end_time=999, score=1, description='A second event.')])
    expected = dict(summary=['A visible event.', 'A second event.'])
    if json.loads(whole_review_target(row)) != expected:
        raise ValueError('Content target included unrelated numeric labels or omitted events')
    for invalid in [{}, dict(summary_timestamps=[]), dict(summary_timestamps=[dict(description=' ')])]:
        try:
            whole_review_target(invalid)
        except ValueError:
            continue
        raise ValueError('Unknown annotation became a successful empty target')
    return dict(checks=4, all_pass=True, no_model_calls=True)


def source_targets(source):
    original = read(check(source['annotations']))
    rows = []
    reviewers = set()
    for index, row in enumerate(original):
        reviewer = row.get('annotator_id')
        if not isinstance(reviewer, str) or reviewer in reviewers:
            raise ValueError('Original review identity missing or duplicated')
        reviewers.add(reviewer)
        rows.append(dict(original_row=index, reviewer=reviewer, target=whole_review_target(row),
                         original_selected_events=len(row['summary_timestamps'])))
    if len(rows) != source['independent_reviewers']:
        raise ValueError('All-original-reviewer denominator differs')
    path = OUT / (source['sid'] + '_targets.json')
    save(path, dict(source=source, scope='Selected-event content, not selection reasons or dense NHL',
        reviews=rows, original_annotations=source['annotations'],
        original_order_and_all_descriptions_preserved=True, score_not_used=True,
        no_timestamps_as_training_targets=True, unselected_semantics='UNKNOWN'))
    return identity(path), len(rows), sum(r['original_selected_events'] for r in rows)


def main():
    OUT.mkdir()
    registry = read(ROOT / 'source_registry09/registration.json')
    sources = [s for s in registry['sources'] if s['role'] == 'fit']
    if len(sources) != 9:
        raise ValueError('Original nine-fit source split changed')
    # Reuse the same native uniform planner; do not read fresh confirmation labels.
    sys.path.insert(0, str(WORK / 'general_highlight_supervision_20261021_v1/code'))
    from time_control50_prepare import source_windows
    rows = []; reviews = events = windows = 0
    for source in sources:
        target, count, n_events = source_targets(source)
        _, _, plan = source_windows(source)
        rows.append(dict(source=source, targets=target, windows=plan))
        reviews += count; events += n_events; windows += len(plan)
    save(OUT / 'completion.json', dict(state='FIRST_NINE_FIT_WHOLE_REVIEW_CONTENT_INVENTORY_PASS',
        original_registry=identity(ROOT / 'source_registry09/registration.json'),
        source_count=9, publisher_counts=dict(Counter(s['publisher'] for s in sources)),
        all_original_reviews=reviews, all_selected_event_descriptions=events,
        whole_source_windows=windows, planned=rows, CPU_contracts=contracts(),
        annotation_task='Author-declared human timestamped summaries; descriptions of selected content',
        not_human_rationale_or_dense_ordinary=True, author_Gemini_transcripts_not_used=True,
        independent_fresh_confirmation_labels_read=False, new_model_calls=0,
        new_training=0, training_admitted=False, production_admitted=False,
        next='Check all nine-source label-independent AV inputs, exact source/reviewer weighting, '
             'text context limits and actual budget before a separate summary-content mechanism registration.'))


if __name__ == '__main__':
    main()
