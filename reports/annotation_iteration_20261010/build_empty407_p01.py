from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'reports/round6_score_alignment/rematch_discussion/aic_video_empty407_20261010'
RUN=ROOT/'reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
header='''# EMPTY407 两轮完成后的 Pro 集中裁决卷宗 p01

连续任务 AIC-VIDEO-REMATCH-NEXT-20261005，子议题EMPTY407-20261010。原预算5/8已用，剩3；拟本次slot6，不能重置。用户明确允许Gemini 3.8 Flash最高档“高点”，四席两轮完整公开意见与原主控方案/修订全文继承。讨论不能代替事实或用户授权。主控已获用户独立授权继续标签、必要微调到可用ZIP；无新大流量、官网自动提交、生产替换或公开发布授权。

## 主控第二轮后的主张与纠正，供最终批判
接受Tibo/Sol：采用有限观察、已审完整窗口银标编辑建议；区分一般未采样残余风险与具体有后果的UNKNOWN。不会假称逐帧金标、人工真值或模型统计独立；已识别会改变segments的不确定性不进完整列表SFT。候选外漏检探针须占补查预算，学生processor实际分辨率也要检查；确认参考不能删学生不可见的困难事件。真实[]不是缺标签/解析失败。
接受旧V14代码不能直接运行新实验：原admit冻结160、evaluate每源只接受一窗、执行会按epoch挑checkpoint；新入口必须独立版本、固定终点并按原source全局PTS汇总两窗，不改旧文件/锁/STOP/成功结果。
接受明确NO单列，空/空不记正例F1=1。所有24计划窗/12源/拒收/UNKNOWN分母保留，条件F1不作为完整质量。接受Tibo提出有U时保守上下界；共同未识别偏差仍未知。
训练更新修订：8是前案上限不是目标，12训练窗有效batch4、2epochs最多6步；实际N=8..12则2*ceil(N/4)=4或6步、尾batch按实际窗数归一、不复制凑数。建议逐窗assistant-token均值CE再按来源均衡权重，新AdamW1e-5；原r16/a32/qkvo/B288张量初始化，base/vision冻结，固定2epochs终点，1200计费秒训练/2400非测试比较为上限。保存新优化器声明，无旧状态恢复伪称。
拒绝Gemini r01的隐式partial目标：普通segments JSON自回归assistant-mask不能用所谓“区间级Loss Masking”自动解决未知遗漏；没有新的可证实likelihood合同，本轮不尝试。它12窗6来源却标“6训练/3开发/3确认”，混了窗口与来源，无法保持全部每源两窗分组隔离；按其6个训练窗与batch4，两epochs也非固定6步。600/1200/5500秒无保证。它所称官方IoU门0.3/0.5及必须完整叙事的具体实例没有官方依据，保留为假设反例，不能称官方真实规则。
接受6训练/2流程开发/4锁定评价来源组的24窗路线作为候选（相比原6/3/3加强锁定评价，仍全旧媒体非盲泛化）。首4窗来自预定训练组，实际观测合同成立才扩展。至少8训练窗4组，正例/NO真实收录不强迫空窗配额；无空窗则不能声称改进拒绝学习。具体质量门由Pro决断：Sol建议确认>=3组>=6/8窗、至少2正例组2NO组、正例源F1+0.03且最差>-0.05；Tibo三组每组不退且至少2严格改善、macro+.05/P/R不降/U保守方向。数值都是探索性风险筛选而非统计保证，请选唯一可执行门，或否定当前426资格但给下一步可购买信息的方案。
source审核：本次重新核50原媒体SHA，48人工向量帧数一致；原metadata overlap receipt及证据SHA仍相同、可用原ID和exact encoded hash无匹配，但无法排除匿名复赛媒体的重编码/片段重复。所有媒体历史图片标注/训练/开发已暴露，不能称盲确认；原B native训练具体曝光未由此manifest证明。旧license登记差异保留未裁决，本次本地audit不创造法律结论，用户之前明确授权标注/微调且赛方允许闭源标签。不得据媒体像素复刻官方或读取100confirm。

## 信息包字节错误的实际复核与修复
r01 full实际535643B SHA4096...296a；6卷实际concat534052B SHA6534ec7f1c7a7cb7549d7cff20bb10726c412441fad0e1531fb62030285a5f29。差1591=full的1591个CRLF；将full仅CRLF转LF后与全部分卷逐字符完全相同，无内容丢失。旧parts_concat_exact=true字节声明错误，保留原文件/错误，Sol正确指出；Grok/Gem/Tibo只声称读文本并不构成验签。当前p01以统一LF一次写入并按实际bytes拆分、实际concat==full断言，再记录实际SHA，不能混称旧r01验签通过。

## 请一次集中裁决
1. 407空的事实、原因层级、上一轮质量门失误及不可证明根因。
2. 是否接受“有限观察且无有后果UNKNOWN”的完整窗口银标资格，以及具体agy工具供给/主控独立作答/processor可见性/补查上限合同，避免无限升级为不存在的人工金标。
3. 选唯一可执行的小规模路线、按源划分、标签/训练资格、固定更新数/归一、开发及锁定评价的指标分母与具体STOP/GO（含U），是否允许有条件一次426风险ZIP。可否定训练但须给有界能获取新信息的下一步。
4. 全部历史原件与37.66永久保护。新426成本先同native非测试实测估算冻结+拆卸余量，上限建议7200计费秒，不保证足够；不足NO426。不得强制非空/TopK/降阈值复赛调参，不得混旧B1或把同教师一致当真值。

以下继承完整r01（含r00b所有必要事实/原报告/代码/全部首轮原答及主控初案），全部二轮原答，以及新增训练叶合同与实际来源审计。
'''
body=[header,(OUT/'context-r01.md').read_text(encoding='utf-8')]
for n in ('tibo-r01.md','sol-r01.md','grok-r01.md','gemini-r01.md'):
    p=OUT/n;raw=p.read_bytes()
    body.append('\n## 第二轮完整公开原答 '+n+'\n原始文件SHA='+hashlib.sha256(raw).hexdigest()+'\n\n'+raw.decode('utf-8'))
files=[RUN/'teacher_student_autopilot_v14/precision_helpers/training_target.py',RUN/'temporal_sft8b_v1/sft_contract.py',OUT/'source_exposure_audit.json',ROOT/'reports/qwen8b_annotation_20261009_v1/corpus_acceptance.json']
for p in files:
    raw=p.read_bytes();body.append('\n## 新必要原文件全文 '+p.relative_to(ROOT).as_posix()+'\n原始bytes='+str(len(raw))+' SHA='+hashlib.sha256(raw).hexdigest()+'\n\n```\n'+raw.decode('utf-8-sig')+'\n```\n')
body.append('\nEND_EMPTY407_P01\n')
raw=''.join(body).replace('\r\n','\n').encode('utf-8')
path=OUT/'context-p01.md'
with path.open('xb') as f:f.write(raw)
chunks=[];cur=b''
for line in raw.splitlines(keepends=True):
    if cur and len(cur+line)>105000:chunks.append(cur);cur=b''
    cur+=line
if cur:chunks.append(cur)
assert b''.join(chunks)==path.read_bytes()
parts=[]
for i,chunk in enumerate(chunks,1):
    p=OUT/f'context-p01-part{i:02d}.md'
    with p.open('xb') as f:f.write(chunk)
    parts.append(dict(file=p.name,bytes=len(chunk),sha256=hashlib.sha256(chunk).hexdigest()))
meta=dict(full_file=path.name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest(),parts=parts,parts_concat_exact=True)
with (OUT/'p01-manifest.json').open('x',encoding='utf-8') as f:json.dump(meta,f,ensure_ascii=False,indent=2)
with (OUT/'context-p01-index.md').open('x',encoding='utf-8',newline='\n') as f:f.write('# 完整分卷索引\n\n实际原字节顺序拼接已断言相等；完整读取全部分卷，末标END_EMPTY407_P01。原包CRLF误声明的复核与修复在本版首页，所有原意见保留。\n\n```json\n'+json.dumps(meta,ensure_ascii=False,indent=2)+'\n```\n')
print(json.dumps(meta,ensure_ascii=False))
