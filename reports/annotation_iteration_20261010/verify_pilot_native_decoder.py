"""One independent CPU replay through original V14 production decoder."""
from pathlib import Path
from fractions import Fraction
import json, hashlib, importlib.util, sys
HERE=Path(__file__).resolve().parent
RUN=HERE.parent/'round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
ROOT=HERE/'native_event_pilot_v1'
sys.path[:0]=[str(RUN/'teacher_student_autopilot_v14'),str(RUN/'baseline_a_pts_v1'),str(RUN/'baseline_a_pts_v1/vendor')]
path=RUN/'teacher_student_autopilot_v14/train_student.py'
spec=importlib.util.spec_from_file_location('pilot_bound_original_decoder',path)
student=importlib.util.module_from_spec(spec);spec.loader.exec_module(student)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
reports=[]
out=ROOT/'native_decoder_cpu_replay.json'
assert not out.exists(),'Successful CPU receipt is immutable; do not repeat'
for folder in map(Path,json.loads((ROOT/'jobs.json').read_text())['jobs']):
    m=json.loads((folder/'manifest.json').read_text());start,end=map(Fraction,m['domain_global_seconds_exact'])
    window=dict(window_id=m['window_id'],source_path=m['source_path'],source_sha256=m['source_sha256'],
        planned_source_frame_ordinals=[r['source_ordinal'] for r in m['frames']],
        planned_actual_pts_sec=[float(Fraction(r['global_seconds_exact'])) for r in m['frames']],
        eligible_source_frame_count=m['eligible_source_frames'],source_total_frames=m['source_total_frames'],
        window_pts_start_sec=float(start),window_duration_sec=float(end-start),height=m['height'],width=m['width'])
    decoded=student.decode_window(window);arr,metadata,plan,evidence=decoded
    assert evidence['frame_pixel_sha256']==[r['rgb_pixel_sha256'] for r in m['frames']]
    assert evidence['source_frame_ids']==window['planned_source_frame_ordinals']
    assert evidence['actual_pts_sec']==window['planned_actual_pts_sec']
    reports.append(dict(window=window,evidence=evidence,manifest_sha256=sha(folder/'manifest.json'),
        status='ORIGINAL_NATIVE_DECODER_PIXEL_ORDINAL_PTS_EQUAL',student_processor_verified=False,
        training_admitted=False,new_model_calls=0,new_optimizer_updates=0))
with out.open('x',encoding='utf-8') as f:json.dump(dict(status='PASS_FOUR_NATIVE_DECODER_REPLAYS_NOT_PROCESSOR_OR_SUPERVISION',
    decoder_source_sha256=sha(path),reports=reports),f,ensure_ascii=False,indent=2)
print(json.dumps(dict(status='PASS_FOUR_NATIVE_DECODER_REPLAYS_NOT_PROCESSOR_OR_SUPERVISION',windows=len(reports),path=str(out))))
