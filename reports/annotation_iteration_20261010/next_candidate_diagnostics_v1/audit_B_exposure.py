"""Registered B adapter SFT metadata audit, not a foundation-model exposure proof."""
import argparse
import json
from pathlib import Path
from geometry_diagnostic import sha,write_once


def run(root,output):
    root=Path(root)
    campaign=root/'reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
    train=campaign/'temporal_sft8b_v1/inputs_01/full_train.jsonl'
    config=campaign/'temporal_sft8b_full_v1/config.json'
    completion=campaign/'temporal_sft8b_full_v1/train_report_completion_01.json'
    plan=root/'reports/annotation_iteration_20261010/slot6_silver24_v1/source_window_plan.json'
    if sha(train)!='124801624736f960d15074ad65840d4e2850dcb7d8d5d3b16a2cb54e7eee4bc0':
        raise ValueError('registered B training manifest differs')
    if sha(config)!='7c05b28c75f2ea4aede7844712d8945b9b79ea8c5402e906514c1cfe755e0de3':
        raise ValueError('registered B config differs')
    if sha(plan)!='09ecb28971932bd3bf8ac275c30d0a6fd534345442f2d2ec3529fa3f8e1e4b22':
        raise ValueError('fixed source plan differs')
    if sha(completion)!='61230deef516877615720b6725d40fad3f054bacced54f85859381f2d397eed6':
        raise ValueError('registered B completion bytes differ')
    c=json.loads(completion.read_text(encoding='utf-8-sig'))
    if c['adapter_model_sha256']!='8e2cca463d8aac39f7a709bdf562373e3e47a3a8da490991c303d5e03b803b23' or c['train_manifest_sha256']!=sha(train):
        raise ValueError('B adapter / SFT manifest receipt binding differs')
    # Stream registered training records only; do not open evaluation labels.
    ids,set_sha,groups,set_parents=set(),set(),set(),set()
    rows=0
    for line in train.open(encoding='utf-8-sig'):
        if not line.strip():continue
        row=json.loads(line)
        rows+=1
        if not row.get('youtube_id') or not row.get('source_sha256'):
            raise ValueError('registered row lacks source identity')
        ids.add(row['youtube_id'])
        set_sha.add(row['source_sha256'])
        groups.add(row['source_group'])
        set_parents.add(row['parent_sample_id'])
    if rows!=c['windows'] or len(ids)!=c['source_groups'] or len(set_parents)!=c['parents']:
        raise ValueError('full training denominator mismatch')
    p=json.loads(plan.read_text(encoding='utf-8-sig'))
    sources=[]
    for role,source_rows in p['sources'].items():
        for source in source_rows:
            sources.append(dict(source_id=source['source_id'],role=role,
                                registered_B_SFT_youtube_id_match=source['source_id'] in ids,
                                registered_B_SFT_exact_media_SHA_match=source['media_sha256'] in set_sha,
                                historical_process_exposure=source['exposure']))
    write_once(output,dict(status='REGISTERED_B_ADAPTER_SFT_SOURCE_IDENTITY_AUDIT_ONLY',
                           adapter_sha256=c['adapter_model_sha256'],
                           bindings={str(f.relative_to(root)):sha(f) for f in [train,config,completion,plan]},
                           registered_SFT_rows=rows,registered_SFT_source_groups=len(ids),
                           registered_SFT_clip_group_strings=len(groups),
                           registered_SFT_youtube_IDs=len(ids),sources=sources,
                           source_denominator=len(sources),
                           matching_source_ids=sum(s['registered_B_SFT_youtube_id_match'] for s in sources),
                           matching_media_SHAs=sum(s['registered_B_SFT_exact_media_SHA_match'] for s in sources),
                           scope_limit='No ID/SHA match excludes only registered B adapter SFT entries. Foundation training, undocumented data, different IDs/reposts and prior process exposure remain outside this proof.',
                           blind_generalization_established=False,quality_gate_pass=False,
                           new_model_calls=0,new_optimizer_updates=0,evaluation_label_files_opened=False))


if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--root',required=True)
    p.add_argument('--output',required=True)
    a=p.parse_args()
    run(a.root,a.output)
