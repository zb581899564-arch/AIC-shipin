"""Independent real-short-window recovery control; no repeated old members."""
import ast
import hashlib
import json
from pathlib import Path
import zipfile

WORK = Path(__file__).resolve().parents[2]
REPORT = Path(__file__).resolve().parent
REMOTE = '/home/inspur/aic_video_work/twenty_hour_five_20261014_v1'
OUT = REPORT/'production_deployment_02'

def digest(data):
    return hashlib.sha256(data).hexdigest()

def main():
    OUT.mkdir(exist_ok=False)
    entries = {}
    for name in ('temporal_production_inputs_v5', 'temporal_production_runtime_v5',
                 'temporal_production_control_v4', 'temporal_production_bootstrap_v2'):
        for file in sorted((WORK/'improvement'/name).glob('*.py')):
            ast.parse(file.read_text(encoding='utf-8-sig'))
            entries[name+'/code/'+file.name] = file
    entries['temporal_production_bootstrap_v2/refs/reader_native_scope_authorization_03.json'] = REPORT/'reader_native_scope_authorization_03.json'
    entries['temporal_production_bootstrap_v2/bootstrap_config_pending_code_sha_02.json'] = REPORT/'runtime/production_control_04/bootstrap_config_root_final_pending_sha_02.json'
    manifest = {'schema':'SMALL_CODE_CONTROL_DEPLOYMENT_V1', 'remote_root':REMOTE,
                'source_media_or_model_included':False, 'actual_execution_authorized_by_archive':False,
                'old_successful_leaf_files_retransmitted':0, 'files':{}}
    archive = OUT/'production_code_control_02.zip'
    with zipfile.ZipFile(archive, 'x', zipfile.ZIP_DEFLATED) as z:
        for name, file in entries.items():
            data = file.read_bytes()
            manifest['files'][name] = {'bytes':len(data), 'sha256':digest(data)}
            z.writestr(name, data)
        z.writestr('deployment_manifest.json', json.dumps(manifest, indent=2).encode())
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert set(z.namelist()) == set(entries)|{'deployment_manifest.json'}
        assert all(digest(z.read(n)) == row['sha256'] for n,row in manifest['files'].items())
    (OUT/'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf8')
    receipt = {'zip':str(archive), 'bytes':archive.stat().st_size,
               'sha256':digest(archive.read_bytes()), 'members':len(manifest['files'])}
    (OUT/'sender_receipt.json').write_text(json.dumps(receipt, indent=2), encoding='utf8')
    print(json.dumps(receipt))

if __name__ == '__main__':
    main()
