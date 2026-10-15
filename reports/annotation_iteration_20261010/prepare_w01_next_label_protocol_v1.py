"""Offline capacity diagnosis and a prospective draft; no production edits."""
from pathlib import Path
import importlib.util,json,hashlib
ROOT=Path(__file__).resolve().parent/'w01_editorial_diagnostic_v1'
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):
    with p.open('x',encoding='utf-8') as f:json.dump(d,f,ensure_ascii=False,indent=2)
report=load(ROOT/'final_diagnostic_audit_v1.json')
contract=Path(r'G:\ai\AIC视频\reports\round6_score_alignment\rematch_execution\rematch_exec_20261005T1215Z\teacher_student_autopilot_v14\precision_helpers\contracts.py')
spec=importlib.util.spec_from_file_location('w01_original_contract_readonly',contract);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
outputs={}
for side in ('teacher','independent'):
    from fractions import Fraction
    ranges=report['document_geometry'][side]['student']['KEEP_union_exact']
    numbers=[[float(Fraction(a)),float(Fraction(b))] for a,b in ranges]
    raw=json.dumps({'segments':numbers},separators=(',',':'))
    result,errors,warnings=m.parse_segments(raw,30,5,True)
    outputs[side]=dict(sealed_annotation_sha256=report['document_geometry'][side]['student']['sha256'],contiguous_intervals=len(ranges),
        candidate_raw=raw,original_parser_result=result,errors=errors,warnings=warnings,training_admitted=False,
        no_KEEP_removed=True,no_NO_gap_filled=True,not_a_model_prediction=True)
save(ROOT/'representation_inspection_v1.json',dict(status='ACTUAL_ORIGINAL_PARSER_REJECTION_OF_BOTH_SEALED_PROPOSALS',
    original_contract_path=str(contract),original_contract_sha256=sha(contract),outputs=outputs,
    five_interval_limit_origin='LOCAL_B0_MODEL_PROMPT_AND_PARSER; no evidence here that it is an official submission restriction',
    count_of_confirmed_true_highlights='UNKNOWN; proposals are not gold',new_model_calls=0,new_optimizer_updates=0))
refs=load(ROOT/'native_index.json')['frames'];seal=load(ROOT/'teacher/seal.json')
save(ROOT/'teacher_seal_metadata_discrepancy_v1.json',dict(status='TEACHER_DECLARED_RANGE_ERROR_PRESERVED_NO_REWRITE',
    expected_source_ordinal_endpoints=[refs[0]['source_ordinal'],refs[-1]['source_ordinal']],
    teacher_student_declared_endpoints=seal['student_read_scope']['source_ordinals'],teacher_native_declared_endpoints=seal['native_read_scope']['source_ordinals'],
    actual_stream_and_per_frame_index_identity='64+64 unique PNG identities independently checked; wrong seal endpoints do not rewrite those observations',
    teacher_seal_sha256=sha(ROOT/'teacher/seal.json'),training_admitted=False))
draft='''# 下一版标注方案草案：先解决事实与目标，不先扩大数据

这是主控根据本轮新诊断提出的下一版方案，不是Pro的新裁决，不解除旧0/4 STOP，不启动GPU。既有Pro使用6/8，剩2。原37.66包已再核SHA/CRC，生产权重未变。

## 新证据

Gemini与新独立审阅分别实际接收64学生图、64原图；学生答案先于原图封存且原字节保持。两份提案均连续覆盖30秒，没有自行保留具体会改变取舍的UNKNOWN。形式完整不等于语义正确：Gemini F37把人物和长字幕误记成下一镜头狗和另一字幕，原图阶段重复错误。教师seal还把首尾源ordinal900..1798写成901..1801，已以侧车保留纠错，未改教师原件。

Gemini选22.83秒、10叙事单元、7连续区间；独立者选23.62秒、5叙事单元、6连续区间；二者KEEP/NO分歧3.55秒。原B0 parser实际拒绝两份完整提案。没有把NO缝隙并入KEEP、删除KEEP或拿恰好五单元的一份作金标。

原目录已有20个人工重要性评分。只查看当前已曝光训练源W01的记录，向量长度与3896原生帧数一致；按源ordinal索引的试探比较中，KEEP并不比NO明显高。精确时钟/原版标注映射及与AIC目标的对应尚未验收，B对本源历史曝光也未核。因此这是一条校准警讯，不是新增验证成绩或金标，也不据此生成阈值、TopK或训练目标。

## 所选工作顺序

1. **事实先行。** 用当前新会话单图F37探针检查fresh短上下文能否正确识别；仅一次、最多3分钟、只读一PNG，不透露旧答案。正确只说明这一次短上下文表现改善；错误或未完成只说明未消解该问题。不能唯一归因长上下文、缓存或图像接口。后续教师按小批事实记录并逐批核对frame_id、主体、字幕，再做全窗编辑；身份和字幕错位优先返修，动作、情绪、动机严格分开。
2. **分开事实覆盖与高光选择。** 完整coverage用于证明哪里看过、哪里没有明确选择，不要求每一条非重复信息都自动KEEP。下一版须在标注之前明确“短高光编辑”的相对重要性：主题关键动作、互动、结果、代表性展示与其必要建立；字幕重要性和静态展示按实际内容判断，不设运动/静止捷径。事实不确定、一般采样风险与编辑偏好分别记录；不把不可见区间转成负例，不为了负例比例删段。
3. **再解决表达合同。** 优先保留原B8B为比较起点。五段是当前模型合同，不据此推称官方限制。若校准后的真实选择仍超过五段，另立新版本比较支持完整目标的表示；可考虑增加列表容量或逐采样重要性输出，但要同步审查prompt、parser、grammar、真实token预算、训练目标和native时间映射。不能只放宽parser，也不事后TopK截标签、合并NO缝隙或切易窗口补数。现在不选定改容量路线。
4. **参考成立后才续训。** 原24窗固定来源计划、已有图像准备继续作为起点；先把导致拒收的具体问题消解，不先增加外部数据或跑剩20窗相同弱提示。下一次实验须另写假说/监督资格/来源划分/曝光与费用记录；达到至少8完整训练窗和4来源组等既有Pro门后，才讨论B上小规模时间LoRA与一次开发/锁定比较。空间框沿用现有基线以控制变量；新权重不得用旧时间预测冒充新推理。

## 暂不采用

批量堆标签；把工具完成当内容正确；放宽容量后直接开训；把采样切点不确定全部扩大成U；拿新封存判断重写旧STOP；把旧37.66 ZIP称为新训练产物。没有任何一窗结果足以保证官网提分。

下一决策材料应包含本轮实际两份封存原答、事实错误、独立read scope与表示拒绝、单图探针的实际终态；若仍有影响方案的重大歧义，再组织普通席交叉审查后使用剩余Pro额度。当前无新Pro调用，不为知会耗次数。
'''
with (ROOT/'next_label_protocol_draft_v1.md').open('x',encoding='utf-8') as f:f.write(draft)
print(json.dumps({'original_parser_rejections':{s:outputs[s]['errors'] for s in outputs},'draft':str(ROOT/'next_label_protocol_draft_v1.md')},ensure_ascii=False))
