from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
ROOT=Path(__file__).resolve().parent; PRIOR=ROOT.parent/'independent_highlight_pilot_v3'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
idx=read(PRIOR/'native_index.json'); rootfacts=read(PRIOR/'main_adjudication/observations.json')
assert rootfacts['actual_observations']==64
groups=[[28,29,30,31],[36,37,38,39],[44,45,46,47],[56,57,58,59],[60,61,62,63]]
subject=['DOG','DOG','DOG','PERSON','PERSON','PERSON','DOG','DOG','DOG','DOG','DOG','DOG','PERSON','NO_PERSON_OR_DOG','NO_PERSON_OR_DOG','DOG','DOG','DOG','DOG','DOG']
composition=['DOG_FACE_OUTDOOR']*3+['PERSON_CHEST']*3+['DOG_PARTLY_OCCLUDED']*4+['DOG_EXTREME_FACE']*2+['PERSON_PARTIAL_EDGE','WALL_CLOCK_NO_SUBJECT','STAIRS_NO_SUBJECT']+['DOG_ON_STAIRS']*3+['DOG_ON_GRASS']*2
assert len(subject)==len(composition)==20
allowed=['PERSON_CHEST','PERSON_PARTIAL_EDGE','DOG_HEAD_CHEST','DOG_FACE_OUTDOOR','DOG_PARTLY_OCCLUDED','DOG_EXTREME_FACE','WALL_CLOCK_NO_SUBJECT','STAIRS_NO_SUBJECT','DOG_ON_STAIRS','DOG_ON_GRASS','OTHER','UNKNOWN']
teacher_groups=[];oracle=[];k=0
for gno,nums in enumerate(groups):
    rows=[]
    for slot,n in enumerate(nums):
        f=idx['frames'][n];assert sha(Path(f['path']))==f['png_sha256']
        assert rootfacts['frame_observations'][n]['png_sha256']==f['png_sha256']
        rows.append(dict(slot=slot,**f)); o=rootfacts['frame_observations'][n]
        oracle.append(dict(group=gno,slot=slot,frame_id=f['frame_id'],source_ordinal=f['source_ordinal'],
          local_seconds_exact=f['local_seconds_exact'],png_sha256=f['png_sha256'],subject=subject[k],composition=composition[k],
          subtitle_visible=o['subtitle_visible'] is not None,subtitle_text=o['subtitle_visible'],visible_fact=o['visible_fact']))
        k+=1
    teacher_groups.append(dict(group=gno,frames=rows,output_path=str(ROOT/'attempt01'/f'group{gno:02d}.json')))
packet=dict(window_id=idx['window_id'],source_sha256=idx['source_sha256'],groups=teacher_groups,
 actual_student_input_frames=64,student_previews_in_previous_packet=8,this_test_student_images=0,
 subject_enum=['PERSON','DOG','NO_PERSON_OR_DOG','UNKNOWN'],composition_enum=allowed,
 model_supplied_frame_identity_forbidden=True,native_clip_not_read=True)
save(ROOT/'teacher_index.json',packet)
save(ROOT/'oracle_frozen.json',dict(reference_kind='MAIN_ACTUALLY_VIEWED_FINITE_IMAGE_FACTS_NOT_HUMAN_GOLD',
 prior_root_observations=dict(path=str(PRIOR/'main_adjudication/observations.json'),sha256=sha(PRIOR/'main_adjudication/observations.json')),items=oracle))
prior=read(PRIOR/'teacher_attempt01/proposal.json')
oldissues={n:prior['frame_observations'][n]['visible_fact'] for nums in groups for n in nums}
save(ROOT/'prior_errors_frozen.json',dict(old_proposal_sha256=sha(PRIOR/'teacher_attempt01/proposal.json'),selected_old_facts=oldissues,
 key_existing_errors=['F30 wrong subject','F36-F37 wrong subject','F44-F45 wrong composition','F57 wrong setting/subject','F58 dog appeared too early','F61 wrong setting']))
save(ROOT/'freeze.json',dict(utc=datetime.now(timezone.utc).isoformat(),hypothesis='FOUR_PNG_BARRIER_WITH_PROGRAM_IDENTITY_BINDING_NO_CLIP',
 files={n:sha(ROOT/n) for n in ('PROTOCOL.md','teacher_index.json','oracle_frozen.json','prior_errors_frozen.json')},
 range=groups,prior_cli_calls=22,max_total_calls=36,stage_calls_max=1,automatic_retry=False,
 existing_evidence_assessment='Old copied identities already correct, but corresponding semantic facts wrong. A pure mapping rewrite cannot establish semantic repair; one minimum-method model test is required.',
 cash_cost='UNKNOWN_NOT_ZERO',new_training=0,new_426=0,new_Pro=0))
(ROOT/'attempt01').mkdir(exist_ok=False)
print(json.dumps(dict(frozen_groups=5,frames=20,max_new_cli=1,total_after=23),ensure_ascii=False))
