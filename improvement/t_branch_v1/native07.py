"""First native clocks, byte isolation and unmodified author-interval admission."""
from fractions import Fraction
from pathlib import Path
import sys
import traceback

from t_io import ROOT, WORK, identity, read, save

HELPER = WORK / 'highlight_source_control_20261021_v1'
sys.path.insert(0, str(HELPER))
from native_audit12 import known_isolation, native_clock

TARGET = ROOT / 'native07'


def admit(row, annotations):
    output = TARGET / row['sid']
    output.mkdir()
    media = row['media']
    if identity(media['path']) != media:
        raise ValueError('Acquired media identity changed')
    isolation = known_isolation(media)
    clock = native_clock(Path(media['path']))
    save(output / 'clock.json', clock)
    origin = Fraction(clock['first_PTS_exact'])
    duration = Fraction(clock['physical_end_exact']) - origin
    reviews = [r for r in annotations if r['video_path'] == row['source']['url']]
    if len(reviews) != row['source']['annotators'] or len({r['annotator_id'] for r in reviews}) != len(reviews):
        raise ValueError('Original independent reviewer rows differ')
    for review in reviews:
        for segment in review['summary_timestamps']:
            start, end = [Fraction(str(segment[key])) / 1000 for key in ['start_time', 'end_time']]
            if not 0 <= start < end <= duration:
                raise ValueError('Original human interval exceeds native source; exclude, never repair')
    save(output / 'original_annotations.json', reviews)
    record = dict(sid=row['sid'], media=media, clock=identity(output / 'clock.json'),
                  annotations=identity(output / 'original_annotations.json'), source=row['source'],
                  independent_reviewers=len(reviews), native_frames=clock['native_frames'],
                  exact_duration=str(duration), isolation=isolation,
                  labels='Human summary preference; unselected and unobserved importance remain UNKNOWN',
                  publisher_and_exact_bytes_only_global_source_independence_UNKNOWN=True,
                  quality_metrics_computed=False, no_RGB_or_processor_or_GPU=True)
    save(output / 'acceptance.json', record)
    print('T_NATIVE07_ACCEPTED', row['sid'], clock['native_frames'], len(reviews), flush=True)
    return identity(output / 'acceptance.json')


def main():
    TARGET.mkdir()
    media_terminal = ROOT / 'media06/completion.json'
    annotation = WORK / 'general_highlight_supervision_20261021_v1/lvsum20/annotations__lvsum_72_dataset.json'
    save(TARGET / 'registration.json', dict(
        media_terminal=identity(media_terminal), annotation=identity(annotation),
        native_helper=identity(HELPER / 'native_audit12.py'),
        all_original_reviewers=True, original_milliseconds_exact=True,
        no_label_stretch_padding_truncation_or_reviewer_selection=True,
        no_model_or_training=True))
    rows = read(media_terminal)['accepted']
    annotations = read(annotation)
    accepted, failed = [], []
    for row in rows:
        try:
            accepted.append(admit(row, annotations))
        except Exception:
            failure = dict(sid=row['sid'], traceback=traceback.format_exc(), whole_source_excluded=True)
            save(TARGET / (row['sid'] + '_failure.json'), failure)
            failed.append(failure)
    save(TARGET / 'completion.json', dict(
        state='NATIVE_AND_AUTHOR_PREFERENCE_ADMISSION_COMPLETE', accepted=accepted, failed=failed,
        media_failed=len(read(media_terminal)['failed']), new_model_calls=0,
        training_admission=False, reason='T1 mechanism and exact known/UNKNOWN contract not frozen yet'))


if __name__ == '__main__':
    main()
