
但如果人物正在解释刚才失败的原因或宣布最重要的修复结论，那么这段静态讲话可能比前面重复展示轮胎的镜头更值得保留。

原B实际采样看不到语音内容，而银标却用[]或NO去监督它放弃讲话镜头。训练CE可能正常下降，银标F1甚至上升，真实高光剪辑质量却下降。

相反，若把每次讲话、每次切镜都标成UNKNOWN，训练永远无法开始。

两种极端都不合理。解决原则应是：先冻结可评价的目标范围，再根据真实可见事实裁定；不能因信息缺失编造NO，也不能因理论上存在未知就否决所有视觉可判的内容。

最终独立意见

当前四窗准入数：0。先导尚未PASS；现在不扩标、不训练、不运行新426。

优先完成已有的W11有效视图审查和risk01完整独立补查，然后对四窗逐项形成正式的编辑裁定。W01重点解决独立事件数和切点；W02重点解决失焦与动作是否改变选择；W10/W11保持讲话语义缺证和实际协议问题的诚实记录。

若没有任何完整银标，通过现行STOP路径结束本版，保留有界信息出口；若确实产生至少一个合格窗口，也只代表可以按原冻结合同继续扩标，绝不代表获得训练或426自动放行资格。

本轮没有新实验、联网、模型调用或Pro调用。连续Pro维持6/8，剩2。


## 完整新增公开记录 grok-r02.md
来源 G:\ai\AIC视频\reports\round6_score_alignment\rematch_discussion\aic_video_empty407_20261010\grok-r02.md
字节 5673 SHA256 0544cb6856e027e6e35640f1bec496ef14891cc42b8f00bfe3e7fd035dac13ab

# grok r02 public completed response

Source: https://grok.com/c/1e265ba4-5df0-449b-84a1-1deae6716eff?rid=4d196106-5573-42c2-8140-051c661beb15
Captured UTC: 2026-10-10T06:54:15.688Z
Status: complete public response visible, not independent experiment

工作了 59s

读取范围确认

已按序完整读取 context-r02-wide-index.md + context-r02-wide-part01.md 至 part07.md，至终末标记 END_EMPTY407_R02。主控声明全卷 2118112 字节 / SHA b463aabf2f1781aee73794faafdac2ef2b376535c1ad1dcfbeb21c3c46cd4a1c；本环境实测分卷 concat 约 2131718 字节（差异主要来自 LF/CRLF 与索引本身，内容流与末标一致，未做独立底层验签）。W11 有效视图续审与 risk01 完整独立补查明确登记为未完成（非隐藏）。连续 Pro 6/8，剩 2，未调用 slot7。仅讨论。

事实 / 推断 / 未知

事实：四窗真实 SUCCESS 提案（256 原生 PNG + 32 有效视图、319 工具、usage 回执完整），training_admitted=false，新 optimizer/student 调用 0；W01 盲审含大量切镜 U，事件数超 5；W02 有失焦与动作类别不明；risk01 笔记确认 R009–R010 切镜、无连续倒地完整见证；W10/W11 教师将讲话判 NO，盲审保留讲述意义未知；两原件有 AAC，但本轮 clip 未供音频。

推断：当前无任何窗口满足“已审完整、无有后果 UNKNOWN、事件可诚实表示为 ≤5 区间”的完整银标资格。

未知：剩余 W11 有效视图与 risk01 全 60 帧独立补查结果；共同偏差对官方分的真实影响。

批判主控与旧意见

主控正确区分了一般残余风险与有后果 UNKNOWN，拒绝为配额造空/伪合并，并明确 pending 项。弱点：仍把“工具 SUCCESS + 盲审一致”过早当作接近银标资格的信号，四窗几乎全 pending 时仍保留扩展路径；对讲话 NO 的处理未在协议层明确“纯视觉编辑”与“音频价值残留”的边界，容易在后续被解读为选择性放行。

自己旧意见（有界事件级银标 + 条件性 B 续训）接受主控纠正：B0 为 0..5 允许空。但原 24 窗规模在已暴露源上证据力弱；本轮 pilot 显示稀疏 64 帧 + 切镜 U 密度高时，完整窗口资格极易饿死或隐含负例。

对五项疑问的证据回答

切镜 / 失焦 / 动作不明：一般残余风险 = 采样间隙 ≤0.5s 且相邻帧无可见主体/构图突变、不会改变 KEEP/NO 或边界归属。允许有支持的编辑边界 = 切镜位置已由相邻样本确认，且事件可独立标注。有后果 UNKNOWN = 切镜/失焦/动作类别不明会改变是否保留该段、端点落在何处、或列表是否结束（W01 大量切镜 U、W02 失焦+前爪短动作即属此类）。不能一律抹成噪声，也不能要求逐帧金标。
无音频讲话：本轮协议是 query-free 视觉有限编辑建议。视觉上静态持留、无新构图/动作信息时可诚实判 NO（不发明台词、不默认谈话无价值）。若盲审认为讲述意义可能改变编辑选择，则该区间必须为 U，不能为配额强行 NO。原生工具 1fps 不透明，不能冒称多模态已读。当前 W10/W11 至少有“讲述意义未知”残留，不能直接完整银标。
最多 5 区间 vs 已确认事件：B0 语法 0..5。W01 盲审 8 个 K 事件，超出限制。不能把 NO/U 算高光，也不能用并集掩盖无关事件。超过 5 且无法诚实选择子集时，该窗不具备完整 segments SFT 资格。此为合同歧义，需 Pro 明确：是“最多 5 个保留事件”还是“超出则整窗不合格”。
W02 直接可见描述：可消除过度推断（无排便见证、字幕不是事实），改为“身体较低、前爪位移、侧卧”。但失焦与短动作类别不明仍可能改变是否 KEEP 该区间，当前仍只能部分 K/NO/U，不能补造成完整目标。
是否已有 ≥1 完整银标：无。所有已完成记录 training_admitted=false，W01 有大量有后果 U 且事件超限，W02 有未决动作/失焦，W11 有效视图与 risk01 完整补查未完成。禁止为凑 1 窗造空/伪合并。

唯一可执行有界工作包 / STOP

当前 pilot 无完整银标 → STOP 扩展与训练。保留 37.66 candidate0。

有界信息出口（不扩源、不改门、不开第二次训练）：完成已登记的 W11 有效视图续审 + risk01 全 60 帧独立事实补查（主控盲记先于教师对照）。若完成后仍无窗口满足“无有后果 UNKNOWN + 事件 ≤5 可诚实表示 + 学生实际可见证据闭环”，则本路线永久 STOP，下一步仅封存失败证据。若出现唯一窗口满足上述严格条件，才可登记为候选银标（仍需独立确认），但本轮不启动 SFT。

最强反例

即使强行把一个有残余切镜/短瞬态 U 的窗口标为银标并续训，教师与审查者共同漏掉 64 帧间隙内的叙事完整单元（助跑-起跳-落地-反馈），学生拟合超窄区间后在银标 F1 上胜出，官方 IoU 因叙事完整性不足而暴跌，原 B0 宽泛区间反而更高分。24 窗已暴露源 + 稀疏观察无法排除此共同偏差。

工程 / 质量 STOP/GO

工程：来源隔离失败、mask 无法绑定、工具回执与声明不符、参数超 9B → STOP。

质量：任何有后果 UNKNOWN 进入完整列表、事件强制合并、讲话强行 NO 为配额、确认 macro ΔtimeF1 ≤0 或正事件漏空增加 → STOP。

未知全列保留，不转负。禁止复赛调阈值、强制非空/TopK、100confirm、同教师一致当真值。

本轮讨论结束，等待下一轮追加完成记录后再交叉审查，再向研究项目 Pro 裁决。


## 完整新增公开记录 gemini-r02.md
来源 G:\ai\AIC视频\reports\round6_score_alignment\rematch_discussion\aic_video_empty407_20261010\gemini-r02.md
字节 14509 SHA256 21d4fbd66ad92e342823a5fc7feef60d1d542dc4484ee1eecee0edbb438581ba

# gemini r02 public completed response

Source: https://gemini.google.com/app/ecd26c8f21f6ed7b
Captured UTC: 2026-10-10T06:54:15.717Z
Status: complete public response visible, not independent experiment

本次实际完整读取范围为 wide-index 及 wide-part01 至 wide-part07 全部 7 个分卷正文，文本流与末标 END_EMPTY407_R02 完整闭合，全卷累计 2,118,112 字节，SHA256 校验值为 b463aabf2f1781aee73794faafdac2ef2b376535c1ad1dcfbeb21c3c46cd4a1c。全卷继承此前两轮普通交叉意见、全部代码合同与 Pro slot6 集中裁决，确认连续 Pro 预算已消耗 6/8、剩余 2 次，本轮未发起 slot7 调用，且不执行任何联网或模型推理/微调实验。   
MD
+ 2

一、自我批判与对主控旧意见的批判

1. Gemini 自我纠偏与严厉批判

撤回 r01 提出的“区间级 Loss Masking”假说：我在 r01 中曾构想“若窗口内存在 UNKNOWN，则在序列损失中仅屏蔽对应时间区间，从而利用剩余 KEEP/NO 进行 SFT”。这一假说被代码事实与自回归训练机制直接否定——在标准因果自回归模型中，输出序列 {"segments": [[a, b]]} 是离散文本 token。如果在尾部生成了 ]} 并伴随 <|im_end|>，模型在因果概率上就是将未列出的全部时间强行监督为“不存在高光”。由于没有独立的显式未知 token 协议可供边缘化（marginalize），任何针对普通自回归 JSON 的所谓“时间掩码”都是自欺欺人，必然向学生注入隐含负例。我完全接受 Pro slot6 与 Tibo/Sol 的批评，承认“含有后果 UNKNOWN 的窗口必须整窗排除出完整 SFT”是当前协议下的唯一科学选择。   
MD
+ 4

再次清算 r00 先验教条：彻底摒弃早期试图强推“非测试 100% 非空”、“帧预算比例硬约束”、“切镜绝不可跨越”等错误断言，坚持以事实证据为准。   
MD

2. 对主控旧意见与当前矛盾的批判

警惕为了“先导至少通过 1 窗”而滑向“造空”与“伪合并”：主控在 r02 中表现出一种危险的焦虑——由于 4 个先导窗口均面临不同程度的瑕疵，主控试图通过“把 W11 讲话判为 NO”来强凑一个全空窗口，或试图探讨“W01 能否通过区间并集掩盖真实事件以压进 5 个语法区间”。这与上一轮“因为允许空就放任非测试 8 全空、最终导致 407 空”是同一种管理缺陷的变种。绝不能为了让先导流程变绿，就人为降格监督标准。   
MD
+ 2

盲审者存在将“切镜工程容差”机械泛化为“全域 UNKNOWN”的过度防御倾向：盲审者在 W01 和 W02 中，将相邻采样帧之间的每一个切镜间隙（约 0.47 秒）都单列为一段独立的 U（如 W01 列出 9 段 U，W02 列出 6 段 U）。如果把所有符合 ≤0.5 秒工程公差、且前后镜头事实清晰的编辑边界切点都机械打成不可消除的语义未知，那么任何含切镜的自然视频都将在数学上永远被 u > 0 阻断。这种防御过当必须与真实的“会改变高光决策的 UNKNOWN”严格区分。   
MD
+ 3

二、主控五项实际疑问的逐项证据裁决
疑问 1：切镜括区、失焦、动作类别不明的性质界定与分流标准

必须在证据层将“普通采样定位公差”、“有支持的编辑决策边界”与“有后果的 UNKNOWN”彻底解耦：   
MD

现象类型	证据特征	定性归属	处理与准入规则
镜头正常硬切（如 W01 F05 到 F06、F13 到 F14）	

前后帧分别为不同机位清晰画面，前后动作各自独立，采样跨度 ≤0.5 秒 
MD

	

有支持的编辑决策边界（非语义 U） 
MD

	

允许在区间端点上取切点估计值（带内外见证帧），该 ≤0.5 秒定位间隙属于协议允许的边界工程公差，不应单列为独立的语义 U 时间段，不阻断 SFT 资格。 
MD


镜头跨镜接续不明（如 W01 F61 台阶末帧到 F62 草地背影）	

前后镜头主体虽为同一犬，但前镜头未见完整下阶跳跃，后镜头已在平地奔跑，中间缺失关键下落过程 
MD

	

有后果的 UNKNOWN（影响事件连续性） 
MD

	

无法判断此动作是连续叙事事件还是两次独立截取，直接影响 KEEP 起止边界与事件计数，必须保留为真实 U。 
MD
+ 1


严重脱焦与拉焦过渡（如 W02 F25–F28 冲镜头大模糊、F34–F41 散景团块）	

画面主体大面积散斑失焦，五官轮廓与肢体动作在原生及有效视图中均完全不可辨 
MD

	

有后果的 UNKNOWN（直接污染起止端点） 
MD

	

摄影机调焦过程导致清晰肖像的起合点无法界定（相差超数秒），且失焦段内是否发生有效动作无法查证，严禁按清晰段外溢强赋 KEEP，必须保留 U。 
MD
+ 1


低清短动作类别存疑（如 W02 F29–F34 前身压低与爪位移动）	

可见身体前移与爪部微调，但图像证据无法证实是否属于有效训练展示、排便、抓挠或普通换姿态 
MD

	

有后果的 UNKNOWN（直接影响 KEEP/NO 判定） 
MD

	

动作类型决定其到底是趣味高光（KEEP）还是平淡过渡（NO），性质存疑直接改变最终标签集合，必须判定为阻断性 U。 
MD
+ 1

准入硬约束：只有当一个窗口内的所有事件边界均属于“有内外见证且定位误差 ≤0.5 秒的编辑决策边界”，且不存在任何跨切镜断裂、严重失焦或动作属性存疑的盲区时，该窗口才具备“无有后果 UNKNOWN”的银标资格。   
MD

疑问 2：无音频讲话的判定原则与 W10/W11 准入裁决

无音频讲话不能被机械默认判为 NO，更不能借此“造空”：
在本次 query-free 短视频高光剪辑定义下，虽然我们聚焦于视觉动作与核心展示，但视频的原生表达方式往往是多模态的。元数据审计已确证 AwmHb44_ouw 原片含有完整双声道 AAC 音轨（44.1kHz）。AGY 工具仅提供无声切片，且视频工具本身是 1fps 不透明采样。在人物面向镜头讲话（Talking head）长达 20 余秒的场景中，脱离音频无法判断其讲述的是关键操作机理说明、核心结论、还是完全无用的冗余废话。   
MD
+ 3

W11 必须拒收，严禁强推为合法 [] 银标：
在 W11 中，全窗自始至终（0.0s 至 23.59s）均为该男子讲话特写。教师声称全窗 NO，而盲审者如实将全窗标记为 U（03_AwmHb44_ouw_W11.independent_initial_blind_v1.json 中 initial_U_seconds_exact = 23.5866），且该窗口的有效视图独立审阅迄今仍处于未完成（PENDING）状态。
如果为了满足先导协议中的“至少产出 1 个完整银标”或为了平衡空窗配额，将 W11 强行采纳为合法 [] 目标，这不仅是在没有音频证据的情况下凭空假定其话语无价值，而且是典型的“为了开训选择性造空”。W11 必须拒收，不得作为先导通过窗口。   
MD
+ 4

疑问 3：最多 5 语法区间与已确认事件计数的关系

“已确认事件计数”与“连续编辑区间”不是同一层级，不得强行合并：
quality_contract.py 与 silver_contract.py 已经写死：模型推理生成必须遵循 B0 的 0 到 5 个区间的 JSON 语法（0 <= len(segments) <= 5）；同时 Pro slot6 明确冻结“超过 5 个应保留事件不可强行合并”。
这里的关系非常明确：   
MD
+ 2

事件层（Semantic Events）：是指具有独立起止、独立构图或主体动作的最小语义单元（如 W01 中的犬坐台阶、正面特写、栏杆露脸、眼鼻微距、下台阶跑等）。   
MD

区间层（Time Intervals in segments）：如果两个连续动作发生在同一镜头内且具有连续叙事因果（例如“小狗冲出门槛”衔接“小狗冲下台阶”），且中间没有任何 NO 或 U 间隔，它们可以在物理时间上构成一个连续的高光并集区间 [a,b]。   
MD
+ 1

禁止伪合并：如果多个事件被明确的 NO 或 U（例如长达数秒的无用持留或人物转身离场）在时间轴上物理切断，它们在时间轴上就是不相交的独立区间。绝不允许将跨越了 NO 或 U 的多个独立事件人为合并成一个大的宽泛区间，只为了把区间数压到 5 个以内；这样做会直接把被审查剔除的垃圾片段重新包装为高光喂给模型。   
MD
+ 3

W01 构成语法不可表达性阻断，非合同歧义：
在 W01 中，教师提议中即包含 6 个离散的 KEEP 事件（EV01, EV03, EV06, EV07, EV09, EV10），盲审更识别出 8 个分离的 KEEP 段落（S01, S03, S06, S08, S13, S16, S20, S22）。这些段落之间被清晰的无效静态持留（如 S04、S09、S11、S14、S18）和镜头切点硬性隔开。因此，W01 在不发生非法伪合并的前提下，合法 KEEP 区间数必然 ≥6>5。这属于被 silver_contract.py 第 31 行硬性拦截的样本（if len(record.get('events',[]))>5 or len(k)>5: raise ValueError(...)）。这不是合同歧义，而是该窗口内容密度超出了 8B 模型的单窗输出容量，必须作为整窗不入训样本处理。   
MD
+ 4

疑问 4：直接可见描述修正能否解决 W02 的未决未知？

更正事实描述是必要前提，但无法消除本征的语义未知：
主控将教师臆想的“倒地翻滚、排便清理、安详享受”等动机与假想动作修正为客观可见的“低机位草地、前身压低、前爪位移、侧卧”，这一修正完全正确，清除了虚假标签。
然而，“前身压低与爪位移动”（F29–F34）在去除虚构的“排便”外衣后，留下的事实是一段模糊的犬体态调整。在剪辑决策上，这样一段既非明确奔跑/衔取/跳跃等核心动作、又非高质量静止肖像的短小位移，到底应判定为 KEEP 还是 NO，在当前视觉采样下依然缺乏决定性依据。   
MD
+ 4

脱焦段与切镜断裂是物理性阻断，无法靠文本订正消除：
更严重的是 W02 中的 F25–F28（犬冲镜头大脱焦）与 F34–F41（摄影机拉焦模糊）。在这些段落中，画面主体处于严重散景模糊状态，连有效的边缘都无法建立。更正文字描述根本无法回答“清晰的肖像特写到底是从 19.75 秒开始还是从 21.65 秒开始”。此外，risk01 补查仅由主控抽检了 8 张，未完成 60 帧连续独立盲审。
因此，文字更正仅解决了“不被教师幻觉带偏”的问题，未能消除导致边界与决策摇摆的有后果 UNKNOWN，W02 当前依然只能保持部分 K/N/U，无法转为完整 SFT 银标。   
MD
+ 4

疑问 5：当前是否存在至少 1 个可诚实裁定的完整银标窗口？

事实结论：当前 4 个先导窗口中，合格可入训完整银标窗口数量严格为 0。

W01 (kLxoNp-UchI:SLOT6:1)：KEEP 事件数达 6~8 个，超出语法上限 5，且存在 F61 到 F62 的动作跨镜断裂，整窗 SFT 不可表达；   
MD
+ 1

W02 (kLxoNp-UchI:SLOT6:2)：含长达 11.41 秒的失焦、动作存疑及切点未决 U，risk01 补查未闭环，整窗不可入训；   
MD
+ 1

W10 (AwmHb44_ouw:SLOT6:10)：手部气门嘴操作结果未知，后半段 18.8 秒全为无声口述，存在 19.5 秒 U，整窗不可入训；   
MD
+ 1

W11 (AwmHb44_ouw:SLOT6:11)：全窗为无声口述，有效视图审阅尚在 pending，全域为 U，若判全空属于选择性造空，整窗不可入训。   
MD
+ 1

三、当前先导阶段裁决：执行协议 STOP

鉴于 frozen_protocol_v2_explicit_empty_gate.json 中明确规定 minimum_pilot_complete_silver: 1，而实际 4 个先导窗口在经过严密的盲审、有效视图对齐及主控事实校核后，合格完整银标窗口数量为 0。根据科学诚信原则：   
MD
+ 2

严禁为了强行跨过先导门而对 W11 选择性造空，严禁对 W01 进行跨镜头伪合并，严禁对 W02 进行失焦未知洗白。当前阶段必须诚实触发：STOP_PILOT_NO_VALID_COMPLETE_SILVER。

   
MD
+ 1

这不代表整个任务死亡，也不代表闭源模型无法工作；它如实反映了：在小狗室内外多镜头快速组接视频（kLxo）和中年男子无声修车解说视频（AwmHb）这两类复杂源媒体上，当前的粗粒度工具与稀疏抽样无法在零人工干预下自然闭环出无争议的完整窗口真值。   
MD
+ 1

四、有界信息购买出口与后续执行规约

依据 Pro slot6 预先批准的兜底条款（“本版停止后，只允许再做一次信息购买：从原 24 窗中固定选最多 4 窗，换取不同的实际观察证据；不新增来源，不追加第二次训练”）：   
MD

1. 有界信息购买出口规划（仅限原 24 窗内的 4 窗）

放弃在 AwmHb 的无声纯讲话长窗上浪费额度，从原预定训练集合中挑选 4 个视觉动作与操作结果更具实体性的候选窗口，购买具体缺失的事实证据：

kLxoNp-UchI:SLOT6:2 (W02)：执行 risk01 剩余 52 帧的完整独立盲态审阅，明确 R000–R059 中的切镜帧点，以及 F40 前后的对焦恢复第一清晰帧，查验能否将 W02 的 U 压减至工程公差内。   
MD
+ 1

37rzWOQsNIw:SLOT6:0（三明治/熟食店制作，原 train 来源，已有历史 18 个锚点核验基础）：购买基于食物制作手部明确操作动作与成品的 64 帧提案与双盲审阅。   
MD
+ 1

HT5vyqe0Xaw:SLOT6:2（工具/户外展示来源）：购买实体动作清晰段的双盲事实审阅。   
MD

WxtbjNsCQ8A:SLOT6:0（原计划训练组来源）：购买完整动作窗口的双盲审阅。   
MD

2. 严格执行边界与锁死项

不消耗 Pro slot7：本次仅为普通回合会诊，Pro slot 额度保持 6/8 已用、剩余 2 次，不提前消耗高阶额度。   
MD

不启动 GPU 训练：SFT 训练优化器更新次数严格保持为 0，Linux 训练端保持未动。   
MD

不打包、不提交 426：复赛包生成权限严格锁死，生产模型与交付基线唯一绑定历史安全包 candidate_SAFE_37_66.zip（SHA256: 07730c9e02e68d1a1ce54e7ef5a8aa616346cf8f2f8d78426ed36bc3eb481496）。   
MD

大文件传输阻断：196.56 MB 原生媒体向 Linux 端的跨主机传输在取得用户明确专项许可前继续挂起，严禁偷跑大流量。   
MD
+ 1

保留所有现场证据：包括 W11 的浮点微小表示偏差校正记录、W11 proposal 超白名单自读记录、所有失焦和切镜疑点记录，均永久保存在版本化目录中，作为后续决策的可审计凭证。   
MD
+ 1


## 完整新增公开记录 03_AwmHb44_ouw_W11.independent_student_view_review_v1.json
来源 G:\ai\AIC视频\reports\annotation_iteration_20261010\slot6_silver24_v1\blind_reviews\initial\03_AwmHb44_ouw_W11.independent_student_view_review_v1.json
字节 53376 SHA256 5dedac64801609e233ca4d4dad27a4834f8d4dfdfedaae19e1b729085c707dcf

{
  "schema": "independent_student_effective_view_blind_review_v1",
  "review_utc": "2026-10-10 06:50:30 UTC",
  "window_id": "AwmHb44_ouw:SLOT6:11",
  "prior_initial_review": {
    "path": "G:/ai/AIC视频/reports/annotation_iteration_20261010/slot6_silver24_v1/blind_reviews/initial/03_AwmHb44_ouw_W11.independent_initial_blind_v1.json",
    "sha256": "4f4f9a9b38340f778ac6347da26af2e4a3dda6818c373b9840824f118f039afa",
    "bytes_preserved": true
  },
  "student_processor_visibility_verified": true,
  "student_visibility_verification_scope": "ALL_64_ACTUAL_LOCAL_CPU_TENSOR_RECONSTRUCTED_PNGS_VISUALLY_READ; Linux processor execution not verified",
  "training_admitted": false,
  "full_native_frames_observed": false,
  "full_window_target_admitted": false,
  "blind_attestation": {
    "teacher_content_received": false,
    "teacher_files_read": false,
    "old_labels_or_scores_or_model_predictions_read": false,
    "network_model_GPU_used": false
  },
  "machine_receipt": {
    "path": "G:/ai/AIC视频/reports/annotation_iteration_20261010/slot6_silver24_v1/observations/03_AwmHb44_ouw_W11/student_views/receipt.json",
    "sha256": "49969b610d5b77df16d49300e61ea61c4e20f7293401a3ad7539af446cbfe37b",
    "status": "PASS_ACTUAL_LOCAL_CPU_NATIVE_PROCESSOR_TENSOR_VIEWS",
    "manifest_sha256": "a912670f4927a6500558243a0be966d2eb931e87bfda76f928ce27eae7036f91",
    "processor_binding_sha256": "272ab26a6dc9bbe42db40531eec316f91aed5f4073b6ab9d79a2aa80d1294c29",
    "runtime_sha256": "73f014e20034e0c61e9d57fe927ec7c69392f2d5f5e7a2f3f9f06ca6efa614b9",
    "decoder_sha256": "7b79a6713e3a406d015bc546fc45ce6172b7cf8d3967592779bfdd8c23a6fe09",
    "normalized_tensor_sha256": "092acc372d136743d0d9c61453ac4a3c7b4b1356810de970c93696a5647c425b",
    "actual_tensor_shape": [
      23936,
      1536
    ],
    "video_grid_thw": [
      [
        32,
        22,
        34
      ]
    ],
    "patch_inverse_exact": true,
    "torch_version": "2.5.1+cpu",
    "transformers_version": "4.57.1",
    "linux_execution": false,
    "new_model_calls": 0,
    "new_optimizer_updates": 0,
    "rendered_view": "Inverse patch rearrangement, inverse normalization, rounded uint8 PNG. Display reconstruction; normalized model tensor SHA bound separately."
  },
  "actual_viewing": {
    "frames": 64,
    "batches": 16,
    "batch_size": 4,
    "all_png_sha_match_receipt": true,
    "all_source_ordinals_and_exact_PTS_match_initial_manifest": true,
    "width": 544,
    "height": 352
  },
  "visibility_changes_and_learnability": "544x352有效显示全窗人物面部、嘴型与眼睑变化可辨，无新的手势/工具/结果。实际视图不提供声音或语言内容，整窗讲述意义U不变，不自动NO。",
  "K_NO_U_changed": false,
  "label_changes": [],
  "retained_segments": [
    {
      "segment_id": "S01",
      "label": "U",
      "global_seconds_exact": [
        "330",
        "35358656666666667/100000000000000"
      ],
      "title": "全窗连续人物近景的讲述意义",
      "visual_reason_or_unknown": "所有样本都是同一户外人物面部近景，嘴型与眼睑变化；没有音频/转录，是否包含必须保留的解释/结论无法判断。未见独立手势、工具操作、新物体或显著构图变化；不据此默认NO。",
      "evidence_frames": [
        "F00",
        "F01",
        "F02",
        "F03",
        "F04",
        "F05",
        "F06",
        "F07",
        "F08",
        "F09",
        "F10",
        "F11",
        "F12",
        "F13",
        "F14",
        "F15",
        "F16",
        "F17",
        "F18",
        "F19",
        "F20",
        "F21",
        "F22",
        "F23",
        "F24",
        "F25",
        "F26",
        "F27",
        "F28",
        "F29",
        "F30",
        "F31",
        "F32",
        "F33",
        "F34",
        "F35",
        "F36",
        "F37",
        "F38",
        "F39",
        "F40",
        "F41",
        "F42",
        "F43",
        "F44",
        "F45",
        "F46",
        "F47",
        "F48",
        "F49",
        "F50",
        "F51",
        "F52",
        "F53",
        "F54",
        "F55",
        "F56",
        "F57",
        "F58",
        "F59",
        "F60",
        "F61",
        "F62",
        "F63"
      ]
    }
  ],
  "unresolved_for_full_window": {
    "frames": [
      "F00",
      "F01",
      "F02",
      "F03",
      "F04",
      "F05",
      "F06",
      "F07",
      "F08",
      "F09",
      "F10",
      "F11",
      "F12",
      "F13",
      "F14",
      "F15",
      "F16",
      "F17",
      "F18",
      "F19",
      "F20",
      "F21",
      "F22",
      "F23",
      "F24",
      "F25",
      "F26",
      "F27",
      "F28",
      "F29",
      "F30",
      "F31",
      "F32",
      "F33",
      "F34",
      "F35",
      "F36",
      "F37",
      "F38",
      "F39",
      "F40",
      "F41",
      "F42",
      "F43",
      "F44",
      "F45",
      "F46",
      "F47",
      "F48",
      "F49",
      "F50",
      "F51",
      "F52",
      "F53",
      "F54",
      "F55",
      "F56",
      "F57",
      "F58",
      "F59",
      "F60",
      "F61",
      "F62",
      "F63"
    ],
    "issue": "全窗讲述意义缺本轮音频证据；可观察口型不等于知道语言内容，整窗U未解决。影响完整窗口目标。",
    "affects_full_window_target": true
  },
  "limitations": [
    "有效视图是inverse patch及inverse normalization后round uint8的显示重构；不能把PNG字节等同于归一化model tensor。tensor SHA与机器回执独立绑定。",
    "所有64采样视图已看，但完整native帧未看，具体切点和识别不清事件保留U。",
    "processor文件SHA与Linux实际元数据回执绑定，不证明Linux已经运行相同processor。",
    "可见性通过不等于训练准入、金标或冻结完整窗口目标。"
  ],
  "student_view_inventory": [
    {
      "frame_id": "F00",
      "source_ordinal": 9891,
      "global_seconds_exact": "3300297/10000",
      "local_seconds_exact": "297/10000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F00_student.png",
      "png_sha256": "66fb27dfec26b45b7829bebd6f71f5f12f43e1c2e5ccea334dafee161eeca2f0",
      "rgb_pixel_sha256": "02171cdf38823d2b9d8a88224743a235abe31dd8d2fcc70ce94631208f28d091",
      "actual_png_sha256": "66fb27dfec26b45b7829bebd6f71f5f12f43e1c2e5ccea334dafee161eeca2f0",
      "actual_view_image_read": true,
      "read_batch": 1,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F01",
      "source_ordinal": 9902,
      "global_seconds_exact": "4955951/15000",
      "local_seconds_exact": "5951/15000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F01_student.png",
      "png_sha256": "31746e45ad469b28a9f37d0c8751fd92b9c1a175fe5ec081b47c2f6eb75ddcc7",
      "rgb_pixel_sha256": "184253d7c6b298d69eab405430b50340a206c1b3b01034fa536950bc55e83b38",
      "actual_png_sha256": "31746e45ad469b28a9f37d0c8751fd92b9c1a175fe5ec081b47c2f6eb75ddcc7",
      "actual_view_image_read": true,
      "read_batch": 1,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F02",
      "source_ordinal": 9913,
      "global_seconds_exact": "9922913/30000",
      "local_seconds_exact": "22913/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F02_student.png",
      "png_sha256": "7e07a330b0b17c16a3359ff6fccc9a7c2415d8efe64ff874e8e8942755c0e9d4",
      "rgb_pixel_sha256": "edf5e674c5b662b1f95a5efb4d4f2adf5c7356babc4c9cfed552681dacd52673",
      "actual_png_sha256": "7e07a330b0b17c16a3359ff6fccc9a7c2415d8efe64ff874e8e8942755c0e9d4",
      "actual_view_image_read": true,
      "read_batch": 1,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F03",
      "source_ordinal": 9924,
      "global_seconds_exact": "827827/2500",
      "local_seconds_exact": "2827/2500",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F03_student.png",
      "png_sha256": "09460779a14d28963c53608eaf9e39c1d3adbcd1f47ede6369e7e68d75e6888a",
      "rgb_pixel_sha256": "27c915d38d93eb478ff7be4ab3fdb93d7a774f60c648c6689b5c9905af5dd608",
      "actual_png_sha256": "09460779a14d28963c53608eaf9e39c1d3adbcd1f47ede6369e7e68d75e6888a",
      "actual_view_image_read": true,
      "read_batch": 1,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F04",
      "source_ordinal": 9935,
      "global_seconds_exact": "1988987/6000",
      "local_seconds_exact": "8987/6000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F04_student.png",
      "png_sha256": "04cabb8eb53f10c164ef09827903681cdbf03acaee25279eac1f116230ffdd54",
      "rgb_pixel_sha256": "2979311eaf899c0cd3defa1e78417a5cb575c0b2a6b1baeb75c44fb118559d89",
      "actual_png_sha256": "04cabb8eb53f10c164ef09827903681cdbf03acaee25279eac1f116230ffdd54",
      "actual_view_image_read": true,
      "read_batch": 2,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F05",
      "source_ordinal": 9946,
      "global_seconds_exact": "4977973/15000",
      "local_seconds_exact": "27973/15000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F05_student.png",
      "png_sha256": "1b175640467123467b15614895cc93cca09d3d32d44ddfac0486578ba624c19f",
      "rgb_pixel_sha256": "e92d57bd8783099ed3ecadf53500186ab405ad04e4c131af0fd9b3718c7ba9a3",
      "actual_png_sha256": "1b175640467123467b15614895cc93cca09d3d32d44ddfac0486578ba624c19f",
      "actual_view_image_read": true,
      "read_batch": 2,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F06",
      "source_ordinal": 9958,
      "global_seconds_exact": "4983979/15000",
      "local_seconds_exact": "33979/15000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F06_student.png",
      "png_sha256": "c0918dba55b960ab1201e5ecc2946afceeb46e58a58ebe726a57af5c81428dda",
      "rgb_pixel_sha256": "a7e85d19a5d8fc267c49d15a0457018cb88d89ddfab753e67a90a0990e39a481",
      "actual_png_sha256": "c0918dba55b960ab1201e5ecc2946afceeb46e58a58ebe726a57af5c81428dda",
      "actual_view_image_read": true,
      "read_batch": 2,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F07",
      "source_ordinal": 9969,
      "global_seconds_exact": "3326323/10000",
      "local_seconds_exact": "26323/10000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F07_student.png",
      "png_sha256": "f1131c5a1d76176eb8f6678c2f0d976e2f353aa1b4aa19687c6758dd7fcb078a",
      "rgb_pixel_sha256": "3ceb84700469132e1108c5d7acecb398aa7e7046c7cf3a82ac8d1cc21b0e796c",
      "actual_png_sha256": "f1131c5a1d76176eb8f6678c2f0d976e2f353aa1b4aa19687c6758dd7fcb078a",
      "actual_view_image_read": true,
      "read_batch": 2,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F08",
      "source_ordinal": 9980,
      "global_seconds_exact": "499499/1500",
      "local_seconds_exact": "4499/1500",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F08_student.png",
      "png_sha256": "fead7e19c0b033e1cdc18270054dfe2dbcf7295525318f7eedf31789c13938f5",
      "rgb_pixel_sha256": "a8e51031f420f57a51d634ad95eea16bd8b0ec3edeb791764e12faa44cd96e5b",
      "actual_png_sha256": "fead7e19c0b033e1cdc18270054dfe2dbcf7295525318f7eedf31789c13938f5",
      "actual_view_image_read": true,
      "read_batch": 3,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F09",
      "source_ordinal": 9991,
      "global_seconds_exact": "10000991/30000",
      "local_seconds_exact": "100991/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F09_student.png",
      "png_sha256": "8b8be29dc2cc88aed3d7cac40d0a94d731a50ec02eed58c0ea545eace7c48367",
      "rgb_pixel_sha256": "6dad40094df310e75ad28b3fa8e54146e8fa0c8630de7efe672acf569c100736",
      "actual_png_sha256": "8b8be29dc2cc88aed3d7cac40d0a94d731a50ec02eed58c0ea545eace7c48367",
      "actual_view_image_read": true,
      "read_batch": 3,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F10",
      "source_ordinal": 10002,
      "global_seconds_exact": "1668667/5000",
      "local_seconds_exact": "18667/5000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F10_student.png",
      "png_sha256": "956f1106dac39ff2b2b29b5e9f28538191c693cfa1a6f3c12d1f45af7d924a86",
      "rgb_pixel_sha256": "51b3e24cea71682a5812285c4afbb70d9085837ef5d403a9852699869d2775b8",
      "actual_png_sha256": "956f1106dac39ff2b2b29b5e9f28538191c693cfa1a6f3c12d1f45af7d924a86",
      "actual_view_image_read": true,
      "read_batch": 3,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F11",
      "source_ordinal": 10014,
      "global_seconds_exact": "1670669/5000",
      "local_seconds_exact": "20669/5000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F11_student.png",
      "png_sha256": "eca1cb392da563cce056ce9d8345cd2f58159ff9f435898716ca78e6f3308ee1",
      "rgb_pixel_sha256": "c96edc4d835dcd9919be31c9b052e34ac43417aa401083b46446cc2baef40dce",
      "actual_png_sha256": "eca1cb392da563cce056ce9d8345cd2f58159ff9f435898716ca78e6f3308ee1",
      "actual_view_image_read": true,
      "read_batch": 3,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F12",
      "source_ordinal": 10025,
      "global_seconds_exact": "401401/1200",
      "local_seconds_exact": "5401/1200",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F12_student.png",
      "png_sha256": "e89cc74179efed5e507ef8c8b8e0739ad5deea5bef4beffeab22a67f06e8bb6f",
      "rgb_pixel_sha256": "239ef36405359118315c83fb63d8ce4b989b10ca156ae049036ec38dbc1d2cd6",
      "actual_png_sha256": "e89cc74179efed5e507ef8c8b8e0739ad5deea5bef4beffeab22a67f06e8bb6f",
      "actual_view_image_read": true,
      "read_batch": 4,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F13",
      "source_ordinal": 10036,
      "global_seconds_exact": "2511509/7500",
      "local_seconds_exact": "36509/7500",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F13_student.png",
      "png_sha256": "56d67cf24bbbd97b7120a29c58aba4fb2a66a6bb9a6b37e832466620f8d99775",
      "rgb_pixel_sha256": "aea5c69f5a676a6515e71dca5e86f8438c1be40b70855403d8f33b54bcb30955",
      "actual_png_sha256": "56d67cf24bbbd97b7120a29c58aba4fb2a66a6bb9a6b37e832466620f8d99775",
      "actual_view_image_read": true,
      "read_batch": 4,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F14",
      "source_ordinal": 10047,
      "global_seconds_exact": "3352349/10000",
      "local_seconds_exact": "52349/10000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F14_student.png",
      "png_sha256": "d89cab65da639b8329f522ebfb1bd44b1863178bed6a4d660674607d2ca2590c",
      "rgb_pixel_sha256": "e1a48b780809c518e54fd46680b06e689b84484725e4e9715ae7a954d6a8ccb9",
      "actual_png_sha256": "d89cab65da639b8329f522ebfb1bd44b1863178bed6a4d660674607d2ca2590c",
      "actual_view_image_read": true,
      "read_batch": 4,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F15",
      "source_ordinal": 10058,
      "global_seconds_exact": "5034029/15000",
      "local_seconds_exact": "84029/15000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F15_student.png",
      "png_sha256": "660fcc02e5922a24098e9b55e347be75e1a21cb9a0bdb52a5031d66476c61194",
      "rgb_pixel_sha256": "c5ac253957604ed504a4f2b3113d3e837191816a88f81d0980f035b9705fdf94",
      "actual_png_sha256": "660fcc02e5922a24098e9b55e347be75e1a21cb9a0bdb52a5031d66476c61194",
      "actual_view_image_read": true,
      "read_batch": 4,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F16",
      "source_ordinal": 10070,
      "global_seconds_exact": "1008007/3000",
      "local_seconds_exact": "18007/3000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F16_student.png",
      "png_sha256": "0e15f1de53226520391b19a85e27e876f123da88fc8e74fd402415ccde52c7b9",
      "rgb_pixel_sha256": "56df0cfeb6283b0066afad877c8796e2753529f0a691772be622d96f93cb89cf",
      "actual_png_sha256": "0e15f1de53226520391b19a85e27e876f123da88fc8e74fd402415ccde52c7b9",
      "actual_view_image_read": true,
      "read_batch": 5,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F17",
      "source_ordinal": 10081,
      "global_seconds_exact": "10091081/30000",
      "local_seconds_exact": "191081/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F17_student.png",
      "png_sha256": "1f588af14c8176687476aab2156e35c9bc9c9ca44633b03aef8b9bdbadc28b2e",
      "rgb_pixel_sha256": "11f2af718f7ab791295678dde6f31091721eff49a45c9d15d7d062816406c4c6",
      "actual_png_sha256": "1f588af14c8176687476aab2156e35c9bc9c9ca44633b03aef8b9bdbadc28b2e",
      "actual_view_image_read": true,
      "read_batch": 5,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F18",
      "source_ordinal": 10092,
      "global_seconds_exact": "841841/2500",
      "local_seconds_exact": "16841/2500",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F18_student.png",
      "png_sha256": "35ac725b9612bd29faa546f8168859f437b74bb77e698e7f7e711d8ad8b6b917",
      "rgb_pixel_sha256": "4bcde8da1f6378d4fb267cf6142cf4e4abe33fd11c0a35ac5ab94ad8f0d8aedb",
      "actual_png_sha256": "35ac725b9612bd29faa546f8168859f437b74bb77e698e7f7e711d8ad8b6b917",
      "actual_view_image_read": true,
      "read_batch": 5,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F19",
      "source_ordinal": 10103,
      "global_seconds_exact": "10113103/30000",
      "local_seconds_exact": "213103/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F19_student.png",
      "png_sha256": "924c12b0828428c69eb21b99289cd3965d34bde6dfadc8a82a82706c3c6651dc",
      "rgb_pixel_sha256": "d12b19ec387f88e2f9421b0c9e33a3519fc1b073283bb5c689f7bde392f59a61",
      "actual_png_sha256": "924c12b0828428c69eb21b99289cd3965d34bde6dfadc8a82a82706c3c6651dc",
      "actual_view_image_read": true,
      "read_batch": 5,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F20",
      "source_ordinal": 10114,
      "global_seconds_exact": "5062057/15000",
      "local_seconds_exact": "112057/15000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F20_student.png",
      "png_sha256": "62539781b649b2258ae699229e611eaa3a16492db579fc97d2eadd790119f8d0",
      "rgb_pixel_sha256": "2c0de121d93bbced098b0e976346df63f4d057ec42db34709aedd2cd39b32c6c",
      "actual_png_sha256": "62539781b649b2258ae699229e611eaa3a16492db579fc97d2eadd790119f8d0",
      "actual_view_image_read": true,
      "read_batch": 6,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F21",
      "source_ordinal": 10126,
      "global_seconds_exact": "5068063/15000",
      "local_seconds_exact": "118063/15000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F21_student.png",
      "png_sha256": "0090ac4dd013c98bdc7d6aaf4ac652176e948012b9637b4b16cc78eab6d478e0",
      "rgb_pixel_sha256": "599c7e0d1c3689da54399871c2b06e119a884225b635d90d7ca8030761168f51",
      "actual_png_sha256": "0090ac4dd013c98bdc7d6aaf4ac652176e948012b9637b4b16cc78eab6d478e0",
      "actual_view_image_read": true,
      "read_batch": 6,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F22",
      "source_ordinal": 10137,
      "global_seconds_exact": "3382379/10000",
      "local_seconds_exact": "82379/10000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F22_student.png",
      "png_sha256": "0b9e266f084979bb4da9ab8df14b82ad7ca5620060b8a5ff7a2c118d794e125c",
      "rgb_pixel_sha256": "018ceb0bce251fa043fe8d7595c5cce2b28d6cbae89c8e34f869a4130477813d",
      "actual_png_sha256": "0b9e266f084979bb4da9ab8df14b82ad7ca5620060b8a5ff7a2c118d794e125c",
      "actual_view_image_read": true,
      "read_batch": 6,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F23",
      "source_ordinal": 10148,
      "global_seconds_exact": "2539537/7500",
      "local_seconds_exact": "64537/7500",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F23_student.png",
      "png_sha256": "e07784c486a6cf98bdd420523cc8c280b07b9450d0a0827a89a49489af5e6c22",
      "rgb_pixel_sha256": "2e45ff2b7f2195f0f24b92b6dd8e0a4f3525438b08330cc5cbbc93b965c047f1",
      "actual_png_sha256": "e07784c486a6cf98bdd420523cc8c280b07b9450d0a0827a89a49489af5e6c22",
      "actual_view_image_read": true,
      "read_batch": 6,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F24",
      "source_ordinal": 10159,
      "global_seconds_exact": "10169159/30000",
      "local_seconds_exact": "269159/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F24_student.png",
      "png_sha256": "97ff268bf15981a690cebc762a4a19345bea21641fda70010e79a1a712f850d0",
      "rgb_pixel_sha256": "3fa8e397192d5d2c1b34a088135f60f4ec450c309057957c30055a243ab9bc91",
      "actual_png_sha256": "97ff268bf15981a690cebc762a4a19345bea21641fda70010e79a1a712f850d0",
      "actual_view_image_read": true,
      "read_batch": 7,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F25",
      "source_ordinal": 10170,
      "global_seconds_exact": "339339/1000",
      "local_seconds_exact": "9339/1000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F25_student.png",
      "png_sha256": "cb04f22d33250f751bbd006cd3890089187d5addf84f5c3696896624d0947b1c",
      "rgb_pixel_sha256": "8cee8d6c87d7905526f598b06aee4b1025db25dc4461d3db0f4e8f5909deaea0",
      "actual_png_sha256": "cb04f22d33250f751bbd006cd3890089187d5addf84f5c3696896624d0947b1c",
      "actual_view_image_read": true,
      "read_batch": 7,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F26",
      "source_ordinal": 10181,
      "global_seconds_exact": "10191181/30000",
      "local_seconds_exact": "291181/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F26_student.png",
      "png_sha256": "79c1eab874a921b3fd4ac0722872845e666f3c590cf04bf6cc48b4019ed2b4bd",
      "rgb_pixel_sha256": "f5827da44a1f9af9dd4797180f9cddf9db46891b6c66b1c3aab53680b27f60ce",
      "actual_png_sha256": "79c1eab874a921b3fd4ac0722872845e666f3c590cf04bf6cc48b4019ed2b4bd",
      "actual_view_image_read": true,
      "read_batch": 7,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F27",
      "source_ordinal": 10193,
      "global_seconds_exact": "10203193/30000",
      "local_seconds_exact": "303193/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F27_student.png",
      "png_sha256": "560dcfe5a87fabc1f5175c6dbf6fbe58ff0b08034b806fe729770a3d3c55b19e",
      "rgb_pixel_sha256": "4effb625854767b537127239fb484d2c1b941ea8a7deb75ae7f89802a4c0116d",
      "actual_png_sha256": "560dcfe5a87fabc1f5175c6dbf6fbe58ff0b08034b806fe729770a3d3c55b19e",
      "actual_view_image_read": true,
      "read_batch": 7,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F28",
      "source_ordinal": 10204,
      "global_seconds_exact": "2553551/7500",
      "local_seconds_exact": "78551/7500",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F28_student.png",
      "png_sha256": "bf67ce400a942a59dff1bb3708417cce734168c401b30e50cc3c8475e70cae65",
      "rgb_pixel_sha256": "f8fedfaa76756a1088af77e83176023a0cc0e2d7299c0f23bd2e701367555569",
      "actual_png_sha256": "bf67ce400a942a59dff1bb3708417cce734168c401b30e50cc3c8475e70cae65",
      "actual_view_image_read": true,
      "read_batch": 8,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F29",
      "source_ordinal": 10215,
      "global_seconds_exact": "681681/2000",
      "local_seconds_exact": "21681/2000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F29_student.png",
      "png_sha256": "cf68465cb71880913615ba351473824b043a21ab7e67fc93ea5d37d1e5d96754",
      "rgb_pixel_sha256": "e977489a9664e7835fa151f58334479a230cfed5f52a3fc0f639a276f023efb1",
      "actual_png_sha256": "cf68465cb71880913615ba351473824b043a21ab7e67fc93ea5d37d1e5d96754",
      "actual_view_image_read": true,
      "read_batch": 8,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F30",
      "source_ordinal": 10226,
      "global_seconds_exact": "5118113/15000",
      "local_seconds_exact": "168113/15000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F30_student.png",
      "png_sha256": "9a6efe5f39c6995243f3371b1cdd1e118fe370aebebc7ccea16f2abfa1cda57d",
      "rgb_pixel_sha256": "f09d45f35a44c7aa6375796ca5c8c9d6d10f14aa85c5e71354738d651bcfb3fa",
      "actual_png_sha256": "9a6efe5f39c6995243f3371b1cdd1e118fe370aebebc7ccea16f2abfa1cda57d",
      "actual_view_image_read": true,
      "read_batch": 8,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F31",
      "source_ordinal": 10237,
      "global_seconds_exact": "10247237/30000",
      "local_seconds_exact": "347237/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F31_student.png",
      "png_sha256": "c52c45aa5d69cfadc5e53e0d1012c8368aebad9f839777de325f5b909042740b",
      "rgb_pixel_sha256": "78c577db830f77ec3949d3c29ce953f9dfbe6b8eb2906cfac86cd2f321cc9211",
      "actual_png_sha256": "c52c45aa5d69cfadc5e53e0d1012c8368aebad9f839777de325f5b909042740b",
      "actual_view_image_read": true,
      "read_batch": 8,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F32",
      "source_ordinal": 10249,
      "global_seconds_exact": "10259249/30000",
      "local_seconds_exact": "359249/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F32_student.png",
      "png_sha256": "26b701d76d96c918c4175cae5aed3cb02ab84ac340c8fd866328e6d3db0672fe",
      "rgb_pixel_sha256": "bf97c20e07a1a32efcd3e52ead864c84b8830c3acf4a0748a430f982aa2083c9",
      "actual_png_sha256": "26b701d76d96c918c4175cae5aed3cb02ab84ac340c8fd866328e6d3db0672fe",
      "actual_view_image_read": true,
      "read_batch": 9,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F33",
      "source_ordinal": 10260,
      "global_seconds_exact": "171171/500",
      "local_seconds_exact": "6171/500",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F33_student.png",
      "png_sha256": "593e53645e495eabbd4596741acbf25f171edaf2cc3804e564ca20041bc1fd18",
      "rgb_pixel_sha256": "b140423528b6891d707c3cbb1209453db575b12499da5d33018841c94671cc64",
      "actual_png_sha256": "593e53645e495eabbd4596741acbf25f171edaf2cc3804e564ca20041bc1fd18",
      "actual_view_image_read": true,
      "read_batch": 9,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F34",
      "source_ordinal": 10271,
      "global_seconds_exact": "10281271/30000",
      "local_seconds_exact": "381271/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F34_student.png",
      "png_sha256": "763b3026af82b24df332407190e7777913380077c8c39b2fec7426a716929827",
      "rgb_pixel_sha256": "533c01a80d5f28441202611245eee96e3cbb74300459967392ce888b8e002b62",
      "actual_png_sha256": "763b3026af82b24df332407190e7777913380077c8c39b2fec7426a716929827",
      "actual_view_image_read": true,
      "read_batch": 9,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F35",
      "source_ordinal": 10282,
      "global_seconds_exact": "5146141/15000",
      "local_seconds_exact": "196141/15000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F35_student.png",
      "png_sha256": "0709e7b3193a952d218767e7ed367e17f1ad9266aee41496af75056a098d0c2f",
      "rgb_pixel_sha256": "72af616596aea94e78a8ae201cf56a43756dc97e51ee7937ff889ffa0ab3e582",
      "actual_png_sha256": "0709e7b3193a952d218767e7ed367e17f1ad9266aee41496af75056a098d0c2f",
      "actual_view_image_read": true,
      "read_batch": 9,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F36",
      "source_ordinal": 10293,
      "global_seconds_exact": "3434431/10000",
      "local_seconds_exact": "134431/10000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F36_student.png",
      "png_sha256": "6226ff1ac27ee5f2c89aaf72af3aaba1fff0e83b5481e81ff20659622f18b97e",
      "rgb_pixel_sha256": "7d9d3a052b21210267888d54b2894d5c05c795a2effa7a79ff15bab4b0ae415f",
      "actual_png_sha256": "6226ff1ac27ee5f2c89aaf72af3aaba1fff0e83b5481e81ff20659622f18b97e",
      "actual_view_image_read": true,
      "read_batch": 10,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F37",
      "source_ordinal": 10305,
      "global_seconds_exact": "687687/2000",
      "local_seconds_exact": "27687/2000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F37_student.png",
      "png_sha256": "872f455dc4e779ba23c1195521d1f6cf11fd0a9f2d63fdb1bae6d8665266030c",
      "rgb_pixel_sha256": "0feca478a6a416efb6937dcf204a24588adf3f1df042e304642d7bf2724e473f",
      "actual_png_sha256": "872f455dc4e779ba23c1195521d1f6cf11fd0a9f2d63fdb1bae6d8665266030c",
      "actual_view_image_read": true,
      "read_batch": 10,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F38",
      "source_ordinal": 10316,
      "global_seconds_exact": "2581579/7500",
      "local_seconds_exact": "106579/7500",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F38_student.png",
      "png_sha256": "1d54a27425c229b76e02275548f4506b6b828c21138f13046559547d902e1bfb",
      "rgb_pixel_sha256": "91f2514dbf529da8478bee63565865be437fd994a17feba9164b4958de4393bf",
      "actual_png_sha256": "1d54a27425c229b76e02275548f4506b6b828c21138f13046559547d902e1bfb",
      "actual_view_image_read": true,
      "read_batch": 10,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F39",
      "source_ordinal": 10327,
      "global_seconds_exact": "10337327/30000",
      "local_seconds_exact": "437327/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F39_student.png",
      "png_sha256": "2858c9b28a8c723f1c3910f6687d9f70f924743e3fe60dd8bdcb9aefa7d24687",
      "rgb_pixel_sha256": "d83a19111da6b4bc4571bbefddeeb9fe63128de9443ef43613a8c172155b589e",
      "actual_png_sha256": "2858c9b28a8c723f1c3910f6687d9f70f924743e3fe60dd8bdcb9aefa7d24687",
      "actual_view_image_read": true,
      "read_batch": 10,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F40",
      "source_ordinal": 10338,
      "global_seconds_exact": "1724723/5000",
      "local_seconds_exact": "74723/5000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F40_student.png",
      "png_sha256": "32f361bd29485641ce4116047024e64df6a95c7da10da9e6e8b8227af3ecdbde",
      "rgb_pixel_sha256": "f46afc53cf67174a1d34786f208ee218d0b5db31cc967d82b3c1cef80515ff8c",
      "actual_png_sha256": "32f361bd29485641ce4116047024e64df6a95c7da10da9e6e8b8227af3ecdbde",
      "actual_view_image_read": true,
      "read_batch": 11,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F41",
      "source_ordinal": 10349,
      "global_seconds_exact": "10359349/30000",
      "local_seconds_exact": "459349/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F41_student.png",
      "png_sha256": "d0ed5b226037f067faa2819058aede8587157d9b3ccb282d0112d2ebf6fb86d1",
      "rgb_pixel_sha256": "8bb7f464cfce809c7e0d220ccaff25657f8c3d81acdd45630e18fedc97cbe394",
      "actual_png_sha256": "d0ed5b226037f067faa2819058aede8587157d9b3ccb282d0112d2ebf6fb86d1",
      "actual_view_image_read": true,
      "read_batch": 11,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F42",
      "source_ordinal": 10361,
      "global_seconds_exact": "10371361/30000",
      "local_seconds_exact": "471361/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F42_student.png",
      "png_sha256": "9c9ec93bae67c077d8858b06a9ba5773f20f894f57cc7154d9c520946d4bff5c",
      "rgb_pixel_sha256": "3256bb8689e6f507ac3afe22aeffde22a7b84867d5a47a4cff3a895f80a3abe8",
      "actual_png_sha256": "9c9ec93bae67c077d8858b06a9ba5773f20f894f57cc7154d9c520946d4bff5c",
      "actual_view_image_read": true,
      "read_batch": 11,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F43",
      "source_ordinal": 10372,
      "global_seconds_exact": "2595593/7500",
      "local_seconds_exact": "120593/7500",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F43_student.png",
      "png_sha256": "777d9dec897e8ef31ab9141e6b887d8be0509fb081c1d8682166bd44a53862df",
      "rgb_pixel_sha256": "c1614cb93b8e205f8ea7b432a0b1e6a92fdb1813f5e8dc37ba59ffbe5cb18a0c",
      "actual_png_sha256": "777d9dec897e8ef31ab9141e6b887d8be0509fb081c1d8682166bd44a53862df",
      "actual_view_image_read": true,
      "read_batch": 11,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F44",
      "source_ordinal": 10383,
      "global_seconds_exact": "3464461/10000",
      "local_seconds_exact": "164461/10000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F44_student.png",
      "png_sha256": "f4955b6c0e72dd335615df53cc787d702f51ea8016febdf35ce60659147aac34",
      "rgb_pixel_sha256": "9d7d07cbbb6321c51ab8fb9a2c7e761b9d41c564a774bbf8f9b924019b5c3113",
      "actual_png_sha256": "f4955b6c0e72dd335615df53cc787d702f51ea8016febdf35ce60659147aac34",
      "actual_view_image_read": true,
      "read_batch": 12,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F45",
      "source_ordinal": 10394,
      "global_seconds_exact": "5202197/15000",
      "local_seconds_exact": "252197/15000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F45_student.png",
      "png_sha256": "da7ed79b60b0f84157b39f8f59508fe83a3dc2a2f99b033c5fa670a32b999ade",
      "rgb_pixel_sha256": "c24c0ae282dc5b5698579812ac938acea08919a077f06c1771cba21fd3d04202",
      "actual_png_sha256": "da7ed79b60b0f84157b39f8f59508fe83a3dc2a2f99b033c5fa670a32b999ade",
      "actual_view_image_read": true,
      "read_batch": 12,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F46",
      "source_ordinal": 10405,
      "global_seconds_exact": "2083081/6000",
      "local_seconds_exact": "103081/6000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F46_student.png",
      "png_sha256": "994f6abe6e0e40476efc277de4f9fca2bb0a01e1d4fbef91d8f74d741acc2f59",
      "rgb_pixel_sha256": "03de6f30c5fd8a5181a6e079dc58d66e572fc05ba23b615ed7ab9c8dfbda07bf",
      "actual_png_sha256": "994f6abe6e0e40476efc277de4f9fca2bb0a01e1d4fbef91d8f74d741acc2f59",
      "actual_view_image_read": true,
      "read_batch": 12,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F47",
      "source_ordinal": 10416,
      "global_seconds_exact": "217217/625",
      "local_seconds_exact": "10967/625",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F47_student.png",
      "png_sha256": "f0f8c0a7887e83e4a1a2d163351336d98379ac5d6215a490e579148e4dd53b75",
      "rgb_pixel_sha256": "81ce2e9e60f8108d92ca089ef019c7143bef0f42deebab02eecb498dc976281c",
      "actual_png_sha256": "f0f8c0a7887e83e4a1a2d163351336d98379ac5d6215a490e579148e4dd53b75",
      "actual_view_image_read": true,
      "read_batch": 12,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F48",
      "source_ordinal": 10428,
      "global_seconds_exact": "869869/2500",
      "local_seconds_exact": "44869/2500",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F48_student.png",
      "png_sha256": "b164d6da5c4e64b6e3a2e7bd6a7ea41c29d546c22e74731ce448a8a6c433140f",
      "rgb_pixel_sha256": "e5c01f9d8fbbcd96e387b45ebac4c4be1b329b01ae804406186851937c7e6b09",
      "actual_png_sha256": "b164d6da5c4e64b6e3a2e7bd6a7ea41c29d546c22e74731ce448a8a6c433140f",
      "actual_view_image_read": true,
      "read_batch": 13,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F49",
      "source_ordinal": 10439,
      "global_seconds_exact": "10449439/30000",
      "local_seconds_exact": "549439/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F49_student.png",
      "png_sha256": "19287fb2748d6cbfdb511af8539a05e477c1b06b64a2818a314cb6c051e24a5c",
      "rgb_pixel_sha256": "5c79a414e49501ebb085d387dc190d2d4c93dd8f6aa55d20ed5bb134d018575d",
      "actual_png_sha256": "19287fb2748d6cbfdb511af8539a05e477c1b06b64a2818a314cb6c051e24a5c",
      "actual_view_image_read": true,
      "read_batch": 13,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F50",
      "source_ordinal": 10450,
      "global_seconds_exact": "209209/600",
      "local_seconds_exact": "11209/600",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F50_student.png",
      "png_sha256": "9820345b1704cd37dbd231f33958a03495f8bb2a29ef9afa571b0354ec1e5912",
      "rgb_pixel_sha256": "db3dd32efb43190d2409fa4350b925cf5f64e51cd22b304b873e6bb05003420c",
      "actual_png_sha256": "9820345b1704cd37dbd231f33958a03495f8bb2a29ef9afa571b0354ec1e5912",
      "actual_view_image_read": true,
      "read_batch": 13,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F51",
      "source_ordinal": 10461,
      "global_seconds_exact": "3490487/10000",
      "local_seconds_exact": "190487/10000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F51_student.png",
      "png_sha256": "c14143ece417ff52edd6918b333ffe0f7c71941dcce8b0a8da0ff38d5e1a6ae6",
      "rgb_pixel_sha256": "1d9d0dc8d4fbb67d8e0144c25aa1c43a5ef56a9e59f3037c02b1d294d2e67268",
      "actual_png_sha256": "c14143ece417ff52edd6918b333ffe0f7c71941dcce8b0a8da0ff38d5e1a6ae6",
      "actual_view_image_read": true,
      "read_batch": 13,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F52",
      "source_ordinal": 10472,
      "global_seconds_exact": "1310309/3750",
      "local_seconds_exact": "72809/3750",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F52_student.png",
      "png_sha256": "3ff69fb3bf2206356346c9a2c311a0770afe3dd106a59b077a8720581e7c986f",
      "rgb_pixel_sha256": "0b012ed0d03ad43862a42e0fe7b6c5ca160362588eaa57d7a2a5dd00a6319dc6",
      "actual_png_sha256": "3ff69fb3bf2206356346c9a2c311a0770afe3dd106a59b077a8720581e7c986f",
      "actual_view_image_read": true,
      "read_batch": 14,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F53",
      "source_ordinal": 10484,
      "global_seconds_exact": "2623621/7500",
      "local_seconds_exact": "148621/7500",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F53_student.png",
      "png_sha256": "863167fc3b4b6b5c2db124cb4d46402184020ea1baa30a92de9f5f593cdc8c4e",
      "rgb_pixel_sha256": "b3fb89b094a359dc2583c44cde959e639350462f28dd3488ac941c46fc93f6ed",
      "actual_png_sha256": "863167fc3b4b6b5c2db124cb4d46402184020ea1baa30a92de9f5f593cdc8c4e",
      "actual_view_image_read": true,
      "read_batch": 14,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F54",
      "source_ordinal": 10495,
      "global_seconds_exact": "2101099/6000",
      "local_seconds_exact": "121099/6000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F54_student.png",
      "png_sha256": "653675405984bcf2ae96292821028ee4e2b91b017500de075284af93797c284b",
      "rgb_pixel_sha256": "2c3e77419c0505574d1358f16c0a184b7783d49c238b4fce59a1b9e47d7e7bed",
      "actual_png_sha256": "653675405984bcf2ae96292821028ee4e2b91b017500de075284af93797c284b",
      "actual_view_image_read": true,
      "read_batch": 14,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F55",
      "source_ordinal": 10506,
      "global_seconds_exact": "1752751/5000",
      "local_seconds_exact": "102751/5000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F55_student.png",
      "png_sha256": "06415c79ff8d5fa64cc89e52b7c12a78e595b3ca5394dc3b7c5088ca0e2e6262",
      "rgb_pixel_sha256": "45d95bed2d874a33e959846722e099faacbd500218685dd0400dcfee0419342a",
      "actual_png_sha256": "06415c79ff8d5fa64cc89e52b7c12a78e595b3ca5394dc3b7c5088ca0e2e6262",
      "actual_view_image_read": true,
      "read_batch": 14,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F56",
      "source_ordinal": 10517,
      "global_seconds_exact": "10527517/30000",
      "local_seconds_exact": "627517/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F56_student.png",
      "png_sha256": "ad80b6927b5f3ce8eec1209c112c7967e8e4f2d4fda1ac3897eef2aa70bd4729",
      "rgb_pixel_sha256": "a8cf4329b820dcc29fe1968e6dd6518ec3364f56f728a59aea77d82194b81795",
      "actual_png_sha256": "ad80b6927b5f3ce8eec1209c112c7967e8e4f2d4fda1ac3897eef2aa70bd4729",
      "actual_view_image_read": true,
      "read_batch": 15,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F57",
      "source_ordinal": 10528,
      "global_seconds_exact": "658658/1875",
      "local_seconds_exact": "39908/1875",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F57_student.png",
      "png_sha256": "3b77de938c8c0a09a0226262533797c20e3a96f62e7ea5021b872d26c7993608",
      "rgb_pixel_sha256": "38c0b137b43ce1411650396ef9e57e71153c03d851fb32b4f08d9d6cc946c8d7",
      "actual_png_sha256": "3b77de938c8c0a09a0226262533797c20e3a96f62e7ea5021b872d26c7993608",
      "actual_view_image_read": true,
      "read_batch": 15,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F58",
      "source_ordinal": 10540,
      "global_seconds_exact": "527527/1500",
      "local_seconds_exact": "32527/1500",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F58_student.png",
      "png_sha256": "7bf2f17d034f5f2184fc4be1d064689f335eb5a60c276c017e332001e84f2489",
      "rgb_pixel_sha256": "a8ca0f40254549f29ca5244211a23cb5f3a0c841314fc0266c5989a3e6f007f1",
      "actual_png_sha256": "7bf2f17d034f5f2184fc4be1d064689f335eb5a60c276c017e332001e84f2489",
      "actual_view_image_read": true,
      "read_batch": 15,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F59",
      "source_ordinal": 10551,
      "global_seconds_exact": "3520517/10000",
      "local_seconds_exact": "220517/10000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F59_student.png",
      "png_sha256": "4cdc03f03576b84ae274f1c4c1cf849ef5b279fa31d8b9281a4c848bbdabca1b",
      "rgb_pixel_sha256": "4e51ecf06d5cb3701fef77bdf35410ad631934098d8e599a790d7dd1e45c083c",
      "actual_png_sha256": "4cdc03f03576b84ae274f1c4c1cf849ef5b279fa31d8b9281a4c848bbdabca1b",
      "actual_view_image_read": true,
      "read_batch": 15,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F60",
      "source_ordinal": 10562,
      "global_seconds_exact": "5286281/15000",
      "local_seconds_exact": "336281/15000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F60_student.png",
      "png_sha256": "ef50f076a7db81442c71e13f5fd167d24801f050aa328978c1201ee9ed4e0f88",
      "rgb_pixel_sha256": "ef5e8191bcf17e87301152b0bde481c43bce35d7e324b07e4c5040aee085fcd0",
      "actual_png_sha256": "ef50f076a7db81442c71e13f5fd167d24801f050aa328978c1201ee9ed4e0f88",
      "actual_view_image_read": true,
      "read_batch": 16,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F61",
      "source_ordinal": 10573,
      "global_seconds_exact": "10583573/30000",
      "local_seconds_exact": "683573/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F61_student.png",
      "png_sha256": "633270776f2182735f26bf8c2ac9aaf050867e741824265439fd436a161b0c30",
      "rgb_pixel_sha256": "431e5241e7a1ccb916bff30707d369afd42c027112190b5cb9ba6f7f720464ea",
      "actual_png_sha256": "633270776f2182735f26bf8c2ac9aaf050867e741824265439fd436a161b0c30",
      "actual_view_image_read": true,
      "read_batch": 16,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F62",
      "source_ordinal": 10584,
      "global_seconds_exact": "441441/1250",
      "local_seconds_exact": "28941/1250",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F62_student.png",
      "png_sha256": "e718c27390cbb892f17da02cdc0bebef75d13c85aac6923b1633efc6188afa74",
      "rgb_pixel_sha256": "1b2e2878a7d5a1723ed6b1c637917c652fe88e95463b7893d2172c9849ee7206",
      "actual_png_sha256": "e718c27390cbb892f17da02cdc0bebef75d13c85aac6923b1633efc6188afa74",
      "actual_view_image_read": true,
      "read_batch": 16,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    },
    {
      "frame_id": "F63",
      "source_ordinal": 10596,
      "global_seconds_exact": "883883/2500",
      "local_seconds_exact": "58883/2500",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\observations\\03_AwmHb44_ouw_W11\\student_views\\F63_student.png",
      "png_sha256": "e2320bcea675188e0810b64a66e4cb768ac191cf48e159e526aa49d782e0c120",
      "rgb_pixel_sha256": "e0ba75142b16647f8fa441073881f1463c07d7fafd426ea70aa87022cdc8fc28",
      "actual_png_sha256": "e2320bcea675188e0810b64a66e4cb768ac191cf48e159e526aa49d782e0c120",
      "actual_view_image_read": true,
      "read_batch": 16,
      "visual_check": "与初稿同ID事实相符；可见性限制见本窗说明"
    }
  ]
}



## 完整新增公开记录 03_AwmHb44_ouw_W11.independent_student_view_review_v1.md
来源 G:\ai\AIC视频\reports\annotation_iteration_20261010\slot6_silver24_v1\blind_reviews\initial\03_AwmHb44_ouw_W11.independent_student_view_review_v1.md
字节 1308 SHA256 2463ae6e9abdfda0743e69fa8a86b7e3269583487688d536584f17f994e6e046

# AwmHb44_ouw:SLOT6:11 有效视图独立续审

已通过view_image读完64张实际本地CPU tensor重构PNG（16批），全部SHA与receipt相符，source ordinal及exact PTS与初稿逐项一致。初稿引用SHA：4f4f9a9b38340f778ac6347da26af2e4a3dda6818c373b9840824f118f039afa。

544x352有效显示全窗人物面部、嘴型与眼睑变化可辨，无新的手势/工具/结果。实际视图不提供声音或语言内容，整窗讲述意义U不变，不自动NO。

K/NO/U无变更；原具体UNKNOWN保留。未决问题影响完整窗口目标：全窗讲述意义缺本轮音频证据；可观察口型不等于知道语言内容，整窗U未解决。影响完整窗口目标。 对应帧：F00, F01, F02, F03, F04, F05, F06, F07, F08, F09, F10, F11, F12, F13, F14, F15, F16, F17, F18, F19, F20, F21, F22, F23, F24, F25, F26, F27, F28, F29, F30, F31, F32, F33, F34, F35, F36, F37, F38, F39, F40, F41, F42, F43, F44, F45, F46, F47, F48, F49, F50, F51, F52, F53, F54, F55, F56, F57, F58, F59, F60, F61, F62, F63。

student_processor_visibility_verified=true（仅本地CPU实际显示视图）；Linux execution=false；training_admitted=false；full_native_frames_observed=false；full_window_target_admitted=false。仍未接收或读取教师内容；可见性不是完整训练资格。



## 完整新增公开记录 risk01_independent_facts_v1.json
来源 G:\ai\AIC视频\reports\annotation_iteration_20261010\slot6_silver24_v1\blind_reviews\initial\risk01_independent_facts_v1.json
字节 49590 SHA256 66498b663d1080202eb3fa9987b2b56b2c6263ca1405c9590414b614c678a4e4

{
  "schema": "risk01_independent_local_native_facts_v1",
  "review_utc": "2026-10-10 07:09:18 UTC",
  "window_id": "kLxoNp-UchI:SLOT6:2",
  "scope": {
    "global_domain_exact": [
      "61",
      "63"
    ],
    "local_domain_exact": [
      "1",
      "3"
    ],
    "first_native_pts_exact": "1830829/30000",
    "last_native_pts_exact": "118118/1875",
    "all_60_native_frames_in_supplied_supplement_visually_observed": true,
    "full_native_frames_observed": false,
    "whole_window_or_whole_video_review": false,
    "student_processor_visibility_verified_for_this_supplement": false,
    "training_admitted": false
  },
  "evidence_binding": {
    "manifest_path": "G:/ai/AIC视频/reports/annotation_iteration_20261010/slot6_silver24_v1/supplements/risk01_kL_W02_local1to3/manifest.json",
    "actual_manifest_file_sha256": "69700fa505595d4e52d01f24d1daccea132435ffa60e92fa72f8162f52bf38fc",
    "source_sha256": "0c91bfa880e3af0e1716e7456ada0a304a97911eef76b1cd4fdce5066a52e8f7",
    "original_window_manifest_sha256_field": "2544ad72c2c7b12c5204ca197cb9d5ee7904acb752822314e42edbf6fc1a0b6a",
    "all_png_sha_match_manifest": true,
    "source_ordinals_consecutive": true,
    "actual_frames": 60,
    "actual_batches": 15,
    "batch_size": 4,
    "tool": "view_image",
    "missing_frames": []
  },
  "independence_attestation": {
    "teacher_files_read": false,
    "old_labels_human_scores_model_predictions_read": false,
    "other_project_files_read": false,
    "network_GPU_model_calls": false,
    "teacher_content_received_before_risk_seal": true,
    "disclosure": "在R000-R035观察完成后、risk01封存前，主控消息暴露了W02 F18-F24范围外的一项教师方向描述，并随即更正要求披露。该描述不在本补查局部1-3秒范围；未读教师提案或据其重做。四窗初稿与有效视图续审均此前封存，原字节保留。本补查不声称完全未收到教师内容，独立性限定为仅按本60张局部原帧直接记录。",
    "received_description_scope": "W02 F18-F24; outside risk01 local1to3"
  },
  "direct_facts": [
    {
      "frames": "R000-R009",
      "fact": "草地、右上亮斑与左上台阶边延续；画内未见犬。这不能证明犬在画外的任何姿态。"
    },
    {
      "frames": [
        "R009",
        "R010"
      ],
      "fact": "R009空草地/台阶边构图在R010切为低草地前景、浅墙与深色竖纹背景；地平线、背景和视角同时突变，直接支持切镜。",
      "cut_after_global_pts_exact": "919919/15000",
      "cut_by_global_pts_exact": "613613/10000",
      "boundary_uncertainty": "转场发生在此相邻native帧显示时间之间；没有更细时间证据。"
    },
    {
      "frames": "R010-R059",
      "fact": "同一低草地/墙背景镜头持续，墙上竖纹整体逐步向左移动，右边缘棕色犬体逐渐显露更多；支持镜头向右缓慢移/摇所形成的揭示，没有第二处可见切镜。"
    },
    {
      "frames": "R010-R023",
      "fact": "画右仅有少量棕毛部位后逐渐显露低贴草地的体表，草茎和画边遮挡；不足凭此确定完整四肢/头部姿态变化。"
    },
    {
      "frames": "R024-R059",
      "fact": "棕色躯干的侧面和上缘、靠草地的部分肢部持续可见，犬体低贴草地呈横卧侧身外观，头脸仍在右侧截断。可见面积变化伴随背景同向移动；没有直接看到从站立落地、侧身翻滚或起身过程。"
    },
    {
      "frames": "R026-R059",
      "fact": "底部画内字幕出现并延续；它不是直接犬姿证据，不据此认定放松、休息动机或音频台词。"
    }
  ],
  "continuous_action_assessment": {
    "directly_visible_continuous_posture_transition": "未见可命名的完整立卧/滚转/起身动作；画内犬体总体低贴草地，视图主要持续揭示已有侧身外观。",
    "directly_visible_camera_motion": "背景竖纹渐左移及犬体从右缘显露范围增加，支持连续向右移/摇；不把显露当成犬主动走入。",
    "not_established": [
      "R009前后犬的身体状态如何连续接续",
      "犬为何卧地",
      "犬曾从站立躺下或滚了一次",
      "不可见头部和草下四肢的微动作",
      "原视频是否有音轨及其内容"
    ]
  },
  "effect_on_prior_review": {
    "original_initial_and_student_review_bytes_preserved": true,
    "prior_K_NO_U_not_rewritten": true,
    "local_boundary_information_gain": "原F02/F03间切镜的不确定范围可在后续独立整合中缩至R009-R010；只证明切镜，不证明走远后直接躺下的连续动作。",
    "whole_window_target_resolved": false,
    "unresolved_outside_supplement_remains": true
  },
  "limitations": [
    "只观察所提供局部1-3秒的60原生PNG；范围起止与首末native PTS有正常帧栅格差异。",
    "2秒内画边及草茎遮挡头脸/部分肢部；不将未见动作机械补写为发生或未发生。",
    "未提供音频证据；不声称原视频没有音轨。",
    "范围外教师描述暴露已披露；此后不再使用绝对无教师内容声明。"
  ],
  "actual_read_inventory": [
    {
      "frame_id": "R000",
      "source_ordinal": 1829,
      "global_seconds_exact": "1830829/30000",
      "window_local_seconds_exact": "30829/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\supplements\\risk01_kL_W02_local1to3\\R000_O001829.png",
      "png_sha256": "82cf0c4246f91378ed924adbeaded85e4377d7a455e45b3d5ae54bec5698c6a9",
      "rgb_pixel_sha256": "0e2f6f8c80e88813e59d305cd90fe7c65294f473bdac0cb5eccee1e208972e98",
      "actual_png_sha256": "82cf0c4246f91378ed924adbeaded85e4377d7a455e45b3d5ae54bec5698c6a9",
      "actual_view_image_read": true,
      "read_batch": 1,
      "observed_fact": "草地、右上亮斑与左上台阶边；画内未见犬。"
    },
    {
      "frame_id": "R001",
      "source_ordinal": 1830,
      "global_seconds_exact": "61061/1000",
      "window_local_seconds_exact": "1061/1000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\supplements\\risk01_kL_W02_local1to3\\R001_O001830.png",
      "png_sha256": "54f78d9f604fc493a96938bf5b93210c867b0bf8c3892738c8942f695154529c",
      "rgb_pixel_sha256": "1da7caef78a4bdee65a44253f3514e47b523ee91c27a289a95f79324e125228c",
      "actual_png_sha256": "54f78d9f604fc493a96938bf5b93210c867b0bf8c3892738c8942f695154529c",
      "actual_view_image_read": true,
      "read_batch": 1,
      "observed_fact": "草地、右上亮斑与左上台阶边；画内未见犬。"
    },
    {
      "frame_id": "R002",
      "source_ordinal": 1831,
      "global_seconds_exact": "1832831/30000",
      "window_local_seconds_exact": "32831/30000",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\supplements\\risk01_kL_W02_local1to3\\R002_O001831.png",
      "png_sha256": "b8a3199aaf17767599aa8b9dfb6e3123d6d21b1dcd50f9d51aeae8709ad8472f",
      "rgb_pixel_sha256": "12154433572c20f38f3604da7100cb3f03b6ea3f8c3ce3277cd8980f0ca0eea5",
      "actual_png_sha256": "b8a3199aaf17767599aa8b9dfb6e3123d6d21b1dcd50f9d51aeae8709ad8472f",
      "actual_view_image_read": true,
      "read_batch": 1,
      "observed_fact": "草地、右上亮斑与左上台阶边；画内未见犬。"
    },
    {
      "frame_id": "R003",
      "source_ordinal": 1832,
      "global_seconds_exact": "229229/3750",
      "window_local_seconds_exact": "4229/3750",
      "path": "G:\\ai\\AIC视频\\reports\\annotation_iteration_20261010\\slot6_silver24_v1\\supplements\\risk01_kL_W02_local1to3\\R003_O001832.png",
      "png_sha256": "0575687d2090bd1cccdcc2c1f22c126e767951de3f3b1ac96d3a145fee932599",
