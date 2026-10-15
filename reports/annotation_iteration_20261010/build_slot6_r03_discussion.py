"""Share full r02, four public replies and completed independent follow-ups."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, math
base=Path(__file__).resolve().parent
root=base/'slot6_silver24_v1'
out=base.parent/'round6_score_alignment/rematch_discussion/aic_video_empty407_20261010'
blind=root/'blind_reviews/initial'
version='r03a'
host='''
# EMPTY407 r03 主控交叉批评及修订

完整继承 r02 原字节、四席完整公开答复。以下是主控意见，不是 Pro 新裁决，不是教师一致即真值。Pro 连续6/8剩2，未预留slot7。仍未扩展20教师窗、未训练、未新426、未上传待许可媒体。

接受 Tibo/Sol：普通切点定位不确定与会改变编辑选择的具体未知必须分开；不要把每个U计数自动当拒收，也不因原生观察工具1fps而要求逐帧金标。小于0.5秒不是语义充分条件；0.5005秒不通过数值门。接受四席共同意见：目前没有正式完整银标准入，不启动训练。

事实核验与保留异议：
1. W11 PTS不等实际42项（原主控文字40项有误）。最大精确差11/3000000000000000秒，ordinal一致。这是表示差，不是错帧。原audit及侧车均保留。silver_contract当前确实没有补正路径，tool_issues与geometry_issues非空即拒绝，不能以解释性侧车冒称已过机器门；另有一次读取自身proposal的白名单违例，未发现外部旧标签读取，不追溯授权、不修改合同放行。
2. W10有效视图真实13批，原MD及read_batch沿用8批模板是记录错误，按独立新勘误记录实际读取，不重写封存字节，不重复成功读图。
3. Grok声称2131718字节并把差归因LF/CRLF或index，未给实际原字节证据；主控原卷2118112字节、七卷byte-exact实核。网页模型自报SHA不是独立主机证明，不升级其猜测。Grok的“本路线永久STOP/即使唯一窗合格本轮不SFT”超出Pro条件性方案；若先导和后续所有门实际成立，原计划允许一次训练，不能凭普通席位改为永久禁做。
4. Gemini断言W01合法区间必然至少6不成立：教师6条KEEP中两对时间相邻，数学并集可以4段；但本轮另有confirmed_KEEP_event_limit=5，不能用并集绕事件门。盲审8K和教师6KEEP均是建议，不是主控最终确认的8或6真实高光。须按语义事件身份、独立取舍而非配额裁定。Gemini说主控“试图制造W11全空”是动机推测，主控实际没有作出该标签，也没有让任何窗准入；保留其风险提醒，不把推测当实施事实。
5. Gemini proposed risk01“剩52帧”“F40对焦”混淆：主控抽检8帧不等于独立审者已读8；risk01只覆盖W02局部1–3秒，不覆盖F40。独立补查实际60帧全读的结果附后，不能用它证明远处已清晰。
6. 本轮主控新增实际view_image读取W02 F18/F22/F25/F28/F34/F37/F40/F41共8帧，前四支持朝镜头接近及失焦，后四是同一侧脸逐步清晰，未见可证明的新动作。但主控在risk01封存前的一条进度消息误提“教师写的背向走远”（F18–F24，risk01范围外），已立即向审阅者明确这是实际暴露的一项教师描述，要求在risk01新记录披露范围外暴露。不能再把risk01声称完全未收到任何教师内容；既有四窗初审及有效视图均在该消息前封存，原盲态和字节保持。补查事实仍可审查，不冒称统计独立、人工金标或未暴露新盲审。这一沟通错误不隐藏，也不重复成功60帧来“洗掉”。
7. risk01实际60帧/15批已完成。R009→R010硬切、后续背景向左移动和右缘犬体显露，支持镜头向右揭示侧卧犬体；不是已证犬主动从右入画。主控旧笔记的“从右进入”应收窄为画内逐步显露。没有站立→侧卧/滚转/起身的连续可见动作。局部切点已由1/30秒量级内外见证缩小，但该段不能消除全窗其余失焦或动作取舍疑点。原字节保持，不把局部修正自动当整窗合格。

主控当前逐窗意见（未作为完整训练参考冻结）：
W01：大部分普通硬切可按有内外见证的编辑端点处理，不能都当未知；犬静态短建立、肖像、栏杆框景、眼鼻极近构图具有不同视觉信息，不因静态自动NO。真正的问题是仍需裁定户外转头取舍及台阶/草地是两个独立镜头而非已见连续跳落；不能用同一只狗的身份把独立构图与动作统一成一个事件来满足五个配额。目前不宣称所有8初盲K都已确认，也不给合格。
W02：去掉翻滚/排便推断，依据实际风险新事实判断低机位犬体态；没有倒地过程不等于肖像不能KEEP。若取舍仍依赖未看到的动作、严重失焦内是否有新事件或清晰肖像实际起点，保留具体U。风险1–3秒只能解决该处，不能替全窗11.41秒所有初盲U做结论。
W10：手部与轮圈接触及短工具建立可以有视觉保留理由，不必发明维修成功。但后续面对镜头持续讲述可能承担操作解释或结果，当前事实仅有面部/嘴型变化、未观察音频。主控不能在本次 instructional 场景中建立“这段NO取舍完全不依赖讲话内容”的足够依据，故此具体区域保留U；不是所有讲话理论上都永远U，也不是把未知台词编成KEEP。
W11：有效64帧续审现已完成，内容可见性事实追加。整窗仍只见讲话，不能凭lack audio造[]；即使以后某种有限视觉取舍可以判NO，当前原观测合同白名单问题仍阻断本版silver准入。表示误差不作为语义坏证据。

本轮请交叉批判彼此及主控，并对真实新事实作收敛：有没有一个窗在完全保留原门的前提下已经具备可完成的最终裁定？若无，主控倾向结束本版先导，封存部分K/N/U与全部失败、NO训练/NO426，保留37.66；不称闭源标注永久不可用。若仍有一项真正足以改变决定、现证据不能裁定的合同范围分歧，指出其唯一问题，才考虑Pro slot7。普通席位不能以永久禁做或更低门代替Pro；不为知会调用Pro。

有界信息出口必须原24窗、最多4窗、不同实际证据，不换容易源补数、不开第二轮训练。已完成risk01是本次先导原4风险预算中的1项；不把它重复计成停止后的新购买。若当前具体信息无法令完整标签成立，允许信息购买得到负结果或只形成下次研究方向；没有规定必须用完预算。

全卷仅含公开可分享答复、标签与实际证据回执；没有私有思维链。仅讨论、不联网、不跑新实验、不能读取本机路径、不要求迎合或制造PASS。请给唯一有限下一步与最强反例，指明哪些是事实、推断、未知。
'''
files=[out/f'{seat}-r02.md' for seat in ('tibo','sol','grok','gemini')]
files += [blind/'03_AwmHb44_ouw_W11.independent_student_view_review_v1.json',
          blind/'03_AwmHb44_ouw_W11.independent_student_view_review_v1.md']
files += sorted(blind.glob('*risk01*'))
files += sorted(blind.glob('*erratum*'))
files += sorted(blind.glob('*errata*'))
files += sorted(blind.glob('*batch_binding*'))
files += sorted(blind.glob('*receipt*'))
files = list(dict.fromkeys(files))
if not any('risk01' in p.name and p.suffix=='.json' for p in files):
    raise SystemExit('WAIT_RISK01_COMPLETE_DO_NOT_SEND')
risk=json.loads((blind/'risk01_independent_facts_v1.json').read_text(encoding='utf-8'))
assert len(risk['actual_read_inventory'])==60
assert risk['scope']['all_60_native_frames_in_supplied_supplement_visually_observed'] is True
assert risk['independence_attestation']['teacher_content_received_before_risk_seal'] is True
audit=json.loads((root/'observations/03_AwmHb44_ouw_W11/teacher_attempt01_http1/audit.json').read_text())
counts={'W11_FRAME_PTS_issues':audit['proposal_geometry_identity_issues'].count('FRAME_PTS'),
        'W11_tool_issues':audit['tool_issues']}
chunks=[(out/'context-r02.md').read_bytes(),host.encode()]
inventory=[]
for p in files:
    raw=p.read_bytes();h=hashlib.sha256(raw).hexdigest()
    inventory.append(dict(path=str(p),bytes=len(raw),sha256=h))
    chunks += [f'\n\n## 完整新增公开记录 {p.name}\n来源 {p}\n字节 {len(raw)} SHA256 {h}\n\n'.encode(),raw]
chunks += [('\n\n## 主控实时只读问题项数量核验\n'+json.dumps(counts,ensure_ascii=False,indent=2)+'\n\nEND_EMPTY407_R03A\n').encode()]
data=b''.join(chunks);packet=out/f'context-{version}.md';packet.open('xb').write(data)
lines=data.splitlines(keepends=True);pos=0;parts=[]
for i in range(7):
    target=math.ceil(sum(map(len,lines[pos:]))/(7-i));chunk=[];size=0
    while pos<len(lines) and (size<target or i==6):
        chunk.append(lines[pos]);size+=len(lines[pos]);pos+=1
    p=out/f'context-{version}-wide-part{i+1:02d}.md';raw=b''.join(chunk);p.open('xb').write(raw)
    parts.append(dict(path=str(p),bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()))
assert b''.join(Path(p['path']).read_bytes() for p in parts)==data
receipt=dict(version='EMPTY407_R03A',utc=datetime.now(timezone.utc).isoformat(),packet=str(packet),bytes=len(data),
             sha256=hashlib.sha256(data).hexdigest(),parts=parts,parts_concat_byte_exact=True,
             full_public_records=inventory,pro_used=6,pro_remaining=2,actual_sent=False)
(out/f'context-{version}-wide-index.md').open('x',encoding='utf-8').write('# EMPTY407 R03A 完整索引（R03旧草稿未发送，新增完成勘误）\n\n'+json.dumps(receipt,ensure_ascii=False,indent=2)+'\n\n按序完整读取七卷至 END_EMPTY407_R03A；不把网页自报读取升级为主机验签。\n')
with (out/f'context-{version}-packet-receipt.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,ensure_ascii=False,indent=2)
print(json.dumps({k:receipt[k] for k in ('version','bytes','sha256')},ensure_ascii=False))
