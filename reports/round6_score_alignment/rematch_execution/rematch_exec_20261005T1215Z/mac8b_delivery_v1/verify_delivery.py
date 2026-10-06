"""Verify returned final bytes and independently validate on the Windows host."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
root=Path(sys.argv[1]).resolve()
code=Path(__file__).resolve().parent.parent/'baseline_a_pts_v1'
package=json.loads((root/'package.stage.json').read_text())
remote=json.loads((root/'independent_validation.json').read_text())
completion=json.loads((root.parent/'completion.json').read_text())
assert package['video_records']==remote['video_records']==completion['videos']==426
assert sha(root/'candidate_MAC_8B.zip')==package['zip_sha256']==remote['zip_sha256']==completion['candidate_sha256']
assert (root/'candidate_MAC_8B.zip').stat().st_size==completion['candidate_bytes']
assert sha(root/'predictions.jsonl')==package['predictions_sha256']==remote['predictions_sha256']
assert sha(root/'provenance.jsonl')==remote['provenance_sha256']
with zipfile.ZipFile(root/'candidate_MAC_8B.zip') as z:
    assert z.namelist()==['predictions.jsonl'] and z.testzip() is None
    assert z.read('predictions.jsonl')==(root/'predictions.jsonl').read_bytes()
subprocess.run([sys.executable,'-B',str(code/'vendor/independent_validate.py'),
    '--strict-loader-root',str(code/'vendor/frozen_strict_loader'),'--metadata',str(root/'metadata.json'),
    '--selected',str(root/'selected.jsonl'),'--predictions',str(root/'predictions.jsonl'),
    '--provenance',str(root/'provenance.jsonl'),'--zip',str(root/'candidate_MAC_8B.zip'),
    '--report',str(root/'local_independent_validation.json')],check=True)
report=json.loads((root/'local_independent_validation.json').read_text())
assert report['status']=='PASS_INDEPENDENT_STRICT_VALIDATION' and all(report['checks'].values())
print(json.dumps(dict(status='PASS_LOCAL_BYTES_CRC_STRICT_LOADER',videos=426,zip_sha256=sha(root/'candidate_MAC_8B.zip'))))
