$ErrorActionPreference='Stop'
$root='G:\ai\AIC视频\reports\annotation_iteration_20261011\contrast_boundary_v1'
$remote='/home/inspur/aic_video_work/annotation_iteration_20261011/contrast_boundary_v1'
$manifestPath=Join-Path $root 'fixed24_source_bundle_manifest_v1.json'
$manifest=Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
if ($manifest.zip.bytes -ne 294241337 -or $manifest.zip.sha256 -ne 'ccff5e1f48551b783db56e00f7110c0d6396ba50c967e990facafdc695c0bdee') { throw 'User-authorized source bundle differs.' }
if ((Get-FileHash -LiteralPath $manifest.zip.path -Algorithm SHA256).Hash.ToLower() -ne $manifest.zip.sha256) { throw 'Bundle SHA drift.' }
$hostName=& ssh -o BatchMode=yes -o StrictHostKeyChecking=yes aic-inspur-home hostname
if ($LASTEXITCODE -ne 0 -or "$hostName".Trim() -ne 'inspur-NP5570M5') { throw 'Wrong Linux host.' }
$prepare=@'
import pathlib,json,os
r=pathlib.Path('/home/inspur/aic_video_work/annotation_iteration_20261011/contrast_boundary_v1')
assert not r.exists() and not r.is_symlink()
assert pathlib.Path('/home/inspur/aic_video_work').resolve()==pathlib.Path('/home/inspur/aic_video_work')
r.mkdir(parents=True,exist_ok=False);(r/'deployment_sources_v1').mkdir()
st=os.statvfs(r)
print(json.dumps({'status':'PREPARED_EXCLUSIVE_SOURCE_TRANSFER_NOT_TRAINING','free_bytes':st.f_bavail*st.f_frsize}))
'@
$prepare | & ssh -o BatchMode=yes -o StrictHostKeyChecking=yes aic-inspur-home '/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python -B -'
if ($LASTEXITCODE -ne 0) { throw 'Exclusive remote target failed; do not retry or overwrite.' }
& scp -o BatchMode=yes -o StrictHostKeyChecking=yes -o ConnectTimeout=15 $manifest.zip.path $manifestPath "aic-inspur-home:$remote/deployment_sources_v1/"
if ($LASTEXITCODE -ne 0) { throw 'Direct source upload failed; preserve partial files, no retry/fallback.' }
$accept=@'
import pathlib,json,hashlib,zipfile,stat,os,datetime
r=pathlib.Path('/home/inspur/aic_video_work/annotation_iteration_20261011/contrast_boundary_v1');d=r/'deployment_sources_v1'
m=json.loads((d/'fixed24_source_bundle_manifest_v1.json').read_text(encoding='utf-8-sig'));p=d/'fixed24_native_sources_v1.zip'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for block in iter(lambda:f.read(8<<20),b''):h.update(block)
 return h.hexdigest()
assert p.stat().st_size==294241337==m['zip']['bytes'] and sha(p)=='ccff5e1f48551b783db56e00f7110c0d6396ba50c967e990facafdc695c0bdee'==m['zip']['sha256']
out=r/'native_sources';assert not out.exists()
st=os.statvfs(r);assert st.f_bavail*st.f_frsize>sum(f['bytes'] for f in m['files'])+sum(f['bytes'] for f in m['files'] if f['member'].endswith('.npz'))
out.mkdir();accepted=[]
with zipfile.ZipFile(p) as z:
 infos=z.infolist();expected={f['member']:f for f in m['files']}
 assert len(infos)==len(expected)==48 and set(z.namelist())==set(expected)
 for i in infos:
  assert i.filename==pathlib.PurePosixPath(i.filename).name and '\\' not in i.filename and not i.is_dir()
  assert not stat.S_ISLNK(i.external_attr>>16) and i.file_size==expected[i.filename]['bytes']
 for i in infos:
  q=out/i.filename
  assert q.resolve().parent==out.resolve()
  with z.open(i) as source,q.open('xb') as dest:
   for block in iter(lambda:source.read(8<<20),b''):dest.write(block)
  assert q.stat().st_size==expected[i.filename]['bytes'] and sha(q)==expected[i.filename]['sha256']
  accepted.append({'path':str(q),'bytes':q.stat().st_size,'sha256':sha(q)})
receipt={'status':'PASS_FIXED24_DIRECT_UPLOAD_EXTRACTION_CRC_ALL48_MEMBER_SHA_NOT_TRAINING','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'route':'Windows -> aic-inspur-home direct SSH; no Mac jump','zip_bytes':p.stat().st_size,'zip_sha256':sha(p),'source_videos':24,'files':accepted,'new_model_calls':0,'new_optimizer_updates':0,'user_authorized':True}
with (d/'upload_acceptance.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,ensure_ascii=False,indent=2)
print(json.dumps({k:v for k,v in receipt.items() if k!='files'}))
'@
$accept | & ssh -o BatchMode=yes -o StrictHostKeyChecking=yes aic-inspur-home '/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python -B -'
if ($LASTEXITCODE -ne 0) { throw 'Uploaded source acceptance failed; no automatic extraction retry.' }
& scp -o BatchMode=yes -o StrictHostKeyChecking=yes "aic-inspur-home:$remote/deployment_sources_v1/upload_acceptance.json" (Join-Path $root 'source_upload_acceptance_v1.json')
if ($LASTEXITCODE -ne 0) { throw 'Receipt download failed; accepted remote files preserved.' }
