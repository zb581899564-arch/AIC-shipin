import pathlib,hashlib,json,zipfile,subprocess,os
root=pathlib.Path('/home/inspur/aic_video_work/midnight_pair_applicability_20261015_v1')
archive=root/'pair_short_control_01.zip'
expected_bytes=201602
expected_sha='bea742f57d71892bb1e678298daf8fe3aa341077f8fd9e69f349b706de00f9bc'
assert root.resolve()==root and not root.is_symlink()
assert archive.stat().st_size==expected_bytes and hashlib.sha256(archive.read_bytes()).hexdigest()==expected_sha
assert sorted(p.name for p in root.iterdir())==['pair_short_control_01.zip']
with zipfile.ZipFile(archive) as z:
 assert z.testzip() is None
 manifest=json.loads(z.read('deployment_manifest.json'));assert set(z.namelist())==set(manifest)|{'deployment_manifest.json'}
 for n,d in manifest.items():
  p=pathlib.Path(n);assert not p.is_absolute() and '..' not in p.parts and (root/p).resolve().is_relative_to(root) and hashlib.sha256(z.read(n)).hexdigest()==d
 z.extractall(root)
for n,d in manifest.items():assert hashlib.sha256((root/n).read_bytes()).hexdigest()==d
with (root/'deployment_acceptance.json').open('x') as f:json.dump(dict(status='PASS_BYTES_SHA_CRC_MEMBERS_DEPLOYED',archive_sha256=expected_sha,bytes=expected_bytes,members=len(manifest)+1,explicit_remaining_recovery_07=True),f)
with (root/'metadata_freeze.log').open('x') as f:
 r=subprocess.run(['/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python','-B',str(root/'freeze_metadata.py')],env=dict(os.environ,CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1'),stdout=f,stderr=subprocess.STDOUT)
with (root/'metadata_freeze_terminal.json').open('x') as f:json.dump(dict(returncode=r.returncode),f)
if r.returncode:
 print(json.dumps(dict(status='METADATA_FREEZE_FAILED_NO_RETRY',returncode=r.returncode,error=(root/'metadata_freeze.log').read_text()[-2500:])))
 raise SystemExit(r.returncode)
p=root/'source_candidates.json';q=root/'new_selection.json'
print(json.dumps(dict(status='DEPLOYED_METADATA_FROZEN',archive_bytes=expected_bytes,archive_sha256=expected_sha,source_candidates_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),source_candidates_bytes=p.stat().st_size,new_selection_sha256=hashlib.sha256(q.read_bytes()).hexdigest(),supplemental_protocol_sha256=hashlib.sha256((root/'supplemental_protocol.json').read_bytes()).hexdigest())))
