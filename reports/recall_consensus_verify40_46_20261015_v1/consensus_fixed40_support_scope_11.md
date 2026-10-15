# 双视角KEEP交集：固定40支持视图静态充分性审查

2026-10-15。结论：现有 `improvement/recall_fixed40_v1/source_audit.py:point_covering_views` 会保留**每个原ORDINARY观察点的全部覆盖视图**，不是每点只选一个的最小cover。完整原源0起15秒/7.5秒网格、精确右尾、源/clock/PTS和零padding规则不变时，原9源17视图几何可引用，无需改plan函数或重新测量、银标计数、几何扫描。

这是新假设的静态覆盖论证，不是实际17输入、模型/QA、固定事实门或新质量门通过。本次没有SSH、新CPU运行、下载、decode、processor、模型、launcher、银标重数或原几何重算；仅阅读现有实现和既有17窗报告。

## 为什么现有函数收齐全部覆盖视图

`original_grid` 返回完整源0起15/7.5网格，加已存physical_end精确右对齐尾窗，使用有理数set去重。`point_covering_views` 逐一遍历这个完整集合，对每个窗口计算所有满足 `start<=o<stop` 的原O点：

```text
for ... in original_grid(...):
    touched = {o for o in observed if start <= o < stop}
    if not touched:
        continue
    ...
    source_views.append(...)
    covered.update(touched)
```

任何touched非空的窗口都append。它没有“已有某点被covered就跳过”、first-match、greedy/set-cover或每点限1窗的分支；`covered`只在末尾用于检查观察点至少全覆盖，不参与选窗。因而被选集合精确为 `S={v∈G:v∩O≠∅}`。单靠 `covered==observed` 或硬编码17的断言本身不足以证明多视图完整；证明来自上述完整枚举和非空即保留的实际控制流。

同源right-tail与均匀窗若几何完全相同，只保留一次。新 `consensus.agreed_keep` 又按归一化有理数窗口几何校验唯一性，同一视图的多个KEEP段先并集，一种几何最多一票；不按case别名或候选条数造第二票。

## 严格充分性

对任一固定来源，令G为生产规则的全部不同overlap窗口，O为该来源原已知ORDINARY精确PTS集合，S为上述保留集合；令每个真实窗口的显式KEEP并集为K_v，且 `K_v⊆v`（原段不得扩边或移出原窗）。

对任意 `o∈O`：若窗口v能在o投票，即 `o∈K_v`，则必有 `o∈v`，所以v必属于S。反之S是G的子集。因此每个o处所有可能投票的窗口均被保留，支持数严格相等：

```text
sum(v∈G, 1[o∈K_v]) = sum(v∈S, 1[o∈K_v])
```

令A_G/A_S分别为完整网格/17子集上“至少两个不同窗口显式KEEP支持”的精确集合，则 `A_G∩O=A_S∩O`。没有保留的窗口在O任何点都不能投票，不会因漏掉第二票而把应触O的交集误判为空。该证明同时覆盖可能有三个几何重叠的右尾情形，不假定每点恰好两窗。

某些点在完整G中天然只有一个覆盖视图，则其完整支持数上限本来就是1；不是选窗漏票。不得补一个不包含该点的邻窗、复制相同geometry或增加padding来制造2票。

观察点绑定仍为同一原source SHA、clock SHA、ordinal与exact PTS；所有窗口和KEEP membership均半开。新交集仅由实际显式KEEP产生，UNKNOWN/DROP无票，同视图重复段无额外票。

## 原17几何可引用的范围

以下仅引用 `fixed40_admission_03.md` 与 `fixed40_execution_design_09.md` 已有9源/222点/17窗记录，没有重算：

| case | 原O点数 | 保留的全部可能触O窗口 |
| --- | ---: | --- |
| R07 | 26 | [105,120), [225/2,255/2) |
| R11 | 55 | [120,135), [255/2,285/2) |
| R15 | 25 | [90,105), [195/2,225/2) |
| R18 | 39 | [499559/4000,559559/4000) |
| R19 | 45 | [195/2,225/2), [105,120) |
| S08 | 3 | [0,15) |
| S30 | 13 | [90,105), [195/2,225/2), [105,120) |
| S32 | 4 | [225/2,255/2), [120,135) |
| S36 | 12 | [30,45), [75/2,105/2) |

R18尾窗来自原已成功clock的physical_end=`559559/4000`，不能用名义150秒或观察clip内0起网格替代。表中单窗来源保留原状，不在本审查中再缩减17范围。几何可引用不等于任何旧B0/VERIFY调用具有完整identity或已成功；实际输入/张量/prompt/model/原始回答/首次独立QA仍须按新登记绑定，缺执行不能当零票。

## 下一事实门需要改的是候选集合语义

plan函数无需修改。未来独立事实检查必须按**全部17个已登记视图及全部实际原段**建立完整分母，核每段真实B0→原VERIFY raw/done→首次独立QA，按不同原窗口几何聚合显式KEEP，再由冻结 `consensus.agreed_keep` 得到双支持集合A。不能直接把旧单KEEP并集当成本轮候选结果，也不能把遗漏/失败视图记为UNKNOWN、空KEEP或零票。

对任意真实VERIFY基线B，实际合并为 `B∪A`。若完整证据得到 `A∩O=∅`，则 `((B∪A)\B)∩O=∅` 对任意B成立，且 `B⊆B∪A` 证明结构性不删。若A触O而缺真实VERIFY基线，只能INCONCLUSIVE，不能直接原差分FAIL或假PASS。旧单KEEP否决器若检查的是更大集合 `∪K_v`，其避O仍是更强的充分条件，但它触O不代表双支持A触O；不得混写两个假设的结果或用旧条件替代新完整质量门。

本轮fresh确认、完整真实调用/首次QA、固定事实门与最终426原帧/框/ratio/model_params数值字节保持均是后续各自证据，本文不授权或宣称它们通过。原40为 `AI_REVIEWED_SILVER_NOT_HUMAN_GOLD`，原coverage/reference_quality FAILED、KEEP184、ORDINARY222、UNKNOWN2675及所有旧失败保持；不把UNKNOWN/未选称普通，不把已曝光来源称新真值。
