from pathlib import Path
import hashlib,json,datetime

root=Path(__file__).resolve().parents[2]
out=root/'reports/round6_score_alignment/rematch_discussion/aic_video_empty407_20261010'
out.mkdir(parents=True,exist_ok=True)
ann=root/'reports/annotation_iteration_20261010'
run=root/'reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
header='''# AIC 视频复赛：407个空视频后的重新决策

任务ID AIC-VIDEO-REMATCH-NEXT-20261005；子议题 EMPTY407-20261010；r00完整业务包。
这份包提供本次决策所需的事实、原报告、必要代码和前次Pro裁决。不是把整个仓库或无关用户对话外传。每个原文件都有本地主控实际读取的字节与SHA；外部模型不应把声明SHA说成自己已独立验签。末尾标志END_EMPTY407_R00。

## 用户原始要求及持续授权
用户：“你妹的407个视频是空是什么鬼，你赶紧用一锅炖那个技能去讨论讨论下一步怎么办吧，可以继续微调我们最佳包，也可以继续让强闭源模型去标注很好的数据集，你自己看着弄”。此前要求自主调研、讨论、检查修复并迭代到质量可用ZIP，优先终端调用agy做高光视频标注。用户说明官方允许闭源辅助标注，不再重复询问标注许可。今天已明确允许Gemini 3.8 Flash网页最高档（实际UI高点/超级详尽）参加本次讨论。
讨论后的训练和标注在用户授权内；公开发布、官网提交、生产模型替换和新大流量下载/传输没有新增授权。原B最佳包、未提交工作、原raw、失败、STOP、费用全部保留。禁止读100confirm、手看复赛内容调参、按复赛输出选择阈值或补TopK。复赛407空是公开报告的失败症状，可评估风险；不据此反推测试配方。

## 当前关键事实与局限
1. 历史最佳原B8B+双窗均衡已由用户反馈37.66/DONE，426记录102112选中帧，ZIP306167字节，SHA07730c9e02e68d1a1ce54e7ef5a8aa616346cf8f2f8d78426ed36bc3eb481496。未独立登录官网验证。双窗改变不是新训练，原B adapter SHA8e2cca463d8aac39f7a709bdf562373e3e47a3a8da490991c303d5e03b803b23保留。
2. 新237步独立TVSum图片评分LoRA不是从原B续训。39train源314行、9个已见dev源89行；16有序图片/row、2秒取中点、20人均值乘20。输出语法20..100，但importance标签是TVSum相对重要性，不是AIC语义高光边界。阈值49来自train人工标签80分位，与模型输出分布校准未获证明，2秒整格扩展是假设。
3. 新实验426仅3189选中帧，407空、19非空；非测试8全部空。510真实生成与实际4439张采样图片独立CPU回放都通过，工程11strict通过；这不证明质量。新ZIP12384字节，SHA01969ab4c8221b279dfa58fe1c9f3c5c47cd01fe8cd7dea312bde93cdb3d6325，官网分UNKNOWN，未提交。主控撤回推荐它作为质量可用包，保留失败产物。
4. 四组89条开发比较中new Spearman .522329/base .043629，但native proxyF改善95CI[-.001096,.210326]跨0；9dev已暴露，不盲。production_B是在新image评分prompt下的诊断，根本不是原B native视频生产公平比较。工程gate只要求点估计大于base且研究排序改善，未能识别AIC域崩塌。
5. agy终端Gemini3.8Flash-high读取6段30s原生MP4，90格KEEP37/REJECT34/UNKNOWN19。工具声称1fps/30images，实际完整观测无法导出证明；20稀疏原生锚点与PTS映射核过，其中最后28-30s格镜头切换暴露整格过宽。teacher入训0、UNKNOWN未当负例。这不代表不能标注，而代表需要任务定义/边界与质量验收。
6. 旧32B160窗+盲复查仅65train/14dev弱支持，其余81UNKNOWN；旧微调15步后选回原B。成功、失败和弱一致性限制保留；同模型复查不是金标。旧空间LoRA合法0/148、旧TVSum时间20步也未胜基座，不能重开旧失败假称新进展。
7. 最佳空间源场31295锚点/原18723.876秒成本保留。本次新选择器新空间调用0，只精确复用完整场后过滤。模型最终实际主辅总参数必须<=9B；闭源可用于非测试训练标注，不能拿闭源直接推理复赛提交。
8. 本轮8新GPU作业自然完成/exit0、独立唯一终态账本4598.561109152623计费秒；不是GPU忙碌积分。无当前活跃本轮作业，历史费用不归零。
9. 现有TVSum48完整人工native映射源、开发104/96组及原开放非测试数据可查；不能凭空称有未暴露任务金标或所有全球数据不存在。新大数据需专项方向/大小/代理流量许可；先用现有数据。
10. 连续Pro预算原簿累计5/8，剩3。前次Pro G0/NO426与用户随后接受风险的双窗实验历史均保留，今日不是重置预算。

## 主控独立初始立场（先于外部意见）
撤回新评分ZIP推荐。407空是严重部署质量风险，但仅此无法确证真实高光召回或唯一原因。先区分语义任务不匹配、全局阈值/输出校准、视频时序输入差异、训练输出偏置/工程语义问题，而不是立刻扩大同配方TVSum训练或测试降阈值。
优先以原B37.66的native视频prompt/grammar/processor/时钟作为candidate0。构建现有非测试来源的目标一致高质量闭源标注，小批先验证再扩大，保留未知与证据不足；使用事件级KEEP/NO/UNKNOWN及原生证据帧和精确边界，独立审查切镜/快速动作，不能要求模型假称全帧看到。标注审查应比较实际可见视觉事实和任务定义，不能把同教师一致率当独立金标。
选择器校准实验只有非测试train/calibration/confirmation source级隔离、事前指标/目标预算和原B native公平对照成立时才值得做。TVSum排序任务可以辅助但不应取代高光边界监督。如果原B续训，则明确加载原B adapter、保留candidate0和实际optimizer变化，train-only不够的标签不凑负例。空间暂保持原8B源场；一轮一条可证伪主路线，质量验收先于426。用户希望推进，请给可执行的有界工作包，别无限等完美真值或无限模型菜单。

## 请每位普通参与者回答
先确认任务/版本/附件/实际读取范围及末标，区分事实、推断、未知。给唯一推荐主路线、最强反例、根因的最小非测试判别检查、具体标注格式/观察方法/质量接受条件、从原B续训还是新选择器及公平对照、数据源和隔离、预算/停止条件。数值阈值若只是前瞻工程投入规则需说明依据，不假称统计保证。批评主控至少一项关键弱点。只讨论材料，不调用外部实验；下一轮将完整共享所有人的原文再交叉批判，后才向Chrome研究Pro问一次。
'''
files=[
ann/'PLAN.md',ann/'RESEARCH.md',ann/'DISCUSSION.md',ann/'INDEPENDENT_REVIEW.md',ann/'QUALITY_REPORT.md',ann/'DELIVERY.md',
ann/'ANNOTATION_FINDINGS.md',ann/'ANNOTATION_ANCHOR_AUDIT.md',ann/'annotation_summary.json',
ann/'observed_train.py',ann/'predict_scores.py',ann/'selector_contract.py',ann/'score_grammar.py',ann/'selector_threshold.json',ann/'temporal_config.json',
ann/'evaluate_iteration_v2.py',ann/'cpu_quality_acceptance_protocol.json',ann/'PROSPECTIVE_STAGE2.md',ann/'CONTEST_PROTOCOL.md',ann/'contest_engine.py',
ann/'agy_short_clips_v2.py',ann/'quality_result.json',ann/'contest_results/completion.json',
run/'b_sft8b_package_v3/PROTOCOL.md',run/'b_sft8b_package_v3/runtime.py',run/'b_score_aligned_package_v4/PROTOCOL.md',
run/'balanced_two_window_risk_v3/PROTOCOL.md',run/'teacher_student_autopilot_v14/PROTOCOL.md',
root/'reports/round6_score_alignment/rematch_discussion/aic_video_post_sg8_20261009/pro-p01.md',
run/'next_round_v1/official_rematch_snapshot.txt',
run/'baseline_a_pts_v1/vendor/temporal_common.py'
]
parts=[header];manifest=[]
for p in files:
    raw=p.read_bytes();body=raw.decode('utf-8-sig');rel=p.relative_to(root).as_posix()
    meta={'file':rel,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()};manifest.append(meta)
    parts.append(f'\n\n## 原文件全文：{rel}\n字节={len(raw)}；SHA256={meta["sha256"]}\n\n```{p.suffix.lstrip(".")}\n{body}\n```\n')
parts.append('\nEND_EMPTY407_R00\n')
packet=out/'context-r00.md'
if packet.exists():raise SystemExit('version already exists; do not overwrite')
packet.write_text(''.join(parts),encoding='utf-8',newline='\n')
data=packet.read_bytes()
ledger={'task_id':'AIC-VIDEO-REMATCH-NEXT-20261005','topic':'EMPTY407-20261010','utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
'packet':{'path':str(packet),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'lines':len(data.decode().splitlines())},
'pro_budget_directory':str(root/'reports/round6_score_alignment/rematch_discussion/aic_video_rematch_20261005T1044Z/pro-budget'),
'pro_used_or_reserved_before':5,'pro_remaining_before':3,
'gemini_mode_user_authorization':'允许，用3.8 Flash最高档','participants':{},'sources':manifest}
(out/'ledger.json').write_text(json.dumps(ledger,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(ledger['packet'],ensure_ascii=False))
