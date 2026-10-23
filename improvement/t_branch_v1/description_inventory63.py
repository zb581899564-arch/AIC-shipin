"""First use of original human event descriptions; no new labels or model work."""
from bisect import bisect_left
from collections import Counter, defaultdict
from fractions import Fraction as F
import hashlib
from pathlib import Path
import traceback

from native_sets import NativeTimeline
from t_io import ROOT, check, identity, read, save

OUT = ROOT / 'description_inventory63'


def rank(value):
    return hashlib.sha256(('T-human-description63/' + value).encode()).hexdigest()


def view(points, start, end):
    first, stop = bisect_left(points, start), bisect_left(points, end)
    if stop - first < 64:
        return None
    ordinals = [first + index * (stop - first - 1) // 63 for index in range(64)]
    return dict(start_exact=str(start), end_exact=str(end), eligible_first=first, eligible_stop=stop,
        source_frame_ordinals=ordinals, sample_exact_pts=[str(points[index]) for index in ordinals])


def source_examples(source):
    clock = read(check(source['clock'])); timeline = NativeTimeline.from_clock(clock)
    rows = read(check(source['annotations'])); found, excluded = {}, Counter()
    total = 0
    for review in rows:
        for index, segment in enumerate(review['summary_timestamps']):
            total += 1
            text = segment.get('description')
            if not isinstance(text, str) or not text.strip():
                excluded['missing_description'] += 1; continue
            start, end = F(str(segment['start_time'])) / 1000, F(str(segment['end_time'])) / 1000
            if not 0 <= start < end <= timeline.end:
                raise ValueError('Original human annotation endpoint invalid; never repair')
            if end - start > 30:
                excluded['whole_original_interval_longer_than_native30_profile'] += 1; continue
            correct = view(timeline.points, start, end)
            if correct is None:
                excluded['fewer_than64_real_frames_no_duplication'] += 1; continue
            length = end - start
            if timeline.end <= 2 * length:
                excluded['no_disjoint_equal_length_control'] += 1; continue
            wrong_start = (start + timeline.end / 2) % (timeline.end - length)
            wrong_end = wrong_start + length
            if max(wrong_start, start) < min(wrong_end, end):
                excluded['fixed_control_overlaps_original'] += 1; continue
            wrong = view(timeline.points, wrong_start, wrong_end)
            if wrong is None:
                excluded['fixed_control_fewer_than64_real_frames'] += 1; continue
            key = rank(source['sid'] + '/' + str(start) + '/' + str(end) + '/' + text)
            if key not in found:
                found[key] = dict(example_id=source['sid'] + '_D' + key[:16], source=source,
                    exact_original_description=text, original_interval_exact=[str(start), str(end)],
                    original_annotation=source['annotations'], original_human_rows=[],
                    correct_view=correct, wrong_native_view=wrong,
                    wrong_is_control_not_semantic_ordinary=True)
            found[key]['original_human_rows'].append(dict(annotator=review['annotator_id'], segment_index=index))
    return list(found.values()), dict(sid=source['sid'], publisher=source['publisher'], role=source['role'],
        original_description_rows=total, eligible_distinct_description_interval_pairs=len(found), exclusions=dict(excluded),
        source_byte_identity=source['media']['sha256'], original_labels_preserved=True)


def balanced(rows, count):
    groups = defaultdict(lambda: defaultdict(list))
    for row in rows:
        groups[row['source']['publisher']][row['source']['sid']].append(row)
    streams = {}
    for publisher, sources in groups.items():
        queues = {sid: sorted(values, key=lambda row: rank(row['example_id'])) for sid, values in sources.items()}
        stream = []
        while any(queues.values()):
            for sid in sorted(queues, key=rank):
                if queues[sid]:
                    stream.append(queues[sid].pop(0))
        streams[publisher] = stream
    selected = []
    while any(streams.values()) and len(selected) < count:
        for publisher in sorted(streams, key=rank):
            if streams[publisher] and len(selected) < count:
                selected.append(streams[publisher].pop(0))
    return selected


def main():
    OUT.mkdir()
    registry = ROOT / 'source_registry09/registration.json'
    sources = [row for row in read(registry)['sources'] if row['role'] in ('fit', 'development')]
    if Counter(row['role'] for row in sources) != dict(fit=9, development=2):
        raise ValueError('Original fit/dev source roles differ; never read confirmation')
    save(OUT / 'registration.json', dict(original_source_registry=identity(registry),
        code=identity(Path(__file__)), purpose='Original human content-description supervision, not timestamp JSON targets or machine labels',
        selected_fit_max=16, selected_dev_max=8, source_and_publisher_balanced_hash=True,
        no_annotation_text_or_interval_edit=True, no_new_GPU_training_or_confirmation=True,
        long_or_insufficient_native_intervals_excluded_for_training_only=True,
        evaluation_still_all_original_reviews_and_complete_sources=True))
    fit, development, audit = [], [], []
    for source in sources:
        rows, counts = source_examples(source); audit.append(counts)
        (fit if source['role'] == 'fit' else development).extend(rows)
    selected_fit, selected_dev = balanced(fit, 16), balanced(development, 8)
    adequate = (len(selected_fit) == 16 and len(selected_dev) == 8
        and len({row['source']['publisher'] for row in selected_fit}) >= 3
        and len({row['source']['sid'] for row in selected_dev}) == 2)
    save(OUT / 'selected_examples.json', dict(fit=selected_fit, development=selected_dev))
    save(OUT / 'completion.json', dict(state='HUMAN_DESCRIPTION_INPUT_INVENTORY_PASS' if adequate else 'STOP_INSUFFICIENT_HUMAN_DESCRIPTION_INPUTS',
        sources=audit, selected_examples=identity(OUT / 'selected_examples.json'),
        fit_examples=len(selected_fit), dev_examples=len(selected_dev),
        fit_recordings=len({row['source']['sid'] for row in selected_fit}),
        fit_publishers=len({row['source']['publisher'] for row in selected_fit}),
        correct_and_disjoint_wrong_views=2 * (len(selected_fit) + len(selected_dev)),
        no_model_or_training_admission_yet=True, no_zero_vote_or_unselected_as_ordinary=True,
        no_fresh_confirmation_read=True, no_new_download=True))


if __name__ == '__main__':
    try:
        main()
    except Exception:
        if OUT.exists():
            save(OUT / 'failure.json', dict(traceback=traceback.format_exc()))
        raise
