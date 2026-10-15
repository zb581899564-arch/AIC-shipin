源边界inward修订已独立实现于 `improvement/local_boundary_v2`，Linux未来根为 `.../twenty_hour_five_20261014_v1/local_boundary_v2`。v2未部署，真实CPU/processor/model/media均0。全部v1代码和已部署gzip helper2字节未改，旧版本可直接供review；旧成功gzip证明未重跑。

主代理批准的必要差异：

- 新schema `LOCAL_BOUNDARY_NATIVE64_V2_REVISION03` 和 `contract_revision=SOURCE_EDGE_INWARD_REVISION_03`，强制独立v2输出根。
- 新chosen cut必须有窗内两侧可见样本，外侧检查不再机械绑定原端点有没有source外画面。
- 原source start以既有已验complete origin mapping确认normalized首PTS=0；不会另设literal rawPTS0要求否定旧合法nonzero origin，也不新猜offset。原source physical end由既有末PTS+正duration确认。
- source首/末只允许inward；内部原point继续原strict bracket，新chosen cut继续真实duration连续检查，sample0/63仍UNKNOWN。
- end仍是最后included样本下一native PTS的exclusive cut，外侧可见帧可恰从cut开始（<=，避免错误严格不等号）。
- prompt明确几何连续不是语义证据，同候选清晰内/外transition不足必须UNKNOWN/KEEP；更激烈的同一持续动作不能单独作为新边界。不恢复source外不可见动作真起止，不要求高光必须完整动作，不传新GT给prompt。
- 独立CPU replay重新算chosen cut可见几何、source原cut合法性、strict内点bracket和真实native membership。gzip保存/读取函数AST与v1完全一致。
- 未来Charades root进入明确外部路径范围，只有dev source_role允许pilot；规范完整source-separation、实际coarse/raw/独立重放证据仍必须先齐，当前没有这些实际新回答，不能启动plan或模型。

critic独立批判提供的例子：25fps源[0,10)，原[0,4)，start窗[0,3)，anchor1，index14=cut0.64，前shown0.60、后shown0.68。原[6,10)的end index49=最后included9.28，exclusivecut9.32、下一个shown恰9.32、anchor9。两者数学上可以在窗内审查新cut，无需source外视频。

反例：source0开始一直是同一动作，cut0.64仅是更激烈阶段。几何/连续性可通过，却不证明同候选之外；必须由模型保留不确定，后续独立开发证据验证。纯contract测试只证明UNKNOWN可严格保原，没有证明模型一定作出正确语义选择。

实际Linux内存中纯code检查：7脚本AST通过，9例contract与独立replay结果一致，包括上述两inward例、sample0/63、内部old bracket断续、chosen duration不足、UNKNOWN/KEEP保原、旧已验nonzero raw origin。没有processor、媒体、模型或v2部署。证据 `pure_contract_check_01.json`；v1字节检查 `v1_preservation_01.json`；v2最终SHA/bytes `code_manifest_03.json`。

后续只有主代理冻结真实Charades coarse及独立重放后，从dev来源固定10–20事件、冻结新语义protocol与实际预算才可使用v2。该修订不为了让五包产生变化而放过不清晰事件身份，也不恢复旧失败路线。
