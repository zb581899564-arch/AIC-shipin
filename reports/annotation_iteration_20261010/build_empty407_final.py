"""Full final discussion packet, byte-preserving split, no browser automation."""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parents[2]
ANN=ROOT/'reports/annotation_iteration_20261010'
OUT=ROOT/'reports/round6_score_alignment/rematch_discussion/aic_video_empty407_20261010'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
decision='''# EMPTY407 最终技术决策与主控承接

状态：Pro slot6 已实际完整回答，连续已用6/8、剩2。本次讨论已完成两轮普通讨论与一次集中裁决；本文件记录方案，不冒充训练、质量改善或新426交付。

采纳完整 pro-p01.md 的唯一 EMPTY407_SLOT6_SILVER24_V1：固定6训练源/2流程开发源/4锁定评价源，每源由原B实际全源native规划器选两窗，共24窗。实际按公开规则重新计算与Pro来源表完全一致；各原件SHA/196564489字节及native_pts文件SHA实核；所有来源已历史曝光，不称未见盲测。新plan只绑定既有协议，不读取评分来选源。窗口端点保留原B float计划的十进制有理数表示，actual帧PTS另保留原始有理数；不把名义域端点称为原件逐帧语义真值。

先导4窗属于新表前两训练源kLxoNp-UchI、AwmHb44_ouw。Pro冻结前的NyBmCxDoHJU/kLxo固定0–30及60–90工具实验是独立工程观察，不算本版先导，不用它们的标签选窗口或替代新blind记录；其中可能有完全同像素窗口也仅作为历史曝光登记。旧六次原生调用不重复，也不升级为训练资格。

对Pro两个澄清：44条explicit count-equal、4条字段缺失、2条count mismatch，主控现场复核同意，历史48仅继承两排除，未声称48新证明；4缺失并非已证明不能用，只按本轮确定44候选执行。所有模型标签是银标建议，不是人工金标或官网目标。

新完整窗口监督必须具备原生视频实际工具回执、floor64全帧身份、原B实际processor有效分辨率证据、教师提案及无标签/无预测的新审阅上下文盲审，然后主控版本化裁定。known consequential UNKNOWN整窗不做完整JSON SFT；有限观察残余采样风险明示，不无限要求每个间隙金标。静态展示可高光，大运动不自动为高光，无音频不能编台词。候选数超过5不得伪合并或默删KEEP；评价不得洗掉学生看不见事件。

盲审必须新上下文：当前主控已读教师输出，不将事后自写称盲审。如需独立审阅子代理，职责仅本轮图像证据与blind记录，fork none，不给任何教师/历史标签/模型预测，不得冒充网页参与席位；必要性是防答案污染，不为泛用并行。主控负责最终审查整合。

观察主线24份教师提案/24份blind记录/4边界风险补查/4候选外探针；每补查一窗内≤2秒/≤128连续帧。不据候选错处改参考。资源与真实会话、tool次数、token另记。旧先导真实EOF与原图读取照实计入累计消耗，绝不把失败数或token记0。新付费通道/充值/租卡/模型下载不获授权；Pro的200元管理上限不构成消费许可，已有资源仍按运行秒和额度记录。

至少8/12合格训练窗、4来源且正例≥2来源才进入原B288张量r16 a32 qkvo续训；base/vision冻结，新AdamW lr1e-5恒定，beta .9/.999 eps1e-8 wd0 clip1，micro1目标accum4、seed20261010、固定2epochs。N=8实更新4、N9..12实更新6；源权N/(G*n_s)，每批loss=(ceil(N/4)/N)*sum(w_i*assistant_token_mean_CE)，不得再固定除4；固定终点，无epoch选优、无第二轮补考。前缀仅工程检查后同optimizer/RNG顺序继续。

一次开发、一次锁定，原B与新候选只差adapter：同native窗口/PTS/采样/processor/B0/grammar/greedy。源级两个窗口联合真实时间，K/NO/U互斥覆盖，间隙不补NO。纯NO不赋空空F1=1，失败不转[]。Pro所有质量门逐项保留：锁定≥6/8完整参考、四源可评价、≥3源已审正例、≥2源各≥5秒NO；dev正例macro增益>0且NO误选不增；locked macro增益≥.05且每正例源不退化、至少2严格改善、P/R不降；NO外溢/已审正例整空不增加；本地tIoU .5一对一事件召回不降；U保守增益各源非负且平均正，预测相同差值精确0。未过任一门本版NO426。

预算准备有效工作60min，native训练1200计费秒，开发/锁定/NT合计2400，条件426 7200；原成本保持，新空间模型0。新权重521时间窗全部真实推理，不引用旧B时间结果。完整空间源场可exact复用。实测同协议shape/token成本估算加安全余量，退出储备≥300秒或2倍实测退出成本；超7200不通过降像素/采样赶工。无自动官网提交、生产替换、公开发布。新数据196.56MB需要Mac跳板和专项传输许可，先做可审核包，继续本地准备。

原37.66 SHA07730c9e02e68d1a1ce54e7ef5a8aa616346cf8f2f8d78426ed36bc3eb481496保持原身份。237步包withdraw推荐已另文保存，407空具体真错比例未知；目标错位、动态信息缺乏是机制假说，不冒称已查明mask错或语言模型必然数值回归均值。不能据模型票数保证涨分。

本版STOP后一次最多4窗信息出口只在原24窗补不同实际证据，不扩源、不第二次训练；参考揭示后新增意见只作诊断，不回写本版STOP为PASS。仍未知：官方细则/编辑风格、原B逐源曝光、匿名重编码重复、现Linux原件就位、AGY实际用量价格。
'''
(OUT/'final-decision.md').write_text(decision,encoding='utf-8')
chunks=[(OUT/'context-p01.md').read_bytes(),b'\n\n# Pro complete public decision\n\n',(OUT/'pro-p01.md').read_bytes(),b'\n\n',decision.encode()]
refs=[OUT/'source_alignment_clarification.json',ANN/'slot6_silver24_v1/source_window_plan.json',
    ANN/'native_event_pilot_v1/teacher_observation_audit_01.json',ANN/'native_event_pilot_v1/NyBmCxDoHJU_00/main_post_teacher_review.md']
for p in refs:
    chunks.extend([('\n\n# Full additional evidence '+str(p.relative_to(ROOT))+'\n\n').encode(),p.read_bytes()])
chunks.append(b'\n\nEND_EMPTY407_FINAL\n')
full=b''.join(chunks);path=OUT/'context-final.md'
with path.open('xb') as f:f.write(full)
parts=[];current=b''
for line in full.splitlines(keepends=True):
    if current and len(current)+len(line)>180000:parts.append(current);current=b''
    current+=line
if current:parts.append(current)
assert b''.join(parts)==full
rows=[]
for i,data in enumerate(parts,1):
    p=OUT/f'context-final-part{i:02d}.md'
    with p.open('xb') as f:f.write(data)
    rows.append(dict(file=p.name,bytes=len(data),sha256=sha(p)))
info=dict(file=path.name,bytes=len(full),sha256=sha(path),parts=rows,parts_concat_exact=True)
with (OUT/'final-manifest.json').open('x',encoding='utf-8') as f:json.dump(info,f,ensure_ascii=False,indent=2)
with (OUT/'context-final-index.md').open('x',encoding='utf-8') as f:f.write('# EMPTY407_FINAL 完整卷索引\n\n依序完整读取全部分卷，至END_EMPTY407_FINAL，不拿摘要替代。新增完整Pro裁决、主控承接、来源窗口计划与错误保留证据。实际字节拼接验证通过；Pro知会不再耗次。\n\n'+json.dumps(info,ensure_ascii=False,indent=2))
print(json.dumps(info,ensure_ascii=False))
