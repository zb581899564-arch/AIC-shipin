from pathlib import Path
import hashlib,json
root=Path(__file__).resolve().parents[2]
out=root/'reports/round6_score_alignment/rematch_discussion/aic_video_empty407_20261010'
run=root/'reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
header='''# EMPTY407 第二轮完整交叉审查 r01

连续任务AIC-VIDEO-REMATCH-NEXT-20261005。普通第一轮四席公开答复均完成；Gemini原r00截断答复保留，补传r00b完整四卷后修订答复也保留。不是多数票证明质量。原所有事实/源码/历史Pro与异议全文随后继承。本版末标END_EMPTY407_R01。Pro仍5/8，剩3，本轮不消耗。

## 主控第一轮后的修订、接受与拒绝
接受：图片评分架构的阈值/校准与事件目标存在明显风险；撤回237步新包质量推荐，保留失败原件。主控过去放行门只比较弱基座及已见TVSum代理，非测试8全空也没触发语义审查，不能把完整工程验收当业务可用性。SHA/PTS/像素保护仍必要，但不能代替高光质量。
接受：优先原37.66对应B8B native管线，标注原生事件并验证学生可见证据、完整窗口和边界；部分KEEP+未知区域不能编成完整segments，因为停止输出会隐含遗漏监督。未知不转负例；同教师一致不是金标；独立盲审先看媒体/规则后看答案。
纠正关键版本错误：Sol把旧历史1..5提示当成当前37.66语法，事实不成立。当前bw_common.helpers -> context_advisory.runtime.bind_helpers -> V14.helper_paths明确绑定V14 precision_helpers/contracts.py；experiment.base_texts()['B0']=该模块EMPTY_PROMPT，内容return between 0 and 5 intervals且允许[]、不把不确定当无高光。bw_engine/local_request实际allow_empty=True。下附完整必要代码。旧1..5提示属于历史B1/原CFR，保留不能混作当前B0。不能仅训练正窗以修一个不存在的表达限制。
纠正主控口头分母笔误：新9dev actual score/gold共有1351点，不是1451。new范围24..53，gold21..87，>=49 new48/1351，gold293/1351；4/9全空，5非空。Tibo的逆序反例应复核：sTEELN-vY30 grid5 gold87/pred48 vs grid32 gold27/pred50；保序标量校准无法修这种逆序，且TVSum重要性仍非AIC金标。Tibo所报5404是4臂×1351。
拒绝：Gemini首答100%非空/强制选帧比例/静态必拒/I-frame即切镜先验；补答已撤回这些。切镜只触发审查，连续叙事允许跨镜；模型新版本不应事后改写原标签端点制造通过。训练早期有限loss也可正常波动，不能把任意震荡都说成失败。Gemini“单尖峰M_spike可过完整门”只检验stage2额外proxyF，忽略stage2还要求研究Spearman/top15多数源改善，因此不是完整门反例；门仍不足以证明AIC质量，这点成立。
拒绝：Grok要求新图片评分器与B native同grammar作公平比较；不同任务的诊断必须各自原prompt/grammar，只统一媒体源/参考域并比较最终选择，不能改B到图片prompt。B续训candidate0/1则确实必须同原native输入和生成协议。旧optimizer状态未核，不要求凭空恢复；继承B权重、明确新建optimizer不等于恢复旧优化轨迹。
保留异议：仅有6–12个来源组的银标门不能证明官方涨分。此前旧32B弱标签15步没有胜过B，不能反复同配方；新计划必须购买不同的实际观察及目标一致证据。不预设降阈值一定无价值，也不把它开成第二条426路线。

## 主控建议唯一有界工作包，供严格批判
先静态核训练mask/实际协议、来源与历史曝光，不重复已有成功生成。首次小试4窗，流程可审计后扩到最多12 source_group×2个事前确定非重叠<=30s窗口，共24窗：6训练/3流程开发/3锁定确认。已有TVSum48源优先，先建立历史曝光关系再定组；不假称确认未见，若都是旧暴露组则明确锁定开发性质和弱证据。来源不够缩小并登记，不擅自下载。
agy终端为提案教师，原生MP4提供全局观察，再显式送原B实际64帧原生RGB/PTS索引(可分批)，每批读取回执与逐帧可见事实可审查；边界补供原生短序列。所有声明和实际工具供给分开，不用teacher自报证明完整观测。第二观察由主控直接查看相同证据且先独立盲记，再对比教师；当前没有人工金标，不冒称人工审查。全窗SFT资格究竟能否在64帧完整供给+原生MP4稀疏工具下成立需重点裁决：不能把所有采样帧已读等同整个视频逐帧已观察，也不能把稀疏之间每一小段一律UNKNOWN而把合法有限观察学习永久阻塞。请给科学上诚实可操作的银标资格，或明确否定本轮全窗续训。
候选事件事实/高光理由/内部与内外边界证据、原生ordinal/PTS、可观察性、未解决范围都保留。超过5事件/不确定边界不擅自合并凑grammar。合法无高光只有足够全窗证据才可[]；部分正例不得作为全部真值。
最多24提案+24盲审记录+8新边界补查=56项观察任务(主控审查不是闭源调用)，已有6片原成功raw只引用不重跑。前瞻工程上限非统计保证。至少8合格训练窗/4组；完整参考先冻结再揭示candidate0/1。主要source等权原生时间F1，事件匹配/边界误差/正事件漏空/明确NO误选另报；UNKNOWN分母全列。小样本不能据此宣称官网涨分。
标签达标才一次B权重初始化native SFT；初拟原r16/alpha32/qkvo，基座/视觉冻结，lr1e-5，有效batch4，至多2epoch/8真实更新(不凑数、不扫超参/挑确认checkpoint)，新optimizer明确登记。逐样本assistant-only CE归一公式须冻结，不能沿用评分训练器假称native视频训练。确认候选0/1只差adapter，使用相同源/window/floor64/精确PTS/processor/像素/EMPTY_PROMPT/0..5/greedy/native映射/空间场。新权重固定终点，只一次确认。
建议前瞻风险门：开发macroΔtimeF1>0；锁定确认macro>0且至少2/3源不负，无正事件漏空增加、明确NO误选时长增加或可确认无关内容边界外溢。要求precision/recall/最坏源退化完整报告，由Pro选择数值门或否定其证据力。不用teacher一致或选帧密度作真值。若必须更大确认才科学充分，请区分统计证明和用户明确接受的有限实验风险。
本阶段上限标注24窗/有界补查，native训练1200计费秒、非测试对照2400计费秒建议；实际资源动态准入，CPU准备不计作模型0成本、资源加载退出时间真实记账。426新推理预算须实测非测试后估算、保留拆卸余量，不能照搬Tibo2400秒(原V14仅时间5430.028秒)。已有成功candidate0精确身份可复用，不重复模型/CPU验收。任何工程/标签/质量门失败STOP这版，保留37.66，不事后重选样本配方。全部通过才单次完整426风险ZIP，官网分UNKNOWN，用户手工提交；不自动生产替换。

请交叉批判全部原文与主控改案，直接回答：当前B0版本、完整监督可观察性资格、银标审查的真实能力与来源/曝光隔离、主控缩减预算能否支撑一次可信小试、质量指标具体分母/未知处理、若拒绝训练是否有仍可购买新信息的可执行下一步。不得把“要求完整观察”无限升级为无可达到的金标证明，但不能虚构资格。仅讨论，不联网/实验/训练；下一步才研究项目Pro集中裁决。
'''
body=[header,(out/'context-r00b.md').read_text()]
for name in ['tibo-r00.md','sol-r00.md','grok-r00.md','gemini-r00-partial-input-visible.md','gemini-r00b.md']:
    p=out/name;raw=p.read_bytes()
    body.append('\n\n## 第一轮原始完整公开回答：'+name+'\nSHA256='+hashlib.sha256(raw).hexdigest()+'\n\n'+raw.decode())
files=[root/'reports/qwen8b_annotation_20261009_v1/training_v2/train_lora.py',root/'reports/qwen8b_annotation_20261009_v1/training_v2/sft_contract.py',run/'balanced_two_window_risk_v3/bw_common.py',run/'balanced_two_window_risk_v3/bw_engine.py',run/'context_advisory_v1/experiment.py',run/'context_advisory_v1/runtime.py',run/'teacher_student_autopilot_v14/train_student.py',run/'teacher_student_autopilot_v14/precision_helpers/contracts.py']
for p in files:
    raw=p.read_bytes();body.append('\n\n## 补充原文件全文：'+p.relative_to(root).as_posix()+'\n字节='+str(len(raw))+' SHA256='+hashlib.sha256(raw).hexdigest()+'\n\n```py\n'+raw.decode('utf-8-sig')+'\n```\n')
body.append('\nEND_EMPTY407_R01\n')
path=out/'context-r01.md'
with path.open('x',encoding='utf-8',newline='\n') as f:f.write(''.join(body))
src=(root/'reports/annotation_iteration_20261010/prepare_empty407_volumes.py').read_text()
ns={'Path':Path,'json':json,'hashlib':hashlib};exec(src[src.index('def parts(path):'):src.index("if __name__=='__main__'")],ns);meta=ns['parts'](path)
(out/'r01-manifest.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
