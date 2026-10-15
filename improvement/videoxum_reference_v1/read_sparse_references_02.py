"""Read newly frozen IDs from the retained author file; no annotation download or GPU."""
import base64
import hashlib
import json
import subprocess
from pathlib import Path

from deploy_media_batch_04 import ssh_script
from stage_common_04 import read, save, sha, utc

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT/'reports/sparse_context_iteration_20261013_v1'


def main():
    output = REPORT/'new_confirm_reference_pool_01.json'
    if output.exists():
        raise ValueError('New selected reference schemas already read; do not repeat')
    registration = read(REPORT/'new_confirm_source_registration_01.json')
    rows = registration['selection']+registration['ordered_engineering_reserves']
    script = '''import base64,hashlib,json,pathlib,socket
from decimal import Decimal
from fractions import Fraction as F
assert socket.gethostname()=='inspur-NP5570M5'
p=pathlib.Path('/home/inspur/aic_video_work/videoxum_reference_iteration_20261013_v1/metadata_02/val_videoxum.json')
raw=p.read_bytes();assert len(raw)==9575564 and hashlib.sha256(raw).hexdigest()=='2832f423ff5fd768a979665e30345a56f1723aacc1821986b5ec042bed30f556'
by_id={x['video_id']:x for x in json.loads(raw,parse_float=Decimal)}
refs=[]
for row in ROWS:
 original=by_id[row['video_id']];labels=[[] for _ in range(10)]
 for event in original['vsum']:
  assert len(event)==10
  for i,span in enumerate(event):
   assert len(span)==2 and 0<=F(span[0])<F(span[1])
   labels[i].append([str(span[0]),str(span[1])])
 onehot=original['vsum_onehot']
 assert len(onehot)==10 and all(len(x)==original['sampled_frames'] for x in onehot)
 assert all(v in (0,1) for x in onehot for v in x)
 refs.append(dict(row,author_duration_raw=str(original['duration']),annotator_intervals_exact_seconds=labels,original_onehot=onehot,author_sampled_frames=original['sampled_frames'],caption_text_exported=False))
data=json.dumps(refs,indent=2).encode()
print(json.dumps(dict(payload_b64=base64.b64encode(data).decode(),bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),sources=len(refs),annotation_sha256=hashlib.sha256(raw).hexdigest(),new_downloads=0,new_CPU_decodes=0,new_model_calls=0)))'''.replace('ROWS', repr(rows))
    try:
        response = ssh_script(script)
    except subprocess.CalledProcessError as error:
        save(REPORT/'reference_export_failure_02.json', dict(status='FAILED_REFERENCE_EXPORT02_PRESERVED', returncode=error.returncode, stderr=error.stderr.decode(errors='replace') if isinstance(error.stderr, bytes) else error.stderr))
        raise RuntimeError('Fresh reference export02 failed; stderr receipt saved') from None
    raw = base64.b64decode(response.pop('payload_b64'))
    if len(raw) != response['bytes'] or hashlib.sha256(raw).hexdigest() != response['sha256']:
        raise ValueError('Transferred fresh reference bytes differ from Linux export')
    references = json.loads(raw)
    if [x['video_id'] for x in references] != [x['video_id'] for x in rows] or len(references) != 24:
        raise ValueError('Frozen fresh source and reserve ordering changed')
    with output.open('xb') as stream:
        stream.write(raw)
    save(REPORT/'new_confirm_reference_schema_transfer_01.json', dict(status='PASS_FRESH24_ORIGINAL_REFERENCE_SCHEMA_BYTES_SHA_NOT_NATIVE_QUALITY',
         utc=utc(), **response, source_registration_sha256=sha(REPORT/'new_confirm_source_registration_01.json'),
         author_original_intervals_modified=False, onehot_stretched_padded_truncated=False,
         original1fps_is_native_GT=False, original_manual_end_gate_pending=True,
         new_confirm_source_ids_frozen=True, caption_text_exported=False, new_media_downloads=0))
    print(json.dumps(dict(status='PASS_FRESH24_RETAINED_AUTHOR_SCHEMAS_AND_LINUX_WINDOWS_BYTES_SHA',
        sources=24,bytes=len(raw),sha256=response['sha256'],new_annotation_downloads=0,new_model_calls=0)))


if __name__ == '__main__':
    main()
