"""Bind completed CPU diagnostics and explicit remaining candidate requirements."""
from datetime import datetime,timezone
import json
from pathlib import Path
import zipfile
from geometry_diagnostic import sha,write_once

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
RUN=ROOT/'reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'


def main():
    t=json.loads((HERE/'temporal_binding_v2.json').read_text())
    s=json.loads((HERE/'spatial_geometry_v2.json').read_text())
    b=json.loads((HERE/'B_exposure.json').read_text())
    if t['quality_gate_pass'] or s['quality_gate_pass'] or b['quality_gate_pass']:
        raise ValueError('diagnostic must not create a quality PASS')
    if not t['publisher_tsv_mat_vectors_exact_equal'] or not t['publisher_mean_matches_gt_score']:
        raise ValueError('publisher audit not accepted')
    if b['registered_SFT_rows']!=724 or b['registered_SFT_source_groups']!=602 or b['source_denominator']!=12:
        raise ValueError('B exposure denominator differs')
    baseline=ROOT/'deliveries/ANNOTATION_ITERATION_20261010/SAFE_37_66/candidate_SAFE_37_66.zip'
    expected='07730c9e02e68d1a1ce54e7ef5a8aa616346cf8f2f8d78426ed36bc3eb481496'
    if sha(baseline)!=expected:
        raise ValueError('37.66 baseline bytes differ')
    with zipfile.ZipFile(baseline) as z:
        if z.namelist()!=['predictions.jsonl'] or z.testzip() is not None:
            raise ValueError('baseline archive structure differs')
        baseline_records=len(z.read('predictions.jsonl').splitlines())
    if baseline_records!=426:
        raise ValueError('baseline record denominator differs')
    utc=datetime.now(timezone.utc).isoformat()
    gaps=dict(schema='EXISTING_REFERENCE_MINIMUM_GAP_REGISTER_V1',utc=utc,
        scope='Existing registered materials only. No new collection, labels, model calls or dataset expansion.',
        temporal=[
            dict(item='publisher_reference_binding',state='PARTIALLY_SUPPLEMENTED_FROM_EXISTING_MATERIAL',
                 evidence='temporal_binding_v2.json',
                 established='W01 TSV/MAT vectors, nframes and mean match; native [30,60) score changes align to 2-second bins; source and 64 sample PNG SHAs bound',
                 missing='Publisher exact time-expansion convention and mapping outside W01 remain unproved',
                 needs_user_files=False,existing_material_next='Publisher metadata/code clarification may help; equal counts or a local bin check alone do not establish the convention'),
            dict(item='original_B_exposure',state='REGISTERED_ADAPTER_SFT_DIRECT_IDENTITY_MATCHES_EXCLUDED',
                 evidence='B_exposure.json',
                 established='724 rows, 704 parents, 602 original YouTube sources; fixed12 have zero ID/SHA matches',
                 missing='Foundation pretraining, undocumented/reposted aliases and prior process exposure are outside this proof',
                 needs_user_files=False,existing_material_next='This registered-SFT question is now bounded; historical process exposure remains declared and cannot be undone'),
            dict(item='highlight_objective_and_complete_reference',state='NOT_SUPPLEMENTABLE_BY_REINTERPRETING_EXISTING_LABELS',
                 evidence='slot6_silver24_v1/pilot_final_adjudication_v1.json; w01_editorial_diagnostic_v1/task.md',
                 established='Original pilot complete silver 0/4; facts are not highlight choices; importance is not unconditional KEEP/NO',
                 missing='Task-matching complete, independently adjudicated KEEP/NO/UNKNOWN and observable boundary evidence; frozen training admission 8-12 windows, >=4 sources; frozen locked reference gate >=6/8 complete with all4 sources and other quality gates',
                 needs_user_files=False,
                 needs_new_annotation_or_supplied_reference=True,
                 existing_material_next='Existing authorized media can be the substrate for new independent editing adjudication. No existing score threshold, narrative-rich proposal or model self-review can manufacture the missing references. Current bounded action does not collect new labels.')],
        spatial=[
            dict(source='GNMC_open4_dev',permission='LOCAL_NONCOMMERCIAL_DIAGNOSTIC_ONLY',
                 ratios=['16:9'],source_SHA_binding=True,frame_binding='SINGLE_STATIC_IMAGE',PTS='NOT_APPLICABLE_STATIC',
                 independence='SINGLE_EDITOR; ORIGINAL_SOURCE_INDEPENDENCE_UNKNOWN_BEYOND_FILENAME',
                 same_frame_frozen_B_output='NOT_FOUND',quality_reference_admitted=False,
                 existing_material_next='Geometry bounds completed; 3/4 have zero IoU sensitivity to center position. Cannot fill native 9:16 video reference or justify production scale.'),
            dict(source='LIVE_YT_VC_registered_candidate',permission='NOT_ESTABLISHED_IN_EXISTING_REGISTRATION',
                 ratios='NATIVE_RATIO_PUBLISHER_DESCRIPTION_ONLY',source_SHA_binding=False,frame_binding='NO_ELIGIBLE_MEDIA_LABEL_BYTES_BOUND',PTS='NOT_BOUND',
                 independence='UNESTABLISHED',same_frame_frozen_B_output='NONE',quality_reference_admitted=False,
                 existing_material_next='Requires permission and actual label/media/frame binding; existing candidate metadata is insufficient.'),
            dict(source='TVSum50_codex_crop1200',permission='EXISTING_LICENSE_HISTORY_NOT_UPGRADED_BY_THIS_AUDIT',
                 ratios=['16:9','9:16'],source_SHA_binding=True,frame_binding='600_SPARSE_NATIVE_PNGS',PTS='REGISTERED_NATIVE_ORDINAL_AND_PTS',
                 independence='MODEL_ANNOTATION_AND_SELF_REVIEW_NOT_HUMAN_GOLD',
                 same_frame_frozen_B_output='NOT_ESTABLISHED',quality_reference_admitted=False,
                 existing_material_next='May support engineering/weak supervision within its approved scope. Independent true composition reference and full predeclared frame coverage remain missing.'),
            dict(source='ROUND3_987_weak_ROI',permission='EXISTING_REGISTERED_SCOPE_ONLY',
                 ratios=['9:16'],source_SHA_binding='EXISTING_PARTIAL_MAPPING',frame_binding='WEAK_ROI_MAPPING',PTS='EXISTING_MAPPING_NOT_NEWLY_VERIFIED',
                 independence='DOUBAO_WEAK_LABELS_PREVIOUSLY_EXPOSED',same_frame_frozen_B_output='NOT_ESTABLISHED_AS_COMPOSITION_REFERENCE',
                 quality_reference_admitted=False,existing_material_next='Cannot replace independent composition truth.'),
            dict(source='production_nontest8_cache',permission='EXISTING_PIPELINE_SCOPE',ratios=['9:16'],
                 source_SHA_binding=True,frame_binding='1486_SOURCE_FIELD_FRAMES_206_ANCHORS;447_SELECTED',PTS='EXISTING_ACCEPTED_CLOCK',
                 independence='MODEL_OUTPUT_NOT_REFERENCE',same_frame_frozen_B_output='AVAILABLE_FOR_THESE8_ONLY',
                 fixed24_source_ID_and_SHA_overlap=0,quality_reference_admitted=False,
                 existing_material_next='Cannot borrow these boxes for different TVSum/GNMC media.')],
        spatial_minimum_missing='Permission-qualified independent native-video composition reference for both ratios, source/frame/PTS binding and same-frame original-B outputs covering all predeclared comparison frames.',
        must_user_upload_media=False,
        next_scope_requirement='New independent annotation/reference acquisition and any unresolved dataset permission must be an explicit next stage; do not manufacture a candidate quality PASS from the existing proxy labels.',
        old_quality_gates_unchanged=True,new_collection=False,new_candidate_generated=False)
    write_once(HERE/'reference_gaps.json',gaps)
    bound_files=[p for p in HERE.iterdir() if p.is_file() and p.name not in {'acceptance.json','RESULT.md'}]
    acceptance=dict(status='CPU_DIAGNOSTICS_ACCEPTED_CANDIDATE_ADMISSION_BLOCKED_BY_REFERENCE_GAPS',utc=utc,
        engineering_checks=dict(six_actual_unit_tests_passed=True,independent_geometry_review_accepted=True,
            independent_temporal_review_fixes_accepted=True,original_reports_and_engineering_failure_preserved=True),
        diagnostics=dict(temporal='temporal_binding_v2.json',spatial='spatial_geometry_v2.json',B_exposure='B_exposure.json'),
        baseline=dict(path=str(baseline),bytes=baseline.stat().st_size,sha256=expected,records=baseline_records,CRC_ok=True),
        old_scale_STOP=dict(path=str(RUN/'next_round_v1/scale_reference_gate_01.json'),sha256=sha(RUN/'next_round_v1/scale_reference_gate_01.json')),
        frozen_quality_protocol=dict(path=str(ROOT/'reports/annotation_iteration_20261010/slot6_silver24_v1/frozen_protocol_v2_explicit_empty_gate.json'),sha256=sha(ROOT/'reports/annotation_iteration_20261010/slot6_silver24_v1/frozen_protocol_v2_explicit_empty_gate.json')),
        source_and_result_SHAs={p.name:sha(p) for p in sorted(bound_files)},
        quality_gate_pass=False,training_admitted=False,new_candidate_generated=False,
        new_model_calls=0,new_GPU_jobs=0,new_optimizer_updates=0,new_426_calls=0,new_uploads=0,
        Pro_used=6,Pro_cap=8,existing_jobs_restarted=False,
        remote_state_snapshot=dict(utc='2026-10-10T13:52:23.287909+00:00',active_project_processes=[],GPU_compute_processes=[]),
        requested_next_qualified_package='NOT_ACHIEVED',next_required_artifact='Qualified task-matching independent reference; see reference_gaps.json')
    write_once(HERE/'acceptance.json',acceptance)
    lines=['# 下一候选诊断实际结果','',
        'CPU工程验收完成，下一候选质量准入仍被真实参考缺口阻塞。本目录没有新的提交ZIP。', '',
        '- W01发布TSV/MAT的20×3896评分逐值相同，publisher均值/nframes一致；899原生帧内143次评分变化/14个序号全部在2秒格边界。不是高光边界或AIC目标等价证明。',
        '- 原B登记SFT 724窗/704父样本/602原始源；固定24窗的12源ID与媒体SHA均0匹配。仅排除登记SFT的直接匹配，不恢复盲测资格。',
        '- 开放GNMC四dev最大整数宽度的最佳位置IoU上限依次0.951748、0.602094、0.498462、0.915703；后三项最佳-最差精确为0，无法区分中心。实际模型框未提供，actual IoU与center gap保持null。',
        '- 6项测试实际通过；160个固定随机几何样例的最大/最小值与独立位置穷举一致。独立审查另外验证966最大值样例/34非法宽度拒绝，后续只读确认新增最小值公式。',
        '- 首版TSV读取范围声明过强，原报告保留，ENGINEERING_ERRATUM.json已实际落盘。B曝光首实现混淆clip group与原始YouTube source，失败记录保留，按原合同修复。', '',
        '## 最小缺件','',
        '时间：完整、任务匹配、独立裁定且学生可观察的取舍与边界。原冻结训练/锁定质量门不变；现有重要性分数、叙事提案和四图事实不能自动补成KEEP/NO。已有视频可作为新增独立标注的输入，不必要求用户重新上传媒体。', '',
        '空间：获准使用的非测试双比例视频构图参考，独立性与source/frame/PTS完整绑定，以及固定比较帧上的原B输出。GNMC仅静态16:9，本次量化不能外推复赛；弱框不能升级为真值。', '',
        '当前已有材料核查已补齐可证的发布包一致性与原B登记SFT身份信息；其余需要新增独立标注/合格参考阶段，不能靠扩大训练或重复制包解决。', '',
        '37.66保底包SHA保持07730c9e02e68d1a1ce54e7ef5a8aa616346cf8f2f8d78426ed36bc3eb481496；本轮模型/GPU/optimizer/426/传输均0。Pro6/8未调用。', '',
        '## 复现','',
        '使用既有slot6_silver24_v1/cpu_env/Scripts/python.exe -B。几何与时间工具的输出使用独占创建，不覆写现有成功回执；复现应指定新的输出路径。',
        'geometry_diagnostic.py --manifest ../../round6_score_alignment/p2r_reference_gate/round6_p2r_20260919T154701Z/pilot/gnmc/selected/dev_manifest.jsonl --output NEW_PATH',
        'temporal_reference_diagnostic.py --root G:/ai/AIC视频 --output NEW_PATH',
        'audit_B_exposure.py --root G:/ai/AIC视频 --output NEW_PATH',
        'python -B -m unittest test_geometry test_temporal -v', '',
        '完整逐项缺件见reference_gaps.json；身份与验收见acceptance.json。传输解码错误没有被记作研究STOP，也没有重启后台进程。','']
    with (HERE/'RESULT.md').open('x',encoding='utf-8') as handle:handle.write('\n'.join(lines))
    print(json.dumps(dict(status=acceptance['status'],acceptance_sha256=sha(HERE/'acceptance.json'),
                          reference_gaps_sha256=sha(HERE/'reference_gaps.json'),new_candidate_generated=False)))


if __name__=='__main__':main()
