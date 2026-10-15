"""Catalog existing B training and frozen 426 identities, without viewing video/GT."""
import base64
import hashlib
import json
import shlex
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT/'reports/human_reference_iteration_20261013_v1'
COPY = ROOT/'reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
REMOTE = '/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    with Path(path).open('x',encoding='utf-8') as stream:
        json.dump(value,stream,ensure_ascii=False,indent=2,allow_nan=False)


def check_correct_dependency_locations():
    output = REPORT/'existing_runtime_dependency_followup_01.json'
    if output.exists():
        return read(output)  # The prior successful real lookup is never repeated.
    script = """import json,socket,hashlib
from pathlib import Path
if socket.gethostname()!='inspur-NP5570M5':raise ValueError('Unexpected host')
run=Path('/home/inspur/aic_video_work/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z')
paths=[run/'baseline_a_pts_v1/exact_pts.py',run/'baseline_a_pts_v1/native_frames.py',run/'b_score_aligned_package_v4/common.py']
files={str(path):dict(exists=path.is_file(),sha256=hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None) for path in paths}
python=Path('/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python')
print(json.dumps(dict(status='READ_ONLY_CORRECT_NATIVE_HELPER_LOCATIONS',files=files,existing_python=str(python),existing_python_present=python.is_file(),processor_or_model_loaded=False)),flush=True)
"""
    payload=base64.b64encode(script.encode()).decode()
    command='python3 -u -c '+shlex.quote('import base64;exec(base64.b64decode('+repr(payload)+'))')
    result=subprocess.run(['ssh','-o','StrictHostKeyChecking=yes','-o','BatchMode=yes',
                          '-o','ConnectTimeout=12','-o','ServerAliveInterval=15','-o','ServerAliveCountMax=2',
                          'aic-inspur-home',command],capture_output=True,text=True,timeout=55)
    if result.returncode:
        raise ValueError(result.stderr.strip() or 'Dependency location lookup failed')
    receipt=json.loads(result.stdout)
    save(output,receipt)
    return receipt


def main():
    output=REPORT/'known_identity_snapshot_01.json'
    if output.exists():
        raise ValueError('Known identity snapshot already completed; do not regenerate it')
    remote=read(REPORT/'existing_runtime_readonly_01.json')
    training=remote['training_metadata']
    if not training['manifest_matches_frozen_config'] or not training['registry_matches_frozen_config']:
        raise ValueError('Current remote B training manifests do not bind their frozen config')
    local_paths=[COPY/'b_score_aligned_package_v4/config.json',COPY/'temporal_sft8b_full_v1/config.json',
                 COPY/'temporal_sft8b_v1/inputs_01/full_train.jsonl',COPY/'temporal_sft8b_v1/inputs_01/r7_train_registry.json']
    for path in local_paths:
        remote_path=REMOTE+'/'+path.relative_to(COPY).as_posix()
        if sha(path)!=remote['files'][remote_path]['sha256']:
            raise ValueError('Local provenance copy differs from current remote bytes: '+str(path))
    config=read(local_paths[1])
    b_config=read(local_paths[0])
    train=[json.loads(line) for line in local_paths[2].read_text().splitlines()]
    registry=read(local_paths[3])['records']
    parent={row['parent_sample_id']:row for row in registry}
    if (len(parent)!=len(registry) or len(registry)!=704 or len(train)!=724 or
            len({row['parent_sample_id'] for row in train})!=704 or
            len({row['youtube_id'] for row in train})!=602 or
            len({row['youtube_id'] for row in registry})!=602):
        raise ValueError('Complete current B training population differs from its actual contract')
    for row in train:
        original=parent[row['parent_sample_id']]
        for key in ('video_id','youtube_id','source_group','source_path','source_sha256','source_bytes'):
            if row[key]!=original[key]:
                raise ValueError('Training window/source registry identity differs: '+key)
    test_path=ROOT/'reports/boundary_refinement_20261012_v1/input_01/metadata.json'
    test=read(test_path)['records']
    if len(test)!=426 or {row['video_id'] for row in test}!={str(index) for index in range(426)}:
        raise ValueError('Frozen production identity catalog lacks the complete official 426 set')
    followup=check_correct_dependency_locations()
    if not all(row['exists'] for row in followup['files'].values()) or not followup['existing_python_present']:
        raise ValueError('Original native helper locations or existing Python are unavailable')
    # Never retrieve images, labels, raw predictions, or model weight bytes here.
    training_sources=[{key:row[key] for key in ('parent_sample_id','video_id','youtube_id','source_group',
                                               'source_path','source_sha256','source_bytes')} for row in registry]
    test_sources=[{key:row[key] for key in ('video_id','source_group','source_path','source_sha256')} for row in test]
    result=dict(status='COMPLETE_KNOWN_B_TRAINING_AND_FROZEN_426_IDENTITIES_NOT_NEW_MEDIA_SEPARATION',
        training=dict(windows=724,parents=704,original_youtube_groups=602,clip_source_groups=len({row['source_group'] for row in train}),
                      media_sha256_count=len({row['source_sha256'] for row in registry}),sources=training_sources),
        testing=dict(sources=426,records=test_sources),
        current_b_adapter_expected_sha256=b_config['b_adapter_sha256'],
        provenance_bindings={str(path.relative_to(ROOT)):sha(path) for path in local_paths},
        frozen_test_identity_catalog_sha256=sha(test_path),
        current_remote_readonly_receipt_sha256=sha(REPORT/'existing_runtime_readonly_01.json'),
        dependency_followup_sha256=sha(REPORT/'existing_runtime_dependency_followup_01.json'),
        group_definition='602 original youtube_id values, 704 registered source clips, 724 training windows',
        identity_limitations=['Base-model pretraining data is not completely known',
                              'SumMe source titles do not provide canonical YouTube identifiers',
                              'Official numeric video IDs do not provide original source identifiers',
                              'Different identifier namespaces alone do not prove semantic separation',
                              'Exact byte comparisons cannot detect re-encoding or excerpts'],
        new_summe_byte_or_identity_separation='UNVERIFIED_UNTIL_AUTHORIZED_MEDIA_EXISTS',
        videos_or_test_GT_viewed=False,new_media_downloads=0,new_model_calls=0,new_optimizer_updates=0)
    save(output,result)
    print(json.dumps(dict(status=result['status'],training_windows=724,source_clips=704,original_groups=602,test_sources=426,
                         original_helpers_and_python_present=True,new_summe_separation='UNVERIFIED',model_loads=0),ensure_ascii=False))


if __name__=='__main__':
    main()
