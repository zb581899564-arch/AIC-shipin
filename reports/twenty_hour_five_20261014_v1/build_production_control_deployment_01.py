"""Small code/control deployment only; no data, model or source execution."""
import ast
import hashlib
import json
from pathlib import Path
import zipfile

WORK = Path(__file__).resolve().parents[2]
REPORT = Path(__file__).resolve().parent
REMOTE = '/home/inspur/aic_video_work/twenty_hour_five_20261014_v1'
OUT = REPORT/'production_deployment_01'

def digest(data):
    return hashlib.sha256(data).hexdigest()

def main():
    OUT.mkdir(exist_ok=False)
    entries = {}
    for local, remote in (
        ('temporal_production_inputs_v4', 'temporal_production_inputs_v4'),
        ('temporal_production_runtime_v4', 'temporal_production_runtime_v4'),
        ('temporal_production_control_v3', 'temporal_production_control_v3'),
        ('temporal_production_bootstrap_v1', 'temporal_production_bootstrap_v1'),
        ('production_stream_cache_v2', 'production_stream_cache_v2'),
        ('temporal_family_native_v3', 'temporal_family_native_package_v3'),
    ):
        for file in sorted((WORK/'improvement'/local).glob('*.py')):
            ast.parse(file.read_text(encoding='utf-8-sig'))
            entries[remote+'/code/'+file.name] = file
    refs = {
        'official_rules_01.json': REPORT/'critic/official_rules_01.json',
        'selected_uniform_risk_role_01.json': REPORT/'selected_uniform_risk_role_01.json',
        'reader_native_scope_authorization_02.json': REPORT/'reader_native_scope_authorization_02.json',
        'representative_storage_ratio_nonfit_forecast_01.json': REPORT/'representative_storage_ratio_nonfit_forecast_01.json',
        'prospective_source_storage_estimator_template_01.json': REPORT/'prospective_source_storage_estimator_template_01.json',
        'frozen_GPU_budget_template_01.json': REPORT/'runtime/production_control_03/frozen_GPU_budget_template_01.json',
    }
    for name, file in refs.items():
        entries['temporal_production_bootstrap_v1/refs/'+name] = file
    entries['temporal_production_bootstrap_v1/bootstrap_config_pending_code_sha_01.json'] = REPORT/'runtime/production_control_03/bootstrap_config_root_final_pending_sha_01.json'
    entries['temporal_family_native_package_v3/protocol.json'] = REPORT/'native_family_risk_protocol_01.json'
    entries['temporal_family_native_package_v3/authorization.json'] = REPORT/'USER_AUTHORIZATION.json'
    manifest = {'schema':'SMALL_CODE_CONTROL_DEPLOYMENT_V1', 'remote_root':REMOTE,
                'source_media_or_model_included':False, 'actual_execution_authorized_by_archive':False,
                'files':{}}
    archive = OUT/'production_code_control_01.zip'
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
