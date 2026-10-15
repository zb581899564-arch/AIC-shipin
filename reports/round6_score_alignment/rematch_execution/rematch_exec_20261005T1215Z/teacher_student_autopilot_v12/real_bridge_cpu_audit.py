"""Replay private real numeric metadata through the repaired bridge, no GPU."""
from decimal import Decimal
from fractions import Fraction
import json
from pathlib import Path
import train_student as s
import teacher_label as t

s.helper_paths(t.HERE.parent)
from contracts import answer_string,parse_segments
from constrained_json import BoundedSegmentsGrammar
from training_target import from_teacher_record,target_text


def run():
    config=t.read(t.HERE/'config.json');selection=Path(config['selection_dir'])
    windows=t.rows(selection/'selected_train.jsonl')+t.rows(selection/'selected_dev.jsonl')
    records=t.rows(t.HERE.parent/'teacher_student_autopilot_v5/pilot_01/validated/validated_records.jsonl')
    old=s.load(t.HERE.parent/'next_round_v1/contracts.py','original_precision_for_replay')
    scanned=0;maximum_digits=0;old_failed=0
    for window in windows:
        duration=window['window_duration_sec']
        points=sorted(set([0.0,duration]+[float(Fraction(str(v))-Fraction(str(window['window_pts_start_sec'])))
                                      for v in window['planned_actual_pts_sec']]))
        for point in points:
            if point==0:continue
            maximum_digits=max(maximum_digits,max(0,-Decimal(str(point)).as_tuple().exponent))
            text=answer_string([[0,point]],duration)
            assert json.loads(text)['segments']==[[0,point]]
            assert BoundedSegmentsGrammar(duration).complete(text),text
            assert parse_segments(text,duration)==([[0,point]],[],[]),text
            scanned+=1
    for record in records:
        label=from_teacher_record(record);text=target_text(label,record['window']['window_duration_sec'])
        assert json.loads(text)==json.loads(record['target_json'])
        assert BoundedSegmentsGrammar(record['window']['window_duration_sec']).complete(text)
        assert parse_segments(text,record['window']['window_duration_sec'])[0]==json.loads(record['target_json'])['segments']
        try:old.answer_string(json.loads(record['target_json'])['segments'],record['window']['window_duration_sec'])
        except ValueError:old_failed+=1
    decoded=[]
    for split in ('train','dev'):
        record=next(r for r in records if r['split']==split)
        window=record['window']
        array,_,_,evidence=s.decode_window(window,record['actual_observation'])
        points=evidence['window_source_pts_sec']
        assert len(points)==window['eligible_source_frame_count']
        assert all(b>a for a,b in zip(points,points[1:]))
        from native_segment_contract import native_segment_ranges
        ranges=native_segment_ranges(json.loads(record['target_json'])['segments'],points,
            window['window_pts_start_sec'],window['window_duration_sec'])
        decoded.append({'window_id':record['window_id'],'split':split,'actual_source_frame_pts_count':len(points),
            'provided_64_pixel_sha_identity_pass':True,'segments_with_actual_frames':len(ranges)})
        del array
    report={'status':'PASS_REAL_METADATA_TEACHER_STUDENT_PRECISION_REPLAY','selected_windows':len(windows),
        'native_endpoint_cases':scanned,'maximum_original_fractional_digits':maximum_digits,
        'real_preserved_pilot_targets':len(records),'old_serializer_rejected_real_targets':old_failed,
        'repaired_serializer_rejections':0,'original_numeric_values_changed':0,'optimizer_steps':0,'GPU_started':False,
        'weak_semantic_quality_not_admitted':True,'real_decode_acceptances':decoded,
        'records_sha256':t.sha(t.HERE.parent/'teacher_student_autopilot_v5/pilot_01/validated/validated_records.jsonl')}
    t.save(t.HERE/'real_bridge_cpu_acceptance.json',report,fresh=True);print(json.dumps(report))


if __name__=='__main__':run()
