"""Freeze local discussion decision and receipts; never controls browser or remote."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

root = Path(__file__).resolve().parent
stamp = datetime.now(timezone.utc).isoformat()
decision = root.joinpath('final-decision-draft.md').read_text(encoding='utf-8')
decision = decision.replace('# AIC 新一轮路线裁决（待收齐普通席位复核后定稿）', '# AIC 新一轮路线裁决：有条件执行单次空间PCHIP探索')
decision = decision.replace('普通三轮原文和Pro完整答复已保存；本文件当前仍是草稿，不是冻结实验/启动/真实验收。', '普通三轮原文、Pro完整答复和裁决后三席完整复核已保存。GPT-6 sol、Tibo、Grok均接受按收紧条件收敛，继续保留质量UNKNOWN；Gemini再次拒答，不计有效支持。本文件是最终讨论决策，不是冻结实验/启动/真实验收。Tibo确认全部正文范围，但文本导出字节与附件原字节不同，未独立验证附件SHA；该限制原样保留。')
decision = decision.replace('缓存已暴露史如实记录，不叫全新语义盲测。现有只读库存8物理sourceSHA/14镜头/206锚点/165合格中央gap8只证明结构库存，不证明独立组或质量。', '缓存已暴露史逐请求登记，不叫全新语义盲测。若某确认探针历史回答实际参与过本轮公式、门或样本选择，或无法核清是否参与，本版在任何新探针揭示前停止NO_426；不重新封存冒充未暴露，不按收益换组。仅存在历史缓存并不自动等于参与选法，须保存可审计来源。现有只读库存8物理sourceSHA/14镜头/206锚点/165合格中央gap8只证明结构库存。新增只读原manifest确认8条记录有8个不同的已登记source_group、缺失0，manifestSHA与绑定值相同；这是来源登记核验，不代表人工证实全球来源独立，也不是完整G0验收。')
decision = decision.replace('按真实目标比例计算面积，使用有理数比较严格正差。', '从真实目标比例的规范原始表示构造连续框，高度=w×target_h/target_w，不另取整；面积、组均值、严格正及留一门统一有理数比较。新评价器不沿用默认9:16或浮点微差；原生产浮点线性/round分支仍逐框字节恒等，不为统一算术而改写。')
decision = decision.replace('G2：同配置完成后6组，独立由全部raw重建8组56相位和门，保存全部结果。', 'G2：同配置完成后6组，独立由全部raw重建8组56相位和数值门，保存全部结果。G2数值通过不等于总GO，还须G3完成固定NONTEST实际选帧整数框变化及全部严格验收。')
decision = decision.replace('定稿和同步后在该既有授权内先完成G0真实资产移交/来源组资格和新CPU实现。', '最终完整卷宗与决策同步普通席位后，在该既有授权内先完成G0真实资产移交/来源组资格和新CPU实现。')
decision += '\n\n## 讨论与额度实际回执\n\n定稿UTC：' + stamp + '。本轮新增Pro已用1/5、剩余4；历史原三次保持，连续预算累计slot4/8。Pro使用Chrome既有研究项目实际对话，完整答复留pro-p01.md及pro-slot4-final.png。没有为知会消耗Pro。新路线模型调用/解码/优化器更新/远端写入均尚为0；只读来源组核验已实际进行，完整G0、实验锁、真实非测试和426包均尚未完成。\n\n淘汰本轮均衡窗口主案是有限投入选择，不是已证伪该方案；旧C/B1/密度/nearest/边界路线各自原STOP不回写。三席可收敛不解除共同模型偏差，仍可能低于旧最佳37.63。后续只有真实验收通过才能报告可提交包，不强造提分。\n'
out = root / 'final-decision.md'
with out.open('x', encoding='utf-8', newline='') as f:
    f.write(decision)
group_summary = dict(utc=stamp, hostname='inspur-NP5570M5', manifest_sha256='ba34a284183e8a079054ffe811d7ec096e6b47c94e6edf812a37fd11b92d8dd7', records=8, distinct_registered_source_groups=8, missing_registered_source_groups=0, distinct_source_sha256=8, ordered_group_mapping_sha256='3d70d8c8ffc9cadf7cabe197dc2f07ea063255f44d617022eb6afd8d3f7cd423', new_model_calls=0, new_decode_calls=0, remote_writes=0, status='READ_ONLY_REGISTERED_GROUP_IDENTITY_NOT_FULL_G0_ACCEPTANCE')
root.joinpath('readonly-source-groups.json').write_text(json.dumps(group_summary, ensure_ascii=False, indent=2)+'\n',encoding='utf-8')
ledger_path=root/'ledger.json'
ledger=json.loads(ledger_path.read_text(encoding='utf-8'))
post=ledger['rounds']['postpro']
post['status']='complete_three_effective_reviews_gemini_refusal'
for seat,ack in [('sol','all five raw volumes/SHA reported verified'),('grok','all five volumes/SHA reported verified'),('tibo','all five text ranges read; exported578359 versus declared579028, raw SHA unverified'),('gemini','no effective opinion or reading acknowledgement')]:
    path=root/(seat+'-postpro.md')
    data=path.read_bytes()
    post[seat]=dict(file=path.name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),captured_utc=stamp,status='refusal' if seat=='gemini' else 'complete_visible_reply',read_ack=ack)
ledger['final_decision']=dict(file=out.name,bytes=out.stat().st_size,sha256=hashlib.sha256(out.read_bytes()).hexdigest(),utc=stamp,source='Pro slot4 conditional technical ruling adopted by host after three-seat review',pro_new_used=1,pro_new_remaining=4,stage='FINAL_NOTICE_PENDING_G0_NOT_COMPLETE')
ledger_path.write_text(json.dumps(ledger,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(ledger['final_decision'],ensure_ascii=False))
