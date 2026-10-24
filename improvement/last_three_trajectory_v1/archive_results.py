"""Bind observed Edge scores and the private screenshot digest back to Linux."""
import base64
import hashlib
import json
from pathlib import Path
import subprocess


def main():
    repo=Path(__file__).resolve().parents[2]
    workspace=repo.parents[1]
    report=workspace/'reports/last_three_trajectory_20261024_v1'
    rows=json.loads((report/'official_results.json').read_text())
    delivery=json.loads((report/'windows_delivery.json').read_text())
    if len(rows)!=3 or any(r['status']!='DONE' for r in rows):
        raise ValueError('Actual three official DONE rows required')
    by_id={r['candidate_id']:r for r in delivery['deliveries']}
    for row in rows:
        if row['zip_sha256']!=by_id[row['candidate_id']]['zip_sha256']:
            raise ValueError('Official name/score bound to unexpected final ZIP')
    screenshot=report/'official_three_scores.png'
    receipt=dict(schema='THREE_EDGE_OBSERVED_OFFICIAL_RESULTS_20261024_V1',rows=rows,
        source='User-authorized Edge actual score table; no guessed evaluator or local quality score',
        screenshot_windows_path=str(screenshot),screenshot_bytes=screenshot.stat().st_size,
        screenshot_sha256=hashlib.sha256(screenshot.read_bytes()).hexdigest(),
        new_observed_best=40.60,old_4048_4047_unchanged=True,registered_order_not_retuned=True)
    raw=json.dumps(receipt,indent=2).encode();digest=hashlib.sha256(raw).hexdigest()
    remote='''import base64,hashlib,json,pathlib
r=pathlib.Path('/home/inspur/aic_video_work/last_three_trajectory_20261024_v1')
b=base64.b64decode(DATA);assert hashlib.sha256(b).hexdigest()==DIGEST
value=json.loads(b)
for row in value['rows']:
 policy=row['candidate_id'].removeprefix('g_risk_')
 delivery=json.loads((r/policy/'package/delivery.json').read_text())
 assert delivery['zip_sha256']==row['zip_sha256']
path=r/'website_score_feedback.json'
assert not path.exists(),'Official receipt exists: inspect and adopt, never overwrite'
path.write_bytes(b)
best=next(row for row in value['rows'] if row['candidate_id']=='g_risk_median3')
assert best['score']==40.60
original=json.loads((r/'median3/package/delivery.json').read_text())
protected=dict(observed_score=40.60,official_name=best['title'],official_time=best['time'],zip_path=original['zip_path'],zip_bytes=original['zip_bytes'],zip_sha256=original['zip_sha256'],full_dependency_root=str(r),inherits_complete_protected_4048_pipeline=True,original_4048_4047_dependencies_protected=True,website_feedback_sha256=DIGEST)
(r/'protected_best_40_60.json').write_text(json.dumps(protected,indent=2))
print(json.dumps(dict(status='THREE_OFFICIAL_DONE_SCORES_BOUND_BEST40_60_PROTECTED',bytes=len(b),sha256=DIGEST)))
'''
    remote=remote.replace('DATA',repr(base64.b64encode(raw).decode())).replace('DIGEST',repr(digest))
    completed=subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=12',
        'aic-inspur-home','python3','-'],input=remote,text=True,capture_output=True,timeout=30)
    if completed.returncode:
        raise RuntimeError(completed.stderr)
    (report/'linux_score_archive_receipt.json').write_text(completed.stdout,encoding='utf-8')
    print(completed.stdout)


if __name__=='__main__':
    main()
