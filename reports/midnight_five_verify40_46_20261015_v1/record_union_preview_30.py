from pathlib import Path
import datetime as dt
import json

r = Path(__file__).resolve().parent
snapshot = json.loads((r / 'union_review_snapshot_29.json').read_text(encoding='utf8'))
value = snapshot['review_receipt.json']
assert not snapshot['handle']['exists']
assert value['status'] == 'PASS_ENGINEERING_PREVIEW_ONLY_PUBLICATION_NOT_AUTHORIZED'
assert value['publication_authorized'] is False
p = r / 'current_state.json'
state = json.loads(p.read_text(encoding='utf8'))
state['updated_UTC'] = dt.datetime.now(dt.timezone.utc).isoformat()
state['stage'] = 'FOUR_DELIVERED_FIFTH_UNION_ENGINEERING_PREVIEW_READY_AWAIT_HUMAN_FOURTH_RISK_SCOPE'
state['unpublished_backup_review'].update(
    status='ENGINEERING_PREVIEW_READY_LINUX_ONLY_NOT_DELIVERED',
    actual_preview=value['zip'], bytes=value['bytes'], SHA256=value['SHA256'],
    canonical_SHA256=value['canonical_SHA256'], frame_count=value['frame_count'],
    added_native_frames_vs_baseline=value['added_native_frames_vs_baseline'],
    removed_native_frames_vs_baseline=0, original_baseline_frames_and_boxes_all_preserved=True,
    independent11strict=True, distinct_from_current_four=True, Windows_delivery_performed=False,
    preview_receipt_ref='union_review_snapshot_29.json', actual_new_model_calls=0,
    risk_effect_screening=False, quality_pass_claimed=False)
p.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf8')
note = """# 第五份备用：三类语义并集风险预览

已完成Linux工程预览，尚未获第四风险包交付许可，未回传Windows；当前实际交付仍4/5。

固定规则是把已生成的动作、情绪反应、信息亮点三类补召回逐原生帧取并集，没有新推理、训练、标签或效果筛选。40.46的122002原帧与原框全部保留，新增184帧、删除0帧，总122186帧；相对动作版多60帧、反应版多176帧、信息版多132帧，与当前4包及全部历史真实预测不同。

预览ZIP 380660字节，SHA256 `207cd33bc2b13c64005dde49d0e6ee2775a44c61a4e1afd10bb24ffc565de26e`。426完整非空、原生帧与框来源、实际8.78245912B、单JSONL、CRC/memberSHA和一次新组合独立11strict均通过。原518模型+1相同输入alias及成功首次QA仅引用，没有重跑。原4ZIP未改变。

这是未知效果的第四个风险方向，不是验证通过包。当前只有一个通过外部代理确认的删选版；PAIR确认3质量门失败，语义保护开发恢复0帧且与已有方案无区别，这两条STOP均保留。若人类同意本轮由3风险扩大为4风险，就可引用本完整预览、不重新推理/封包，完成最终传输验收作为第5份；若不同意则保留Linux预览，不发布、不把4/5说完成。
"""
(r / 'FOURTH_RISK_PREVIEW.md').write_text(note, encoding='utf8')
with (r / 'CONTINUATION.md').open('a', encoding='utf8') as stream:
    stream.write("\nUnion preview actual complete (CPU-only, PID gone, independent11strictPASS): ROOT/semantic_union_review_27/review_receipt.json, archive380660B/SHA207cd33bc2b13c64005dde49d0e6ee2775a44c61a4e1afd10bb24ffc565de26e,122186frames/+184/-0 vsVERIFY, allbaselineboxes exact. Actualnewmodels0. It remains publication_authorized=false, notWindows/notpackages/notfifth. All4 existingdifferent and23distincthistorical excluded. Need one human fourth-risk scope decision before anydelivery; do not interpret elapsedtime or originalroute approval as riskcount approval.\n")
print('Concrete preview ready for one human scope decision; actual delivery count4.')
