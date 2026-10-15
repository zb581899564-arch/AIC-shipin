"""Only final submission archives and short receipts cross back to Windows."""
from pathlib import Path
import argparse,datetime as dt,hashlib,json,subprocess,zipfile

W=Path(__file__).resolve().parents[2];R=Path(__file__).resolve().parent
ROOT='/home/inspur/aic_video_work/midnight_five_verify40_46_20261015_v1'
BASELINE_SHA='86593725c6bad919dc0d342fe98ad65e489a13a6e492da5de3afd247a3226543'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canonical(values):
    values=[{k:v[k] for k in ('video_id','targetRatioWH','predictions')} for v in sorted(values,key=lambda v:v['video_id'])]
    return hashlib.sha256(json.dumps(values,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def run(arms):
    code=f'''from pathlib import Path
import json,hashlib
r=Path({ROOT!r});out=[]
for arm in {arms!r}:
 p=r/'packages'/('package_'+arm)/'completion.json'
 if p.exists():
  d=json.loads(p.read_text());assert d['arm']==arm and d['independent11strict'] is True and d['records']==426
  z=Path(d['zip']);assert z.resolve().is_relative_to(r/'packages') and z.stat().st_size==d['bytes'] and hashlib.sha256(z.read_bytes()).hexdigest()==d['SHA256']
  out.append(d)
print(json.dumps(dict(packages=out),separators=(',',':')))
'''
    query=subprocess.run(['ssh','-o','BatchMode=yes','-o','ConnectTimeout=12','aic-inspur-tailscale','python3','-'],input=code,text=True,capture_output=True,check=True)
    rows=json.loads(query.stdout)['packages'];actual=[]
    for row in rows:
        arm=row['arm'];risk=arm in ['ACTION','REACTION','INFORMATION']
        dest=W/'deliveries'/('MIDNIGHT_'+arm+('_RISK' if risk else '')+'_8B_20261015')
        receipt=dest/'windows_delivery_acceptance.json'
        if receipt.exists():
            previous=json.loads(receipt.read_text(encoding='utf8'));p=Path(previous['Windows_ZIP'])
            assert p.exists() and p.stat().st_size==row['bytes'] and sha(p)==row['SHA256']
            actual.append(dict(previous,already_successful_not_retransferred=True));continue
        dest.mkdir(exist_ok=False)
        partial=dest/(Path(row['zip']).name+'.transfer.partial')
        result=subprocess.run(['scp','-o','BatchMode=yes','-o','ConnectTimeout=12','aic-inspur-tailscale:'+row['zip'],str(partial)],capture_output=True,text=True)
        if result.returncode:
            (dest/'transfer_failure.json').write_text(json.dumps(dict(exit=result.returncode,stderr=result.stderr,expected=row,preserve_partial=True,automatic_retry=False),ensure_ascii=False,indent=2),encoding='utf8')
            raise RuntimeError('Final archive transfer failed; partial preserved, no automatic retry')
        assert partial.stat().st_size==row['bytes'] and sha(partial)==row['SHA256']
        with zipfile.ZipFile(partial) as z:
            assert z.namelist()==['predictions.jsonl'] and z.testzip() is None
            raw=z.read('predictions.jsonl');assert hashlib.sha256(raw).hexdigest()==row['member_SHA256']
            values=[json.loads(s) for s in raw.splitlines() if s.strip()]
        assert len(values)==426 and {v['video_id'] for v in values}==set(map(str,range(426))) and all(v['predictions'] for v in values)
        assert all(v['model_params_b']==8.78245912 for v in values)
        assert sum(len(v['predictions']) for v in values)==row['frame_count']
        assert canonical(values)==row['canonical_SHA256'] and row['protected_baseline_SHA256']==BASELINE_SHA
        final=dest/Path(row['zip']).name;partial.rename(final)
        accepted=dict(status='PASS_WINDOWS_FINAL_ZIP_LINUX_BYTES_SHA_CRC_MEMBER_SHA_426',arm=arm,Windows_ZIP=str(final),
            bytes=row['bytes'],SHA256=row['SHA256'],member_SHA256=row['member_SHA256'],canonical_SHA256=row['canonical_SHA256'],
            records=426,frame_count=row['frame_count'],added_frames=row['added_frames'],removed_frames=row['removed_frames'],
            independent11strict_Linux=True,Windows_CRC_member_and_counts=True,actual_parameters=8782459120,
            actual_new_model_calls=row['actual_new_model_calls'],logical_cases=row['logical_cases'],adopted_identical_input_aliases=row['adopted_identical_input_aliases'],
            quality_pass_claimed=row['quality_pass_claimed'],risk_effect_quality_screening=False if risk else None,
            original_baseline_archive_unchanged=True,official_score='UNKNOWN',automatically_submitted=False,UTC=dt.datetime.now(dt.timezone.utc).isoformat(),Linux_completion=row)
        receipt.write_text(json.dumps(accepted,ensure_ascii=False,indent=2),encoding='utf8')
        actual.append(accepted)
    stamp=dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    summary=dict(actual_new_final_packages=len(actual),requested_arms=arms,deliveries=actual)
    (R/('windows_delivery_'+stamp+'.json')).write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({k:v for k,v in summary.items() if k!='deliveries'}))
    for d in actual:print(json.dumps({k:d[k] for k in ['arm','Windows_ZIP','bytes','SHA256','frame_count','added_frames','removed_frames','quality_pass_claimed']},ensure_ascii=False))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--arms',nargs='+',required=True);a=p.parse_args();run(a.arms)
