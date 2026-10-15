"""Freeze the observed pilot outcome without changing any sealed observation."""
from pathlib import Path
from datetime import datetime, timezone
import json, hashlib, math

base = Path(__file__).resolve().parent
root = base / 'slot6_silver24_v1'
out = base.parent / 'round6_score_alignment/rematch_discussion/aic_video_empty407_20261010'
utc = datetime.now(timezone.utc).isoformat()
public = [out / f'{s}-r03.md' for s in ('tibo', 'sol', 'grok', 'gemini')]
public += [out/'gemini-r03-completion.md', out/'gemini-r03-input-status.json']
for path in public:
    if not path.exists():
        raise SystemExit(f'WAIT_COMPLETE_PUBLIC_RECORD: {path.name}')

note = '''# 主控代表帧复核与证据范围勘误

实际直接读取W01原始F01/F15/F40/F48/F60/F63六张代表帧，未据此宣称重读全部64张。
可见人物摊手、犬正面肖像、栏杆框景、眼鼻极近特写、门口前沿犬姿态、草地犬背影。
F60/F63都可见同一西班牙语字幕“y cuando la puerta esté abierta sal un rato”。这为门口与户外镜头可能属于同一剪辑叙事提供最强反例，不能只因硬切就强定两个事件；同字幕也不自动证明连续跳落、事件同一或整窗完整取舍。
没有观察音频，没有确认教师6条或初审8条都是必须保留的独立事件。事件身份、编辑价值和区间并集必须分别裁定。
本轮结案依据是尚未建立完整合法目标，不是已证明W01不可表达。

risk01 JSON实际数组R036/R037/R038的observed_fact为null；actual_view_image_read及批号、帧绑定保留。只能声明60帧实际读取记录完整，不能声明60条逐帧文字事实齐全。补查封存前曾暴露范围外教师方向描述，保留此限制，未重复读图洗掉暴露。
'''
(root/'main_factual_final_scope_v1.md').open('x', encoding='utf-8').write(note)
risk = json.loads((root/'blind_reviews/initial/risk01_independent_facts_v1.json').read_text(encoding='utf-8'))
null_facts = [row for row in risk['actual_read_inventory'] if row.get('observed_fact') is None]
jobs = json.loads((root/'observations/jobs.json').read_text(encoding='utf-8'))['jobs']
assert len(jobs) == 24
reasons = [
    '完整事件身份与编辑取舍未裁定；不把6/8提案当确认数，也不声称五事件门已证明不可能通过。',
    '局部硬切/镜头揭示得到更正；其余失焦、姿态取舍及肖像起点仍未形成完整目标。',
    '手部和工具可按视觉保留；后续讲述在此操作上下文的取舍尚不能与未观察讲话意义分离。',
    '讲话区域完整选择未成立，另有原audit白名单问题；浮点PTS差不是错帧，解释侧车未通过原合同。',
]
windows = []
for i, folder in enumerate(map(Path, jobs)):
    windows.append(dict(window_id=folder.name, cpu_actual_processor_prepared=True,
        teacher_execution='SUCCESS' if i < 4 else 'NOT_EXECUTED_AFTER_PILOT_STOP',
        independent_initial_and_effective_views_complete=i < 4,
        disposition='REJECT_COMPLETE_SFT_PARTIAL_FACTS_RETAINED' if i < 4 else 'NOT_OBSERVED_NOT_A_FAILURE',
        training_admitted=False, final_complete_target=None,
        reason=reasons[i] if i < 4 else '仅完成CPU输入准备；先导停止后不扩展教师观察。'))
inventory = []
for path in public:
    raw = path.read_bytes()
    inventory.append(dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()))
decision = dict(status='STOP_PILOT_NO_VALID_COMPLETE_SILVER', utc=utc,
    authority='MAIN_FINAL_ADJUDICATION_UNDER_PRO_SLOT6_CONDITIONAL_STOP_NOT_NEW_PRO_DECISION',
    trigger='现有有限观察及一次不同实际证据补查后，无一窗建立原合同要求的完整学生可观察目标；继续同题意见循环无新增信息。',
    planned_denominator=24, pilot_teacher_success=4, pilot_complete_reference_qualified=0,
    remaining_teacher_not_observed=20, windows=windows, partial_facts_are_not_complete_supervision=True,
    new_optimizer_updates=0, new_student_temporal_calls=0, new_spatial_calls=0, new_426=False,
    pro_used=6, pro_remaining=2, pro_slot7_called=False, new_pro_approval_missing=True,
    no_conflict_with_slot6=True, risk_supplements_used=1, risk_null_fact_entries=len(null_facts),
    risk_teacher_description_exposure_preserved=True,
    post_stop_information_jobs_started=0, post_stop_information_maximum=4,
    stop_scope='THIS_FROZEN_PILOT_VERSION_ONLY_NOT_PERMANENT_LABELING_IMPOSSIBILITY',
    linux_media_transfer='NOT_SENT_PENDING_SEPARATE_PERMISSION_NO_TRAINING_NEED_AFTER_STOP',
    official_quality_improvement='NOT_MEASURED_NO_NEW_MODEL', public_records=inventory)
with (root/'pilot_final_adjudication_v1.json').open('x', encoding='utf-8') as f:
    json.dump(decision, f, ensure_ascii=False, indent=2)

text = '''# EMPTY407 slot6 本版先导最终裁定

裁定：STOP_PILOT_NO_VALID_COMPLETE_SILVER。主控依据真实观察和原Pro slot6条件停止本版；这不是新Pro意见，也不是模型训练失败。

目标仍是改善最佳B8B的高光选择并交付真实可提交ZIP。当前AGY四窗真实SUCCESS，独立原始/有效视图审阅完成；24窗真实CPU准备完成。四窗完整银标准入0/4，余20窗只有输入准备，不算20个标注失败，固定评价分母24保留。未知不改负例，不制造[]，部分K/NO/U只作复核资料。

W01：普通切点与静态镜头不自动U/NO。教师6与初审8均是建议，教师KEEP并集可为4段，不能据此宣称确认事件数≤5或>5。门口/草地同字幕可能构成同一编辑叙事，是反对机械拆事件的强反例；没有完整事件身份、取舍、边界最终裁定，暂不准入，不宣称永久不可表达。
W02：局部连续60帧补查纠正翻滚过程及主动入画推断；镜头揭示和硬切有事实支持，未解决全窗其他模糊和取舍问题。动作名称不明本身不自动U。risk01封存前收到范围外教师描述，不能称完全未暴露；R036–038文字事实为空，不证明未看图。
W10：可见手部和工具短建立不依赖虚构维修成功；具体操作上下文中后续讲述是否承担解释/结果仍会影响完整选择，未听到的内容不能当事实，也不把所有讲话一律U。13批勘误只修记录。
W11：完整有效视图已看完，不能直接以无声讲话造空目标；原工具审计白名单问题独立阻断本版合同。42项PTS差是极小浮点表示差，ordinal一致，不是错帧；侧车不等于机器合同通过。

采纳Tibo/Sol对普通切点、具体未知、有限补查边界及先导条件的解释；拒绝Grok仍把提案数当确认数，拒绝Gemini先前“必然六区间”、动机推测及把407全空归因尚未训练NO标签的说法。407历史故障来自237步图像评分路径，不能伪称本版语言SFT因果已验证。公开模型一致不是金标或质量证明。

Gemini同轮补读报告已见END，原截断答复及补读原文均保留。但其补读后仍把6~8提案数当容量已证明超限，把初审11.41/19.5秒U时长当最终事实，并称未来模型“将迅速/必然”崩溃，主控明确不采纳；这些是未最终裁定的建议和风险假设。补读对407具体机制的泛化描述也不是实际实验因果验收。不因其支持STOP便隐藏这些错误。

最强反例：W01按独立编辑裁定仍可能用已有可见事实形成合法≤5事件/区间目标，不必再增加帧；因此本次STOP不否决闭源标注路线。反向风险是为了凑配额静默删有效内容或把具体未知判NO。当前未有这样的完整裁定，不能把可能性写成PASS。

最终动作：封存四窗部分事实、原始失败与公开反对意见；本版不扩展20教师窗，不启B续训、不生成新426。已完成的CPU、教师任务和观察不重复。停止后的最多4窗信息出口是上限，不是必须花完；目前新任务0，不自动开启第二轮训练。不存在单一孤立事实已被证明可解除全部阻碍，不消耗Pro slot7。连续Pro6/8，余2，缺少新的Pro认可；本裁定遵循原slot6，并不覆盖原协议。

交付：历史用户反馈37.66的candidate_SAFE_37_66.zip原字节保持，另打包质量复核ZIP，后者不能直接训练或官网提交。没有新优化器更新、学生GPU/空间调用或新官方成绩；费用只保留实际工具aggregate及未知现金额。待许可197530023字节跨主机媒体包未上传，本版停止后无训练传输需要。

证据界限：来源历史曝光，不声称盲泛化；抽样和学生可辨认性只保证观测链真实性，不保证官网分。没有听音频/人工金标/官方新核验。生产仍原B，历史STOP、成本和237步撤回包保留。
'''
(out/'final-pilot-decision.md').open('x', encoding='utf-8').write(text)
chunks = [(out/'context-r03a.md').read_bytes()]
for path in public + [root/'main_factual_final_scope_v1.md', root/'pilot_final_adjudication_v1.json', out/'final-pilot-decision.md']:
    raw = path.read_bytes()
    chunks += [f'\n\n## 完整最终新增记录 {path.name}\nSHA256 {hashlib.sha256(raw).hexdigest()}\n\n'.encode(), raw]
chunks.append(b'\n\nEND_EMPTY407_FINAL_PILOT_V1\n')
data = b''.join(chunks)
(out/'context-final-pilot-v1.md').open('xb').write(data)
lines=data.splitlines(keepends=True); pos=0; parts=[]
for i in range(7):
    target=math.ceil(sum(map(len,lines[pos:]))/(7-i)); chunk=[]; size=0
    while pos<len(lines) and (size<target or i==6):
        chunk.append(lines[pos]); size+=len(lines[pos]); pos+=1
    path=out/f'context-final-pilot-v1-part{i+1:02d}.md'; raw=b''.join(chunk); path.open('xb').write(raw)
    parts.append(dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest()))
assert b''.join(Path(row['path']).read_bytes() for row in parts)==data
receipt=dict(version='EMPTY407_FINAL_PILOT_V1', utc=utc, bytes=len(data),
    sha256=hashlib.sha256(data).hexdigest(), parts=parts, parts_concat_byte_exact=True,
    full_context_inherited=True, actual_sent=False)
(out/'context-final-pilot-v1-index.md').open('x',encoding='utf-8').write('# 完整最终卷宗知会\n\n'+json.dumps(receipt,ensure_ascii=False,indent=2)+'\n\n依次读取全部7片至END_EMPTY407_FINAL_PILOT_V1。仅知会，无新实验或新决策请求。\n')
(out/'context-final-pilot-v1-receipt.json').open('x',encoding='utf-8').write(json.dumps(receipt,ensure_ascii=False,indent=2))
print(json.dumps(receipt,ensure_ascii=False,indent=2))
