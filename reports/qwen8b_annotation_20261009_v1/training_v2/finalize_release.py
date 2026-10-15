"""Build and independently read back a private portable selected training release."""
import datetime
import hashlib
import json
import shutil
import zipfile
from pathlib import Path

from verify_bundle import verify

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def main():
    assert not (HERE / 'release_completion.json').exists()
    crop = json.loads((HERE / 'preflight_actual_crop/preflight.json').read_text(encoding='utf-8'))
    temporal = json.loads((HERE / 'preflight_actual_temporal_fixed/preflight.json').read_text(encoding='utf-8'))
    audit = json.loads((HERE / 'selected_data_audit.json').read_text(encoding='utf-8'))
    runtime = json.loads((HERE / 'runtime_contract_checks.json').read_text(encoding='utf-8'))
    for receipt in (crop, temporal):
        assert receipt['status'].startswith('PASS_') and not receipt['model_weights_loaded'] and not receipt['optimizer_started']
    assert crop['stats']['train']['rows'] == 181 and crop['stats']['validation']['rows'] == 148
    assert temporal['stats']['train']['rows'] == 314 and temporal['stats']['validation']['rows'] == 89
    assert audit['temporal_sources'] == 48 and audit['fixed_grid_frames'] == 6047
    assert audit['source_split_overlap'] == 0 and audit['label_informed_input_sampling'] is False
    assert runtime['status'].startswith('PASS_') and not runtime['CUDA_initialized']
    dataset_names = ['crop_balanced_train', 'crop_full_validation', 'temporal_fixed_train', 'temporal_fixed_validation']
    paths = set()
    for name in dataset_names:
        data_path = HERE / 'data' / (name + '.jsonl')
        paths.add(data_path)
        for line in data_path.read_text(encoding='utf-8').splitlines():
            row = json.loads(line)
            for p in row['images']:
                image = (ROOT / p).resolve(strict=True)
                assert image.is_relative_to(ROOT)
                paths.add(image)
    for name in ['train_lora.py', 'sft_contract.py', 'predict_rows.py', 'evaluate_predictions.py', 'verify_bundle.py',
                 'README.md', 'fixed_grid_samples.jsonl', 'fixed_grid_preparation.json',
                 'selected_data_audit.json', 'runtime_contract_checks.json', 'correlation_contract.json',
                 'linux_runtime.json', 'crop_balanced_selection.json', 'gemini_boundary_dispositions.jsonl']:
        paths.add(HERE / name)
    for name in ['configs/crop.json', 'configs/temporal_fixed.json',
                 'preflight_actual_crop/preflight.json', 'preflight_actual_temporal_fixed/preflight.json']:
        paths.add(HERE / name)
    paths.update((HERE / 'processor_snapshot').glob('*'))
    paths = sorted(paths, key=lambda p: p.relative_to(ROOT).as_posix())
    total = sum(p.stat().st_size for p in paths)
    if shutil.disk_usage(HERE).free <= total + len(paths)*512:
        raise ValueError('Current local capacity does not cover archive estimate')
    files = {p.relative_to(ROOT).as_posix(): {'bytes': p.stat().st_size, 'sha256': sha(p)} for p in paths}
    manifest = {'status': 'SELECTED_LOCAL_TRAINING_RELEASE', 'files': files,
                'tasks': {'crop': {'train': 181, 'validation': 148}, 'temporal': {'train': 314, 'validation': 89}},
                'temporal_sources': 48, 'temporal_frames': 6047,
                'semantic_event_boundaries_verified': False, 'gemini_event_boundaries_used': 0,
                'selected_configs': ['training_v2/configs/crop.json', 'training_v2/configs/temporal_fixed.json'],
                'training_started': False, 'weights_included': False, 'full_videos_included': False}
    manifest_path = HERE / 'selected_manifest.json'
    assert not manifest_path.exists()
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    verification = verify(ROOT)
    paths.append(manifest_path)
    archive = HERE / 'QWEN8B_TRAINING_PREP_V2_20261009.zip'
    assert not archive.exists()
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=3) as z:
        for i, p in enumerate(paths):
            z.write(p, p.relative_to(ROOT).as_posix())
            if i % 1000 == 0:
                print(json.dumps({'stage': 'BUILD_PRIVATE_ARCHIVE', 'done': i+1, 'expected': len(paths)}), flush=True)
    expected_names = {p.relative_to(ROOT).as_posix() for p in paths}
    with zipfile.ZipFile(archive) as z:
        assert len(z.namelist()) == len(expected_names) and set(z.namelist()) == expected_names
        assert all(not n.startswith('/') and '..' not in Path(n).parts for n in z.namelist())
        for name, expected in files.items():
            raw = z.read(name)  # Read through EOF verifies each CRC as well as SHA below.
            assert len(raw) == expected['bytes'] and hashlib.sha256(raw).hexdigest() == expected['sha256']
        raw = z.read(manifest_path.relative_to(ROOT).as_posix())
        assert hashlib.sha256(raw).hexdigest() == sha(manifest_path)
    report = {'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'status': 'PASS_LOCAL_SELECTED_DATA_CODE_PROCESSOR_PREFLIGHT_AND_PORTABLE_ARCHIVE',
              'tasks': manifest['tasks'], 'temporal_sources': 48, 'temporal_frames': 6047,
              'selected_file_hashes_verified': verification['files'],
              'input_image_files': sum(p.suffix.lower() == '.png' for p in paths),
              'archive_files': len(paths), 'zip_bytes': archive.stat().st_size, 'zip_sha256': sha(archive),
              'zip': str(archive), 'all_archive_crc_and_sha_verified': True,
              'manifest_sha256': sha(manifest_path),
              'gemini_event_candidates_checked': 600, 'gemini_event_boundaries_used_as_targets': 0,
              'semantic_event_boundary_review_complete': False,
              'time_training_target': 'Exact human sampled-frame importance, not semantic event boundary extraction',
              'actual_8b_loss_or_optimizer_smoke_performed': False,
              'production_model_weights_loaded': False, 'gpu_started': False, 'training_started': False,
              'dataset_uploaded_to_linux': False, 'large_transfer_permission': 'NOT_YET_REQUESTED',
              'small_processor_download_bytes': sum(p.stat().st_size for p in (HERE/'processor_snapshot').glob('*')),
              'small_processor_download_direction': 'LINUX_TO_WINDOWS_VIA_MACMINI_PROXYJUMP',
              'windows_preflight_environment_not_claimed_training_capable': True}
    (HERE / 'release_completion.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)


if __name__ == '__main__':
    main()
