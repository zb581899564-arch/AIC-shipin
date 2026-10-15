"""Freeze metadata-only source roles and native quarter windows before viewing."""
from pathlib import Path
from fractions import Fraction as F
from datetime import datetime, timezone
import hashlib,json,zipfile
import numpy as np

ROOT=Path(__file__).resolve().parent
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for block in iter(lambda:f.read(8<<20),b''):h.update(block)
 return h.hexdigest()
def save(p,value):
 with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')

def main():
 audit_path=ROOT/'source_audit/local_tvsum_source_audit_v1.json';audit=read(audit_path)
 source_sort=lambda x:(x['source_id'],x['media_sha256'])
 train=sorted([s for s in audit['sources'] if s.get('role_proposal')=='TRAIN_ROLE_PROPOSAL'],key=source_sort)[:16]
 dev=sorted([s for s in audit['sources'] if s.get('role_proposal')=='PROCESS_DEV_ROLE_PROPOSAL'],key=source_sort)
 locked=sorted([s for s in audit['sources'] if s.get('role_proposal')=='LOCKED_ROLE_PROPOSAL_OLD_VALIDATION'],key=source_sort)
 assert len(train)==16 and len(dev)==len(locked)==4,[(s['source_id'],s.get('role_proposal')) for s in audit['sources']]
 sources={'train':train,'process_dev':dev,'locked_evaluation':locked};jobs=[]
 for role,rows in sources.items():
  for s in rows:
   assert sha(s['media_path'])==s['media_sha256'] and sha(s['native_pts_path'])==s['native_pts_sha256']
   assert not any(s['current_recipe_overlap'][k] for k in ['B602_youtube_id','B602_exact_media_sha','R7_dev_youtube_id','R7_confirm_youtube_id','silver12_source_group','rematch_available425_exact_media_sha'])
   if role=='train':assert s['historical_project_exposure']['older_source_split']=='train'
   src=read(Path(s['media_path']).parent/'manifest.json');clock=np.load(s['native_pts_path'])
   tb=F(int(clock['time_base'][0]),int(clock['time_base'][1]));points=[int(x)*tb for x in clock['pts']]
   assert len(points)==s['native_frames'] and all(a<b for a,b in zip(points,points[1:]))
   start,span=points[0],points[-1]-points[0]
   for k in range(4):
    b=start+span*(k+1)/4;a=max(start+span*k/4,b-F(30))
    eligible=[i for i,p in enumerate(points) if a<=p<b];assert len(eligible)>=64
    ids=[eligible[(i*(len(eligible)-1))//63] for i in range(64)]
    assert ids==sorted(set(ids))
    w={'width':src['stream_metadata']['width'],'height':src['stream_metadata']['height'],
       'source_path':s['media_path'],'source_sha256':s['media_sha256'],'window_id':s['source_id']+':CONTRASTQ:'+str(k),
       'window_pts_start_sec':float(a),'window_pts_end_exclusive_sec':float(b),'window_duration_sec':float(b-a),
       'planned_source_frame_ordinals':ids,'planned_actual_pts_sec':[float(points[i]) for i in ids],
       'planned_exact_pts':[str(points[i]) for i in ids],'eligible_exact_pts':[str(points[i]) for i in eligible],
       'eligible_source_frame_count':len(eligible),'source_total_frames':len(points),'original_window_index':k,
       'domain_start_exact':str(a),'domain_end_exact':str(b)}
    jobs.append({'index':len(jobs),'role':role,'source_id':s['source_id'],'source_group':s['source_group'],
                 'category':s['category'],'coverage_class':'PENDING_SEMANTIC','window':w})
 plan={'schema':'CONTRAST_BOUNDARY_FIXED_SOURCE_PLAN_V1','status':'PASS_METADATA_ONLY_ROLES_AND_QUARTER_DOMAINS_FROZEN_BEFORE_NEW_MEDIA_REVIEW',
       'utc':datetime.now(timezone.utc).isoformat(),'source_audit':{'path':str(audit_path),'sha256':sha(audit_path)},
       'selection_rule':'case-sensitive source_id and media SHA; first16 of audited20 train; audited4 process-dev; 4 remaining old validation locked. No semantic or model prediction selection.',
       'window_rule':'Each source native first-to-last PTS domain is quartered exactly; final min(30s,quarter span) of each quarter; last frame excluded by half-open endpoint. No duration interpolation or rounding.',
       'sources':sources,'jobs':jobs,'historical_project_exposure':True,'global_unseen':False,'new_teacher_calls':0,'new_optimizer_updates':0}
 assert len(jobs)==96 and len({j['window']['window_id'] for j in jobs})==96
 save(ROOT/'source_window_plan_v1.json',plan)
 auth={'status':'USER_AUTHORIZED_NEW_CONTRAST_BOUNDARY_DATA_AND_SFT_EXPERIMENT_OLD_STOP_PRESERVED',
       'user_quote':'那你继续补充新的训练数据，把普通片段和高光边界标注做好，再微调验证，一直做到能打包出质量合格的新包，别拿旧37.66包充数。',
       'utc':datetime.now(timezone.utc).isoformat(),'old_failed_recipe_restarted':False,'new_source_plan_sha256':sha(ROOT/'source_window_plan_v1.json'),
       'initial_model':'ORIGINAL_B_8B_ONLY','old37_66_delivery_allowed_as_new_output':False,
       'teacher':'gemini-3.8-flash-high via existing agy CLI, isolated fresh conversations, finite native sample contact sheets',
       'teacher_new_call_budget':96,'teacher_per_call_seconds':1200,'pilot_calls':2,
       'no_automatic_retry_failed_media':True,'teacher_cash':'UNKNOWN_NOT_ZERO','official_upload':False,
       'new_large_source_transfer':'PENDING_EXACT_BYTES_USER_PERMISSION_NOT_COVERED_BY_OLD12_SOURCE_APPROVAL'}
 save(ROOT/'user_authorization_v1.json',auth)
 bundle=ROOT/'fixed24_native_sources_v1.zip'
 files=[]
 with zipfile.ZipFile(bundle,'x',compression=zipfile.ZIP_STORED) as z:
  for role,rows in sources.items():
   for s in rows:
    for p,name in [(Path(s['media_path']),s['source_id']+'.mp4'),(Path(s['native_pts_path']),s['source_id']+'.native_pts.npz')]:
     z.write(p,name);files.append({'member':name,'bytes':p.stat().st_size,'sha256':sha(p),'original_path':str(p)})
 with zipfile.ZipFile(bundle) as z:
  assert z.testzip() is None
  for f in files:assert hashlib.sha256(z.read(f['member'])).hexdigest()==f['sha256']
 save(ROOT/'fixed24_source_bundle_manifest_v1.json',{'status':'PASS_LOCAL_FIXED24_SOURCE_BUNDLE_CRC_ALL_MEMBER_SHA_NOT_TRANSFERRED',
  'source_plan_sha256':sha(ROOT/'source_window_plan_v1.json'),'zip':{'path':str(bundle),'bytes':bundle.stat().st_size,'sha256':sha(bundle)},
  'files':files,'route':'Windows -> online macmini SSH jump -> Linux new independent native_sources directory',
  'remote_root':'/home/inspur/aic_video_work/annotation_iteration_20261011/contrast_boundary_v1','user_transfer_permission':False})
 print(json.dumps({'plan_windows':len(jobs),'train_windows':64,'dev_windows':16,'locked_windows':16,'source_files':24,'zip_bytes':bundle.stat().st_size,'zip_sha256':sha(bundle),'transfer_pending':True}))

if __name__=='__main__':main()
