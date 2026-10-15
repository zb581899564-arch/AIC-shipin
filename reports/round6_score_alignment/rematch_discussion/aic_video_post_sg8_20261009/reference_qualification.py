"""Finite metadata qualification of named existing references; no media/answers.

Reuses recorded prior findings; does not repeat decoder, model, all-asset or
quality acceptance. Never scans outside this fixed whitelist.
"""
from pathlib import Path
import hashlib, json
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
FILES=[
 'round6_score_alignment/p1b/pilot_manifest.json',
 'round6_score_alignment/p1b/README_annotation_v2.md',
 'reports/round6_score_alignment/phase1b/source_and_license_audit.json',
 'improvement/round3_supervisor/label_origin_audit.json',
 'reports/round6_score_alignment/p2d_deployable_dev/round6_p2d_20260919T130011Z/existing_16x9_reference_audit.json',
 'reports/round6_score_alignment/p2r9_native_portrait_reference/round6_p2r9_20260920T040552Z/annotation_semantics_matrix.json',
 'reports/round6_score_alignment/p2r_reference_gate/round6_p2r_20260919T154701Z/reference_protocol.md',
 'reports/round6_score_alignment/p2r_reference_gate/round6_p2r_20260919T154701Z/snapshots/gnmc_readme.md',
]
def bind(name):
 p=ROOT/name
 b=p.read_bytes()
 return dict(path=name,bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def load(name): return json.loads((ROOT/name).read_text(encoding='utf-8-sig'))
def main():
 bindings=[bind(f) for f in FILES]
 pilot=load(FILES[0]); origin=load(FILES[3]); old=load(FILES[4]); matrix=load(FILES[5])
 assert 'intentionally unannotated' in pilot['purpose']
 assert origin['provenance_models']=={'api_doubao_doubao-seed-2-1-pro-260628':987}
 assert old['status']=='NO_ELIGIBLE_16X9_QUALITY_REFERENCE'
 assert old['finding']['valid_semantic_annotations']==old['finding']['human_reviewed_annotations']==0
 protocol=(ROOT/FILES[6]).read_text(encoding='utf-8')
 assert '不得据此批准训练、比赛测试、打包或提交' in protocol
 readme=(ROOT/FILES[7]).read_text(encoding='utf-8')
 assert "'16:9'" in readme and "'3:4'" in readme and "'9:16'" not in readme
 listing=sorted(str(p.relative_to(ROOT)).replace('\\','/') for p in (ROOT/'round6_score_alignment/p1b').glob('*.json*'))
 unreviewed_exports=[p for p in listing if any(x in Path(p).name.lower() for x in ('reference_export','annotation_export','human_label'))]
 rows=[
  dict(entry='P1B_PILOT',qualification='NO_REFERENCE_ESTABLISHED',reason='Manifest is an annotation interface with intentionally UNANNOTATED fields; no newly registered human export found',source_groups=8,target='mixed 16:9/9:16',coverage='UNANNOTATED_NOT_NEGATIVE',permission='local internal diagnostics recorded; per-video grants unresolved',exposure='old pilot/interface observed'),
  dict(entry='ROUND3_987',qualification='WEAK_MODEL_REFERENCE_ONLY',reason='All 987 provenance rows are api_doubao; not independent human quality',matched=origin['matched'],missing=origin['missing'],coverage='UNKNOWN',permission='existing project use only',exposure='training/development observed'),
  dict(entry='P2D_4_16X9',qualification=old['status'],reason='Reuse prior zero semantic/human review finding; no new quality acceptance',coverage='none',permission='per-video grant not found',exposure='old interface pilot'),
  dict(entry='GNMC',qualification='DIAGNOSTIC_ONLY_NOT_COMPETITION_AUTHORITY',reason='Recorded protocol excludes training/competition testing/packaging/submission; README five native ratios do not include 9:16',coverage='photo crop annotations only',permission='existing diagnostic scope preserved',exposure='prior diagnostic inspected'),
 ]
 for x in matrix['rows']:
  rows.append(dict(entry=x['candidate_id'],qualification=x['qualification_status'],reason=x['human_semantics'],native_target=x['native_9_16'],media_binding=x['media_binding'],permission='NOT_ESTABLISHED_FOR_THIS_EXPERIMENT',coverage='as recorded; no new media/CSV inspected',exposure='metadata only'))
 assert not unreviewed_exports, 'A new named export needs separate qualification before conclusion'
 result=dict(status='NO_NEW_AUDITABLE_ENTRY_IN_FIXED_WHITELIST',utc=datetime.now(timezone.utc).isoformat(),
  scope='Only eight named existing registration documents and top-level p1b export filenames',
  independent_task_matched_reference_established=False,rows=rows,bindings=bindings,
  p1b_top_level_json_filenames=listing,new_registered_exports=unreviewed_exports,
  unregistered_other_assets='UNKNOWN_NOT_GLOBALLY_SCANNED',
  old_findings_reused=True,old_full_acceptance_not_rerun=True,
  training_authorized_by_reference=False,package_authorized_by_reference=False,
  new_model_calls=0,new_decoder_calls=0,new_optimizer_updates=0,new_download_bytes=0,
  test_predictions_read=False,confirm100_read=False,external_media_transmitted=False)
 out=HERE/'reference-qualification-report.json'
 with out.open('x',encoding='utf-8',newline='\n') as f:
  json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
 print(json.dumps({k:v for k,v in result.items() if k not in ('rows','bindings','p1b_top_level_json_filenames')},ensure_ascii=False))
if __name__=='__main__': main()
