"""Prepare first registered pilot only. No media decoding or old-label reads."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
HERE=Path(__file__).resolve().parent
ITER=HERE.parent

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
    with Path(p).open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)

def main():
    jobs=json.loads((ITER/'slot6_silver24_v1/observations/jobs.json').read_text())['jobs']
    folder=Path(jobs[0]);m=json.loads((folder/'manifest.json').read_text());sv=json.loads((folder/'student_views/receipt.json').read_text())
    if sha(ITER/'slot6_silver24_v1/source_window_plan.json')!='09ecb28971932bd3bf8ac275c30d0a6fd534345442f2d2ec3529fa3f8e1e4b22':raise ValueError('fixed24 changed')
    if m['source_id']!='kLxoNp-UchI' or m['role']!='train' or sv['patch_inverse_exact'] is not True:raise ValueError('first pilot or processor identity differs')
    if sv['manifest_sha256']!=sha(folder/'manifest.json') or len(sv['frames'])!=64 or len(m['frames'])!=64:raise ValueError('bound64 missing')
    common=dict(window_id=m['window_id'],source_id=m['source_id'],source_sha256=m['source_sha256'],
                role=m['role'],local_domain_exact=['0','30'],global_domain_exact=['30','60'],
                historical_exposure='PRIOR_MODEL_AND_EDITORIAL_PROCESS_EXPOSURE_NOT_BLIND_DATASET',
                task='在本30秒可见素材内，选择具有相对突出的独立回看或分享价值的短高光：显著主题展示、互动、关键动作/结果、情绪张力或画面表现力。必要准备和结果限于帮助理解已选突出内容。连续叙事、字幕可读、讲话、运动或静态都不自动成为KEEP/NO依据。不得猜音频或设选帧比例、非空配额。明确无额外可见贡献的段落可NO；具体未决语义/动作/边界若会改变选择则UNKNOWN。编辑偏好可以明确裁定，但不能声称唯一客观真值。',
                reference_kind='FINITE_OBSERVATION_SILVER_EDITING_ADVICE_NOT_GOLD',
                sample_policy='original registered floor64; no additional chosen easier frames')
    for name,frames in [('student_index.json',sv['frames']),('native_index.json',m['frames'])]:
        for row in frames:
            if sha(row['path'])!=row['png_sha256']:raise ValueError('PNG byte identity differs')
        save(HERE/name,dict(**common,frames=frames))
    teacher=dict(**common,clip_path=m['clip_path'],clip_sha256=m['clip_sha256'],clip_pts_offset_exact=m['clip_pts_offset_exact'],
                 full_native_frames_observed=False,original_frames=m['frames'],effective_frames=sv['frames'][::8],
                 student_processor_receipt=dict(path=str(folder/'student_views/receipt.json'),sha256=sha(folder/'student_views/receipt.json')))
    save(HERE/'teacher_packet.json',teacher)
    for d in ('blind_student','blind_native','teacher_attempt01','main_adjudication'): (HERE/d).mkdir(exist_ok=False)
    save(HERE/'preparation.json',dict(utc=datetime.now(timezone.utc).isoformat(),fixed24_plan_sha256=sha(ITER/'slot6_silver24_v1/source_window_plan.json'),
         window_id=m['window_id'],job_index=0,source_role='train',source_sha256=m['source_sha256'],
         packet_SHAs={n:sha(HERE/n) for n in ('student_index.json','native_index.json','teacher_packet.json')},
         all24_denominator=[dict(index=i,folder_name=Path(p).name,status='THIS_PILOT_ONLY' if i==0 else 'NOT_ADMITTED_TO_THIS_STAGE') for i,p in enumerate(jobs)],
         independent_initial_proposals_not_shared_before_sealing=True,new_decoder_calls=0,new_model_calls=0,new_optimizer_updates=0))

if __name__=='__main__':main()
