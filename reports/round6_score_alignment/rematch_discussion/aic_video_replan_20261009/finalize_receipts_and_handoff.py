"""Record this discussion and its local-only implementation without touching frozen history."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

DISC = Path(__file__).resolve().parent
PROJECT = Path('G:/ai/AIC视频')
RUN = PROJECT / 'reports/round6_score_alignment/rematch_execution/rematch_exec_20261005T1215Z'
ROUTE = RUN / 'spatial_gap8_pchip_slot4_v1'


def identity(path):
    data = path.read_bytes()
    return {'file': path.name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def main():
    now = datetime.now(timezone.utc).isoformat()
    ledger_path = DISC / 'ledger.json'
    ledger = json.loads(ledger_path.read_bytes())
    notice = ledger['rounds']['final_notice']
    acknowledgements = {}
    for seat in ('grok', 'sol', 'tibo', 'gemini'):
        path = DISC / f'{seat}-final-ack.md'
        if path.exists():
            acknowledgements[seat] = identity(path)
    notice['acknowledgements'] = acknowledgements
    notice['gemini_delivery_correction'] = {
        'observed_utc': now,
        'initial_attempt': 'Earlier UI transient was recorded as sent; final user turn was absent after a single reload of the same conversation.',
        'recovery': 'After confirming absence, seven final-v2 attachments uploaded and upload-complete observed; send then produced actual new final-notice user turn and reply-in-progress.',
        'status': 'FINAL_V2_USER_TURN_VISIBLE_WITH_ALL_SEVEN_ATTACHMENTS',
        'no_extra_pro': True,
    }
    notice['status'] = 'FINAL_COMPLETE_PACKET_AND_DECISION_DELIVERED_TO_ALL_FOUR'
    ledger['final_decision']['stage'] = 'DISCUSSION_COMPLETE_G0_LOCAL_CPU_PASS_NATIVE_HANDOFF_PENDING'
    ledger['pro_budget'].update({'new_completed': 1, 'new_remaining': 4})
    ledger['execution'] = {
        'route': str(ROUTE), 'stage': 'G0_LOCAL_CPU_PASS_NATIVE_HANDOFF_PENDING',
        'receipt': identity(ROUTE / 'g0_local_cpu_math.json'),
        'full_native_G0_accepted': False, 'new_model_calls': 0, 'new_decoder_calls': 0,
        'new_optimizer_updates': 0, 'remote_writes': 0, 'new_final_426_zip': False,
        'automation': {'id': 'aic-linux', 'status': 'ACTIVE', 'interval_minutes': 15,
                       'notification_policy': 'failed_runs_only', 'destination': 'thread',
                       'creation_tool_result': 'Created automation in the app; subsequent mode=view rendered automation card'},
    }
    ledger['finished_record_utc'] = now
    ledger_path.write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    marker = '<!-- END_CURRENT_SPATIAL_GAP8_SLOT4_REPLAN -->'
    text = (
        f'## 20261009重新网页一锅炖与空间gap8 PCHIP有限接续（记录UTC {now}）\n\n'
        '用户要求重新讨论、网页席位改GPT-6 sol，本轮额外Pro五次已追加原连续预算簿；旧三次不重置。'
        '技能及固定席位已修改；实际普通三轮、Chrome既有研究项目Pro slot4完整裁决、四席裁决后复核和最终完整全文知会完成。'
        '本轮Pro实际1/5、剩4，累计slot4/8；Tibo原附件字节SHA未独立验成的限制、Gemini早先拒答/晚到完整复核和知会首次未持久化的纠正均保留。'
        '完整私有讨论目录reports/round6_score_alignment/rematch_discussion/aic_video_replan_20261009，最终final-decision-v2.md，'
        'SHAe5fb63ecee8ceebe37ea9f5449d3d5b54fcfe860aa14c6ad66213c5e0b5b9c2b；不冒称多数正确或保证官网涨分。\n\n'
        '唯一新入口spatial_gap8_pchip_slot4_v1/CONTINUE.md与PROTOCOL.md。保留V14固定时间521回答/102470源帧键、原B时间adapter与原8B空间基座、B2原31295锚点。'
        '仅同镜头四连续原锚点的中央gap8/外侧1..8/原恒定最大合法宽度，最终整数xy标准非等距PCHIP有理数半偶；原锚点与不适用正常分支旧浮点线性逐框保持。'
        '新四支持provenance和独立展开多项式验收，不改旧冻结loader或只加来源名。'
        '元数据固定哈希8来源组、前2工程后6确认、每组1文件1gap/7隔离探针/最多88缺失单帧请求；先封存预测再揭示探针，探针不作为生产锚点。'
        '确认探针若实际参与公式/门/样本选择或曝光史无法核清，则任何新揭示前NO_426，不换组。'
        '4/6确认差正、确认和全组均值正、确认留一非负、固定NONTEST选帧最终整数框实际变化及全部严格验收同时通过才唯一426探索包。'
        '同模型逐帧一致性不是构图真值或官网质量；失败NO_426/NO_EFFECT，不重开旧输入路线或无限换配方。\n\n'
        '当前实际stage=G0_LOCAL_CPU_PASS_NATIVE_HANDOFF_PENDING。新本地7CPU合同通过、2500非等距模式/22500值独立重算，'
        '不是实际native全量G0或模型质量。原manifest只读已核NONTEST8登记source_group各不相同/缺失0，仍待全资产/实际模型processor/'
        '原线性依赖/许可/曝光史移交、样本与新锁冻结、单次launcher及真实非测试。新模型/解码/optimizer/远端写入0、无新426ZIP。'
        '新代码尚未冻结；既有讨论后自主执行授权保持，继续具体完成G0→真实非测试→仅过门426→独立终态。\n\n'
        '已重新登记aic-linux ACTIVE每15分钟thread heartbeat、failed_runs_only静默，prompt使用该CONTINUE完整当前边界。'
        '原NRA监控已删除是旧路线历史，不覆盖本次新接续。共享任务/锁/7200offset/旧费用/所有历史源码锁/raw/STOP/UNKNOWN保护；'
        '不重跑成功生成和已完成验收，不改SSH/Tailscale/代理/服务。小量控制直SSH既有例外授权保持；Mac在线不参与，'
        '新model/data/批量产物/ZIP大流量仍先说明方向字节链路机场消耗并等许可。'
        '最终真实426全11strict/独立新数学与来源/ZIP大小SHA CRC唯一JSONL/身份及所有GPU自然终态费用唯一账本、筛选GitHub完成后才通知；'
        '包留Linux，不自动回传或官网提交。旧最佳37.63保护，V14约37.60仅用户差值推算；新官网分UNKNOWN。\n\n'
        + marker + '\n\n'
    )
    targets = (PROJECT / 'AGENTS.md', RUN / 'STATUS_AUTOPILOT_20261007.md')
    for path in targets:
        for lock_path in RUN.glob('*/source_lock.json'):
            lock = json.loads(lock_path.read_bytes())
            for key in ('files', 'production_files'):
                rows = lock.get(key, {})
                names = list(rows) if isinstance(rows, dict) else [row['path'] for row in rows]
                assert not any(name.replace('\\', '/').endswith('/' + path.name) or name == path.name
                               for name in names), (str(lock_path), str(path), 'handoff is frozen')
    for path in targets:
        original = path.read_bytes()
        # Preserve every historical section byte-for-byte. This script runs once.
        assert marker.encode() not in original, 'current handoff already recorded; do not duplicate'
        path.write_bytes(text.encode('utf-8') + original)
    (RUN / 'controller/spatial_gap8_slot4_handoff_latest.md').write_text(text, encoding='utf-8')
    receipt = {
        'utc': now, 'status': 'PASS_DISCUSSION_FINAL_DELIVERY_AND_LOCAL_ONLY_IMPLEMENTATION_RECORD',
        'final_packet': identity(DISC / 'context-final2.md'),
        'decision': identity(DISC / 'final-decision-v2.md'),
        'pro_full_reply': identity(DISC / 'pro-p01.md'),
        'pro_ui_screenshot': identity(DISC / 'pro-slot4-final.png'),
        'ledger': identity(ledger_path), 'local_cpu': identity(ROUTE / 'g0_local_cpu_math.json'),
        'pro_new_used': 1, 'pro_new_remaining': 4, 'remote_execution_started': False,
        'full_native_G0_accepted': False, 'model_calls': 0, 'optimizer_updates': 0,
        'all_four_final_packets_delivered': True, 'final_ack_files': acknowledgements,
        'automation': ledger['execution']['automation'],
    }
    (DISC / 'discussion_acceptance.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    with (DISC / 'EXECUTION.md').open('a', encoding='utf-8') as handle:
        handle.write(f'\n最终知会回执与本地接续记录UTC {now}：全部四席已实际送达final-v2；Gemini首次瞬态未持久化经同URL刷新核无该消息后补齐上传/发送，原记录纠正保留。Pro本轮仍1/5剩4。'
                     'aic-linux已实际重新创建ACTIVE/15分钟/failed_runs_only并view核卡片；全量native G0、Linux部署和模型调用尚未开始。新AGENTS/STATUS只追加未绑定当前说明，所有历史锁schemas已先核保护。\n')
    print(json.dumps({'status': receipt['status'], 'utc': now, 'pro_new_used': 1,
                      'pro_new_remaining': 4, 'native_G0_complete': False}, ensure_ascii=False))


if __name__ == '__main__':
    main()
