"""First original-frame/HL-NHL-UN alignment, with uncertainty kept separate."""
import csv
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import time

from direct import ROOT, save, ref


def annotation_intervals(path):
    rows = list(csv.DictReader(path.open(newline="", encoding="utf-8-sig")))
    if not rows or set(rows[0]) != {"Event type","First frame","Last frame","Num. frames"}:
        raise ValueError("Unexpected author CSV schema")
    expected, parsed = 0, []
    labels = {"Highlight":1,"Not a highlight":0,"Uncertainty":-1}
    for row in rows:
        start, end, count = [int(row[key]) for key in ("First frame","Last frame","Num. frames")]
        if row["Event type"] not in labels or start != expected or end < start or count != end-start+1:
            raise ValueError("Noncontiguous or inconsistent original inclusive frame interval")
        parsed.append(dict(first=start,last=end,count=count,label=labels[row["Event type"]]))
        expected = end+1
    return parsed, expected


def native_clock(path):
    import av
    points, durations, geometry = [], [], None
    with av.open(str(path)) as container:
        if len(container.streams.video) != 1:
            raise ValueError("Ambiguous video stream")
        stream = container.streams.video[0]
        # One decoder thread avoids claiming shared CPU cores during admission.
        stream.codec_context.thread_count = 1
        for ordinal, frame in enumerate(container.decode(stream)):
            if frame.pts is None or frame.time_base is None:
                raise ValueError("Missing original frame PTS")
            point = Fraction(frame.pts)*Fraction(frame.time_base)
            if points and point <= Fraction(points[-1]):
                raise ValueError("Nonmonotone native presentation order")
            current = (frame.width,frame.height)
            geometry = current if geometry is None else geometry
            if geometry != current:
                raise ValueError("Native geometry changed")
            duration = getattr(frame,"duration",None)
            points.append(str(point))
            durations.append(str(Fraction(duration)*frame.time_base) if duration else None)
        if not points or durations[-1] is None or Fraction(durations[-1]) <= 0:
            raise ValueError("Actual positive last-frame duration required")
        return dict(PTS=points, frame_durations=durations, native_frames=len(points),
            physical_end_exact=str(Fraction(points[-1])+Fraction(durations[-1])),
            first_PTS_exact=points[0], width=geometry[0],height=geometry[1],
            stream_time_base=str(stream.time_base),decoder=av.__version__,
            rate_diagnostic_only=str(stream.average_rate),
            container_duration_diagnostic_only=container.duration,
            no_frame_resampling=True,no_label_padding_truncation_or_stretch=True)


def known_isolation(media):
    source = Path('/home/inspur/aic_video_work/human_reference_iteration_20261013_v1/known_identity_snapshot_01.json')
    snapshot = json.loads(source.read_text())
    rows = snapshot['training']['sources']+snapshot['testing']['records']
    if len(snapshot['training']['sources']) != 704 or len(snapshot['testing']['records']) != 426:
        raise ValueError("Known identity inventory incomplete")
    matches = [row for row in rows if row['source_sha256']==media['sha256']]
    if matches:
        raise ValueError("Known training/test exact media intersection")
    return dict(snapshot=ref(source),known_train_clips=704,known_test_sources=426,
        exact_byte_intersection=0,global_pretraining_overlap='UNKNOWN',
        semantic_content_identity_beyond_publisher_and_bytes='UNKNOWN')


def audit_source(stem, folder):
    destination = ROOT/'native12'/stem
    destination.mkdir()
    media, annotation = ref(folder/(stem+'.mp4')), ref(folder/(stem+'.csv'))
    isolation = known_isolation(media)
    intervals, count = annotation_intervals(Path(annotation['path']))
    clock = native_clock(Path(media['path']))
    save(destination/'clock.json',clock)
    if count != clock['native_frames']:
        raise ValueError(f"Author frame domain does not equal original decode: {stem} {count=} native={clock['native_frames']}")
    save(destination/'original_labels.json',dict(intervals=intervals,frames=count,
        indexing='original zero-based inclusive; author extractor start_number0 / createGrounTruth last+1',
        UNKNOWN=-1,HL=1,NHL=0,uncertainty_never_background=True))
    result = dict(source=stem,media=media,annotation=annotation,clock=ref(destination/'clock.json'),
        original_labels=ref(destination/'original_labels.json'),isolation=isolation,
        native_frames=count,counts={str(value):sum(row['count'] for row in intervals if row['label']==value)
            for value in [-1,0,1]},
        independent_recording_count=1,window_count_is_not_independent_source_count=True,
        scope='Static-camera athletic-performance HL; not general highlight or official joint truth')
    save(destination/'acceptance.json',result)
    print(json.dumps({key:result[key] for key in ['source','native_frames','counts']}),flush=True)
    return ref(destination/'acceptance.json')


def main():
    completion = json.loads((ROOT/'sportclip_remaining11_completion.json').read_text())
    folder = ROOT/'media'/'sportclip10'
    sources = ['diving','long_jump','pole_vault','tumbling']
    ordered = sorted(sources,key=lambda value:hashlib.sha256(('UPM-SportCLIP-v1/'+value).encode()).hexdigest())
    save(ROOT/'native12_registration.json',dict(
        source_archive=completion['archive_sha256'],source_hash_order=ordered,
        tentative_source_roles={name:('held_sport' if name==ordered[-1] else 'development') for name in sources},
        no_held_metric_before_frozen_candidate=True, no_model_calls_in_this_stage=True,
        author_index_evidence=['https://github.com/MarcosRodrigoT/SportCLIP/blob/main/extractor.py#L60',
            'https://github.com/MarcosRodrigoT/SportCLIP/blob/main/utils.py#L28'],
        equality_required='all original CSV frame ordinals exactly equal native decode domain',
        semantic_scope='Athlete actively performing versus explicit non-highlight, uncertainty masked',
        dataset_license='Author-provided local research benchmark; no broader redistribution claimed',
        source_count=4,unseen_global_pretraining_overlap='UNKNOWN'))
    (ROOT/'native12').mkdir()
    rows = [audit_source(source,folder) for source in sources]
    save(ROOT/'native12_completion.json',dict(state='PASS_FOUR_ORIGINAL_MEDIA_MANUAL_FRAME_ALIGNMENT',
        sources=rows,source_count=4,no_new_model=True,no_automatic_production=True,time=time.time()))


if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        save(ROOT/'native12_failure.json',dict(error=repr(error),time=time.time()))
        raise
