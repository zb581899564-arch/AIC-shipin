"""Run only after a direct human fourth-risk approval has actually been received."""
from pathlib import Path
import ast
import datetime as dt
import hashlib
import json
import subprocess
import zipfile

R = Path(__file__).resolve().parent
W = R.parents[1]
ROOT = '/home/inspur/aic_video_work/midnight_five_verify40_46_20261015_v1'
EXPECTED_SHA = '207cd33bc2b13c64005dde49d0e6ee2775a44c61a4e1afd10bb24ffc565de26e'
BASELINE_SHA = '86593725c6bad919dc0d342fe98ad65e489a13a6e492da5de3afd247a3226543'


def canonical(values):
    body = [{key: value[key] for key in ('video_id', 'targetRatioWH', 'predictions')}
            for value in sorted(values, key=lambda value: value['video_id'])]
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def main():
    # This file does not create approval.  Missing/pending/presubmitted choices
    # stop before any network operation or publication.
    auth_path = R / 'user_fourth_risk_authorization_31.json'
    auth = json.loads(auth_path.read_text(encoding='utf8'))
    assert auth['human_answer_received'] is True and auth['approved_risk_count'] == 4
    assert auth['maximum_total_new_packages'] == 5 and auth['proposal_zip_SHA256'] == EXPECTED_SHA
    assert auth['human_raw_reply'] and auth['source'] == 'DIRECT_CURRENT_CHAT_HUMAN_REPLY'
    body = json.dumps(auth, ensure_ascii=False)
    code = f'''from pathlib import Path
import datetime as dt,hashlib,json,os,shutil,socket,zipfile
r=Path({ROOT!r});auth=json.loads({body!r});p=r/'semantic_union_review_27/review_receipt.json'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
ref=lambda p:dict(path=str(p),sha256=sha(p))
read=lambda p:json.loads(p.read_text())
assert socket.gethostname()=='inspur-NP5570M5'
assert auth['human_answer_received'] is True and auth['approved_risk_count']==4 and auth['maximum_total_new_packages']==5
assert auth['proposal_zip_SHA256']=={EXPECTED_SHA!r} and auth['source']=='DIRECT_CURRENT_CHAT_HUMAN_REPLY'
preview=read(p);source=Path(preview['zip'])
assert preview['status']=='PASS_ENGINEERING_PREVIEW_ONLY_PUBLICATION_NOT_AUTHORIZED' and preview['publication_authorized'] is False
assert preview['independent11strict'] is True and preview['quality_pass_claimed'] is False
assert preview['original4unchanged'] is True and preview['kept_baseline_boxes_exact'] is True
assert preview['frame_count']==122186 and preview['added_native_frames_vs_baseline']==184 and preview['removed_native_frames_vs_baseline']==0
assert source.stat().st_size==380660 and sha(source)=={EXPECTED_SHA!r}
original_ref=preview['original_package_inputs_ref'];assert sha(Path(original_ref['path']))==original_ref['sha256']
baseline_ref=read(Path(original_ref['path']))['protected_baseline_zip_ref']
assert sha(Path(baseline_ref['path']))==baseline_ref['sha256']=={BASELINE_SHA!r}
assert sha(r/'quality_admission.json')=='5b15615bd5000adcbe55b87908d0a1e5d0babd7d973ccfdc3ff9ff76a7660e38'
actual={{q.parent.name for q in (r/'packages').glob('package_*/completion.json')}}
assert actual=={{'package_ACTION','package_REACTION','package_INFORMATION','package_ORDINARY'}}
for arm,reference in preview['current_four_package_refs'].items():
 path=Path(reference['path']);assert sha(path)==reference['sha256'];v=read(path);assert sha(Path(v['zip']))==v['SHA256']
report=preview['independent_validation_ref'];assert sha(Path(report['path']))==report['sha256']
with zipfile.ZipFile(source) as z:
 assert z.namelist()==['predictions.jsonl'] and z.testzip() is None
 assert hashlib.sha256(z.read('predictions.jsonl')).hexdigest()==preview['member_SHA256']
auth['actual_preview_receipt_ref']=ref(p)
auth_path=r/'user_fourth_risk_authorization_31.json'
with auth_path.open('x') as f:json.dump(auth,f,ensure_ascii=False,indent=2)
out=r/'packages/package_SEMANTIC_UNION';out.mkdir(exist_ok=False)
target=out/source.name;shutil.copyfile(source,target);assert sha(target)=={EXPECTED_SHA!r}
completion=dict(status='AUTHORIZED_FOURTH_RISK_FINAL_ZIP_REUSES_COMPLETE_PREVIEW_NO_NEW_QA_OR_MODEL',
 arm='SEMANTIC_UNION',zip=str(target),bytes=target.stat().st_size,SHA256=sha(target),member_SHA256=preview['member_SHA256'],
 canonical_SHA256=preview['canonical_SHA256'],records=426,frame_count=122186,added_frames=184,removed_frames=0,
 independent11strict=True,independent_validation_ref=report,actual_parameters=8782459120,
 protected_baseline_SHA256={BASELINE_SHA!r},retained_original_boxes_exact=True,original_baseline_all_frames_kept=True,
 quality_pass_claimed=False,risk_effect_quality_screening=False,authorized_risk_count=4,maximum_total_new_packages=5,
 direct_human_authorization_ref=ref(auth_path),complete_preview_ref=ref(p),preview_reused_not_repacked=True,
 production_completion_ref=preview['production_completion_ref'],production_evidence_counts=preview['production_evidence_counts'],
 actual_new_model_calls_in_release=0,new_processor_calls=0,new_media_decodes=0,first_QA_repeated=False,
 old_scientific_failures_changed=False,official_score='UNKNOWN',website_submitted=False,
 UTC=dt.datetime.now(dt.timezone.utc).isoformat())
with (out/'completion.json').open('x') as f:json.dump(completion,f,indent=2)
print(json.dumps(completion))
'''
    ast.parse(code)
    result = subprocess.run(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=12',
        'aic-inspur-tailscale', 'python3', '-'], input=code, text=True, capture_output=True)
    with (R / 'union_authorized_release_31_result.json').open('x', encoding='utf8') as stream:
        json.dump(dict(exit=result.returncode, stdout=result.stdout, stderr=result.stderr[-3000:]), stream, ensure_ascii=False, indent=2)
    result.check_returncode()
    receipt = json.loads(result.stdout)
    dest = W / 'deliveries/MIDNIGHT_SEMANTIC_UNION_RISK_8B_20261015'
    dest.mkdir(exist_ok=False)
    partial = dest / (Path(receipt['zip']).name + '.transfer.partial')
    transfer = subprocess.run(['scp', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=12',
        'aic-inspur-tailscale:' + receipt['zip'], str(partial)], capture_output=True, text=True)
    if transfer.returncode:
        (dest / 'transfer_failure.json').write_text(json.dumps(dict(exit=transfer.returncode,
            stderr=transfer.stderr,expected=receipt,preserve_partial=True,automatic_retry=False)),encoding='utf8')
        raise RuntimeError('Authorized union transfer failed; preserve partial and adopt completed Linux release')
    assert partial.stat().st_size == receipt['bytes'] == 380660
    assert hashlib.sha256(partial.read_bytes()).hexdigest() == receipt['SHA256'] == EXPECTED_SHA
    with zipfile.ZipFile(partial) as z:
        assert z.namelist() == ['predictions.jsonl'] and z.testzip() is None
        raw = z.read('predictions.jsonl')
        assert hashlib.sha256(raw).hexdigest() == receipt['member_SHA256']
        values = [json.loads(line) for line in raw.splitlines() if line.strip()]
    assert len(values) == 426 and {v['video_id'] for v in values} == set(map(str, range(426)))
    assert all(v['predictions'] and v['model_params_b'] == 8.78245912 for v in values)
    assert sum(len(v['predictions']) for v in values) == 122186
    assert canonical(values) == receipt['canonical_SHA256']
    final = dest / Path(receipt['zip']).name
    partial.rename(final)
    accepted = dict(status='PASS_AUTHORIZED_FOURTH_RISK_WINDOWS_LINUX_SHA_CRC_MEMBER_426',
        Windows_ZIP=str(final), Linux_completion=receipt, bytes=380660, SHA256=EXPECTED_SHA,
        frame_count=122186, added_frames=184, removed_frames=0, quality_pass_claimed=False,
        risk_effect_screening=False, original_baseline_all_frames_boxes_kept=True,
        automatically_submitted=False, UTC=dt.datetime.now(dt.timezone.utc).isoformat())
    (dest / 'windows_delivery_acceptance.json').write_text(json.dumps(accepted, ensure_ascii=False, indent=2), encoding='utf8')
    print(json.dumps(accepted, ensure_ascii=False))


if __name__ == '__main__':
    main()
