"""Archive actual completed G0 evidence after the host records final Pro decision.

No remote writes, model/decoder calls, old source edits or launcher actions.
Protect historical files and production_files before unfrozen handoff updates.
"""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,shutil
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
RUN=ROOT/'reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
ENTRY=RUN/'post_sg8_reference_g0_slot5_v1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 assert (HERE/'pro-p01.md').exists() and (HERE/'final-decision.md').exists()
 refs=json.loads((HERE/'reference-qualification-report.json').read_bytes())
 plan=json.loads((HERE/'plan-metadata-g0-readonly.json').read_text(encoding='utf-8-sig'))
 assert not refs['independent_task_matched_reference_established']
 assert plan['status']=='PASS_EXACT_DEVELOPER_METADATA_PLAN_NOT_CONSUMER_OR_QUALITY'
 targets=[ROOT/'AGENTS.md',RUN/'STATUS_AUTOPILOT_20261007.md']
 for p in RUN.glob('*/source_lock.json'):
  v=json.loads(p.read_bytes())
  for k in ('files','production_files'):
   x=v.get(k,{})
   paths=list(x) if isinstance(x,dict) else [r['path'] for r in x]
   for n in paths:
    normal=str(n).replace('\\','/')
    for t in targets:
     assert not normal.endswith('/'+t.name) and normal!=t.name, 'Handoff is protected by historical lock'
 ENTRY.mkdir(exist_ok=False)
 names=['reference-qualification-report.json','plan-metadata-g0-readonly.json','implementation-evidence-bindings.json','implementation-notes.md','independent-g0-verification.json','fallback-registration-readonly.json','input_scope.json','reference_qualification.jsonl','source_exposure.json','two_window_plan.json','cpu_acceptance.json','final-decision.md']
 for n in names:
  shutil.copyfile(HERE/n,ENTRY/n)
  assert (HERE/n).read_bytes()==(ENTRY/n).read_bytes()
 receipt=dict(status='COMPLETE_BOUNDED_REFERENCE_AND_EXACT_PLAN_G0_NO_426',utc=datetime.now(timezone.utc).isoformat(),
  decision_authority='Host decision under user authorization, informed by Chrome research project GPT-6 Pro slot5',
  pro_reply_sha256=sha(HERE/'pro-p01.md'),final_decision_sha256=sha(HERE/'final-decision.md'),
  evidence=[dict(file=n,bytes=(ENTRY/n).stat().st_size,sha256=sha(ENTRY/n)) for n in names],
  developer_records=104,source_groups=96,original_windows=112,affected_records=8,affected_groups=8,planned_changed_requests=16,
  reference_status=refs['status'],reference_established=False,quality='UNKNOWN',new_official_score='UNKNOWN',
  new_model_calls=0,new_decoder_calls=0,new_optimizer_updates=0,new_GPU_charge_seconds=0,
  new_GPU_job_started=False,new_remote_launcher=False,new_remote_writes=False,new_426_ZIP=False,
  consumer_processor_admission='NOT_RUN_NOT_NEEDED_FOR_CLOSED_METADATA_SCOPE',old_costs_and_offset='UNCHANGED_NOT_RECOUNTED',
  historical_source_lock_schemas_protected=['files','production_files'],unregistered_assets='UNKNOWN_NOT_GLOBALLY_SCANNED')
 (ENTRY/'completion.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 (ENTRY/'closure.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 msg=('# 本轮已完成有界G0，NO_426\n\n'
  '两轮普通网页讨论与研究项目Pro slot5裁决完成；本轮用1次，当前余3次。'
  '只执行固定已有参考资格审计与开发双窗元数据计划，不启动GPU、训练或426。\n\n'
  '实核104记录/96来源组/112原窗，双窗8记录/8来源组，候选均分会改变16请求。'
  '原尾0.3–2.134秒、新窗15.15–16.067秒；新右窗保留65个旧尾观测、移除343个、加入447个左上下文观测。'
  '精确中点均非真实PTS，不吸附；实际消费者/RGB/processor/token/模型未运行。'
  '数学/元数据PASS不是质量或完整GPU准入。\n\n'
  '独立线性Fraction/divmod重算全部8记录旧新ordinal SHA相等，15项元数据及合成合同PASS；'
  '消费者有理数边界语义尚NOT_RUN，浮点往返反例保留，不自动启动GPU。\n\n'
  '指定8份既有登记文档及p1b顶层export名范围未建立新的任务匹配独立参考；'
  '987豆包标签保持弱参考，UNANNOTATED不转空/负，GNMC既有许可仍仅本地诊断。'
  '未登记其他资产UNKNOWN，不声称全盘无参考。已到本轮有限出口，不自动接均分风险包或重开旧配方。\n\n'
  '新model/decoder/optimizer/GPU job/remote launcher均0，实际没有新426包。'
  '旧GPU费用/7200offset/最佳B37.63/全部旧raw和STOP保持。'
  '下一步缺口是适用于所选任务的独立参考：完成状态、覆盖/负例语义、原生比例/时钟、许可、来源隔离及曝光史；'
  '缺项未核清前不得把已有工具、模型缓存或合法几何当成真值。\n\n'
  '讨论和完整Pro原文位于 ../../../rematch_discussion/aic_video_post_sg8_20261009；'
  '本目录completion仅代表有界元数据工作完成，绝不是最终ZIP completion。\n')
 (ENTRY/'CONTINUE.md').write_text(msg,encoding='utf-8')
 (ENTRY/'PROTOCOL.md').write_text(msg+'\n固定范围、前瞻NO_426出口与完整异议见讨论final-decision.md。\n',encoding='utf-8')
 marker='<!-- END_POST_SG8_SLOT5_G0 -->'
 block='## 20261009：后续一锅炖slot5与实际有界G0闭环\n\n'+msg.split('\n\n',1)[1]+'\n'+marker+'\n\n'
 for p in targets:
  old=p.read_text(encoding='utf-8')
  assert marker not in old,'Do not duplicate a completed handoff update'
  p.write_text(block+old,encoding='utf-8')
 print(json.dumps(receipt,ensure_ascii=False))
if __name__=='__main__':main()
