"""Append late visible review without rewriting previously captured history."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib

root=Path(__file__).resolve().parent
stamp=datetime.now(timezone.utc).isoformat()
late=root.joinpath('gemini-postpro-late-visible.txt').read_text(encoding='utf-8')
root.joinpath('gemini-postpro-late.md').write_text(late,encoding='utf-8')
correction='''# 主控：Gemini晚到回复及精确更正

先前该消息在检查时显示拒答，之后同一已发送postpro请求出现完整答复。没有额外发送、重新生成或新Pro调用。拒答捕获文件和先前完整卷宗均保留，晚到完整可见回复另存。Gemini声称完整读五卷及SHA匹配；该声称仅按网页原文记录，不等于主控能验证其内部计算。现在普通四席均有postpro实质意见，不据票数宣称正确。

Gemini的支持不改变已裁决算法、样本、门或唯一426出口。主控拒绝其以下延伸/过度表述：

- 新费用不固定写第164行；执行时真实账本/共享任务核验、按实际作业自然终态唯一追加。163行只是旧快照。
- 实际作用门严格是固定NONTEST8已选帧最终整数框变化，不能改成“NONTEST或开发集”择一。
- 不采用“彻底规避弱参考过拟合”或“排除了探针退化风险”的质量保证。共同模型偏差、8组到426外推和实际官方质量仍UNKNOWN。
- AI回复不能授予执行权限；接续依据人类之前明确授权，而非Gemini“可以直接推进”。讨论方案仍非冻结协议/实际G0 PASS。
- 最终新ZIP仅在真实选中框变化及全部门通过后存在；不能单靠算法替换推断文件必然已改变。

这是晚到意见的来源修正与既有硬合同澄清，不是新科学方案或结果驱动改门，无需再消耗Pro。最终新版决策为final-decision-v2.md；旧final-decision.md及context-final.md保留为先前制作的历史版本，尚未向任何席位点击发送。将移除未发送旧附件，再统一发送最终新版完整卷宗及决策。
'''
root.joinpath('host-final-late-correction.md').write_text(correction,encoding='utf-8')
decision=root.joinpath('final-decision.md').read_text(encoding='utf-8')
decision=decision.replace('Gemini再次拒答，不计有效支持。','Gemini晚到完整回复已保存，先前拒答捕获也保留；四席均有实质复核意见，不按多数票宣称正确。')
decision=decision.replace('Grok的NO_426立场继续保留，Gemini拒答不计支持；无假共识。','Grok原NO_426质量异议继续保留；Gemini晚到支持中的固定账本行号、NONTEST或开发集择一效应及质量保证等延伸不采用。完整来源与主控更正附host-final-late-correction.md，无假共识。')
decision+='\n\n## 晚到回复更正\n\nUTC '+stamp+'：Gemini的同一postpro请求后来返回完整复核，之前拒答状态为当时捕获，不覆盖新状态。主控只采纳与Pro原合同一致的技术意见，具体拒绝项见host-final-late-correction.md。本v2为最终讨论决策，旧v1原字节保留。算法/样本/数值门/唯一出口未改；新Pro仍1/5、模型/解码/优化器/远端写仍0。\n'
out=root/'final-decision-v2.md'
with out.open('x',encoding='utf-8',newline='') as f:f.write(decision)
ledger_path=root/'ledger.json'
d=json.loads(ledger_path.read_text(encoding='utf-8'))
d['rounds']['postpro']['status']='complete_four_effective_reviews_late_gemini_reply_preserved'
data=root.joinpath('gemini-postpro-late.md').read_bytes()
d['rounds']['postpro']['gemini_late']=dict(file='gemini-postpro-late.md',bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),status='complete_visible_reply_after_initial_refusal',captured_utc=stamp,read_ack='five volumes/fullSHA claimed; internal byte computation not independently verifiable')
d['final_decision_v1']=d['final_decision']
d['final_decision']=dict(file=out.name,bytes=out.stat().st_size,sha256=hashlib.sha256(out.read_bytes()).hexdigest(),utc=stamp,source='Pro slot4 plus host adoption after four-seat post-review, with late Gemini limitations',pro_new_used=1,pro_new_remaining=4,stage='FINAL_NOTICE_PENDING_G0_NOT_COMPLETE')
ledger_path.write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(d['final_decision'],ensure_ascii=False))
