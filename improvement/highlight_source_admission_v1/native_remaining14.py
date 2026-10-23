"""Use original authoritative frame endpoints, retain auxiliary count discrepancies."""
import csv
import hashlib
import json
from pathlib import Path
import time

from direct import ROOT, ref, save
from native_audit12 import native_clock, known_isolation


def read_original_labels(path):
    rows = list(csv.DictReader(path.open(newline='',encoding='utf-8-sig')))
    expected, intervals, discrepancies = 0, [], []
    encoding = {'Highlight':1,'Not a highlight':0,'Uncertainty':-1}
    if not rows or set(rows[0]) != {'Event type','First frame','Last frame','Num. frames'}:
        raise ValueError('Original CSV schema changed')
    for number,row in enumerate(rows):
        start,end,declared=[int(row[key]) for key in ['First frame','Last frame','Num. frames']]
        if row['Event type'] not in encoding or start != expected or end < start:
            raise ValueError('Ambiguous original frame ordinal or label')
        if declared != end-start+1:
            discrepancies.append(dict(row=number,original_declared_count=declared,
                original_first=start,original_last=end,inclusive_endpoint_count=end-start+1))
        intervals.append(dict(first=start,last=end,label=encoding[row['Event type']],
            original_declared_count=declared))
        expected=end+1
    return intervals,expected,discrepancies


def one_source(stem,folder):
    target=ROOT/'native14'/stem;target.mkdir()
    media,annotation=ref(folder/(stem+'.mp4')),ref(folder/(stem+'.csv'))
    intervals,expected,discrepancies=read_original_labels(Path(annotation['path']))
    if stem=='diving':
        first_clock=ROOT/'native14'/'diving_clock.json'
        first_media=ROOT/'media'/'sportclip_members13'/'diving.mp4'
        if ref(first_media)['sha256'] != media['sha256']:
            raise ValueError('Adopted first native measurement media changed')
        clock=json.loads(first_clock.read_text());clock_ref=ref(first_clock)
    else:
        clock=native_clock(Path(media['path']))
        save(target/'clock.json',clock);clock_ref=ref(target/'clock.json')
    if clock['native_frames'] != expected:
        raise ValueError(f'Original label domain/native frame mismatch: {stem} {expected=} native={clock["native_frames"]}')
    save(target/'labels_original_endpoints.json',dict(intervals=intervals,native_frames=expected,
        known_encoding={'HL':1,'NHL':0,'UN':-1},uncertainty_masked_not_background=True,
        no_original_endpoint_or_class_changed=True,original_count_column_diagnostic=discrepancies,
        author_evaluator_uses_first_last_inclusive_not_Num_frames=True))
    result=dict(source=stem,media=media,annotation=annotation,clock=clock_ref,
        labels=ref(target/'labels_original_endpoints.json'),known_isolation=known_isolation(media),
        original_count_discrepancies=discrepancies,
        counts={str(label):sum(row['last']-row['first']+1 for row in intervals if row['label']==label)
            for label in [-1,0,1]},native_frames=expected,
        author_frame_endpoints_equal_native_decode=True,
        old13_auxiliary_count_FAILURE_preserved=True,
        first_successful_diving_clock_adopted=stem=='diving')
    save(target/'acceptance.json',result)
    print('NATIVE_ACCEPTED',json.dumps({key:result[key] for key in ['source','native_frames','counts','original_count_discrepancies']}),flush=True)
    return ref(target/'acceptance.json')


def main():
    previous=json.loads((ROOT/'native13_registration.json').read_text())
    save(ROOT/'native_remaining14_registration.json',dict(
        previous=ref(ROOT/'native13_registration.json'),actual_failure=ref(ROOT/'native13_failure.json'),
        diagnosis='Only redundant Num.frames last-row arithmetic differs by1; author evaluator uses endpoints',
        author_code_evidence={'url':'https://github.com/MarcosRodrigoT/SportCLIP/blob/main/utils.py',
            'function':'createGrounTruth','inclusive_first_last':True,'Num.frames_not_used':True},
        endpoint_class_and_uncertainty_fields_unchanged=True,
        source_roles_unchanged=previous['roles'],adopt_first_diving_clock=ref(ROOT/'native14'/'diving_clock.json'),
        no_successful_decode_repeated=True,max_wait_seconds=1200,no_GPU=True,no_training=True))
    started=time.monotonic()
    while not (ROOT/'sportclip_remaining11_completion.json').exists():
        if (ROOT/'sportclip_remaining11_failure.json').exists():
            raise RuntimeError('Remaining acquisition actually failed; preserve native first clock')
        if time.monotonic()-started > 1200:
            raise TimeoutError('Bounded wait for original archive elapsed')
        time.sleep(2)
    rows=[one_source(stem,ROOT/'media'/'sportclip10')
        for stem in ['diving','long_jump','pole_vault','tumbling']]
    save(ROOT/'native_remaining14_completion.json',dict(
        state='PASS4_ORIGINAL_MEDIA_MANUAL_FRAME_ALIGNMENT',sources=rows,
        source_count=4,source_roles=previous['roles'],new_model_calls=0,new_training=0,
        no_automatic_production=True,all_auxiliary_count_discrepancies_preserved=True,
        no_frame_padding_truncation_label_stretch=True,time=time.time()))


if __name__=='__main__':
    try:
        main()
    except Exception as error:
        save(ROOT/'native_remaining14_failure.json',dict(error=repr(error),time=time.time()))
        raise
