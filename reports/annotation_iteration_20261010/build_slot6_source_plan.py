"""Reconstruct Pro's public source rule and bind actual B native window planner."""
from pathlib import Path
from fractions import Fraction as F
from bisect import bisect_left
import json,hashlib,sys,importlib.util,numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
DISC=ROOT/'reports/round6_score_alignment/rematch_discussion/aic_video_empty407_20261010'
RUN=ROOT/'reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
SEED='EMPTY407_SLOT6_SILVER24_V1'
OUT=HERE/'slot6_silver24_v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):
    with p.open('x',encoding='utf-8') as f:json.dump(d,f,ensure_ascii=False,indent=2)
sys.path[:0]=[str(RUN/'next_round_v1'),str(RUN/'baseline_a_pts_v1')]
spec=importlib.util.spec_from_file_location('slot6_registered_frame_contract',RUN/'next_round_v1/frame_contract.py')
frames=importlib.util.module_from_spec(spec);spec.loader.exec_module(frames)
spec=importlib.util.spec_from_file_location('slot6_registered_student',RUN/'teacher_student_autopilot_v14/train_student.py')
student=importlib.util.module_from_spec(spec);spec.loader.exec_module(student)
rows=json.loads((DISC/'source_exposure_audit.json').read_text())['source_rows']
eligible=sorted([r for r in rows if r['human_ordinal_alignment']=='COUNT_EQUAL_ONLY_NOT_SEMANTIC_PROOF'],key=lambda r:hashlib.sha256((SEED+'|'+r['source_group']).encode()).hexdigest())
train=[];cats=set()
for r in eligible:
    if r['prior_split']=='train' and r['category'] not in cats:
        train.append(r);cats.add(r['category'])
        if len(train)==6:break
valid=[r for r in eligible if r['prior_split']=='validation']
groups={'train':train,'process_dev':valid[:2],'locked_evaluation':valid[2:6]}
expected={'train':['kLxoNp-UchI','AwmHb44_ouw','HT5vyqe0Xaw','37rzWOQsNIw','WxtbjNsCQ8A','byxOvuiIJV0'],
    'process_dev':['-esJrBWj2d8','i3wAGJaaktw'],'locked_evaluation':['EYqVtI9YWJA','J0nA4VgnoCo','cjibtmSLxQ4','Yi4Ij2NM7U4']}
assert {k:[r['source_id'] for r in v] for k,v in groups.items()}==expected
OUT.mkdir(exist_ok=False);jobs=[];media=[]
for role,sources in groups.items():
    for r in sources:
        src=Path(r['media_path']);assert src.stat().st_size==r['media_bytes'] and sha(src)==r['media_sha256']
        m=json.loads((src.parent/'manifest.json').read_text());npz=src.parent/'native_pts.npz'
        assert sha(npz)==m['native_pts_sha256']
        with np.load(npz) as d:
            tb=F(*map(int,d['time_base']));points=[int(p)*tb for p in d['pts']]
        assert len(points)==m['native_frames'] and points[0]==int(m['first_pts'])*tb and points[-1]==int(m['last_pts'])*tb
        assert all(a<b for a,b in zip(points,points[1:]))
        origin=points[0];end=F(int(m['stream_metadata']['stream_duration_ticks']))*tb
        assert origin==0,'Do not silently reinterpret a nonzero-origin source'
        original=frames.window_schedule(dict(scope_start_sec=0.,scope_end_sec=float(end)), 'SLOT6_NONTEST_SOURCE',dict(branch=frames.BRANCH_NATIVE,duration=float(end)))
        # All chosen sources are >60s: existing balanced-two-window special branch is inactive.
        assert float(end)>60 and len(original)>=2
        ranked=sorted(range(len(original)),key=lambda ix:hashlib.sha256((SEED+'|window|'+r['source_group']+'|'+str(ix)).encode()).hexdigest())[:2]
        assert len(set(ranked))==2
        for ix in sorted(ranked):
            a,b=original[ix];w=student.window_from_pts(str(src),r['media_sha256'],[float(p) for p in points],a,b,r['source_id']+':SLOT6:'+str(ix),width=m['stream_metadata']['width'],height=m['stream_metadata']['height'])
            first,stop=bisect_left(points,F(str(a))),bisect_left(points,F(str(b)))
            assert w['planned_source_frame_ordinals']==student.floor_indices(first,stop)
            assert b-a<=30 and len(w['planned_source_frame_ordinals'])<=64
            w.update(source_total_frames=len(points),original_window_index=ix,planned_exact_pts=[str(points[i]) for i in w['planned_source_frame_ordinals']],domain_start_exact=str(F(str(a))),domain_end_exact=str(F(str(b))),eligible_exact_pts=[str(p) for p in points[first:stop]])
            jobs.append(dict(role=role,source_id=r['source_id'],source_group=r['source_group'],window=w,
                source_metadata=r,original_window_plan=original,native_pts_file_sha256=sha(npz),training_admitted=False))
        media.append(dict(source_id=r['source_id'],path=str(src),sha256=r['media_sha256'],bytes=r['media_bytes']))
assert len(jobs)==24 and sum(r['bytes'] for r in media)==196564489
save(OUT/'source_window_plan.json',dict(status='PASS_METADATA_RECONSTRUCTION_AND_ACTUAL_B_WINDOW_PLANNER_NOT_SUPERVISION',seed=SEED,
    sources=groups,jobs=jobs,media=media,media_bytes=sum(r['bytes'] for r in media),
    helper_sha256={str(p.relative_to(RUN)):sha(p) for p in [RUN/'next_round_v1/frame_contract.py',RUN/'next_round_v1/package_contract.py',RUN/'teacher_student_autopilot_v14/train_student.py']},
    pro_answer_sha256=sha(DISC/'pro-p01.md'),linux_presence_verified=False,transfer_authorized=False,
    old_four_window_tool_pilot_is_not_this_frozen_plan=True,closed_model_calls_this_protocol=0,new_optimizer_updates=0))
print(json.dumps(dict(status='PASS_FIXED_12_SOURCE_24_B_WINDOWS',media_bytes=196564489,jobs=[dict(source=x['source_id'],role=x['role'],original_index=x['window']['original_window_index'],domain=[x['window']['domain_start_exact'],x['window']['domain_end_exact']]) for x in jobs]),ensure_ascii=False,indent=2))
