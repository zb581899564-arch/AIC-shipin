"""Original human interval schema and native-end admission, outside inference."""
import os
os.environ['CUDA_VISIBLE_DEVICES'] = ''
import hashlib
import json
from fractions import Fraction as F
from pathlib import Path
import sys

ROOT = Path('/home/inspur/aic_video_work/calibrated_event_20261018_v1')
sys.path.insert(0, str(ROOT/'code_v1'))
from calibrate import read, ref, require, save, utc, bound


def extract():
    out = ROOT/'confirm4_reference_01'
    out.mkdir()
    source = Path('/home/inspur/aic_video_work/videoxum_reference_iteration_20261013_v1/metadata_02/val_videoxum.json')
    require(hashlib.sha256(source.read_bytes()).hexdigest() == '2832f423ff5fd768a979665e30345a56f1723aacc1821986b5ec042bed30f556', 'Adopted original author annotation bytes')
    rows = {r['video_id']:r for r in read(source)}
    registration = read(ROOT/'new4_confirmation_registration_01.json')
    frozen = read(ROOT/'frozen_selection.json')
    bound(frozen['weights_ref'])
    references = []
    for selected in registration['selection']:
        raw = rows[selected['video_id']]
        require(str(raw['duration']) == selected['author_duration_raw'], 'Fixed pure metadata author identity')
        labels = [[] for _ in range(10)]
        for event in raw['vsum']:
            require(len(event) == 10, 'All ten original human summary reviewers')
            for k, span in enumerate(event):
                require(len(span) == 2 and F(str(span[0])) >= 0 and F(str(span[1])) > F(str(span[0])), 'Original finite positive human interval')
                labels[k].append([str(span[0]), str(span[1])])
        require(all(labels), 'No reviewer can silently become an empty failure')
        # One-second labels are schema diagnostics only, never resized as native GT.
        onehot = raw['vsum_onehot']
        require(len(onehot) == 10 and all(len(x) == raw['sampled_frames'] and all(v in (0,1) for v in x) for x in onehot), 'Original one-second annotation schema')
        references.append(dict(name=selected['video_id'], author_duration_raw=str(raw['duration']), annotator_intervals_exact_seconds=labels, sampled_frames=raw['sampled_frames'], original_event_count=len(raw['vsum']), original_row_sha256=hashlib.sha256(json.dumps(raw, sort_keys=True).encode()).hexdigest(), texts_exported=False))
    save(out/'references.json', references)
    save(out/'exposure_receipt.json', dict(status='PASS4_FIRST_ORIGINAL_REFERENCE_SCHEMA_AFTER_PAVA_FROZEN', annotation_ref=ref(source), method_frozen_ref=ref(ROOT/'frozen_selection.json'), source_registration_ref=ref(ROOT/'new4_confirmation_registration_01.json'), source_names=[r['name'] for r in references], references_ref=ref(out/'references.json'), labels_not_in_model_or_processor=True, endpoint_admitted=False, quality_metrics_not_computed=True, utc=utc()))
    print(json.dumps(dict(status='PASS4_ORIGINAL_ALL10_SCHEMA_NOT_NATIVE_END_OR_QUALITY', sources=len(references))))


def endpoints():
    pipeline_root = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT/'confirm4_01'
    require(pipeline_root.parent == ROOT and pipeline_root.name in ('confirm4_01', 'confirm4_02'), 'Explicit registered native pipeline root')
    native = read(pipeline_root/'stages/b0_prepare/completion.json')
    references = {v['name']:v for v in read(ROOT/'confirm4_reference_01/references.json')}
    rows = []
    for s in native['sources']:
        clock = read(bound(s['clock_ref']))
        end = F(clock['physical_end_exact'])
        labels = references[s['name']]['annotator_intervals_exact_seconds']
        violations = [(k, i, span) for k, intervals in enumerate(labels) for i, span in enumerate(intervals) if not F(0) <= F(span[0]) < F(span[1]) <= end]
        rows.append(dict(sid=s['sid'], name=s['name'], clock_ref=s['clock_ref'], native_frames=clock['native_frames'], native_end_exact=str(end), zero_origin=F(clock['original_exact_pts'][0]) == 0, violations=violations, pass_native_end=not violations))
    status = 'PASS4_ORIGINAL_ALL10_NATIVE_END_ZERO_ORIGIN_NO_REFERENCE_REPAIR' if all(v['pass_native_end'] and v['zero_origin'] for v in rows) else 'FAILED_ORIGINAL_NATIVE_ENDPOINT_NO_LABEL_REPAIR'
    save(ROOT/'confirm4_reference_01/native_end_acceptance.json', dict(status=status, sources=rows, unchanged_original_labels=True, no_stretch_padding_truncation=True, utc=utc()))
    print(json.dumps(dict(status=status, sources=len(rows))))
    require(status.startswith('PASS'), 'Native endpoint failed; no model launch or reference repair')
    save(ROOT/'confirm4_reference_01/native_admission_for_model.json', dict(status='PASS', source_ids=[r['sid'] for r in rows], clock_sha256_by_sid={r['sid']:r['clock_ref']['sha256'] for r in rows}, original_endpoints_fit=True, no_label_resizing=True, labels_provided_to_model=False, utc=utc()))


if __name__ == '__main__':
    {'extract':extract, 'endpoints':endpoints}[sys.argv[1]]()
