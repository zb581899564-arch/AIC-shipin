"""Append complete public pilot records to the already-shared full discussion dossier."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, math
base = Path(__file__).resolve().parent
root = base/'slot6_silver24_v1'
out = base.parent/'round6_score_alignment/rematch_discussion/aic_video_empty407_20261010'
old = out/'context-final.md'
jobs = [Path(p) for p in json.loads((root/'observations/jobs.json').read_text())['jobs'][:4]]
files = [root/'frozen_protocol_v2_explicit_empty_gate.json', root/'pilot_execution_receipt_v1.json',
         root/'cpu_preparation_completion.json', root/'source_audio_presence_only.json',
         root/'main_factual_probe_notes_v1.md', root/'main_factual_probe_corrections_v2.md',
         root/'blind_initial_geometry_acceptance_v1.json',root/'quality_contract.py',root/'silver_contract.py']
pending = []
for folder in jobs:
    attempt=folder/'teacher_attempt01_http1'
    files += [attempt/'proposal.json', attempt/'audit.json', attempt/'terminal.json']
    correction=attempt/'main_metadata_correction_v1.json'
    if correction.exists(): files.append(correction)
    for suffix in ('independent_initial_blind_v1.json','independent_initial_blind_v1.md',
                   'independent_student_view_review_v1.json','independent_student_view_review_v1.md'):
        p=root/'blind_reviews/initial'/f'{folder.name}.{suffix}'
        if p.exists(): files.append(p)
        else: pending.append(str(p))
files += [root/'supplements/risk01_kL_W02_local1to3/manifest.json',
          root/'supplements/risk01_kL_W02_local1to3/main_factual_probe_notes_v1.md']
host='''
# EMPTY407 实际先导证据后的普通交叉审查 r02

这不是新的配方或解除旧STOP。此前完整卷宗、四席两轮意见、Pro slot6、最终知会均原样继承。当前连续Pro已用6/8剩2，尚未预留或发送slot7。

四个冻结先导窗真实AGY SUCCESS，256原生PNG/32实际有效显示PNG全部供给、319工具、实际usage在回执；24窗实际CPU processor准备完成，新student推理/optimizer/空间调用均0。新197530023字节媒体包上传问题仍等待明确答复；不因本讨论绕许可。

主控初始立场：不能用工具SUCCESS、审阅者一致或本地F1冒称官网改善；也不能把一种审阅意见自动当真值。已知会改变答案的UNKNOWN不能进入完整JSON SFT。但是普通采样定位区间不能机械变成所有切镜都不可训练，边界工程上限0.5秒不等于必须逐帧金标；这是当前实际争议。

尚未裁定先导STOP或PASS，不按凑1窗配额挑标签、不跑后20教师或训练。保留所有不一致，不平均原端点、不按candidate选择窗口。W11精确PTS差为11/3000000000000000秒，ordinal一致，已版本化侧车校正；它不是实际帧错位，不拿微小表示差证明语义坏。自身proposal一次读入超声明白名单保留，不等于外部标签泄漏。

具体疑问必须据本次实际公开记录回答：
1. 全部原生/有效视图中识别到的切镜括区、失焦、动作类别不明，怎样分别判断是一般残余风险、允许有支持的编辑边界，还是已识别会改变KEEP/NO/列表是否结束的UNKNOWN？不允许以银标有噪声一笔抹去，也不要求无限观察。
2. 两个原件实际有AAC音轨，本轮clip/实际AGY回执未提供音频观察。W10/W11教师把人物讲话判NO，盲审保留讲述意义未知。能否在保持本轮query-free视觉有限编辑建议定义下做一个有依据的最终选择，还是本窗必须拒收？不能发明台词、默认谈话无价值、或只为训练配额制造空例。原生视频工具采样不透明且只提供1fps画面，不能冒称原件完整多模态已读。
3. 原B0语法约束实际是最多5时间区间。Pro另规定超过5个应保留事件不可强行合并。W01教师10条raw中6KEEP、其余NO/U，盲审8条K建议；真实应该如何统计“已确认事件”与一个连续剪辑区间？不得把NO/U算高光，也不得以区间并集掩盖彼此无关的真实事件。是否属于必须请Pro明确的合同歧义？
4. W02“翻滚、蹲坐/排便”在事实层没有充分支持：主控实际图像见身体低、前爪位移、侧卧；字幕不是排便见证。独立记录还有失焦、前爪短动作类型未知。改成直接可见描述能否消除影响编辑选择的未知，还是当前仍只能部分K/N/U？请区分更正事实与为准入补造目标。
5. 是否已有至少1个能诚实裁定的完整silver窗口？若有，给出对应记录、还须真实观察的最小信息与严格条件，不凭推荐就说已通过。若无，按现方案STOP，再给一次最多4窗、仍原24窗、不同实际证据的有界信息出口；不扩源、不改冻结门、不开第二次训练。

主控保留异议：四窗几乎被一律拒绝可能来自真实不确定，也可能来自把编辑选择主观性/普通定位风险一律当未知。反过来为了开训选择性裁定NO会再度复制407空问题。不要简单投票，请各自批判这两种错误。静态展示可KEEP、运动不自动KEEP，明确已见空不等于未读到正例。

本轮仅讨论，不联网、不读本地路径/外链、不执行任何新模型/训练/传输。原始公开附件内容包括必要代码/完整teacher提案/初始及已完成有效视图blind记录；不包含AGY stream中的私有思维内容。尚在进行的独立后续审阅明确登记缺失，下一轮追加实际完成记录，不伪称已完成。
'''
chunks=[old.read_bytes(), host.encode('utf-8')]
inventory=[]
for p in files:
    data=p.read_bytes(); h=hashlib.sha256(data).hexdigest()
    inventory.append(dict(path=str(p),bytes=len(data),sha256=h))
    chunks.append(f'\n\n## 完整新增公开证据：{p.name}\n来源：{p}\n字节：{len(data)}；SHA256：{h}\n\n'.encode('utf-8'))
    chunks.append(data)
chunks.append(('\n\n## 尚未完成的记录（不是已观察证明）\n'+json.dumps(pending,ensure_ascii=False,indent=2)+'\n\nEND_EMPTY407_R02\n').encode('utf-8'))
data=b''.join(chunks); packet=out/'context-r02.md'
packet.open('xb').write(data)
# Seven consecutive newline-safe byte parts, plus the index fits the observed eight-file UI limit.
lines=data.splitlines(keepends=True); parts=[]; pos=0
for i in range(7):
    remaining=sum(map(len,lines[pos:])); target=math.ceil(remaining/(7-i)); chunk=[]; size=0
    while pos<len(lines) and (size<target or i==6):
        chunk.append(lines[pos]);size+=len(lines[pos]);pos+=1
    part=out/f'context-r02-wide-part{i+1:02d}.md'; value=b''.join(chunk);part.open('xb').write(value)
    parts.append(dict(path=str(part),bytes=len(value),sha256=hashlib.sha256(value).hexdigest()))
assert pos==len(lines) and b''.join(Path(p['path']).read_bytes() for p in parts)==packet.read_bytes()
receipt=dict(version='EMPTY407_R02',utc=datetime.now(timezone.utc).isoformat(),packet=str(packet),
             bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),parts=parts,
             parts_concat_byte_exact=True,full_public_records=inventory,pending_records=pending,
             pro_used=6,pro_remaining=2,actual_sent=False)
index=out/'context-r02-wide-index.md'
index.open('x',encoding='utf-8').write('# EMPTY407_R02 全卷索引\n\n'+json.dumps(receipt,ensure_ascii=False,indent=2)+'\n\n请完整按序读取全部七卷至 END_EMPTY407_R02。主控物理字节串联实核；网页模型不能虚称独立SHA通过。\n')
with (out/'context-r02-packet-receipt.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,ensure_ascii=False,indent=2)
print(json.dumps(dict(bytes=receipt['bytes'],sha256=receipt['sha256'],parts=7,pending=len(pending)),ensure_ascii=False))
