v3 是 v2 revision03 的独立复制，尚未部署或运行真实 plan/CPU/model。v1/v2 和冻结 CPU helpers 未改；8 个 v2 源文件逐 SHA 与原 manifest03 一致。

仅 4 个业务文件有改动：

- `lb_contract.py`：只把 schema 改为 LOCAL_BOUNDARY_NATIVE64_V3_REVISION03，CONTRACT_REVISION 保持 SOURCE_EDGE_INWARD_REVISION_03。所有函数 AST 与 v2 完全一致。
- `lb_io.py`：EXPECTED_BASE 与唯一 runtime 模块名改为 v3；增加 Charades boundary_v2、coarse_v1 证据根，并分出 MEDIA_ROOTS，coarse 根不在媒体范围内。gzip 函数完全不变。
- `plan_local_inputs.py`：增加 scope_metadata/event_scope_metadata 纯元数据门，开发与确认分 role/count/exposure；确认冻结 selection SHA，开发前冻结 confirmation extraction SHA，均纳入 required_files；原 raw+CPU+独立 replay 完整证据门保留。仅用注册表既有事件，不自动读取 GT 或挑候选。Charades input meta 的原 role 不可改名，coarse raw/request/done/replay 仅独立 coarse root，media 仅 Charades media_01/source_id。事件增加 source_id/source_role 元数据。
- `prepare_local_inputs.py`：只把 source media 的 checked_ref roots 改成 MEDIA_ROOTS。continuity 函数不变。

infer/grammar/replay 三文件与 v2 字节完全一致；README 更新 scope 和字段。scope 字段接口已经主控接受。两个科学 scope 为10..20 events，smoke 为1event/EXPOSEDdev，旧成功 smoke 不重跑。确认 extraction 规则由主控提前冻结：固定 role 来源按 window/segment 顺序先每源第一候选一轮、再第二一轮、最多20，LEGAL_EMPTY 保留完整源覆盖分母，不足10如实阻断，不能增源凑数。

一次 Linux in-memory 纯检查：7 AST；5 合法 scope/count/role 组合通过；16 个 metadata 拒绝场景通过（9/21 events、曝光标记错、缺 selection/extraction SHA 或锁、提前冻结/封存标记错、dev误当confirm、旧SumMe当confirm、coarse raw当media、旧v2输出根）。合同所有数学/prompt/UNKNOWN/exclusive-end函数、prepare continuity、独立 replay endpoint 和 gzip 函数 AST 均保持。真实 plan/媒体读取/processor/model 为0，未读取参考或 coarse 回答。

原 B coarse driver 尚需主控真实完成及独立 replay；本次只验证接口元数据，不能宣称端点或确认质量。两份新增 frozen 元数据可放本 v3 base，和 protocol 一样按 bytes/SHA 纳入原 required_files 门，planner 不解封质量内容。资源/GPU/replay/封包沿现有主控接口，没有另增准入流程。
